# task-0508 notes — R-328 PEAD 负惊喜软惩罚线 E2 执行判门

开始: 2026-08-27 13:48 GMT+8（VPS 本地离线执行，禁 SSH HP，零生产影响）
预注册依据: R-328（sha256=3054c9ed80f33d6ab6bf03098690356771eac259b9ca5f4a04cda99f2a5e0483 已验一致，15,643B 全文精读）

## 输入资产盘点
- `work/r274/events_sue.parquet` 8.6MB：257,055 事件 / cols=[code,report_date,net_profit_ttm,avail_date,qidx,sue_std,sue_pct]（avail_date 为 R-274 法定期限代理版，本任务不用，以 EM NOTICE_DATE 重算）
- `work/r274/kline_monthly.parquet` 13.9MB：728,612 行 / cols=[ym,close,amount,amt20,outstanding_share,td_cum] / ym 2006-01~2026-08 / amt20 单位=元(20日均成交额, median≈0.80亿)
- `/tmp/r324_notice.jsonl` 8.93MB：EM F10 NOTICE_DATE 库（OK/EMPTY/FAIL 行式），codes 见运行日志
- 冻结管线脚本: `/tmp/r324_compute.py`（R-324 主计算，E2 在其基础上扩展）+ `/tmp/r274_vps/r274_v2.py`（W1 口径源头）
- 机读锚: `work/r324/summary_r324.json`（G0 判据源）+ `work/r324/disclosure_dist.json`（T1 对照源）

## 基准打分实现口径（报告须照实披露）
在役四因子合成沿 R-278/R-263 脚本冻结约定 SUM_SPECS=[log_mv w1 dir−1, amt20 w1 dir−1, pb_inv w0.7 dir+1, roe w0.3 dir+1]
→ E2 基准打分 base_score = 截面标准化后按权重×方向求和、再截面 zscore；
合成 s = z(base) + λ·z(G_resid)（λ∈{0.15 V1/V2 0.30}）；spearman IC 下 rank 与加权排序等价披露。
组合层口径（G4/G5 用）：top-N 等权多头月频重估，N=100 主口径 + N∈{20,50} 稳健性披露；
换手 t_m = 1 − |S_m∩S_{m−1}|/N；增幅%=(TO_V1−TO_V4)/TO_V4。
容量: 月度容量 = 10%×当月入选持仓 ADV20(amt20) 中位数；全样本月度容量的中位数 ≥2000 万判 PASS，最小值另报。

## E2 判门核验清单（先于计算登记，逐项回填 PASS/FAIL）
- [ ] G0 锚校验（先决）: 复算 ic_sue(mixed PIT) vs summary_r324 selfcheck_sue_std_full(n232 mean+0.0128 icir0.131 t2.00)；阈值: mean 相对偏差≤5% 且与落盘 r324/ic_selfcheck_sue.csv 序列 corr≥0.999 → [待填]
- [ ] G1 正交增量确认（主判据）: mixed G_resid 月度 IC mean>0 且 t≥2 且与锚 +0.0152 同号 → [待填]
- [ ] G2 组合层增量门: ΔIC(IC(s)−IC(V4)) >0 全时段合计；分年正号占比照实披露（V1 λ0.15 为主判定对象，V2/V3 一并披露）→ [待填]
- [ ] G3 分段门: ΔIC 以 ~2019 年中分两半段，两段不同时为负即 PASS → [待填]
- [ ] G4 turnover 门: (TO_V1−TO_V4)/TO_V4 ≤10%（N=100 主口径）→ [待填]
- [ ] G5 容量门: 月度容量中位数 ≥2000 万（10%×ADV20 中位数）→ [待填]
- [ ] G6 相关性/独立性: 影子期正式检验（E2 仅报打分层截面相关性参考值 + deferral 声明）→ [待填]

