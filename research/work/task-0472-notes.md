# task-0472 过程笔记
## 2026-08-23 启动
- expected_output: shared/results/01-AI行业研究/R-292-中央控制层训练.md（目录前缀疑误，R-* 系列在 05-量化投资，任务正文明确路径为 05-量化投资/R-292-*）
- R-292 编号确认（任务中心 expected_output 编号为 R-292）

## 数据清单确认
- A 全史 NAV: shared/results/04-投资研究/a13_rsraw_e1f10_full_nav.csv（日频 2006-01-04..2026-08-14，5008 行）
- A2 影子 NAV: shared/results/04-投资研究/engines/a2/shadow_nav.csv（日频 2006-01-04..2024-06-28，4491 行 = R-286 历史基线段）
- E2 可转债候选第三腿: shared/results/work/r281/e2_nav_monthly.csv（月频 2018-01..2026-07，102 月）——R-289 判门通过获影子资格，但独立性 corr(A,E2)~0.58 >0.5 未达标（R-289 披露）
- R-282 §五 corr(A,A2)=0.999851（n=221 月度化）→ 触发 R-259 §6.1 极端情形规则候选
