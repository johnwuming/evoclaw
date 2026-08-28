# R-351 Phase A 跟踪条件处置：roe/roa 补验 + 卖出跌停闸/DIV_EVENTS 修复方案

- 任务号：task-0550 ｜ 日期：2026-08-29 ｜ 性质：①只读补验（R-345 附加条件①，P0 前置）+ ②③方案起草（零代码改动、零在役触碰）
- 上游：R-345 §九附加条件（①PIT 补验强制项；②paper_engine 两缺口修复项）；方法论：R-343 逐行代码核验范式（as-of/shift(1) 判定标准）
- 过程笔记：`shared/results/work/task-0550-tracking-notes.md`（检查点 1–6 全证据链）
- HP 访问：SSH 只读；python=`/home/noname/miniconda3/envs/quant/bin/python`；未杀任何在役进程

## 〇、总裁决（先行）

| # | 事项 | 判定 | 一句话依据 |
|---|---|---|---|
| ① | roe/roa 过滤通道构建器 PIT 补验 | **安全——全链路无前视，Phase B 影子层消费放行** | 构建=法定披露截止日映射+bisect 真 as-of；消费=调仓日向后取快照；所有精确性瑕疵均为"滞后"方向，无一"领先" |
| ② | paper 卖出侧跌停闸缺失 | **方案已成稿，待用户批准后实施** | 卖出两路径（清仓 L1442 / 减仓 L1460）均无跌停检查；当前 8 只在持仓，属活敞口 |
| ③ | DIV_EVENTS 分红入账未接线 | **方案已成稿，待用户批准后实施** | L61 定义后全文件 0 次引用；8 只在持仓跨除息日即失真，属活敞口 |

**对 R-345 总裁决的影响：无变化。** ①补验通过后，R-345 A1 的唯一残留事项清零，六项审计全部闭合；②③按 R-345 语义本就是"修复项、不阻塞、不自动修"，本报告只交付方案，**实施必须经用户批准**。

---

## 一、①roe/roa 过滤通道构建器 PIT 补验（P0 前置项，已完成）

### 1.1 构建器定位勘误（解释 R-345 为何未能在预算内核验）

R-345 §二.6 将构建器指向 `scripts/fetch_valuation_data.py` 并报告 "grep lag/shift/avail/as_of 命中 0"。本次定位结果：

- `fetch_valuation_data.py`（470 行）**只读不写**该面板：L41 `FUND_PANEL` 仅用于构建行业 PE 月度中位数（L377–405 `build_industry_pe_monthly` 读面板 merge 行业映射），不产出 roe/roa。
- 真正构建器是 **`scripts/prep_dividend_roa.py`（396 行，L42 `FUNDAMENTALS` 输出路径）**——其实现用 `bisect`/`searchsorted` 手写 PIT join（L352 注释自述"替代 merge_asof 以兼容 pandas 3.x"），故 R-345 的关键词 grep 即使查对文件也命不了中。**两处叠加导致该通道成为审计盲区，非代码有恙。**

### 1.2 构建层证据（prep_dividend_roa.py，逐行）

| 环节 | 位置 | 机制 | 判定 |
|---|---|---|---|
| 披露日映射 | L195–206 `disclosure_available()` | 报告期→**法定披露截止日**：Q1→4/30、中报→8/31、Q3→10/31、年报→次年 4/30 | PIT 安全（截止日必已披露，最坏滞后不领先） |
| avail_date 生成 | L252 | `fin["avail_date"] = fin["report_date"].map(disclosure_available)` | 同上 |
| roe_ttm/roa_ttm | L255–266 | TTM 滚动 4 季求和；roa=roe×(1−资产负债率) | 财务计算，无时点问题 |
| 面板月份键 | L309–318 | `date`=**日历月末**（MonthEnd），close 取当月最后交易日收盘 | 无前视 |
| div_yield_ttm | L322–334 | `searchsorted(ex_date, 月末, side="right")` 累计 → 只含 ex_date ≤ 月末的已实施分红 / 月末收盘 | PIT 安全 |
| **roe/roa as-of join** | **L346–380** | 对每只股票按 avail_date 排序，`bisect.bisect_right(av_dates, d) - 1` 取 **avail_date ≤ 面板月末 d 的最后一条**（注释自述 point-in-time join） | **真 as-of backward join，报告期直 join 结构性不存在** |
| 边界语义 | L352–355 | d == avail_date 当日即纳入 | 安全：法定截止日当天财报必然已可得（监管要求），当日收盘可用 |

### 1.3 消费层证据（a13 引擎链，逐行）

