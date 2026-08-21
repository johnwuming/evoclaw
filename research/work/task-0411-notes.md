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

## 3. G0+T1-T4 回测（进行中）
