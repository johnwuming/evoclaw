# task-0398 过程笔记：g3 corr 口径引擎修正 + e1f10dz 正式重评

## 结论速览
- **改造完成并验证**：evolution_pipeline.py g3 区分「排序因子」与「护栏登记项」（D-20260819-G3CORR），向后兼容验证通过（非 E1 系列老候选 score 逐位不变），equiv BIT-EXACT。
- **e1f10dz 正式裁决：已激活**。引擎正式 evaluate：score **0.8781**（与 R-242 独立复核值完全一致，偏差 0.0000 ≤0.005）、rank1/池8、无 stat_warn、holdout PASS（25.80%/-16.13%）→ 按 R220/P0-4 v1.1 规则自动 activate（D-20260819-004）。
- 状态流转：a13_rsraw_e1f10dz→active，a9_ranksum_raw→sota，v5h_xsub→retired；main.json 已切换（md5 c58759da→2ef46a33）。
- ⚠️ **跟踪项（给主 agent）**：paper 侧集成依赖 task-0396——paper_trade.py（8/9 版，活跃 cron 消费者）与 paper_engine.py 均无 e1_lambda/e1_deadzone 支持（且 ranksum/ext_specs 也未见支持，缺口在今晨 ranksum 激活时已存在）。**下次 paper 月度调仓 2026-09-01 16:30**，task-0396 须在此之前落地 e1 因子化支持，否则 paper 持仓将与回测口径背离。回滚命令：`evolution_pipeline.py rollback --to a9_ranksum_raw --reason '...'`。

## 环境与对象确认
- 改造对象：HP ~/quant-evolve/scripts/evolution_pipeline.py（原 72612B）
- g3 复刻路径参考：scripts/a13_score.py（正式路径走引擎 gate_max_corr → score_composite 消费 gates.g3_max_corr）
- 在役 registry：model/registry/{v5h_xsub,a9_ranksum_raw}.json
- 老候选分数基准：results/a13_score_summary.json（原评 active=v5h_xsub）
- 复核基准值：e1f10dz 护栏豁免口径 score 0.8781（允许偏差 ≤0.005）

## R-242 口径复核关键数字（来源：报告已读）
- mom_pen_dz vs 在役因子集 |IC相关|：ret120(护栏) 0.7555、roe_ttm 0.2066、circ_mv 0.1236、pb_inv 0.0697、avg_amount_20d 0.0696
- 豁免口径 max|ρ| = 0.2066 < 0.5 免罚线 → corr 分量 1.0；未修正口径 0.7781 < 0.867
- 豁免不涉及 oos/dd——它们本来就计价行为差异

## 改造内容（3 处 patch，+4238 字符，py_compile OK）
1. **GUARD_CORR_CONFIG**（GATE_CONFIG 后）：`guard_col_default=["ret120"]`（e1_guard 未显式给 mom_cols 时）、`guard_avatars={"ret120":["mom_pen","mom_pen_dz"]}`（替身显式名单，防豁免无界扩大）、`supp_ic_files=["a13_supp_ic_monthly.csv"]`。
2. **load_ic_monthly**：左连接并入补充月度IC列（base 主表、仅新增列、跳过 n_* 辅助列）→ 老版本复合 IC 逐位不变；g1/g2/g3 均受益于数据覆盖。
3. **gate_max_corr(reg, active=None)**：
   - 新增 `_guard_exempt_pairs(new_factors, active_reg)`：四条件全满足才豁免——①在役 params.e1_guard 为真 ②护栏列登记在 selection.factors ③护栏列不在排序 specs（ext_specs/ext_factor/sort/ext_weights 序列化检查）④候选因子在 guard_avatars 名单。缺一即回退旧口径。
   - 数据源升级：矩阵→catalog→月度IC Pearson 兜底（≥24 月重叠，与 W1 矩阵同源方法）。
   - 输出审计字段：guard_exempt_pairs / corr_policy / corr_sources。
   - 备份：scripts/evolution_pipeline.py.bak-g3corr-20260819（md5 与改前一致；注意 task-0397 当天 06:09 也改过此文件，备份基于其后版本）。

## 验证结果

### ① 向后兼容（scripts/task0398_reverify.py → results/a13_g3_reverify.json）
复刻 a13_score.py 数据流（active=v5h_xsub、同 n_trials=91 冻结、月度IC路径），唯一差异 = 新豁免逻辑：
| 候选 | 原 score | 新 score | 判定 |
|---|---|---|---|
| a9_raw_universe | 0.8061 | 0.8061 | IDENTICAL |
| a9_ranksum_raw | 0.8670 | 0.8670 | IDENTICAL（corr 分量 0.3755、maxρ 0.6249 逐位同） |
| a9_ranksum_quality | 0.7848 | 0.7848 | IDENTICAL |
| a13_rsraw_e1f05/10/15 | 0.8321/0.8279/0.8275 | 0.8696/0.8654/0.8651 | EXPECTED_DELTA（E1 系列，corr 0→0.3755） |
| a13_rsraw_e1f10dz | 0.8337 | 0.8712 | EXPECTED_DELTA（vs v5h 口径） |
非 E1 系列 ok_all_identical=True。

