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

## 23:15–23:28 第二执行体（cron/心跳重复派发）独立验收记录

**背景**：task-0484 被 spawn 了两次（同分钟）：微信会话 spawn 的 `task-0484-gold-shadow`（task-center assigned_agent 记录）+ 心跳 cron spawn 的本执行体（session c5713348…，deliveryContext=heartbeat）。两者并行写同一批产物。

**处置**：本执行体 23:16 检测到并发迹象（HP 脚本时间戳 15:13 UTC=23:13、engines.json audit ts 23:20、VPS cron 文件 23:18），立即切换为**只读验证模式**，未向 HP engines.json/脚本/结果目录、R-306 报告、README 写入任何内容（本文件开头段为唯一早期写入，已被主执行体合并保留）。避免双写 registry/双跑 baseline 的污染风险。

**任务终态**：主执行体完成全部四件套；主 agent 已审核通过（task-center status=done 23:24，review_summary 在案）。本执行体不再写 completions、不做 pending_review PUT——对已关闭任务回退状态属破坏性操作。

**独立验收（本执行体，全部只读，全部 PASS）**：
- tar 备份 `model/registry_backup_task0484_20260824.tar.gz` 67 项 ✓
- engines.json `python -m json.tool` 合法；条目 [A, A2, gold_trend_sma200] ✓
- **A identical=True、A2 identical=True**（备份抽出 engines.json 与现状 parsed deep-equal，硬红线核心证明独立复核）✓
- B 条目：status=shadow、slot=B、parent=None、started_at=2026-08-24、min/max 3/6、termination c1–c4 齐备、note 含 G3 牛市依赖+G6 corr −0.0400 监控重点 ✓
- baseline evals[0] vs 唯一取材源 VPS `work/r483/e2_gates_result.json`：ann 0.07590979342570381 vs 0.07590979342573179（Δ2.8e-14）、mdd −0.05901780820812119 vs −0.05901780820817082（Δ5e-14）、calmar 1.286218443728281 vs 1.2862184437276736（Δ6e-13）、corr(A,gold) −0.040013346299740626 vs −0.04001334629967728（Δ6e-14，n=131，窗 2013-08-31..2024-06-30）——CSV 12 位序列化舍入级，判逐位复现 ✓；clean_evals=0 起点正确 ✓
- shadow_nav.csv 158 行（头+157 月 2013-08-31..2026-08-31），首/末行与 r483 e2_nav_monthly.csv 逐字段一致（w_applied/gold_ret/mmf_ret/gross/net 转制+nav 累计列）✓；seed/mmf_monthly_push 同源 ✓
- 两脚本 py_compile OK；HP `crontab -l | grep -c gold`=0（未安装）✓
- VPS `hp-cron-pending/gold_shadow_evaluate.cron`：5 字段标准格式，月 3 日 09:38 append + 09:40 evaluate，错开 A2 的 09:35 ✓；INSTALL.md 含 gold 安装/回滚章节 ✓
- 分段核验：seg_2013_2019 calmar 0.9018713903478757、seg_2020_2026 calmar 2.2957289612380074——与 R-305 报告 0.902/2.296 一致 ✓

**轻微偏差（已在 R-306 文档化，语义等价，无需处置）**：
1. engine_id 字面值为 `gold_trend_sma200`+`slot=B`（任务书字面 `engine_id=B`）；type=`standalone_shadow`（任务书 `standalone_trend`）；registry_ref 落在 evidence 段。
2. cron 文件名 `gold_shadow_evaluate.cron`（任务书 `b_shadow_evaluate.cron`）。
3. R-306 §四 时间标签「15:15:04+08:00 HP 本地」有误：HP 时钟为 UTC，实为 23:15:04 GMT+8（cosmetic）。

**流程建议（供主 agent）**：心跳派发应对 `assigned_agent` 非空且 status=running 的任务跳过重复 spawn；或子 agent 启动时先查 task-center 状态。本次双执行体曾并行写 HP（23:13–23:20 窗口），存在 registry 双写真实风险，靠时间差侥幸避免。
