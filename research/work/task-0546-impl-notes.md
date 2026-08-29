# task-0546 实施笔记（2026-08-29）

## 环境事实
- paper_engine.py 实际路径：/home/noname/quant-evolve/scripts/paper_engine.py（1759 行）——注意任务书写的 ~/quant-evolve/paper_engine.py 不准确
- 关键行号（grep 实测）：L61 DIV_EVENTS（仅 1 处引用）；L949 is_limit_up；is_limit_up 调用点 L1251、L1500；L97 LIMIT_UP_PCT=0.098；L98 ST_LIMIT_UP_PCT=0.05
- 报告编号：全库现有最大 R-351 → 本报告用 R-352
- 报告目录：shared/results/05-量化投资/（R-34x/35x 都在这里，不是 04-投资研究）
