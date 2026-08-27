# R-336 量化系统「破而后立」目标架构与迁移方案

- 任务号：task-0514 / 报告 R-336
- 日期：2026-08-27
- 触发：用户 23:30 原话「我希望系统架构从破而后立（重构）的角度考虑迁移，方案要考虑后续扩展性，专业性」+ 外部 AI 对 R-335 的评审（治理骨架保留、工程包袱推倒）+ 23:39 组合构建层增补建议
- 性质：**纯方案文档，零代码改动**。不改 API/前端/registry/crontab，不 SSH HP
- 与 R-335 的关系：R-335 是「吸收式」（兼容遗留、双读）；本方案是「目标态先行」——先白纸画标准架构，再设计迁移路径。治理骨架思想（版本对象+状态机+对账）保留，全部用标准术语重述

## 一句话版本

**先把系统当作白纸，用机构标准术语画出七层架构（数据→因子→回测→组合构建→组合→执行→风控，横切事件账本），把「A腿/gold腿/GM编号/F6F7」全部翻译成 sleeve/portfolio_version/gate 这类标准词并冻结成 GLOSSARY；再把现状里最危险的三个东西——未审计的回测、无数字的门禁、可变 JSON 里的隐式状态机——分别用「正确性审计+量化阈值表+append-only 事件账本」替换掉；最后分四阶段迁移（审计地基→影子双轨→治理切换→旧件退役），其中唯一需要你批准的红线是 Phase C 的 paper 指针语义切换。**

## 0. 破什么、立什么（方法论定位）

| 破（推倒的个人历史包袱） | 立（标准替代物） | 评审依据 |
|---|---|---|
| 私有术语体系（A腿/gold腿/GM1-15/F6/F7/R-xxx 进代码命名） | 标准术语七层架构 + GLOSSARY.md 唯一对照表 | 评审缺点1「术语代号强耦合」 |
| 状态机隐式存于可变 JSON（composites/engines/registry） | append-only event_log，JSON 降级为重放投影缓存 | 评审缺点2「未做事件溯源」 |
| 门禁靠口径描述、无逐层数字 | 分层毕业阈值表（研究→影子→paper→canary，全数字） | 评审缺点3「未量化=主观放行」 |
| 回测引擎基于旧脚本打补丁、正确性未审计 | 回测正确性审计清单（六项），不通过=迁移硬阻塞 | 评审缺点4「错误回测上越严格越危险」 |
| 只有归档、无退役规则 | 客观退役规则 + 影子 4 维漂移监控 | 评审缺点5/6 |
| 零常驻=零兜底 | 断路器 + checkpoint + 仓位对账三件套 | 评审缺点7 |
| 组合权重靠口径拍板（F6/F7 二选一） | 组合构建层（可插拔求解器：等波动率→风险预算/ERC，不用 MVO） | 23:39 增补建议 |

保留不破：组合作为一等版本对象、一切变更走同一条流水线、成绩单=回测成绩+逐条门禁原因、三方对账、双层门禁（组件级管「单拎够不够格」/组合级管「拼起来行不行」）、个人单机约束（不引入消息队列/多服务，事件账本=本地 JSONL）。

## 1. 目标架构白纸设计（七层 + 横切账本）

### 1.1 总图

```
┌─────────────────────────────────────────────────────────────────┐
│ ① Data Layer 数据服务层                                          │
│    PIT对齐·qfq复权·退市股·涨跌停掩码·成本模型 —— 四口径唯一出处    │
├─────────────────────────────────────────────────────────────────┤
│ ② Alpha Layer 因子/信号层                                        │
│    factor → signal（唯一输出契约：{date, symbol, weight/score}）  │
├─────────────────────────────────────────────────────────────────┤
│ ③ Backtest Layer 回测层（审计后可信）                             │
│    composite_backtest · 组件回测 · 双裁判（自研+qrun 交叉验证）    │
├─────────────────────────────────────────────────────────────────┤
│ ④ Portfolio Construction Layer 组合构建层【新增，23:39 增补】      │
│    给定风险预算求解 sleeve 权重：等波动率 → 风险预算/ERC           │
│    （协方差 Ledoit-Wolf 收缩；明确不用 MVO）                      │
├─────────────────────────────────────────────────────────────────┤
│ ⑤ Portfolio Layer 组合层                                         │
│    portfolio_version（一等对象）· promotion 状态机 · gate 报告     │
├─────────────────────────────────────────────────────────────────┤
│ ⑥ Execution Layer 执行层                                         │
│    paper / canary / live · rebalance · checkpoint · 撮合假设      │
├─────────────────────────────────────────────────────────────────┤
│ ⑦ Risk Layer 风控层（横切⑥⑤，裁决优先级：组合级 > 策略级）        │
│    回撤分级闸门 · sleeve级ddc · 断路器 · 退役 · 再平衡协调协议     │
└─────────────────────────────────────────────────────────────────┘
        横切：Iteration Ledger 迭代账本（append-only event_log）
        每层的每次状态变更都追加事件；当前状态 = 事件重放投影
```

