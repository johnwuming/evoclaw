# task-0390 过程笔记（A13 四闸门去除候选批引擎级回测）

任务：task-0390 | 开始：2026-08-19 09:19 | 子agent会话 e23ab514

## 授权与规则（用户 02:05/02:25 拍板）
- 四闸门去除不变（div≥2%/ROE>15%/ROA>10%/price≤10 四道质量闸门，R-219 #14-17）
- E1 不做 on/off 硬排除对照，改为因子化：momentum 惩罚进排序分，挂载点 a9_common.py L81-95 + e1_lambda 进 a9_sel cfg（task-0391 已定位）
- 评分制 v1.1（R-225）：六分项 stat0.35/oos0.25/is0.15/dd0.10/corr0.10/logic0.05，N/A 重归一；新血统线已废（不用于 REJECT）；g6 已禁用（D-20260819-G6DEL，dd 分量仍进评分）
- 禁改：paper_engine、HP crontab；evolution_pipeline.py 只加 A13 实验配置（如需）且先备份
- HP 上已有进程勿杀；长计算 nohup+日志轮询，≤40min 预算

## 背景（来自 R-222/R-225/R-238 记忆）
- raw 宇宙（去四闸门）locked 21.76%/-36.78% vs v5h 15.74%/-29.80%（+6pp 年化/-7pp MDD）
- E3 ranksum(mv+amt+pb_inv0.7+roe0.3) raw：21.76%/-33.55% Calmar1.344，MDD 省 3.23pp —— 即"ranksum raw"，近1年 +12.7% 跑赢 v5h(-1.5%)，旧血统线 REJECT（MDD 恶化 3.75pp>2pp），现翻案
- PB IC：raw 全宇宙 ICIR 0.521 vs 质量宇宙 0.196（PB alpha 在闸门外）
- 现役 v5h_xsub 15.74%/-29.80%；评分锚：v2b_trr 0.7811 / v5h_xsub 0.7792 / v5i_comb 0.7692
- v1.1 stat_warn：g2 p<0.01 或 DSR<0.90；rank==1 自动上岗衔接

## 执行日志（边查边写）

### 09:20 本地准备
- 任务中心确认 task-0390 running，sourceSession weixin
- 报告编号确认：现有最大 R-238 → 本报告 R-239

### 09:47 HP 实施与回测启动
- 备份：`scripts/a9_common.py.bak-a13-20260819-0940`（16694B 原件）
- a9_common.py E1 因子化补丁落地（patcher /tmp/patch_a13.py，py_compile OK）：
  - 位置：patch_engine NEW_B(ext 排序分支) 内，`_score = Σ w·rank` 后插入
  - 公式：`score -= e1_lambda × |clip(ret120, -1, 0)|`；`e1_deadzone>0` 时死区变体（仅 ret120<-dz 计罚）
  - cfg 开关：`e1_lambda`/`e1_deadzone`；e1_guard 硬排除保持独立（默认关，A13 候选设 0）
  - diff 摘要：+~1.2KB；grep e1_lambda=2 处（NEW_B 代码+docstring）；docstring 补 PE2 行
- runner `scripts/a13_run.py`：S0 市场加载+pb merge+q3z_tr → S1 equiv2 复检 → C1-C4 四候选（nohup 后台）
  - 候选：a13_rsraw_{e1f05,e1f10,e1f15,e1f10dz} = ranksum(log_mv⁻,amt20⁻,pb_inv0.7⁺,roe0.3⁺) × raw宇宙 × e1_guard=0 × e1_lambda∈{0.5,1,1.5}+dz0.3
  - xsub365 + q3z_tr(MA200,f0.30) + cost v2 + 一字板，与 a9_sel 完全同骨架
- **equiv2 复检 PASS（零回归）**：a13x_equiv_v5h locked 15.74%/-29.80%/0.998 ≡ a7_v5h_xsub，diffs={} 逐位一致 → E1 因子化补丁对旧路径(e1_lambda=0)无影响
- C1 结果：a13_rsraw_e1f05 full 22.28%/-33.55%/1.369 | locked 21.92%/-33.55%/1.351（vs a9_ranksum_raw E1硬 21.76%/-33.55%）
- 评分脚本 `scripts/a13_score.py` 已就位（py_compile OK）：复用 evolution_pipeline 的 gate_icir/deflated_sharpe/gate_mdd_vs_parent/score_composite（R-225 v1.1 口径），补建原始全市场月度 IC（pb_inv/ret120/mom_pen/mom_pen_dz，PIT），输出 a13_score_summary.json
- 关键评分口径：metrics=locked 窗；DSR 用 locked 净值日收益×n_trials_cum；g3 用月度IC序列Pearson（与 factor_ic_corr.csv 同源方法）；holdout 用 SHADOW_CONFIG(2024-07起, ann≥0.6×locked, MDD≤locked+10pp)

