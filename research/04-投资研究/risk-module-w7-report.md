# R-207-W7 风控模块交付报告：退出纪律代码化 + 微盘拥挤度采集 + 容量估算

> **任务**：task-0276 / W7
> **日期**：2026-08-15
> **主机**：HP 10.12.192.174 `~/quant-evolve`
> **验收对象**：`config/risk-charter.json`、`scripts/risk_patrol.py`、`scripts/collect_crowding.py`、`results/risk-status.json`、`results/crowding-indicators.json`、`results/crowding_history.csv`、`results/risk-events.jsonl`、本报告
> **设计依据**：R-207 产品开发说明书（第二部分 C1/C2、第三部分 §3.2 risk_patrol）、R-204 行业标杆调研（维度四退出纪律 / 维度八微盘特异性风控）

---

## 1. 模块总览

本模块把 R-204 提出的**"退出纪律事前写死 + 微盘拥挤度监控 + 容量估算"**三条护栏落地为可每日/每周自动运行的代码，全部产出真实计算数据（非编造）：

| 组件 | 文件 | 运行频率 | 消费方 |
|---|---|---|---|
| 退出纪律章程 | `config/risk-charter.json` | 只读（改须 decision-log） | risk_patrol、页面 M4.8 |
| 退出纪律巡检 | `scripts/risk_patrol.py` | 每日 16:45（周一~五，cron） | M4.8、告警链路 |
| 微盘拥挤度+容量 | `scripts/collect_crowding.py` | 每周日 07:00（cron） | M4.7、M4.8 联动 |
| 状态快照 | `results/risk-status.json` | 每次巡检更新 | M4.8 |
| 拥挤度指标 | `results/crowding-indicators.json` + `crowding_history.csv` | 每周更新 | M4.7 |
| 触发事件/告警 | `results/risk-events.jsonl` / `results/notifications-queue.jsonl` | 触发即 append | 页面 + 微信链路 |

**当前整体结论（2026-08-07 数据）**：
- **退出纪律 = 绿**（回撤 -9.0% vs 25%/35% 阈值；6m 超额 -3.4% vs -10%；12m 超额 -4.4% vs -15%），实盘 Sharpe 因 paper 仅 2 点数据标记 grey/insufficient。
- **微盘拥挤度 = 红**（唯一红项：小盘超额衰减 60 日斜率 -0.44%/日，t=-12.5，处于历史 5.5% 分位——微盘相对大盘持续快速走弱）。
- **容量**：当前 11 票策略容量约 **1.37 亿 / 2.73 亿 / 4.10 亿元**（保守/中性/乐观），对个人资金完全不构成约束，瓶颈票为奥普科技(603551)。

---

## 2. 退出纪律章程 `config/risk-charter.json`

### 2.1 Schema 与规则

```json
{
  "charter_version": "1.0",
  "effective_date": "2026-08-15",
  "benchmark": "hs300",
  "rules": {
    "drawdown_circuit_breaker": {
      "level1_cut_half": {"metric": "nav_drawdown_vs_hwm", "threshold": 0.25, "action": "降仓至50%"},
      "level2_stop":       {"metric": "nav_drawdown_vs_hwm", "threshold": 0.35, "action": "清仓复盘，人工重启"}
    },
    "underperform_discipline": {
      "watch":      {"metric": "rolling_6m_excess_vs_benchmark",  "threshold": -0.10, "action": "进入观察，暂停模型升级"},
      "downweight": {"metric": "rolling_12m_excess_vs_benchmark", "threshold": -0.15, "action": "降仓至70%"}
    },
    "live_vs_backtest": {"metric": "live_sharpe_vs_backtest", "ratio_threshold": 0.5, "window_months": 6, "action": "策略失效review"}
  },
  "amendment_rule": "阈值修改必须走decision-log并通知用户，禁止静默修改"
}
```
（文件另含 `rule_basis` 段逐条记录阈值依据与可调区间，`adjustable_note` 声明"初值、可调、改必留痕"。）

### 2.2 各阈值依据（R-204 对齐）