### 1.2 逐层职责 / 接口 / 可插拔点

**① Data Layer 数据服务层**
- 职责：行情/财务/公告数据的唯一权威出口。四口径在此冻结并强制下发：PIT 对齐（NOTICE_DATE 细则，R-328）、qfq 前复权唯一口径（R-330 F4）、退市股全包含、涨跌停可交易掩码（Mask-First，R-333 实证 300862 一字板不可成交）、成本模型（R-333 实测三情景：记账 4.0bp / 可实现中间态 11.5bp/边 / 小微上限 15.7bp/边）。
- 输入：原始数据源（东财公告、腾讯 qfq、akshare）。
- 输出契约：`bar(symbol, date, ohlqfq_adj, tradable_mask, pit_fields...)`；任何上层拿到的数据必须已带掩码和复权，禁止上层自行 join 财务（000001 滞后 371 天反例即违反此契约的后果）。
- 可插拔点：**新资产类别**（可转债 R-332、利率债 ETF R-331、QDII R-330）= 新增一个 data adapter，注册进四口径校验清单即可，不动其他层。

**② Alpha Layer 因子/信号层**
- 职责：因子挖掘、验证、产出标准化 signal。现有 evolution_pipeline（registry 版，g1-g6 组件门禁）、辩论代理（R-334 吸收的双子代理）、Mask-First/ICIR+HMM（落 M5 择时）都归这层。
- 输入：Data Layer 契约数据。
- 输出契约：`signal(sleeve_id, date, positions, ic_series, turnover_estimate)`。
- 可插拔点：**新因子/新引擎** = 新 signal producer，注册进组件门禁（g1-g6），产物只是 portfolio_version 的一个候选组件指针。**新调度器**（半月/周/cron 变更）= Alpha Layer 内部实现细节，对下游不可见。

**③ Backtest Layer 回测层**
- 职责：组件回测 + 组合回测（composite_backtest），输出结构化成绩单（组合层指标 + 逐 episode 差分 + 声明区 + 门禁逐条通过/不通过）。**审计后可信是本层存在前提**（第 5 节）。
- 输入：signal + portfolio_version 配置（经组合构建层解析为权重）。
- 输出契约：`backtest_report(portfolio_version_id, metrics, gate_results[], assumptions[], md5_anchor)`。
- 可插拔点：**第二裁判**（qlib qrun 双轨，R-334 表②）= 独立回测实现注册进交叉验证清单，双窗 e2e diff 达阈值前不替换在役；F6/F7 口径 = composite_backtest 的两个口径插件（口径1=ddc 释放补 gold；口径2=50/50 打底+REDUCE 0.25/0.75）。

**④ Portfolio Construction Layer 组合构建层（新增）**
- 职责：给定风险预算，求解各 sleeve 权重。**与⑤解耦的铁律：portfolio_version 存「配置」（sleeve 指针/风控参数/求解器选型+参数），本层输出「权重求解结果」——配置与求解分离，禁止在 portfolio_version 上直接加 model_weights 字段**（否则配置与求解耦合，sleeve 增多后失控）。
- 演进分阶段：第一阶段=等波动率（equal-volatility，两三腿时最稳健）；第二阶段=风险预算/ERC（协方差用 Ledoit-Wolf 收缩估计）；**明确不用 MVO**（对收益预测误差极敏感，易过拟合集中）。
- 输入：各 sleeve 的滚动波动率/协方差（Data Layer 历史窗 + Backtest 层 sleeve 净值曲线）、风险预算参数。
- 输出契约：`weight_solution(portfolio_version_id, solve_date, weights{}, solver_meta{type, params, cov_estimator})`——求解结果本身也追加进 event_log，可重放。
- 可插拔点：**新求解器** = 注册式 solver（equal_vol / risk_parity / ERC / 未来 HRP），portfolio_version 里只存 solver_id+params。P2/P3 的约束体系、分层风险预算、HRP、体制切换=演进方向，本方案不现在做。

