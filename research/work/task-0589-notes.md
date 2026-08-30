# task-0589 过程笔记 — gold 引擎 active_paper 执行机制核验（R-378）

开始时间：2026-08-30 16:04
编号实查：本地目录最大 R-377 → 本报告 **R-378**（无冲突）

## 核验点清单
1. paper_engine_gold.py 逐段读懂（执行循环/下单/记账/产出文件）
2. gold_shadow_nav.csv 性质（纯计算 vs 有仓位佐证）
3. runtime 链为何无黄金（R-354 决策原文）
4. reconciliation gold_engine_active_paper=true 检查实现
5. 判定三选一
6. 选项与代价分析

---

## 核验点 1：paper_engine_gold.py 代码级结论（本地 scripts/paper_engine_gold.py，16474B 全读）

**执行机制：纯计算模拟，无任何真实下单/成交路径。**

证据（代码级）：
1. 全文 import 仅 argparse/json/os/sys/urllib/numpy/pandas —— 无任何券商/交易 API、无下单函数、无成交回报处理。
2. 数据输入 = 腾讯公开行情 `web.ifzq.gtimg.cn fqkline sh518880`（fetch_gold_daily，L57-90）+ MMF 月度收益推送 CSV（mmf_monthly_push.csv）。
3. 「仓位」= state JSON 里的浮点数 `current_weight`（st["open"]["w"]），无资产账户、无份额、无现金扣减。mark_nav() 注释自认「信息性 NAV 标记」（L172）。
4. 产出文件：`results/engines/gold/paper_state.json`（STATE_PATH，L47）——months 结账行/marks(尾部120条)/audit 追加日志，全部是自维护的模拟账本。
5. 月度调仓 = close_and_roll() 里 `w_new = float(w_sig.loc[prev_me])` 直接写 JSON 权重 + 按 |Δw|×0.13% 从模拟净值里扣成本——成本是 NAV 公式项，不是真实交易费。
6. **引擎自己在 state JSON 里写明**（cmd_init, L271）：
   `"activation": {..., "real_money": "未涉及——真金分配为独立人工门"}`
   即设计时已声明：paper 链不碰真金，真金分配是独立的人工审批门。
7. 激活记录：user 2026-08-25 00:35 批准 shadow→active（影子期豁免）；NAV=1.0 新链，157月模拟史由 shadow 链承载。

**「active_paper」真实含义**：state.status 字符串 + registry 状态，指「该策略模拟链处于活跃标记状态」（逐日 fetch 价格→按冻结规则公式更新模拟 NAV/权重），**不是**维护真实仓位账本。无下单、无成交、无持仓份额记录。

## 初判（待其余核验点佐证）
执行形态属「虚腿」：有完整计算链（模拟 NAV + 权重状态 + 月度结账），零成交链。

## 核验点 2：HP 实测 gold 目录（~/quant-evolve/results/engines/gold/）

目录内容全部清单：mmf_monthly_push.csv / paper_state.json / shadow_nav.csv / shadow_nav_seed.csv。
**无任何 trades/fills/positions/broker 文件** —— 唯一的「账本」就是 paper_state.json（模拟 NAV 链）。

paper_state.json 实测（2026-08-28 07:40 更新）：
- status=active_paper；created 2026-08-24；activation.real_money="未涉及——真金分配为独立人工门"
- current_weight=**0.0**（2026-07-31 信号：px 8.433 < sma200 9.479 → w=0，即模拟链当前也是零黄金+纯货基）
- months=[]（尚未有任何月度结账）；marks 4 条（8-24~8-27，NAV 1.0→1.000069，纯 MMF 漂移）
- 激活即声明：NAV=1.0 新链，157月模拟史由 shadow_nav.csv 承载

