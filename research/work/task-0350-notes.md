# task-0350 过程笔记（R-223 量化迭代流程与规则总纲）

## 1. HP registry 现读验收（2026-08-17 22:0x）
- registry 共 48 个文件（含 .main.json.snapshot 4 个，实际版本 ~44 个）
- status 分布：**active = v5h_xsub** ✓、**sota = v2b_trr** ✓、**candidate 含 v6a_def** ✓
- 其余大量 candidate / pending / retired（v0_seed、v1i_q3z retired）
- 版本时间线：v0_seed → v1a-v1k（第一代单因子）→ v2a-v2f → v3a-v3f → v4a-v4e → v5a-v5i → v6a_def
- 验收标准1：通过

## 2. VPS 已有报告清单（05-量化投资/）
- R-195 RD-Agent 评估、R-196 执行总纲、R-198 因子清单调研、R-200 平衡问题
- R-201/202 部署与框架调研、R-203 流程梳理与自动化改造、R-204 行业标杆
- R-205/206/207 Tab重构三连、R-213 质疑评审
- R-216 因子普查、R-217 换赛道、R-218 华福调研、R-219 约束审计、R-220 处置建议、R-221 SSH排查、R-222 A9实验
- work/ 下 notes：task-0331~0349

（后续持续追加）

## 3. 现役/关键版本配置（registry 现读）
### v5h_xsub（active，activated 2026-08-17 04:58:48）
- selection: strategy=dividend_quality_smallcap_seedB, sort=ext(ext_factor=low_amount, ext_weights=[1.0,0.0]), e1_guard=true, mom_cols=[ret120], xsub_days=365（次新剔除：上市不满1年剔除，first_last字段实现含退市）
- factors: div_yield_ttm / roe_ttm / roa_ttm / circ_mv / ret120
- timing: q3z_x_ew_trend_overlay；q_key=q3z(win36,zscore,hi1.0,cut0.40,w_min0.3)；trend=池内等权指数(含退市)月末收盘 vs MA200 破位×0.6；月度乘法合成，无重裁剪(自然下限0.18)
- gate: DSR=0.9923, n_trial=85, verdict=PASS；logic=次新剔除(P0-5)降尾部风险
- provenance: task-0338 A7 P0 增强因子批次收口, parent=v4b_mve1, report=results/a7-iteration-report.md

### v6a_def（candidate，created 2026-08-17 12:12:45）
- selection 与 v5h 完全一致（四闸门+ext low_amount+E1+xsub365）
- timing: q3z(w_min=0.0) × MA15 快趋势，自然下限 0.0；[A9 E2 网格 MA15_on_f0]
- gate verdict=candidate；注册线: MDD 改善 5.13pp(≥3) 且年化损失 1.11pp(≤2)；用户 2026-08-17 20:10 拍板注册防守档；Calmar 0.593 > v5h 0.528
- provenance: batch=A9, task-0342, experiment=E2 timing grid MA15_on_f0

### v2b_trr（sota，evaluated 2026-08-16 15:24:02）
- selection: sort=mv, div_min=0.02, roe_min=0.15, roa_min=0.10, n_hold=20, price_cap=10.0, cost_model=v2, limit_board=on, capital_base=1000万
- timing: 同结构 q3z(w_min0.3)×EW-MA200
- gate: ICIR_IS=0.5994, ICIR_OOS=-0.0525, DSR=0.9873, n_trial=51, MDD改善 -4.88pp（即恶化4.88? 待对符号：mdd_deterioration_pp=-4.88 为改善4.88pp）, oos_split=2021-01
- provenance: task-0327 A3 fork 回撤攻坚, parent=v1i_q3z

## 4. decision-log 全貌（53 条）
- 结构字段：ts/decision_id/type/version/trigger/action/backup/params/rollback_condition/expected_impact/code_ref/data_snapshot
- 类型序列：seed_reset → bootstrap → evaluate_pass/reject → activate → a2b/a2c_batch_activate → a4d/a5/a6_batch_closeout → A7 closeout+addendum → R220 处置 → A9 closeout+register_candidate → paper_timing_align → A8 closeout
- 关键决策详情：
  - D-20260816-SEEDB-RESET: task-0316 Q4b 收口后种子B重置；params={div_min0.02,roe_min0.15,roa_min0.10,sort:mv,n_hold20,price_cap10.0}；备份 tar 729条目 md5 b2e1d572
  - D-20260817-A7-01: A7 收口 9 版本（v5a_amt37/v5b_amt55/v5c_amt73/v5d_amh55/v5e_cv73/v5f_cal/v5g_lim/v5h_xsub/v5i_comb）；v5h activate；回退条件=激活后回撤超阈值或paper显著劣于endtoend→rollback v2b_trr
  - D-20260817-A9-1 (19:50): A9 收口结论 6 条：
    (1) 四闸门=真实安全换收益交易(+6.0pp年化/+7.0pp MDD)
    (2) PB 价值 alpha 主要藏于原始宇宙（质量宇宙近12月IC≈0.004失效, raw仍0.0324, 微盘段近端归零）
    (3) 闸门外价值暴露(E3 raw)较纯去闸门(E1 raw)省3.23pp回撤且年化持平
    (4) MA15_on_f0 过防御线(MDD改善5.13pp, 年化损1.11pp)→防守备选操作点（后经用户20:10拍板注册为 v6a_def candidate）
    (5) q3z off 纯趋势空仓全部 MDD -38%~-52%，外部"MA15空仓压回撤"证伪
    (6) 当前可达前沿 v5h(15.7/-29.8)~raw(21.8/-36.8)，防守端点 MA15_on_f0(14.6/-24.7)，25%/-20% 双目标仍不可达
  - D-20260817-A9-2 (12:12): v6a_def 注册 candidate（不切换现役，上线需 evaluate/评分流程）
  - D-20260817-R220N37 (12:28): paper 调仓时点对齐回测口径（R-219 #37 发现，task-0347）；下次调仓 2026-09-01
  - D-20260817-A8-1 (20:58): A8 收尾；bucket raw 年化+2.55pp 过线但 MDD 恶化4.21pp>2pp → 不注册；合成方式归因闭环：ranksum 排序层最优(抗极值+全序分辨率)；bucket 顶部分辨率不足且并列推高换手0.536全场最高；zscore quality宇宙最优但raw被极值扭曲；前沿 v5h(15.7/-29.8)~raw ranksum(21.8/-33.6)

## 5. 五门禁定义（evolution_pipeline.py 现读，L57-65 GATE_CONFIG）
- STATUS_ENUM = [candidate, pending, active, sota, retired]
- g1 icir_is_min=0.5：IS 全样本复合 ICIR 年化下限
- g2 oos_p_min=0.05：OOS 相对 IS 劣化单侧 t 检验 p>0.05（不显著劣于）；oos_split_ym=2021-01
- g3 max_corr_max=0.7：候选新增因子 vs 在役因子最高|ρ|<0.7；数据源 factor_ic_corr.csv 优先/catalog corr_alerts；无新增因子→N/A（E3修复 task-0292）
- g4 dsr_min=0.95：Deflated Sharpe（Bailey & López de Prado 2014），n_trials 累计计数
- g5 logic 非空：候选改动须有逻辑说明
- g6 mdd_vs_parent_max_pp=2.0：endtoend MDD 较父版本(active)恶化 ≤2pp，**一票否决**（E3修复 task-0292；数据缺失→N/A 不折减）
- verdict 规则：decisive(有 PASS/FAIL 的门禁) 全 PASS → PASS；L778: PASS 且 prev=candidate → 自动 activate（待确认具体行文）
