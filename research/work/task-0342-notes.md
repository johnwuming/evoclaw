# task-0342 A9 收口笔记（边查边写，报告唯一取材源）

## 0. 背景与复刻口径（来自 HP /tmp/a9-notes.md，18:3x 前任进程已校验）
- v5h 复刻口径：质量四闸门 + ext mv[1,0](amt20 notna, a2c 兼容) + e1_guard(120日收益<-30%出池) + xsub365(日历天) + q3z_tr(w_min0.3 EWM0.3 × 池内EW指数MA200破位×0.6, 自然下限0.18)
- locked = 2006-01-01~2024-06-30 (AUDIT_LOCK_END)；full = 2006-01-01~2026-08-31
- 成本 v2 + 一字板 on, n_hold=20, 月度调仓, capital 1e7
- E1 等价校验：equiv2 逐位一致 PASS（patch 链可信）；equiv1 a2c 参考小幅漂移，降级为警告（a2b/a2c 血统参考自身问题，与本次链路无关）
- E2 锚定校验：MA200_on_f30 ≡ v5h 逐位一致（locked 15.74%/-29.80%/0.998/0.528）✓

## 1. E1 原始宇宙对照（a9_raw_universe_{full,locked}）
- locked: 21.76% 年化 / -36.78% MDD / Sharpe 1.215 / Calmar 0.592
- full: 21.58% / -36.78% / 1.200
- vs v5h locked (15.74%/-29.80%/0.998/0.528)：年化 +6.02pp、Sharpe +0.22、Calmar +0.06，代价 MDD 恶化 6.98pp
- E4 新血统线（年化+2pp 且 MDD 恶化≤2pp）：未过（6.98pp ≫ 2pp）→ 不注册
- 结论：四闸门 = 真实的"安全换收益"交易；locked 年化(21.76) > full(21.58) → 近端无衰减迹象
- 原始宇宙前沿点 21.8%/-36.8%，距 25%/-20% 双目标仍无交点

## 2. PB IC 宇宙差异裁决（a9_pb_ic_summary.json, 月频 IC, W1 口径, PIT=avail_date）
- 质量闸门内: mean_IC 0.0313 / ICIR 0.196 / 正率 60.6% / n=221月 / 近12月 0.0042（≈失效）
- 原始全宇宙: mean_IC 0.0576 / ICIR 0.521 / 正率 71.7% / n=247月 / 近12月 0.0324（仍有效）
- 原始微盘底20%市值: mean_IC 0.0487 / ICIR 0.537 / 正率 69.2% / 近12月 0.0007（近端失效）
- a4d 参考: pb 原方向 mean_IC -0.0525 (ICIR -1.626, 方向-1)，质量宇宙内 -0.0412 → pb_inv 取反后即为本次口径
- 裁决：
  1) PB 价值 alpha 主要藏在被四闸门砍掉的原始宇宙（ICIR 0.521 vs 0.196，差 2.7 倍）
  2) 微盘贡献了原始宇宙 IC 的主要部分（0.0487/0.0576），但近 12 月微盘 IC 归零（0.0007），近端 PB alpha 来自非微盘段
  3) 质量宇宙内 PB 近端 IC ≈ 0 → v5h 现役排序里再加 pb 权重的边际收益低（与 E3 quality 结果互证）

## 3. E3 排序合成贡献（a9_ranksum_{quality,raw}_{full,locked}，specs=mv1.0+amt1.0+pb_inv0.7+roe0.3）
- quality locked: 15.33% / -28.78% / 1.0092 / 0.5325（月胜率 61.5%，换手 0.347，222 次调仓）
- raw locked: 21.76% / -33.55% / 1.3435 / 0.6485（月胜率 65.2%，换手 0.466）
- 对照 v5h locked 15.74%/-29.80%/0.998/0.528：
  - quality: 年化 -0.41pp、MDD 改善 1.02pp → 加 pb_inv 在质量宇宙内无实质增益（微幅换收益，不过任何注册线）
  - raw: 年化 +6.02pp、MDD 恶化 3.75pp → 未过新血统线（3.75pp > 2pp），但优于 E1 raw 的 MDD（-33.55% vs -36.78%），即"排序合成+闸门外价值暴露"比"纯去闸门"多省 3.2pp 回撤、年化持平
- E3 full 口径：quality 14.86%/-28.78%/0.9945/0.5165；raw 22.16%/-33.55%/1.3624/0.6605（full>locked，无近端衰减）
- E4 新血统判定：E3 两版均不满足

