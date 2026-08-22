# task-0455 S1: PCR 情绪确认项/降权调制 E2 预注册+执行 工作笔记

## 时间线
- 00:15 任务下发（R-277 S1，用户拍板全部推进）
- E1 依据 R-272：PCR_oi low≤0.30（roll36m 分位）次月 M_micro −1.98% vs 无条件 +0.06%（−2.04pp），胜率 33.3%（n=27），pre −1.72(n=9)/post −2.11(n=18) 同号，corr(rv)=−0.343/Jac=0.04；A13 副载体 −0.64pp（在役未吸收完）。旗舰 2023-12→2024-01 −24.2%。

## 先例结构（已读）
- R-252/R-253（拥挤度降权 E2）：runner 补丁链 a9_common.patch_engine，G0 同数据对拍逐位一致，4 点网格，窗口统一截 2026-08-13，台账 IT-R2xx。T4 胜者（F2 线性×λ1.0，危机 MDD +1.45pp）。
- R-254（T4 评分制 v1.1）：0.8584 rank2 败于 a13 0.8781。五门=g1(IC)/g2(ICIR-DSR)/g3(corr)/g4/g5，三条件裁决=rank1+无 stat_warn+holdout PASS。
- R-264/R-265（csad E2→评分）：同构，M1.1 rank2 −0.0049。
- R-270/R-271（风格轮动 E2 负结果）：NAV 混合形态，G1 危机改善门主门。
- 窗口纪律沿 R-253：指标终点截最后真实 mark 公共日。

## 待核验
- [ ] registry 评分制 v1.1/v1.2 实际状态（先读再算）
- [ ] HP r272 数据（monthly_panel.csv 结构、PCR_oi 序列覆盖）
- [ ] 引擎组合构建方式（新入场定义、权重结构）
- [ ] r252_run.py 补丁链可复用性

## 决策记录
（边查边写）

## HP 环境核验（00:20-00:28）
- registry：a13_rsraw_e1f10dz active；候选池 a14_crowdf2(0.8584)/a15_csad_resid(0.8732)；无 v1.2 评分配置激活痕迹 → 沿用 v1.1 部署口径
- 五门 v1.1 部署口径（evolution_pipeline.py GATE_CONFIG 实读）：g1 ICIR_IS年化≥0.5；g2 OOS劣化单侧p>0.05（split 2021-01，锁 2024-06）；g3 max|corr|≤0.7；g4 DSR≥0.95；g5 logic 非空；g6 MDD 硬判定已禁用（数值入评分 dd 分量）。三条件上岗=rank1+无stat_warn+holdout PASS
- 引擎机制（backtest_dividend_quality_iter.py 实读）：月调仓=每月首交易日；等权 w=1/len(new_pool)→pending_holdings 权重字典；日收益=Σw·r/Σw_valid；择时 eff_ret=day_ret×pos_ratio×timing_ratio（q3z×EW-MA200 在总仓位层）；成本v2 按卖+买逐笔 w_each 估
- r252_run.py 补丁链模板：_prev_month_key(d)=调仓日前一自然月 → 查冻结状态表；FULL_RANGE=("2006-01-01","2026-08-14")，窗口指标截 2026-08-13（R-253 纪律）；G0=同数据同截断 λ=0 注入 vs orig a9 路径逐位一致
- r272 数据在位：monthly_panel.csv 249 行（2006-01→2026-07，含 pcroi_pct 列）、pcr_monthend.csv 342 行

## 形态定稿（预注册写入前决策）
- 信号：pcroi_pct(月m)≤30（roll36m 分位，R-272 冻结口径）→ 月 m+1 调仓 active；2017-02 前无信号=不干预
- T1=新入场降权λ0.7；T2=λ0.8；T3=确认项否决 added 中排名最弱 ⌈20%×len(added)⌉ 只；G0=λ1 恒不触发（逐位对拍，不计 trial）→ n_trials=3≤4
- 实现锚点（引擎源码原样区，A9 补丁不触碰）：①权重块 `w = 1.0 / len(new_pool)...pending_holdings`；②`added = [c for c in target_pool if c not in holdings]`（veto 注入点）；③成本v2 买入 `order_amt = port_val * w_each`（降权月买 entrance 用实际权重 w_each×wbuy，wbuy=1.0 时位不变）
- G0 结构保证：inactive/λ=1 走原字面分支 → IEEE 逐位一致
