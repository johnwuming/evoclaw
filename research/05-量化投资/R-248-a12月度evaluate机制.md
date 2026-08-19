# R-248：a12_s2_reb 月度 evaluate 自动推进机制设计（task-0381）

## 一、背景

R-238（task-0374）将大小盘轮动 S2_reb 判入 shadow_watch 影子观察（全样本 Calmar 0.618 最优、locked 近无损、holdout 分化防护 +12.4pp 全额兑现，但血统线未达）。task-0379 已人工登记 registry：`model/registry/a12_s2_reb.json` status=candidate + gate.shadow_watch.active=true（clean_evals=0/3，评分制 v1.1 等价态）。

遗留两个 gap（R-238 结尾 + 任务书）：
1. 无自动月度 evaluate cron——影子观察期 clean_evals 不会自动累加，机制空转；
2. paper_engine shadow 不支持轮动型——无法走"每日影子净值"通道。

用户 2026-08-19 19:41 拍板推进本机制。约束：不改 evolution_pipeline.py / paper_engine / registry 语义 / HP crontab（新增 cron 行仅出建议文本待批）。

## 二、方法

### 2.1 evaluate 路径确认（核心调研结论）

`evolution_pipeline.py cmd_evaluate` 对 a12_s2_reb **原生可评估，无需改动引擎本体**：

- 全程只读 registry + nav csv + factor_ic 月度数据，不调选股/回测引擎入口；
- g1/g2 ICIR 走 `load_ic_monthly()`（a12_s2_reb 的 selection.factors 与 v5h_xsub 同款，数据在库且随半月度 evolution 每月 1/15 自动更新）；
- g3 相关性已含 task-0398 护栏豁免修正（SCORE_CONFIG v1.1 口径，incumbent=a9_ranksum_raw）；
- g4 DSR 读 `backtest_refs.endtoend`（locked nav）；g5 logic 读 reg.gate.logic；g6 数值保留、判定禁用（D-20260819-G6DEL）；
- `compute_holdout_metrics` 读 `backtest_refs.nav`（full nav）按 SHADOW_CONFIG（2024-07 起，ann ≥ 0.60×locked，MDD ≤ locked+10pp）分段判定；
- 产物 `results/bt_{version}/gate-report.json` + 回写 reg.gate（`_shadow_update` 状态机）。

**gap 实质重新定位**：不是"evaluate 不支持轮动"，而是（a）无人按月触发；（b）nav 文件为静态回测产物（截至 2026-08-14），不会随新数据滚动。

### 2.2 三层机制设计

| 层 | 职责 | 实现与状态 |
|---|---|---|
| L1 评估层 | 每月跑一次 `evaluate --version a12_s2_reb` | 本任务落地（脚本+干跑已验证） |
| L2 nav 刷新层 | 底表更新时重跑 `a12_rot_engine.py`（实测全量 131.5s）刷新 nav | 接口预留（--refresh-nav），默认关 |
| L3 晋升守卫 | clean_evals ≥ required−1 时停止自动评估，转人工评审 | 已实现（exit 42 + red 通知） |

**L3 依据**：cmd_evaluate 自动上岗链为 rank=1 且影子出影（clean_evals 满 3）且 holdout pass → `_do_activate` 改 main.json。registry note 明示"观察期满由人工确认"（R-238 §4.2 亦然），故自动化只做 0→1→2 的累加，第 3 期（可能出影触发上岗链）拦截转人工。stat_warn 语义（True 清零 / False +1）下该预检查为保守正确。

**L2 依赖标注**：`a12_rot_engine.py` 读两个静态底表——`timing_v2/a12_rot_series.parquet`（RS/Mlarge/micro_state，源自 task-0365 VPS 侧 /root/sr365 调研管线，非 HP 常态化）与 `signal_series.parquet`（tv2_compute_v2）。底表不刷新则重跑引擎无增量，故 wrapper 按 mtime 检测式降级：底表新于上次评估才重跑，否则跳过并标注 `nav=静态`。底表管线工程化另行立项（见结论）。

**触发时机**：建议每月 2 日 17:10（HP 本地）。理由：月首交易日 16:30 paper 调仓已落盘、避开 1/15 日 02:00 半月 evolution 与 16:30 日常 paper 高峰、且当月 IC 底表已随 1 日 evolution 更新。

### 2.3 脚本落地（HP）

