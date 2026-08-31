# task-0607 过程笔记（月末日频口径错配）

## 已证事实（0602 复用，task-0602-results.json）
- a13+现金（runtime_w60_rebal，月末采样）：MDD **-10.344%**（2015-04-30→2015-07-31）
- a13+现金（runtime_daily_w60_display_win，日频至 2026-07-31）：MDD **-21.307%**（2015-06-12→2015-07-08）
- 系数 = 21.307/10.344 = **2.06 倍** ✓
- 58/42 静态（baseline1_display_5842，月末采样）：MDD **-9.690%**（2015-04-30→2015-07-31），ann 14.44% vol 10.32% sharpe 1.399
- 58/42 日频待算（本任务）

## 数据源（读 task-0602-compute.py 头部确认）
- a13 腿日频 NAV：`/root/.openclaw/workspace/shared/results/04-投资研究/a13_rsraw_e1f10dz_full_nav.csv`（date,nav）
- 月度曲线：`/root/.openclaw/workspace/tools/quant-bff/live/data/nav_curves.csv`
- 金腿日频：本地无 → 腾讯接口重建 sh518880 qfq 日线
  - GET https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh518880,day,{start},{end},640,qfq
  - data.sh518880.qfqday（或 .day），行 [date,open,close,high,low,...]，close=下标2
  - 分页：end 游标回退至 first≤start
  - ⚠️ 重建口径=静态权重+原始价格收益，非在役信号路径（必须声明）

## DDC 核实（进行中）
- 待 grep：PRD R-344、R-373/R-374 等报告中 ddc15/DDC/回撤四带定义
- 用户口径：sleeve 回撤 ≤−20% → 减半？vs 代码命名 ddc15（暗示 −15%？）
