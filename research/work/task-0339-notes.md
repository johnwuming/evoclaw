# task-0339 A7b 过程笔记（边查边写）
> 生成 2026-08-17 ~10:00 | 任务：v4b骨架现金曲线 + P0候选稳健性核验

## 访问路径（09:52-10:00 确立）
- HP SSH 10.12.192.174:22 **Connection refused**（多次重试均拒；task-0337/0338 同期同样被拒，疑 fail2ban/MaxStartups）
- 替代路径（沿用 task-0338）：**HP HTTP API http://10.12.192.174:8060 + X-API-Key**（key 在 VPS /root/.openclaw/workspace-quant/scripts/.hp-api-key，32字符）
  - /health OK：quant env 存在，merged 304MB，qfq 5448，disk free 31.7GB
  - /run 可执行（cwd=/home/noname/quant-evolve，env=quant，timeout 上限1800s）
- A7 产物现状：results/a7_ic_monthly.csv + a7_ic_summary.json（IC预检已完成，回测批进行中/未出）
- results/ 总数 552 文件

## 阶段0 基线
（待完成：复跑 v4b_mve1 locked 核对 12.42%/-28.99%/0.840；确认 A7 进程在但不动）

## 阶段0 基线核对（~10:10）
- a5_v4b_mve1_formal_locked_metrics.json（740B）确认：
  sort=gq, n_hold=20, cost_model=v2, limit_board=on, capital=1e7, dd_control=0
  period 2006-01-04~2024-06-28（18.48y, 222次调仓）
  **annual_return=0.1242 / max_drawdown=-0.2899 / sharpe=0.8401 / calmar=0.4285**
  → 与任务书 locked 口径 12.42%/-28.99%/0.840 完全一致 ✓
- A7 进程检查：ps 未见 a7/runner 进程（A7 批可能已结束或未起）；勿动其产物
- 复跑机制：/tmp/a5_runner.py（18KB）patch q4b_run_BC.py 的 run_backtest（ext 排序/权重/inv_vol/vt_target/dd_trigger/value-mom/gq 分支），base_cfg 注入 SEEDP
- 下一步：读 a5_runner main 流程 + base_cfg 复现 v4b_mve1 配置；设计现金注入方式

### 10:30 runner 机制读通（a5_runner.py 362行）
- v4b_mve1 配置 = sort=gq, gq_weights=[1.0,0.0]（即纯 mv 排序）, e1_guard=True, value_cols+mom_cols=GQCOLS, timing=q3z_tr（q3z × EW-MA200 双信号）
- 主循环：MODE=screen/formal_full/formal_locked；base_cfg 注入 SEEDP+engine.DEFAULTS；每次候选先 mk["timing_pos"]=POS[pk]
- POS 构造：q3z 择时 × (ew>ma200 ? 1.0 : 0.6) 月频趋势因子
- 等价校验：patched 开关全关 == 原引擎 nav 逐位一致（full/locked 均 OK）
- 市场加载 q4b.load_fullpool_market 需数分钟（每候选复用同一 market，可一次加载多候选）

### 10:35 a7b_runner.py 生成完毕（HP /tmp/a7b_runner.py, 383行, SYNTAX_OK）
- 改造点：①cash_ratio patch（eff_ret *= (1-cash)）②e1_thresh 可配置（默认-0.30）③ma_window 可配置（默认200）④新增 _pos_ma(w) helper ⑤main 段重写
- 运行计划（一次加载市场，12次回测）：
  - baseline: v4b_mve1 locked 复跑核对
  - 现金曲线: cash_ratio {0,10,20,30,40}% locked
  - 稳健性A(参数扰动): e1_thresh {-0.20,-0.40} / ma_window {150,250} locked
  - 稳健性B(分段子样本): 2018-2021 / 2022-2026
- 输出: results/a7b_* + a7b_summary.json

### 10:45 等价校验 PASS + baseline verify 进行中
- a7b_runner 等价校验 full+locked 均 EQUIV_OK（nav 逐位一致），等价于原引擎
- 已进入 baseline verify (locked) 回测（sort=mv 纯 mv 路径，18.48y/222调仓）
- 注：等价校验用 sort=mv 原引擎路径；v4b_mve1 正式候选走 GQ 分支（gq_weights=[1,0] 纯mv）

### 10:50 baseline verify 复跑确认（cash_00 = 0%现金档）
- v4b_mve1 locked 复跑：**ann=0.1242 mdd=-0.2899 sharpe=0.8401 calmar=0.4285** ✓ 与任务书 locked 口径完全一致
- 批处理已产出 10 个 a7b 文件，继续跑 cash_10..40 + 稳健性

