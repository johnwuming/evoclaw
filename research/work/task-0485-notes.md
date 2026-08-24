# task-0485 过程笔记（黄金趋势引擎激活实施 R-307）

时间预算：≤40 分钟实施 + 报告。硬上限 1h。边查边写，证据落此文件。

## 基线研读（VPS 侧）

- R-306 四件套在位（VPS hp-cron-pending/）：gold_shadow_evaluate.cron（5 字段，3 日 09:38 append + 09:40 evaluate 两行）、gold_mmf_push_vps.cron（VPS 每月 2 日 09:00 push）、gold_mmf_push.py、INSTALL.md。
- INSTALL.md 要点：HP 装 cron 前 `crontab -l > /tmp/ct.bak`；gold 2 行；VPS MMF 1 行（source secrets.env）；回滚 = tar(076eeaea… 67项) + 删 B 条目 + 删脚本 + 删 results/engines/gold/。
- R-305 冻结形态（e2_backtest.py 逐行核读，V1=w1_sig=dir200×vt10）：
  - m=月末收盘（日 close resample ME last）；sma200=日 close rolling(200).mean() 取月末值
  - dir200 = 月末 px > sma200 ? 1 : 0
  - vol60 = 日 pct_change rolling(60).std() × sqrt(252)（60 交易日已实现波动年化；任务书"24月"为笔误，冻结代码以 vol60 为准，G0 锚 voltarget corr 1.0 亦为证）
  - vt10 = (0.10/vol60).clip(0,1)；w1_sig = dir200×vt10
  - 执行：w = w_sig.shift(1)（t 月末信号 → t+1 月执行）；gross = w×mr + (1−w)×mmf_m；cost=|Δw|×0.0013，首月建仓也计成本
  - mmf_m = 000198 万份收益→日ret→resample ME 复利
- E2 关键数字（e2_gates_result.json 落盘，禁止心算）：V1_net ann=0.07590979342573179, mdd=−0.05901780820817082, calmar=1.2862184437276736；G6 corr=−0.0400（n=131）；cost_model="abs(dw)*0.0013 per month (one-way 0.10% + spread 0.03%, frozen)"。
