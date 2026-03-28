# /data03/hjj/hjj/LFS-new/newwork/region/01_calc_eke.py
import os, glob, time, random, warnings
import numpy as np, pandas as pd, xarray as xr
import multiprocessing as mp
from datetime import datetime, timedelta

# 🎯 导入终极配置
from config_regions import CPU_NUM, START_DATE, END_DATE, DATA_OUT_DIR, REGIONS

warnings.filterwarnings('ignore')

# --- 本地配置 ---
MAX_WAIT_SECONDS = 5
OBS_BASE_PATH = '/data04/LFS/diag/OSCAR/'
MOD_BASE_PATH = '/data04/LFS/LFSv1.0/ext_fct/10km/'
TMP_NC_PATH = os.path.join(DATA_OUT_DIR, 'tmp_2d')
CLIM_FILE = '/data03/hjj/hjj/LFS-new/newwork/OSCAR_clim_12months_FINAL.nc'
os.makedirs(TMP_NC_PATH, exist_ok=True)

global_clim, global_grid = {}, {}

def init_worker(clim_dict, grid_dict):
    global global_clim, global_grid
    global_clim, global_grid = clim_dict, grid_dict

def get_region_mask(lon_2d, lat_2d, bounds):
    return (lon_2d >= bounds['lon'][0]) & (lon_2d <= bounds['lon'][1]) & \
           (lat_2d >= bounds['lat'][0]) & (lat_2d <= bounds['lat'][1])

def calc_eke(u, v, u_clim, v_clim):
    return 0.5 * ((u - u_clim)**2 + (v - v_clim)**2) * 10000 

def process_single_case(case_dir):
    time.sleep(random.uniform(0, MAX_WAIT_SECONDS))
    try:
        case_date = datetime.strptime(os.path.basename(case_dir).split('_')[1], '%Y%m%d')
    except: return None

    month = case_date.month
    if month in [6, 7]: season = 'Summer'
    elif month in [12, 1]: season = 'Winter'
    else: return None

    results_1d = []
    grid_shape = global_grid['shape']
    sum_bias, sum_mse, sum_obs, sum_mod, valid_cnt = (np.zeros(grid_shape) for _ in range(5))

    for day_idx in range(1, 31):
        fcst_date = case_date + timedelta(days=day_idx - 1)
        valid_month_idx = fcst_date.month - 1
        
        obs_f = os.path.join(OBS_BASE_PATH, f"oscar_currents_interim_{fcst_date.strftime('%Y%m%d')}.nc")
        case_mod_d_str = fcst_date.strftime('%Y-%m-%d')
        uu_f = os.path.join(case_dir, f"uu-{case_mod_d_str}_10km.nc")
        vv_f = os.path.join(case_dir, f"vv-{case_mod_d_str}_10km.nc")

        if not (os.path.exists(obs_f) and os.path.exists(uu_f) and os.path.exists(vv_f)): continue

        try:
            with xr.open_dataset(obs_f, decode_times=False) as ds_o:
                obs_u, obs_v = ds_o['u'][0].values, ds_o['v'][0].values
                if obs_u.shape != grid_shape: obs_u, obs_v = obs_u.T, obs_v.T
            
            with xr.open_dataset(uu_f, decode_times=False) as ds_u, \
                 xr.open_dataset(vv_f, decode_times=False) as ds_v:
                mod_u = ds_u['uu'][0, 0].interp(lat=global_grid['lat'], lon=global_grid['lon']).values
                mod_v = ds_v['vv'][0, 0].interp(lat=global_grid['lat'], lon=global_grid['lon']).values

            u_c, v_c = global_clim['u'][valid_month_idx], global_clim['v'][valid_month_idx]
            obs_eke = calc_eke(obs_u, obs_v, u_c, v_c)
            mod_eke = calc_eke(mod_u, mod_v, u_c, v_c)
            bias_2d = mod_eke - obs_eke
            
            m_val = ~np.isnan(bias_2d)
            sum_bias[m_val] += bias_2d[m_val]
            sum_mse[m_val]  += bias_2d[m_val]**2
            sum_obs[m_val]  += obs_eke[m_val]
            sum_mod[m_val]  += mod_eke[m_val]
            valid_cnt[m_val] += 1

            rec = {'season': season, 'case_date': case_date.strftime('%Y%m%d'), 'forecast_day': day_idx}
            for reg_name, reg_mask in global_grid['masks'].items():
                m = m_val & reg_mask
                if np.sum(m) > 0:
                    rec[f'{reg_name}_obs_eke'] = np.nanmean(obs_eke[m])
                    rec[f'{reg_name}_mod_eke'] = np.nanmean(mod_eke[m])
                    rec[f'{reg_name}_bias']    = np.nanmean(bias_2d[m])
                    rec[f'{reg_name}_rmse']    = np.sqrt(np.nanmean(bias_2d[m]**2))
                    rec[f'{reg_name}_mae']     = np.nanmean(np.abs(bias_2d[m]))
                else:
                    rec[f'{reg_name}_obs_eke'] = np.nan
            results_1d.append(rec)
        except Exception: continue
            
    if results_1d:
        with np.errstate(invalid='ignore'):
            ds_out = xr.Dataset({
                'mean_bias': (['lat', 'lon'], sum_bias / valid_cnt),
                'rmse':      (['lat', 'lon'], np.sqrt(sum_mse / valid_cnt)),
                'obs_eke':   (['lat', 'lon'], sum_obs / valid_cnt),
                'mod_eke':   (['lat', 'lon'], sum_mod / valid_cnt),
                'count':     (['lat', 'lon'], valid_cnt)
            }, coords={'lat': global_grid['lat'], 'lon': global_grid['lon']})
            ds_out.to_netcdf(os.path.join(TMP_NC_PATH, f"eke_2d_{case_date.strftime('%Y%m%d')}_{season}.nc"))

    return results_1d