| 规则 | 初值 | 依据 | 可调区间 |
|---|---|---|---|
| 回撤降仓线 level1 | 25% | R-204 维度四"触及历史最大回撤 1~1.5 倍即降仓"；本策略 20 年历史最大回撤 **-36.85%**（2015-07-08），取 0.7×极值作提前介入线 | 20%~30% |
| 回撤熔断线 level2 | 35% | R-204"净值 -15%~-20% 停止策略 + 复盘重启"；对齐本策略历史极值 -36.85% 取 0.95× | 30%~40% |
| 6m 超额观察线 | -10% | R-204"连续 N 月跑输基准→观察/降权"；策略 20 年年化超额约 +6.7%，6 个月跑输 -10%（年化约 -20%）属显著反向 | -8%~-12% |
| 12m 超额降仓线 | -15% | 一年超额被完全吞掉并转负→降仓复核 | -12%~-18% |
| live/backtest Sharpe 比 | 0.5 | R-204"live Sharpe < 回测 50% 且持续 2 季度→失效" | 0.4~0.6 |

> **基准说明**：主基准 hs300（数据齐全、与 R-207 M3.3 分年度基准一致）；同时用自算微盘等权指数做**交叉验证**（见 §5，交叉值仅参考不改变主判定）。

---

## 3. 退出纪律巡检 `scripts/risk_patrol.py`

### 3.1 设计
- **主净值序列**：`results/i3_abs_s1_nav.csv`（2006-01-04 ~ 2026-08-07，5003 点）——与当前生效模型 **V2_d25_n30_p10 + i4_q3z 择时**同参数的策略 track record；paper 实盘 `baseline-paper-nav.csv` 刚启动（仅 2 点），故回撤/超额类规则主序列用 track record，**paper 积累 ≥20 点后自动切换实盘主判**（代码已写死该切换条件并注明）。
- **颜色/余量算法**（`color_from_current`）：红色=已触发；黄色=当前值已进入阈值的 50%~100% 区间（距触发 1 倍内）；绿色=安全。余量 margin=(阈值-|当前|)/阈值，正=安全，0=触发。live_vs_backtest 为下限型（越小越危险），paper 数据不足时标 **grey/insufficient**（不误报）。
- **触发链路**：任一红 → append `risk-events.jsonl`（时间/规则/当前值/阈值/建议动作）+ append `notifications-queue.jsonl`（HP 侧，auto_sync 带回 VPS 转 .task-notifications.jsonl）。
- **回放演练**：`--replay` 在 track record 上重放 2015 区间，验证熔断全链路（§6）。

### 3.2 当前实测值（risk-status.json，2026-08-07）

| 规则 | 当前值 | 阈值 | 余量 | 颜色 | 判定 |
|---|---|---|---|---|---|
| drawdown_circuit_breaker.level1 | -9.05% | 25% | 0.64 | 🟢 green | 安全 |
| drawdown_circuit_breaker.level2 | -9.05% | 35% | 0.74 | 🟢 green | 安全 |
| underperform_discipline.watch | -3.44% (6m, vs hs300) | -10% | 0.66 | 🟢 green | 安全 |
| underperform_discipline.downweight | -4.41% (12m, vs hs300) | -15% | 0.71 | 🟢 green | 安全 |
| live_vs_backtest | paper 仅 2 点 | 0.5 | — | ⚪ grey | insufficient |
| 交叉验证 vs 微盘等权 | watch +22.0% / downweight +25.8% | — | — | 🟢 | 策略相对纯微盘大幅超额 |

**解读**：策略当前处 HWM 下方 -9% 回撤（2026 年内 6m/12m 跑输 hs300 但幅度温和），且相对"纯微盘等权指数"大幅正超额（+22%/+25.8%）——即最近弱的是**垃圾微盘**，不是本策略的**质量小盘**。这与拥挤度指标一致（§5）。

---

## 4. 微盘拥挤度采集 `scripts/collect_crowding.py`

### 4.1 数据源与计算式（akshare 不可达 → 全本地自算）
> akshare 实测连接失败（ConnectionError，与已知"K线停更事件"一致），四指标全部从本地 `data/all_stocks_qfq/*_daily_qfq.parquet` 自算；面板 5205 只、2018-06 起 870 万行，分批读 + numpy 紧凑存储（峰值内存 <1.5GB，满足 15GB 约束）。

