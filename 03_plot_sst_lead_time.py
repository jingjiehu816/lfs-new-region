# /data03/hjj/hjj/LFS-new/newwork/region/03_plot_sst_lead_time.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR
import warnings
warnings.filterwarnings('ignore')

VAR_NAME = 'SST'
INPUT_CSV = os.path.join(DATA_OUT_DIR, f'SST_Evaluation_20230101-20241231.csv')

def calc_bxp(arr):
    arr = arr.dropna().values
    if len(arr) == 0: return None
    return {'med': np.percentile(arr, 50), 'q1': np.percentile(arr, 25), 'q3': np.percentile(arr, 75),
            'whislo': np.percentile(arr, 5), 'whishi': np.percentile(arr, 95), 'fliers': []}

def get_stats():
    if not os.path.exists(INPUT_CSV): return None
    df = pd.read_csv(INPUT_CSV)
    all_s = []
    for d in range(1, 31):
        df_d = df[df['forecast_day'] == d]
        res = {}
        for r_k in REGIONS.keys():
            # 🎯 匹配 SST 脚本中的大写后缀
            for m in ['Bias', 'RMSE', 'MAE']: 
                res[f'{r_k}_{m}'] = calc_bxp(df_d[f'{r_k}_{m}'])
        all_s.append(res)
    return all_s

def draw_reg_panel(ax_top, ax_bot, stats, r_k, title, is_left=False):
    b_box, r_box, m_box = [], [], []
    for i, s in enumerate(stats):
        if s and s[f'{r_k}_Bias']:
            b, r, m = s[f'{r_k}_Bias'].copy(), s[f'{r_k}_RMSE'].copy(), s[f'{r_k}_MAE'].copy()
            for x in [b, r, m]: x['label'] = i+1
            b_box.append(b); r_box.append(r); m_box.append(m)
    
    ax_top.bxp(b_box, positions=np.arange(1,31), patch_artist=True, showfliers=False, widths=0.35,
               boxprops={'facecolor':'lightblue'}, medianprops={'color':'red'})
    ax_top.bxp(r_box, positions=np.arange(1,31)+0.4, patch_artist=True, showfliers=False, widths=0.35,
               boxprops={'facecolor':'lightgreen'}, medianprops={'color':'black'})
    ax_bot.bxp(m_box, positions=np.arange(1,31)+0.2, patch_artist=True, showfliers=False, widths=0.4,
               boxprops={'facecolor':'moccasin'}, medianprops={'color':'darkorange'})
    
    for ax in [ax_top, ax_bot]:
        ax.set_xlim(0, 32); ax.set_xticks([1.2, 7.2, 15.2, 30.2])
        ax.set_xticklabels(['1', '7', '15', '30'], weight='bold')
        ax.grid(axis='y', ls=':', alpha=0.5)
    
    ax_top.set_title(title, weight='bold', size=14)
    ax_top.axhline(0, color='k', ls='--', alpha=0.5)
    if is_left:
        ax_top.set_ylabel('Bias & RMSE (℃)', weight='bold')
        ax_bot.set_ylabel('MAE (℃)', weight='bold')

def main():
    stats = get_stats()
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.15)
    for idx, (r_k, r_i) in enumerate(REGIONS.items()):
        inner_gs = gs[idx // 2, idx % 2].subgridspec(2, 1, hspace=0.1)
        ax_t, ax_b = fig.add_subplot(inner_gs[0]), fig.add_subplot(inner_gs[1])
        draw_reg_panel(ax_t, ax_b, stats, r_k, r_i['name'], is_left=(idx%2==0))
    
    leg = [Line2D([0],[0], color='red', marker='s', markerfacecolor='lightblue', label='Bias'),
           Line2D([0],[0], color='black', marker='s', markerfacecolor='lightgreen', label='RMSE'),
           Line2D([0],[0], color='darkorange', marker='s', markerfacecolor='moccasin', label='MAE')]
    fig.legend(handles=leg, loc='upper center', bbox_to_anchor=(0.5, 0.96), ncol=3, fontsize=12)
    plt.savefig(os.path.join(PLOT_OUT_DIR, f'Boxplot_{VAR_NAME}_LeadTime.png'), dpi=300, bbox_inches='tight')

if __name__ == '__main__': main()