# /data03/hjj/hjj/LFS-new/newwork/region/03_plot_eke_lead_time.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR
import warnings
warnings.filterwarnings('ignore')

# --- 配置 ---
VAR_NAME = 'EKE'
# 适配 EKE 特有的多文件逻辑（取夏季作为代表，或你可以合并文件）
INPUT_CSV = os.path.join(DATA_OUT_DIR, 'EKE_TimeSeries_Summer.csv')

def calc_bxp(arr):
    """计算箱线图统计量"""
    arr = arr.dropna().values
    if len(arr) == 0: return None
    return {'med': np.percentile(arr, 50), 'q1': np.percentile(arr, 25), 'q3': np.percentile(arr, 75),
            'whislo': np.percentile(arr, 5), 'whishi': np.percentile(arr, 95), 'fliers': []}

def get_stats():
    """获取所有区域随预报时效的统计量"""
    if not os.path.exists(INPUT_CSV): return None
    df = pd.read_csv(INPUT_CSV)
    all_s = []
    for d in range(1, 31):
        df_d = df[df['forecast_day'] == d]
        res = {}
        for r_k in REGIONS.keys():
            # 🎯 匹配 EKE 脚本中的列名后缀（小写）
            for m in ['bias', 'rmse', 'mae']: 
                res[f'{r_k}_{m}'] = calc_bxp(df_d[f'{r_k}_{m}'])
        all_s.append(res)
    return all_s

def draw_reg_panel(ax_top, ax_bot, stats, r_k, title, is_left=False):
    """绘制单个区域的上下两层子图"""
    b_box, r_box, m_box = [], [], []
    for i, s in enumerate(stats):
        if s and s[f'{r_k}_bias']:
            b, r, m = s[f'{r_k}_bias'].copy(), s[f'{r_k}_rmse'].copy(), s[f'{r_k}_mae'].copy()
            for x in [b, r, m]: x['label'] = i+1
            b_box.append(b); r_box.append(r); m_box.append(m)
    
    # 上层：Bias & RMSE
    ax_top.bxp(b_box, positions=np.arange(1,31), patch_artist=True, showfliers=False, widths=0.35,
               boxprops={'facecolor':'lightblue'}, medianprops={'color':'red'})
    ax_top.bxp(r_box, positions=np.arange(1,31)+0.4, patch_artist=True, showfliers=False, widths=0.35,
               boxprops={'facecolor':'lightgreen'}, medianprops={'color':'black'})
    
    # 下层：MAE
    ax_bot.bxp(m_box, positions=np.arange(1,31)+0.2, patch_artist=True, showfliers=False, widths=0.4,
               boxprops={'facecolor':'moccasin'}, medianprops={'color':'darkorange'})
    
    # 格式化
    for ax in [ax_top, ax_bot]:
        ax.set_xlim(0, 32); ax.set_xticks([1.2, 7.2, 15.2, 30.2])
        ax.set_xticklabels(['1', '7', '15', '30'], weight='bold')
        ax.grid(axis='y', ls=':', alpha=0.5)
    
    ax_top.set_title(title, weight='bold', size=14)
    ax_top.axhline(0, color='k', ls='--', alpha=0.5)
    if is_left:
        ax_top.set_ylabel('Bias & RMSE', weight='bold')
        ax_bot.set_ylabel('MAE', weight='bold')

def main():
    stats = get_stats()
    if not stats: return
    
    # 🎯 建立 2x2 的区域矩阵，每个区域包含上下两个子图（实际上是 4x2 的 gridspec）
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.15)
    
    for idx, (r_k, r_i) in enumerate(REGIONS.items()):
        # 为每个区域创建嵌套子图
        inner_gs = gs[idx // 2, idx % 2].subgridspec(2, 1, hspace=0.1)
        ax_t = fig.add_subplot(inner_gs[0, 0])
        ax_b = fig.add_subplot(inner_gs[1, 0])
        
        draw_reg_panel(ax_t, ax_b, stats, r_k, r_i['name'], is_left=(idx%2==0))
        if idx >= 2: ax_b.set_xlabel('Forecast Lead Time (Days)', weight='bold')

    # 图例
    leg = [Line2D([0],[0], color='red', marker='s', markerfacecolor='lightblue', label='Bias'),
           Line2D([0],[0], color='black', marker='s', markerfacecolor='lightgreen', label='RMSE'),
           Line2D([0],[0], color='darkorange', marker='s', markerfacecolor='moccasin', label='MAE')]
    fig.legend(handles=leg, loc='upper center', bbox_to_anchor=(0.5, 0.96), ncol=3, frameon=True, fontsize=12)
    
    plt.suptitle(f'{VAR_NAME} Error Distribution by Lead Time', fontsize=20, weight='bold', y=.98)
    out_f = os.path.join(PLOT_OUT_DIR, f'Boxplot_{VAR_NAME}_LeadTime.png')
    plt.savefig(out_f, dpi=300, bbox_inches='tight')
    print(f"✅ {VAR_NAME} 趋势图已生成: {out_f}")

if __name__ == '__main__': main()