**⑤ Portfolio Layer 组合层**
- 职责：portfolio_version 一等对象（继承 R-335 vC-x.y 全部设计，重命名）：`{portfolio_version_id, sleeves{}, risk_control{drawdown_gates, sleeve_ddc, vol_target, backfill_rule}, solver_ref, parent_version, status, gate_report, paper_since}`。promotion 状态机：`candidate → backtested → gated → shadow → approved → paper → canary → live / archived / retired`。
- 输入：weight_solution + backtest_report。
- 输出契约：portfolio_version 对象 + 一张成绩单（用户唯一消费物：过了没、为什么没过）。
- 可插拔点：**新 sleeve** = components 加一条指针 + 权重求解器自动扩维（第三腿利率债 R-331 就这么进）。

**⑥ Execution Layer 执行层**
- 职责：paper/canary/live 三档执行、调仓、撮合假设声明（收盘竞价可成交=当前假设，R-333 已证其对佣金计费方式敏感）、checkpoint 快照。
- 输入：portfolio_version（live 指针）+ 权重。
- 输出契约：`execution_report(date, fills, slippage_actual, nav, checkpoint_ref)`。
- 可插拔点：**paper→live 切换** = 本层唯一人工门（用户批准）；canary 档预留小资金灰度，当前未启用。

**⑦ Risk Layer 风控层**
- 职责（两层独立触发、裁决优先级**组合级 > 策略级**）：
  - 组合级：回撤分级闸门（<5% 正常 / 5–10% 提级审查 / 10–15% 降仓×0.5 / >15% 熔断）+ 波动率目标化（参数位：target_vol 初版 8%，再平衡带 ±2pp）+ 断路器 + 退役规则；
  - sleeve 级：ddc（现 ddc_th20_rd50_rc5，受控净值回撤 ≤−20% → ×0.5，回补 −5%，T 判定 T+1 生效）保留不动。
  - 再平衡协调协议：sleeve 内部重大调仓后，组合层进入**冷却期（1 个完整调仓周期）**，期间组合级不因该 sleeve 风险贡献（RC）变化反向加仓——防「减仓→RC 骤降→被反向加仓」横跳震荡。
- 可插拔点：新风控规则 = event_log 里的 risk.* 事件类型扩展，不动状态机。

**横切 Iteration Ledger**
- append-only JSONL 事件账本（第 3 节）：每层每次状态变更追加事件；composites.json/engines.json/registry 全部降级为「重放投影缓存」。个人单机约束保留：本地文件，无消息队列、无常驻服务。

## 2. 术语体系：破个人命名的落地物

原则：**代码/文档/沟通一律用标准名；旧名只允许出现在 GLOSSARY 的左列**。新会话/新协作者只读 GLOSSARY 一页即可进入系统，消除单人锁定。

（可直接落盘的 GLOSSARY.md 全文见附录 A。）

## 3. 事件溯源改造（Iteration Ledger）

### 3.1 现状 → 目标

| 项 | 现状 | 目标 |
|---|---|---|
| 状态载体 | registry / engines.json / composites.json 三处可变 JSON，改了就没了原值 | append-only `events/iteration-ledger.jsonl`，一事件一行 |
| 历史追溯 | 靠 6 种散装留痕（decision-log/ledger/history/switch_log/n_trials_ledger/cycle-report + engines.audit） | 重放投影即完整历史 |
| 误操作恢复 | 无（覆盖即丢） | 重放到任意时间点重建状态 |
| JSON 文件角色 | 唯一事实 | **投影缓存**（重放结果的物化，可随时删了重建） |

### 3.2 事件类型枚举（v1）

```
# 对象生命周期
version.created        # 新 portfolio_version / registry candidate 创建
version.updated        # 非状态字段变更（动机、描述）
component.registered   # 新 signal producer / sleeve 注册
solver.selected        # 组合构建层求解器选型变更（含参数）
weight.solved          # 构建层权重求解结果（含 weights + solver_meta）

# 门禁与晋升
gate.evaluated         # 门禁评估完成（含逐条 pass/fail + 阈值 + 实测值）
promotion.requested    # 晋升申请（shadow/paper/canary/live）
promotion.approved     # 用户批准（actor=user）
promotion.rejected     # 用户拒绝（附原因）
promotion.executed     # 指针切换完成（含前后版本号）

# 风控与退役
risk.action            # 断路器/分级闸门/ddc 触发（含触发值与阈值）
retirement.triggered   # 退役规则触发（含规则编号与实测值）
retirement.executed    # 退役完成

# 数据与审计
backtest.completed     # 回测完成（含 md5 锚）
reconciliation.failed  # 三方对账不一致（含差异明细）
checkpoint.created     # 调仓后快照
```

