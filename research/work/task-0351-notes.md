# task-0351 过程笔记 2026-08-17 22:33:56
## 阶段0 定位结论
- registry: model/registry/*.json 44版本；evolution_pipeline.py 55603B；GATE_CONFIG L57-64；verdict合成 L751-753；PASS auto-activate L778-786
- verdict合成: decisive=all PASS→PASS; any FAIL→REJECT; else N/A
- gate函数返回detail: g1 icir_is_annualized; g2 p_one_sided/mean_ic; g3 max_abs_corr; g4 dsr; g6 mdd_deterioration_pp
- 锚点: v5i_comb REJECT(dsr=0.9947,icir_is=2.5896,calmar=0.5197); v5h_xsub active PASS calmar=0.5283; v2b sota calmar=0.5074; v6a_def 无gate(candidate)
- 注意: v5a-v5i 的 registry.gate.icir_oos/mdd_det_pp 为 None → 需查 bt_*/gate-report.json 详情
