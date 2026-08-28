# R-347 Phase B 动作3：组合回测选择器化 + vC-0 复现门

- 任务：task-0541（R-336 v1.4 §8 Phase B 动作3，23:07 自动推进授权）｜2026-08-28/29｜在役零改动
- 上游依赖：task-0540（vC-0 快照 + 等波动率求解器 v1，HP `~/quant-evolve/portfolio_v1/`）
- 结论先行：**vC-0 复现门 G1–G5 全 PASS**——F1 基线 `all_results.json` md5 `915e446388fc8e63c281378c3dd66580` 逐位复现（另两件输出亦逐位对齐），PIT 四锚点断言全过；F6/F7 组合回测已可按参数在「在役原样口径」与「vC-0 口径」间切换，全程未触碰任何在役文件。

## 1. 交付物（全部新文件，HP `~/quant-evolve/portfolio_v1/combo_selector/`）

| 文件 | 作用 |
|---|---|
| `caliber.py` | 口径插件：`in_service`（task-0492/0494/0495 原脚本常量逐字对应）/ `vc0`（从 vC-0.json 读取+断言）；缝合点=CaliberSpec 流入引擎，vC-1 换权重不换代码 |
| `state_machine.py` | dd 状态机（sim_dd 同构，含 r_ctrl）+ PIT 月度状态（t 月权重由 t-1 月末收盘状态判定）+ 四锚点断言 |
| `combo_backtest.py` | 选择器入口：`--caliber {in_service,vc0} --variant {F1,F6,F7a,F7b}`；F1/F7a/F7b=目标权重月度引擎，F6=月均仓位引擎（均与原脚本逐行同构） |
| `run_vc0_repro.py` | 复现门编排（G1–G5，见 §3） |
| `engine/backtest_f1_drift_engine.py` | task-0492 `backtest.py` **字节级副本**（md5 `ed95aa7603fdefec7110959bbd3a77c9`，VPS/HP 两端核验一致） |
| `results/` | `repro_gate.json`、`vc0_repro_comparison.csv`（21 行逐项对照）、F1 重跑三输出、`selector/` 四变体核验 JSON |
| `data/` | HP 在役只读源经 md5 校验后的入位副本（a13 full nav / gold shadow nav / monthly_returns） |

过程笔记：`shared/results/work/task-0541-phaseb-a3-notes.md`；本地代码暂存 VPS `work/task-0541/combo_selector/`。

## 2. vC-0 口径的参数化语义（本动作的核心缝合点）

vC-0.json 无显式权重字段（`weighting.in_service=dual_independent_paper_chains`）。vC-0 口径按以下规则**从快照推导**，并对每一步断言：

1. `capital_policy.gross_limit=1.0` + 双 sleeve 结构 → 等权分割 w_A=w_gold=0.5（断言==在役原样口径）；
2. ddc 参数取 `equity_sleeve.risk_control.ddc`（0.20/0.5/0.05）；
3. 成本取 `hedge_sleeve_gold.frozen_form.cost_per_absdw`（0.0013）；
4. F7a/F7b 降仓权重由规则推导（A 降至 base×dd_reduce，释放额全给 gold / 半金半现），断言==在役常量 (0.25,0.75,0)/(0.25,0.625,0.125)。

任何一步断言失败即复现门如实 FAIL（未来 vC-1 权重偏离时按预注册纪律报告差异，不硬凑、不放宽）。

## 3. vC-0 复现门结果（HP 权威跑，quant python，2026-08-29 00:1x）

| 门 | 内容 | 结果 |
|---|---|---|
| G1 数据入位 | a13_full_nav=358ce819…、gold_shadow_nav=3654c3e8… md5 校验 | PASS |
| G2 口径等价 | F1/F6/F7a/F7b 四变体 in_service==vc0 数值字段逐项相等 | PASS |
| G3 F1 md5 基线 | 引擎副本 md5 一致 + 重跑 `all_results.json`=**915e446388fc8e63c281378c3dd66580**（R-317 基线 915e446388… 逐位对齐）、`nav_curves.csv`=9704a300…、`monthly_returns.csv`=0113f40d… 三件逐位一致 | PASS |
| G4 PIT 四锚点 | 2015-06=FULL / 2015-07=REDUCE / 2020-06=REDUCE / 2020-07=FULL + 首月 FULL + episode（2015-06-29 REDUCE dd=-0.2026 → 2020-06-19 RESTORE dd=-0.0499）+ 60 个 REDUCE 月 | PASS |
| G5 选择器交叉验证 | vc0 口径四变体指标==在役原脚本在案值（task-0495 `f7_results.json` md5=c8866a2d… 落盘值）：F1 13.57%/1.431、F7a 13.61%/1.483、F7b 13.26%/1.469、F6 19.11%/1.197 逐项相等 | PASS |

选择器 CLI 独立入口另验：`--caliber vc0 --variant F7a` 输出与在役在案值逐位一致。逐项对照见 HP `combo_selector/results/vc0_repro_comparison.csv` 与 `repro_gate.json`。

## 4. 在役零改动核验

- HP `find scripts results model config registry.json evolution_pipeline.py paper_engine*.py -newermt "2026-08-28 23:50"` → **空**（无任何在役文件被触碰）；
- F6/F7 原文件（VPS `work/task-0494`、`work/task-0495`）未修改，引擎以字节级副本进 selector；
- 产物只落 `portfolio_v1/combo_selector/` 新目录 + 本报告/笔记；`portfolio_v1/README.md` 追加更新日志一行（扩展既有文件，属 task 书面要求）；
- 回退方式：删除 `combo_selector/` 目录即零残留。

## 5. 局限与声明

1. md5 基线 915e446388… 对应 task-0492 **漂移引擎**（F1 13.54%）；选择器 F1/F6/F7 引擎沿用 task-0494/0495 **简化引擎**（无月内漂移，F1 13.57%），两口径差 <0.05pt 系 R-317 已声明口径差，非缺陷。复现门与选择器各自对应正确的原版引擎，未混用。
2. G3 的 vC-0 链接方式为「vC-0 权重口径前置断言 + task-0492 字节级副本重跑」：副本代码不可参数化（字节级是逐位复现的前提），权重缝合点在断言层；真正的参数化权重路径由选择器（G5）承载并在 vc0 口径下验证。若未来 vC-N 权重≠0.5/0.5，G2/G5 将 FAIL 并给出差异字段，届时需按预注册纪律重开复现基线。
3. F6/F7 结论依旧受 R-317 局限约束（n=1 episode，gold 为影子链月频 net）；本动作不新增统计结论。
4. 零生产改动：未触碰 evolution_pipeline.py / registry / paper_engine / crontab。

## 6. 验收标准对照

- [x] md5 逐位一致（915e446388fc8e63c281378c3dd66580）+ PIT 四锚点全过 → **PASS**
- [x] 参数化口径插件（in_service/vC-0 可切换），未修改 F6/F7 原文件
- [x] 在役零改动（find -newermt 空结果记于 §4 与 notes §5）
- [x] 产物落 portfolio_v1/，路径见 §1；README 更新日志一行
