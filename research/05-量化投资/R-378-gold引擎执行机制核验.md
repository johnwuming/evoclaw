# R-378 gold 引擎 active_paper 执行机制核验：虚腿还是未完成腿（task-0589）

- 日期：2026-08-30｜类型：研究核验（纯只读，HP 与本地数据零改动）
- 触发：用户 08-30 15:48 提问——gold_trend_sma200 的 active_paper 到底会不会产生真实成交/仓位？41.97% 设计权重在模拟实盘里是否成立？
- 结论先行：**虚腿（by design 的未完成腿）**。active_paper 是自维护的模拟 NAV 账本，有自动化逐日计算链、零成交链、零真实仓位；runtime 账户（baseline-paper）从未建过黄金仓。41.97% 是 08-28 solver 设计解，从未在运行组合落地。这是显式分阶段的门控设计，不是遗漏。

## 1. 判定（三选一明确段落）

| 候选 | 判定 | 一句话依据 |
|---|---|---|
| 真执行（有仓位/成交记录，只是未接入展示） | **否** | 代码无任何下单/券商路径；HP gold 目录无任何成交/持仓文件 |
| **虚腿（纯计算状态，无真实仓位）** | **是（最终判定）** | active_paper = state JSON 里的浮点权重 + 公式 NAV，无账户、无份额、无现金变动 |
| 部分执行（有计算链无成交链） | 部分贴合但不采 | 它从未被设计为执行腿：R-307 显式把「激活」与「真金分配/层2 ERC 接入」拆成两个人工门，前者已过、后者未触发 |

最终表述：**虚腿 = by design 的未完成腿**。「active_paper」在代码与数据里的真实含义是「该策略的模拟净值链处于活跃标记状态」，不是「维护真实仓位账本」。runtime 的 40% 现金是 a13 择时层（timing_v4_i4_q3z）的真实输出，账目上成立；41.97% 黄金是设计层权重，运行组合对应物=0。设计组合 ≠ 运行组合。

## 2. 证据链

### 2.1 paper_engine_gold.py 代码级（本地 scripts/paper_engine_gold.py，16474B 全文通读，HP md5 与 R-307 留档一致）

1. **import 面**：argparse/json/os/sys/urllib/numpy/pandas——无任何券商 SDK、下单函数、成交回报处理。全文无 order/fill/trade 执行语义的代码路径。
2. **数据输入**：腾讯公开行情 `web.ifzq.gtimg.cn fqkline sh518880`（`fetch_gold_daily`）+ MMF 月度收益推送 CSV（`mmf_monthly_push.csv`，VPS 每月 2 日推送）。均为公开数据读取，非账户数据。
3. **「仓位」本体**：state JSON 的浮点数（`st["open"]["w"]` / `current_weight`）。`mark_nav()` 自注释「信息性 NAV 标记」：`nav = nav_open × (1 + w×gold_sofar + (1−w)×mmf_sofar)`——纯公式，无资产账户、无份额、无现金扣减。
4. **月度「调仓」**：`close_and_roll()` 里 `w_new = float(w_sig.loc[prev_me])` 直接写 JSON 权重，成本按 `|Δw|×0.13%` 从模拟净值里扣除——成本是 NAV 公式项，不是真实交易费。
5. **产出物**：唯一状态文件 `results/engines/gold/paper_state.json`（months 结账链 / marks 日标记尾部 120 条 / audit append-only 日志）。无 nav 成交流水、无持仓明细、无对账单。
6. **引擎自我声明**（cmd_init 写入 state）：`"activation": {..., "real_money": "未涉及——真金分配为独立人工门"}`。设计时就声明 paper 链不碰真金。
7. **自动化现状**（HP crontab 实查）：R-307 当时装的 cron 只有 shadow append+evaluate 两行（每月 3 日），daily 标记 cron 属「后续项」未装；其后已补装（crontab L35-36，无任务注释行，结合 state 08-28 更新时点推断为 task-0540 前后）：`40 7 * * 1-5` paper_engine_gold.py --action daily（工作日 15:40 北京）+ `0 3 * * 0` weekly verify。即模拟计算链现已自动化，但这只强化「自动纸面链」的定性——自动化的是 NAV 标记，不是任何交易。

### 2.2 HP 实测（~/quant-evolve/results/engines/gold/，2026-08-30 读取）

- 目录全部内容：`mmf_monthly_push.csv`、`paper_state.json`、`shadow_nav.csv`、`shadow_nav_seed.csv`。**无任何 trades/fills/positions/broker 文件**——唯一「账本」就是模拟 NAV 链。
- `paper_state.json`（updated 08-28 07:40 UTC）：status=active_paper；current_weight=**0.0**（07-31 信号 px 8.433 < SMA200 9.479 → 趋势空仓）；months=[]（激活以来无月度结账）；marks 4 条（08-24~08-27，NAV 1.0→1.000069，纯 MMF 漂移）；audit 仅 init 一条。
- **即便在模拟链里，当前黄金权重也是 0**。小异常记录：marks 止于 08-27 而 updated_at=08-28 07:40（恰为 daily cron 时点）——qfq 数据当日滞后致 fetch 末 bar=08-27，dup 保护跳过记账，行为正常非故障。

