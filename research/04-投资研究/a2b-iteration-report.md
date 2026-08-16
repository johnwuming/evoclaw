# A2-b2/task-0325 第二批模型迭代报告：DSR 友好化（6候选，2 PASS，1 activate）

> 2026-08-16 · 状态：已完成（v1i_q3z 五门禁全 PASS → activate；v1k_q5z PASS 留备选；4 候选 REJECT）
> 父版本 V-v0_seed（locked 26.26%/-69.49%/0.885）；基建口径：全量池+成本v2+一字板+审计锁(AUDIT_LOCK_END=2024-06-30)
> 批次目标：冲「大幅提升 SR」过 g4 DSR（第一批唯一全灭门禁，0.644-0.760@N=39）

## 0. 批次设计逻辑（先算通过线，再定候选）

- DSR 门禁本质：sr0 = c(N)·σ_daily，通过需 sr ≥ sr0 + 1.6449·√denom/√(T-1)
- N=45 时 c=2.2356；T=4490, denom≈1.03 → margin≈0.0249；sr=Sharpe/15.875
- **通过线换算**（关键推导，写进设计阶段）：
  - σ_d≈0.0203（父本档）→ 需 Sharpe≥1.09（父本 0.885，纯选股改善够不着）
  - σ_d≈0.0125（择时档）→ 需 Sharpe≥0.84；σ_d≈0.0113 → ≥0.80
- 结论：**降 σ 的仓位类改动（择时/波动率目标）是过 g4 的唯一现实路径**——σ 同时进分子与 sr0（双重利好），而排序/加权/换手改善 SR 幅度有限
- 6 候选覆盖 4+2 方向矩阵（对照 v0_seed 各只改一个维度）：

| IT编号 | 版本 | 改动维度(唯一) | 经济逻辑(g5预埋) |
|---|---|---|---|
| IT-A2B-01 | v1f_lv70 | 排序: mv→0.3·(−z mv)+0.7·(−z vol20) | 方向a低波增强: v1e 已证降回撤但 SR 受损，加深倾斜换 σ↓ |
| IT-A2B-02 | v1g_ivw | 组合构建: 等权→波动率倒数加权 | 方向b: 池内风险平价，高波股降杠杆 |
| IT-A2B-03 | v1h_buf | 交易治理: 排名缓冲带 top20进/top40出 | 方向c: hysteresis 降换手→成本v2冲击↓→净SR↑ |
| IT-A2B-04 | v1i_q3z | 择时叠加: +q3z 估值择时(T线同款) | 方向d: PE 36月zscore>1 降仓，σ与MDD双降，DSR分子分母同改善 |
| IT-A2B-05 | v1j_vt18 | 仓位管理: 组合目标波动率18% | 方向e: 波动聚集性可预测，trailing 63d 自适应缩放 |
| IT-A2B-06 | v1k_q5z | 择时叠加(备份): +q5z 60月长窗 | 方向d': 与q3z corr 0.964，家族第二抽签 |

## 1. 阶段0 复现与等价校验

- **等价性校验**：本批扩展 ext runner（第一批方法 + 三路新 patch：weight_mode=inv_vol / rank_buffer / vt_target，全部 cfg 开关守卫，引擎文件零改动），开关全关复跑 full+locked，与 seedB 基线指标**逐位一致（diffs={}）**
- **v1e_vol 复跑核对**：第一批数字完全可复现（full/locked diffs={}，a2b_repro_v1e_* 留痕）
- ledger 起点 n_trials_cum=39（offset 34 + backtest 5）

## 2. 逐候选回测结果（新基建口径，full=2006-01~2026-08，locked=2006-01~2024-06）

| 版本 | full 年化 | full MDD | full Sharpe | locked 年化 | locked MDD | locked Sharpe | locked Calmar | 换手 |
|---|---|---|---|---|---|---|---|---|
| v0_seed(父) | 0.2635 | −0.6949 | 0.903 | 0.2626 | −0.6949 | 0.885 | 0.378 | 0.272 |
| v1f_lv70 | 0.1708 | −0.6551 | 0.749 | 0.1647 | −0.6551 | 0.721 | 0.251 | 0.529 |
| v1g_ivw | 0.2694 | −0.6973 | 0.929 | 0.2732 | −0.6973 | 0.920 | 0.392 | 0.272 |
| v1h_buf | 0.2707 | −0.6891 | 0.934 | 0.2699 | −0.6891 | 0.915 | 0.392 | 0.168 |
| v1i_q3z | 0.1584 | **−0.3474** | 0.921 | 0.1580 | **−0.3474** | 0.905 | **0.455** | 0.272 |
| v1j_vt18 | 0.1852 | −0.5015 | 0.865 | 0.1808 | −0.5015 | 0.840 | 0.361 | 0.272 |
| v1k_q5z | 0.1704 | −0.3737 | 0.932 | 0.1701 | −0.3737 | 0.917 | 0.455 | 0.272 |