## 4. E2 择时网格（a9_timing_grid_table.csv，40 组全 = MA{15,20,50,100,200} × q3z{on,off} × 地板{0,10,18,30}，full+locked 双口径全行有值 → 判定完整，无需补跑）
- 基准 v5h = MA200_on_f30 locked 15.74%/-29.80%/0.998/0.528
- 过"防御注册线"（MDD 改善≥3pp 且年化损失≤2pp）的组合：
  1. MA15_on_f0: 14.63% / -24.67% / 1.0412 / 0.5931 → MDD +5.13pp，年化 -1.11pp ✓（最优）
  2. MA20_on_f0: 14.58% / -24.67% / 1.0284 / 0.5909 → MDD +5.13pp，年化 -1.16pp ✓
  3. MA15_on_f18: 14.65% / -25.83% / 1.0386 / 0.5672 → MDD +3.97pp，年化 -1.09pp ✓
  4. MA20_on_f18: 14.60% / -25.84% / 1.0255 / 0.5651 → MDD +3.96pp，年化 -1.14pp ✓
- 次级发现（不过 3pp 线）：MA200_on_f0 = 15.37%/-27.34% → 仅放松地板(0.3→0) 省 2.46pp 回撤、损 0.35pp 年化
- 反例/证伪：
  - 外部"MA15+空仓压 MDD 到 -17%"证伪：q3z off（纯趋势可空仓）全部 MDD -38%~-52%（MA15_off_f0 = 19.88%年化但 -38.01% MDD）
  - A7b"MA 缩短恶化回撤"仅在 f30 档成立（MA15_on_f30 -31.19% 劣于现役）；放松地板后反转，快线+低地板 = 最优 MDD 控制
  - f0 与 f10 行为逐位一致（q3z 平滑序列很少低于 0.10）→ 有效地板档位实际只有 {0/10, 18, 30} 三档
- 网格裁决：快线救回撤的前提是叠加 q3z 估值压缩且放松地板；纯快线趋势跟踪（空仓）在本宇宙 = 高收益高回撤赌注

## 5. E4 综合判定（按任务书新血统线：年化+2pp 且 MDD 恶化≤2pp vs 15.74%/-29.80%）
- E1 raw: +6.02pp / MDD 恶化 6.98pp ✗
- E3 raw: +6.02pp / MDD 恶化 3.75pp ✗
- E3 quality: 年化 -0.41pp ✗
- E2 最优组 MA15_on_f0: 年化 -1.11pp ✗
- → **无候选过新血统线，不注册 v6a，走 a9_closeout**
- 但 MA15_on_f0 等四组过"防御线"（MDD≥3pp 改善且年化损失≤2pp）→ 作为记录性备选操作点写入 closeout 与 ledger，不注册血统
- 前沿表述：现役 v5h (15.7%/-29.8%) 与 raw 系 (21.8%/-36.8%) 构成当前可达前沿两端；MA15_on_f0 (14.6%/-24.7%) 在左下方新增一个防守端点；25%/-20% 双目标仍不可达

- 台账/日志位置：results/experiment-ledger.jsonl（77 行，末行 IT-A7-09 n_trials_cum=75，data_snapshot hash bcf45e9f kline 2026-08-10）；model/decision-log.jsonl（49 行，格式 ts/decision_id/type/version/trigger/metrics/expected_impact/rollback_condition/code_ref/files）；model/registry/（v0~v5i，v5h_xsub 现役，本批不新增）
- ledger IT-A9 计划 4 行：01=E1 raw(REJECT)、02=E3 raw(REJECT)、03=E3 quality(REJECT)、04=E2 最优 MA15_on_f0(REJECT 新血统/记录防御备选)，n_trials_cum 76-79
- decision-log：D-20260817-A9-1 type=a9_closeout

## 6. 待办
- [x] E2 完整性判定：40/40 组全，无需补跑
- [ ] 读 E3 full 两版 metrics（补录）
- [x] HP ledger IT-A9-01..04 已写入（81 行，n_trials 76-79）
- [x] HP decision-log D-20260817-A9-1 a9_closeout 已写入（50 行）
- [ ] HP results/a9-iteration-report.md >4KB
- [ ] VPS R-222 报告 ≥3KB + README 变更记录
- [ ] VPS .task-completions.jsonl
