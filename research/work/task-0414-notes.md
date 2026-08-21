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
