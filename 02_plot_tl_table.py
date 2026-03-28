# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_tl_table.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import DATA_OUT_DIR, PLOT_OUT_DIR 
import warnings
warnings.filterwarnings('ignore')

# --- 配置 ---
INPUT_CSV = os.path.join(DATA_OUT_DIR, 'Thermocline_Stats_Full.csv')
TIME_PERIODS = {'1-7 d': range(1, 8), '8-15 d': range(8, 16), '16-30 d': range(16, 31)}
PERIODS = list(TIME_PERIODS.keys())
VARS = {'upper_depth': 'Upper Depth', 'lower_depth': 'Lower Depth', 'thickness': 'Thickness'}

def get_tl_data():
    """提取温跃层三个关键变量的数据"""
    if not os.path.exists(INPUT_CSV):
        print(f"❌ 找不到数据文件: {INPUT_CSV}"); return None
    
    df = pd.read_csv(INPUT_CSV)
    data_rows = []
    
    for v_key, v_name in VARS.items():
        row = [v_name]
        # 🎯 遍历 Bias, MAE, RMSE
        for metric in ['Bias', 'MAE', 'RMSE']:
            for days in TIME_PERIODS.values():
                col_name = f'{v_key}_{metric}'
                # 兼容温跃层脚本特有的列名 'Day'
                day_col = 'Day' if 'Day' in df.columns else 'forecast_day'
                val = df[df[day_col].isin(days)][col_name].mean() if col_name in df.columns else np.nan
                row.append(val)
        data_rows.append(row)
    return data_rows

def draw_combined_table(data):
    """绘制三段式 TL 评估表"""
    w_first, w_rest = 0.25, (1.0 - 0.25) / 9
    col_widths = [w_first] + [w_rest]*9
    x_pos = [0] + list(np.cumsum(col_widths))
    x_centers = [(x_pos[i] + x_pos[i+1])/2 for i in range(len(col_widths))]

    total_rows = 2 + len(data)
    fig, ax = plt.subplots(figsize=(13, total_rows * 0.8 + 0.5), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, total_rows); ax.axis('off')

    for i, row in enumerate(reversed(data)):
        y_center = i + 0.5
        ax.text(0.01, y_center, row[0], ha='left', va='center', weight='bold', fontsize=12)
        for j, val in enumerate(row[1:]):
            txt = f"{val:.2f}" if not np.isnan(val) else "N/A"
            ax.text(x_centers[j+1], y_center, txt, ha='center', va='center', fontsize=12)

    y_sub, y_super = len(data) + 0.5, len(data) + 1.5
    ax.text(x_centers[0], y_sub, "Variable", ha='center', weight='bold', fontsize=13)
    for j in range(9):
        ax.text(x_centers[j+1], y_sub, PERIODS[j % 3], ha='center', weight='bold', fontsize=11)

    metrics = ["Bias (m)", "MAE (m)", "RMSE (m)"]
    for i, m_text in enumerate(metrics):
        ax.text((x_pos[1+i*3] + x_pos[4+i*3])/2, y_super, m_text, ha='center', weight='bold', fontsize=14)

    kws = {'color': 'k', 'solid_capstyle': 'butt'}
    ax.plot([0, 1], [total_rows, total_rows], lw=2, **kws)
    for i in range(3):
        ax.plot([x_pos[1+i*3]+0.005, x_pos[4+i*3]-0.005], [len(data)+1, len(data)+1], lw=1, **kws)
    ax.plot([0, 1], [len(data), len(data)], lw=1, **kws)
    ax.plot([0, 1], [0, 0], lw=2, **kws)

    plt.title('Thermocline Structure Forecast Evaluation', pad=25, fontsize=16, weight='bold')
    out_file = os.path.join(PLOT_OUT_DIR, 'Table_Thermocline_Combined.png')
    plt.savefig(out_file, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f"✅ 温跃层评估表格已生成: {out_file}")

if __name__ == '__main__':
    data = get_tl_data()
    if data: draw_combined_table(data)