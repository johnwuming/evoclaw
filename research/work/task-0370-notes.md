# task-0370 A10-4 因子治理产品化 过程笔记
[2026-08-19 19:29 start]
目标：① A7c 动态画像月度自动更新脚本（增量+幂等）② IC 衰减监控（连续3期低于阈值→告警+建议降权系数）
硬约束：不改 evolution_pipeline/registry/paper_engine/HP crontab；降权执行与 crontab 只出待批方案

## Step 1: 定位 A7c 画像产物
