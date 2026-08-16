# task-0333 A5 notes (growth×quality + momentum guard + value downgrade + v2b timing)
[2026-08-17 01:3x GMT+8] start. Phase 0 in progress.

### 阶段0 基线核对 (2026-08-17)
- v2b_trr locked (a2c 重跑文件): 15.15%/-29.86%/0.936 ← 与任务书一致, 基线OK
- v2b_trr full: 待查 (与strecheck对照)
- a4d 报告结论已核: 价值IC全负(ICIR -1.3~-1.7), buf_quality唯一近零(+0.091); E1砍20.8%尾部亏损误杀12.1%赢家; G1 avg+21.2%/胜率78.4%; Calmar不变式=选股层真alpha必须

### 阶段1 因子预检 (a5_gq_ic_monthly.csv, W1口径, 248月 2006-01~2026-08)
- 方法学验证: buf_quality 全市场 IC +0.0035/+0.091 与 a4d 报告完全一致 → 口径可复现
- 成长x质量复合 (univ=质量小盘宇宙, mean n=88):
  grw(营收+利润yoy)  full -0.0165/-0.747 | univ -0.0422/-0.989 (负)
  qly(buf_quality+cf_np) full +0.005/+0.171 | univ -0.0068/-0.134
  gq(grw+qly)         full -0.0027/-0.11  | univ -0.0265/-0.62  (负)
  gqmv(0.5gq+0.5mv)   full -0.008/-0.286  | univ -0.0235/-0.466 (负)
  mv_neg              full -0.0274/-0.528 | univ -0.0127/-0.163
- 判读: 成长x质量复合在宇宙内 IC 为负(ICIR -0.62), 未确认 > 纯mv增量空间。
  但: (1) 纯mv的月度线性IC亦非正(尾部选择效应≠线性IC), v0_seed 26%证明mv排序在回测有效;
  (2) 本批主机制=E1动量护栏+G1加强(均有postmortem实证), 不依赖成长x质量IC;
  (3) 成长x质量作次要tiebreak/轻权重blend, 保留mv主权重。
  → 候选设计: mv主权重>成长x质量权重; 保留任务骨架但注明IC预检未确认, 以回测为准。

### 阶段2/3 启动 (2026-08-17 18:08)
- a5_runner.py 已部署 /tmp/a5_runner.py (18120 B), 基于 a4d_runner 机制, 新增 P8(mom_lookup) + P9(sort=gq 含 E1/G1/PEG)
- 候选5个: v4a_gqe1(0.6mv+0.4gq+E1+q3z_tr) / v4b_mve1(纯mv+E1+q3z_tr对照) / v4c_gqpeg(+PEG<2) / v4d_gqg1(0.5+0.5+G1加分+q3z_tr) / v4e_gqg1x(同d无择时)
- 等价校验前置: 原引擎 vs patched 开关全关 逐位一致
- 先 screen(2016-2026) 验证, 再 formal(full+locked)

### 阶段3 正式回测 interim (2026-08-17, formal mode, EQUIV_OK 全过)
- v4a_gqe1 (0.6mv+0.4gq+E1+q3z_tr): locked 10.74%/-31.31%/0.744 | full 10.79%/0.755
- v4b_mve1 (纯mv+E1+q3z_tr 对照): locked 12.42%/-28.99%/0.840 | full 12.31%/0.843
- v4c_gqpeg (gqe1+PEG<2): locked 10.36%/-33.68%/0.723 | full 10.37%/0.730
- v4d_gqg1 (0.5+0.5+G1+q3z_tr): locked 11.59%/-29.67%/0.796 (进行中)
- 观察: 纯mv+E1(v4b) MDD -28.99% 与现役v2b_trr(-29.86%)相当且年化略降; 成长x质量blend未增alpha(与IC预检一致)
