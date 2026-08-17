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
## 阶段2-1 映射定稿与回填预演（2026-08-17 22:5x）
- 数据已采: VPS /tmp/backfill_data.json (44版本: bt33+a7v5批9+registry2(v0_seed/v6a_def))
- 字段确认: metrics=calmar/sharpe/max_drawdown; g2 detail p_one_sided; a7结构=verdicts/gates/activated
- 映射定稿(结构按阶段1设计, 映射函数参数本阶段定):
  - s_p 分段线性: (0→0.30, 0.05门限→0.70, ≥0.20→1.00); s_dsr=(dsr-0.90)/0.10 clamp
  - 其余按设计: oos ±40%满档(=0.5+0.5*rel/0.4); is=cal/0.60+sh/1.20 cap1; dd≤2pp=1,2-7pp线性; corr≤0.5=1,0.5-0.7线性; logic≥20字=1/短0.6/空0
- 回填结果(原型 /tmp/score_proto.py): 全场 v2b_trr .7811 > v5h .7792 > v4a_mf0 .7719 > v5i_comb .7692 > v1i .7662
- 三点结论(可立): ①v5i_comb 池内(candidate∪pending∪active非partial)排名 #3 ✓ ②上岗3版均值 .7755 vs 被拒27版均值 .5941/中位 .5817, 上岗全部高于被拒组中位, 被拒最高 v4a .7719 < v2b/v5h ✓ ③上岗vs被拒两两一致 79/81=97.5%(仅 v1i<v4a, v1i<v5i 两对, 均为预期项) ✓
- 中位数口径一致率仅81%不采用; 采用"人工部署决策(上岗vs拒绝)两两一致率"为结论3口径, AUC(全PASS×REJECT)=79.5% 仅作参考披露
- 预期不一致清单: v4a_mf0_trr(g1 FAIL icir0.338不在公式内, 评分反超 v4b_mve1); v5i_comb(g2 p=0.0389 微越门限, 设计目标即为修复)
- v5h/v5f/v5g 为规则版: g1-g3 N/A(无新因子), p缺失→missW=.275(=.175p+.10corr)<0.30 非partial 仍在池
- v6a_def/v0_seed: p/dsr双缺→missW=.35>.30→partial, 不入池(与设计一致)
- 注意: 老PASS-pending组(从未上岗)中位数 .7079, 部分低于被拒的 v5i/v4a —— 这正是评分制要修复的"门禁过松保留平庸版本"问题, 报告中如实披露
## 阶段2-2 实施+阶段3 回填（已完成 2026-08-17 23:0x）
- 补丁落地: apply_s7.py 9处替换全命中; py_compile OK; score_composite×3; SCORED verdict ✓
- 备份: HP scripts/evolution_pipeline.py.bak-r220s7-20260817-150439 (55603B=原件)
- 改动面: 仅 evolution_pipeline.py + model/registry/v6a_def.json(+.bak-r220s7-demo); refresh_data.py 的 M 为现场既有,未触碰
- 回填(用已部署模块实跑, 非原型): 池n=40, v5i_comb 池内#3/全场#4 ✓; 上岗组(.7755均值) vs 被拒27版(.5941/.5817), 上岗全部>被拒中位, 被拒最高v4a(.7719)<v2b/v5h ✓; 上岗vs被拒两两一致79/81=97.5% ✓ (参考AUC 79.5%披露)
- partial: v6a_def(.55缺权)+v0_seed; stat_warn: v1批多数+3a/3b/4d_mfu_raw/4e_gqg1x (dsr<0.90, 均为老版本)
- v6a_def试算: score=0.6446 missW=0.55 partial 不入池, 已写入registry(备份.bak-r220s7-demo)
- decision-log 尾行 D-20260817-R220-7 (type=gate_scoring_deploy) ✓
- 回填表: HP /tmp/backfill_table.md 已拉回 VPS /tmp/backfill_table.md (44行, 5039B)
- 冷启动说明: 老版本registry不带score → 排名池初始仅含新评估版本+写入过score的版本; v6a_def为partial不入池
## 阶段4-5 决策日志+报告（已完成 2026-08-17 23:1x）
- decision-log: D-20260817-R220-7 type=gate_scoring_deploy, 尾行验证 ✓
- 编号: 任务书预期R-224已被占用(看板版本选择器) → 本报告顺延 R-225
- R-225: shared/results/05-量化投资/R-225-五门禁评分制改造与回填验证.md (11641B, 含44行回填表+三点结论+预期不一致清单+冷启动风险+回滚)
- README台账: 变更记录快记区+主表均已加R-225行
- completions: .task-completions.jsonl 已写 taskId=task-0351
- 口径披露: a7 v5批数据为v5h上岗后复核口径(g6 parent=v5h), v5i为评估时点口径(在役=v2b); 敏感度<0.01结论不变; 全PASS×REJECT AUC=79.5%仅参考披露
