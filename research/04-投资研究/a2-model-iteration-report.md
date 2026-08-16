# A2/task-0324 模型迭代报告：107因子进进化管线（第一批5候选）

> 2026-08-16 · 状态：已完成（本批 5 候选全 REJECT，未 activate，如实留痕）
> 起点 V-v0_seed（种子B，active）；基建口径：全量池 + 成本v2 + 一字板 + 审计锁(AUDIT_LOCK_END=2024-06-30)

## 1. 迭代设计（对照 v0_seed 只改一个维度，g5 经济逻辑预埋）

| IT编号 | 版本 | 改动维度(唯一) | 经济逻辑 |
|---|---|---|---|
| IT-A2-01 | v1a_score | 排序 mv→质量复合分(0.4div/0.3roe/0.3roa/−0.3mv z) | 池内用股息+盈利+市值标准化合成替代纯市值排序，捕捉"便宜的高质量小盘"，降低纯壳股暴露 |
| IT-A2-02 | v1b_mvq | 排序 mv→小盘主导复合(0.7mv+0.3质量) | 保留规模溢价主贝塔，质量/价值微调边际选股；与v1a构成小盘/质量两极对照 |
| IT-A2-03 | v1c_liq | 流动性 min_amt 0→500万 | 剔除极端不可交易标的，降冲击成本与一字板损耗；本金1000万/20票=单票50万，500万日额≈10%日换手容量 |
| IT-A2-04 | v1d_cv | 排序 mv→0.5·(−z mv)+0.5·(−z amount_cv) | A1最强新因子(t=−11.8, adj ICIR 2.64)：成交额波动低=筹码节奏平稳、无游资炒作；与市值(簇7)信息互补 |
| IT-A2-05 | v1e_vol | 排序 mv→0.5·(−z mv)+0.5·(−z vol_20d) | A股小盘池低波动异象(t=−7.0, adj ICIR 1.57, 簇4独立)：低波动博弈溢价低、回撤更浅 |

- 前3个走引擎原生参数（sort/min_amt）；v1d/v1e 引入 A1 量价新因子（107因子进管线的实质落点），通过 `run_backtest_ext`（对 engine.run_backtest 源码做字符串级插入 ext 排序分支、exec 到副本 globals，原 engine 文件零改动）
- **等价性校验**：ext runner 以 seedB 参数(sort=mv)复跑 full+locked，指标与 v0_seed 基线**逐位一致**（diffs={}），证明 ext 分支未扰动引擎逻辑

## 2. 阶段0 基线复现

- `seedB_run_v0.py all` 复跑一次，改动零；full/locked metrics md5 与 rerun 前**字节一致**
- full：26.35% / −69.49% / Sharpe 0.9027 / 248 次调仓；locked：26.26% / −69.49% / 0.885 / 222 次调仓 —— 与 ledger 及 registry 完全一致 ✓

## 3. 逐候选回测结果（新基建口径，full=2006-01~2026-08，locked=2006-01~2024-06）

| 版本 | full 年化 | full MDD | full Sharpe | locked 年化 | locked MDD | locked Sharpe | locked 累计 |
|---|---|---|---|---|---|---|---|
| v0_seed(父) | 0.2635 | −0.6949 | 0.903 | 0.2626 | −0.6949 | 0.885 | 73.38 |
| v1a_score | 0.2200 | −0.7017 | 0.835 | 0.2155 | −0.7017 | 0.810 | 42.03 |
| v1b_mvq | 0.2509 | −0.6688 | 0.897 | 0.2475 | −0.6688 | 0.874 | 62.73 |
| v1c_liq | 0.2629 | −0.7036 | 0.900 | 0.2619 | −0.7036 | 0.882 | 72.24 |
| v1d_cv | 0.2192 | −0.7231 | 0.796 | 0.2158 | −0.7231 | 0.792 | 36.01 |
| v1e_vol | 0.1773 | −0.6671 | 0.759 | 0.1689 | −0.6671 | 0.724 | 21.62 |