### 3.3 事件格式与重放（单机版）

每行一个 JSON 对象：`{"ts": "...", "actor": "evolution_pipeline|user|risk_layer", "event_type": "gate.evaluated", "target": "PV-2.0", "payload": {...}}`。写前 `flock` 互斥（cron 与手动并发安全）；每行写完即 fsync；按月滚动文件（`iteration-ledger-2026-08.jsonl`）。

重放伪代码：

```python
def replay(ledger_files) -> State:
    state = State()                      # 空状态
    for line in chain(*ledger_files):    # 按时间序
        ev = json.loads(line)
        state.apply(ev)                  # 幂等 apply：version.created 建对象、
    return state                         # promotion.executed 移指针、risk.action 记录
# 投影缓存 = replay 结果 dump 回 registry/engines/composites JSON
# 校验：每次重放后对投影做 sha256，与缓存文件头记录比对，不一致即 reconciliation.failed
```

不引入消息队列/数据库：个人单机下 JSONL+flock 足够，结构上已满足「事件不可改、状态可重放、历史可审计」三要件。

## 4. 门禁量化阈值表（P0 核心）

以下全部为**初版建议值，可讨论调整，但必须是数字**——评审原话：未量化的门禁=主观放行。全部成本后口径。

### 4.1 研究候选 → shadow（进入影子观察）

| # | 判据 | 阈值 | 现状参照 |
|---|---|---|---|
| G-S1 | 样本外 Sharpe（2021-01 split 后） | ≥ 1.0 | g1 ICIR_IS≥0.5 之上新增组合级维度 |
| G-S2 | IS/OOS 收益比 | ≥ 0.5 | 防 IS 过拟合 |
| G-S3 | 参数扰动 ±20% 后 Sharpe 降幅 | ≤ 30% | 高原检验，防参数碰巧 |
| G-S4 | 成本后年化仍为正 | 是 | 成本用 R-333 可实现中间态 11.5bp/边，非记账 4bp |
| G-S5 | 与在役组合持仓相关性（holding-based） | ≤ 0.70 | 同源信号 >0.75 告警；危机期趋近 1 = 分散失效，重评 |
| G-S6 | 组件级 g1-g6 | 全 PASS | 现状已有，原样继承（ICIR_OOS p<0.05、max_corr≤0.7、DSR≥0.95、MDD 恶化≤2pp 一票否决） |

### 4.2 shadow → paper（影子毕业）

| # | 判据 | 阈值 |
|---|---|---|
| G-P1 | 影子期时长 | ≥ 1 个完整月频调仓周期 |
| G-P2 | 信号对齐率（影子 vs 回测同日信号一致） | ≥ 95% |
| G-P3 | 跟踪误差 | 在回测 TE 的 ±1.5 倍带内 |
| G-P4 | 4 维漂移初查（表见 7.2） | 无一项超带 |

### 4.3 paper → canary/live（执行毕业）

| # | 判据 | 阈值 |
|---|---|---|
| G-L1 | 4 维漂移全部在带内 | 连续 ≥ 2 个调仓周期（表见 7.2） |
| G-L2 | 成交/调仓执行率 | ≥ 90% |
| G-L3 | 实测滑点 vs 假设滑点 | ≤ 假设带 11.5bp/边 × 1.5 |
| G-L4 | 用户批准 | 唯一人工门（不可自动化） |

### 4.4 组合级风险闸门（Risk Layer 用，持续生效）

| 项 | 阈值（初版） | 层级 |
|---|---|---|
| 回撤分级闸门 | <5% 正常 / 5–10% 提级审查 / 10–15% 降仓×0.5 / >15% 熔断停新仓 | 组合级 |
| 波动率目标化 | target_vol 8%，再平衡带 ±2pp（参数位，Phase B 校准） | 组合级 |
| sleeve 级 ddc | ≤−20% ×0.5，回补 −5%（现 ddc_th20_rd50_rc5 原样保留） | sleeve 级 |
| 两层关系 | 独立触发、都触发时按**组合级 > 策略级**裁决取更严者 | — |

## 5. 回测引擎正确性审计方案（P0 第一优先）

