# task-0386 过程笔记：历史年化20%+版本评分制v1.1重评

## 目标
HP 侧历史年化 20%+ 版本（locked 口径 metrics 筛选）逐个用已部署 score_composite 函数重算评分，registry 补 score_composite + rescored 标记 + manifest 重生成。不自动激活，只给晋升/摘 legacy 建议清单。

## 编号确认
- R-244 已占用（04-投资研究/R-244-ZeroTier推链路排查与qfq日更方案.md）
- R-245 空闲 → 本任务报告编号 R-245
- R-246 已占用（根目录 R-246-因子治理A10-4实施报告.md）

## 关键事实
- 评分口径：SCORE_CONFIG v1.1（R-225），score_composite/gate_* 已部署于 evolution_pipeline.py，g6 硬门禁禁用（D-20260819-G6DEL），新血统线废弃不用于 REJECT
- 在役：a13_rsraw_e1f10dz（incumbent），重评 oos 分量以当前在役为基准
- 参考产物：a13_score_summary.json / a15_score_summary.json

## 进度日志

## 2026-08-19 20:4x 筛选结果（locked metrics = backtest_refs.metrics.annual_return）
≥0.20 共 12 个：
- v1g_ivw 0.2732 candidate mdd=-0.6973
- v1h_buf 0.2699 candidate mdd=-0.6891
- v0_seed 0.2626 retired mdd=-0.6949
- v1c_liq 0.2619 candidate mdd=-0.7036
- v1b_mvq 0.2475 candidate mdd=-0.6688
- v3a_peg 0.2472 candidate mdd=-0.7210
- a13_rsraw_e1f10dz 0.2202 **active 在役基准（不改其条目，用现有 a13_score_summary 做对照）**
- a9_ranksum_raw 0.2176 sota
- v1d_cv 0.2158 candidate
- v1a_score 0.2155 candidate
- v4d_mfu_raw 0.2059 candidate
- v3b_glm 0.2048 candidate
重评目标=除在役外的 11 个。registry 路径：~/quant-evolve/model/registry/（已有备份 registry.bak.20260818_s2shadow、registry.bak.20260819_t0394.tar.gz）
manifest：~/quant-evolve/results/versions-manifest.json（100KB，keys: generated_at/active/versions）

## 20:5x 干跑结果（--calc，results/rescore_20pct_v11_summary.json）
脚本：~/quant-evolve/scripts/rescore_20pct_v11.py（复用部署函数 gate_icir/gate_max_corr/deflated_sharpe/gate_mdd_vs_parent/score_composite/compute_holdout_metrics/score_rank_pool；不 import 重回测）
- 在役基准 a13_rsraw_e1f10dz（ann 0.2202 / mdd -0.3355 / sharpe 1.3561 / calmar 0.6562），池内分 0.8781 居首
- 结果（score / rank / 关键分量）：
  - a9_ranksum_raw 0.7715 rank=6（prior 0.867，差因基准换成 a13：oos_calmar 0.7844→0.4853；corr 0.6249→0.7555=ret120 vs 在役护栏替身 mom_pen_dz，G3CORR 豁免不覆盖该方向）stat_warn=False，holdout pass（ho ann 0.2584 与旧 summary 一致✓）
  - v1g_ivw 0.2988 / v1h_buf 0.2979 / v0_seed 0.2908(retired,假设入池rank) / v1c_liq 0.2896 / v1b_mvq 0.2877 / v3a_peg 0.2861 / v1a_score 0.2690 / v4d_mfu_raw 0.2657 / v3b_glm 0.2651 / v1d_cv 0.2611
  - 老版本共性：p=0.0714(分量0.74)、DSR 0.40-0.65(分量0)、dd恶化33-39pp(分量0)、corr 0.9437(分量0)、oos_calmar=0 → stat_warn=True，全部 holdout pass=True（ho段mdd普遍改善至-0.13~-0.21）
- 池 top（并入后）：a13 0.8781 > v4a_mf0_trr 0.8088 > v5k_nh10 0.80 > v5i_comb 0.7985 > v5j_bl30 0.7811 > a9 0.7715
- promo=[]（无 rank1+holdout+无警示者）→ 无晋升候选；老版本维持原状
- IC 覆盖度：v3a_peg 缺 peg_np、v4d_mfu_raw 缺 roc/ev_ebit、v3b_glm 缺 graham_score（gate_icir 部署口径按可用子集合成，已在 summary+registry 标注 ic_coverage，不编造）
- 修正过：排名并池只含 candidate/pending/active（v0_seed retired 为假设入池参考 rank）
