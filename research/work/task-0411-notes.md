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
