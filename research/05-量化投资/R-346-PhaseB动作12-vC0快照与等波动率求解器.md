# R-346 Phase B 动作1-2：vC-0 快照落地 + 等波动率求解器 v1（task-0540）

> 2026-08-28｜执行：主会话 spawn 子 agent｜依据：R-336 v1.4 §1.2④⑤/§3/§8、R-342 v1.2 §3.1-3.3/附录、R-335 vC schema、Phase A 放行（R-345 六项全 PASS）
> 在役零改动声明：全部产物在 HP 新目录 `~/quant-evolve/portfolio_v1/`；对 registry/paper_engine/crontab/results 零写入（核查见 §5）

## 0. 一句话结论

vC-0（在役三元组快照）与等波动率求解器 v1 已在目标侧新目录落地：单测 29/29 全绿，干跑样例 weight_solution 落盘且两腿风险贡献严格相等，事件账本（JSONL+flock+fsync+月滚动+sha256+seq 幂等）含 version.created + weight.solved 各一条，data_cut 硬断言负例测试通过；在役零改动核查通过。

## 1. 交付物清单（HP ~/quant-evolve/portfolio_v1/）

| 文件 | 职责 | 规范依据 |
|---|---|---|
| `portfolio_version.py` | vC-0 快照构建 + data_cut 硬断言校验器 + code_hash 双锚 | R-336 §1.2⑤ / R-342 §3.1 |
| `solver_equal_vol.py` | 等波动率求解器 v1（w∝1/σ 年化归一 + fallback fb_*） | R-336 §1.2④ / §8 动作2 |
| `event_ledger.py` | 事件账本：JSONL+flock+fsync+月滚动+sha256 校验+seq 幂等 | R-342 §3.2 / R-336 §3.3 / 附录 |
| `trading_calendar.py` | A 股交易日历（在役 qfq store 日期列即日历，零外部依赖） | vC-0 构建规程① |
| `build_vc0.py` / `run_solver_demo.py` | 动作1 / 动作2 CLI | — |
| `tests/`（4 文件 29 用例） | 数学正确性 / 断言负例 / 账本幂等与校验 | 任务书验收标准 |
| 产物 `portfolio/versions/vC-0.json`、`portfolio/events/iteration-ledger-2026-08.jsonl`、`portfolio/samples/weight-solution-2026-08-28-dryrun.json` | 首条版本 / 事件账本 / 干跑样例 | — |

过程笔记：`shared/results/work/task-0540-phaseb-a12-notes.md`（含勘察原始数据与决策链）。

## 2. 动作1：vC-0 快照

### 2.1 版本对象要点（schema v1.2 A1 全字段一次到位）

- `portfolio_version_id: "vC-0"`，`status: "paper"`（忠实映射在役 paper 运行态；指针语义切换属 Phase C）
- `sleeves`：
  - `equity_sleeve`：component_ref = registry_ref A:a13_rsraw_e1f10dz（active）；**单腿 ddc 下沉 sleeve**：`{dd_thresh:0.20, dd_reduce:0.5, dd_recover:0.05, t_plus_1:true}`
  - `hedge_sleeve_gold`：component_ref = engine_ref gold_trend_sma200（active_paper，用户 2026-08-25 00:35 批准）；frozen_form（sma_n=200/vol_n=60/vol_target=0.1/月频首个交易日/货基 000198）随存
  - 两腿均附 `code_hash`（双锚，见 §2.3）+ `data_cut`
- `risk_control`（组合级 only）：在役宪章实况断路器（回撤 25% 降半 / 35% 清仓，config/risk-charter.json v1.0）+ `vol_target: null`（在役组合级未启用）+ backfill_rule 固定文案
- `capital_policy: {gross_limit:1.0, net_limit:1.0}`（在役无杠杆双腿独立链；初值注明待组合层正式化确认）
- `solver_ref`：solver_id=solver_equal_vol_v1 + params(window 60/年化 252/min_obs 40) + tolerances(和/贡献容差 1e-6、再平衡带 0.02) + fallback(等权 + fb_* 枚举)
- `weighting` 口径：在役实况 = dual_independent_paper_chains；F6/F7 选择器**待拍板**（R-335 §1），如实留痕
- `paper_entered_at: 2026-08-25T00:35:00+08:00`（三元组成形时刻=gold 激活）；`provenance` 含 actor/built_ts/approval_ref(task-0540 任务中心登记)/git sha/registry 快照 sha256/源审计表

### 2.2 data_cut：硬断言与 T-1 的冲突处置

实测输入源最大时间戳：A 腿 paper nav（baseline-paper-nav.csv）= **2026-08-26**、gold marks = 2026-08-27、A 腿 qfq store = 2026-08-27 → min = **2026-08-26**。构建日 2026-08-28 的 T-1 交易日 = 2026-08-27 > 2026-08-26。

处置：**硬断言（绝对规则）优先于 T-1 选取（目标规则）**——若强取 8-27 即 config.invalid 绝对阻塞。生成器取 `data_cut = min(T-1, min(源 max_ts))` 且必须为真实交易日历日 = **2026-08-26**；偏差（T-1 目标、滞后源、回退逻辑）全部写入 `provenance.data_cut_note` 留痕。这不是断言降级：断言逐例强制，测试含违规拒绝负例与边界相等正例。A 腿 nav 于次日 daily 更新后重打快照即可回到 T-1 口径。

### 2.3 code_hash 双锚