| 环节 | 位置 | 机制 |
|---|---|---|
| 引擎加载 | a13_run.py L22–31 | `load_engine()` → `backtest_dividend_quality_iter.py` + `patch_engine`（a9_common.py） |
| 调仓日 | backtest_dividend_quality_iter.py **L250** | `rebalance_dates = 每月首个交易日`（`groupby(dt.to_period("M")).min()`） |
| **fund 快照** | 同文件 **L389–390** | `fund = panel[panel["date"] <= d].sort_values("date").groupby("code").tail(1)`——调仓日 d 向后取最近月末面板行，**as-of 语义** |
| 闸门 | a9_common.py L49–73（PA） | `fund.loc[code, "div_yield_ttm"/"roe_ttm"/"roa_ttm"]` 过滤（div_min=0.02 / roe_min=0.15 / roa_min=0.10） |
| roe 因子（权重 0.3） | a13_run.py L103 + a9_common.py L155–156 | `roe` 取自 `tdf`（目标持仓表），tdf 源自同一 fund 快照——与闸门同源同时点，无二次对齐风险 |
| pb 因子（权重 0.7） | a9_common.py L237–249 | `merge_asof(avail_date, backward)`——R-345 §二.1 已核验 PASS，本次不重做 |
| 收益归属 | L389 快照 → L250 月初执行 | 信号=上月末及更早信息，执行=次月首个交易日收盘，净值向后累积——R-343 §二定义的标准无前视结构 |
| 退市镜像 | q4b_build_delisted_panel.py L15 | "statYear 数据在 (year+1)-05 才生效，面板 date=生效月末日"——比主面板更保守，PIT 安全 |

### 1.4 方向性分析与结论

逐环节检查精确性瑕疵的方向：

1. 披露日用**法定截止日**而非真实 ann_date：实际 3 月已披露的一季报，面板 4/30 才可用——**滞后方向**（保守），无领先。
2. 月末归一（最后交易日→日历月末）：调仓日在月初，快照最多用到上月末数据——滞后方向。
3. `disclosure_available` 对 1–3 月报告期统一映射 4/30，含 Q1 与部分年报错位可能——最坏也是晚用，不早用。

**结论：构建器+消费链全链路无前视。** a13 因子的 roe 通道（闸门 roe_min=0.15 + 因子权重 0.3）与 roa 通道（闸门 roa_min=0.10）历史结论**无需重新定性**，R-345 §九条件①的唯一未尽事项就此闭合，**Phase B 影子层消费 a13 因子面板放行**。

---

## 二、②卖出侧跌停闸修复方案（建议稿——实施须用户批准）

### 2.1 现状与证据

- 回测层已有闸：a13 BASE `limit_board="on"`、`limit_up_pct=0.098`（a13_run.py L60；R-345 §五.1）。
- paper 买入侧已有闸：`is_limit_up`（paper_engine.py L949–963，qfq 收盘 pct ≥ th−1e-4，ST 分阈 0.05/0.098）+ 买入前硬闸（L1499–1502）。
- **paper 卖出侧无闸**：`grep -c limit_down` = **0**。卖出仅两路径——
  - **清仓卖出**（L1433–1455）：sell_list = 不在目标 ∪ ST ∪ 无价，逐只按 `get_price(d)` 成交并 `del holdings`；
  - **择时减仓**（L1460–1492）：超配 5% 阈触发，按市值降序逐只 trim。
  - 两处均按当日收盘价直接入账，跌停一字板日照常"卖出"。R-345 审计时 0 笔卖出未行使；**当前 paper-state 8 只在持仓（task-0486 重建后），9/1 调仓起随时可能行使，缺口已从"潜伏"转为"活敞口"**。

### 2.2 方案（不改在役代码，以下为实施蓝图）

**修改点 1——新增 `is_limit_down(code, d, st_flags)`（建议插在 L963 is_limit_up 之后，约 +15 行）**：镜像 is_limit_up 结构（qfq 收盘 `pct = cur/prev − 1`，容差 `+1e-4`），但阈值**板块感知**：

```
th = 0.198  若 code 前缀 ∈ {300,301,688,689}（创业板/科创板 ±20%，ST 同板仍 20%）
th = 0.05   若主板且 is_st_on（主板 ST ±5%）
th = 0.098  其余主板
判定：pct <= -th + 1e-4（收盘锁在跌停价）
```

为何不用买入侧的统一 0.098：a13 微盘宇宙含创业板标的，单日 −10%~−15%（未锁跌停）并不罕见；卖侧误闸的代价是**多扛一个月下跌**（真实损失），与买侧误闸（少赚）不对称，故卖侧阈值必须分板，防系统性误闸。

**修改点 2——清仓卖出块（L1442 循环体内、执行卖出前）+4 行**：`if GATE_ON and is_limit_down(code, d, st_flags): log("跳过卖出 …跌停无法卖出"); continue`——**不 del holdings、不入账**；持仓保留，下月调仓因仍不在目标集自然重试。