### 10:55 cash 档位进度（locked，每档 vs 0%）
- cash_00: ann=0.1242 mdd=-0.2899 sharpe=0.8401 calmar=0.428（基线复跑确认）
- cash_10: ann=0.1114 (-1.28pt) mdd=-0.2642 (+2.57pt 改善) sharpe=0.834 (-0.006) calmar=0.422
- 斜率初步：每10%现金 ≈ -1.3pt年化 / +2.6pt回撤改善 / 夏普基本持平（贴主 -3pt/+4pt 的斜率不成立，我们框架斜率更温和）
- cash_20: ann=0.0984 (-2.58pt) mdd=-0.2385 (+5.14pt改善) sharpe=0.825 (-0.015) calmar=0.412
- 现金曲线趋势明确：每10%≈-1.3pt年化/+2.6pt回撤改善，夏普单调缓降（-0.006/-0.015）
- cash_30: (待从日志补) cash_40: ann=0.0720 mdd=-0.1877 sharpe=0.800 calmar=0.383
  （cash_30 夹在中间，日志截断未见，稍后从 summary 补）
- **现金曲线 5 档齐全，进入稳健性网格（e1_thresh/ma_window 扰动）**
- 现金档位 MDD≤20% 需 cash≥40%（0.1877），代价年化从12.42→7.20（-5.2pt）

### 11:05 稳健性A（参数扰动）进度
- robust_e1_hi (ret120>-0.40 放宽): ann=0.1239 mdd=-0.2890 sharpe=0.837 calmar=0.428
  → vs 基线(0.1242/-0.2899/0.840) 几乎无差异（E1 阈值放宽几乎不影响）
- robust_ma_150 (EW-MA 150): ann=0.1194 mdd=-0.3156 sharpe=0.814 calmar=0.378
  → 窗口缩短使回撤恶化（-0.3156 vs -0.2899），方向=窗口越短风险越高
- 待补：e1_lo / ma_250 / 子样本 2018-2021 / 2022-2026

### 11:15 完整结果到手（a7b_summary.json 全量解析）
**现金曲线（locked, 18.48y/222调仓）：**
| cash | ann | mdd | sharpe | calmar |
|---|---|---|---|---|
| 0% | 0.1242 | -0.2899 | 0.8401 | 0.4285 |
| 10% | 0.1114 | -0.2642 | 0.8335 | 0.4216 |
| 20% | 0.0984 | -0.2385 | 0.8251 | 0.4124 |
| 30% | 0.0852 | -0.2130 | 0.8142 | 0.4001 |
| 40% | 0.0720 | -0.1877 | 0.7996 | 0.3834 |
→ 每10%现金 ≈ **-1.3pt年化 / +2.6pt回撤改善 / 夏普缓降-0.010**（贴主 -3pt/+4pt/夏普略升 不成立）
→ MDD≤20% 需 cash≥40%（mdd=0.1877），年化代价 12.42→7.20（-5.2pt）；离 25% 目标 -17.8pt

**稳健性A 参数扰动（vs 基线 0.1242/-0.2899/0.840）：**
- e1_lo (ret120>-0.20 收紧): 0.1147/-0.3115/0.783 → 收紧恶化（掉深跌票暴露）
- e1_hi (ret120>-0.40 放宽): 0.1239/-0.2890/0.837 → 与基线几乎无差异（稳健 ✓）
- ma_150 (窗口缩短): 0.1194/-0.3156/0.814 → 回撤恶化
- ma_250 (窗口加长): 0.1188/-0.3008/0.803 → 略差
- 方向一致性：E1 收紧方向=回撤恶化、放宽=无差；MA 缩短=风险升、加长=略差 → 基线参数在"温和区间"，但方向敏感（收紧/缩短均损）

**稳健性B 分段子样本：**
- 2018-2021: 0.0733/-0.1388/0.6311/calmar 0.528
- 2022-2026: 0.0500/-0.1555/0.4929/calmar 0.321
- 两段方向一致：均正收益/正夏普/正Calmar，但近年显著衰减（ann 7.3→5.0），微盘alpha衰减确认

### 11:20 交付物验收 + 收口
- HP results/ a7b 文件 **65 个**（≥10 验收线 ✓）
- a7b-iteration-report.md **5688B**（>3KB 验收线 ✓）
- a7b-cash-curve-metrics.md / a7b-robustness-table.md / a7b-summary-table.json 齐全 ✓
- 现金曲线表 5 档齐全（≥4 档验收线 ✓）；稳健性判定表含参数扰动+分段子样本 ✓
- 结论：事前杠杆不推动前沿；离目标 ann +12.6pt / MDD 需改善 8.99pt / Sharpe +0.36；与 task-0333 Calmar 不变式一致
