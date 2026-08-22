# task-0442 R-274 fin_deep 现金流列广度44.5%数据债核查 — 过程笔记

## 时间线
- [15:44] 任务启动。目标：审计 fin_deep 现金流列缺失是采集债还是披露缺失；抽样≥30 分层比对 akshare/baostock；判定可补性+成本；允许则 Sloan 应计 IC 画像（零回测）。

## 环境与路径
- HP: sshpass -p "$QUANT_SSH_PASSWORD" ssh noname@10.12.192.174, ~/quant-evolve, python=/home/noname/miniconda3/envs/quant/bin/python

## R-266 关键事实（已读全文 9267B）
- fin_deep 面板：HP `data/derived/fin_deep_monthly_panel_ak.parquet`，3,004,665 行 × 24 列，ym 2005-06~2026-08
- 现金流系 11 列（accrual_quality/cf_or_ratio/cf_np_ratio/ocf_stability/dupont_asset_turn/dupont_leverage/dupont_tax_burden/debt_to_asset/cash_to_asset/inventory_to_asset/ar_to_asset）近月 nonnull 仅 44.5%（全史 27%）
- 利润表系（gp_margin/roe_report/revenue_yoy/net_profit_yoy/profit_accel）近月 95-99%
- 无末端截断、新鲜度季节性正常 → 债在"广度"（横截面覆盖），非时间断裂
- 命名 `_ak` 后缀 → 疑似 akshare 采集

## 计划
1. HP 上找 fin_deep 构建脚本 → 定位原始数据源（akshare 接口/落盘位置）
2. 面板上直接统计：缺失分布（按年份×ym、按股票上市板块）、44.5% 的构成（哪些列共享缺失）
3. 分层抽样 ≥30：缺失行 (code, ym) → 查该股该期财报在 akshare/baostock 现金流量表源是否有数据
4. 判定可补性 + 全量补采成本（行数、预计时长）
5. 时间允许 → Sloan 应计 IC 画像（净利-经营现金流)/总资产，PIT 用披露日，月频 IC，W1 口径）
