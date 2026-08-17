# task-0351 过程笔记 2026-08-17 22:33:56
## 阶段0 定位结论
- registry: model/registry/*.json 44版本；evolution_pipeline.py 55603B；GATE_CONFIG L57-64；verdict合成 L751-753；PASS auto-activate L778-786
- verdict合成: decisive=all PASS→PASS; any FAIL→REJECT; else N/A
- gate函数返回detail: g1 icir_is_annualized; g2 p_one_sided/mean_ic; g3 max_abs_corr; g4 dsr; g6 mdd_deterioration_pp
- 锚点: v5i_comb REJECT(dsr=0.9947,icir_is=2.5896,calmar=0.5197); v5h_xsub active PASS calmar=0.5283; v2b sota calmar=0.5074; v6a_def 无gate(candidate)
- 注意: v5a-v5i 的 registry.gate.icir_oos/mdd_det_pp 为 None → 需查 bt_*/gate-report.json 详情
## 阶段1 设计（定稿）
- SCORE_CONFIG 常量区: w_stat=.35(g2 p映射+g4 DSR映射等权) w_oos=.25(Δcalmar/Δsharpe vs在役, ±40%相对增量满档) w_is=.15(calmar/0.60+sharpe/1.20) w_dd=.10(≤2pp=1.0, 2-7pp线性衰减) w_corr=.10(≤0.5=1.0, 0.5-0.7衰减) w_logic=.05(≥20字=1.0/短=0.6/空=0)
- N/A分量按权重重归一（对齐门禁层N/A不折减）；缺权>0.30→flags=partial，不进排名池不可auto-activate
- stat_warn: g2 p<0.01 或 DSR<0.90（v5i p=0.0389不触发）
- 自动activate: rank==1(池=candidate∪pending∪active, 排除partial) 且 (无stat_warn 或 ≥1.10×第二名) 且 自身非partial
- verdict值改SCORED（历史PASS/REJECT/legacy数据不动）；_do_activate校验放宽: legacy PASS/grandfathered 或 gate.score存在 或 --force
- 数据源: 33个bt_*/gate-report.json + a2b/a2c/a4d/a5/mf gate_table(含oos_p/dsr/mdd_pp/max_corr) + a7_gates_result.json(v5批9个全量) → 44版本全覆盖; v6a_def无gate数据→partial
- 上岗血统(switch_log): v0_seed→v1i_q3z(0816 14:53)→v2b_trr(0816 15:24)→v5h_xsub(0817 04:57); S_oos父版本按时点取
- 手算锚: v5h≈0.86 > v5i≈0.81(v5批第2) > v5g≈0.80; v6a_def≈0.99但partial不入池; v1i(retired不入池)估0.90
- 注意: v4a_mf0_trr(calmar0.5536,被g1拒)可能反超v4b_mve1(0.4285,人工PASS) → 预期列入不一致清单(g1不在R-220公式内)
