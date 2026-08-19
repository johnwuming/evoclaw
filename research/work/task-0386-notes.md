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
