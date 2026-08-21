# task-0411 过程笔记：R-252 拥挤度选股降权 E2 引擎级对照执行

- 日期：2026-08-21 09:21 开工；PUT task-0411 status=running ok
- 执行依据：R-252 §十执行清单（照单执行，门槛不可改）
- 交付：R-253 报告 + work/r252/e2_results.json + HP results/ 产物

## 0. 参照系数字（从 R-252/task-0410 摘入，供判定用）
- 在役 a13_rsraw_e1f10dz：W-full ann 0.2239 / MDD -0.3355；W-crowd(2020-01→2026-08) ann 0.1394 / MDD -0.1613；W-crisis(2023-09-01→2024-02-29) MDD -0.0957 窗收益 -3.57%；W-holdout(2024-07-01→2026-08-14) ann 0.2574 / MDD -0.1613
- 四门：G1 W-crisis MDD ≥ -8.57%；G2 W-crowd ann ≥ 12.44%；G3 W-full MDD ≥ -35.55% 且 W-crowd MDD ≥ -18.13%（W-full MDD 变动 >0.5pp=实现缺陷警报）；G4 W-holdout ann ≥ 24.24% 且 MDD 恶化 ≤2pp
- 网格：T1=F1×0.5 / T2=F1×1.0 / T3=F2×0.5 / T4=F2×1.0；n_trials=4
- 双锚：roll3y 2023-09=92.848 / 2026-07=3.3113
- 高位月(>60) 20 个月：2020-10；2022-11；2023-02,03,06,07,08,09,10,11,12；2024-01~08；2025-05

## 1. HP 环境探查（2026-08-21 09:2x）
- SSH：key `~/.ssh/id_hp` -p 2222 noname@10.12.192.174 OK（scp/sftp 不可用，用 cat 管道传输）
- runner 基建：scripts/a13_run.py + a9_common.py（load_engine/patch_engine/build_timing/write_dual_artifacts）；a15_run.py 同款。补丁链：inspect.getsource(engine.run_backtest) 打 PA/PB(ext排序)/PC/PE2/PD/PE 补丁后 exec 成新函数，引擎文件零改动
- 在役 C4 配置：sort=ext, ext_mode=ranksum, ext_specs=[(log_mv,1,-1),(amt20,1,-1),(pb_inv,0.7,1),(roe,0.3,1)], ext_filter_all=1, raw_universe=1, e1_guard=0, xsub_days=365, e1_lambda=1.0, e1_deadzone=0.30；BASE 同 a13_run（cost v2/limit_board on/n_hold 20/capital 1e7）；FULL_RANGE 2006-01-01→2026-08-31
- ext 排序实现（a9_common NEW_B）：每因子列 _fval 取原始值 → ranksum 模式 `_tr = _col.rank(pct=True)` → `_con = wgt*sgn*_tr` 求和，再叠 e1_lambda 惩罚。**R-252 调制必须作用在变换后列**（原始值乘正常数不改变 pct-rank，无效果）；λ_c=0 时乘 1.0 位逐位不变（IEEE x*1.0==x）→ G0 结构可保证
- 调仓日：rebalance_dates = 每月首个交易日（groupby M .min()）；ext 分支在 `if d in rebalance_dates:` 内，d 可用于调制函数
- 耗时基准（a13 日志）：市场加载 70s，每回测 ~352s → G0+T1-T4 共 5 跑 ≈ 31 分钟
- 台账：results/experiment-ledger.jsonl，格式 {run_id, ts, type, code_ref, data_snapshot, metrics:{experiment_id, features, full, locked}, logic}；现存最大 IT-A13-04 → 本批 IT-R252-01..04（仅 4 网格点，G0 不入台账避免 n_trials 混淆）
- NAV 文件：date,nav,num_held；在役 full_nav 末行 2026-08-14

## 2. 冻结状态序列（R-252 §十.1）✅
- 脚本 scripts/r252_freeze.py（HP），公式与 r250_v2.py L25 逐字同式，月度=groupby(M).last()，dropna 后 2020-01→2026-08 共 80 月
- 产物 results/work/r252/roll3y_states.csv（列 month,roll3y_pct,s_step,s_linear）+ .md5
- **md5 = 91b70df95013d24ba6b609e66fa8c06f**
- 双锚校验：2023-09 = 92.847682 → round3 = 92.848 ✓；2026-07 = 3.311258 → round4 = 3.3113 ✓
- 高位月(>60)恰 20 个，与 R-252 §二.6 清单逐一一致：2020-10；2022-11；2023-02,03,06-12；2024-01~08；2025-05
- 注：首版未 dropna 时 n=92（含 2019 段 NaN 行），dropna 后 80 ✓（2019 段不进冻结文件，回测中 m≡1，合 §二.5）

