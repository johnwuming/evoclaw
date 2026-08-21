# task-0438 过程笔记（风格轮动 E2 执行，R-270 照单跑）

- 开工：2026-08-22 00:05 前后，task-0438 已置 running（API 返回 ok）。
- 执行依据：R-270 预注册（12.6KB 全文已读）。门槛/网格/口径以 R-270 为准，一字不改。
- R-268（E1）全文已读：S1 = ln(PE1000/PE300) 日频 spread，trailing 756 交易日分位（roll3y，min_periods=250，PIT 含 x[:-1] 排除自身），月末采样，≥0.70 高估 → 次月切换。S2 = micro_turnover_share_roll20 同式 roll3y 分位 ≥0.60。
- 关键数据定位（待核）：
  - legulegu PE：/tmp/r268/pe_lg_*.csv（task-0428 落盘，可能已清）；镜像 work/task-0428-data/
  - a13 nav：shared/results/04-投资研究/a13_rsraw_e1f10dz_full_nav.csv（5009 日，至 2026-08-14）
  - 拥挤度：shared/results/04-投资研究/crowding_history.csv（2019-01-02→2026-08-19）
  - hs300：HP hs300_daily_20060101_20260808.parquet
  - 代理验证数据：HP 既有财务面板+市值（ths 面板，市值后 20% 股票 EP 中位数倒数）

## 执行清单（照 R-270 §八）
1. 代理验证（§二.3.b：自算微盘等权 PE vs 中证1000 代理信号 roll3y 分位秩相关 ≥0.6，共同窗 2017-11→今）→ 不过则停止执行如实报告
2. G0 对拍（m≡0 → NAV ≡ full NAV，max|Δ|<1e-12；全触发月加权校验）
3. T1 X=30% / T2 X=50%（三成本档，0.05% 档判门）
4. T3 拥挤度单独信号对照（X=胜者 X）
5. 判门（G1 危机窗 2023-05-01→2024-02-29 MDD 改善≥2pp；G2 全窗损耗≤1pp；G3 两半段>−1pp；G4 holdout 仅披露）
6. 台账计账 ≤4，先登记后读结果
7. R-271 报告 + README + completions
8. R-269 归档注记（沿 R-258 先例，正文不改）

## 核验点记录
（边查边写）
