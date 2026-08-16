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
