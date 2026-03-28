# /data03/hjj/hjj/LFS-new/newwork/region/00_plot_study_regions.py
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import warnings
warnings.filterwarnings('ignore')

# 🎯 从 config_regions 导入配置
from config_regions import REGIONS, PLOT_OUT_DIR

def plot_study_regions():
    fig = plt.figure(figsize=(12, 8), dpi=300)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=140))
    ax.set_extent([100, 185, -5, 55], crs=ccrs.PlateCarree())

    # 底图
    ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='k', linewidth=0.5, zorder=2)
    ax.add_feature(cfeature.OCEAN, facecolor='aliceblue', zorder=1)
    ax.coastlines(linewidth=0.8, zorder=3)

    # 遍历配置字典画框
    for key, info in REGIONS.items():
        lw = 2.5 if key == 'WPac' else 2
        zorder = 4 if key == 'WPac' else 5
        ax.plot(info['lon'], info['lat'], color=info['color'], linestyle=info['linestyle'], 
                linewidth=lw, transform=ccrs.PlateCarree(), label=info['name'], zorder=zorder)

    # 文本标注
    ax.text(113, 13, 'SCS', fontweight='bold', fontsize=12, transform=ccrs.PlateCarree(), color='red', zorder=6)
    ax.text(128, 26, 'Kuroshio', fontweight='bold', fontsize=12, transform=ccrs.PlateCarree(), color='blue', zorder=6)
    ax.text(150, 35, 'Kuroshio Ext.', fontweight='bold', fontsize=12, transform=ccrs.PlateCarree(), color='darkorange', zorder=6)
    ax.text(165, 10, 'Western Pacific', fontweight='bold', fontsize=14, transform=ccrs.PlateCarree(), color='purple', alpha=0.7, zorder=6)

    # 网格线
    gl = ax.gridlines(draw_labels=True, linestyle=':', linewidth=0.5, color='gray', alpha=0.7)
    gl.top_labels = gl.right_labels = False
    gl.xformatter, gl.yformatter = LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    gl.xlabel_style, gl.ylabel_style = {'size': 11}, {'size': 11}

    # 图例放右侧外边框
    plt.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), framealpha=0.9, fontsize=11)
    plt.title('Defined Study Regions for Ocean Model Evaluation', pad=20, fontsize=16, fontweight='bold')

    # 保存
    out_file = os.path.join(PLOT_OUT_DIR, '00_study_regions_map.png')
    plt.savefig(out_file, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✅ 区域示意图已保存：{out_file}")

if __name__ == '__main__':
    plot_study_regions()