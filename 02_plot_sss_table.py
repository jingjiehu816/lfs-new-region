# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_sss_table.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR 
import warnings
warnings.filterwarnings('ignore')

INPUT_CSV = os.path.join(DATA_OUT_DIR, 'SSS_Evaluation_20230101-20241231.csv')
TIME_PERIODS = {'1-7 d': range(1, 8), '8-15 d': range(8, 16), '16-30 d': range(16, 31)}
PERIODS = list(TIME_PERIODS.keys())

def get_data():
    if not os.path.exists(INPUT_CSV): return None
    df = pd.read_csv(INPUT_CSV)
    rows = []
    for reg_key, reg_info in REGIONS.items():
        row = [reg_info['name']]
        for metric in ['Bias', 'MAE', 'RMSE']:
            for days in TIME_PERIODS.values():
                col = f'{reg_key}_{metric}'
                val = df[df['forecast_day'].isin(days)][col].mean() if col in df.columns else np.nan
                row.append(val)
        rows.append(row)
    return rows

def draw(data):
    w_f, w_r = 0.25, (1.0 - 0.25) / 9
    col_w, x_pos = [w_f] + [w_r]*9, [0]
    x_pos = [0] + list(np.cumsum(col_w))
    x_c = [(x_pos[i] + x_pos[i+1])/2 for i in range(len(col_w))]
    rows_n = 2 + len(data)
    fig, ax = plt.subplots(figsize=(14, rows_n * 0.8), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, rows_n); ax.axis('off')

    for i, row in enumerate(reversed(data)):
        y = i + 0.5
        ax.text(0.01, y, row[0], ha='left', va='center', weight='bold', size=12)
        for j, v in enumerate(row[1:]):
            ax.text(x_c[j+1], y, f"{v:.3f}" if not np.isnan(v) else "N/A", ha='center', va='center', size=12)

    y1, y2 = len(data)+0.5, len(data)+1.5
    ax.text(x_c[0], y1, "Study Region", ha='center', va='center', weight='bold', size=13)
    for j in range(9): ax.text(x_c[j+1], y1, PERIODS[j%3], ha='center', va='center', weight='bold', size=11)
    for k, t in enumerate(['Bias', 'MAE', 'RMSE']):
        ax.text((x_pos[1+k*3]+x_pos[4+k*3])/2, y2, f"{t} (PSU)", ha='center', va='center', weight='bold', size=14)

    ax.plot([0,1],[rows_n,rows_n],'k',lw=2); ax.plot([0,1],[len(data),len(data)],'k',lw=1); ax.plot([0,1],[0,0],'k',lw=2)
    for i in range(3): ax.plot([x_pos[1+i*3]+0.005, x_pos[4+i*3]-0.005],[len(data)+1,len(data)+1],'k',lw=1)
    
    plt.title('Sea Surface Salinity (SSS) Evaluation', pad=25, size=16, weight='bold')
    plt.savefig(os.path.join(PLOT_OUT_DIR, 'Table_SSS_Combined.png'), bbox_inches='tight')

if __name__ == '__main__':
    d = get_data()
    if d: draw(d)