| # | 指标 | 数据源 | 计算式 |
|---|---|---|---|
| 1 | 微盘成交占比 | 全市场 daily_qfq | 每日按**总市值=收盘×outstanding_share** 排序取后 20% 组，组内成交额合计 ÷ 全 A 成交额；输出日度 + 月度均值 + 滚动 20 日均值 |
| 2 | 微盘换手率分位 | 同上（turnover 列） | 微盘组日均换手率的 **60 日滚动历史分位**（2019 以来），当前值在近 60 日内的百分位 |
| 3 | 小盘超额衰减 | 微盘等权指数 vs hs300 | 微盘等权日收益 − hs300 日收益 → 60 日累计对数超额 → 对时间做 OLS，取**斜率**与 **t 统计量**；负且 t<-2=撤退前兆 |
| 4 | 雪球敲入距离代理 | zz500（中证500） | 现价 / (0.8×12 个月前点位) − 1 = 距敲入线空间%；中证1000 本地数据陈旧（止于 2016）→ **unavailable**，替代方案：用中证500 作挂钩标的代理（中证500 本就是最主流雪球挂钩指数） |

**微盘定义**：每日全市场按总市值排序后 20%（≈中证2000/万得微盘的自算替代）。⚠️ 已知局限：本地池无退市股（幸存者偏差，微盘流动性或略高估）；outstanding_share 为当前股本快照（历史市值近似），对拥挤度趋势监控影响可控——报告 §5 已用 2024-01 危机做历史校验。

### 4.2 当前实测值（2026-08-07）与颜色判定

| 指标 | 最新值 | 判定 | 颜色 |
|---|---|---|---|
| 微盘成交占比 | **2.53%**（月均 2.78%，60d 分位 48.3） | <90 分位 | 🟢 green |
| 微盘换手率 60d 分位 | **46.7**（百分位） | <90 | 🟢 green |
| 小盘超额衰减斜率 | **-0.00442/日（t=-12.5，历史 5.5% 分位）** | 负且显著 | 🔴 red |
| 雪球敲入距离（中证500） | **+58.5%**（距 0.8×12 个月前点位 58% 空间） | 无敲入压力 | 🟢 green |

**overall_flag = 🔴 red**（excess_decay 单一红项拉红）。

### 4.3 历史校验（指标有效性实证）
- **2024-01 微盘危机**：指标准确捕捉——2024-01~02 微盘成交占比冲至 6.1%~9.0%（月均 7.8% vs 危机前 7.1%），超额斜率最深 -0.75%/日、t=-5.2。说明该指标对已知踩踏事件响应正确。
- **结构性趋势**：微盘成交占比从 2019 年约 9% 一路降至 2026 年约 2.4%；自建微盘等权指数 730（2019-01）→ 606（2026-08），7.5 年 -17%（2020-12 峰值 990 → 2024-06 谷底 538 → 现 606）。微盘整体长期跑输且流动性持续萎缩。

---

## 5. 容量估算（并入 collect_crowding）

**方法**：单日可买量 = ADV20（20 日成交额均值）× 参与率（5%/10%/15%）→ 策略容量 = 可买量 ÷ 该票持仓权重 → 取 11 票瓶颈（min）。

**结果**（ADV 基于 2026-08-07 前 20 交易日，持仓权重来自 baseline-paper-portfolio.json）：

| 档位 | 参与率 | 策略容量（瓶颈） | 11 票均值容量 |
|---|---|---|---|
| 保守 | 5% | **1.37 亿元** | 2.55 亿 |
| 中性 | 10% | **2.73 亿元** | 5.10 亿 |
| 乐观 | 15% | **4.10 亿元** | 7.65 亿 |

- **瓶颈票 = 奥普科技(603551)**：ADV20 ≈ 2293 万/日，权重 8.39% → 中性容量 2732 万。
- 其余票容量充足（最宽裕为中国铝业 31 亿、分众传媒 11 亿，两者本非微盘）。
- **结论**：对当前 10 万级模拟/个人资金，容量完全不构成约束；但若资金放大至亿元级，奥普科技等小票会首先卡容量，需届时做分批建仓或换票处理。每股明细见 crowding-indicators.json `capacity.per_stock`（code/name/weight/ADV20/三档容量）。

