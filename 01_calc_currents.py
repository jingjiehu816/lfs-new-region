# /data03/hjj/hjj/LFS-new/newwork/region/01_calc_currents.py
import os, glob, time, random, warnings
import numpy as np, pandas as pd, xarray as xr
import multiprocessing as mp
from datetime import datetime, timedelta

# 🎯 导入终极配置
from config_regions import CPU_NUM, START_DATE, END_DATE, DATA_OUT_DIR, REGIONS

warnings.filterwarnings('ignore')

# --- 本地配置 ---
MAX_WAIT_SECONDS = 10 
OBS_BASE_PATH = '/data04/LFS/diag/OSCAR/'
MOD_BASE_PATH = '/data04/LFS/LFSv1.0/ext_fct/10km/'
THRESHOLD_VAL, REL_ERROR_THRESH, SURFACE_IDX = 0.5, 30.0, 0

def calculate_speed(u, v): return np.sqrt(u**2 + v**2)

def calc_metrics(mod, obs, w, mask=None):
    m = (~np.isnan(mod)) & (~np.isnan(obs))
    if mask is not None: m = m & mask
    if np.sum(m) == 0: return np.nan, np.nan, np.nan
    diff, weights = mod[m] - obs[m], w[m]
    sw = np.sum(weights)
    if sw == 0: return np.nan, np.nan, np.nan
    bias = np.sum(diff * weights) / sw
    mae = np.sum(np.abs(diff) * weights) / sw
    rmse = np.sqrt(np.sum(diff**2 * weights) / sw)
    return bias, mae, rmse

def calc_pass_rate(mod_s, obs_s):
    m = (~np.isnan(mod_s)) & (~np.isnan(obs_s)) & (obs_s > THRESHOLD_VAL) & (mod_s > THRESHOLD_VAL)
    if np.sum(m) == 0: return np.nan
    rel_err = np.abs(mod_s[m] - obs_s[m]) / (obs_s[m] + 1e-8) * 100
    return (np.sum(rel_err <= REL_ERROR_THRESH) / np.sum(m)) * 100

def process_single_case(case_dir):
    time.sleep(random.uniform(0, MAX_WAIT_SECONDS))
    try:
        case_date = datetime.strptime(os.path.basename(case_dir).split('_')[1], '%Y%m%d')
    except: return []

    results = []
    for day in range(1, 31):
        fcst_dt = case_date + timedelta(days=day-1)
        obs_f = os.path.join(OBS_BASE_PATH, f"oscar_currents_interim_{fcst_dt.strftime('%Y%m%d')}.nc")
        uu_f = os.path.join(case_dir, f"uu-{fcst_dt.strftime('%Y-%m-%d')}_10km.nc")
        vv_f = os.path.join(case_dir, f"vv-{fcst_dt.strftime('%Y-%m-%d')}_10km.nc")

        if not (os.path.exists(obs_f) and os.path.exists(uu_f) and os.path.exists(vv_f)): continue

        try:
            with xr.open_dataset(obs_f, decode_times=False) as ds_o:
                o_u, o_v = ds_o['u'][0].values, ds_o['v'][0].values
                lat, lon = ds_o['lat'].values, ds_o['lon'].values
                if o_u.shape != (len(lat), len(lon)): o_u, o_v = o_u.T, o_v.T

            ln2, lt2 = np.meshgrid(lon, lat)
            ln_n, w2 = np.mod(ln2, 360), np.cos(np.radians(lt2))
            # 🎯 适配新区域
            reg_masks = {v['short_name']: (ln_n >= v['lon'][0]) & (ln_n <= v['lon'][1]) & (lt2 >= v['lat'][0]) & (lt2 <= v['lat'][2]) for k, v in REGIONS.items()}

            with xr.open_dataset(uu_f, decode_times=False) as ds_u, xr.open_dataset(vv_f, decode_times=False) as ds_v:
                m_u = ds_u['uu'].isel(time=0, lev=SURFACE_IDX).interp(lat=lat, lon=lon).values
                m_v = ds_v['vv'].isel(time=0, lev=SURFACE_IDX).interp(lat=lat, lon=lon).values

            o_s, m_s = calculate_speed(o_u, o_v), calculate_speed(m_u, m_v)
            rec = {'case_date': case_date.strftime('%Y-%m-%d'), 'forecast_day': day}
            
            rec['u_bias'], rec['u_mae'], rec['u_rmse'] = calc_metrics(m_u, o_u, w2)
            rec['v_bias'], rec['v_mae'], rec['v_rmse'] = calc_metrics(m_v, o_v, w2)
            rec['s_bias'], rec['s_mae'], rec['s_rmse'] = calc_metrics(m_s, o_s, w2)
            rec['pass_rate'] = calc_pass_rate(m_s, o_s)
            
            for r_key, mask in reg_masks.items():
                for var, m_d, o_d in [('s', m_s, o_s), ('u', m_u, o_u), ('v', m_v, o_v)]:
                    b, mae, r = calc_metrics(m_d, o_d, w2, mask)
                    rec[f'{r_key}_{var}_Bias'], rec[f'{r_key}_{var}_MAE'], rec[f'{r_key}_{var}_RMSE'] = b, mae, r
            results.append(rec)
        except: continue
    return results

def main():
    all_cases = sorted(glob.glob(os.path.join(MOD_BASE_PATH, "case_*_10km")))
    target = [c for c in all_cases if START_DATE <= os.path.basename(c).split('_')[1] <= END_DATE]
    
    if not target:
        print("❌ 未找到有效 Case！")
        return

    final = []
    total = len(target)
    with mp.Pool(CPU_NUM) as pool:
        # 🎯 纯净版进度条
        for i, res in enumerate(pool.imap_unordered(process_single_case, target)):
            if res: final.extend(res)
            if (i + 1) % max(int(total / 10), 1) == 0 or (i + 1) == total:
                print(f"    -> Currents 进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)", flush=True)

    if not final: return
    df = pd.DataFrame(final).sort_values(['case_date', 'forecast_day'])
    # 🎯 统一存入 data 文件夹
    out = os.path.join(DATA_OUT_DIR, f"Currents_Stats_Full_{START_DATE}-{END_DATE}.csv")
    df.to_csv(out, index=False)

if __name__ == "__main__": main()