### 2.3 gold_shadow_nav.csv 性质：纯计算

月频模拟表（列=month, w_applied, gold_ret, mmf_ret, gross, net, nav），2013-08~2026-08 共 157 行。全部为「价格×冻结规则」公式计算列，无仓位、无成交、无账户佐证。它是 157 个月模拟史监控链（R-306 四件套），与 paper_state 的 08-24 起新链并存互证——两条都是纸面链。

### 2.4 runtime 链为何无黄金：时间线 + 决策原文（已找到）

- **08-14/08-17**：baseline-paper 链建仓/启动（paper_engine.py，task-0251，单一 a13 equity 引擎；8 持仓 equity_w=0.6 + 现金 40393/40%；mode=paper；model_version=a13_rsraw_e1f10dz）。此时 gold 引擎尚在 shadow 研发期，**物理上不可能纳入**。
- **08-25 00:35**：用户批准 gold shadow→active（R-307）。**决策原文**：报告头部「**激活 ≠ 真金：真金分配仍是独立人工门，本任务零真金、零资金操作**（registry promotion.scope 显式声明）」；§三.5「**激活≠真金：真金分配、层2 ERC 接入均为独立人工门，永不自动化**」。层2 ERC 接入即组合层接线，被显式排除在激活范围外。
- **08-28**：vC-0.json 创建（sleeves=equity_sleeve[active] + hedge_sleeve_gold[active_paper]；solver_equal_vol_v1 dryrun 解 58.03/41.97，见 R-377 证据 3）。capital_policy 自注：**「在役无杠杆、A/gold 双独立 paper 链；初值，组合层正式化时确认」**——组合层正式化被显式留作未来事项，vC-0 当时就是「两条独立 paper 链」的设计快照，而非可执行组合。
- **08-29**：R-354 治理切换：paper 指针→`portfolio_version_ref=vC-0`、事件溯源、镜像钩子（nav.daily/trade.fill 权威源=baseline-paper-nav.csv/trades.csv，全为 equity 侧）、三方对账。§2e「在役引擎数值零变化声明」：含 gold paper_state 在内五文件 sha256 切换前后逐一 SAME。**R-354 本身没有「黄金排除」决策原文——它只是忠实投影既有 vC-0 定义并声明零变化**（如实记录：切换报告无黄金议题，排除语义在 R-307 与 vC-0 capital_policy）。

定性：**有意分阶段设计，非遗漏**。但「组合层正式化/接线」这一步获批至今未执行，所以运行账户仍是 a13 单引擎账户，设计组合与运行组合的缺口一直存在且此前未被明确标注——这正是本次用户疑问的根源。

### 2.5 对账检查项 gold_engine_active_paper=true 的实现与语义边界

HP `portfolio_v1/governance/governance.py` L420（recon-2026-08-29.json 同源）：

```python
checks["gold_engine_active_paper"] = sl.get("hedge_sleeve_gold", {}).get("component_ref", {}).get("status") == "active_paper"
```

- **它做什么**：读 vC-0.json 设计文档里 `sleeves.hedge_sleeve_gold.component_ref.status` 字符串，与 `"active_paper"` 字面量比对。同函数 L419 对 equity 腿做同构检查（registry_entry=="a13_rsraw_e1f10dz"）。
- **能证明**：设计文档引用的 gold 引擎自 declared 状态是 active_paper（设计↔引擎引用一致性，防悬空引用）。
- **不能证明**：runtime 账户含黄金仓位、存在成交链、模拟链在跑（它甚至不读 paper_state.json，状态字符串与引擎 state 同源但检查不校验引擎侧实际文件）。**这个 true 是引用一致性检查，不是持仓存在性检查。** 对账 PASS 会给人「黄金腿在役」的错觉，实为语义错位。

## 3. 41.97% 的准确语义

- 出处：`portfolio/samples/weight-solution-2026-08-28-dryrun.json`，solver_equal_vol_v1（60 日窗/252 年化/min_obs 40/band 0.02）等波动率解 equity 58.03% + gold 41.97%（R-377 证据 3 实测）。
- 性质：**设计层 solver 输出，一次性 dryrun 快照**，vC-0 权威 JSON 本体无 weights 字段（HP 版无 weight_solution 块，R-354 §4.3 已留痕），从未生成任何组合层调仓指令。
- 即期事实：当前 gold 信号 w=0（趋势空仓）。**即使立刻接线，首期黄金暴露也是 0**（腿内全货基 000198 现金增强）——接线改变的是记账/展示语义与现金形态，不产生即期黄金暴露。08-24 px 9.564 逼近 SMA200 ~9.48，9-01 调仓日若金叉则腿内开始持有黄金（仍是纸面）。

