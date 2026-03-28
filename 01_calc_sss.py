# /data03/hjj/hjj/LFS-new/newwork/region/01_calc_sss.py
import os, glob, re, time, random, warnings
import numpy as np, pandas as pd, xarray as xr
import multiprocessing as mp
from datetime import datetime, timedelta

# 🎯 导入统一配置
from config_regions import CPU_NUM, START_DATE, END_DATE, DATA_OUT_DIR, REGIONS

warnings.filterwarnings('ignore')

MOD_BASE_DIR = '/data04/LFS/LFSv1.0/ext_fct/10km'
OBS_BASE_DIR = '/data03/hjj/hjj/DATA/MOB_SSS_0.1'

global_grid = {}

def init_worker():
    global global_grid
    sample_f = glob.glob(os.path.join(MOD_BASE_DIR, "case_*", "*.nc"))[0]
    with xr.open_dataset(sample_f, decode_times=False) as ds:
        lat, lon = ds['lat'].values, ds['lon'].values
        
    ln2, lt2 = np.meshgrid(lon, lat)
    masks = {k: (ln2 >= v['lon'][0]) & (ln2 <= v['lon'][1]) & \
                (lt2 >= v['lat'][0]) & (lt2 >= v['lat'][2]) for k, v in REGIONS.items()}
    global_grid = {'weight': np.cos(np.radians(lt2)), 'masks': masks}

def process_single_case(case_dir):
    time.sleep(random.uniform(0, 3))
    try:
        case_date_str = re.search(r'case_(\d{8})', os.path.basename(case_dir)).group(1)
        case_date_obj = datetime.strptime(case_date_str, '%Y%m%d')
    except: return []

    results = []
    for day_idx in range(1, 31):
        valid_date = case_date_obj + timedelta(days=day_idx-1)
        if valid_date.month == 2 and valid_date.day == 29: continue
        
        mod_f = os.path.join(case_dir, f'ss-{valid_date.strftime("%Y-%m-%d")}_10km.nc')
        obs_f = os.path.join(OBS_BASE_DIR, valid_date.strftime("%Y%m"), f'{valid_date.strftime("%Y%m%d")}_so_remap.nc')

        if not (os.path.exists(mod_f) and os.path.exists(obs_f)): continue

        try:
            with xr.open_dataset(mod_f, decode_times=False) as ds_m: mod_d = ds_m['ss'][0, 0].values
            with xr.open_dataset(obs_f, decode_times=False) as ds_o: obs_d = ds_o['so'][0, 0].values
            
            diff = mod_d - obs_d
            rec = {'case_date': case_date_str, 'forecast_day': day_idx}
            
            for r_key, r_mask in global_grid['masks'].items():
                m = (~np.isnan(diff)) & r_mask
                if np.sum(m) > 0:
                    w, d = global_grid['weight'][m], diff[m]
                    sw = np.sum(w)
                    rec[f'{r_key}_Bias'] = np.sum(d * w) / sw
                    rec[f'{r_key}_MAE']  = np.sum(np.abs(d) * w) / sw 
                    rec[f'{r_key}_RMSE'] = np.sqrt(np.sum((d**2) * w) / sw)
                else:
                    for met in ['Bias', 'MAE', 'RMSE']: rec[f'{r_key}_{met}'] = np.nan
            results.append(rec)
        except: continue
    return results

def main():
    all_cases = sorted(glob.glob(os.path.join(MOD_BASE_DIR, "case_*_10km")))
    target_cases = [c for c in all_cases if START_DATE <= re.search(r'case_(\d{8})', c).group(1) <= END_DATE]

    if not target_cases: return

    final_res = []
    total = len(target_cases)
    with mp.Pool(CPU_NUM, initializer=init_worker) as pool:
        # 🎯 纯净版进度条
        for i, res in enumerate(pool.imap_unordered(process_single_case, target_cases)):
            if res: final_res.extend(res)
            if (i + 1) % max(int(total / 10), 1) == 0 or (i + 1) == total:
                print(f"    -> SSS 进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)", flush=True)

    # 🎯 防崩溃保护
    if not final_res: return

    df = pd.DataFrame(final_res).sort_values(by=['case_date', 'forecast_day'])
    out_csv = os.path.join(DATA_OUT_DIR, f'SSS_Evaluation_{START_DATE}-{END_DATE}.csv')
    df.to_csv(out_csv, index=False)

if __name__ == "__main__":
    main()