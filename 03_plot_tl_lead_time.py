# /data03/hjj/hjj/LFS-new/newwork/region/03_plot_tl_lead_time.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from config_regions import DATA_OUT_DIR, PLOT_OUT_DIR
import warnings
warnings.filterwarnings('ignore')

INPUT_CSV = os.path.join(DATA_OUT_DIR, 'Thermocline_Stats_Full.csv')
VARS = {
    'upper_depth': {'title': 'Upper Boundary Depth', 'l_top': 'A', 'l_bot': 'D'},
    'lower_depth': {'title': 'Lower Boundary Depth', 'l_top': 'B', 'l_bot': 'E'},
    'thickness':   {'title': 'Thermocline Thickness', 'l_top': 'C', 'l_bot': 'F'}
}

def calc_bxp(arr):
    arr = arr.dropna().values
    return {'med': np.percentile(arr, 50), 'q1': np.percentile(arr, 25), 'q3': np.percentile(arr, 75),
            'whislo': np.percentile(arr, 5), 'whishi': np.percentile(arr, 95), 'fliers': []} if len(arr)>0 else None

def get_stats():
    if not os.path.exists(INPUT_CSV): return None
    df = pd.read_csv(INPUT_CSV)
    day_col = 'Day' if 'Day' in df.columns else 'forecast_day'
    all_s = []
    for d in range(1, 31):
        df_d = df[df[day_col] == d]
        res = {}
        for v in VARS.keys():
            for m in ['Bias', 'RMSE', 'MAE']: res[f'{v}_{m}'] = calc_bxp(df_d[f'{v}_{m}'])
        all_s.append(res)
    return all_s

def main():
    stats = get_stats()
    fig, axes = plt.subplots(2, 3, figsize=(22, 10), hspace=0.25, wspace=0.15)
    for i, (v_k, v_i) in enumerate(VARS.items()):
        # Top: Bias/RMSE
        b_box, r_box = [], []
        for d, s in enumerate(stats):
            if s and s[f'{v_k}_Bias']:
                b, r = s[f'{v_k}_Bias'].copy(), s[f'{v_k}_RMSE'].copy()
                b['label'] = r['label'] = d+1
                b_box.append(b); r_box.append(r)
        axes[0,i].bxp(b_box, positions=np.arange(1,31), patch_artist=True, showfliers=False, widths=0.35, boxprops={'facecolor':'lightblue'}, medianprops={'color':'red'})
        axes[0,i].bxp(r_box, positions=np.arange(1,31)+0.4, patch_artist=True, showfliers=False, widths=0.35, boxprops={'facecolor':'lightgreen'}, medianprops={'color':'black'})
        axes[0,i].set_title(v_i['title'], weight='bold', size=15)
        
        # Bottom: MAE
        m_box = []
        for d, s in enumerate(stats):
            if s and s[f'{v_k}_MAE']:
                m = s[f'{v_k}_MAE'].copy(); m['label'] = d+1; m_box.append(m)
        axes[1,i].bxp(m_box, positions=np.arange(1,31)+0.2, patch_artist=True, showfliers=False, widths=0.4, boxprops={'facecolor':'moccasin'}, medianprops={'color':'darkorange'})
        
        for ax in [axes[0,i], axes[1,i]]:
            ax.set_xlim(0, 32); ax.set_xticks([1, 7, 15, 30]); ax.grid(axis='y', ls=':', alpha=0.5)

    axes[0,0].set_ylabel('Bias & RMSE (m)', weight='bold'); axes[1,0].set_ylabel('MAE (m)', weight='bold')
    plt.savefig(os.path.join(PLOT_OUT_DIR, 'Boxplot_Thermocline_LeadTime.png'), dpi=300, bbox_inches='tight')

if __name__ == '__main__': main()