shadow_nav.csv 性质：月频模拟表（列=month,w_applied,gold_ret,mmf_ret,gross,net,nav），
2013-08~2026-08 共 157 行，全部为公式计算列（价格×规则），无仓位/成交佐证。
注意：近期 w_applied=0（金价低于 SMA200，趋势信号空仓）——**即便虚腿，模拟仓当前也是 0 金**。

## 中期结论（已可定性）
三态判定：**虚腿**（纯计算状态，无真实仓位）。
且当前模拟权重也是 0（趋势空仓信号），设计权重 41.97% 若接线，首个信号也是空仓。

---

## 核验点 4：reconciliation gold_engine_active_paper=true 的实现

HP governance.py L420（~/quant-evolve/portfolio_v1/governance/governance.py）：
```python
checks["gold_engine_active_paper"] = sl.get("hedge_sleeve_gold", {}).get("component_ref", {}).get("status") == "active_paper"
```
**它只检查 vC-0.json 设计文档里 sleeves.hedge_sleeve_gold.component_ref.status 字符串 == "active_paper"**。
- 能证明：设计文档引用的 gold 引擎自declared状态是 active_paper（引用一致性）。
- 不能证明：任何真实仓位/成交/runtime 组合含黄金。纯字符串比对，与 paper_state.json 的 status 字段同源（引擎自己写的）。
- 同函数 L419 equity 检查同理（registry_entry=="a13_rsraw_e1f10dz"）。

## 核验点 3 进行中：R-354 报告已读（本地 5KB 全文）
R-354 = Phase C 治理切换执行报告（2026-08-29）。关键：
- paper 指针切至 portfolio_version_ref=vC-0；runtime 镜像钩子 nav.daily/trade.fill 实跑 8 trade.fill（equity 侧）
- §2e：gold paper_state 五文件 sha256 切换前后 SAME —— 即切换**没动 gold 引擎**，gold 不在切换写入面内
- **报告里没有「黄金为何不进 runtime 组合」的决策原文** —— 切换只是忠实投影既有 vC-0 定义。需向前追：vC-0 定义时的 sleeves 权重设计（R-336/R-353？）与 baseline-paper 组合构建时的决策。

## 核验点 3 完成：runtime 链为何无黄金（决策原文已找到）

时间线：
- 08-14/08-17：baseline-paper 链建仓/启动（paper_engine.py，task-0251，单一 a13 equity 引擎，8 持仓 equity_w=0.6+现金40%，timing_layer=timing_v4_i4_q3z）——**此时 gold 引擎尚未激活**（还在 shadow 研发）
- 08-25 00:35：用户批准 gold shadow→active（R-307）。**决策原文**：「激活 ≠ 真金：真金分配仍是独立人工门，本任务零真金、零资金操作」+「真金分配、层2 ERC 接入均为独立人工门，永不自动化」（R-307 头部+§三.5，registry promotion.scope 显式声明）
- 08-28：vC-0.json 创建（sleeves=equity+gold，solver_equal_vol_v1 dryrun 解 58.03/41.97，见 R-377）；capital_policy 自注：**「在役无杠杆、A/gold 双独立 paper 链；初值，组合层正式化时确认」**——组合层正式化被显式留作未来事项
- 08-29：R-354 治理切换——paper 指针→vC-0、镜像钩子、对账。§2e 明确「五文件 sha256 切换前后 SAME」含 gold paper_state；切换不含任何组合重组动作

**定性：有意分阶段设计，非遗漏。** 设计层 vC-0 已含黄金腿（41.97% 设计解），但「组合层正式化/接线」被显式定义为独立人工门，至今未获批执行。runtime 账户因此仍是 a13 单引擎账户（equity_w=0.6 是 a13 择时层输出，非组合 sleeve 配置）。

## 核验点补充：gold paper 链自动化现状（比预期好）
HP crontab 现有（R-307 之后的后续项，伴随 state 08-28 更新时间推断为 task-0540 装上）：
- `40 7 * * 1-5` paper_engine_gold.py --action daily（工作日 15:40 北京）
- `0 3 * * 0` weekly verify
外加每月 3 日 shadow append+evaluate 两行（R-306/307）。
小异常：paper_state marks 止于 08-27 而 updated_at=08-28T07:40（cron 时点）——qfq 数据当日滞后，fetch 末 bar=08-27 触发 dup 保护跳过记账，行为正常。