评审原话：**「一个严格的门禁如果建立在错误的回测上，越严格越危险。」** 故本方案把回测审计放在迁移路径 Phase A 的第一位，且设为 Phase C（治理切换）的硬前置。

### 5.1 审计项清单（六项）

| # | 审计项 | 现状证据 | 审计方法 | 不通过后果 |
|---|---|---|---|---|
| A1 | 前视偏差（PIT 对齐逐因子核查） | R-328 已立 NOTICE_DATE 细则（严禁报告期直 join，000001 滞后 371 天反例）；R-317 回测脚本内建 PIT 断言（2015-06=FULL/2015-07=REDUCE/2020-06=REDUCE/2020-07=FULL） | 逐因子核查 join 键是否全部走 PIT 口径；锚点断言扩展到全部在役因子 | **绝对阻塞**：任何迁移不得进行 |
| A2 | 复权口径 | R-330 F4 冻结 qfq 唯一口径；513100 拆分未复权假 MDD −85% 为已知反例 | 全标的复权因子抽样对账（含 ETF 拆分案例）；对全部 sleeve 历史重算净值 diff | **绝对阻塞** |
| A3 | 退市股处理 | 股票池口径未系统核查 | 股票池含退市股清单 diff；历史各期股票池 vs 当日全市场（幸存者偏差检验） | 阻塞组合级历史结论采信 |
| A4 | 涨跌停可交易掩码贯穿性 | Mask-First 已吸收（R-334 表②）；R-333 实证 300862 四连一字板实际不可成交 | 验证掩码从 Data Layer→Backtest 撮合→paper 全链贯穿（三层各抽查一字板日） | 阻塞 paper→live 毕业门 |
| A5 | 滑点/冲击成本模型 | 现状=记账滑点恒 0（R-333 实证 dev_bp≡0）+假设 13bp/边（R-304 v2 冻结）vs 实测三情景 4.0/11.5/15.7bp | 采用 R-333 可实现中间态 11.5bp/边为基线；参与率 >0.1% 时启用平方根冲击项（Almgren-Chriss 简化式，当前实测参与率 0.002–0.07% 暂可豁免）；Phase B 期间用 paper 实测滑点回填校准 | 不阻塞迁移，但门禁 G-S4/G-L3 必须用校准后成本 |
| A6 | 分红除息处理 | 股票分红 vs ETF 分红处理路径未单独立案 | 抽样除息日对账（人工核对 3 个分红事件的前后净值） | 记录在案，异常才阻塞 |

### 5.2 审计方法三板斧

1. **锚点单测**：已知历史日期手工对账——复用并扩展 R-317 PIT 断言（四个锚点月份）+ F1 基线 md5（915e446388…）逐位复现；每个 sleeve 至少 2 个锚点。
2. **随机样本月度对账**：随机抽 3 个月，人工（子 agent）重算当月组合净值，与引擎输出 diff ≤1bp。
3. **paper 真实成本对账**：R-333 已完成（两代引擎 18 笔逐笔对账），直接引用其结论——本项已存在，不重做，只把它注册为持续对账任务（每季一次）。

### 5.3 审计结论的处置

审计不通过项 = 阻塞迁移的硬前置：A1/A2 任一 FAIL → F6/F7 及全部历史回测结论作废重跑（Phase B 顺延）；审计通过 → 「审计后可信」标记进 backtest_report 契约（第 1.2 节③），回测报告必须携带审计版本号。

## 6. 安全兜底三件套（P0）

评审缺点 7：零常驻服务=无灾备，实盘一旦自动下单缺兜底很危险。三件套全部落在 Execution Layer 与 Risk Layer，事件全部进 event_log。

### 6.1 断路器（circuit_breaker）

| 触发条件 | 初版阈值 | 动作 |
|---|---|---|
| 单日亏损 | ≥ 2.0% NAV | 当日停止开新仓（已持仓不动） |
| 组合回撤 | 进入 10–15% 带 | 降仓 ×0.5（分级闸门联动） |
| 组合回撤 | > 15% | 熔断：停新仓 + 提级审查 + 用户通知 |
| 报错率 | 连续 2 次调仓执行失败 或 日频任务连续 3 日失败 | 暂停自动流程转人工 |
| 数据陈旧 | NAV mark 停摆 ≥2 交易日（R-333 已发现 6 日停摆先例） | 冻结一切自动决策 |

恢复规则：断路器动作只能人工复位（promotion.approved 同级人工门），自动恢复禁止。

### 6.2 状态 checkpoint

