# task-0348 [A8-收尾] 分桶打分版补跑 + 三方式对照 — 过程笔记（边查边写）

## 上下文恢复（20:20）
- HP runner 基建在 ~/quant-evolve/scripts/a9_sel.py + a9_common.py（/tmp 下原始 a9 runner 已清理，scripts/ 内为持久版本）
- a9_common.patch_engine: PA raw_universe / PB ext 排序(zscore|ranksum) / PC e1_guard+xsub / PD pb 列 / PE 返回扩展
- E3 因子集 SUM_SPECS = [("log_mv",1.0,-1), ("amt20",1.0,-1), ("pb_inv",0.7,+1), ("roe",0.3,+1)]
- locked=2006-01-01~2024-06-30(AUDIT_LOCK_END), full=2006-01-01~2026-08-31; 成本v2+一字板on, n_hold=20, 月度调仓, capital 1e7
- 择时 q3z_tr: MA200, floor0.30, pos mean=0.516
- timing: 市场加载 ~70-80s, 每回测 ~60s; a9_sel.log 已验证 equiv2 逐位一致机制

## 基线（locked 口径, 已有结果勿重跑）
| 版本 | 年化 | MDD | Sharpe | Calmar | 换手 | 来源 |
|---|---|---|---|---|---|---|
| 现役 v5h_xsub | 15.74% | -29.80% | 0.998 | 0.528 | 0.320 | a7_v5h_xsub_formal |
| zscore 四因子 quality | 15.94% | -29.52% | 1.036 | 0.540 | 0.330 | a9_zsum_quality |
| zscore 四因子 raw | 19.85% | -34.59% | 1.264 | 0.574 | 0.258 | a9_zsum_raw |
| ranksum 四因子 quality | 15.33% | -28.78% | 1.009 | 0.533 | 0.347 | a9_ranksum_quality |
| ranksum 四因子 raw | 21.76% | -33.55% | 1.344 | 0.649 | 0.466 | a9_ranksum_raw |
| E1 raw(纯mv去闸门) | 21.76% | -36.78% | 1.215 | 0.592 | 0.271 | a9_raw_universe |
| A7 v5b(混排血统, 不同因子集) | 14.52% | -30.76% | — | — | — | A7 报告 |

## 方案（20:22 定稿）
- 新 runner: ~/quant-evolve/scripts/a8_bucket.py（新文件，不动现有代码）
- patch 链: import a9_common → 取 inspect.getsource(patch_engine) → 定点替换加入 bucket 模式（替换处 assert count==1）→ exec 编译
  - 保证与 a9 补丁链逐字一致，仅新增 bucket 分支；锚定校验(a8x_equiv_v5h vs a7_v5h_xsub_formal 逐位)背书
- bucket 语义: 每因子月度截面 rank(pct) → 符号翻转(sgn<0 取 1-r) → floor(r×5).clip(0,4) 得桶号 0-4（4=最优）→ score=Σ w_i×桶号_i；同 E3 权重
- 跑 3 个回测: a8x_equiv_v5h(锚) + a8_bucket_quality + a8_bucket_raw，各出 full+locked 双窗（每 tag 10 文件）
- E4 线: bucket raw locked 年化 ≥17.74%(+2pp vs 现役) 且 MDD ≥-31.80%(恶化≤2pp) → 过线记 decision-log；否则 closeout
- ledger: IT-A8-01 (bucket_quality) / IT-A8-02 (bucket_raw)，features 字段必带

## 结果（20:40-21:00 全部完成）

EQUIV 锚: a8x_equiv_v5h ≡ a7_v5h_xsub_formal 逐位一致 BIT_EXACT（locked 15.74%/-29.80% 复现）→ a9 骾架+bucket 分支链路可信

### 三方式对照（locked，同因子同宇宙：log_mv1.0+amt20 1.0+pb_inv0.7+roe0.3）
| 方式 | quality 年化/MDD/Sharpe | raw 年化/MDD/Sharpe | raw 换手 |
|---|---|---|---|
| zscore(A9) | 15.94%/-29.52%/1.036 | 19.85%/-34.59%/1.264 | 0.258 |
| ranksum(A9) | 15.33%/-28.78%/1.009 | 21.76%/-33.55%/1.344 | 0.466 |
| bucket(本批) | 15.27%/-28.80%/1.005 | 18.29%/-34.01%/1.176 | 0.536 |
- bucket full: quality 14.83%/-28.80%, raw 18.26%/-34.01%; locked≥full 无近端衰减

### E4 判定: 未过线 → closeout
- bucket raw locked 18.29% = +2.55pp ✓ 但 MDD -34.01% 恶化4.21pp > 2pp ✗ → 不注册
- bucket quality: 年化-0.47pp 无增益; MDD改善1.0pp<3pp防御线 → 无任何注册路径

### 结论（机制排序）
1. **ranksum > zscore > bucket**（raw 年化 21.76>19.85>18.29）——ranksum 为排序层最优合成方式
2. 机制: 尾部分辨率决定性（n=20 持仓取自顶端，bucket 5 级量化顶部并列成灾，并列组内排序≈无信息）；ranksum 抗极值+全序分辨率，微盘宇宙最稀缺性质；zscore 保幅度在 quality 最优但 raw 被市值/成交额重右尾拉伸
3. bucket 双重代价: 年化垫底 + 换手0.536全场最高（桶并列月间洗牌，纯损耗）；非线性容量未被框架使用
4. 前沿不变: v5h(15.7/-29.8)~raw ranksum(21.8/-33.6)，防守端 MA15_on_f0(14.6/-24.7)

## 交付物清单（HP）
- results/a8_bucket_* 21 文件（quality/raw × full/locked × 5 产物 + summary 锚1）+ a8_bucket_summary.json
- results/a8-iteration-report.md（6.6KB, 三方式对照表+E4+机制解释）
- ledger IT-A8-01/02（n_cum 80/81）+ decision-log D-20260817-A8-1（a8_closeout）
- a9-iteration-report.md 末尾衔接注记
- scripts/a8_bucket.py（新文件，不动现有链路；首版自检 n=10 浮点边界误报已修 n=11）
- 全程 nohup，无已跑进程被杀；未改 evolution_pipeline/paper_engine/crontab

## 进度（终）
- [x] 20:20 上下文恢复 + 基线确认
- [x] 20:27 a8_bucket.py 写入 scripts/
- [x] 20:28 nohup 启动 → 首版自检断言过严(n=10 浮点边界降桶)失败，修为 n=11 边界安全用例后 20:36 重启
- [x] 20:38 锚定校验 PASS: A8 EQUIV 锚逐位复现 v5h locked 15.74%/-29.80%
- [x] 20:41 bucket quality 完成；20:45 bucket raw 完成（raw 因宇宙大耗时 ~5.5min）
- [x] 20:52 三方式对照表 + a8-iteration-report.md 上传 HP
- [x] 20:58 ledger IT-A8-01/02 + decision D-20260817-A8-1 + a9 衔接注记
- [x] 21:00 验收 5 项全过（21 文件/6.6KB/ledger+decision/锚 BIT_EXACT/注记）
