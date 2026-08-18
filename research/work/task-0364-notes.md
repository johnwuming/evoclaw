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

### T+22min 首跑失败→修复
- merge_asof 全局排序 bug（by=code 时 right 需全局按 key 排序，a9 同款处理）；已 sed 修复 avail_date/m_end 全局排序后重启
- 教训：merge_asof(by=...) 的 right 必须 sort_values(key) 全局序，(code,key) 序不够

### T+60min 续跑验收完成（15:20-15:35）
- 后台 run 实际已于 14:23 全部完成（logs/a4b_run.log: 469s, 6/6 候选），无需重跑
- **n_trials=6，全部 REJECT**（HP results/a4b_gate_table.json + a4b_backtest_summary.json）

| 候选 | locked 年化/MDD | holdout 年化/MDD | IC(IR)_locked | 门禁挂点 |
|---|---|---|---|---|
| s1a mv+PEG<2 | 15.44%/-29.98% | 7.00%/-16.82% | 0.043(0.17) | g2, g5(corr .97) |
| s1b mv+PEG<1.5 | 15.22%/-30.01% | 5.04%/-18.49% | 0.046(0.18) | g2, g5 |
| s1c mv+PEG≤q60 | 16.29%/-30.07% | 12.19%/-18.47% | 0.044(0.17) | g2, g5 |
| s2a gqblend | 13.77%/-28.50% | 10.92%/-15.61% | 0.034(0.18) | g2 |
| s2b gqrank | 13.97%/-27.89% | 10.93%/-15.61% | 0.021(0.11) | g2 |
| s2c growdom | 13.96%/-27.72% | 10.57%/-15.61% | 0.031(0.19) | g2 |

- 对照 v5h_xsub 15.74%/-29.80%：最佳年化 s1c 仅 +0.55pp（新血统线需 +2pp）；最佳 MDD s2c 改善 2.08pp 但年化 -1.78pp → 两条线均无候选达标
- g1/g3/g4 全 PASS（turnover 0.29-0.34，容量 0.59-0.85亿 vs v5h 0.7× 线全过）
- **数据缺陷注意**：IC holdout 仅 2024-07/08 有非空横截面（因子面板末端缺失；nav 本身到 2026-08-14）→ holdout IC 证据极薄，但 g2 挂点在 locked ICIR（0.11-0.19 < 0.25），结论不受影响
- 覆盖率：peg_np 53.1%（na 剔除影响 s1a/s1b 宇宙），grw/bufq ≥99%
- ledger 补登记：bt_a4b_batch + ev_a4b_batch（n_trials_cum 86→92）+ decision-log D-20260818-A4b-1（脚本原本无 ledger 写入逻辑，已补）
- VPS 副本：work/task-0364-out/（33 文件：summary/gate/ic_monthly/各候选 metrics+yearly + a4b_run.py 507 行）
- **结论**：价值降级为过滤器（结构1）与成长×质量复合接棒（结构2）均未过新血统线；PEG 过滤闸不提供足额 alpha，复合结构牺牲年化换 MDD 不达 +2pp 线 → 全部不 activate，不动 registry
- 断点（阶段B，未启动）：R-222 防守端 MA15_on_f0（14.63%/-24.67%）组合方向，或放弃选股层重设计路线——留人工拍板
