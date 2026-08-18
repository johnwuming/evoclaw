# task-0365 过程笔记：大小盘轮动可行性调研（产出 R-236）

任务：task-0365。调研三块：框架映射 / 数据可得性（大盘腿两种口径）/ 最小实证（size spread 信号画像）。结论须回答立项与否（A12 批次设计概要）。
范围约束：不涉及期权。

## 0. 前置输入摘要（已读，2026-08-18 12:3x）

- R-230：五维信号映射表、回测口径（locked 2006-01~2024-06 / holdout 2024-07~2026-08）、全量池 OOM 警告（流式必须）。
- R-231（E1 方法论模板）：
  - 微盘池口径 = collect_crowding.py：每日全市场按总市值 mcap=close×outstanding_share 排序后 20%（qfq 池，numpy lexsort 流式）；
  - Mmicro 微盘等权年化 15.72%/MDD −71.5%；M 全池等权 22.07%/−71.8%，两者日收益相关 0.96；
  - 事件口径：episode=连续触发日段，事件日=段首日，fwd15=载体(t+15)/载体(t)−1；
  - 信号触发<5 次不上岗；分段披露 2006-2015 / 2016-2026。
  - 已知微盘专属崩塌段：2024-02-05 量化踩踏（全家族择时信号漏报，M dd −31.6%）；2026 流动性枯竭段（任务书点名）。
- task-0361-notes：
  - 执行环境偏离先例：HP 内存耗尽时数据只读副本 rsync 至 VPS 计算、产物回写 HP results/；
  - VPS 计算环境：pandas 3.0.5 / numpy 2.5.2 / pyarrow 25.0.1（/opt/finworker/bin/python 同版本，已验证）；
  - VPS /root/tv2data/ 现仅剩 out/（E1 产物 signal_series.parquet 712KB 等 5 件）；原始 qfq 池已被清理，需重新同步。

## 1. 环境与数据核查（2026-08-18 12:3x-12:4x）

### 1.1 HP 状态（12:35 实查）
- 内存恢复：MemAvailable 10913MB（上次 57MB）——106 个 idle openclaw-node 已不在。swap 用 444MB。
- HP results/timing_v2/ 完整（E1 产物 7 件，含 tv2_compute_v2.py 17274B 计算脚本可复用）。
- data/all_stocks_qfq/ 1.1G（5,448 文件）。
- 按任务书：计算仍在 VPS（/opt/finworker/bin/python），数据只读副本重新 rsync。

### 1.2 VPS 侧
- /opt/finworker/bin/python：pandas 3.0.5 / numpy 2.5.2 / pyarrow 25.0.1 ✅。
- /root/tv2data/out/signal_series.parquet（5003 行×22 列，M/Mmicro/breadth 等）可直接复用作 Mmicro 交叉验证。

（待续：指数数据可得性、qfq 同步、大盘腿构建）
