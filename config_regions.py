# /data03/hjj/hjj/LFS-new/newwork/region/config_regions.py
import os

# ================= 1. 全局计算参数 (统一在此修改) =================
CPU_NUM = 32                     # 全局统一并行核心数
START_DATE = '20230101'          # 评估起始时间
END_DATE = '20241231'            # 评估结束时间

# ================= 2. 全局路径配置 =================
BASE_WORK_DIR = '/data03/hjj/hjj/LFS-new/newwork/region'

# 🎯 所有的 CSV 和中间 NC 文件，统一存入 data 目录
DATA_OUT_DIR = os.path.join(BASE_WORK_DIR, 'data')  
# 🎯 所有的最终图片，统一存入 plot 目录
PLOT_OUT_DIR = os.path.join(BASE_WORK_DIR, 'plot')

os.makedirs(DATA_OUT_DIR, exist_ok=True)
os.makedirs(PLOT_OUT_DIR, exist_ok=True)

# ================= 3. 统一区域定义 =================
REGIONS = {
    'SCS': {
        'name': 'South China Sea', 'short_name': 'SCS',
        'lon': [105, 121, 121, 105, 105], 'lat': [3, 3, 23, 23, 3],
        'color': 'red', 'linestyle': '-'
    },
    'Kuro': {
        'name': 'Kuroshio Main Stream', 'short_name': 'Kuro',
        'lon': [120, 140, 140, 120, 120], 'lat': [18, 18, 35, 35, 18],
        'color': 'blue', 'linestyle': '-'
    },
    'KE': {
        'name': 'Kuroshio Extension', 'short_name': 'KE',
        'lon': [140, 165, 165, 140, 140], 'lat': [30, 30, 40, 40, 30],
        'color': 'darkorange', 'linestyle': '-'
    },
    'WPac': {
        'name': 'Western Pacific', 'short_name': 'WPac',
        'lon': [120, 180, 180, 120, 120], 'lat': [0, 0, 50, 50, 0],
        'color': 'purple', 'linestyle': '--'
    }
}