# task-0484 notes（边查边写，恢复点）

任务：黄金趋势引擎影子观察登记实施（R-306）。用户 2026-08-24 22:54 选①影子观察登记（R-305 判定 6/7 门 PASS、G3 前段部分达标）。

## 23:15 VPS 侧上下文核验
- R-286 实施先例已读：四件套 = ①engines.json 新条目 ②影子 NAV 基线段+append 脚本 ③月度 evaluate 脚本 ④VPS hp-cron-pending/ cron 文件（不安装）。
- R-259 §4.2 schema / §5.2 接入四条件 / §5.3 数据管道 / §5.4 月度治理已读：
  - §5.4 月度 evaluate 每月 3 日 09:35（a10 monitor 之后）；A2 已占 3 日 09:35 → B 需错峰。
  - 终止判据四条：①连续 N 月低于门槛 ②corr 超独立性上限 ③数据断供 ≥K 月 ④用户手动。数值占位「待冻结+用户确认」。
  - 晋升（shadow→active/真金/层2 ERC）一律用户人工门，永不自动化。
- R-305 判门数字（唯一取材源 HP work/r483/e2_gates_result.json）：
  - V1 净：ann 7.591% / vol 6.83% / MDD −5.902% / Calmar 1.286 / 月胜率 80.9%
  - G3 前段 2013-19 Calmar 0.902、后段 2.296；2020+ 贡献 65.24% 净对数收益
  - G6 corr(净,a13)=−0.0400（n=131，2013-08..2024-06）
- hp-cron-pending/ 位置：/root/.openclaw/workspace/hp-cron-pending/（已有 a2_shadow_evaluate.cron：`35 9 3 * * *` 月 3 日 09:35 + INSTALL.md）
- task-0483-notes 提供 HP r483 线索：`work/r483/e2_gates_result.json`、`e2_nav_monthly.csv`（157 月）、e2_prereg sha256 40ae265704041ac1…

## 待办清单
- [ ] HP：定位 r483 work 目录，读 e2_gates_result.json（先落盘 /tmp）
- [ ] HP：tar 备份 model/registry（改前）
- [ ] HP：engines.json 追加 B 条目，diff 证明 A/A2 逐字不变
- [ ] HP：results/engines/b/shadow_nav.csv 基线段（r483 V1 净口径月度 NAV 157 月 2013-08..2026-08）
- [ ] HP：新脚本 b 专用 append + evaluate（新文件名，不改 A2 版）
- [ ] HP：evaluate --mode baseline 首跑，Calmar 逐位复现 1.286 量级；corr(A,B) 重叠窗
- [ ] VPS：hp-cron-pending/b_shadow_evaluate.cron + INSTALL.md 更新（错峰）
- [ ] VPS：R-306 报告 + README 更新日志
