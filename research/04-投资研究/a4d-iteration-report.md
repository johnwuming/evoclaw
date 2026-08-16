# A4D/task-0328 第四批模型迭代报告：价值大师选股（6候选，2 PASS 留 pending，0 activate）

> 2026-08-16 · 状态：已完成（战役目标 25%/-20%/1.2 **全部未达**；价值 IC 为负结论入库；0 activate，现役仍 v2b_trr）
> 父本系：v0_seed（裸选股）/ v2b_trr（q3z×MA200 趋势择时）/ v2d_dd（回撤触发血统）
> 基建口径：全量池+成本v2+一字板+审计锁（AUDIT_LOCK_END=2024-06-30）；等价校验：原引擎 vs patched 开关全关 **逐位一致**（full/locked nav exact，EQUIV_OK）

## 0. 批次设计逻辑（用户点名：价值策略大师指标进选股层）

- 风格映射：林奇 PEG（peg_np/peg_rev/pegy）、格雷厄姆烟蒂（graham_score）、巴菲特质量带（buf_quality）、聂夫（neff_val）、戴维斯双击（davis_dp）、林奇六类分型代理（lynch_bucket）
- 全部从既有 PIT 面板推导（ths_ttm_panel 的 net_profit_ttm/equity + fin_deep_monthly_panel_ak 的 growth 字段 + fundamentals_monthly 的 circ_mv/div），**零新数据采集**；PIT 对齐：ttm 用 avail_date 映射到月末 as-of，growth 用 usable_from 月频面板（与 W1/A1 同机制）
- 候选 = 选股层改造（价值因子 blend 排序 0.5·(-z mv)+0.5·(±z 价值)）× 择时血统（裸 / +q3z_tr / +q3z+dd），每候选单维度改动 vs 明确 parent

## 1. 阶段0/1：大师指标 IC 预检（月频全市场，W1 口径，方向调整）

| 指标 | 大师出处 | 方向 | mean_IC | ICIR_ann | 覆盖率 | 宇宙内 mean_IC | 裁决 |
|---|---|---|---|---|---|---|---|
| pe_ttm | 格雷厄姆/聂夫 | -1 | -0.0386 | -1.038 | 87.1% | -0.0508/-1.37 | 保留(IC负) |
| pb | 格雷厄姆烟蒂 | -1 | **-0.0525** | **-1.626** | 96.0% | -0.0412/-1.01 | 保留(IC负) |
| peg_np | 林奇PEG | -1 | -0.0344 | -1.337 | 58.6% | -0.0497/-1.38 | 保留(IC负) |
| peg_rev | 林奇PEG(营收) | -1 | -0.0350 | -1.318 | 64.7% | -0.0568/-1.67 | 保留(IC负) |
| pegy | 林奇PEGY | -1 | -0.0347 | -1.288 | 59.7% | -0.0501/-1.43 | 保留(IC负) |
| pcf_proxy | 聂夫现金流 | -1 | -0.0301 | -0.968 | 52.0% | -0.0289/-0.76 | 保留(IC负) |
| neff_val | 聂夫 | +1 | -0.0166 | -0.796 | 91.7% | -0.0482/-1.50 | 保留(IC负) |
| davis_dp | 戴维斯双击 | +1 | -0.0091 | -0.573 | 96.0% | -0.0180/-0.60 | 保留(弱) |
| buf_quality | 巴菲特质量带 | +1 | **+0.0035** | **+0.091** | 99.0% | -0.0077/-0.17 | 保留(唯一近0) |
| graham_score | 格雷厄姆烟蒂分 | +1 | **+0.0004** | **+0.012** | 96.0% | -0.0109/-0.24 | 保留(近0) |
| lynch_bucket | 林奇六类分型 | +1 | 0.0000 | 0.001 | 99.0% | — | 砍掉(无IC且逻辑冗余) |

**核心发现（本批最重要证据）**：该宇宙（div≥2%、roe>15%、roa>10%、price<10 的质量小盘）内，全部价值指标 IC 为**负**或近零——便宜的股票后续收益反而更低。size 中性后仍全负（pe_ttm -0.036、peg_np -0.048）。小市值溢价与成长/动量主导该池，价值维度不构成 alpha 源。buf_quality 与 graham_score 是全表仅有的近零指标（非负），后续候选优先选它们。

## 2. 阶段3：正式回测结果（locked=2006-01~2024-06 正式口径；full 补充）

| IT | 版本 | parent | 组件改动 | locked 年化/MDD/Sharpe | full 年化/Sharpe |
|---|---|---|---|---|---|
| IT-A4D-01 | v3a_peg | v0_seed | 排序 mv→PEG blend（裸） | 24.72% / −72.10% / 0.883 | 25.34% / 0.915 |
| IT-A4D-02 | v3b_glm | v0_seed | 排序 mv→Graham blend（裸） | 20.48% / −67.76% / 0.757 | 21.24% / 0.790 |
| IT-A4D-03 | v3c_peg_trr | v2b_trr | 排序 mv→PEG blend | 14.65% / −30.73% / **0.964** | 14.74% / 0.984 |
| IT-A4D-04 | v3d_buf_trr | v2b_trr | 排序 mv→巴菲特质量 blend | 12.38% / −29.29% / 0.808 | 12.50% / 0.826 |
| IT-A4D-05 | v3e_peg_dd | v2d_dd | 排序 mv→PEG blend（+dd 触发） | 10.05% / **−22.76%** / 0.932 | 9.79% / 0.913 |
| IT-A4D-06 | v3f_grm_trr | v2b_trr | 排序 mv→Graham blend | 12.39% / −29.47% / 0.819 | 12.51% / 0.837 |

