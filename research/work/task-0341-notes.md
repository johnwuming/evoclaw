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

## 阶段1 动态IC计算（完成，10:3x-10:4x）

### 计算产物（本地 + 已推 HP results/）
- a7c-dynamic-ic-table.{md,csv,json}：17 行动态 IC 全表（全周期/近24m/近36m/2018-2021 vs 2022-2026/半衰期/画像）
- a7c-iteration-report.md（5.5KB）、a7c-dynamic-ic-report.md（7KB）、a7c-rolling-ic-series.json
- HP results/ 共 6 个 a7c 文件（COUNT=6），验收 ✓

### P0×6 结论（有效IC=raw×方向）
- **P0-1 低成交额族：近期仍有效**。avg_amount_20d 全期 -0.103/-0.664、近24m -0.104/-0.561、2022-26 -0.110/-0.686（近端更强）；log_amount_60d 同理。换手率版（turnover_rate/60d）同号但近24m 走弱（-0.049~-0.061/-0.25~-0.30）→ 衰减中。
- **P0-2 Amihud：近期仍有效**。amihud 20d 全期 0.076/0.483、近24m 0.076/0.483、2022-26 0.078/0.481。但 A7 微盘预检 +0.0039 近零 → 全市场强、微盘增量弱。
- **P0-6 换手CV：近期仍有效（近端走强）**。amount_cv 近24m ICIR -1.10（全表最强），60d 版近端增强。A7 微盘预检方向反转（+0.189）→ 需独立回测裁决。
- **P0-3 日历 / P0-4 涨停 / P0-5 次新：数据缺口**（非横截面IC），A7 回测归因，IC 表标 N/A。
- P1 F7 低波族全组衰减中；P1 F13 股息水平版近24m 已反转（-0.005/-0.032）→ 已失效；P2 F14 壳价值族稳定（近24m 0.45-0.48）但本质市值代理，不单独推进。

## 阶段2 与 A7 衔接（完成）
- A7 locked（≤2024-06）已出：基线 a5_v4b_mve1 12.42%/-28.99%/0.8401；v5a_amt37 14.42%/-30.76%/0.9325；v5b_amt55 14.52%/-30.76%/0.9494（最优）；v5c_amt73 14.25%/-30.65%/0.9427；v5d_amh55 13.18%/-31.03%/0.8606（最弱）。
- 对齐：低成交额族增量（v5a/b/c +1.8~2.1pp）与 A7c“近期仍有效”一致 → 推进；Amihud（v5d +0.8pp）增量弱 → 降优先级；amount_cv 未含在 v5 系，建议下批补测。
- 幸存者偏差警示：全市场 W1 IC 强信号在微盘宇宙内方向可能反转（A7 预检 amt20 +0.106 / amt_cv20 +0.189），最终以 A7/A7b 微盘 locked 净增量为准。

## 阶段3 交付（完成）
- 全部产出已推 HP results/a7c_*（6 文件）；本笔记为 VPS 侧收口副本。
- 完成回报将写入 scripts/.task-completions.jsonl。

## 半衰期（catalog v3 多期拟合）
- 短半衰 2-4m：amount_cv/turnover/波动族 → 换手波动类高频敏感
- 长半衰 11-12m：amihud/log_amount_60d/股息 → 非流动性/成交额水平类慢变量

### 核验补充（10:3x）
- 符号约定：CSV 存原始 IC（正=因子值高→未来收益高）；catalog mean_ic 已按 direction 调整。有效IC = raw × (dir=='neg'?-1:1)。已用 market_cap_log/avg_amount_20d/amihud/cv/div_yield 交叉验证一致。
- 本地 IC 面板 247 月（2006-01~2026-07），107 因子列，W1 月频口径。
- HP SSH 仍 refused（fail2ban），但 **HP HTTP API :8060 + X-API-Key 可用**（key 在 /root/.openclaw/workspace-quant/scripts/.hp-api-key）——A7 结果查证走 API；本任务 IC 计算用本地副本（同源）。
- A7 结果：HP results/ 尚无 a7_* 产物（a7_runner 9 候选 v5a-v5i 于 ~11:20 启动，仍在跑）→ 阶段2 先做独立画像，衔接标注 pending。

### 可算因子 vs 数据缺口（阶段0 定稿）
- **IC 面板可算**：P0-1 低成交额/低换手族（avg_amount_20d/turnover_rate/turnover_rate_60d/log_amount_60d）；P0-2 Amihud（amihud_illiquidity/amihud_60d）；P0-6 换手CV（amount_cv/amount_cv_60d/turnover_std_20d）；P1 F7 低波（volatility_20d/60d/idiosyncratic_vol/downside_vol_20d）；P1 F13 股息水平（div_yield_ttm）；P2 F14 壳价值（shell_value_proxy/mktcap_rank_pct/microcap_liq_interact）
- **数据缺口（IC 不适用/无列）**：P0-3 日历效应（择时层，非横截面IC）；P0-4 涨停交易层（无构造列，A7 回测归因）；P0-5 次新剔除（无上市天数列，A7 回测归因）；P1 F9 商誉/F10 业绩预告/F11 激励回购/P2 F8 股东户数/F12 北向两融（需新数据）→ 这些以 A7 回测替代动态评估，IC 表标 N/A
