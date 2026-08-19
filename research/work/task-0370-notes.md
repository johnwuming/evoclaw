# task-0370 A10-4 因子治理产品化 过程笔记
[2026-08-19 19:29 start]
目标：① A7c 动态画像月度自动更新脚本（增量+幂等）② IC 衰减监控（连续3期低于阈值→告警+建议降权系数）
硬约束：不改 evolution_pipeline/registry/paper_engine/HP crontab；降权执行与 crontab 只出待批方案

## Step 1: 定位 A7c 画像产物

### 定位结果（完成）
- A7c 产物在 HP ~/quant-evolve/results/a7c-*（6 文件，2026-08-17 02:38），生成脚本副本在 VPS work/task-0341-out/a7c_ic_calc.py + a7c_rolling_series.py
- **数据源**：VPS shared/results/04-投资研究/factor_ic_monthly.csv（ym 2006-01~2026-07 共247月，107因子列，W1月频口径）；factor_catalog_v3.json（direction/mean_ic/icir/half_life_months）
- IC 口径（与 W1 一致）：有效IC = raw × (dir=='neg'?-1:1)；画像分类=稳定有效/衰减中/已失效反转/近期涌现
- 15普查因子中17列可算（P0-1×4, P0-2×2, P0-6×3, F7低波×4, F13股息×1, F14壳×3）；P0-3/4/5 等数据缺口标 N/A
- VPS python: /opt/finworker/bin/python；HP python: /home/noname/miniconda3/envs/quant/bin/python

### 数据一致性核验（完成）
- HP results/factor_ic_monthly.csv md5=c0a1db... 与 VPS 完全一致；factor_catalog_v3.json md5=992f31... 一致
- HP 面板最新 ym=2026-07（247月）；列含 ym + 107 因子
- 设计决策：新脚本产物写到独立目录 results/a10-monthly-profile/ 与 results/a10-ic-decay-alerts.*，不覆盖 a7c 原始产物（符合"新文件为主"）
