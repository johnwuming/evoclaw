# task-0341 过程笔记：P0 候选因子动态有效性核验（滚动IC + 衰减/涌现分类）

> 边查边写。每完成一个信息点立即追加。恢复点=本文件。

## 环境与数据来源（阶段0）
- 2026-08-17 10:2x：HP SSH（10.12.192.174）全部端口 Connection refused（ping 通）——与 task-0337 记录的 fail2ban/MaxStartups 限流一致。多次重试仍 refused。
- **处置**：改用 VPS 本地副本分析（IC 数据与 catalog v3 均已同步到 VPS），结论不受影响；HP 侧同步待 SSH 恢复后补（A7/A7b 进程不受影响，本任务无 HP 进程操作）。
- 本地数据源（VPS）：
  - `shared/results/04-投资研究/factor_ic_monthly.csv`：ym 2006-01 ~ 2026-07，107 因子列（catalog v3 全集），月频 W1 口径
  - `shared/results/04-投资研究/factor_catalog_v3.json`：107 因子元数据（含全周期 mean_ic / icir / half_life_months）
  - `shared/results/work/task-0337-microcap-factor-survey.md`（= evolving-claw-repo 副本）15 因子清单
- Python：/opt/finworker/bin/python（pandas 3.0.5 / numpy 2.5.2）

## 15 因子 → catalog v3 列名映射（阶段0 完成）
- P0-1 低成交额/低换手族 (F1+F14) → avg_amount_20d, turnover_rate, turnover_rate_60d, log_amount_60d（IC 面板可算）
- P0-2 Amihud (F2) → amihud_illiquidity, amihud_60d（可算）
- P0-3 日历效应 (F3) → 非横截面 IC 因子（择时层/时间序列机制），IC 面板无月哑变量 → 数据缺口，另以定性+分段月收益处理
- P0-4 涨停交易层 (F4) → IC 面板无涨停构造列（需 kline 自算一字板/涨停计数）→ 数据缺口，proxy 待定
- P0-5 次新剔除 (F5) → IC 面板无上市天数列 → 数据缺口
- P0-6 换手波动率 (F6) → amount_cv, amount_cv_60d, turnover_std_20d（可算）
- P1 F7 低波 → volatility_20d, volatility_60d, idiosyncratic_vol, downside_vol_20d
- P1 F13 股息（水平）→ div_yield_ttm
- P2 F14 壳价值 → shell_value_proxy, mktcap_rank_pct, microcap_liq_interact
- P1 F9 商誉 / F10 业绩预告 / F11 激励回购 / P2 F8 股东户数 / F12 北向两融 → IC 面板无列（需新数据）→ 数据缺口

## 阶段1 动态IC计算
（进行中）

### 核验补充（10:3x）
- 符号约定：CSV 存原始 IC（正=因子值高→未来收益高）；catalog mean_ic 已按 direction 调整。有效IC = raw × (dir=='neg'?-1:1)。已用 market_cap_log/avg_amount_20d/amihud/cv/div_yield 交叉验证一致。
- 本地 IC 面板 247 月（2006-01~2026-07），107 因子列，W1 月频口径。
- HP SSH 仍 refused（fail2ban），但 **HP HTTP API :8060 + X-API-Key 可用**（key 在 /root/.openclaw/workspace-quant/scripts/.hp-api-key）——A7 结果查证走 API；本任务 IC 计算用本地副本（同源）。
- A7 结果：HP results/ 尚无 a7_* 产物（a7_runner 9 候选 v5a-v5i 于 ~11:20 启动，仍在跑）→ 阶段2 先做独立画像，衔接标注 pending。

### 可算因子 vs 数据缺口（阶段0 定稿）
- **IC 面板可算**：P0-1 低成交额/低换手族（avg_amount_20d/turnover_rate/turnover_rate_60d/log_amount_60d）；P0-2 Amihud（amihud_illiquidity/amihud_60d）；P0-6 换手CV（amount_cv/amount_cv_60d/turnover_std_20d）；P1 F7 低波（volatility_20d/60d/idiosyncratic_vol/downside_vol_20d）；P1 F13 股息水平（div_yield_ttm）；P2 F14 壳价值（shell_value_proxy/mktcap_rank_pct/microcap_liq_interact）
- **数据缺口（IC 不适用/无列）**：P0-3 日历效应（择时层，非横截面IC）；P0-4 涨停交易层（无构造列，A7 回测归因）；P0-5 次新剔除（无上市天数列，A7 回测归因）；P1 F9 商誉/F10 业绩预告/F11 激励回购/P2 F8 股东户数/F12 北向两融（需新数据）→ 这些以 A7 回测替代动态评估，IC 表标 N/A
