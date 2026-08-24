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

## 步骤1：paper_engine_gold.py（自包含 paper 引擎）

- 写 VPS scripts/paper_engine_gold.py（本地留档）→ scp 子系统被 HP 拒（subsystem request failed），改 ssh cat 管道落 HP ~/quant-evolve/scripts/paper_engine_gold.py。
- md5 双侧一致：5cfddb6cd763029bd9a140aac3a73d80；HP py_compile OK（16474B）。
- 设计：--action init/daily/monthly/verify；state=results/engines/gold/paper_state.json；NAV=1.0 激活新链（理由：157 月模拟史由 shadow 监控链继续承载，两链并存互证；避免 shadow 8-31 部分月（至 8-24）存根混接双记账；paper 增量全部可归因）。
- 信号代码与 engines_shadow_nav_gold.py / r483 e2_backtest.py 逐行同构（fetch_gold_daily / compute_signals 原样复制）。
- 单测（VPS 离线合成数据）：①正常月结 net=gross−cost 逐位 ✓ ②MMF 断供→估计路径有限值 ✓ ③mmf_est 月推送到达后重述+NAV 链重算 ✓ ④月中标记有限值 ✓。
- 冻结口径重要发现（如实披露不改）：月末标签 reindex 精确匹配——非交易日月末（周末）SMA200=NaN→dir=0→w=0；实测冻结数据 158 月末标签中 61 个非交易日月末，dir200 非零=64，恰等于 R-305「在场 64/157 月」。此为 E1/E2/影子链一致行为，paper 引擎逐位复刻（一致性优先），已在报告风险节披露。
- 当前信号预核（冻结数据）：2026-07-31（周五交易日）px 8.4330 < SMA200 9.4791 → 8 月 w=0（与 seed 一致）；2026-08-31 为周一交易日，9-01 调仓将按届时数据算信号（8-24 px 9.564 已逼近 SMA200 ~9.48）。

## 步骤2：registry 激活（HP）

- 前置 tar：model/registry_backup_task0485_20260825.tar.gz（67 项，sha256 e8b7347c262fb100a317…）。
- 写前 sha 83c47f3a6529a574（12908B，= R-306 baseline 后链续）→ 写后 sha 0f2148a8e614650f（14649B）。
- 变更：gold status shadow→active、type standalone_shadow→standalone_active、name 去「影子观察」、layer1.registry.note 更新、新增 promotion 节（activated_at 2026-08-25T00:35+08:00、批准人、影子期豁免语境、baseline_evals 全部取自 shadow.evals[0] 落盘值零手抄：corr −0.040013346299740626 n=131、ann 0.07590979342570381、mdd −0.05901780820812119、calmar 1.286218443728281、157 月；scope 显式「真金分配不在本次范围」；monitoring_note=evaluate 语义转正式监控）。
- 写后三重校验全过：A_deep_equal=True、A2_deep_equal=True、gold_active=True、json 合法、engines=[A,A2,gold_trend_sma200]。

## 步骤3：cron 安装（按 INSTALL.md，纯增量）

- VPS MMF dry-run 先行：gold_mmf_push.py → 2026-07 月收益 0.000718079382561（与 seed 逐位一致），未真推。
- VPS crontab：备份 /tmp/vps_crontab_backup_task0485_20260825.txt → 追加注释+1 行（0 9 2 * * source secrets.env; python3 gold_mmf_push.py --push）→ `crontab -l | grep -c mmf`=1 ✓；diff 仅 2 新增行。
- HP crontab：备份 ~/crontab_backup_task0485_20260825.txt（33 行）→ 追加注释+2 行（3 日 09:38 append / 09:40 evaluate，5 字段原样）→ `crontab -l | grep -c gold`=3（2 cron 行+1 注释）✓；diff 仅 3 新增行（33a34,36），既有 33 行零改动 ✓。logs/ 目录 mkdir -p 保障。
- evaluate 语义激活后转正式监控：cron 注释行与 registry promotion.monitoring_note 双处标注。

## 步骤4：首跑 init + 幂等 + verify（HP 实测输出）

- init --dry-run：fetch 腾讯 3179 根（2013-07-29..2026-08-24）；signal@2026-07-31 px=8.4330 sma200=9.4791 vol60=0.2201 w=0.0000（与 VPS 冻结数据预核逐位一致）。
- init（真跑）：state 落 results/engines/gold/paper_state.json（1665B）；month=2026-08 stub=True；mmf_daily_est=0.00002316（src 2026-07-31 推送）。
- daily 首跑：mark 2026-08-24 nav=1.000000（基准日=8-24，0 天）；daily 二跑：[dup: 未重复记账] 幂等 ✓。
- verify：w match=True / nav_chain=True / nav_open=True / marks=True / months_closed=0 ✓。
- state 摘录：current_weight=0.0、last_rebalance=2026-08、open.nav_open=1.0、marks=1、audit=1、last_signal 如上、json 合法。

## 在役零改动总证明

- registry：A/A2 写前/写后 deep-equal True（见步骤2）；sha 83c47f3a…→0f2148a8… 仅 gold 条目+顶层重排。
- HP crontab：diff 33a34,36 纯新增。
- 引擎文件：paper_engine_gold.py 纯新文件（md5 5cfddb6c…），未 touch evolution_pipeline.py / 在役 paper_engine.py / engines_shadow_*（gold 自有）。
