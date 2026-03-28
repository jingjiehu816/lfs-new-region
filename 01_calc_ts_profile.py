# /data03/hjj/hjj/LFS-new/newwork/region/01_calc_ts_profile.py
import os, glob, re, warnings
import numpy as np, pandas as pd, xarray as xr
import multiprocessing as mp

# 🎯 导入配置中心
from config_regions import CPU_NUM, DATA_OUT_DIR, REGIONS 

warnings.filterwarnings('ignore')

INPUT_ROOT = '/data03/hjj/hjj/LFS-new/profile'
LAYERS = {'0-300m': (0, 300), '300-500m': (300, 500), '500-1000m': (500, 1000)}
STD_LEVELS = np.array([
    0.5, 2, 3, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 
    90, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 700, 800, 900, 
    1000, 1250, 1500, 1750, 2000
])

def get_layer_weights(levels):
    w = np.zeros_like(levels)
    w[0] = (levels[1] + levels[0])/2
    for i in range(1, len(levels)-1): w[i] = (levels[i+1] - levels[i-1])/2
    w[-1] = levels[-1] - levels[-2]
    return w

LAYER_W = get_layer_weights(STD_LEVELS)

def process_single_nc(nc_file):
    try:
        case_date_str = os.path.basename(os.path.dirname(nc_file)).split('_')[1]  
        lead_match = re.search(r'lead(\d{2})', os.path.basename(nc_file))
        if not lead_match: return None
        
        forecast_day = int(lead_match.group(1)) + 1 
        rec = {'case_date': case_date_str, 'forecast_day': forecast_day}

        with xr.open_dataset(nc_file, decode_times=False) as ds:
            tdif, sdif = ds['tdif_reg'].values, ds['sdif_reg'].values
            awgt, nlon, nlat = ds['awgt'].values, ds['nlon'].values, ds['nlat'].values

        for r_key, reg_info in REGIONS.items():
            nlon_norm = np.mod(nlon, 360)
            reg_mask = (nlon_norm >= reg_info['lon'][0]) & (nlon_norm <= reg_info['lon'][1]) & \
                       (nlat >= reg_info['lat'][0]) & (nlat <= reg_info['lat'][1])
            
            if np.sum(reg_mask) == 0:
                for l_key in LAYERS.keys():
                    for var in ['T', 'S']:
                        for metric in ['Bias', 'RMSE', 'MAE']: rec[f'{r_key}_{var}_{metric}_{l_key}'] = np.nan
                continue
                
            sub_tdif, sub_sdif, sub_awgt = tdif[reg_mask, :], sdif[reg_mask, :], awgt[reg_mask]

            for l_key, (top, bot) in LAYERS.items():
                lev_idx = np.where((STD_LEVELS >= top) & (STD_LEVELS <= bot))[0]
                if len(lev_idx) == 0: continue
                
                sub_thick = LAYER_W[lev_idx]
                
                for var_prefix, dif_data in zip(['T', 'S'], [sub_tdif, sub_sdif]):
                    layer_dif = dif_data[:, lev_idx]
                    
                    valid_z = ~np.isnan(layer_dif)
                    w_z = sub_thick[None, :] * valid_z
                    sum_w_z = np.sum(w_z, axis=1)
                    valid_obs = sum_w_z > 0
                    
                    prof_bias = np.full(layer_dif.shape[0], np.nan)
                    prof_rmse_sq = np.full(layer_dif.shape[0], np.nan)
                    prof_mae = np.full(layer_dif.shape[0], np.nan) 
                    
                    if np.sum(valid_obs) > 0:
                        safe_layer_dif = np.nan_to_num(layer_dif, nan=0.0)
                        v_dif, v_w_z, v_sum_w = safe_layer_dif[valid_obs], w_z[valid_obs], sum_w_z[valid_obs]

                        prof_bias[valid_obs] = np.sum(v_dif * v_w_z, axis=1) / v_sum_w
                        prof_rmse_sq[valid_obs] = np.sum((v_dif**2) * v_w_z, axis=1) / v_sum_w
                        prof_mae[valid_obs] = np.sum(np.abs(v_dif) * v_w_z, axis=1) / v_sum_w 
                    
                    valid_h = ~np.isnan(prof_bias)
                    if np.sum(valid_h) > 0:
                        w_h = sub_awgt[valid_h]
                        total_w_h = np.sum(w_h)
                        if total_w_h > 0:
                            f_bias = np.sum(prof_bias[valid_h] * w_h) / total_w_h
                            f_rmse = np.sqrt(np.sum(prof_rmse_sq[valid_h] * w_h) / total_w_h)
                            f_mae  = np.sum(prof_mae[valid_h] * w_h) / total_w_h
                        else: f_bias = f_rmse = f_mae = np.nan
                    else: f_bias = f_rmse = f_mae = np.nan
                        
                    rec[f'{r_key}_{var_prefix}_Bias_{l_key}'] = f_bias
                    rec[f'{r_key}_{var_prefix}_RMSE_{l_key}'] = f_rmse
                    rec[f'{r_key}_{var_prefix}_MAE_{l_key}']  = f_mae 

        return rec
    except Exception: return None

def main():
    all_nc_files = sorted(glob.glob(os.path.join(INPUT_ROOT, "case_*", "profile_diff_*.nc")))
    total = len(all_nc_files)
    if total == 0: return
        
    final_results = []
    with mp.Pool(CPU_NUM) as pool:
        # 🎯 纯净版进度条 (按块返回结果)
        for i, res in enumerate(pool.imap_unordered(process_single_nc, all_nc_files, chunksize=10)):
            if res: final_results.append(res)
            if (i + 1) % max(int(total / 10), 1) == 0 or (i + 1) == total:
                print(f"    -> TS Profile 进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)", flush=True)

    # 🎯 防崩溃保护
    if not final_results: return

    df = pd.DataFrame(final_results).sort_values(by=['case_date', 'forecast_day'])
    csv_out = os.path.join(DATA_OUT_DIR, 'TS_Profile_Regions_Stats.csv')
    df.to_csv(csv_out, index=False)

if __name__ == "__main__":
    main()