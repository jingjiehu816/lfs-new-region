# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_ts_profile_table.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR 

INPUT_CSV = os.path.join(DATA_OUT_DIR, 'TS_Profile_Regions_Stats.csv')
LAYERS = ['0-300m', '300-500m', '500-1000m']

def get_ts_data(var_type='T'): # T or S
    if not os.path.exists(INPUT_CSV): return None
    df = pd.read_csv(INPUT_CSV)
    final_rows = []
    for reg_key, reg_info in REGIONS.items():
        for ly in LAYERS:
            row_name = f"{reg_info['name']} ({ly})"
            row = [row_name]
            for m in ['Bias', 'MAE', 'RMSE']:
                col = f"{reg_key}_{var_type}_{m}_{ly}"
                val = df[col].mean() if col in df.columns else np.nan
                row.append(val)
            final_rows.append(row)
    return final_rows

def draw_table(data, var_label, unit):
    rows_n = len(data) + 1
    fig, ax = plt.subplots(figsize=(10, rows_n * 0.6), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, rows_n); ax.axis('off')
    
    x_c = [0.15, 0.45, 0.65, 0.85]
    headers = ['Region (Layer)', 'Bias', 'MAE', 'RMSE']
    
    # 画表头
    for j, h in enumerate(headers):
        ax.text(x_c[j], rows_n-0.5, h, ha='center', weight='bold')
    
    # 画内容
    for i, row in enumerate(reversed(data)):
        for j, val in enumerate(row):
            txt = f"{val:.4f}" if isinstance(val, float) else str(val)
            ax.text(x_c[j], i+0.5, txt, ha='center')

    ax.plot([0,1], [rows_n, rows_n], 'k', lw=2)
    ax.plot([0,1], [rows_n-1, rows_n-1], 'k', lw=1)
    ax.plot([0,1], [0,0], 'k', lw=2)
    
    plt.title(f'TS Profile {var_label} Stats {unit}', pad=20, weight='bold')
    plt.savefig(os.path.join(PLOT_OUT_DIR, f'Table_Profile_{var_label}.png'))

if __name__ == '__main__':
    for v, u in zip(['T', 'S'], ['(℃)', '(PSU)']):
        d = get_ts_data(v)
        if d: draw_table(d, v, u)