## 判定：虚腿（三选一明确）
- 真执行：否。零券商/下单 API、零成交文件、零真实仓位。runtime 账户（baseline-paper）从未建黄金仓。
- **虚腿：是**——gold active_paper = 独立自维护的模拟 NAV 账本（state JSON），有自动逐日计算链（daily cron），零成交链、零真实仓位、未接入 runtime 账户与展示 NAV。
- 部分执行：若定义为「有计算链无成交链」也算贴合，但比「部分执行」更弱的是：它从未被设计为执行腿——激活与组合接线是显式分离的两个人工门，前者已过、后者未触发。
**最终表述：虚腿（by design 的未完成腿）**：41.97% 是 solver 设计解（08-28 dryrun），runtime 对应物=0 黄金仓位；40% 现金是 a13 择时层的真实输出，二者账目上都成立、但语义上「设计组合≠运行组合」。

且注意：当前 gold 信号 w=0（07-31 px 8.433<SMA200 9.479）——**即使立刻接线，首期黄金暴露也是 0**（腿内全货基 000198），接线改变的是记账/展示语义与现金增强，不是即期黄金暴露。

## 与 F1_quarterly 口径问题的区分（R-377）
正交两事：
- F1 问题=回测展示基底滞后：performance.json 曲线列锁 50/50 时代基线，定义已改 58.03/41.97，provenance 文本误导（已由 R-377 定性）。
- 本问题=运行账户实仓缺失：runtime 账户从未建黄金仓，41.97% 设计解从未落地。
即使 F1 曲线按 58.03/41.97 重算（回测语义修复），runtime 账户依然没有黄金腿；反之接线 runtime 也不回改回测曲线。修复一个不解决另一个。

## 选项与代价（决策留用户）
A. 组合层 paper 合成（不碰真金）：把 equity 链 NAV 与 gold 链 NAV 按 58.03/41.97+rebalance band 0.02 合成组合 NAV 投影进 runtime/BFF。
   工程量：中（组合 NAV 合成器+vC-0 投影扩展+recon 扩展+BFF 字段；两链起点不同需对齐口径：equity 08-14 10万 vs gold 08-24 NAV=1.0）。
   风险：在役触碰面大（governance 投影/recon 检查/BFF/看板全动）；双记账歧义；需把「合成组合 NAV」与「账户真实 NAV」两个语义在展示层分开，否则重演 R-377 式 provenance 漂移。即期黄金暴露=0（信号空仓），用户看到的 41.97% 仍是纸面。
B. 真买（真金门）：真金分配+券商通道（手动或 API）+合规审批。R-307 已声明永不自动化，须用户显式批准+资金操作。工程与合规成本最高，且当前信号 w=0，真买了也是空仓（只买货基增强或等待金叉信号）。
C. 承认未完成腿（推荐低代价路径）：设计层 vC-0 保留 41.97% 不动；runtime 展示如实标注「账户=a13 单引擎 paper（60% 仓位为择时输出），gold 腿为独立 active_paper 监控链，未接入账户」；recon 检查 gold_engine_active_paper 语义注释化（明确它只证明设计引用一致）；看板加一行说明。
   工程量：小（标注+注释+看板一行，零在役数值改动）。风险：极低。代价：看板继续呈现「设计 vs 运行」的差异，需用户接受 41.97% 短期内不对应任何仓位。

## 验收预检
- 报告含 paper_engine_gold ≥3 次 ✓（写作时保证）
- 判定三选一段落 ✓（§判定）
- R-354 决策原文：找到的是 R-307/vC-0 capital_policy（R-354 本身无黄金排除决策，如实记录）