## 终止开关状态
- [ ] T1 数据污染: 本次 lag 直方/src_counts 程序化对照 disclosure_dist.json（缓存未变质确认）→ [待填]
- [ ] T2 双口径背离: mixed vs strict only-real 的 G_resid IC 符号相反或任一 t<2 → 终止归档 → [待填]
- [ ] T3 影子期劣化: 影子期事项，E2 阶段 N/A（影子期未开始）→ [待填]

## 变体计划（n_trials=4 显性计数）
- V1 主试验: λ=0.15, mixed 面板
- V2 强度敏感性: λ=0.30, mixed 面板
- V3 面板敏感性: λ=0.15, strict only-real 面板（fallback 事件整体剔除）
- V4 无惩罚基准对照: λ=0（Δ 指标分母）

## 计算脚本与原始输出路径
- E2 脚本: /tmp/r328_e2.py（复刻 r324_compute.py 数据层+扩展组合层，禁止改清洗带/阈值/λ）
- 运行日志: /tmp/r328_e2.log；结果 JSON: work/task-0508-out/e2_summary.json；逐月序列 csv 同目录

---

## 执行流水记录

[13:49] G0 判定开始：复算管线跑通前先建清单如上。

[13:55-14:00] 第一次运行 /tmp/r328_e2.py（数据层逐行复刻 r324_compute.py；扩展=strict 面板+组合层）。前置门结果：
- **T1 PASS**：`t1_distribution_check.json` 直方 9 桶与 src_counts 三类全部逐项相等基线 disclosure_dist.json；real_cover_now=0.8169 == 基线。缓存未变质。
- **G0 PASS**：复算 ic_sue n=232 mean=0.0128 icir=0.131 t=2.00，对锚相对偏差 0.022%（≤5%），与落盘 r324/ic_selfcheck_sue.csv 序列 corr=1.000000（≥0.999）。（原始输出 `out/g0_ic_selfcheck.csv`）
- **G1 PASS（主判据）**：mixed G_resid n=147 mean=+0.0266 ICIR=0.359 t=4.35 —— mean>0 ✓、t≥2 ✓、与铏 +0.0152 同号 ✓，且与 summary_r324.json C2_resid_ic 逐位一致。（原始输出 `out/g1_gresid_mixed.csv`）
- **T2 未触发**：strict only-real G_resid n=133 mean=+0.0249 ICIR=0.334 t=3.85 —— 双口径同号且均 t≥2。（原始输出 `out/gresid_strict.csv`）
- 数字溯源核对：上述四项与 R-324 正文表「C2 mixed +0.0266/4.35(n147) | strict +0.0249/3.85(n133)」完全一致 → 数据层复刻无漂移。

[14:01] bug#2 定位：composite_panel 用 base.add(RZ) 无 fill_value → RZ 中无残差格 NaN 传播，V1 面板被动缩小为残差子集（n=147）而 V4 为全池（n=232），IC 对比不同池不公平，ΔIC 伪负。修复：add(RZ.fillna(0))——无增量信息股票保持基准打分，符合「微扰」语义。此为修实现错误非救结果：修复后若 ΔIC 仍<0 则如实 FAIL 归档。14:08 第三次全量重跑（前两遍 A/B 段数字逐位一致，确定性复现良好）。

[14:13] bug#2 真根因定位（重要教训）：pandas 3.0.5 的 DataFrame.add() 对非交集行填 NaN 而非透传左值——上次修复（fillna(0) 列内）未处理 RZ 行缺失，V1 有效月仍 147、G4/G5 数字与上遍逐位相同引发怀疑。已用最小单测验证新方案：RZ.reindex(index=months, columns=cols).fillna(0) 再 add → 非残差月/股完全保留 base 原值（UNIT_TEST_OK）。教训：面板对齐语义必须单测先行；第二轮结果与首轮逐位相同反而是「修复未生效」的信号，该敏感处理。
[14:16] 第四次全量重跑启动（/tmp/r328_e2.log）。裁决纪律声明：本次为修正不公平对照的实现错误（不同池 IC 不可比），非调参救结果；若修复后 ΔIC 仍 <0 则如实 FAIL 归档。
