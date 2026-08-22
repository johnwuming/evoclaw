# task-0456 notes — excess_decay E1 画像（边查边写）

## A1. 指标口径确认（来源：tmp/task-0373/collect_crowding.py，生成 crowding-indicators.json 的脚本）

- excess_decay 定义（脚本行180-207）：微盘组（每日全市场按总市值后20%，等权）日收益 micro_ret_mean − hs300 日收益 = 日超额；nan→0；cum_ex=∏(1+excess)；log_cum=ln(cum_ex)；对最近 60 个交易日（ROLL=60）做 log_cum 对时间 idx 的 OLS 回归 → slope、tstat（se=sqrt(SSE/(60-2)/denom)）。
- 阈值（脚本行424-433，JSON note 同）：**slope<0 且 tstat<−2 → red**；仅 slope<0 → yellow；否则 green。
- R-273 §三.6 引用：2026-08-19 值 slope=−0.001889，t=−4.643，red ✓（与 crowding-indicators.json latest 一致，可溯源）。
- 指标历史序列文件 crowding_history.csv **VPS 无**（HP 侧未同步）→ 需 VPS 本地重算（脚本在 VPS，数据 all_stocks_qfq 5205 只 parquet 在 VPS workspace-quant/data/）。
- 脚本 hist 输出过滤 date>=2019-01-01 → 监控面板口径 2019 起。E1 普查同样以 2019 起为基准（与监控一致），更早仅作参考。
- 60 日窗口指标 + 盘中日频更新；**PIT 约定（画像用）**：月末最后可用日定值，次月才可作信号用。

## A2. 数据盘点
- all_stocks_qfq: /root/.openclaw/workspace-quant/data/all_stocks_qfq/，5205 个 *_daily_qfq.parquet（待确认最早/最晚日期、hs300 文件名）。
- crowding-indicators.json（9149B, generated 2026-08-19）：microcap_eqw_index 仅 90 日（2026-04-10→08-19），峰 793.09(05-11)→谷 538.36(07-22) = −32.12%（R-273 §三.1）。
- 微盘等权指数全历史需重算（脚本内部有 eqw 全序列，仅存 90 日）。

## A3. 待办
- [ ] 重算 2019→2026 日频 slope/tstat 序列 → 触发普查
- [ ] 触发后 1/2/3 月微盘 vs hs300 超额收益、胜率
- [ ] q3z 正交性（先找 q3z 状态序列是否在 VPS）
- [ ] R-280 报告 + README 更新
