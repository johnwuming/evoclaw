# task-0412 notes（R-254：T4 candidate 登记 + 评分制 v1.1）
- 2026-08-21 11:40 任务置 running ✓（task 中心返回 ok）
- R-253 读完：T4=bt_r252_t4_f2_l10_20260821，四门 PASS（G1 -8.11%/G2 13.21%/G3 -33.55%,-16.13%/G4 24.96%,0.00pp），胜者=F2 优先规则
- T4 locked 审计口径：full ann 0.221396 / mdd -0.335542（R-253 §3.2）
- R-253 最大编号=253 → 本报告=R-254 ✓
- R-245 先例要点：tar 备份 registry→逐条目写 gate.score/score_components/score_flags/stat_warn/rank_in_pool/score_holdout/ic_coverage/rescored→gen_versions_manifest.py；rescore_20pct_v11.py 为参照脚本；两次干跑确定性验证后 --write
- R-252 §五：E2 胜出仅获评分制资格，不构成激活；评分制 v1.1 = rank1 + 无 stat_warn + holdout PASS + 用户确认
- 在役基准：a13_rsraw_e1f10dz score 0.8781 rank1

## 2026-08-21 11:50 HP 实况核验
- T4 产物（HP ~/quant-evolve/results/）：r252_t4_f2_l10_{full,locked}_{nav,metrics,holdings,trades,yearly}.* — **locked 窗真跑存在**（period_end 2024-06-28=AUDIT_LOCK_END，222 次调仓，18.48y，与 a13 locked 同窗同口径）
- T4 locked metrics：ann 0.2182 / mdd -0.3355 / sharpe 1.3484 / calmar 0.6503 / turnover 0.4591
- T4 full metrics（→2026-08-14）：ann 0.2216 / mdd -0.3355 / sharpe 1.3642 / calmar 0.6604 / turnover 0.4537
- R-253 审计口径（终点截 08-13）：full ann 0.221396 ≈ 0.2214（任务书引用值）
- 台账 IT-R252-04：run_id bt_r252_t4_f2_l10_20260821，ts 2026-08-21 02:24:03，data_snapshot.kline_as_of=2026-08-14，states_md5=ab4143123fefccc29a21ad6160577f16，ledger 内 full/locked 数字与产物文件一致 ✓
- **metrics 口径决策**：任务书示例「full ann 0.2214」，但 T4 有真 locked 窗产物（与在役 a13 metrics 同窗 2006-01-04→2024-06-28）→ 按库内惯例（a13/R-245 先例：metrics=locked 窗）存 locked 0.2182，R-253 审计 full 数字（0.2214 截 08-13 / 0.2216 原始终点）入 metrics_full+provenance，报告明示。理由：oos/is 分量与 a13（0.2202 locked）同窗对照才 apples-to-apples，避免 T4 全窗（含 2024-07 后 holdout 段）与 a13 locked 窗错配导致 oos 分量重复计入 holdout 段
- full_nav 末 3 行：…08-12,61.8748 / 08-13,61.6147 / 08-14,61.8606（num_held=20，08-14 为真实 mark）→ holdout 用截 08-13 副本（任务书要求，防末日伪影，与 R-253 口径一致）
- 部署函数确认：SCORE_CONFIG v1.1 权重 p.175/dsr.175/oos_calmar.125/oos_sharpe.125/is_calmar.075/is_sharpe.075/dd.10/corr.10/logic.05；GATE_CONFIG icir_is_min 0.5/oos_p_min 0.05/dsr_min 0.95/g6_enabled=False（D-20260819-G6DEL）；GUARD_CORR_CONFIG 已含 D-20260820-G3SYM 对称豁免（task-0401 已部署，R-245 §3.3 建议已落地）
- n_trials_cum=95（R-252 四点后 91→95）；AUDIT_LOCK_END=2024-06-30
- IC 数据 factor_ic_monthly.csv：247 行，a13 因子集 5 列全在（circ_mv/avg_amount_20d/pb_inv/roe_ttm/mom_pen_dz）→ T4 同因子集 ic_coverage=5/5
- 当前排名池 top8：a13 0.8781 / v4a_mf0_trr 0.8088 / v5k_nh10 0.80 / v5i_comb 0.7985 / v5j_bl30 0.7811 / v5b_amt55 0.7537 / v5c_amt73 0.7486 / v1g_ivw 0.2988
- IC 口径说明（如实）：T4 调制作用于组合构建层（ext ranksum 变换后 log_mv 列 ×m(t)），不新增/改变因子定义 → 因子级月度 IC 序列与在役 a13 同源同输入；组合级调制后 IC 无法从因子级 IC 产物直接导出，沿部署函数口径用因子级复合 IC（与 a13 评分同输入），不编造
- g3 预判：T4 因子集=在役因子集 → new_factors 空 → N/A（部署口径：无新增因子相关性无信息量）；GUARD_CORR_CONFIG 豁免（含对称修正）不触发，无 §3.3 不对称问题
- registry 无 a14/a15 条目占用 → ver 名 a14_crowdf2 可用
- 版本号确认：全库最大 R-253 → 本报告 R-254 ✓
