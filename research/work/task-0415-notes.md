# task-0415 全A板块轮动 E1 画像 — 过程笔记

- 开工：2026-08-21 12:55，task-0415 置 running 成功（任务中心返回 ok:true）
- 编号确认：05-量化投资 现有最大 R-254 → 本报告用 R-255
- 方法论参照：R-231（E1/E2/E3 三级框架，E1=零回测画像）、R-217（换赛道独立评估）

## 数据采集记录

- 接口探测：HP quant env akshare 1.18.83；`ak.sw_index_first_info()` 返回 31 个申万一级行业（2021 版分类，含代码 801010.SI 农林牧渔 … 801980.SI 美容护理）
- 月频接口：`ak.index_hist_sw(symbol, period="month")` 直接返回月K（1999-12 起，农林牧渔 321 根，最新 2026-08-20 为未完结月）
- 采集脚本：/home/noname/quant-evolve/results/work/r0415/collect_sw.py，31 行业 × sleep 0.4s 限速，输出 sw_industry_monthly.csv（date × 行业收盘宽表）
- 注意事项：①2021 版分类历史回填（美容护理等 2021 新行业有回填历史，E1 画像可接受，报告注明）②2026-08 为未完结月，分析中剔除，仅用完整月
- 在役对照：/home/noname/quant-evolve/results/a13_rsraw_e1f10dz_full_nav.csv（日频 nav，2006-01-04 → 2026-08-14，5009 行）
