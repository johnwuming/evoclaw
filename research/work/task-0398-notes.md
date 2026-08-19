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
- [x] 读 evolution_pipeline.py g3/corr 代码路径（gate_max_corr L393 / score_composite L736 消费 gates.g3_max_corr；a13_score.py 是复刻路径，正式路径走引擎 gate_max_corr）
- [x] 备份 evolution_pipeline.py.bak-g3corr-20260819（md5 与原一致；注意 task-0397 曾于 06:09 改过此文件，备份基于其之后版本 72612B）
- [x] decision-log 追加 D-20260819-G3CORR（type=gate_config_change）
- [x] 改造完成（3 处 patch，py_compile OK，+4238 字符）：
  1. GUARD_CORR_CONFIG：guard_col_default=[ret120]、guard_avatars={ret120:[mom_pen,mom_pen_dz]}、supp_ic_files=[a13_supp_ic_monthly.csv]
  2. load_ic_monthly：左连接并入补充月度IC列（base 主表、仅新列、跳过 n_* 辅助列）→ 老版本复合 IC 逐位不变
  3. gate_max_corr(reg, active=None)：新增 _guard_exempt_pairs 豁免（四条件：在役 e1_guard 为真+护栏列登记在 factors+不在排序 specs+候选因子在替身显式名单）；数据源加月度IC Pearson 兜底（矩阵→catalog→IC，≥24 月）；输出带 guard_exempt_pairs / corr_sources 审计字段
- [x] 冒烟测试通过：豁免单元测试（替身命中/非替身不豁免/无 e1_guard 空集/护栏列参与排序不豁免）+ merged IC 112 列含 4 补充列 + 引擎 g3 for e1f10dz = 0.2066 worst(mom_pen_dz,roe_ttm) exempt(mom_pen_dz,ret120)——与 R-242 独立复核 0.2066 逐位一致
- [ ] 兼容性验证（老候选 score 不变）
- [ ] e1f10dz 正式重评（≈0.8781）
- [ ] equiv 干跑
- [ ] 注册/激活裁决