def main():
    ds_clim = xr.open_dataset(CLIM_FILE).load()
    lon_arr, lat_arr = ds_clim['lon'].values, ds_clim['lat'].values
    lon_2d, lat_2d = np.meshgrid(lon_arr, lat_arr)
    
    clim_dict = {'u': ds_clim['u'].values, 'v': ds_clim['v'].values}
    grid_dict = {
        'lon': lon_arr, 'lat': lat_arr, 'shape': (len(lat_arr), len(lon_arr)),
        # 🎯 适配新区域
        'masks': {v['short_name']: get_region_mask(lon_2d, lat_2d, v) for k, v in REGIONS.items()}
    }
    ds_clim.close()

    all_cases = sorted(glob.glob(os.path.join(MOD_BASE_PATH, "case_*_10km")))
    target_cases = [c for c in all_cases if START_DATE <= os.path.basename(c).split('_')[1] <= END_DATE]

    if not target_cases: return

    final_1d = []
    total = len(target_cases)
    with mp.Pool(CPU_NUM, initializer=init_worker, initargs=(clim_dict, grid_dict)) as pool:
        # 🎯 纯净版进度条
        for i, res in enumerate(pool.imap_unordered(process_single_case, target_cases)):
            if res: final_1d.extend(res)
            if (i + 1) % max(int(total / 10), 1) == 0 or (i + 1) == total:
                print(f"    -> EKE 进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)", flush=True)

    df = pd.DataFrame(final_1d).dropna(subset=['case_date'])
    for season in ['Summer', 'Winter']:
        df_season = df[df['season'] == season]
        if not df_season.empty:
            df_season.to_csv(os.path.join(DATA_OUT_DIR, f'EKE_TimeSeries_{season}.csv'), index=False)

    for season in ['Summer', 'Winter']:
        nc_files = glob.glob(os.path.join(TMP_NC_PATH, f"eke_2d_*_{season}.nc"))
        if not nc_files: continue
        ds_all = xr.open_mfdataset(nc_files, combine='nested', concat_dim='case')
        tot_cnt = ds_all['count'].sum(dim='case')
        ds_mean = (ds_all[['mean_bias', 'rmse', 'obs_eke', 'mod_eke']] * ds_all['count']).sum(dim='case') / tot_cnt
        ds_mean.to_netcdf(os.path.join(DATA_OUT_DIR, f'Spatial_EKE_Map_{season}.nc'))

    os.system(f"rm -rf {TMP_NC_PATH}")

if __name__ == "__main__": main()