# Q3 可交易性基建：成本模型 v2 + 一字板不可成交约束 — 交付报告

**task-0293** · 2026-08-16 · 状态：✅ 完成
模块：`scripts/cost_model_v2.py`（新）· 集成：`scripts/backtest_dividend_quality_iter.py` · 透传：`scripts/backtest_macro_timing_iter4.py`

---

## 1. 成本模型 v2（estimate_cost）

```
单边总成本 = 佣金 2.5bp(min 5元) + 印花税卖出 5bp + 冲击 k·sqrt(参与率)
参与率 = 下单金额 / 20日ADV(成交额)   k=10（保守，可调）
```

- 接口：`estimate_cost(order_amt, adv20, side, impact_k=10)` → `{total_bps, commission_bps, stamp_bps, impact_bps, participation}`；非法输入返回 None
- ADV20 由 K线 `amount` 列滚动 20 日均值计算（回测内 `win=a.loc[:d].tail(20)`）
- 合成用例自测（3+非法）：
  - 小单 buy 100万/ADV1亿 → 3.5bp（comm2.5 + impact1.0）
  - 大单 sell 2000万/ADV5000万 → 13.8bp（comm2.5+stamp5+impact6.32）
  - 小额 1万/ADV2万 → 12.1bp（佣金min5元触发=5bp + impact7.07）
  - order/adv ≤0 或 side 非法 → None
- ⚠️ 关键实现注意（本次实际踩坑）：**佣金 min 5 元必须按真实名义金额折算**。回测 NAV=1.0 归一化时直接传 0.05 元订单 → 单笔 100 万 bp 直接毁灭组合（annual_return=nan、max_dd=-1266）。集成层引入 `capital_base=1e7`（CLI `--capital_base` 可调）换算真实下单金额，另加单期成本 5% 安全阀。规模敏感性：1000万本金/20只等权=单笔50万 → 冲击 <1.3bp；5亿以上资金冲击项将显著放大。

## 2. 一字板不可成交约束（is_untradeable）

- 判定：`O==H==L==C`（相对容差 1e-6）且 涨跌幅 ≥ 板块阈值-0.1%容差 → 一字板
- 方向：`direction="buy"`=一字涨停不可买；`"sell"`=一字跌停不可卖；None=双向
- 阈值分段（代码前缀+日期）：主板60/00=10%·ST5%；科创板688=20%；创业板300/301 2020-08-24前10%后20%；北交所30%
- **方法近似性**（文档要求写明）：数据为 qfq 前复权 OHLC，无未复权价。复权因子日内恒定 → O==H==L==C 等价关系在复权前后不变；qfq 序列的 `close/prev_close-1` 即真实涨跌幅。若当日恰逢除权且复权因子有微小浮点残差，由 0.1% 容差吸收。
- 合成用例自测（6 例全过）：主板一字涨停 buy=True / 科创板20cm一字=True（+19.5%容差外=False）/ ST一字跌停 sell=True / 普通日 False / 一字但+3% False / 创业板阈值分段正确

## 3. 集成（可开关，默认不变）

`backtest_dividend_quality_iter.py`：
- `--cost-model legacy|v2`（默认 **legacy**，保持现有结论连续性）
- `--limit-board off|on`（默认 **off**）
- v2 路径：调仓日对每笔 SELL/BUY 按名义本金×权重估成本汇总扣减；ADV 缺失(<10日)兜底 legacy 一半
- 一字板处理：买入遇一字涨停 → 跳过本次调仓（buy_skip，与原 limit_up_reached 叠加）；持仓遇一字跌停卖不出 → **顺延持有**（sell_skip，新增）
- holdings.csv 新增 `sell_skipped_limit_down` 列；metrics.json 记录 cost_model/limit_board/capital_base
- load_market_data 新增 opens/highs/lows 三字典（O/H/L 列），`_MARKET_CACHE` 结构扩展

`backtest_macro_timing_iter4.py`：BASE_CFG 显式 `cost_model="legacy", limit_board="off", capital_base=1e7` 透传 engine（可改 v2/on 复用整套模块）。

## 4. 验证跑对比（全区间 2005-01~2026-08，默认参数，真实双跑）

| 指标 | legacy + off | **v2 + limit-board on** |
|---|---|---|
| annual_return | 24.35% | **24.98%** |
| max_drawdown | -69.64% | -69.49% |
| sharpe | 0.865 | **0.881** |
| calmar | 0.3496 | 0.3595 |
| monthly_turnover_est | 0.2609 | 0.2601 |
| cumulative (21.6y) | 109.9x | 122.8x |

- 验证文件：`results/q3_legacy_2023_{metrics,nav,holdings,trades}.csv` / `results/q3_v2lb_fix_*`（前缀带 2023 系首跑名，实际区间为全区间；metrics.json 内 period_start/end 可证）
- 约束生效统计：buy_skip 17 次（两版相同，原 limit_up_reached 已有近似过滤）；**sell_skip 顺延 2 次（新约束真实生效）**
- 成本差异解释：v2 单期 ≈6-8bp < legacy 固定 10bp/期。1000万名义本金、20只等权（单笔50万）在 ADV>5000万 的标的冲击 <1.3bp；等权月调仓策略本身换手低（月换手 26%）。**结论：v2 成本更真实且对小资金略宽松；但该结论依赖 capital_base 假设，5亿以上资金必须重估**（参与率>10% 时 impact 项平方根放大）。
- 跑时长：单次全区间约 5-7 分钟（数据加载 6030 只 parquet 占大头），未超 15min 上限。

## 5. 回归确认

- legacy 默认路径与改动前口径一致：cost_rate=0.001 未动、默认开关 legacy/off、`--help` 全参数不变、py_compile 三文件全过
- 未动 audit_lock.py / evolution_pipeline.py / fin_deep / qfq 数据（git status 仅新增 cost_model_v2.py）
- 自测命令：`python scripts/cost_model_v2.py`（全过）；过程笔记 `/tmp/q3-notes.md`

## 6. 后续建议（非本任务范围）

1. impact_k=10 目前是保守拍值，可用逐笔/VWAP 数据实证校准
2. 一字板判定可升级为用未复权价+涨跌停价精确比对（需补未复权数据源）
3. 大资金规模敏感性分析（capital_base 0.1/1/10 亿网格）值得单独跑一次
