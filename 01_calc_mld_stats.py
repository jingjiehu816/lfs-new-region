# /data03/hjj/hjj/LFS-new/newwork/region/01_calc_mld_stats.py
import os, glob, re, warnings
import numpy as np, pandas as pd, xarray as xr
import multiprocessing as mp

# 🎯 导入终极配置
from config_regions import CPU_NUM, DATA_OUT_DIR, REGIONS

warnings.filterwarnings('ignore')

# --- 本地配置 ---
INPUT_ROOT = '/data03/hjj/hjj/LFS-new/mld2/mod/'

def process_single_case(case_dir):
    try:
        case_date_str = os.path.basename(case_dir).split('_')[1]
    except: return []

    nc_files = glob.glob(os.path.join(case_dir, 'mld_day*.nc'))
    if not nc_files: return []

    results = []
    for nc_file in nc_files:
        try:
            day_match = re.search(r'day(\d{2})_', os.path.basename(nc_file))
            if not day_match: continue
            
            rec = {'case_date': case_date_str, 'forecast_day': int(day_match.group(1))}

            with xr.open_dataset(nc_file, decode_times=False) as ds:
                diff, lat, lon = ds['diff'].values, ds['lat'].values, ds['lon'].values

            lon_2d, lat_2d = np.meshgrid(lon, lat)
            w_2d = np.cos(np.radians(lat_2d))

            for reg_info in REGIONS.values():
                r_key = reg_info['short_name']
                lon_norm = np.mod(lon_2d, 360)
                mask = (lon_norm >= reg_info['lon'][0]) & (lon_norm <= reg_info['lon'][1]) & \
                       (lat_2d >= reg_info['lat'][0]) & (lat_2d <= reg_info['lat'][1])

                valid_mask = mask & ~np.isnan(diff)
                
                if np.sum(valid_mask) > 0:
                    w, d = w_2d[valid_mask], diff[valid_mask]
                    sw = np.sum(w)
                    if sw > 0:
                        bias = np.sum(d * w) / sw
                        mae  = np.sum(np.abs(d) * w) / sw 
                        rmse = np.sqrt(np.sum((d**2) * w) / sw)
                    else: bias = mae = rmse = np.nan
                else: bias = mae = rmse = np.nan

                rec[f'{r_key}_Bias'] = bias
                rec[f'{r_key}_MAE']  = mae 
                rec[f'{r_key}_RMSE'] = rmse

            results.append(rec)
        except Exception: continue
    return results

def main():
    all_case_dirs = sorted(glob.glob(os.path.join(INPUT_ROOT, "case_*_10km")))
    total_cases = len(all_case_dirs)
    
    if total_cases == 0:
        print(f"❌ 未找到 MLD Case 文件夹！")
        return
        
    final_results = []
    with mp.Pool(CPU_NUM) as pool:
        # 🎯 纯净版进度条
        for i, res in enumerate(pool.imap_unordered(process_single_case, all_case_dirs)):
            if res: final_results.extend(res)
            if (i + 1) % max(int(total_cases / 10), 1) == 0 or (i + 1) == total_cases:
                print(f"    -> MLD 进度: {i+1}/{total_cases} ({(i+1)/total_cases*100:.1f}%)", flush=True)

    # 🎯 防空列表崩溃 (彻底解决 KeyError: 'case_date')
    if not final_results:
        print("⚠️ 警告：未提取到任何有效的 MLD 数据，跳过保存。")
        return

    df = pd.DataFrame(final_results).sort_values(by=['case_date', 'forecast_day'])
    csv_out = os.path.join(DATA_OUT_DIR, 'MLD_Regions_Stats.csv')
    df.to_csv(csv_out, index=False)

if __name__ == "__main__":
    main()