每次调仓执行完成后写快照：`{date, positions, cash, nav, portfolio_version_ref, ledger_offset, md5}`。恢复 = 最近 checkpoint + 重放 checkpoint.ledger_offset 之后的 event_log。验证：恢复重建的持仓 vs paper 账本 diff=0。

### 6.3 仓位三方对账（three_way_reconciliation）

paper 账本 vs 引擎持仓 vs portfolio_version 定义，三方核对：
- 频率：每次调仓日强制 + 每周例行；
- 容忍度：单 sleeve 权重差 ≤1pp、现金差 ≤0.5% NAV、持仓标的集合完全一致；
- 超限动作：写 `reconciliation.failed` 事件（含差异明细）+ 冻结开新仓 + 用户通知。现有 paper 一致性徽标（P0/quantConsistDot）升级为本对账的前端呈现。

## 7. 退役机制 + 影子漂移监控（P1）

### 7.1 客观退役规则（自动触发、人工处置）

| # | 规则 | 初版阈值 | 触发后 |
|---|---|---|---|
| RET-1 | 组合级回撤超历史最大回撤 1.5 倍 | 现役参照 mdd −6.80% → 触发线 −10.2%（与分级闸门 10–15% 降仓带衔接） | `retirement.triggered` → 自动停用进 review → 用户裁决 |
| RET-2 | 连续跑输基准 | 连续 6 个月频周期 | 同上 |
| RET-3 | 组件因子 IC 衰减 | rolling IC 连续 3 月 <0 或 ICIR 连续 3 月为负 | 组件级退役（sleeve 内换 signal，不动组合） |
| RET-4 | 相关性失效 | 危机窗（组合回撤>5% 期间）holding corr >0.90 | 分散失效 flag → 提级审查 |

退役≠删除：`retirement.executed` 后该 sleeve 移出 portfolio_version、生成新版本走流水线，旧版本与全部事件留档可回溯。

### 7.2 影子 4 维漂移监控表（shadow/live 通用）

| 维度 | 定义 | 带宽（初版） | 监控频率 |
|---|---|---|---|
| D1 日 P&L 偏差 | \|shadow P&L − 回测同日 P&L\| / NAV | ≤ 20bp/日（月累计 ≤1.5×回测月波动×权重） | 每日 |
| D2 Sharpe 偏差 | rolling 60 日 Sharpe（shadow）−（backtest 同窗） | \|Δ\| ≤ 0.3 | 每周 |
| D3 成交/调仓执行率 | 实际成交笔数 / 计划调仓笔数；信号对齐率 | 执行率 ≥90%；对齐率 ≥95% | 每调仓日 |
| D4 滑点偏差 | 实测滑点 vs 假设（11.5bp/边） | ≤ 假设 ×1.5 | 每调仓日 |

毕业规则回连第 4 节：shadow→paper 看 G-P1..P4，paper→canary/live 看 G-L1..L4（4 维全部在带内连续 ≥2 个调仓周期）。任何一维连续 2 期超带 → 晋升冻结 + 漂移归因报告。

## 8. 迁移路径（破而后立的「迁」）

四阶段，每阶段有独立验收与回滚；前两阶段不动任何在役流程。

### Phase A：审计与地基（零在役风险，先行）

| 项 | 内容 | 验收命令 |
|---|---|---|
| A-1 回测审计 | 第 5 节六项审计全部执行并出报告（R-333 复用不重做） | 六项逐项 PASS/FAIL 清单落盘；A1/A2 FAIL = 后续阶段顺延 |
| A-2 GLOSSARY | 附录 A 落盘 `05-量化投资/GLOSSARY.md`，旧名冻结 | 文件存在；新文档全部用标准名 |
| A-3 事件账本骨架 | 建 `events/iteration-ledger.jsonl` 空账本+重放器（零代码=此阶段仅设计冻结，代码实施另行立项） | 设计文档验收：事件类型表+重放伪代码与第 3 节一致 |

回滚：无需要回滚的内容（纯新增，零在役触碰）。

### Phase B：目标态影子运行（双轨核对）

新账本记录所有变更事件（version/gate/promotion 事件），与旧 registry/engines/composites JSON **双轨核对**：每日重放投影 vs 现存 JSON 三方 diff=0 才算通过；组合构建层用等波动率求解器跑纯影子（不切任何指针）。

验收：连续 4 周双轨 diff=0；等波动率求解器输出的权重解与 F7a 50/50 手工口径差异 <2pp。回滚：停新账本记录即可，旧流程从未被改。

