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

## 发现1：四表原始数据规模（data/fin_deep/_meta_ak.json, 采集于 2026-08-16）
- yjbb（业绩报表）: 451,669 行, **11,765 只股票**, 86 期全部完成
- zcfz（资产负债表）: 279,074 行, **5,244 只股票**, 86 期
- xjll（现金流量表）: 287,642 行, **5,244 只股票**, 86 期
- lrb（利润表）: 288,443 行, **5,244 只股票**, 86 期
- _state_ak.json: 344 键全 ok，无 empty/缺失期 → 不是"期没采"，是"每期行内股票覆盖"差异
- **初判**：现金流系/资产负债系列缺失的直接原因极可能是 xjll/zcfz 每期只覆盖约 5,244 只（疑=当前在市股票），而 yjbb 覆盖 11,765 只（含退市/曾上市）→ 待逐期验证
- 关键列：Sloan 应计 = (net_profit[yjbb或lrb] − ocf[xjll]) / total_asset[zcfz]；PIT 用 pubDate

## 发现2：逐期行数对比（直接读 parquet 实测）
| report_period | yjbb | xjll | xjll/yjbb |
|---|---|---|---|
| 20050331 | 1,438 | 1,173 | 81.6% |
| 20100630 | 2,465 | 2,110 | 85.6% |
| 20151231 | 9,087 | 4,088 | 45.0% |
| 20201231 | 10,891 | 5,181 | 47.6% |
| 20251231 | 11,518 | 5,228 | 45.4% |
| 20260630 | 1,123 | 429 | 38.2%（采集于08-16，中报未披露完）|

- xjll 总股票 5,244 ≈ 当前 A 股在市规模（沪+深+北 ≈5,300+）
- yjbb 20251231 有 11,518 行 ≈ 当前 A 股 5,228 + ~6,300 非主板代码（疑新三板/B股/退市，NEEQ 2025 强制年报 ~7,000 家）
- **5244/11765 = 44.57% 精确复现 R-266 的 44.5%** → 强烈指向：44.5% = 面板股票池含非 A 股代码（yjbb 引入）而现金流表只有 A 股，分母被污染
- 待验证：①缺失代码的前缀分布（43/83/87/92=NEEQ，200/900=B股）②A 股真宇宙内 xjll 覆盖率③2005-2010 年老期缺口构成（81-85%，非 44.5%，需单独看）