### ② equiv 干跑（BIT-EXACT）
a13x_equiv_v5h vs a7_v5h_xsub anchor：full/locked metrics diff 均为空 → BIT-EXACT。结构性佐证：本次只改 evolution_pipeline.py 评分路径，回测链（a9_common patch_engine / q4b）零接触（a9_common.py md5 未变）。

### ③ e1f10dz 正式 evaluate（引擎路径，results/bt_a13_rsraw_e1f10dz/gate-report.json）
- g3：max_abs_corr **0.2066**，worst (mom_pen_dz, roe_ttm)，guard_exempt_pairs [(mom_pen_dz, ret120)]，corr_sources 4 对全部 ic_monthly 解决——与 R-242 独立复核 0.2066 逐位一致
- score **0.8781**：p 1.0 / dsr 0.999 / oos_calmar 0.5148 / oos_sharpe 0.5117 / is 1/1 / dd 1.0 / corr 1.0 / logic 1.0——与 R-242 §3.2 表逐位一致
- rank=1/池8（池内第二名 a9_ranksum_raw 0.867）；stat_warn=False；n_trials=91
- holdout PASS：2024-07~2026-08-14 段 ann 25.80% / mdd -16.13%（ann_ok、mdd_det -17.42pp ≤10pp）
- 自动激活三条件齐 → activate：registry status=active、main.json version=a13_rsraw_e1f10dz（e1_guard=0/e1_lambda=1.0/e1_deadzone=0.30）、decision-log D-20260819-004(activate)+D-20260819-005(evaluate)

### 决策链（decision-log.jsonl）
D-20260819-G3CORR（gate_config_change，改造内容/依据/回滚）→ D-20260819-004（activate）→ D-20260819-005（evaluate）。

## e1f10dz registry 条目（model/registry/a13_rsraw_e1f10dz.json）
- selection.params：a13_run.py C4 原始配置（ranksum4 + raw_universe + e1_guard=0 + e1_lambda=1.0 + e1_deadzone=0.30）；factors=[circ_mv, avg_amount_20d, pb_inv, roe_ttm, mom_pen_dz]
- timing/data_snapshot：承袭 a9_ranksum_raw（同批数据池，kline_as_of 2026-08-10，hash bcf45e9f）
- backtest_refs：locked 2006-01-04~2024-06-28（ann 22.02%/mdd -33.55%/sharpe 1.3561/calmar 0.6562），full~2026-08-14
- provenance：parent a9_ranksum_raw，报告指向 R-242

## 风险与跟踪
1. **paper 集成缺口（最重要）**：活跃 cron（每月首个交易日 16:30）调 scripts/paper_trade.py --action rebalance 消费 model/main.json；paper_trade.py（742 行，8/9 版）与 paper_engine.py（8/18 版）grep 均无 e1_lambda/e1_deadzone/ext_specs 支持。该缺口自今晨 ranksum 激活（D-20260819-002）起已存在，非本次引入；e1f10dz 激活使缺口加深一层（E1 保护完全依赖 e1_lambda 生效，被忽略 = 无护栏无惩罚）。**deadline：2026-09-01 月首调仓前 task-0396 必须落地，否则回滚**（rollback --to a9_ranksum_raw 不能消除 ext_specs 缺口，需回滚到更早或人工处置——建议主 agent 直接催办 task-0396）。
2. e1f10dz 持仓护栏域残留 1.67%（R-242 建议 #3）：shadow 期监控全池护栏域强度极值（历史均值 9.95%）。
3. 激活属低边际切换（行为差异 <3% 持仓），价值在消除最后一个硬护栏、对齐「E1 不做限制性规则」原则。

## 验证命令（可重跑）
```bash
# 兼容性重算（~20s）
/home/noname/miniconda3/envs/quant/bin/python scripts/task0398_reverify.py
# equiv 干跑（读既有产物，秒级）
python -c "import json; a=json.load(open('results/a13x_equiv_v5h_full_metrics.json')); b=json.load(open('results/a7_v5h_xsub_formal_full_metrics.json')); print('BIT-EXACT' if all(a.get(k)==b.get(k) for k in ('annual_return','max_drawdown','sharpe','calmar')) else 'FAIL')"
# 激活状态三处
python -c "import json; print(json.load(open('model/registry/a13_rsraw_e1f10dz.json'))['status'], json.load(open('model/main.json'))['version'])"
tail -3 model/decision-log.jsonl
```

## HP 新增文件
- scripts/task0398_patch.py（补丁脚本，已消费，留档）/ task0398_reverify.py（兼容性验证，可重跑）/ task0398_register.py（registry 登记，留档）
- results/a13_g3_reverify.json（兼容性验证产物）
- results/bt_a13_rsraw_e1f10dz/gate-report.json（引擎正式评估报告）
- model/registry/a13_rsraw_e1f10dz.json + .main.json.snapshot（激活快照）；a9_ranksum_raw.main.json.snapshot（旧在役冻结）

## 未触碰清单（约束遵守）
paper_engine.py / paper_trade.py / a9_common.py（md5 核对未变）/ registry 既有条目（只新增 e1f10dz + 引擎自身状态流转）/ HP crontab。