- `scripts/a12_monthly_evaluate.sh`：cron 入口。flock 幂等锁防并发；失败 120s 后重试一次；exit 42（人工评审守卫）归一为 0。
- `scripts/a12_shadow_eval.py`：逻辑层。预检查（版本/状态/影子位）→ 月度幂等（`data/a12-eval-state.json` 记 last_eval_ym，本月已评跳过；dry-run 不占号）→ L3 守卫 → L2（可选）→ L1 评估 → 摘要提取与通知。
- `--dry-run`：备份 registry json + decision-log + experiment-ledger 三处 → 跑 evaluate → 逐字节恢复 + md5 校验；gate-report.json 留作评估产物。
- 通知：append `results/notifications-queue.jsonl`（notify_hub 同 schema），经既有 auto_sync 链路带回 VPS，进主会话通知队列。

### 2.4 干跑验证（2026-08-19，未写 registry）

```
[L1] DRY-RUN 运行: evolution_pipeline.py evaluate --version a12_s2_reb
⏸️ 评分 rank=8/池8（score=0.6666）未达自动上岗条件，保持 candidate
🚦 evaluate 完成: verdict=SCORED → results/bt_a12_s2_reb/gate-report.json
[dry-run] 已恢复 a12_s2_reb.json md5一致=True
[dry-run] 已恢复 decision-log.jsonl md5一致=True
[notify:info] 👁️ a12_s2_reb 月度影子评估DRY-RUN：score=0.6666 holdout_ann=0.2538 pass=True clean_evals=0/3
=== 结束 rc=0 ===
```

补充验证：bash -n / py_compile 全过；模拟 `last_eval_ym=2026-08` 后 live 模式正确幂等跳过；全程 registry md5 未变（2be515e74b7d）。

## 三、发现

1. **首期影子画像健康**：score=0.6666、holdout（2024-07 起）年化 25.38%、holdout pass=True；rank=8/池8（池含全 registry 候选，rank 低是因 nav 未含最新数据且六分项中 is/oos/corr 等按 locked 全窗口径，符合预期——影子观察关注的是 stat_warn 与 holdout，不是 rank）。
2. evaluate 对轮动型零改造可用的根因：评分体系输入全部是"文件级"产物（IC 序列、nav、registry 登记项），轮动差异被封装在 timing 层的 nav 生成端。
3. 自动上岗链风险真实存在（cmd_evaluate 源码：出影+rank1+holdout pass → _do_activate），L3 守卫为必要组件而非过度设计。
4. HP 系统时区与 VPS 差 7h（HP 显示 UTC 口径），cron 建议按 HP 本地时间表达，与现有 paper 16:30 同基准。

## 四、结论与建议

1. 机制就绪：L1 已落地验证、L2 接口预留、L3 守卫生效；**cron 行建议（待用户批，未安装）**：

```
10 17 2 * *  cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python scripts/a12_monthly_evaluate.sh >> /home/noname/quant-evolve/logs/a12_monthly_eval.log 2>&1
```

2. 首月人工观察建议：cron 批准后首个周期（下月 2 日）检查 `logs/a12_monthly_eval.log` + 通知链路（notifications-queue → auto_sync → VPS）端到端一次。
3. 后续立项建议（不在本任务范围）：
   - 轮动信号底表 HP 工程化（sr365_compute 移植或数据同步），使 L2 nav 刷新常态化——这是"每日影子净值"理想态的前置；
   - paper_engine 轮动型 shadow 支持（R-238 已标注，属 paper_engine 改造）。
4. 风险与边界：dry-run 会留一条 notifications-queue 通知与 gate-report.json（registry 三处副作用已恢复）；live 模式每月真实累加 clean_evals，stat_warn 触发会清零重来（机制语义如此，通知可感知）。

## 五、来源

- registry：HP `model/registry/a12_s2_reb.json`（shadow_watch 人工登记，task-0379）
- 引擎源码：HP `scripts/evolution_pipeline.py`（SHADOW_CONFIG L107、_shadow_update L982、cmd_evaluate L1005+、自动上岗链 L1100+）；`scripts/a12_rot_engine.py`（404 行，131.5s 全量）；`scripts/a12_formal_products.py`（task-0384）
- 干跑产物：HP `results/bt_a12_s2_reb/gate-report.json`；日志 VPS `shared/results/work/task-0381-notes.md`
- 上游报告：R-238（shadow_watch 立项与晋升路径）、R-225（评分制 v1.1）、R-241/R-242（SCORE_CONFIG 与护栏豁免衔接）、task-0353 notes（SHADOW_CONFIG 实现）
- crontab：HP `crontab -l`（2026-08-19 快照）；通知链路：HP `scripts/notify_hub.py`（task-0279）+ auto_sync