**修改点 3——择时减仓块（L1464 循环体内）+3 行**：同样 skip 该 code，`continue` 处理下一只（减仓缺口由后续候选承接，承接不足则顺延）。

**开关**：`PAPER_LIMIT_DOWN_GATE = os.environ.get("PAPER_LIMIT_DOWN_GATE", "on") == "on"`——运行时 kill switch，回退不依赖回滚文件。

### 2.3 预期行为

- 跌停收盘日触发卖出 → 拒绝成交、持仓保留、现金不变、trades.csv 无该笔记录、log 留痕；NAV 按跌停收盘价标记（get_price 照常）。
- 次月调仓自动重试；若连续跌停则连续顺延——与真实市场"一字跌停卖不出"一致。
- 历史零重述：现有 8 笔买单与历史净值不受影响，闸门只对生效后的卖出行使。

### 2.4 回退方案

1. 环境开关置 off（即时生效，无需回滚代码）；
2. `cp paper_engine.py paper_engine.py.bak.task0550_YYYYMMDD`（沿用既有 .bak 约定），异常时整文件还原；
3. 改动面局部（1 个新函数 + 2 处 3–4 行插入），无 state/trades schema 变更，无迁移负担。

### 2.5 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| 阈值口径争议（20% 板阈值取 0.198 容差） | 低 | 容差与 is_limit_up 对齐；阈值常量化便于调参 |
| qfq 文件刷新滞后 + 恰逢除息日 → pct 失真误闸 | 低（概率小、代价=顺延一月） | 文件每日刷新；可接受，v1 不引入原始价修正 |
| 被闸持仓持续下跌放大回撤 | 语义正确性代价 | 这正是真实市场行为；闸门目的是消除"跌停也能卖"的虚幻成交 |
| 与 ST 卖出规则叠加：ST 跌停 −5% 卖不出 | 预期行为 | 真实约束，非缺陷 |

---

## 三、③DIV_EVENTS 分红入账接线方案（建议稿——实施须用户批准）

### 3.1 现状与证据

- `paper_engine.py` L61 定义 `DIV_EVENTS` 路径常量，**全文件 0 次读取**（grep 确认，R-345 L100 结论复核属实）。
- 数据在位：`data/derived/dividend_events.parquet`（48,081 行；code/ex_date/cash_per_share/period；2026-05 以来 3,470 条）。**注意该文件最后构建于 2026-08-13 且 crontab 无自动刷新**——接线方案必须附带数据新鲜度处置。
- 失真机制：paper 标记价用 qfq（当前价=真实价），持仓跨除息日时价格自然回落，但现金分红不入账 → **NAV 低估恰好一个分红额**。R-345 审计时持有窗口 0 命中（4 个代码级疑似全在窗口外）；**当前 8 只在持仓，分红季（5–8 月高峰刚过、年度分红仍陆续实施）随时可触发，属活敞口**。

### 3.2 方案

**修改点 1——加载与水位线（约 +10 行）**：`load_div_events()` 读 parquet 建 `code → [(ex_date, cash_per_share)]` 有序表；state 新增 `state["last_div_date"]`（ISO 日期串），缺失时初始化为 `state["created_at"]` 日期（保证重建组合前的历史事件不追溯入账）。

**修改点 2——日常挂点：action_daily 缺口回填循环内（L1330 区段，逐日 upsert NAV 处）**：对每个回填日 t（含今日），处理 `ex_date ∈ (last_div_date, t]` 且当前持仓中 `buy_date < ex_date` 的持仓：`state["cash"] += shares × cash_per_share`，写台账，推进水位线。逐日处理（而非一次性合并到最新日）保证 NAV 曲线在除息当日精确入账。

**修改点 3——调仓挂点：action_rebalance 卖出块之前（L1442 前）+8 行**：以同一水位线函数处理 `ex_date ≤ 今日` 的事件后再执行卖出。**此挂点不可省**：除息日当日卖出仍享有分红（A 股规则，T−1 收盘持有即享有；R-345 §七.2 的 601600 案例即"除息日当天买入不享有"的同型边界），若只在 daily 挂点，先跑 rebalance 后跑 daily 的时序会漏掉"卖出当天除息"的账。

**entitlement 规则（两挂点共用）**：`buy_date < ex_date` 且处理时点该持仓仍在 state 中 → 享有。shares 在两次调仓间恒定，无需按日快照。

**台账**：新增 `results/paper-div-ledger.csv`（date/code/shares/dps/amount，append-only）——**不写入 trades.csv**，避免"div"动作类型冲击既有 trades 消费方（R-333 对账、NAV 审计）的 schema 假设。

