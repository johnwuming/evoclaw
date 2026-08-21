# task-0414 阶段A：ML 非线性因子组合试点（数据债评估 + LightGBM 原型 IC 画像）

- 目标：数据债评估（fin_deep 末端缺失、107 因子面板可用性）+ LightGBM 原型月频 IC 画像 vs ranksum 基准
- 达线判定（预登记）：LightGBM 复合 ICIR 较 ranksum 基准增量 ≥ +0.15 且五分段无方向翻转 → 建议进 E2；否则负结果归档
- 纪律：零回测、零引擎改动、walk-forward 严格时间分离、超参 ≤2 组预登记、种子固定、试验全程计账、数据 md5 锁定

## 进度日志（边查边写）

### T0 19:10 本地上下文
- R-265 为现有最大编号 → 本报告用 R-266 ✓
- R-251 先例要点：W1 IC 口径 = spearman(F_m, R_{m→m+1}) 月频全市场 min_obs=20；股票池全 A qfq 上市≥120 交易日；参照基准 a13_rsraw_e1f10dz = ranksum4(log_mv/amt20/pb_inv/roe)
- W1 通道代码：HP:~/quant-evolve/scripts/a2_ic_data.py → results/factor_ic_monthly.csv
- xhs 笔记要点：Optuna/TPE 可借鉴，但 5 日频率与月频体系不匹配；红旗=过拟合，故本试点超参预算收紧到 ≤2 组配置

### T+8min HP 数据债实查（probe1-3）
- fin_deep_monthly_panel_ak.parquet: 3,004,665 行 × 24 列，ym 范围 2005-06 ~ 2026-08，每月 11,783 行（含退市）
- **无末端截断**：所有列 eff_end（nonnull≥30% 的最后月）= 2026-08；近月覆盖稳定
- **真实数据债是广度覆盖**：现金流量表系列（accrual_quality/cf_or_ratio/cf_np_ratio/ocf_stability/dupont_asset_turn/dupont_leverage/dupont_tax_burden/debt_to_asset/cash_to_asset 等）近月 nonnull 仅 44.5%（全史 27%）；利润表系（gp_margin/roe_report/revenue_yoy/net_profit_yoy/profit_accel）近月 95-99%
- 待查：近月值是否 ffill 陈旧（raw fin_deep 抓取截止）→ probe4 验证
- 107 因子面板（v3ak 机制）：months 2006-01~2026-07，n_months_ic=246，全 A 口径（MIN_LISTED_DAYS=120, MIN_PRICE=0, mvol>0）
- W1 通道代码：factor_expansion_v3ak.build_factor_panel → F(n_codes,n_month,107)/R(月收益)/MASK；compute_monthly_ic: IC[m]=spearman(F[:,m], R[:,m+1])，min_obs=20
- a2 全量重建耗时 562s → 自建精简面板（只算所需列）预计 5-10min

### 在役四因子口径溯源（a9_common.py NEW_B）
- log_mv = log(circ_mv)；pb_inv = 1/pb (pb>0)；roe = roe_ttm；amt20 = 日额 20 日均值
- pb 来源（merge_pb_into_panel）：ths_ttm_panel.equity 按 avail_date PIT as-of → pb = circ_mv/equity（**不是报告期 join**，符合 PIT 纪律）
- circ_mv = 月末收盘 × K线 outstanding_share 列
- 107 面板含 circ_mv/roe_ttm/return_*/turnover_* 但**不含 pb/amt20** → 自建面板补齐

### 方案定稿（预登记）
- 特征清单（8 列，全部现成数据零新采集）：log_mv, log_amt20, pb_inv, roe_ttm, ret_20d, ret_60d, vol_60d, turn_20d
- 标签：次月收益 R[m+1]；MASK 与 W1 相同（上市≥120 交易日、月收盘>0、月量>0）
- walk-forward：预测月 m，训练样本 j ∈ [m-60, m-1]（(F[j], R[j+1])，j+1≤m 严格无泄漏），月频推进
- 超参两组（预登记后冻结）：
  - D（默认）：num_leaves=31, lr=0.05, n_estimators=300, min_child_samples=200, early_stop=patience30（训练窗末 12 月作验证）
  - O（Optuna）：TPE ≤20 trial 仅在首个训练段选定后冻结
- 种子 42；试验计账：D=0 额外 trial，O=≤20
- 基准：ranksum4 = Σ sign×rank_pct（log_mv/amt20 用负向, pb_inv/roe 正向）同口径重算 IC 序列
- 达线：LGBM 复合 ICIR − ranksum ICIR ≥ +0.15 且五分段无方向翻转

### T+45min 面板完成 + 基准落盘
- panel.npz: (5206 codes, 247 月 2006-01~2026-07, 8 特征), mask=693,194 行月；md5 见 panel_meta.json
- ranksum4 基准（同口径重算）: n=240 月, mean_ic=0.0862, **ICIR=0.6893**, ic>0 占比 76.3%
  - 单因子参照（W1 catalog）: circ_mv 0.269 / div_yield 0.261 → 四因子 ranksum 复合远高于单因子，量级合理（复合效应）
- 特征覆盖（mask 内）: panel_meta.json feature_coverage_in_mask 待写入报告

### LGBM 运行（含波折，如实记录）
- optuna 未装且不装（避免依赖升级动生产 env）→ O 组改为预登记随机搜索 20 trial（seed42，空间：num_leaves{15,31,63}×lr{0.03,0.05,0.10}×min_child{100,200,400}×ff{0.7,0.9,1.0}），计账口径同 Optuna ≤20
- 运维教训×2：pkill -f 自匹配 kill 了自身 ssh shell（两次），后用分隔 ssh+方括号正则解决；quintile 需逐月 score 落盘，中途补 np.save 后重启（损失~3min）
- D 组 walk-forward 中段观察：2018-2024 多个月 IC 为负（2018 -0.10 / 2020 -0.15 / 2024-01 -0.37），近年特征-收益关系弱化明显，与 2024 微盘股剧烈波动期吻合；如实进报告
- O 组选定参数与 val_ic 见 lgbm_run.log / lgbm_summary.json

### T+75min 最终数字与判定
- 同窗186月: ranksum ICIR 0.667 / LGBM-D 0.750 (Δ+0.084) / LGBM-O 0.717 (Δ+0.050)
- 五分段全正(无翻转)✓ 五分位单调✓ 但 Δ<0.15 → **未达线, 负结果归档, 不进E2**
- IC序列相关 0.77/0.78 (22%正交信息未转化足够增量); 分组价差 LGBM≈ranksum (1.90 vs 1.91pp)
- 验收四件套全过: V1 score↔csv 三月逐位一致 / V2 K线复算月收益+amt20 / V3 walk-forward边界实查 / V4 ranksum独立秩实现复算
- md5: panel 738727d3, ranksum bf6e8336, D 80610b42, O 5a747bf3, analysis 5efbc7a9
- 试验计账: D=0 组外trial, O=20 trial(随机搜索替代optuna, 已在报告如实记录偏差)
- R-266 已写入 (5783B≥2KB), README 待更新, completions 待写
