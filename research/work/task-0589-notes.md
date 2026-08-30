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
