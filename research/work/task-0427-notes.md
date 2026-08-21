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

1. [x] HP 实查 r263 产物文件名（bt 前缀）：run_id=bt_r263_m1_w03_20260821，产物前缀 r263_m1_w03_*（locked/full nav、metrics、holdings、trades）
2. [x] 读 r254_score_t4.py + evolution_pipeline.py 部署函数（gate_icir/gate_max_corr/score_composite/compute_holdout_metrics/score_rank_pool/gate_mdd_vs_parent/deflated_sharpe 全文核读）
3. [ ] registry 写前 tar 备份（registry.bak.20260821_task0427.tar.gz）
4. [ ] 新增 candidate 条目（ver=a15_csad_resid，已确认库内无 a15_* 占用）
5. [ ] 评分脚本 r265_score_m11.py + 两次干跑
6. [ ] --write + manifest 重生成 + diff 校验
7. [ ] R-265 报告（编号实查：全库最大 R-264 → 本报告 R-265）+ README + completions

## 阶段 1：HP 实查事实（2026-08-21）

- 在役 a13_rsraw_e1f10dz registry：factors=[circ_mv, avg_amount_20d, pb_inv, roe_ttm, mom_pen_dz]；ext_specs=[[log_mv,1.0,-1],[amt20,1.0,-1],[pb_inv,0.7,1.0],[roe,0.3,1.0]]；metrics(locked)=ann 0.2202/mdd −0.3355/sharpe 1.3561/calmar 0.6562；gate.score=0.8781, n_trial=91, max_corr 0.2066, dsr 0.9999, icir_is 2.0717/icir_oos 2.6491；score_holdout PASS(0.258/−0.1613, nav=full 未截断旧产物)。
- M1.1 locked_metrics.json（HP 实读）：ann 0.2251/mdd −0.3423/sharpe 1.3386/calmar 0.6578/cum 41.6333/win 0.6606/years 18.48/reb 222/turnover 0.5995；panel_md5=416019cf…✓
- M1.1 full_metrics.json：ann 0.2229/mdd −0.3423/sharpe 1.3143/calmar 0.6512/turnover 0.5965（终点 2026-08-14）。
- e2_results.json（R-264 唯一取材源）：M1.1 full(t0813) ann 0.2229/mdd −0.3423/sharpe 1.314；holdout ann 0.2046/mdd −0.1780/sharpe 1.13（2024-07-01→2026-08-13, 516d）；vs 在役 pp：full_ann −0.10/full_mdd −0.68/holdout_ann −5.32；G2 locked ICIR 5f 0.6906 vs 4f 0.6451（Δ+0.0455）；5f IC: full n246 ICIR 0.6642/locked 0.6906/holdout 0.5009；4f: full 0.6211/locked 0.6451/holdout 0.4716；覆盖 mean 0.8003、有效权重份额 0.1469（名义 0.1836）；Jaccard mean 0.4837；换手 0.5965（+14.92pp vs g0_orig 0.4473）。
- 台账：63 条 backtest；HISTORICAL_TRIAL_OFFSET=34 → n_trials_cum=97（部署口径实读）。
- factor_ic_monthly.csv 有 circ_mv/avg_amount_20d/roe_ttm 列；pb_inv/mom_pen_dz 来自 a13_supp_ic_monthly.csv（load_ic_monthly 左连接）；无 csad_resid 列；factor_ic_corr.csv 无 csad 行（grep=0）。
- r0422 ic_monthly_residual.csv：ym,n,n3,ic_raw,…,ic_res_v2 列（v2 残差 IC 序列 2005-08 起）→ g3 数据源。
- ic_composite_r263_m1_w03.csv / ic_composite_4f.csv：date,ic,n,note（引擎复合 IC 月度序列，2006-02 起）→ g1/g2 数据源（任务书指定 dumps 口径）。
- full_nav：5008 数据行（2006-01-04→2026-08-14）；截 08-13 → 5007 行；locked_nav 4491 数据行。

## 评分实现决策（沿部署函数，零 pipeline 改动）

