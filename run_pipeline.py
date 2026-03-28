# /data03/hjj/hjj/LFS-new/newwork/region/run_pipeline.py
import os
import time
from config_regions import DATA_OUT_DIR, PLOT_OUT_DIR

# ================= 🎯 运行控制中心 =================
# 0: 区域定义图 | 1: 并行计算数据 | 2: 统计表格 | 3: 时效趋势图 | 4: 空间分布图
ACTIVE_STAGES = [1, 2, 3, 4] 

# 各阶段对应的脚本列表
SCRIPTS = {
    0: ["00_plot_study_regions.py"],
    1: ["01_calc_currents.py", "01_calc_eke.py", "01_calc_mld_stats.py", 
        "01_calc_sss.py", "01_calc_sst.py", "01_calc_ts_profile.py"],
    2: ["02_plot_currents_table.py", "02_plot_eke_table.py", "02_plot_mld_table.py", 
        "02_plot_sss_table.py", "02_plot_sst_table.py", "02_plot_tl_table.py", "02_plot_ts_profile_table.py"],
    3: ["03_plot_eke_lead_time.py", "03_plot_sst_lead_time.py", "03_plot_tl_lead_time.py"],
    4: ["04_plot_eke_spatial.py"]
}

def run_step(name):
    """执行单个脚本并记录耗时"""
    print(f"[{time.strftime('%H:%M:%S')}] 🚀 Running: {name}")
    start = time.time()
    exit_code = os.system(f"python {name}")
    if exit_code != 0:
        print(f"❌ Error in {name}. Pipeline stopped.")
        return False
    print(f"✅ Done! ({time.time()-start:.1f}s)")
    return True

def main():
    print("="*50 + "\n LFS Evaluation Pipeline \n" + "="*50)
    
    for stage in sorted(ACTIVE_STAGES):
        print(f"\n# --- Stage {stage} Start --- #")
        for script in SCRIPTS.get(stage, []):
            if not run_step(script): return
            
    print("\n" + "="*50 + "\n🎉 All Tasks Completed! \n" + "="*50)

if __name__ == "__main__":
    main()