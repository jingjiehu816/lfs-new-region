# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_mld_table.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR 
import warnings
warnings.filterwarnings('ignore')

# --- 配置 ---
INPUT_CSV = os.path.join(DATA_OUT_DIR, 'MLD_Regions_Stats.csv')
TIME_PERIODS = {'1-7 d': range(1, 8), '8-15 d': range(8, 16), '16-30 d': range(16, 31)}
PERIODS = list(TIME_PERIODS.keys())

def get_mld_data():
    """从 CSV 提取数据并按指标分组"""
    if not os.path.exists(INPUT_CSV):
        print(f"❌ 找不到数据文件: {INPUT_CSV}"); return None
    
    df = pd.read_csv(INPUT_CSV)
    data_rows = []
    
    for reg_key, reg_info in REGIONS.items():
        row = [reg_info['name']]
        # 🎯 遍历 Bias, MAE, RMSE 三大指标
        for metric in ['Bias', 'MAE', 'RMSE']:
            for days in TIME_PERIODS.values():
                col_name = f'{reg_key}_{metric}'
                if col_name in df.columns:
                    val = df[df['forecast_day'].isin(days)][col_name].mean()
                else:
                    val = np.nan
                row.append(val)
        data_rows.append(row)
    return data_rows

def draw_combined_table(data):
    """绘制三段式 MLD 评估表"""
    w_first, w_rest = 0.25, (1.0 - 0.25) / 9
    col_widths = [w_first] + [w_rest]*9
    x_pos = [0] + list(np.cumsum(col_widths))
    x_centers = [(x_pos[i] + x_pos[i+1])/2 for i in range(len(col_widths))]

    total_rows = 2 + len(data)
    fig, ax = plt.subplots(figsize=(13, total_rows * 0.75 + 0.5), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, total_rows); ax.axis('off')

    # 1. 写数据 (从下往上)
    for i, row in enumerate(reversed(data)):
        y_center = i + 0.5
        ax.text(0.01, y_center, row[0], ha='left', va='center', weight='bold', fontsize=12)
        for j, val in enumerate(row[1:]):
            txt = f"{val:.2f}" if not np.isnan(val) else "N/A"
            ax.text(x_centers[j+1], y_center, txt, ha='center', va='center', fontsize=12)

    # 2. 写表头
    y_sub, y_super = len(data) + 0.5, len(data) + 1.5
    ax.text(x_centers[0], y_sub, "Study Region", ha='center', weight='bold', fontsize=13)
    for j in range(9):
        ax.text(x_centers[j+1], y_sub, PERIODS[j % 3], ha='center', weight='bold', fontsize=11)

    # 绘制大标题 (单位：m)
    metrics = ["Bias (m)", "MAE (m)", "RMSE (m)"]
    for i, m_text in enumerate(metrics):
        ax.text((x_pos[1+i*3] + x_pos[4+i*3])/2, y_super, m_text, ha='center', weight='bold', fontsize=14)

    # 3. 画线
    kws = {'color': 'k', 'solid_capstyle': 'butt'}
    ax.plot([0, 1], [total_rows, total_rows], lw=2, **kws) # 顶线
    for i in range(3):
        ax.plot([x_pos[1+i*3]+0.005, x_pos[4+i*3]-0.005], [len(data)+1, len(data)+1], lw=1, **kws)
    ax.plot([0, 1], [len(data), len(data)], lw=1, **kws) # 栏目线
    ax.plot([0, 1], [0, 0], lw=2, **kws) # 底线

    plt.title('Mixed Layer Depth (MLD) Forecast Evaluation', pad=25, fontsize=16, weight='bold')
    out_file = os.path.join(PLOT_OUT_DIR, 'Table_MLD_Combined.png')
    plt.savefig(out_file, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f"✅ MLD 评估表格已生成: {out_file}")

if __name__ == '__main__':
    data = get_mld_data()
    if data: draw_combined_table(data)