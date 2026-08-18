# task-0371 实施笔记 — 拥挤度契约 v2 落地（R-237 方案II + eqw_index 截尾）

时间：2026-08-18 16:20–17:00 | 依据：R-237 设计报告 + task-0367 盘点 | 用户 16:00 已批①③（②方案I 另立项）

## 1. 方案II：VPS 新鲜度告警（已上线）

**新脚本** `scripts/crowding-freshness-check.sh`（3.5KB，bash+python3）
- 判定（R-237 契约阈值）：
  - red：generated_at 距今 >192h；含文件缺失/JSON 损坏（管线心跳中断）
  - yellow：latest_date 滞后 >5 个交易日（周一~五计数，节假日未计，误差可接受）
  - ok：静默（不写通知，仅 stdout）
- 接入：告警追加 `{"task_id":"crowding-freshness","timestamp":...,"message":...,"status":...}` 到 `scripts/.task-notifications.jsonl`（与 cron-auto-sync 同格式，心跳自动转述）
- 节流：`scripts/.crowding-freshness-state` 记日期，每日只实际检查一次 → 告警最多每日一条
- 调度：**未新建任何 cron**；挂入 `heartbeat.sh run()`（sync_completions 之后一行，`|| true` 保护，日志 `logs/crowding-freshness.log`），心跳已有调度自动带动
- 自测四态（FORCE=1 + /tmp 队列，未污染真实链路）：
  | 态 | 构造 | 结果 |
  |---|---|---|
  | ok | 真实文件（滞后2td/24h） | STATUS=ok，队列无写入 ✓ |
  | yellow | latest_date=08-06（滞后8td） | STATUS=yellow，队列1条 ✓ |
  | red | generated_at=08-05（319h>192h） | STATUS=red，队列1条 ✓ |
  | red | 文件缺失 | STATUS=red，队列1条 ✓ |
  - 节流：真实路径连跑2次，第2次 SKIP ✓；heartbeat.sh `bash -n` + run 输出未破坏 ✓

## 2. eqw_index 截尾（HP collect_crowding.py 输出段）

**改动前备份**（HP `~/quant-evolve/scripts/`）：`collect_crowding.py.bak.20260818`、`risk_patrol.py.bak.20260818`（scp 不通 sftp，用 ssh cat 往返；改后 VPS+HP 双端 py_compile 通过）

**collect_crowding.py 三处**：
1. 新常量 `OUT_EQW_CSV = results/eqw_index_history.csv`
2. 输出段：`out["schema_version"]=2`（契约 v2）；`microcap_eqw_index` 只留 `eqw_series[-90:]`
3. 全史 1848 点写 eqw_index_history.csv（date,microcap_eqw_index 两列）

**risk_patrol.py 一处（必要联动，不在禁改清单内）**：
- 发现：risk_patrol L173-175 用 JSON 内 eqw_index 做 6/12 月滚动交叉验证（ROLL6=126/ROLL12=252 > 90 点 → 全 NaN → `NaN` 字面量写进 risk-status.json → 非法 JSON，前端 riskStatus 卡会炸）
- 修法：`read_microcap_eqw()` 改为**优先读 eqw_index_history.csv**（全史权威载体），CSV 缺失/损坏回退旧 JSON 路径（向后兼容）
- 验证：HP 导入模块实测 read_microcap_eqw() → 1848 点（2019-01-02→2026-08-14），与改造前数据基础完全等价
- 16:45 日度 cron 为天然端到端验证（结果见 §4）

**HP 手动重算**（nohup 后台 PID 146900，日志 /tmp/cc_manual_20260818.log，~1分钟完成）：
| 产物 | 前 | 后 |
|---|---|---|
| crowding-indicators.json | 93,436B | **9,145B**（远超 <40KB 目标） |
| eqw_index_history.csv | — | 36,904B（1848 行全史） |
| crowding_history.csv | 282,469B | 282,469B（不变，列未动） |

重算后 JSON 校验：schema_version=2 ✓ eqw_len=90（2026-04-07→08-14）✓ latest_date=2026-08-14 ✓ overall_flag=red（excess_decay 保持）✓ indicators 四项+capacity 结构不变 ✓ json 可解析 ✓
（注：容量三档数值与 08-17 版略有差异，系 ADV20 窗口随日期滚动，正常）

## 3. 消费端影响评估
- server.js M4.7：主动剔除 microcap_eqw_index → 截尾无害且提速；schema_version 为新字段，旧读取逻辑不受影响（阶段B 才启用）
- risk_patrol：经 CSV 优先改造后功能等价（见上）
- auto_sync（VPS 每 30min）：MIRROR_INCLUDES 已含 crowding-indicators.json，镜像后看板目录自动升级 v2；eqw_index_history.csv 未加入 MIRROR_INCLUDES（VPS 侧无消费，按需后加）

## 4. 16:45 risk_patrol cron 端到端验证
- 更正：HP 时区 UTC，cron "45 16 * * 1-5" = 北京次日 00:45，今晚才自然触发；改为手动跑一次同等验证（RP_PID 147742，无并发进程）
- 结果：risk-status.json 更新（08:51 HP时），**cross_check_vs_microcap_eqw = 0.20541/0.23811，与改造前（JSON全史）完全一致** → CSV 路径数据等价性得证；strict JSON 解析 OK，无 NaN 字面量
- server.js 风险卡消费链路不受影响
- **17:00 auto-sync 镜像验证**：VPS 看板目录 crowding-indicators.json → 9,145B / mtime 16:40(HP源) / schema_version=2 / eqw_len=90 / overall=red —— HP产出→同步→看板读路径全链路闭环

## 5. 遗留
- 方案I（HP 日更增量管线）另立项，未动 HP crontab
- eqw_index_history.csv 若将来要进看板/研究归档，需加 auto_sync MIRROR_INCLUDES