---

## 6. 触发演练记录（risk-events.jsonl，mode=replay）

用 2015 年历史区间在 track record 净值上回放退出纪律，全链路（事件+告警）实测通过：

| 触发日期 | 规则 | 回放值 | 阈值 | 建议动作 |
|---|---|---|---|---|
| 2015-07-03 | level1_cut_half | 回撤 -27.6% | 25% | 降仓至50% |
| 2015-07-08 | level2_stop | 回撤 -36.9% | 35% | 清仓复盘，人工重启 |
| 2015-01-05 | underperform_discipline.downweight | 12m 超额 -18.3% | -15% | 降仓至70% |

- 演练事件写 `risk-events.jsonl`（mode=replay，标注"非当前实时触发"）；level1/level2 同时走通告警链路 → `notifications-queue.jsonl`（标题含 [演练] 标记，避免与真实告警混淆）。
- **当前实时状态无触发**（整体绿/拥挤度红），故 live 模式未产生真实告警（不误报）。

---

## 7. Cron 部署（仅追加，已备份）

```
# 备份：~/crontab.backup.20260815.txt（原 13 行）
45 16 * * 1-5  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/risk_patrol.py >> logs/risk_patrol.log 2>&1
0  7  * * 0    cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/collect_crowding.py >> logs/collect_crowding.log 2>&1
```
现有 3 条 paper cron、进化/估值/指标采集 cron **全部未动**（只追加）。risk_patrol 定在 paper daily(16:30) 之后 15 分钟，天然读当日最新净值。

---

## 8. 与 R-204 行业标准的对照

| R-204 要求（维度四/八） | 本模块落地 | 状态 |
|---|---|---|
| 退出纪律事前写死、禁止事后放宽 | `risk-charter.json` + amendment_rule（改须 decision-log+通知） | ✅ |
| 回撤止损（历史最大回撤 1~1.5 倍降仓 / 净值熔断） | level1 25% 降仓 / level2 35% 清仓复盘 | ✅ |
| 连续 N 月跑输基准→观察/降权 | watch -10%@6m / downweight -15%@12m | ✅ |
| live Sharpe < 回测 50% → 失效 review | live_vs_backtest ratio 0.5（paper 数据不足时 grey 不误报） | ✅（待数据积累） |
| 微盘拥挤度监控（①成交占比 ②换手率分位 ③超额滚动衰减 ④雪球敲入代理） | 四指标全部本地自算，2024-01 危机校验通过 | ✅ |
| 容量估算（单日交易量 ≤ ADV×5%~15% 倒推容量） | 三档容量 + 每股明细 + 瓶颈识别 | ✅ |
| 任一异常→自动降仓建议 | risk_patrol 红项 → risk-events + 告警链路 | ✅ |
| 独立风控视角（阈值独立配置文件） | risk-charter 独立于 model/，开发不可改 | ✅ |

**已知缺口/后续**：① paper 实盘满 20 个交易日后 live_vs_backtest 自动启用；② 中证1000 雪球代理待数据源恢复（现用中证500 代理）；③ 退市股池（R-207 W6）落地后微盘成交占比需重估（当前或略高估微盘流动性）；④ 拥挤度红项目前仅告警，未自动降仓（降仓动作建议与 paper_engine 联动，属 E3 组合级风险预算范畴，留待用户决策）。

---

## 9. 验收自检

1. ✅ `risk-charter.json` schema 完整（含 rule_basis/amendment_rule）
2. ✅ `risk-status.json` 5 规则真实计算值 + 颜色 + 余量（绿/灰，含 crowding_reference + drill）
3. ✅ `crowding-indicators.json` 4 指标 **3 实测 + 1 代理**（雪球用中证500 代理，中证1000 标 unavailable + 替代说明）
4. ✅ 容量三档有数字（1.37/2.73/4.10 亿），与每股 ADV20/权重可复核
5. ✅ `risk-events.jsonl` 演练 3 条（2015 回放，mode=replay）
6. ✅ 本报告 >6KB；两脚本 py_compile 通过且 HP 实跑产出真实数据

*交付：subagent task-0276，2026-08-15。*
