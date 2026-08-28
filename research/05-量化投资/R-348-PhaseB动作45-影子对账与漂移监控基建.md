# R-348 — Phase B 动作4-5：影子双轨对账与 4 维漂移监控基建

| 项 | 内容 |
|---|---|
| 任务 | task-0543（Phase B 统一开发批次第三波） |
| 日期 | 2026-08-28（HP UTC 时区；北京时间为 08-29 凌晨） |
| 依据 | R-336 v1.4 §7.2（4 维漂移带宽）、§8 Phase B 动作4-5 |
| 上游 | R-346（vC-0 快照+求解器）、R-347（选择器化+复现门）；在役 paper 链（equity A:a13_rsraw_e1f10dz / gold gold_trend_sma200） |
| 红线 | 在役零改动：全部产物落 `portfolio_v1/`，只读消费 `results/` 与 `model/registry/`；未动 crontab |

## 1. 交付物

| 文件（HP `~/quant-evolve/portfolio_v1/`） | 说明 |
|---|---|
| `shadow_recon.py` | 影子双轨逐日对账（动作4），产物落 `recon/` |
| `drift_monitor.py` | 4 维漂移监控（动作5），产物落 `drift/` + `drift-history.jsonl` |
| `recon/recon-2026-08-28.{json,md}` | 对账 dry-run 产物 |
| `drift/drift-2026-08-28.{json,md}` | 漂移评估 dry-run 产物 |
| `README.md` | 更新日志追加 task-0543 一行 |

## 2. shadow_recon.py 设计（动作4：目标侧 vs 在役运行态）

三视角对账，退出码 0=完成（超带以报告逐项判定为准）：

- **V1 NAV diff**：目标组合 NAV = weight_solution 加权（equity 0.580297 / gold 0.419703）双 sleeve paper 链；在役组合 NAV = `dual_independent_paper_chains` 名义 0.5/0.5；两链各自首共同日 rebase=1.0，逐日水平差 bp，容忍带借用 §7.2 D1 20bp（标定前缺省，Phase B 标定后冻结）。
- **V2 权重 diff**：solver 权重 vs 在役名义权重，对照 vC-0 `solver_ref.tolerances.rebalance_band=0.02`。
- **V3 事件覆盖**：event ledger JSONL 合法性 + seq 从 1 连续；vC-0 sleeve 引用可达性（registry 条目 status=active、engines.json 含 gold 引擎）；vC-0 建立后在役交易日应有当日对账产物（缺口列表，首跑后自然收敛）；数据新鲜度（滞后工作日数）。

## 3. drift_monitor.py 设计（动作5：§7.2 四维）

| 维度 | 实现 | 初版带宽 |
|---|---|---|
| D1 日P&L偏差 | equity：paper NAV vs 回测 `a13_rsraw_e1f10dz_full_nav.csv` 同日收益差（重叠日逐日打标）；gold：paper 月内累计（marks/open−1）vs 监控链当月 `net` | ≤20bp/日 |
| D2 Sharpe偏差 | rolling 60 日 Sharpe（paper vs 回测同窗）；obs<61 → `insufficient_obs` 并给出最早可判日 | \|Δ\|≤0.3，每周（初版日频跑、判带更保守） |
| D3 执行率/对齐率 | equity：最近调仓日 trades vs holdings 快照逐笔核对；gold：`w_signal` vs `current_weight` | 执行率≥90%；对齐率≥95% |
| D4 滑点偏差 | trades 的 price/cost 逐笔滑点 | ≤11.5bp×1.5=17.25bp |

连超判定数据源：`drift/drift-history.jsonl` append-only（同日重跑按 run_date 去重），逐维记录当期 flag 并计算 `consecutive_out_of_band`；任一维连续 2 期超带 → 报告标 ⚠️ 达冻结线（冻结动作本身属 promotion 状态机/人工门，脚本不执行）。

## 4. dry-run 结果（2026-08-28 真实数据）

**shadow_recon**：V1 共同日 3 天（08-24..26），max diff 11.485bp → 在带内；V2 权重差 ±0.0803 超带——**已知口径差非异常**：在役为双独立 paper 链、无组合层调仓机制，solver 权重要到 Phase C 指针切换才生效，报告中打标留痕、附归因、不触发动作；V3 ledger 2 事件 seq 连续、引用全部可达、vC-0 后在役日无缺口；新鲜度 equity 滞后 2 工作日（last_data_date 08-26）、gold 1 工作日。

