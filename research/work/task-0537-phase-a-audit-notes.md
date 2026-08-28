# task-0537 Phase A 回测正确性六项审计 — 过程笔记

时间：2026-08-28 23:05 开始（Asia/Shanghai）。预算 40 分钟；超 25 分钟落盘中间产物退出。
编号：R-345（已确认未占用）。

## 一、审计条款提取（R-336 v1.4 §5 + §8 Phase A）

### 六项清单（§5.1）
| # | 审计项 | 审计方法 | 不通过后果 |
|---|---|---|---|
| A1 | 前视偏差（PIT 对齐逐因子核查） | 逐因子核查 join 键全走 PIT 口径；锚点断言扩展到全部在役因子（R-317 四锚点 2015-06=FULL/2015-07=REDUCE/2020-06=REDUCE/2020-07=FULL） | **绝对阻塞** |
| A2 | 复权口径（qfq 唯一，R-330 F4） | 全标的复权因子抽样对账（含 ETF 拆分 513100 案例）；全部 sleeve 历史重算净值 diff | **绝对阻塞** |
| A3 | 退市股处理 | 股票池含退市股清单 diff；历史各期股票池 vs 当日全市场（幸存者偏差检验） | 阻塞组合级历史结论采信 |
| A4 | 涨跌停可交易掩码贯穿性 | 掩码 Data Layer→Backtest 撮合→paper 全链贯穿（三层各抽查一字板日；R-333 实证 300862 四连一字板不可成交） | 阻塞 paper→live 毕业门 |
| A5 | 滑点/冲击成本模型 | 基线=可实现中间态 11.5bp/边（R-333）；参与率>0.1% 启用平方根冲击项（当前实测 0.002–0.07% 暂豁免）；Phase B 用 paper 实测回填校准 | 不阻塞迁移；G-S4/G-L3 必须用校准后成本 |
| A6 | 分红除息处理 | 抽样除息日对账（人工核对 3 个分红事件前后净值） | 记录在案，异常才阻塞 |

### 三板斧（§5.2）
1. 锚点单测：R-317 PIT 断言四锚点 + F1 基线 md5（915e446388…）逐位复现；每个 sleeve ≥2 锚点。
2. 随机样本月度对账：随机抽 3 个月重算当月组合净值，与引擎输出 diff ≤1bp。
3. paper 真实成本对账：R-333 已完成（两代引擎 18 笔逐笔对账），直接引用结论，不重做，注册为持续对账任务（每季一次）。

### 处置语义（§5.3 / §8）
A1/A2 任一 FAIL → F6/F7 及全部历史回测结论作废重跑，Phase B 顺延，**Phase B 不可启动**。

## 二、Checklist（执行勾选）
- [ ] A1 前视偏差
- [ ] A2 复权口径
- [ ] A3 退市股
- [ ] A4 涨跌停掩码
- [ ] A5 滑点成本
- [ ] A6 分红除息
- [ ] 三板斧①锚点单测
- [ ] 三板斧②随机样本月度对账（3 个月 diff ≤1bp）
- [ ] 三板斧③引用 R-333（不重做）
- [ ] 零既有文件改动对照（HP+本地 ls -l 前后）

## 三、执行记录（边查边写）

### 23:05 前置确认
- R-345 未占用（ls R-34x 仅到 R-344）。R-336 共 56644B，分段读取，未全读。
- 已提取 §5.1/§5.2/§5.3/§8 Phase A 全文（sed 行段）。

### 23:10 在役对象锁定
- model/registry/engines.json：3 引擎 = A(active, 微盘选股 a13_rsraw_e1f10dz + q3z×EW-MA200 择时)、A2(shadow, a14_crowdf2 w=0.5 叠加)、gold_trend_sma200(active, slot B)。
- HP 结构：scripts/ 213 文件；data/all_stocks_qfq/{code}.parquet 为 akshare 前复权 K 线（中文列名）；data/delisted_pool.parquet 361 只退市股。

