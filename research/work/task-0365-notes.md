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

## 2. 计算与结果记录（2026-08-18 12:4x-13:1x）

### 2.1 数据可得性结论（已实证）
- 大盘腿口径A（主用）：qfq 池每日 mcap 排序前 20% 等权——与微盘腿同一 lexsort 实现对称（rank≥0.8n），零边际数据成本，可得。幸存者偏差：qfq 池无退市股，但退市股几乎从不进前 20%，对大盘腿影响可忽略（披露）。
- 大盘腿口径B（对照）：HP `data/hs300_daily_20060101_20260808.parquet` 已在库，5003 行 2006-01-04~2026-08-07，与 breadth 同长度交易日，可得；成分股历史 hs300_constituents.csv 仅当前快照（无 PIT 历史）→ 成分加权腿不可 PIT 复现，用官方指数腿替代。
- 估值差信号：macro/index_valuation.parquet 仅 hs300 PE（2005-04~2026-08-14，5189 行，等权/中位数/加权三口径）；微盘域估值无源（fetch_log 实证：中证500 全源失败 akshare 接口漂移 index_value_hist_funddb 已移除）→ **估值差信号数据不完整，首阶段降级为候选项**（若立项需从 financial 数据 PIT 构造微盘池 PE 或另接源）。
- 外部 web 检索不可用（web_search 超时/无 provider），框架映射章节改为内部知识+R-218/R-227/R-230 体系内映射，无外部引用，报告中披露。

### 2.2 第一轮计算结果（首轮日志，重跑确认中）
- Mmicro 交叉验证 vs E1 signal_series：n=5003，corr=0.9999992，mean|Δret|=9.2e-06，final_ratio 0.9955 → 微盘腿口径与 E1 逐位同构 PASS。
- 腿统计（2006-01~2026-08，等权日频）：
  - Mmicro：年化 15.81% / MDD −71.45% / Calmar 0.221
  - Mlarge_top20（市值前 20% 等权）：年化 26.18% / MDD −69.17% / Calmar 0.378 ← 前段历史大盘腿更强（2006-2010 大盘牛市）；注意此“大盘池”含中盘（5400 只中前 20%≈1080 只）
  - hs300 指数：年化 8.15% / MDD −72.3%（2008 年 −72.7% 真实存在）/ Calmar 0.113
- 腿日收益相关：micro↔large 0.864，large↔hs300 0.937，micro↔hs300 0.728。
- 信号 episode 首轮数字（hit15=切腿后 15 日 RS 相对收益方向正确率）：
  - ma20：large 238 次 55.0% / large 状态占 53.9%（过于频繁，年均 ~12 次切换）
  - ma60：large 120 次 59.2% / 占 57.9%
  - mom60：large 116 次 57.8% / 占 60.3%
  - ma5_20：large 135 次 59.3% / 占 53.1%
  - 切回 micro 方向 hit15 仅 46~52%（近似抛硬币）
- 首轮 B5 命名窗口段有 pandas 索引 bug（iloc[mask][-1]），已修复加重跑；Part A 加缓存防重算。
