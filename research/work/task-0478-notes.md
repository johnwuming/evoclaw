# task-0478 notes — csad 独立引擎 E2 回测 + 与在役 a13 结合收益分析
时间戳: 2026-08-24 13:28 GMT+8 (start)

## 0. 任务书要点
- 目标: csad 独立引擎真实 NAV 回测 + 与在役 a13 组合收益实测 (R-297)
- 数据: HP ~/quant-evolve/, python=/home/noname/miniconda3/envs/quant/bin/python
- 关键: 预注册先写后算(机器锁 JSON+sha256 落盘时间<首跑), 判门数字全部来自 e2_results.json
- 零引擎/registry/paper_engine/HP crontab 改动

## 1. 执行日志 (append)

## 2. 探测记录 (2026-08-24 13:30)
- HP 连接 OK (10.12.192.174, QUANT_SSH_PASSWORD)
- a13_rsraw_e1f10dz_full_nav.csv: date,nav,num_held, 5009 行 (2006-01-04 起, 日频)
- csad_resid_monthly.csv: ym,code,resid_z, 596523 行, md5 416019cf5368bde27c289949069f6193 ✓ (与任务书一致)
- r263 脚本目录 scripts_r263 未在 results/work/r263/ 下找到, 需确认位置 (VPS 镜像 work/r263/scripts_r263/)

## 3. 探测记录-续 (13:45)
- r263_run.py 机制理解: a9_common.patch_engine 链式补丁, ext_specs 注入第5因子 csad_resid 负权 (NaN→0)
- a9_common.py: PB ext 排序分支 (ext_mode=zscore|ranksum, ext_specs=[(factor,weight,sign),...]); PC e1_guard + xsub_days; PA raw_universe 四闸门可关
- r263_eval.py: G0/G1/G2/G3 判门, e2_results.json, 复合 IC 用 dump 的引擎排序分
- 关键: 独立引擎形态 = ext_specs 仅含 csad_resid (唯一排序核) 而非 4因子+csad 第5因子 — 需确认引擎权重分配

## 4. 引擎机制确认 (13:52)
- ext ranksum 评分: 每 spec (name,wgt,sgn), _col.rank(pct=True) → _con = wgt*sgn*_tr → 求和
  → 单因子 ext_specs=[("csad_resid",1.0,-1)] 即 csad_resid_z 唯一排序核(负向=低残差分化优先) ✓
- ext_filter_all=1: wgt≠0 或 _fa 时要求因子非缺失 (独立引擎需 csad 非缺失, NaN 政策=冻结面板缺失置0 → 实际上缺失行会被 _fa 过滤掉, 需确认)
- 引擎等权 (w=1.0/len(new_pool)); 梯度需自定义补丁, 时间预算内优先等权 Top-N
- a13 引擎: raw_universe=1(四闸门关), e1_guard=0, xsub_days=365, e1_lambda=1.0, e1_deadzone=0.30, n_hold=20, cost v2
- 独立引擎决策: 候选池同 a13 (raw_universe=1, xsub=365, 四闸门关), 排序=纯 csad (e1_lambda=0 保持唯一排序核), 等权 Top-N

## 5. 判门参照确认 (13:58)
- R-289 可转债判门量级: G1 超额门(主窗毛年化超额 vs 基准≥5pp), G2 回撤门(MDD≤20%), G3 分段门(两窗>0), G4 holdout, G5 容量
- 但 csad 是股票多头引擎(非可转债), 与 a13 同池; G1 质量门参照 R-263 思路: 独立引擎自身质量(ann/MDD), 冻结于预注册
- R-255 corr<0.5 独立性门槛(G2 核心); R-263 G3 holdout 红旗条款; R-260 近段 ICIR -0.269 显性化
