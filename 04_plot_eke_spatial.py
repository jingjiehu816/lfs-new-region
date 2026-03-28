# /data03/hjj/hjj/LFS-new/newwork/region/04_plot_eke_spatial.py
import os, xarray as xr, numpy as np, matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR
import warnings
warnings.filterwarnings('ignore')

def plot_eke_spatial_for_region(reg_key, reg_info):
    # 🎯 自动读取对应的季节空间场 NC
    nc_file = os.path.join(DATA_OUT_DIR, 'Spatial_EKE_Map_Summer.nc')
    if not os.path.exists(nc_file): return
    
    ds = xr.open_dataset(nc_file)
    # 根据 config 中的经纬度范围裁剪
    sub = ds.sel(lat=slice(reg_info['lat'][0]-2, reg_info['lat'][2]+2), 
                 lon=slice(reg_info['lon'][0]-2, reg_info['lon'][1]+2))

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), subplot_kw={'projection': ccrs.PlateCarree()})
    
    # 子图配置：Bias 和 RMSE
    plots = [('mean_bias', 'EKE Bias (cm²/s²)', 'RdBu_r', -200, 200), 
             ('rmse', 'EKE RMSE (cm²/s²)', 'YlOrRd', 0, 400)]
    
    for i, (var, title, cmap, vmin, vmax) in enumerate(plots):
        ax = axes[i]
        im = sub[var].plot(ax=ax, transform=ccrs.PlateCarree(), cmap=cmap, vmin=vmin, vmax=vmax, add_colorbar=False)
        ax.add_feature(cfeature.COASTLINE); ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.set_title(f"{reg_info['short_name']} {title}", weight='bold')
        plt.colorbar(im, ax=ax, orientation='vertical', shrink=0.7, pad=0.02)
        gl = ax.gridlines(draw_labels=True, ls='--', alpha=0.5); gl.top_labels = gl.right_labels = False

    out_name = f"Spatial_EKE_{reg_key}_Map.png"
    plt.savefig(os.path.join(PLOT_OUT_DIR, out_name), dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    for k, v in REGIONS.items():
        plot_eke_spatial_for_region(k, v)