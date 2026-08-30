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