## 4. 与 F1_quarterly 口径问题的区分（R-377）

两个正交问题，修复其一不解决另一：
- **F1 问题 = 回测展示基底滞后**：performance.json 曲线列锁 task-0492 基线（50/50 时代 md5 9704a300），定义 08-28 已改 58.03/41.97，provenance 文本未随更新形成「声称仍为真」的误导。语义层：**回测曲线该不该按新定义重算**。
- **本问题 = 运行账户实仓缺失**：runtime 账户从未建黄金仓，41.97% 设计解从未落地。语义层：**模拟实盘账户的持仓该不该有黄金**。
即使 F1 曲线按 58.03/41.97 重算（回测语义修复完毕），runtime 账户依然零黄金；反之给 runtime 接线也不回改回测曲线。用户评估时两者应分开决策、分开验收。

## 5. 选项与代价分析（决策归用户，本报告只供弹药）

### 选项 A：组合层 paper 合成（不碰真金）

把 equity 链与 gold 链按 58.03/41.97 + rebalance band 0.02 合成组合 NAV，投影进 governance/BFF/看板。

- 工程量：**中**。组合 NAV 合成器（月度再平衡语义、两链起点对齐：equity 08-14 10 万成本口径 vs gold 08-24 NAV=1.0）、vC-0 投影扩展（补 weights 块）、recon 扩展（sleeve 权重漂移检查目前对不上实际账户）、BFF 字段、看板新列。
- 风险：**在役触碰面大**——governance 投影/recon/BFF/看板全动；双记账歧义（合成组合 NAV vs 账户真实 NAV 两套数并存）；若 provenance 标注不严，重演 R-377 式「展示基底滞后于定义」漂移；PIT 上无新风险（两链各自已 PIT），但合成层引入再平衡时点选择（月度 vs band 触发）需预注册。
- 语义收益：看板出现真正的 vC-0 组合曲线；41.97% 从纸面解变成组合权重。
- 语义局限：即期黄金暴露仍=0，用户看到的 41.97% 第一天就几乎全在货基腿。

### 选项 B：真买（真金门）

真实资金按设计权重买入 518880（或按引擎信号）。

- 前置：真金分配人工门（R-307 声明永不自动化）+ 资金操作 + 券商通道（手动下单或 API，当前无接入）。
- 工程量/合规成本：**最高**；且当前信号 w=0，真金入场第一笔也只会是货基/空仓等待金叉。
- 本报告不建议与 A 混谈：A 是纸面组合语义修复，B 是资本决策，门槛完全不同。

### 选项 C：承认未完成腿（低代价路径）

设计层 vC-0 保留 41.97% 不动；runtime 如实呈现 a13 单引擎账户（60% 为择时输出+40% 现金），gold 腿标注为「独立 active_paper 监控链，未接入账户」。

- 工程量：**小**。runtime.json/BFF 语义标注、recon 该检查项加 details 注释（明确只证引用一致）、看板加一行说明。零在役数值改动。
- 风险：极低。代价：看板继续呈现「设计 vs 运行」差距，需用户接受 41.97% 短期不对应任何仓位。
- 配套可选：把 gold paper NAV 作为独立监控行展示（数据已在 paper_state.json，不并入账户 NAV），兼顾可见性与语义诚实。

## 6. 用户评估要点

1. 「黄金腿 runtime 未建仓」是事实且为门控设计使然：激活门（已过）≠ 组合接线门（未触发）≠ 真金门（永不自动）。41.97% 现在只存在于设计文档与 dryrun 解中。
2. 对账里 gold_engine_active_paper=true 不证明持仓存在，只是设计引用一致性检查——此前若据它认为黄金腿在运行，属语义错位，不是数据造假。
3. 当前黄金趋势信号本身也是空仓（px<SMA200），短期无论怎么接线都无黄金暴露；真正的时间敏感点是 9-01 调仓日的信号（8 月金价 +13.4% 部分月，08-24 已逼近 SMA200）。
4. 与 F1_quarterly 口径问题正交，建议分开决策（§4）。
5. 若选 C，建议同时给 recon 检查改注释防再误读；若选 A，建议先出组合层预注册（再平衡语义+起点对齐）再动在役投影。

## 7. 验收自检

- 报告 ≥6KB：✓（约 9KB）
- grep -c "paper_engine_gold" ≥3：✓（多处）
- 判定三选一明确段落：✓（§1）
- R-354 决策原文：报告内无黄金排除决策，已如实记录；真正的决策原文在 R-307 与 vC-0 capital_policy，均全文引用（§2.4）
- 纯只读：HP 仅 ssh 读文件/crontab/registry/versions；本地仅读文件+写本报告/笔记/README 日志，数据文件零改动 ✓