**税务（披露性决策点）**：v1 按**毛额**入账（略乐观——真实世界股息红利差别化税率：持有 ≤1 月 20%、1 月–1 年 10%、>1 年免税，卖出时补扣）。a13 持有期约 1 个月，现实税负约 10%。v1.1 可选在卖出时按持有期补扣 10% 预扣估计。**采用毛额还是即扣 10%，请用户在批准时一并裁定。**

**数据新鲜度配套**：接线生效后，每月调仓前手动（或由 data_validator 扩展一条新鲜度检查，属另一笔小改动、同批批准）执行 `prep_dividend_roa.py --only div` 刷新事件表；stale 事件表的后果=漏账（不是错账），水位线机制天然幂等可补。

### 3.3 预期行为

- 持仓跨除息日：除息当日现金增加 `shares × cash_per_share`，NAV 不再因价格回落而低估；台账留痕可审计。
- 与 qfq 标记价天然自洽：价格回落（真实价）+ 现金入账（分红）= 持有人真实经济利益，两半各归其位。
- 幂等：水位线 + save_state 原子推进，重跑不双记；append_nav 本身按日 upsert，兼容回填。

### 3.4 回退方案

1. 还原 `paper_engine.py.bak`（改动集中在 1 个加载函数 + 2 个挂点，无在役逻辑重排）；
2. state 多出的 `last_div_date` 字段对旧代码无害（dict 多余键），回退无需清洗 state；
3. 台账文件独立，删除即净；已入账现金如需精确回冲，按台账逆序核减（预案记录，正常不需动用）。

### 3.5 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| 双重入账（重跑/回填窗口重叠） | 中（机制性） | 水位线只在 save_state 成功后推进；挂点函数单一共享；上线后首月核对台账 vs cash 变动 |
| 漏账（事件表 stale / 卖出当日除息且仅 daily 挂点） | 中 | rebalance 前置挂点封堵时序漏洞；新鲜度配套处置 |
| 毛额入账略乐观（税差 ~10%） | 低（金额小） | 已列为批准时的显式决策点；v1.1 可补扣 |
| 退市股 dividend_events 覆盖缺口 | 低 | 退市持仓在 sell_list 优先级已处理；接线后首月抽 1 只真实除息持仓人工对账 |
| state schema 演进（新增键） | 低 | 旧代码忽略未知键；task-0486 重建链兼容 |

---

## 四、实施顺序与批准点（显式声明）

| 顺序 | 事项 | 性质 | 批准点 |
|---|---|---|---|
| 0 | ①roe/roa 补验 | **已完成（本报告，只读）** | 无需批准；R-345 附加条件①就此闭合，Phase B 影子层消费 a13 面板放行 |
| 1 | ②卖出跌停闸 | 待实施 | **须用户批准**。建议在 2026-09-01 月度调仓前实施（8 只在持仓，9/1 起即可能行使卖出）；批准时请裁定是否采纳板块感知阈值（推荐）或买入侧统一 0.098 镜像（更简但创业板误闸偏多） |
| 2 | ③DIV_EVENTS 接线 | 待实施 | **须用户批准**。可紧随②同批实施（改动同文件，一次备份一次验证）；批准时请裁定分红入账口径：毛额（v1 默认）或即扣 10% 预扣（更贴近真实） |

两处实施共用一套验证协议：改前 `.bak` 备份 → 改后跑 `--action validate` + 次日 `--action daily` 观察日志 → 台账/卖出 skip 日志抽查 → README 更新日志。**在未经用户批准前，本报告不改任何在役文件。**

## 五、零改动声明

- HP 侧全程 SSH 只读：未修改 paper_engine/registry/evolution_pipeline/crontab/engines，未杀任何在役进程，未在 HP 落任何新文件（本轮所有勘察经 grep/sed/python -c 标准输出，无脚本上传）。
- 本地产物仅三处新写入：本报告、过程笔记、README 更新日志一行。
- `find -newermt` 对照自检于交付前执行（见 notes 检查点 7）。

## 六、来源

- R-345 §二.6/§五/§七/§九（三项定义与缺口披露）；R-343 §二/§六（逐行核验范式与判定标准）
- HP 代码（只读引证）：scripts/prep_dividend_roa.py（L195–206/252/275–343/346–380）；scripts/backtest_dividend_quality_iter.py（L187–190/250/389–390）；scripts/a9_common.py（L23–32/49–73/155–156/237–249）；scripts/a13_run.py（L22–31/60/103）；scripts/q4b_build_delisted_panel.py（L15）；scripts/paper_engine.py（L61/93–98/286/949–990/1036–1048/1312–1330/1385–1502）；data/derived/{fundamentals_monthly.parquet, dividend_events.parquet}；results/paper-state.json
