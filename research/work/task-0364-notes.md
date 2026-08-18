# task-0364 (A4b) 选股层重设计 过程笔记

- 目标：结构1（mv 排序 + PEG<2 过滤闸）vs 结构2（成长×质量复合接棒），对照 v5h_xsub 15.74%/-29.80% / v2b_trr 15.15%/-29.86%
- 成功标尺：新血统线 = 年化 +2pp 且 MDD 恶化 ≤2pp（相对现役对照），五门禁全过
- 交付：R-235 报告 + HP results/a4b_* + ledger/decision-log 登记

## 时间线

### T0 本地输入已读
- R-226：建议原文——价值降级为过滤器（mv 排序 + PEG<2 过滤）；成长×质量复合接棒（buf_quality 唯一近零可用价值锚）
- R-222：A9 结论——raw 宇宙 21.76%/-36.78%；E3 raw+pb_inv 排序 21.76%/-33.55%；质量宇宙内 PB IC 近端失效；MA15_on_f0 防守端 14.63%/-24.67%
- 本地 memory 无 A4D 结论细节 → 需从 HP ledger/results 提取

（进行中：HP 环境勘察）

### T+15min HP 勘察完成
- A4D 定义复原（报告+产物）：peg_np = pe_ttm(circ_mv/net_profit_ttm, PIT avail_date) / net_profit_yoy(fin_deep_monthly_panel_ak, usable_from 月频面板, yoy 单位%)，覆盖 58.6%
- A4D 六门禁结果：v3d_buf_trr 12.38%/-29.29% 与 v3f_grm_trr 12.39%/-29.47% 全 PASS 但年化不达标留 pending；价值 IC 全负结论复用
- buf_quality 原始代码已删（a4d 脚本清理），按报告口径重建代理：z(roe_ttm)+z(gp_margin)+z(cf_np_ratio)-z(debt_to_asset) 月度横截面
- 基建：a9_common.patch_engine 可复用（ext zscore/ranksum + e1_guard + xsub + raw_universe），fund=panel[date<=d].tail(1) → 新列自动传播
- 候选设计（6个，全部 v5h 骨架 e1+xsub365+q3z_tr 择时，quality 闸门 BASE 同 v2b/v5h）：
  - 结构1：s1a mv主干+PEG<2(na剔除)；s1b PEG<1.5；s1c PEG≤60分位(na保留)
  - 结构2：s2a z(0.6·-mv+0.2·grw+0.2·bufq)；s2b ranksum(-log_mv, npg, bufq, gpersist)；s2c z(0.5·-mv+0.35·grw+0.15·bufq)
  - grw = mean(z(npg), z(rev_yoy), z(growth_persist))
- 五门禁：g1 locked mean_IC>0；g2 ICIR_m(locked)≥0.25 且 holdout IC>0；g3 turnover≤0.60；g4 容量≥0.7×v5h（0.05×持仓amt20均值×n_hold 口径）；g5 月收益 corr vs v2b_trr/v5h_xsub <0.97
