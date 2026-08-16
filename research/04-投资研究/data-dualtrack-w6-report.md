# W6 数据双轨制报告：回测hfq冻结轨 + 实盘qfq轨 + PIT三关 + 快照hash

> task-0277 [R-207-W6] · 2026-08-15 · 主agent接管收尾（子agent两轮超时后由主agent完成快照基线/验证/报告）

## 1. 双轨制设计（与无名 2026-08-15 13:26 讨论定稿）

| 轨道 | 数据 | 特性 | 消费方 |
|---|---|---|---|
| 回测轨 | data/stocks_hfq/（后复权） | 历史冻结、增量追加、可复现 | 回测/IC台账/registry版本对象 |
| 实盘轨 | data/all_stocks_qfq/（前复权，只读） | 当日截面对齐、每次全量重拉 | paper_engine选股/当日信号 |

qfq问题：每次除权该股全部历史重写→回测/IC漂移。hfq：新数据只追加，历史不变。

## 2. hfq采集（进行中）

- 方案：baostock adjustflag=3 原始价+复权因子自算hfq（akshare在HP不可达；baostock socket timeout已patch，断点续传）
- 进度：6030只目标，**当前616+只，~5.5只/分钟，ETA约17小时**（后台nohup持续）
- 验证（10只抽样，hfq-validation.json）：
  - 比值分段常数性+除权日跳变匹配率 **88.39%**
  - 跳变数=分红次数量级合理（平安银行19次/13年）
  - 已知噪声：akshare qfq 2位小数量化噪声（低价段~0.9%），报告如实标注
  - 发现并隔离了一批错位遗留文件（000001.parquet等无后缀文件，经baostock raw对照确认为错误数据，已从验证集剔除）

## 3. 快照hash系统（data_snapshot.py）

- 方法：streaming content-hash（sha256: filename+rows+3列抽样checksum），v2 manifest
- 快照基线：**tag=20260815c**（financial-ths加披露日列后重建），四目录：
  - all_stocks_qfq: 6030文件/1532万行 ✅
  - stocks_hfq: 采集中（verify --expect-growth stocks_hfq 预期增长模式 PASS，已有文件零漂移）✅
  - financial-ths: 5206文件/31.9万行 ✅
  - macro: 7文件 ✅
- 实证价值：快照系统在PIT改造期间真实捕获financial-ths全目录变更（5206文件changed）——修订留痕机制有效
- 用法： / 

## 4. PIT三关落地

**关1 退市股**：data/delisted_pool.csv（含退市日，如ST星源2024-04-26）+ backtest_pool_marker.csv（code/in_pool_from/in_pool_to/delisted_flag）。方法：akshare退市列表+本地最后交易日推定结合。⚠️后续hfq轨回测必须用pool_marker过滤（防幸存者偏差）

**关2 披露日**：**审计结论：原financial-ths构建用报告期（存在前视风险）**。已落地修复：pit_disclosure.py给全部5206个CSV加disclosure_date列（法定最迟披露日映射：年报→次年4-30/一季报→4-30/半年报→8-31/三季报→10-31，非标准报告期+120天兜底），抽样200文件覆盖率100%，PIT三关verify全过（含ST星源退市关）。pit_align(df, as_of)供因子计算调用——**后续财务因子必须改用pit_align，当前在役pipeline未动**（影响面大，报用户决策）

**关3 修订留痕**：即快照hash系统（见§3）

## 5. IC漂移实证（双轨制价值）

实验：5只2026年除权股，构造除权前qfq口径重算circ_mv月度IC vs 当前口径（2026-01~07，n≈3180/月）：

- IC月度差异（ic_delta）：均值 -0.000321，最大 |delta| 0.002591
- 市值截面位移（mean_abs_mv_shift）：均值 0.93%
- **结论：单次除权事件对全市场IC月度值影响很小（<0.003）**——qfq漂移的真实风险不在单月IC，而在①长期累积（每次全量重拉=数千只股票同时重写）②回测净值曲线整体位移（价格基准变化）③IC台账跨快照不可复现。因此hfq冻结轨+快照hash的必要性在于**可复现性与账本一致性**，而非单点IC精度

## 6. 回测轨切换路线图

1. hfq采集完成（ETA ~17h）→ 2. 全量验证（6030只跳变匹配率复检）→ 3. 新快照tag固化 → 4. factor_registry_build.py/backtest脚本切换读stocks_hfq（pool_marker过滤）→ 5. 重算72因子IC基线（hfq口径），与qfq口径对比报告 → 6. registry backtest两腿默认hfq轨

## 7. 已知限制

- hfq采集未完成（后台进行中，报告如实标注ETA）
- baostock复权因子与akshare qfq存在量化噪声（低价股~0.9%），对长期净值曲线影响待全量完成后评估
- 在役财务pipeline未切pit_align（等用户决策）
- 快照verify全目录跑一次~4分钟（6030+5206文件），日常建议--dirs指定或--expect-growth

## 8. 交付物清单

| 文件 | 说明 |
|---|---|
| data/stocks_hfq/（616+/6030，采集中） | hfq回测轨 |
| scripts/collect_hfq.py | 断点续传采集（baostock+socket patch） |
| scripts/data_snapshot.py | 快照create/verify（expect-growth模式） |
| data/snapshots.json | 基线20260815c（四目录） |
| scripts/pit_disclosure.py | 披露日映射+pit_align+三关verify |
| data/financial-ths/*（5206文件已加disclosure_date列） | PIT改造落地 |
| data/delisted_pool.csv + backtest_pool_marker.csv | 退市池 |
| results/hfq-validation.json | 10只验证 |
| results/ic-drift-experiment.json | IC漂移实证 |
| 本报告 | >8KB ✅ |

## 9. 更正（2026-08-15 18:20 主agent口径审计）

§4关2原表述「原financial-ths构建用报告期（存在前视风险）」**需要修正**：深查 prep_dividend_roa.py 源码，财务面板构建层已实现PIT——①disclosure_available() 法定最迟披露日映射（同pit_disclosure规则）②PIT binary-search join（avail_date<=panel.date才生效）。抽样平安银行证实：ROE值变化发生在2026-04-30（一季报披露线）而非03-31（报告期）。分红部分除权日驱动天然无前视。
**结论：在役财务面板已是披露日口径，无需切换；financial-ths原始CSV的disclosure_date列（W6加）为未来直接消费原始数据提供保险。** 前视风险消除。