**drift_monitor**：D1 equity=重叠不足（回测 full_nav 末行 2026-08-14 与 paper 建链同日，交集 0 个收益日）；D1 gold=暂定带内（diff 4.685bp，月未完）；D2 双侧观测不足（equity 9/60、gold 4/60，equity 最早可判约 2026-11-07）；D3 在带内（8/8 笔核对一致，gold 信号=当前权重）；D4 在带内（max 滑点 0bp，构造性结果，注明真实滑点回填属 A5 校准后续）；连超计数全 0。

## 5. 幂等与在役零改动核验

- 两脚本同日重跑各 2 次无报错：产物同名（日期戳）tmp+`os.replace` 原子覆盖；history 同日去重后仍 1 行。
- `find ~/quant-evolve -newermt "2026-08-28 16:10" -not -path "*/portfolio_v1/*"`：仅 `data/notify-state.json`、`logs/notify_hub.log`，mtime 16:10:01 为在役通知进程自身心跳（早于本任务首跑 16:25），与本任务无关。本任务写入的全部 8 个文件均在 `portfolio_v1/` 内（2 脚本、README、5 产物）。

## 6. dry-run 暴露的三个待办（Phase B 标定项）

1. **D1 equity 重叠缺口**：回测日线 full_nav 末行=2026-08-14，paper NAV 起于同日 → D1 无法常态判定。需将回测 NAV 延展至当前数据日（属动作3 口径插件的日更延伸，另行立项），或在 D1 明确改用「组合层重放 vs paper」口径。
2. **权重口径差**：V2 的 ±0.08 超带将持续存在直至 Phase C；建议在漂移标定（Phase B 退出条件）时把「名义 0.5/0.5」显式写进 vC-0 provenance，避免逐期人工归因。
3. **equity 数据滞后**：08-27（周五）数据 16:30 cron 后仍未入库（last_data_date 08-26），连续出现会拖累 V1 共同日增长，建议排查在役日线采集链（只读排查，不在本任务范围）。

## 7. crontab 安装提案（**未安装**，等用户批准）

**频率理由**：equity daily 16:30 出 T 日 NAV；gold daily 07:40 补 T−1 marks → 工作日 08:10 起双链 T−1 数据齐备，日频对账/漂移恰好覆盖最新完整交易日；两脚本秒级轻量、幂等，重复触发安全。

**建议 cron 行**（HP noname crontab）：

```
# task-0543 Phase B 动作4-5：影子双轨对账 + 4维漂移监控（安装需用户批准）
10 8 * * 1-5  cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python portfolio_v1/shadow_recon.py >> logs/shadow_recon.log 2>&1
15 8 * * 1-5  cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python portfolio_v1/drift_monitor.py >> logs/drift_monitor.log 2>&1
```

**安装命令全文**（批准后执行；先备份再追加，不动既有行）：

```bash
crontab -l > /tmp/crontab.bak-task0543 && (crontab -l; echo '10 8 * * 1-5  cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python portfolio_v1/shadow_recon.py >> logs/shadow_recon.log 2>&1'; echo '15 8 * * 1-5  cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python portfolio_v1/drift_monitor.py >> logs/drift_monitor.log 2>&1') | crontab - && crontab -l | tail -4
```

D2 频率说明：§7.2 定周频；初版日频跑全 4 维，obs≥60 前不判带，判定触发早于周频属更保守方向，不改带宽口径。

## 8. 验收标准对照

| 标准 | 结果 |
|---|---|
| 两脚本真实数据 dry-run、产物落盘 JSON+MD | ✅ recon/ 与 drift/ 各 2 件 + history.jsonl |
| 重复执行不报错（幂等） | ✅ 各重跑 2 次 |
| drift 输出含 4 维逐项带内/超带判定 | ✅ D1-D4 逐项 status（含 insufficient 诚实打标） |
| 在役零改动（find -newermt 对照） | ✅ 写入全在 portfolio_v1/（§5） |
| crontab 提案（不安装） | ✅ §7 |

## 9. 边界与后续

- 对账/漂移的影子侧当前=paper 运行态 vs 回测基线；「目标侧重放引擎」（event 溯源重放组合 NAV）属 Phase C 治理切换范围，届时 V1 口径可升级为真·双轨。
- D3 初版为 paper 自洽口径（成交即计划），真实计划-成交口径待执行层接入后标定。
- 下一步建议：①批准 §7 cron 安装；②立项 D1 回测 NAV 延展；③equity 日线滞后排查。
