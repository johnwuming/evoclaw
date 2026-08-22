# task-0413 T4(a14_crowdf2) 复看过程笔记

> 阶段A证据收集。来源逐点落此文件,报告撰写只从本文件取材。
> 基准:零改动 registry/paper_engine/在役引擎文件;产物只落 results/ 新文件。

## A1. T4 定义与 R-254 评分细节(摘自 R-254 报告,9040B 已全读)

- **T4 定义**:R-253 E2 胜者(run bt_r252_t4_f2_l10_20260821)。拥挤度高状态期对选股层尺寸因子连续降权:F2 线性 clip((p-40)/20,0,1) × λ_c=1.0,作用于 ext ranksum 变换后 log_mv 列;p 为 roll3y(756d, min250) 分位(月频 PIT,调仓用上月已锁值);其余参数与在役 C4 逐字同。
- **评分制 v1.1 结果**:总分 0.8584,池内 rank2(a13 0.8781 > T4 0.8584 > v4a_mf0_trr 0.8088)。
  - 分量:p 1.0(单侧 p=0.4719)、dsr 0.999(DSR 0.9999)、oos_calmar 0.4888、oos_sharpe 0.4929、is_calmar 1.0、is_sharpe 1.0、dd 1.0(locked mdd 同 -0.3355)、corr N/A(权重0.10重归一)、logic 1.0。
  - 门禁:g1 PASS(icir_is 2.0717/180月)、g2 PASS(icir_oos 2.6491/42月)、g3 N/A、g4/g5 PASS、g6 disabled。
  - holdout PASS:2024-07-01→2026-08-13 ann 0.2504 ≥ 0.6×0.2182;mdd 恶化 -17.42pp(实为改善)≤10pp。
- **留档理由**:三条件差 rank1 一条(-0.0197 vs a13)。唯一失分点=oos 两分量:T4 相对在役绩效增量≈零(0.489/0.493,零增量=0.5),而 a13 当年 oos 增量为正。拥挤度降权收益(危机窗 MDD +1.45pp)不进评分制任何分量。
- **量化缺口**:oos 分量要 ≥0.7 需相对增量 ≥+16pp,即 locked calmar 0.6503→~0.76,远超 E2 观测收益区间。
- **当时建议**:① 评分制 v1.2 加 crisis 窗分量(需另立项);② 以「择时/风控组件」定位评估接入。
- **registry**:candidate=a14_crowdf2.json(status=candidate, parent=a13_rsraw_e1f10dz),无任何 status 变更。

## A1b. 复看触发条件(任务书转述,待从 R-252/253 或 registry 原文核实)

- ① crowding 快照积累出「新高拥挤回落段」做真 OOS 检验;② 或 2027-08 例行重评。
- 用户 2026-08-22 16:10 拍板:现在执行复看,不等触发窗口。

## 编号确认

- shared/results/05-量化投资/ 现有最大 = R-272(情绪维度E1画像)。R-272 已占 → 本任务正式报告用 **R-273**。

## A2. 拥挤度指标精确定义(摘自 R-250 + R-252 预注册)

- **底层指标** share_roll20 = 微盘成交额/全A成交额 20日均值(amount 口径,不受 qfq 复权改写,PIT 稳健)。微盘=每日按总市值(收盘×总股本)后20%。
- **状态变量** p(t) = share_roll20 的 trailing 756 交易日(roll3y, min250)分位,逐字式 `shr.rolling(756,min250).apply(lambda x:(x[:-1]<=x[-1]).mean()*100,raw=True)`。
- **T4 调制** m(t)=clip((p-40)/20,0,1)×λ_c=1.0 → **p<40 时 m=0,T4 与在役 C4 完全等价**(同一因子集、同一调仓、同一 nav)。
- **快照机制**(task-0408 已落地):HP results/crowding_snapshots.csv append-only 月锁,首锁 2026-07 roll3y=3.3113;2026-08 起实盘/影子状态以快照为准;E2 历史段消费冻结文件 roll3y_states.csv(双锚 2023-09=92.848 / 2026-07=3.3113)。
- **状态序列事实**(R-252 §二.6,n=80 月 2020-01→2026-08):high(>60) 共 20 个月,最后一个=**2025-05**;2025-06 起全部低位;2026-07=3.31。
- VPS 数据现状:crowding_history.csv(HP 日频)**未同步** VPS(auto_sync include 仅 crowding-indicators.json);roll3y_states.csv 也在 HP。VPS 有:crowding_monthly.csv(月度镜像至 2026-08,crowding-indicators.json(2026-08-19 生成)、r252 E2 全部 nav/metrics 产物。

## A3. 快照/监控数据盘点

- crowding-indicators.json(9149B):generated_at 2026-08-19 18:00,latest_date 2026-08-19,schema v2。4 指标:micro_turnover_share(latest 0.02901,60日分位 90,yellow)、micro_turnover_pctile(63.3,green)、excess_decay(latest -0.001889,t=-4.643,**red**)、snowball_knockin(green);overall_flag=**red**。microcap_eqw_index 90 点(2026-04-10→2026-08-19,748.96→612.84)。
- VPS freshness 机制:crowding-freshness-check.sh 每日一查(generated_at>192h=red,latest 滞后>5交易日=yellow),task-0371 落地。
- crowding_monthly.csv(12863B,HP 镜像,2026-08-21 生成):月度 shr_roll20/epct(全史expanding分位)/pct60/snowball/nav_end/ret/crow_state,2020-01→2026-08。
- 快照历史缺口:crowding-indicators.json 为覆盖式快照,无逐日历史;月度锁存 2026-07 才首锁,历史段(2020-01→2026-06)仍依赖 HP qfq 全量重算(R-252 §8.1 已知残余风险)。

(待续:判据计算)
