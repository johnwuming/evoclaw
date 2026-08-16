# Q4a 退市池 hfq 覆盖补齐缺口报告（task-0294）

日期：2026-08-16 ｜ 执行：task-0294（Q4a）｜ 项目：~/quant-evolve

## 结论速览

| 指标 | 补齐前 | 补齐后 |
|------|--------|--------|
| 退市池（parquet 361 口径）hfq 覆盖 | 297/361 = 82.3% | **360/361 = 99.7%** |
| data/stocks_hfq/ 文件数 | 5506 | 5569 |
| 本任务补采 | — | **63 只**（成功落盘） |
| 不可得 | — | **1 只**（900951，见下） |

## 缺口原因（64 只构成）

| 类别 | 数量 | 原因 | 处置 |
|------|------|------|------|
| A类 000/600 沪深A | 36 | 原脚本 collect_delisted_hfq.py 按设计跳过「退市日<2006-01-01」（对2006起回测无用）；全部为 1999-2005 退市的老股 | baostock 乘法 hfq 全历史补采，36/36 成功 |
| B类 200/900 B股 | 28 | baostock 完全无 B 股数据（K线/因子/基础信息全空）；且其中多数不在原脚本扫描的 delisted_pool.csv（337）内 | 腾讯 ifzq.gtimg.cn hfqday 分页拉取，27/28 成功；900951 无 hfq 档案 |

## 数据源与口径（⚠️ 回测使用者必读）

- **A类（36 只）**：baostock `query_history_k_data_plus(adjustflag="3")` × `query_adjust_factor` 后复权因子（乘法），与现有库 collect_delisted_hfq.py / collect_hfq.py **完全同口径**。
- **B类（27 只）**：腾讯 `web.ifzq.gtimg.cn/appstock/app/fqkline/get` 的 hfqday 序列。baostock 无 B 股、东财接口对本机 RemoteDisconnected、新浪/网易源已废，TX 为唯一可用全历史源。
  - 口径注意：TX 后复权的**因子基准与 baostock 不一致**（跨源绝对价格不可比）；同股时序收益率/波动计算可用。
  - index 中标记 `adjust_basis: "tx_hfq"`，可程序化区分。
  - TX 不提供换手率：B 股 `turn` 列全 NaN，`amount` 部分为 NaN。若 Q4b 因子用到 turn，B 股样本会缺失该因子输入。

## 不可得清单（1 只）

| code | 名称 | 原因 |
|------|------|------|
| 900951 | 退市大化 | TX raw 有 5390 行（1997-10-21~2020-08-20）但 hfqday/qfqday 均空——源无该股除权档案，无法复权；baostock 无 B 股。该股 2020-08 私有化退市。若 Q4b 需要，需人工用 raw+分红公告自建因子（不建议） |

## 质量校验

1. **格式一致性**：抽验 000003/600625/900949/200771 —— 9 列（date/code/open/high/low/close/volume/amount/turn）、dtypes、`{code}_daily_hfq.parquet` 命名与现有库完全一致 ✅
2. **行数一致性**：63/63 只 index 记录 rows 与 parquet 实际行数一致 ✅
3. **幂等性**：脚本按 index status=ok + 文件存在跳过；append_stock 语义为读旧→concat→按date去重→排序→原子写，重跑不重复写坏数据 ✅（实际重跑 3 次，A类 36 全部 skip，无重复行）
4. **边界核对**：各股 last 日期 ≤ 退市日（B 股多为最后交易日前数日，符合 B 股终止上市惯例）✅
5. 未触碰 qfq / fin_deep / audit_lock 相关目录与文件 ✅

## 交付物

- 数据：data/stocks_hfq/ 新增 63 个 parquet
- 索引：data/stocks_hfq_delisted_index.json（q4a 记录含 note="q4a补采…"，B 股带 adjust_basis 字段）
- 脚本：scripts/collect_q4a_gap64.py（可重跑，幂等）
- 过程笔记：HP /tmp/q4a-notes.md（逐步探测/决策记录）
- 缺口清单：HP /tmp/q4a_missing64.csv

## 对 Q4b 的提示

- B 股样本（27 只）turn 因子不可得；建议 Q4b 全量池基线重跑时对因子输入做按列缺失容忍或在池定义中说明。
- A类 36 只全部 2006 前退市，对 2006 起回测是「进池即无数据」的样本；覆盖补齐只为口径完整（100% 可得覆盖），不改变回测样本量。
- 覆盖率以 delisted_pool.parquet 361 为准；delisted_pool.csv（337）为旧常量表，勿混用。