### 11:05 (重试恢复, 回测进程持续运行中)
- a13_run 进程 pid 253603 100% CPU 运行中, elapsed 14:29（启动约 10:48 北京）
- C2 a13_rsraw_e1f10 完成: full 22.08%/-33.55%/1.363 | locked 21.63%/-33.55%/1.341
- 已完成: equiv2 PASS, C1(e1f05), C2(e1f10)；剩余 C3(e1f15), C4(e1f10dz) 各约 346s
- 进度节奏: 每候选 ~346s, C3≈11:06, C4≈11:12 完成 → 随后跑 a13_score.py 评分

### 11:14 四候选全部完成（a13_run.py 1537s 全部完成）
- C1 e1f05: full 22.28%/-33.55%/1.369 | locked 21.92%/-33.55%/1.351
- C2 e1f10: full 22.08%/-33.55%/1.363 | locked 21.63%/-33.55%/1.341
- C3 e1f15: full 21.96%/-33.55%/1.355 | locked 21.63%/-33.55%/1.339
- C4 e1f10dz: full 22.39%/-33.55%/1.374 | locked 22.02%/-33.55%/1.356 （死区变体最优）
- 全部 locked MDD = -33.55%（与 a9_ranksum_raw 的 -33.55% 一致）
- 对照: a9_ranksum_raw(E1硬) locked 21.76%/-33.55%；a9_raw_universe(mv+E1硬) locked 21.76%/-36.78%
- 结论预判: E1 因子化在 λ∈{0.5..1.5} 全区间保留年化（21.63-22.02% vs 硬排除 21.76%），MDD 均 -33.55% 无恶化；
  死区变体 e1f10dz 年化最高 22.02% 且把动量惩罚集中在旧闸门域，是最优 E1 因子化形态
- 下一步: 补 ledger IT-A13-01..04 + 跑 a13_score.py 评分 v1.1

### 11:18 评分 v1.1 完成（n_trials=91，ledger IT-A13-01..04 已补，95 行）
补充IC: a13_supp_ic_monthly.csv 260月，pb_inv 247/260 非空（末月2026-08 n=0 常数告警，非系统性问题）；ret120 253/260

| 候选 | score | locked ann/MDD | holdout ann | g2p | DSR | corr(mc) | dd(pp) | rank_in_pool |
|---|---|---|---|---|---|---|---|---|
| **a9_ranksum_raw(翻案)** | **0.8670** | 21.76%/-33.55% | 25.84% | 0.4033 | 0.9999 | 0.6249 | 3.75 | **1** |
| a13_rsraw_e1f10dz | 0.8337 | 22.02%/-33.55% | 25.80% | 0.4719 | 0.9999 | 0.7555 | 3.75 | 1 |
| a13_rsraw_e1f05 | 0.8321 | 21.92%/-33.55% | 25.62% | 0.6562 | 0.9999 | 0.9426 | 3.75 | 1 |
| a13_rsraw_e1f10 | 0.8279 | 21.63%/-33.55% | 26.28% | 0.6562 | 0.9999 | 0.9426 | 3.75 | 1 |
| a13_rsraw_e1f15 | 0.8275 | 21.63%/-33.55% | 25.03% | 0.6562 | 0.9999 | 0.9426 | 3.75 | 1 |
| a9_raw_universe(mv) | 0.8061 | 21.76%/-36.78% | 20.09% | 0.272 | 0.9991 | N/A | 6.98 | 2 |
| a9_ranksum_quality(对照) | 0.7848 | 15.33%/-28.78% | 10.69% | 0.4033 | 0.9941 | 0.6249 | -1.02 | 4 |

- 排名池 n=6（registry 有 gate.score 非 partial 的 candidate/pending/active）：v4a_mf0_trr 0.8088 / v5k_nh10 0.8 / v5i_comb 0.7985 / v5j_bl30 0.7811 / v5b_amt55 0.7537
- **激活建议**：a9_ranksum_raw rank1(0.8670>0.8088)+stat_warn=False+holdout PASS → auto-activate 候选，建议激活（需用户确认）；未实际写 registry（激活权在主 agent/用户）
- 关键解释：
  - 四闸门去除的 alpha 主要来自 ranksum 四因子合成（ranksum_raw 0.867 vs mv-only raw 0.806：MDD 从 -36.78% 改善到 -33.55% 是决定性因素，dd 分 0.65 vs 0.004）
  - E1 因子化在 λ∈{0.5..1.5} 全区间保留年化(21.63-22.02%)与 MDD(-33.55% 恒定)，equiv2 零回归；但 corr 分量被 mom_pen 与在役 ret120 的高相关(0.94)压低（hard-guard 版用 ret120 与在役同源反而 corr 仅 0.62）
  - 死区变体 e1f10dz 是 E1 因子化最优形态（corr 0.7555 < 0.9426，score 0.8337 最高，locked ann 22.02% 最高）
  - 对照 a9_ranksum_quality（闸门不去除）score 0.7848 显著低于 raw 系 → 四闸门去除本身是 A13 价值来源之一
- 数据口径：metrics=locked 窗；DSR=locked 净值日收益×n_trials(91)；g3=月度IC序列Pearson；holdout=SHADOW_CONFIG(2024-07起)
- 产物：HP results/a13_score_summary.json (23.7KB)、a13_supp_ic_monthly.csv、a13_rsraw_{e1f05,e1f10,e1f15,e1f10dz}_{full,locked}_*
