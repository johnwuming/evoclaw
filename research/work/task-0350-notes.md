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