- 结果文件：results/a2_<version>_{full,locked}_{nav,yearly,metrics,trades,holdings}.{csv,json}（62 个文件，供看板版本化消费）
- 台账：results/experiment-ledger.jsonl 追加 5 行（type=backtest，IT-A2-01~05，n_trials_cum 34→38）

## 4. 五门禁裁决（evolution_pipeline.py evaluate，n_trials=39，eval_window=locked）

| 候选 | g1 ICIR_is≥0.5 | g2 OOS p>0.05 | g3 |ρ|<0.7 | g4 DSR≥0.95 | g5 逻辑 | g6 MDD≤2pp | 裁决 |
|---|---|---|---|---|---|---|---|---|
| v1a_score | PASS 0.599 | PASS p0.071 | N/A* | **FAIL 0.712** | PASS | PASS +0.68 | REJECT |
| v1b_mvq | PASS 0.599 | PASS p0.071 | N/A* | **FAIL 0.760** | PASS | PASS −2.61 | REJECT |
| v1c_liq | PASS 0.599 | PASS p0.071 | N/A* | **FAIL 0.723** | PASS | PASS +0.87 | REJECT |
| v1d_cv | PASS 1.025 | PASS p0.055 | PASS | **FAIL 0.644** | PASS | **FAIL +2.82** | REJECT |
| v1e_vol | PASS 1.113 | PASS p0.352 | PASS | **FAIL 0.691** | PASS | PASS −2.78 | REJECT |

\* g3 N/A：v1a/v1b/v1c 因子集与 active(v0_seed) 一致，无新增因子，相关性门禁无信息量（管线既有语义，不计PASS不折减）
- 门禁表完整含关键数字见 results/bt_<version>/gate-report.json（每个候选 1 份，evaluate 自动产出）
- g4 DSR 全灭（阈值 0.95，实测 0.644–0.760）：DSR=Φ((sr−sr0)·√T/√denom)，n_trials=39 下 sr0=0.0425 日度，候选 sr 仅 0.0456–0.0550，未过预期最大值线
- g3 数据已真实接通：本批重建 results/factor_ic_monthly.csv（107因子×247月，W1方向调整口径，v3ak 机制 + W1 财务四因子合并）+ factor_ic_corr.csv（107×107），并与 catalog 统计一致性抽检（diff≤0.0015）

## 5. 裁决与决策留痕

- **本批 5 候选全部 REJECT，未 activate**（按纪律不强行激活）
- registry 保留 5 个 candidate 版本（model/registry/v1*.json，gate.verdict=REJECT），v0_seed 保持 active
- decision-log.jsonl：D-20260816-003~007（逐候选 evaluate_reject）+ **D-20260816-008（a2_batch_reject 批次决策）**
- IC 数据支撑产物：results/factor_ic_monthly.csv / factor_ic_corr.csv / factor_catalog_v2.json（重建）/ a2_ic_regen_meta.json（一致性抽检）

## 6. 下一批方向建议

1. **DSR 友好化（最高优先级）**：g4 是唯一全灭门禁。方向：持仓等权→波动率倒数加权、组合层低波增强，或压缩调仓换手（DSR 惩罚随尾部风险放大）
2. **v1e_vol 二次迭代**：因子门禁全绿（g1 1.113 / g2 p0.352 / g3 PASS）且 MDD 改善 2.78pp，仅 DSR 未达 —— 叠加"低波+稳定性"(amount_cv 同族)与换手约束，争取 IS 收益回归
3. **v1d_cv 换手治理**：amount_cv 信号强（g1 1.025）但 MDD 恶化 2.82pp（g6 FAIL），半衰期2月高换手 → 加换手惩罚/持仓缓冲
4. **探索更高质量因子占比**：v1a(v0.4)/v1b(v0.3) 复合分已优于纯mv排序的质量维度，可小幅上调质量权重并与低波叠加
5. **择时×选股交互**：A3 候选，在组合层叠加择时压缩危机段回撤，直接作用于 DSR 分子
