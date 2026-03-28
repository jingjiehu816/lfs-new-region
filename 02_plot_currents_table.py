# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_currents_table.py
import os, glob, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR 
import warnings
warnings.filterwarnings('ignore')

# 自动匹配最新的流速 CSV
csv_pattern = os.path.join(DATA_OUT_DIR, 'Currents_Stats_Full_*.csv')
csv_files = sorted(glob.glob(csv_pattern))
INPUT_CSV = csv_files[-1] if csv_files else None

TIME_PERIODS = {'1-7 d': range(1, 8), '8-15 d': range(8, 16), '16-30 d': range(16, 31)}
PERIODS = list(TIME_PERIODS.keys())

def get_data():
    if not INPUT_CSV or not os.path.exists(INPUT_CSV):
        print(f"❌ 找不到数据文件"); return None
    
    df = pd.read_csv(INPUT_CSV)
    data_rows = []
    
    for reg_key, reg_info in REGIONS.items():
        row = [reg_info['name']]
        # 依次提取流速大小 (s) 的 Bias, MAE, RMSE
        for metric in ['Bias', 'MAE', 'RMSE']:
            for days in TIME_PERIODS.values():
                col = f'{reg_key}_s_{metric}'
                val = df[df['forecast_day'].isin(days)][col].mean() if col in df.columns else np.nan
                row.append(val)
        data_rows.append(row)
    return data_rows

def draw(data):
    # 1宽列 + 9数据列
    w_first, w_rest = 0.25, (1.0 - 0.25) / 9
    col_widths = [w_first] + [w_rest]*9
    x_pos = [0] + list(np.cumsum(col_widths))
    x_centers = [(x_pos[i] + x_pos[i+1])/2 for i in range(len(col_widths))]

    total_rows = 2 + len(data)
    fig, ax = plt.subplots(figsize=(14, total_rows * 0.8), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, total_rows); ax.axis('off')

    # 写数据 (流速保留3位小数)
    for i, row in enumerate(reversed(data)):
        y_c = i + 0.5
        ax.text(0.01, y_c, row[0], ha='left', va='center', weight='bold', size=12)
        for j, val in enumerate(row[1:]):
            txt = f"{val:.3f}" if not np.isnan(val) else "N/A"
            ax.text(x_centers[j+1], y_c, txt, ha='center', va='center', size=12)

    # 写表头
    y_sub, y_super = len(data) + 0.5, len(data) + 1.5
    ax.text(x_centers[0], y_sub, "Study Region", ha='center', va='center', weight='bold', size=13)
    for j in range(9): ax.text(x_centers[j+1], y_sub, PERIODS[j % 3], ha='center', va='center', weight='bold', size=11)
    
    # 三段式大标题
    metrics = ["Bias (m/s)", "MAE (m/s)", "RMSE (m/s)"]
    for i, m_text in enumerate(metrics):
        ax.text((x_pos[1+i*3] + x_pos[4+i*3])/2, y_super, m_text, ha='center', va='center', weight='bold', size=14)

    # 画线
    kws = {'color': 'k', 'solid_capstyle': 'butt'}
    ax.plot([0, 1], [total_rows, total_rows], lw=2, **kws)
    for i in range(3): ax.plot([x_pos[1+i*3]+0.005, x_pos[4+i*3]-0.005], [len(data)+1, len(data)+1], lw=1, **kws)
    ax.plot([0, 1], [len(data), len(data)], lw=1, **kws)
    ax.plot([0, 1], [0, 0], lw=2, **kws)

    plt.title('Ocean Surface Currents Speed Evaluation', pad=25, fontsize=16, weight='bold')
    plt.savefig(os.path.join(PLOT_OUT_DIR, 'Table_Currents_Combined.png'), bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    tbl_data = get_data()
    if tbl_data: draw(tbl_data)