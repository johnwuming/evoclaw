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

## 过程证据链（恢复点，全实测）
[23:05] 数据源探测：HP eastmoney HTTP RemoteDisconnected（带 UA 亦断）；腾讯 fqkline OK（socket+HTTP）；sina getNav 0 行；腾讯 fund API 404 → 决策：金价格段 HP 自包含（腾讯），MMF VPS 月推。
[23:10] r482（新浪源）vs 腾讯月末收盘：158/158 全同 maxdiff=0；E2 冻结信号复刻 156 完整月 w maxdiff 4.6e-05 / gold_ret 4.6e-13 / net 1.1e-06 → 移植成立。
[23:12] seed 构建并锚校验：ann/mdd 与 e2_gates_result.json V1_net 差 <1e-12（157 月）。
[23:14] B 条目文本拼接：cut=old.rindex('\n  ]\n}')，A/A2 前缀逐字节不变 True；sha before 8dc8b92c(5999B) → after 08b045e7(10404B)。
[23:16] VPS evaluate dry-run：corr -0.0400133462997406 vs E2 G6 -0.04001334629967728 差<1e-12，n=131 窗口一致；ann/calmar 逐位。
[23:18] HP 部署：tar 备份 67 项 sha 076eeaea3e736024536f9697；推 6 文件；HP 验证：A/A2 前缀(5992B)不变 True + deep-equal True；py_compile OK；evaluate dry-run corr -0.0400133463 n=131；append dry-run 幂等（fetch 3179 根 2013-07-29..2026-08-24）；init 幂等 157 行；crontab grep gold=0。
[23:20] baseline 真跑：exit 0，B evals=1 clean_evals=0 last_eval 2026-08-24T15:15:04+08:00；写后 A/A2 deep-equal True；post sha 83c47f3a6529a574（12908B）JSON 合法。
[23:22] MMF 推送助手 dry-run：2026-07 月收益 0.000718079382561 vs 冻结 seed 0.0007180793825602994 逐位一致。
[23:24] 发现：A2 旧待装 cron 为 6 字段，HP crontab 实为 5 字段（30 16 * * 1-5）——安装会失效，INSTALL.md 记修正，未改旧文件。
[23:26] 交付：R-306 报告（8.4KB）+ README 顶部条目 + hp-cron-pending/{gold_shadow_evaluate.cron(2行 5字段), gold_mmf_push_vps.cron, gold_mmf_push.py} + INSTALL.md 追加。
关键决策：①baseline 不计 corr 连续计数（防 a13 锁定 NAV 历史尾窗 0.2327 污染）；②月度模式优先活 NAV results/paper-nav.csv，不可用/过旧→corr_stale 拒计数；③append 只追加完整月（月末标签<当前自然月），尾月 8-24 冻结口径已在 engines.json 标注。
