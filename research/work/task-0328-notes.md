# A4D notes task-0328
## 2026-08-16 A4D 进度
### 阶段0 IC 预检(全市场 W1口径, 已落盘 results/a4d_value_ic_precheck.csv)
- pe_ttm: mean_ic=-0.0386 icir=-1.038 cov=0.871
- pb: mean_ic=-0.0525 icir=-1.626 cov=0.960  (最弱: 低PB无正收益)
- peg_np: -0.0344/-1.337 cov=0.586
- peg_rev: -0.035/-1.318
- pegy: -0.0347/-1.288
- pcf_proxy: -0.0301/-0.968
- neff_val: -0.0166/-0.796
- buf_quality: +0.0035/+0.091 (中性)
- davis_dp: -0.0091/-0.573
- graham_score: +0.0004/+0.012 (中性)
- lynch_bucket: ~0
- 结论: 全市场截面价值IC弱/负(高PE小盘跑赢→可能被size混淆), 纯价值排序大概率伤收益;
  需在【回测宇宙=质量小盘过滤后】+【size中性】重算IC, 判断价值在宇宙内是否仍负/翻正
- 计划: v3系列候选必须含 blend(mv+价值) 与纯价值对照; 价值可能贡献MDD而非收益
### 阶段1 IC补充(宇宙内=质量小盘过滤 + size中性)
- 宇宙内: pe_ttm -0.0508/-1.37 | peg_rev -0.0568/-1.67 | neff -0.0482/-1.50 | peg_np -0.0497/-1.38 | pegy -0.0501/-1.43 | pb -0.0412/-1.01
- size中性: 仍全负 pe_ttm -0.0358/-0.56, peg_np -0.0475/-0.75; 唯 buf_quality +0.0076/+0.13, graham +0.0047/+0.08 (近0)
- 结论: 该宇宙(div>=2%, roe>15%, roa>10%, 小盘) 便宜=低收益, 成长/动量主导; 纯价值排序伤收益(呼应a2c v2f_lv教训)
- 候选策略: 价值必须BLEND(mv主+价值辅), 价值端提供MDD缓释与多样性; 候选含纯价值对照+blend+择时组合
- 候选集(v3系): v3a_peg(裸选股PEG blend) v3b_glm(裸选股Graham blend) v3c_peg_trr(+v2b择时) v3d_buf_trr(+v2b择时) v3e_peg_dd(+v2d dd) v3f_grm_trr(+v2b择时)
### 阶段3 正式回测结果 (full+locked 双窗口, 全量池+成本v2+一字板+审计锁)
等价校验: 原引擎 vs patched 开关全关 == 逐位一致 (full/locked nav exact, EQUIV_OK)
| 候选 | locked ann/mdd/sharpe | full ann/mdd/sharpe |
| v3a_peg (裸选股 PEG blend) | 24.72%/-72.10%/0.883 | 25.34%/-72.10%/0.915 |
| v3b_glm (裸选股 Graham blend) | 20.48%/-67.76%/0.757 | 21.24%/-67.76%/0.790 |
| v3c_peg_trr (PEG+q3z_tr) | 14.65%/-30.73%/0.964 | 14.74%/-30.73%/0.984 |
| v3d_buf_trr (巴菲特+q3z_tr) | 12.38%/-29.29%/0.808 | 12.50%/-29.29%/0.826 |
| v3e_peg_dd (PEG+q3z+dd) | 10.05%/-22.76%/0.932 | 9.79%/-22.76%/0.913 |
| v3f_grm_trr (Graham+q3z_tr) | 12.39%/-29.47%/0.819 | 12.51%/-29.47%/0.837 |
对照: v2b_trr(active) 15.15%/-29.86%/0.936 | v0_seed 26.26%/-69.49%/0.885 | v2d_dd 9.51%/-19.98%/0.857
结论: 无候选达标 25%/-20%/1.2; 价值blend未增alpha(v3a 24.72%<v0_seed 26.26%);
v3c_peg_trr Sharpe 0.964>v2b_trr 0.936 但年化/MDD略劣; v3e_peg_dd MDD -22.76% 最接近-20%
### 阶段3 收口(已落盘 summary: results/a4d_backtest_summary_none.json)
- 等价校验: 原引擎 vs patched 开关全关, full+locked nav 逐位一致 (EQUIV_OK)
- 6候选 × 2窗 = 60 结果文件 (a4d_<ver>_formal_{locked,full}_{metrics,nav,yearly,trades,holdings})
- 战役目标对照(locked): 目标 25%/-20%/1.2 → 全部未达标
  v3a_peg 24.72/-72.10/0.883 | v3b_glm 20.48/-67.76/0.757 | v3c_peg_trr 14.65/-30.73/0.964
  v3d_buf_trr 12.38/-29.29/0.808 | v3e_peg_dd 10.05/-22.76/0.932 | v3f_grm_trr 12.39/-29.47/0.819
- 判读: 价值blend未增alpha(v3a 24.72 < v0_seed 26.26; v3c 14.65 < v2b_trr 15.15);
  v3c_peg_trr Sharpe 0.964 > active 0.936 但年化/MDD略劣; v3e MDD -22.76 最接近-20但年化仅10.05
### 阶段4 五门禁结果 (n_trials 51→57, 扩展IC: a4d_ic_monthly_ext)
| 候选 | g1 | g2 | g3 | g4 DSR | g5 | g6 | 裁决 |
| v3a_peg | FAIL 0.342 | FAIL | PASS | FAIL 0.729 | PASS | FAIL | REJECT |
| v3b_glm | PASS 0.561 | PASS | PASS | FAIL 0.497 | PASS | FAIL | REJECT |
| v3c_peg_trr | FAIL 0.342 | FAIL | PASS | PASS 0.9925 | PASS | PASS | REJECT |
| v3d_buf_trr | PASS 0.575 | PASS | PASS | PASS 0.9587 | PASS | PASS | PASS→pending |
| v3e_peg_dd | FAIL 0.342 | FAIL | PASS | PASS 0.997 | PASS | PASS | REJECT |
| v3f_grm_trr | PASS 0.561 | PASS | PASS | PASS 0.9647 | PASS | PASS | PASS→pending |
- 关键: peg系候选(v3a/v3c/v3e) g1/g2 FAIL —— PEG因子IC为负(阶段0/1已证: 该宇宙价值IC全负), 复合ICIR被拖垮
- graham/buf系(PEG-free价值) ICIR 0.56-0.58 过线; v3d/v3f 六门全PASS
- 战役目标对照: 全部未达 25%/-20%/1.2; v3d/v3f PASS但不严格优于active v2b_trr(年化12.4<15.15, SR 0.81<0.94) → 不activate
- 决策: 0 activate; 2 PASS留pending; D-20260816-A4D-01 批次收口
