# task-0427 过程笔记（csad M1.1 评分制 v1.1）

> 硬约束：零回测、零引擎/pipeline/paper_engine/crontab 改动；评分门槛/权重一字不改；registry 仅新增 candidate + manifest。
> 链路：R-257→R-260→R-263（预注册）→R-264（E2 PASS，胜者 M1.1 w=0.3，IT-R263-01）→本任务。

## 阶段 0：上下文要点（已读必读文档）

- R-264 胜者全指标（终点截 2026-08-13 口径）：full ann 0.2229 / MDD −0.3423 / sharpe 1.314；locked 0.2251 / −0.3423；holdout ann 0.2046 / MDD −0.1780。
- 硬披露：holdout ann −5.32pp vs 在役；换手 +14.92pp（0.4473→0.5965）；locked +0.49pp。
- G2 数字：locked ICIR 5f 0.6906 vs 4f 0.6451（Δ+0.0455）；holdout 5f ICIR 0.5009（G3 红旗未触发）。
- 冻结面板 csad_resid_monthly.csv md5=416019cf5368bde27c289949069f6193。
- 在役基准 a13_rsraw_e1f10dz score 0.8781（rank1）。评分口径：SCORE_CONFIG v1.1（p/dsr 0.175, oos_calmar/oos_sharpe 0.125, is_calmar/is_sharpe 0.075, dd 0.10, corr 0.10, logic 0.05；g6 禁用 D-20260819-G6DEL；g3 含 G3CORR+G3SYM 豁免）。
- R-254 先例（T4）：locked 窗真跑 metrics + full 截 t0813 副本供 compute_holdout_metrics；两次干跑逐位一致后 --write；registry 回写字段 gate.score/score_components/score_flags/stat_warn/rank_in_pool/score_holdout/ic_coverage + scored{task,at}。
- R-245 先例：函数清单 gate_icir/gate_max_corr/deflated_sharpe/gate_mdd_vs_parent/score_composite/compute_holdout_metrics/score_rank_pool；summary json 落盘 results/。
- R-263 §五.4/§五.5：E2 胜出仅获评分资格；G3 未触发但 holdout NAV 弱势是已知事实，评分制 OOS 分量正对衰减区（尾段 ICIR −0.269），激活先验低——报告必须写知情段。
- IC 口径：r263 dumps 有 g0 与 m1 排序分（work/r263/dump_r263_{g0_w0,m1_w03}.parquet），ic_composite_{4f,r263_m1_w03}.csv 已有复合 IC 月度序列；五因子复合 IC 从 dumps/已有 csv 取。覆盖度如实标注（csad_resid 面板 80.03% 池覆盖）。
- corr 口径：与在役 a13 因子集最高|ρ|——R-257 §三.4 给出 csad_resid 与在役四因子截面秩相关全部 |ρ|<0.6（amt20 0.27/pb_inv −0.18/log_mv −0.10/roe −0.04）→ 但评分用的是 gate_max_corr 部署函数口径（月度 IC 序列相关），需按函数实算。注意 R-245 §3.3 GUARD_CORR_CONFIG 豁免不对称问题若撞上如实标注。

## 待办清单

1. [ ] HP 实查 r263 产物文件名（bt 前缀）
2. [ ] 读 r254_score_t4.py / rescore_20pct_v11.py 方式
3. [ ] registry 写前 tar 备份
4. [ ] 新增 candidate 条目
5. [ ] 评分脚本 r265_score_m11.py + 两次干跑
6. [ ] --write + manifest 重生成
7. [ ] R-265 报告 + README + completions
