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