- g1/g2：构造单列 ic_df（ym=date[:7], csad_m11_comp5f=引擎复合 IC），调 ep.gate_icir —— 单列 mean(axis=1)=复合 IC 本身；4f 序列同法作参考披露。csad_resid 无部署 IC 列，因子级等权复合会静默丢掉该因子，故用引擎复合（任务书指定）。
- g3：脚本内 monkeypatch ep.load_ic_monthly（内存合并 csad_resid=ic_res_v2 列，不落盘、不落 supp 文件、用后恢复），调 ep.gate_max_corr —— 等价其第三数据源（月度 IC Pearson ≥24 月）。GUARD_CORR_CONFIG 不对称豁免不触发（csad_resid 非 ret120 替身名单），如实标注。
- g4：locked nav rets + n_trials_cum()（97）。
- g6/dd：metrics(locked mdd −0.3423) vs a13(−0.3355) → det 0.68pp（g6 disabled, 数值入 dd）。
- holdout：compute_holdout_metrics 消费新建 r263_m1_w03_full_nav_t0813.csv（refs.nav 优先），段 2024-07 起。

## 阶段 2：评分结果（两次干跑逐位一致，确定性 PASS）

- nav t0813 副本：results/r263_m1_w03_full_nav_t0813.csv（5007 行，md5 9f1e28a509abc598a03866af21a99431）
- g1：IS 复合 ICIR 年化 2.4314（179 月，引擎复合 IC 口径）PASS（4f 参考：2.2338）
- g2：OOS p=0.6143（42 月，2021-01~2024-06，mean IC OOS 0.10368 > IS 0.09588），icir_oos 2.2459 PASS（4f 参考 p=0.6847）
- g3：max|ρ|=0.2932（csad_resid vs mom_pen_dz，230 月 Pearson；其余 circ_mv −0.1186/avg_amount_20d 0.0911/pb_inv 0.1247/roe_ttm 0.1759）→ corr 分量 1.0（≤0.5 满档）；豁免不触发（csad_resid 非替身名单），无 R-245 §3.3 不对称问题
- g4：DSR 0.9999（T=4490，n_trials=97=34+63 台账口径）
- g6/dd：locked mdd −0.3423 vs a13 −0.3355 → 恶化 0.68pp ≤2pp → dd 分量 1.0
- 总分 0.8732：p 1.0 / dsr 0.999 / oos_calmar 0.503（0.6578 vs 0.6562，rel +0.24%）/ oos_sharpe 0.4839（1.3386 vs 1.3561，rel −1.29%）/ is_calmar 1 / is_sharpe 1 / dd 1.0 / corr 1.0 / logic 1.0；missing_weight 0.0、flags 空、stat_warn 无
- holdout（部署函数，t0813 副本）：ann 0.2052（≥0.6×0.2251=0.1351 ✓）/ mdd −0.1780（较 locked 改善 16.43pp ✓）→ PASS（注：0.2052 为 _seg_nav_metrics 244d 年化口径，R-264 口径 0.2046，差异为年化方法，部署口径为评分权威）
- rank_in_pool=2：a13 0.8781 > **a15_csad_resid 0.8732** > a14_crowdf2 0.8584 > v4a_mf0_trr 0.8088 > v5k_nh10 0.80 > v5i_comb 0.7985
- **三条件裁决：不过线（差 rank1 一条，−0.0049）**；stat_warn 无 ✓、holdout PASS ✓
- 差距归因：非 oos 分量两版同为满档（a13 的 p/dsr/is/dd/corr/logic 与 a15 同满档，a13 旧格式无分量明细，按恒等式反解其 oos 合计 0.1283，单分量≈0.511）；M1.1 差距全部来自 oos 两分量——locked ann +0.49pp 但 sharpe −1.29%（换手+14.9pp 抬高日波动）、calmar +0.24% 的近零增量
- holdout 弱势与评分制关系（知情义务核心）：holdout −5.32pp 未直接进入总分（评分 OOS 分量=locked 窗相对增量；holdout 只进三条件门且宽裕通过 0.2052≫0.1351）；若 M1.1 是 rank1，−5.32pp 将是激活决策的首要逆风——本次以 rank2 归档，该逆风留在档案供复看

## 阶段 3：--write 待办

- [ ] tar 备份 registry.bak.20260821_task0427.tar.gz
- [ ] 写 a15_csad_resid.json + manifest 重生成
- [ ] diff 校验：仅新增 candidate+manifest，active 逐字不变