### Phase C：治理切换（⚠️ 红线区）

组合版本/门禁/晋升全部走新架构；旧 registry 入口**冻结只读**；断路器/分级闸门/checkpoint/三方对账上线。

> ⚠️ **红线标注：本阶段中「paper 指针语义切换」= 改 active 语义，必须用户批准，不可自动执行。** 与既有「激活类变更批准」同一人工门。未获批准前 Phase C 其余项也不得执行（避免半新半旧状态长期并存）。

验收：`promotion.executed` 事件链完整；三方对账徽标绿；断路器演练（模拟触发一次单日亏损事件，验证停新仓动作+人工复位）。回滚：paper 指针回切旧语义 + 旧 registry 解冻只读（旧入口在 Phase D 前不删，回滚路径保持畅通）。

### Phase D：旧件退役清单（需用户逐项批准）

| 退役件 | 动作 | 前置 |
|---|---|---|
| composites.json 可变写路径 | 转为投影缓存（只由重放器生成） | Phase C 验收后 2 周 |
| p3_3_evolution_standalone 双 cron | 停（R-334 已裁决，动 crontab 需批准） | GM4 单轨化 |
| 散装留痕 6 载体 | 只读归档，新事件只进 event_log | event_log 连续 4 周无 reconciliation.failed |
| F6/F7 硬编码脚本 | 移交 composite_backtest 口径插件，旧脚本 trash | 口径插件 md5 复现 F1 基线 |
| 旧术语在代码/文档中的残留 | grep 清零（GLOSSARY 左列词不再出现于新代码） | 全量 grep 计数归零 |

### 8.1 风险表（迁移全程适用）

| 风险 | 描述 | 缓解 |
|---|---|---|
| 回测审计 FAIL 推翻存量结论 | A1/A2 不过 → F6/F7 历史成绩单作废，Phase B/C 顺延 | 这正是审计目的：宁可在假数据上暂停，不在假数据上加速；重跑成本已由 R-317 156 月管线降低 |
| 双轨期状态漂移 | 新账本与旧 JSON 不一致 | 每日 diff=0 硬验收；不一致即 reconciliation.failed 冻结切换 |
| 半新半旧长期并存 | Phase C 批准迟迟不至，两套并行磨损 | Phase C 整体打包为单次切换（见红线标注），不逐项切 |
| 等波动率求解器与 F7a 口径冲突 | 影子期权重差 >2pp | 差异写进 shadow 报告供用户拍板；Phase B 不切指针，冲突只影响观察值 |
| 术语切换沟通断层 | 用户/协作者对旧名的肌肉记忆 | GLOSSARY 双向索引；过渡期（Phase A-C）对话中标准名后括注旧名一次 |
| 事件账本损坏 | 断电/并发写 | flock+fsync+按月滚动；月文件 sha256 快照（只追加，永不改写） |
| 新增求解器引入过拟合 | ERC 参数拟合窗口敏感 | 求解器只用波动率/协方差（不含收益预测）；Ledoit-Wolf 收缩；Phase B 影子期对比等波动率 |

## 9. 结论

1. 破而后立的边界：破的是**命名体系、隐式状态、未审计回测、无数字门禁、无兜底**；立的是**标准术语七层架构+事件溯源+量化阈值+安全三件套**；治理骨架（版本对象/状态机/成绩单/对账）保留并用标准术语重述。
2. 七层架构中组合构建层（等波动率→ERC，不用 MVO；配置与求解分离）是「叠加更多模型+按风控分仓位」的正解，也是扩展性的落点：新资产=Data adapter、新因子=signal producer、新求解器=solver 注册、新腿=sleeve 指针。
3. 门禁全部数字化：G-S1..S6 / G-P1..P4 / G-L1..L4 三级毕业 + 组合级回撤分级闸门（5/10/15%）+ vol target 8%±2pp；与 sleeve 级 ddc 两层独立触发、组合级优先。
4. 回测正确性审计（A1-A6）是第一优先且 A1/A2 FAIL = 硬阻塞；R-333 成本审计直接复用注册为季度任务。
5. 迁移四阶段 A（审计+地基）→ B（影子双轨）→ C（治理切换，⚠️ paper 指针切换需用户批准）→ D（旧件退役，逐项批准）；全程不动 registry active/paper_engine/HP crontab 直到对应批准发生。

---

## 附录 A：GLOSSARY.md（可直接落盘）