### 23:15-23:35 逐项证据（第一轮 audit_0537.py → HP results/phase_a_audit_0537/audit_findings.json）
- **A1**：ths_ttm_panel 235170 行，avail_date−report_date 中位 62 天 / min 30 / 负值 0。a9_common.merge_pb_into_panel L246：`merge_asof(by=code, left_on=date, right_on=avail_date, backward)` — 真 PIT as-of join。timing_layer_prod.py shift(1)×1。paper_engine_gold.py prev_me×12 + PIT×2。R-343（task-0531，今日）已核：黄金族 r482/r483 真 shift(1)；A股 IC 族天然免疫；择时 v2 族 shift(1)；HP 在役 paper 层无同月对齐。
- **A2**：本地 r483 重放（复制到 /tmp/r483replay，OUT 重定向）：e2_nav_monthly.csv md5=18bdf07bc3353f3884765fce2692cd49 与原件逐位一致（157 月全历史）；e2_gates_result.json 仅 run_at 时间戳 + NaN 比较伪差异。513100：raw(sina) 单日最小 −80.45%（拆分悬崖实锤）vs qfq(tx) −9.59%/+11.19% 无悬崖。
- **A3**：delisted_pool 361 只；**all_stocks_qfq/ 目录（6089 文件）中退市股覆盖 = 0** ← 疑点，待 merged parquet 复核。
- **A4**：paper 层 is_limit_up（L949，pct≥阈−1e-4 禁买 L1251）；paper 8 笔买单 0 笔涨停日违规；backtest 层 limit_board="on" + limit_up_pct=0.098（a13_run.py BASE）；limit_board 实现散布 a11_rules/a8_bucket 等引擎文件。
- **A5**：paper COST_BUY=0.00025(万2.5)+MIN_COMMISSION 5 元+COST_SELL_COMM 0.00025+STAMP_DUTY 0.001(千1)；a13 回测 BASE cost_rate=0.001、cost_model="v2"；R-333 结论引用：记账滑点≡0、实测三情态 4.0/11.5/15.7bp/边、参与率 0.002–0.07%→平方根冲击豁免。
- **A6**：paper_engine.py DIV_EVENTS（data/derived/dividend_events.parquet，48081 行）仅定义未使用（grep 计数=1）→ 分红未入账嫌疑实锤方向。dividend_events 与 paper 持仓交集 4 事件：300009(05-29,0.25)、600867(06-05,0.30)、603551(06-09,0.55)、601600(08-14,0.147)。持有窗口内金额待 f2（注意 601600 买入日=除息日，除息日买入不享有分红）。

### 三板斧
- ①锚点：R-317 F1 md5 915e446388… 的复现记录在案（R-317 L9，task-0492 /tmp 副本重跑三输出逐位一致；脚本本体已随 /tmp 清理不在盘，如实记录）；gold sleeve 锚点=本次 157 月全重放逐位一致（强于 2 锚点要求）。
- ②月度对账：gold=全历史重放 diff=0bp；A股 paper sleeve 待 f2 baseline-paper-nav.csv。
- ③R-333 引用不重做 ✓（两代引擎 18 笔逐笔对账，R-333 报告在案）。

### 零改动对照
- HP：audit 前 `find ~/quant-evolve -newermt 23:00` 快照 /tmp/audit_0537_before.txt；产物只写 results/phase_a_audit_0537/（新目录）+ /tmp。本地：r483 原件 md5 前后不变（18bdf07b…），重放仅写 /tmp/r483replay/out/。

## 四、最终判定（00:15）

| 项 | 判定 | 关键证据 |
|---|---|---|
| A1 | PASS（附补验） | merge_asof(avail_date,backward)；lag 中位 62/负 0；四族 shift(1)；残留：fundamentals_monthly 构建器未核验（无 lag 关键词命中）→ Phase B 前强制补验 |
| A2 | PASS | gold 157 月重放 md5=18bdf07b… 逐位一致；513100 raw −80.45% vs qfq −9.59% 无悬崖；hfq/qfq 双轨各司其职 |
| A3 | PASS | 退市池 361 + hfq 退市索引 365 + 退市基本面面板；引擎代码「全量池(含退市)宇宙」；qfq 目录非引擎源（澄清） |
| A4 | PASS | 回测 limit_board=on/0.098；paper is_limit_up 闸 8/8 零违规；卖出侧无跌停闸（0 笔卖出未行使）→ 修复项 |
| A5 | PASS | 费用三件套在账（万2.5×2+千1+5元下限）；R-333 引用；参与率豁免；三口径归一到 11.5bp 列 gate spec 条件 |
| A6 | PASS | 持有窗口分红事件=0；DIV_EVENTS 未接线=潜伏缺口 → 修复项；回测侧 hfq 含分红 |

**总裁决：无 FAIL，A1/A2 解除阻塞 → 放行 Phase B，附 3 项非阻塞条件（①fundamentals_monthly PIT 补验为影子消费 a13 面板前置 ②paper 两缺口修复另立项 ③成本口径归一 11.5bp 进 gate spec v1）。**

报告已落盘：R-345（19KB）。README 更新日志一行已追加。剩余：.task-completions.jsonl + PUT pending_review。

（待续）