- 结果文件：results/a2b_<version>_{full,locked}_* 5件套×6候选=60件 + 等价/复跑校验 20 件 + 汇总 a2b_backtest_summary.json
- 亮点：v1i_q3z MDD **−69.49%→−34.74%（改善 34.75pp）**，Calmar 0.378→0.455；v1h_buf 换手降 38%（0.272→0.168）；v1g_ivw 年化微升（26.94%）
- 择时候选换手与父完全一致（仓位系数不改进出名单——维度隔离干净）

## 3. 五门禁裁决（evolution_pipeline.py，N=45，eval_window=locked）

| 候选 | g1 ICIR_is | g2 OOS | g3 |ρ| | g4 DSR | g5 | g6 MDD | 裁决 |
|---|---|---|---|---|---|---|---|
| v1f_lv70 | PASS 0.599 | PASS | PASS 0.558 | **FAIL 0.6834** | PASS | PASS −3.98pp | REJECT |
| v1g_ivw | PASS 0.599 | PASS | N/A | **FAIL 0.7666** | PASS | PASS −0.24pp | REJECT |
| v1h_buf | PASS 0.599 | PASS | N/A | **FAIL 0.7656** | PASS | PASS +0.58pp | REJECT |
| **v1i_q3z** | PASS 0.599 | PASS | N/A | **PASS 0.9776** | PASS | **PASS −34.75pp** | **PASS** |
| v1j_vt18 | PASS 0.599 | PASS | N/A | **FAIL 0.8953** | PASS | PASS −19.34pp | REJECT |
| **v1k_q5z** | PASS 0.599 | PASS | N/A | **PASS 0.9743** | PASS | **PASS −32.12pp** | **PASS** |

- g3 N/A：v1g/v1h/v1i/v1j/v1k 因子集与 active 相同（择时/加权/缓冲不引入新因子），无信息量；v1f 因子集同 v1e（volatility_20d 已入 catalog）
- g4 DSR 明细（v1i_q3z）：sr=0.0570 vs sr0=0.0242，σ_d≈0.0108（父 0.0203，**降 47%**），skew −0.19，kurt 5.96（尾部也改善）
- 门禁表完整数字：results/bt_<version>/gate-report.json（逐候选）+ results/a2b_gate_table.json（汇总）
- **设计预判兑现**：仓位类候选（σ↓）恰好是唯二过关者；排序/加权/换手类 SR 改善 0.72-0.93 不足以过线——验证「sr0=c(N)·σ」推导

## 4. 裁决与决策留痕

- **v1i_q3z 五门禁全 PASS → activate**（registry candidate→pending→active，main.json md5 fbba3372→35b8e6a7）
  - 选择依据：DSR 余量更大（0.9776 vs 0.9743）、MDD 改善更深（34.75pp vs 32.12pp）、T线预验证主候选（q5z 为设计备份）
- v1k_q5z PASS，留 pending 备选（registry 在位，可随时 activate）
- 现役切换：**v0_seed（sota）→ v1i_q3z（active）**
- decision-log：D-20260816-009~014（逐候选 evaluate）+ D-20260816-015（activate v1i_q3z）+ D-20260816-016（a2b_batch_activate 批次决策）
- ledger：+12 行（6 backtest + 6 evaluate），n_trials_cum 39→45
- 回滚兜底：v0_seed.main.json.snapshot 字节级快照在位（rollback --to v0_seed），Dashboard 时间线一键回退

## 5. 风险与如实披露

- **收益换风险**：v1i_q3z 年化 15.80% vs 父 26.26%（−10.46pp），DSR 过关本质是 σ 大幅压缩；用户若偏好收益侧，q5z（17.01%）或未来 A3 深化可再平衡
- 择时层引入新数据依赖（data/macro/index_valuation.parquet，月更）；registry.timing 已登记 data_source/disable_switch
- v1g_ivw 成本模型保持等权近似（排序名单不变，仅权重不同，冲击成本二阶误差）
- v1j_vt18 DSR 0.8953 贴线未过——波动率目标方向有效（MDD −50.15%），18% 可微调或与择时合成后再战

## 6. 下一批方向建议

1. **A3 择时×选股交互深化**：v1i_q3z 已在役，下批在其基础上叠加选股维度（如 v1e_vol 排序 × q3z 择时），检验乘性合成的边际增益
2. **q3z 参数微调第三抽签**：N 已到 45，多一次 PASS 窗口内微调（如 cut 0.40→0.35）会再增 n_trials，需权衡；建议时间冷却后再试
3. **vt18+择时合成**：v1j（DSR 0.895）与择时正交，合成或过线但 n_trials 成本高——建议预注册假设后一次跑
4. **paper 对齐**：模拟实盘切到 v1i_q3z 口径（timing 层启用），观察 2-4 周与 endtoend 一致性