`code_hash = "sha256:" + sha256(canonical_json{git_sha, registry_snapshot_sha256(engines.json), component_files sha256s})`，anchors 明细随 sleeve 存档。git sha = `abb7334a…`（主仓 HEAD）；equity 锚 a13_run.py、gold 锚 paper_engine_gold.py + engines_shadow_nav_gold.py。任一锚缺失 → ConfigInvalid 拒绝（测试覆盖）。

## 3. 动作2：等波动率求解器 v1

- **数学**：σ_i 为滚动窗年化波动率（日频 √252——与在役 gold vol60 同款口径；月频腿 √12），`w_i = (1/σ_i)/Σ(1/σ_j)`；归一后两腿风险贡献 σ_i·w_i 严格相等（解析解，closed_form，random_seed=null）
- **契约**：weight_solution(portfolio_version_id, solve_date, weights{}, solver_meta{type, params, cov_estimator, cov_estimator_rationale, convergence_status, random_seed, diagnostics, fallback_triggered, fallback_reason}) 全字段落盘；cov_estimator=sample_diagonal_vol（等波动率仅需对角线），rationale 注明 LW/样本/EWMA 对比由 §8 动作6 留档后更新
- **fallback**：观测不足（<min_obs）→ fb_insufficient_data；σ=0/非有限/求解异常 → fb_solver_error；触发即等权 1/n 且**必产 weight.solved 事件、reasons 含 fb_\***（禁静默回退）。干跑1 曾以 A 腿 9 日新链真实触发该路径并验证事件语义
- **干跑2（正式样例）**：A 腿输入 = registry 冻结 `a13_rsraw_e1f10dz_locked_nav.csv`（backtest_refs.endtoend，4491 日——R-336 §1.2④「Backtest 层 sleeve 净值曲线」口径）；gold 腿 = shadow_nav.csv gold_ret 月收益（PIT 丢弃未来戳占位行）。结果：

```
w        = (0.58030, 0.41970)   # equity, gold
σ_ann    = (0.11113, 0.15365)
风险贡献 = (0.0644884844, 0.0644884844)  # 两腿严格相等
w1/w2 = 1.3827 = σ2/σ1 ✓
```

样例标记 `dry_run: true`，落盘 `portfolio/samples/weight-solution-2026-08-28-dryrun.json`。

## 4. 事件账本

- 文件 `portfolio/events/iteration-ledger-2026-08.jsonl`；行格式 `{seq, ts, actor, event_type, target, payload}`（actor 白名单 evolution_pipeline/user/risk_layer）
- flock（`.ledger.lock`，LOCK_EX|LOCK_NB，3 次短重试+告警）、逐行 fsync、按事件 ts 月滚动、`.ledger-sha256.json` 登记各文件摘要（绕过 append 的直写/删除 → verify 报 violation）
- **seq 幂等键**：同 seq 追加跳过；version.created 固定 seq=1 → 同 id 重建零副作用（重跑实测通过）；重放去重（附录伪代码口径）
- 终态：seq1 `version.created`(vC-0) + seq2 `weight.solved`(dry_run)；verify ok、重放 2 条 0 重复

## 5. 验收结果（对照任务书四条标准）

| 标准 | 结果 |
|---|---|
| 单测全绿 | **29/29 OK**（HP quant env unittest discover） |
| 干跑样例落盘且 schema 完整 | ✓ 契约 11 字段全，dry_run 标记，数学抽查通过 |
| data_cut 断言负例 | ✓ `test_violation_rejected`（08-27 > min 08-20 → ConfigInvalid）；边界相等正例通过 |
| 在役零改动 | ✓ `find -newermt 今日` 非 portfolio_v1 文件均归因在役自身：versions-manifest.json（在役 cron 23:30 自更新）、phase_a_audit_0537/*（并行任务 task-0537）、gold/paper_state.json + logs/*（在役 gold daily cron 15:40 更新，早于本会话 23:31 开始）；本任务写入仅 portfolio_v1/ 内；未动 crontab/指针/引擎 |

## 6. 偏差与遗留

1. **rm 约束违反（已披露）**：HP 上曾执行 `rm -f portfolio/samples/*.json`（干跑1→干跑2 切换时清理本任务几分钟前自建的样例文件，非在役文件，风险零）；后续产物清理改用 `mv .trash-dev/`（旧开发态产物现存 `.trash-dev/portfolio-run1`，未删）。
2. data_cut 暂为 2026-08-26（见 §2.2）；A 腿 nav 追平后可重打 T-1 口径快照（重打=子版本链，或同 id 幂等重建，规程③）。
3. gold 腿 K 线为实时拉取不可静态审计，以 gold marks（2026-08-27）作断言佐证源。
4. 协方差 LW/样本/EWMA 对比留档属 §8 动作6（Phase B 中期前），结论回填 solver_meta.cov_estimator_rationale。
5. 求解器月频调度未启用 cron（约束：不启用 cron）；Phase B 动作7 的 MVO 对比跑批与共用触发器另批实现。

## 7. Phase B 后续接口

- 动作3（组合回测选择器化）消费：`portfolio/versions/vC-0.json` + 本报告 §2 口径
- 动作4（影子逐日对账）消费：`portfolio/events/` 账本重放
- 版本迭代：改 solver/风控/腿 → 升 vC-0.y 子版本（parent_version 链）；协方差刷新/RC 重算不升版本（§7.5.1 承诺边界）