## 3. G0+T1-T4 回测（09:31 启动，PID 569916，nohup 后台）
- 脚本 scripts/r252_run.py：链式补丁 = inspect.getsource(a9_common.patch_engine) 源码追加 R252 调制块（OLD_R/NEW_R 锚在 `_con = float(_wgt)*float(_sgn)*_tr`，24 空格缩进），exec 后注入 _R252 命名空间；引擎文件零改动，与 a13/a15 runner 完全同参（BASE/E1F10DZ/FULL_RANGE 逐一复刻）
- 干跑验证（/tmp/r252_drycheck.py）全部通过：补丁链可编译（16899→23086 字符）；_R252 在 patched 引擎 globals 可达；m(d) 在 7 个日期样例上数值正确（含 2023-10-09 F1λ=1 → m=0、F2 中间带 p=47.06 λ=0.5 → m=0.8235）；λ_c=0 时 m≡1.0 于全部 5391 个工作日；float x*1.0==x 逐位不变
- 事故记录（已修复，不影响结果）：①首版 scp 不可用改 cat 管道；②首次启动命令 `cat>file && cd && nohup &` 因 & 优先级把传输链后台化，脚本被写成 0 字节 → 分离传输/启动两步 + md5 校验后重启；③首版冻结 CSV 索引名 date≠month → 重冻结（规范列名）；④补丁锚缩进 20→24 空格修复 IndentationError
- 运行时序：76s 市场+择时就绪（pos mean=0.516 与在役同），G0 于 76.3s 开跑；每跑 ~352s

## 3b. G0 首跑事故与修复（§七.4 执行事故，不计 n_trials，已披露）
- 现象：417s 完成后 G0 对拍 FAIL — **index mismatch n_new=5012 vs n_ref=5008**（在 NAV 值比较前就断）
- 根因：**市场数据漂移**，非实现缺陷。在役 a13_rsraw_e1f10dz_full_nav 产物 kline 截至 2026-08-14（台账 data_snapshot.kline_as_of=2026-08-14）；本次加载的数据已含 08-17/18/19/20 共 4 个新增交易日 → NAV 多 4 行。两文件末行：ref=2026-08-14 nav=64.3096，new=2026-08-20 nav=64.1135
- 修复：FULL_RANGE 终点 2026-08-31 → **2026-08-14**（= 预注册参照系窗口终点，R-252 §五 W-full 表 2006-01-04→2026-08-14；窗口截断使数据一致且不改变预登记参照系数字）；删除 r252_g0_lam0_* 旧产物后重启（09:42，PID 570506）
- 台账验证：事故时点 IT-R252 条目 0 条，无污染；G0 不入台账（仅 4 网格点）
- 时序安全性论证：engine 内 trade_dates/rebalance_dates 被 end_ts 过滤；因子/基本面约 .loc[:d] 向后看；择时月度序列月桶内因果，月末时间戳 2026-08-31 > 08-14，ffill 映射便 08-14 前交易日仍取 7 月桶值 → 截断不改变窗口内取值路径（若 G0 逐位一致即实证背书）

## 3c. G0 二跑仍败 → 根因定位与最终修复（§七.4）
- 二跑（窗口已截 08-14）：行数对齐 5008，但 max|Δnav|=0.2567 —— 逐日定位发散模式：
  - 2008-05-21 起微漂移 7.2e-09，缓慢累积到 2026-08-12 的 1.38e-07（无跳变、无仓位翻转）→ **qfq 前复权重写特征**（2026-08-19 collect_qfq_baostock.py 变更，新除权事件触发全量因子重算；佐证：成交额口径 crowding_history 锚点全部不变，仅价格路径微变）
  - 末日 08-14 单日跳 0.2567（0.4%）→ **端点伪影**：在役产物 08-14 行为数据末端冻结行（nav=08-13 直写、num_held=0、无真实 P&L）；当前数据下重跑的 08-14 是真实持仓 mark（我方 08-13 nav=64.3095626754451/held=20 → 08-14 nav=64.56629810577765/held=20；在役 08-13=08-14=64.30956281284777/held=0）
- 结论：**「与旧在役产物逐位一致」在当前数据上结构性不可能**（旧产物底层数据已不存在），非实现缺陷
- 最终修复（§七.4 事故路径，全量披露）：
  1. **G0 改为同数据实现层对拍**：r252_g0_orig（原 a9 补丁无注入，在役配置，同数据同截断）vs r252_g0_lam0（R252 注入 λ_c=0）——唯一差异 = 调制注入，须逐位一致（<1e-12）→ 直接检验 G0 设计目的（λ_c=0 零回归）
  2. **窗口指标统一截断 2026-08-13**（双方最后真实 mark 公共日；否则候选在 08-14 的真实 mark 会不对称抬高 holdout ann ~0.19pp）；参照系 4dp 复算验证不变 → 预登记门槛继续有效
  3. 数据漂移量化披露：≤1.4e-07（08-13 前），对 4dp 指标无影响
- 三跑（09:56 启动）：G0(skip 已存) → G0B 基准 → 门检 → T1-T4；台账 4 点不变

## 3d. G0 门最终结果 ✅ PASS（424.4s，三跑）
- **实现层对拍：r252_g0_lam0 vs r252_g0_orig（原 a9 补丁无注入，同数据同截断）：max|Δnav| = 0.000e+00，n=5008，逐位完全一致（不仅 <1e-12，是严格 0）** → R252 调制注入在 λ_c=0 下严格惰性，G0 设计目的（实现零回归）达成
- G0/G0B full 指标一致：ann 0.2241 / mdd -0.3355 / sharpe 1.375（与在役旧产物 ann 0.2239 差 2e-4，源自 qfq 重写微漂移 + 末日伪影，已量化披露）
- 数据漂移披露：vs 旧在役产物 max=2.567e-01（其中末日伪影占绝大头；08-13 前 ≤1.4e-07）
- T1 于 424.4s 开跑，预计 T1-T4 于 ~10:27 完成

## 4. 四门判定与 e2_results.json（待回测完成后填）
