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

## 2. HP 现状盘点（2026-08-19 19:35 确认）
- collect_crowding.py 21.4KB (mtime 08-18 08:39，含 task-0371 契约v2改动)，无 --daily 标志（grep daily 仅注释）；.bak.20260818 已存在
- refresh_data.py(akshare源) 已死：cron_refresh.log 尾行 "Segmentation fault (core dumped)"，akshare 请求 ConnectionError(RemoteDisconnected)
- 真正数据通道 = collect_qfq_baostock.py（baostock源，08-15 建），写 {code}_daily_qfq.parquet（含 outstanding_share/turnover），5206 只全部 08-15 写入
- 但该脚本 --mode update 实际是全量重拉(start默认2005-01-01)，docstring 声称的"只拉缺失尾部+因子跳变检测"未实现 → 需实施真增量
- 指数文件陈旧：hs300/zz500 parquet 均止于 2026-08-08（mtime 08-08 06:33），baostock 股票脚本不更新指数 → 日更需补指数通道
- crontab(只读)：refresh_data 周日20:00、collect_crowding 周日07:00、risk_patrol 周1-5 16:45、paper_trade 16:30 等
- 当前 crowding-indicators.json latest_date=08-14（R-237 记录），parquet 最新数据 08-14（08-15 周六跑）

## 待实施
A. collect_qfq_baostock.py 真增量 --mode update（只拉缺失尾部+除权跳变检测→全量回退）+ 指数(hs300/zz500)日更
B. collect_crowding.py 增加 --daily 模式（尾窗面板+追加历史+覆写JSON快照）
C. 实测：先日更数据→跑 --daily→验证 CSV shape/max(date)、JSON latest_date

## 3. baostock 通道验证（19:35）
- HP baostock login success；今日 08-19 股票(sz.000001 有 08-19 行)与指数(sh.000001 08-19=3894.42)数据均已可取
- → 日更前提成立：baostock 在 HP 可用且当日数据收盘后可得（现 19:35 已可拿到当日）
- 建议 cron 时点：数据日更 18:00（baostock 收盘数据约 17:30+ 到位），collect --daily 18:10
