# task-0373 拥挤度日更实施 过程笔记
开始: 2026-08-19 19:30:06

## 1. R-237 方案 I 范围摘录（2026-08-19 19:30 读毕，10.7KB）
- 方案I：HP 侧 collect_crowding.py --append 模式，周一~周五 16:50（risk_patrol 16:45 之后）
- 逻辑：复用增量 parquet → 只重算当行 → append crowding_history.csv + 覆写 crowding-indicators.json 快照
- 前提：确认 data/ 每日增量到位（R-237 撰写时 refresh 仅周日 20:00 → 本次须核实 parquet 实际刷新节奏）
- 契约 v2：schema_version=2 + series_90d + data_cutoff 三层新鲜度；microcap_eqw_index 截尾近3年；CSV 只增列不删列
- 约束：不改 evolution_pipeline.py/registry/paper_engine/HP crontab；cron 行只作待批输出
- 注意：方案I 图中标注“先做方案II(VPS侧告警)”为推荐顺序，但本次任务用户已批方案I 实施（含前提检查）

## 实施计划
1. HP 盘点：collect_crowding.py 结构、crontab(只读)、data/ parquet 刷新节奏(mtime+max date)
2. 前提检查：parquet 是否日更（若仅周更→需评估日频采集的数据可得性）
3. 实施 collect_crowding 日频模式（.bak 备份原件）
4. 实跑验证：产物落盘+shape+max date
5. 输出待批 crontab 行+回滚说明
