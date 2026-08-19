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

## 4. 实施进度（19:50）
- collect_qfq_baostock.py v2 已推送 HP（10406B，HP py_compile OK）：真增量(尾行拉取+重叠日除权跳变检测>0.5%自动全量)、--mode idx(指数日更)、--workers N(多进程并发)
- 原件已备份 scripts/collect_qfq_baostock.py.bak.20260819 (4015B)
- baostock 公共 API 无多连接类 → 并发用多进程(Linux fork，每 worker 独立 login)

## 5. 数据日更实测通过（19:56）
- collect_qfq_baostock --mode update --workers 6：codes=5206 updated=5206 err=0 added_rows=42351 dur=168s ✓（日志 logs/qfq_update_20260819.log）
- --mode idx：hs300 08-07→08-19 (5003→5011行)、zz500 08-07→08-19 (5003→5011行) ✓
- 核验：000001 parquet 末3日=08-17/18/19 ✓；hs300/zz500 末日=08-19 ✓
- baostock 单查询约0.2s，6进程并发 → 5206只 2.8分钟，日更开销可忽略

## 阶段 B 实施开始（22:48）
- 脚本已全读：collect_crowding.py 21404B，结构=build_panel(全量)→四指标→全量覆写 CSV+JSON+eqw CSV；仅 --start-date 参数，无 --daily
- 产物实际路径（非 notes 旧描述 results/crowding/）：results/crowding_history.csv（1849 行含头，止 08-14）、results/crowding-indicators.json（schema2/latest_date 08-14）、results/eqw_index_history.csv（止 08-14）
- 基线 md5（08-19 22:48 实测）：
  - crowding_history.csv = 2838f49a58973d6bcef27a60698f3210
  - crowding-indicators.json = b5ca0a594a6b99be80d653587e683aac
  - eqw_index_history.csv = 3fc773b6fb44f38787151466ed17485e
- 数据现状：股票 qfq parquet 000001/600000/300001 max=2026-08-19（今日，已日更）；hs300/zz500 parquet mtime 08-19 15:01 但文件名写 20260808，需核实际 max date
- 下一步：核指数 parquet 内 max date + 08-19 全市场股票覆盖度 → 决定 --daily 实跑是否含 08-19 行
- 数据核验（22:50）：5206 只股票 qfq parquet max date 全部=2026-08-19（今日已日更就绪）；hs300/zz500 parquet 内 max date 也到 08-19（mtime 08-19 15:01）
- CSV 止 08-14 → 预期 --daily 追加 08-17(Mon)/08-18(Tue)/08-19(Wed) 共 3 行
- 实施策略：main() 主体逐位不动，仅加 --daily/--tail-days 两个 argparse 参数 + 解析后 if args.daily 提前分支到新增 run_daily()；周更路径 diff 仅见增量 → 零回归可证明
- 本地补丁完成（22:55）：语法 OK，diff 0 行删除（纯增量 190 行），周更 main() 主体未动
- HP 安装完成（22:56）：备份 collect_crowding.py.bak.20260819（21404B=原件）；新版 30878B 已装且 py_compile 通过
- 实跑前基线：CSV 1849 行止 08-14；JSON latest_date 08-14；eqw 止 08-14