```markdown
# GLOSSARY 量化系统术语表（v1，R-336 冻结）
# 规则：代码/文档/沟通一律用右列标准名；左列旧名仅存于本表与历史报告。

## 对象与层
| 旧名 | 标准名 | 说明 |
|---|---|---|
| A腿 / 小市值策略 | sleeve_equity | 股票 alpha sleeve（小市值因子线） |
| gold腿 / 黄金引擎 | sleeve_gold | 黄金趋势 sleeve |
| （未来）利率债第三腿 | sleeve_bond | R-331 候选，架构预留 |
| vC-x.y | portfolio_version(PV-x.y) | 组合版本一等对象 |
| GM1-GM15 | milestone_ref GM-x（仅历史引用） | R-322 通用模块编号，冻结为历史里程碑，不再用于新命名 |
| F6 | composite_backtest 口径1（ddc 释放补 gold） | R-316 |
| F7a/F7b | composite_backtest 口径2（50/50 打底 + REDUCE 0.25/0.75） | R-317 |
| registry | model_registry | 组件版本注册表 |
| engines.json | runtime_engine_state | 引擎运行态登记 |
| composites.json | portfolio_registry（Phase C 后=投影缓存） | 组合版本注册表 |
| 层2补位 / backfill | overlay_backfill | ddc 释放部分补位规则 |
| ddc / 中央风控 | sleeve_drawdown_controller(DDC) | th20_rd50_rc5 |

## 流程与状态
| 旧名 | 标准名 | 说明 |
|---|---|---|
| 候选→pending→active→sota→retired（组件） | component lifecycle: candidate→pending→active→sota→retired | 保留原语义 |
| 候选→回测→门禁→影子→批准→paper→归档（组合） | promotion lifecycle: candidate→backtested→gated→shadow→approved→paper→canary→live / archived / retired | R-335 状态机的标准化 |
| 影子 | shadow trading | 与在役并行观察 |
| paper / 模拟实盘 | paper trading | 模拟执行档 |
| 小资金灰度 | canary | 预留档 |
| 五门禁（早期口径）/ g1-g6 | component gate CG-1..6 | GATE_CONFIG 实测为 g1-g6，五门禁=早期规划口径 |
| 组合门禁 | portfolio gate PG | mdd/Calmar/相关性等 |
| 退役 | retirement | RET-1..4 客观规则 |
| 6 种留痕载体 | event_log（iteration ledger） | 全部收敛进 append-only 账本 |
| 三方对账 / 一致性徽标 | three_way_reconciliation | paper↔engine↔version |

## 数据与信号
| 旧名 | 标准名 | 说明 |
|---|---|---|
| 因子/模型输出 | signal | Alpha Layer 唯一输出契约 |
| R-xxx 代号 | report_id（编号保留，不再作对象名） | 报告编号系统不变，但对象/变量命名解耦 |
| 成本 v2 / 13bp | cost_model_v2 → cost_model_calibrated | R-333 三情景校准后为 11.5bp/边基线 |
| 进化双轨 D6 | legacy_evolution_track（Phase D 退役） | p3_3 停用后消亡 |
| 涨跌停掩码 / Mask-First | tradable_mask | Data Layer 四口径之一 |
```

## 来源清单

- 外部评审全文：work/source-review-r335-external.md（2026-08-27 23:30 用户提供）
- 组合构建层增补建议：work/source-advice-portfolio-construction.md（2026-08-27 23:39 用户提供）
- R-335 组合版本统一迭代架构方案（被评审对象，治理骨架来源）
- R-334 量化架构简化重构调整版方案（qlib 双轨/PIT/qfq/Mask-First/成本四口径、GM 编号处置）
- R-333 paper 真实成本对账审计（A5 审计项直接引用：4.0/11.5/15.7bp 三情景、一字板实证）
- R-328 PEAD E2 预注册（NOTICE_DATE PIT 细则与 371 天反例）
- R-330 QDII G3 判门口径（F4 qfq 唯一口径、513100 反例）
- R-317/R-316（156 月统一口径、F1 md5 基线、ddc 语义）、R-318（层2 补位与基线事实）
- work/task-0501-notes.md（现状两径汇流、GATE_CONFIG、STATUS_ENUM、双 cron 实证）
- work/task-0514-notes.md（本报告过程笔记）

---

*本报告纯方案设计，零代码改动。Phase C 涉及 paper 指针语义切换与 Phase D 涉及 crontab/退役的每一项，均需用户批准后方可执行；registry active / paper_engine / HP crontab 在役项零擅动红线原样沿用。*
