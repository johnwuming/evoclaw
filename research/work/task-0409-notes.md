# task-0409 / R-251 SUE 财报事件因子 IC 画像 — 过程笔记

- 任务：R-249 方向五 E1 前置，SUE 因子 IC 画像（W1 口径），达线判定参照在役四因子
- 开始：2026-08-21 01:41
- 状态：初始化

## 步骤记录

1. [01:41] 任务中心 task-0409 已置 running（API 返回 ok:true）
2. [01:41] 编号确认：05-量化投资 下最大为 R-250 → 本报告 R-251

3. [01:47] HP 数据定位完成：
   - ths_ttm_panel: data/derived/ths_ttm_panel.parquet, 235170 行 × 8 列
     [code, report_date, net_profit_ttm, equity, roe_ttm, roa_ttm, debt, avail_date]
     avail=1998-04-30 起，code 数待查；早期为半年报频率
   - W1 IC 通道: results/factor_ic_monthly.csv 宽表 ym+107因子, 2006-01~2026-07 共 247 月
     口径(factor_expansion_v3ak.compute_monthly_ic): IC[m]=spearman(F_m, R_{m+1}), MIN_OBS_MONTH=20, 全市场
     财务因子月度值 = fin 面板按 ym reindex 后 ffill（as-of PIT 同型）
   - 在役 registry: model/registry/a13_rsraw_e1f10dz.json (status=active)
     ranksum4 因子: log_mv(1.0,-1), amt20(1.0,-1), pb_inv(0.7,+1), roe(0.3,+1) + mom_pen_dz
   - 参照线 ICIR (factor_ic_monthly.csv 同口径):
     div_yield_ttm: IC .0265 ICIR .261 t 4.10 | circ_mv: IC .0475 ICIR .269 t 4.24
     roe_ttm: IC -.0130 ICIR -.092 t -1.45 | net_profit_yoy: IC -.013 ICIR -.209 t -3.24 (240月)
     → 参照线取在役可用因子：circ_mv ICIR≈0.27（最高）, div_yield≈0.26
   - 价格: data/all_stocks_qfq/*_daily_qfq.parquet 逐股日线
