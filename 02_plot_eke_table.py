# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_eke_table.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR 
import warnings
warnings.filterwarnings('ignore')

TIME_PERIODS = {'1-7 d': range(1, 8), '8-15 d': range(8, 16), '16-30 d': range(16, 31)}
PERIODS = list(TIME_PERIODS.keys())

def get_data(metric):
    f_summer = os.path.join(DATA_OUT_DIR, 'EKE_TimeSeries_Summer.csv')
    f_winter = os.path.join(DATA_OUT_DIR, 'EKE_TimeSeries_Winter.csv')
    if not (os.path.exists(f_summer) and os.path.exists(f_winter)): return None
    
    dfs = pd.read_csv(f_summer)
    dfw = pd.read_csv(f_winter)
    rows = []
    for r_key, r_info in REGIONS.items():
        row = [r_info['name']]
        # 依次填入夏季(1-7, 8-15, 16-30)和冬季
        for df in [dfs, dfw]:
            for days in TIME_PERIODS.values():
                col = f'{r_key}_{metric.lower()}' # EKE 计算脚本通常存为 _bias, _mae, _rmse
                val = df[df['forecast_day'].isin(days)][col].mean() if col in df.columns else np.nan
                row.append(val)
        rows.append(row)
    return rows

def draw(data, metric):
    w_f, w_rest = 0.28, (1.0 - 0.28) / 6
    x_pos = [0] + list(np.cumsum([w_f] + [w_rest]*6))
    x_centers = [(x_pos[i] + x_pos[i+1])/2 for i in range(len(x_pos)-1)]

    total_rows = 2 + len(data)
    fig, ax = plt.subplots(figsize=(11, total_rows * 0.7 + 0.5), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, total_rows); ax.axis('off')

    for i, row in enumerate(reversed(data)):
        y_c = i + 0.5
        ax.text(0.01, y_c, row[0], ha='left', va='center', weight='bold', size=12)
        for j, val in enumerate(row[1:]):
            ax.text(x_centers[j+1], y_c, f"{val:.1f}", ha='center', va='center', size=12)

    y_sub, y_super = len(data) + 0.5, len(data) + 1.5
    ax.text(x_centers[0], y_sub, "Study Region", ha='center', weight='bold', size=13)
    for j in range(6): ax.text(x_centers[j+1], y_sub, PERIODS[j % 3], ha='center', weight='bold', size=11)

    ax.text((x_pos[1] + x_pos[4]) / 2, y_super, "Summer", ha='center', weight='bold', size=15)
    ax.text((x_pos[4] + x_pos[7]) / 2, y_super, "Winter", ha='center', weight='bold', size=15)

    ax.plot([0, 1], [total_rows, total_rows], 'k', lw=2)
    ax.plot([x_pos[1]+0.01, x_pos[4]-0.01], [len(data)+1, len(data)+1], 'k', lw=1)
    ax.plot([x_pos[4]+0.01, x_pos[7]-0.01], [len(data)+1, len(data)+1], 'k', lw=1)
    ax.plot([0, 1], [len(data), len(data)], 'k', lw=1)
    ax.plot([0, 1], [0, 0], 'k', lw=2)

    plt.title(f'EKE {metric.upper()} Evaluation (cm²/s²)', pad=20, fontsize=16, weight='bold')
    plt.savefig(os.path.join(PLOT_OUT_DIR, f'Table_EKE_{metric}_Combined.png'), bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    for m in ['bias', 'mae', 'rmse']:
        d = get_data(m)
        if d: draw(d, m)