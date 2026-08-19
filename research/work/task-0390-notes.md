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
