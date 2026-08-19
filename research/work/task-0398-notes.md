# task-0398 过程笔记：g3 corr 口径引擎修正 + e1f10dz 正式重评

## 环境与对象确认
- 改造对象：HP ~/quant-evolve/scripts/evolution_pipeline.py（SCORE_CONFIG L69-84、score_composite L731+）
- g3 另有实现参考：scripts/a13_score.py L158-176（R-242 复核脚本的复刻口径）
- 在役 registry：model/registry/{v5h_xsub,a9_ranksum_raw}.json
- 老候选分数基准：results/a13_score_summary.json
- 复核基准值：e1f10dz 护栏豁免口径 score 0.8781（允许偏差 ≤0.005）

## R-242 口径复核关键数字（来源：报告已读）
- mom_pen_dz vs 在役因子集 |IC相关|：ret120(护栏) 0.7555、roe_ttm 0.2066、circ_mv 0.1236、pb_inv 0.0697、avg_amount_20d 0.0696
- 豁免口径 max|ρ| = 0.2066 < 0.5 免罚线 → corr 分量 1.0
- 未修正口径 score 0.7781；豁免口径 0.8781（> ranksum_raw 0.867）
- 修正建议原文：g3 在役因子集应区分「排序因子」与「护栏登记项」——在役 params 含 e1_guard 且其 mom_col(ret120) 不在排序 specs 中时，该列对候选因子化替身(mom_pen/mom_pen_dz)豁免 g3 比较
- 豁免不涉及 oos/dd——它们本来就计价行为差异

## 执行进度
- [x] 读 R-242 报告
- [ ] 读 evolution_pipeline.py g3/corr 代码路径
- [ ] 备份 + decision-log D-20260819-G3CORR
- [ ] 改造（向后兼容）
- [ ] 兼容性验证（老候选 score 不变）
- [ ] e1f10dz 正式重评（≈0.8781）
- [ ] equiv 干跑
- [ ] 注册/激活裁决