- 结果文件：results/a4d_<ver>_formal_{locked,full}_* 5件套×6候选×2窗 = **60件** + 汇总 a4d_backtest_summary_none.json
- 等价/中间产物：a4dx_equiv_* / a4dx_ref_*（等价校验，EQUIV_OK）；a4d_value_panel.parquet；a4d_value_ic_precheck.csv；a4d_value_ic_sizeneutral.csv；a4d_ic_monthly_ext.csv / a4d_ic_corr_ext.csv（门禁扩展IC）

## 3. 阶段4：五门禁裁决（n_trials 51→57；扩展 IC 数据源，管线代码零改动）

| 候选 | g1 ICIR_is | g2 OOS | g3 ρ | g4 DSR | g5 | g6 MDD | 裁决 |
|---|---|---|---|---|---|---|---|
| v3a_peg | FAIL 0.342 | FAIL | PASS | FAIL 0.729 | PASS | FAIL | REJECT |
| v3b_glm | PASS 0.561 | PASS | PASS | FAIL 0.497 | PASS | FAIL | REJECT |
| v3c_peg_trr | FAIL 0.342 | FAIL | PASS | PASS 0.993 | PASS | PASS | REJECT |
| v3d_buf_trr | PASS 0.575 | PASS | PASS | PASS 0.959 | PASS | PASS | **PASS→pending** |
| v3e_peg_dd | FAIL 0.342 | FAIL | PASS | PASS 0.997 | PASS | PASS | REJECT |
| v3f_grm_trr | PASS 0.561 | PASS | PASS | PASS 0.965 | PASS | PASS | **PASS→pending** |

- **PEG 系候选（v3a/v3c/v3e）g1/g2 FAIL 的根因**：PEG 因子 IC 为负（阶段0/1已证），复合 ICIR 被拖垮（0.342<0.5）；g1/g2 用扩展 IC 如实计算，未放水
- v3d/v3f（buf_quality/graham 系）ICIR 0.56-0.58 过线 + DSR 过线（0.959/0.965）+ g6 MDD 未恶化 → 六门全 PASS
- v3a/v3b 裸选股 g6 FAIL（MDD -67~-72% 远超 active 的 -29.86%），g4 亦不过（DSR 0.73/0.50）

## 4. 裁决与决策留痕

- **0 activate**：v3d_buf_trr/v3f_grm_trr 虽六门全 PASS，但**不严格优于现役 v2b_trr**（年化 12.4%<15.15%、Sharpe 0.81<0.94，仅 MDD 微优 0.5pp），且战役目标未达——activate 无正当性，按"PASS 留 pending 待人工确认"处理
- 现役不变：**v2b_trr（active）**；registry 新增 6 候选（v3 系列，fork 自 v0_seed/v2b_trr/v2d_dd）
- decision-log：D-20260816-025~030（逐候选 evaluate）+ **D-20260816-031（批次收口）**
- ledger：+6 行 backtest（IT-A4D-01..06）+ 6 行 evaluate（管线自动），n_trials_cum 51→57

## 5. 战役目标对照（25% / −20% / 1.2，locked 口径）

| 候选 | 年化 vs 25% | MDD vs −20% | Sharpe vs 1.2 | 差距判读 |
|---|---|---|---|---|
| v3a_peg | −0.28pp（24.72%） | −52.1pp（−72.1%） | −0.317 | 年化最接近但 MDD 失控 |
| v3c_peg_trr | −10.4pp | −10.7pp（−30.7%） | −0.236 | Sharpe 最高仍不达标 |
| v3e_peg_dd | −15.0pp | **−2.8pp（−22.8%）** | −0.268 | MDD 最接近但年化塌陷 |
| v3d/v3f | −12.6pp | −9.3pp | −0.39 | 双 PASS 但全面不达标 |

**结论：战役目标 25%/-20%/1.2 本批不可达（已实证）**。价值选股在质量小盘宇宙无 alpha（IC 全负），无法像预期那样"价值拉年化 + 择时压回撤"；Calmar 不变式（回撤每压 5pp 年化掉 3pp）再次验证：v3e 把 MDD 压到 −22.8% 时年化只剩 10.05%。

## 6. 风险与如实披露

- PEG 因子用 net_profit_yoy 代理 E(增长率)，覆盖 58.6%（pegy 59.7%）——缺值股（多为亏损/微利）被价值排序自动剔除，与 IC 覆盖一致
- 扩展 IC（a4d_ic_monthly_ext.csv）为存量 107 因子 + 9 价值因子的加列，不覆盖全部可能组合的相关性（g3 中 2 对 unresolved 按未超限处理）
- 价值因子进 registry.factors 后 g1/g2 复合 ICIR 如实下降，本批未做任何阈值/数据调整
- v3e_peg_dd 的 dd 状态机在回测 cfg 内（P5 分支），与 v2d_dd 同参数（-8%/−0.45/−3%）

## 7. 下一批方向建议

1. **价值维度降级为过滤器而非排序器**：IC 为负说明"便宜"不拉收益，但高 PEG（>3）或 PB 极端值可能是风险点；试"mv 排序 + PEG<2 过滤"（保住小市值 alpha 同时剔除最贵标的）
2. **质量/成长方向接棒**：本批证明该宇宙 alpha 在成长与质量——buf_quality 是唯一 IC 近零的价值大师指标，可扩展为"成长+质量"复合（net_profit_yoy×buf_quality）
3. **MDD≤−20% 需换赛道**（同 a2c 结论）：v3e 已到 −22.8%，再压需期权对冲/可转债-小盘轮动/现金增强，均新立项
4. **v3d/v3f 可作 paper 对照**：若用户想验证"质量带/Graham 在实盘的防守性"，可临时启用观察 2-4 周（不 activate 主版本）
5. 参数冷却：n_trials 已达 57，后续微调余量收窄，建议 ≥2 批后再做择时参数网格
