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
