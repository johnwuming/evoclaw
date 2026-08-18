# R-234 n_trials 补账报告（E2 择时网格 / A7c 画像 / 现金曲线）

- 任务号：task-0363（信用项，研究+登记）
- 日期：2026-08-18
- 性质：n_trials 试验预算补账（R-226 P1 / A10-5 落地第一步）；只读核对为主，未改 production 代码
- 交付：`n_trials_ledger.csv`（本目录）+ 本报告

## 一、背景与目标

R-226 P1 指出：**E2 40 组择时网格 / A7c 画像 / 现金曲线均未计入试验预算——多重检验风险属实**。A10-5 要求"探索网格全部计入试验预算（DSR N 更新），PBO/White Reality Check 作为披露项"。本任务建立 n_trials 账目，回答三个问题：过去已消费多少 trial、哪些已计入、哪些欠账、未来预算池还剩多少。

## 二、方法与数据来源

- 只读核对 HP `results/experiment-ledger.jsonl`（89 行：backtest 52 / evaluate 35 / None 2，n_trials_cum 到 86）、`a9_timing_grid_table.csv`、`a7b_summary.json`，以及 VPS 报告 R-222/R-223/R-225/R-226/R-231 与 work/task-0341-out/a7c-dynamic-ic-table.csv
- 现行登记机制三处：① HP experiment-ledger.jsonl 的 `n_trials_cum` 字段（DSR g4 消耗它）；② R-230 §四"实验分层 n_trials 计账"前向规范；③ 各报告自声明。**VPS 侧无统一台账**（本任务产出 n_trials_ledger.csv 补上）

## 三、核心发现（结论先行）

**当前 DSR N = 86；三块欠账合计 68；若含 R-231 待入台账共 71。全部补登后 DSR N 应更新为 154（含 R-231 则 157）。**

| 类别 | 任务/报告 | 已消费 trial | 已计入 | 欠账 | 证据 |
|---|---|---|---|---|---|
| E2 择时网格 40 组 | task-0342 / R-222 §五 | 40 | 1（IT-A9-04 网格优胜组） | **39** | a9_timing_grid_table.csv 40 组；ledger A9 批仅 4 条（IT-A9-01..04, ntc 76-79） |
| A7c 因子动态画像 | task-0341 / R-223 A7c 行 | 17 | 0 | **17** | a7c-dynamic-ic-table.csv 17 因子变体；ledger 无 IT-A7c |
| A7b 现金曲线 | task-0339 / R-223 A7b 行 | 12 | 0 | **12** | a7b_summary.json：baseline+cash5+robust4+sub2；ledger 无 IT-A7b |
| 择时v2信号画像 E1 | task-0361 / R-231 §四 | 3 | 0（报告已声明） | **3（待入台账）** | R-231 SPREAD w∈{5,10,20} n_trials=3；HP ledger 未写 |

**合计**：消耗 72，计入 1，欠账 71（三块 68 + R-231 3）。

### 每块细节

1. **E2 择时网格 40 组（欠账 39）**：R-222 §五"E2 择时网格全景（40 组全，锚校验通过）"，网格 = MA{15,20,50,100,200}×q3z{on,off}×地板{0,10,18,30} 共 40 组全跑。但 HP ledger 对 A9 批仅登记 4 条（IT-A9-01 E1 raw / 02 E3 raw / 03 E3 quality / 04 E2 网格优胜组），40 组中只有 IT-A9-04 作为"网格最优"计 1 trial，其余 39 组未逐一入账。当时未计入预算（R-226 P1 属实）。
2. **A7c 因子动态画像（欠账 17）**：task-0341 对 107 因子 IC 面板做动态核验，产出 17 个因子变体画像（全周期/近24m/近36m/分段/半衰期），ledger 无 IT-A7c 条目。因子 IC 核验自由度=17，全部未计入。
3. **A7b 现金曲线（欠账 12）**：task-0339 现金曲线 5 档 + 稳健性 4 组 + 分段子样本 2 组 = 12 次回测，ledger 无 IT-A7b 条目，全部未计入。（严格口径：baseline/cash_00 为已知基线 v4b_mve1 复核，净新试验 10；本账按 12 全计，更保守）
4. **R-231 E1 信号画像（待入台账 3）**：R-231 已自声明 n_trials=3 并注明"HP experiment-ledger 由主会话统一登记，本任务未触碰生产台账"——即报告层已登记、台账层欠账。

### 现行登记机制评估

- **真源**：HP `experiment-ledger.jsonl` 的 n_trials_cum（DSR g4 直接消费，R-223 §3.4"DSR N 计数 = n_trials_cum 跨批次累计，v5h=85"，现 max=86）。
- **R-225 评分制**只改 verdict 合成层（score_composite/score_rank_pool），**未新增 n_trials 登记机制**。
- **R-230 §四**定义了前向分层计账规范（E1≈40/E2=2/E3≈12，接 A9 76-79 续编），但未成为强制落账检查。
- 结论：**无 VPS 侧统一 n_trials 台账**；机制散落三处。建议落点：`n_trials_ledger.csv` 作为 VPS 只读披露/审计镜像，HP ledger 仍为唯一写入真源。

## 四、下一步（按 R-226 A10-5）

1. **存量补登**：主会话在 A10-5 时把本 ledger 的欠账行补写进 HP experiment-ledger.jsonl（type=backtest/analysis，n_trials_cum 从 86 续到 157），DSR N 更新为 154（不含 R-231）或 157（含）。
2. **未来约束**：探索网格（参数扫描/画像/现金曲线类）在批任务收口时**必须**逐参数组写入 ledger；R-230 分层规范升级为强制落账检查（缺账不给 REJECT/PASS 收口）。
3. **披露**：PBO / White Reality Check 作为 DSR 之外的披露项（R-226 A10-5 采纳），随补登一并实现。
4. **校验钩子**：可在批收口验收里加 `grep -c "IT-批次" experiment-ledger.jsonl` ≥ 参数组数 的检查（本次未改 production，仅建议）。

## 五、结论建议

- 多重检验风险**属实**：E2 40 组 / A7c 17 因子 / A7b 12 回测此前均未入账，DSR 的 N 被低估约 71（相对当前 86 几乎翻倍），现役 v5h 等版本的 DSR 在补登后需用更大 N 重算。
- 建议立即补登 + 后续强制逐参数组落账，并尽快实施 A10-5 的 PBO/White Reality Check 披露。

## 六、来源清单

1. R-226 下一步探索计划（P1 条目原文、A10-5）
2. R-222 A9 原始宇宙与择时网格实验报告（E2 40 组来源、ledger IT-A9-01..04）
3. R-223 量化迭代流程与规则总纲（A7b/A7c 行、DSR N 计数机制、ledger 统计）
4. R-225 五门禁评分制改造与回填验证（评分制登记机制确认）
5. R-230 择时层v2三维扩展设计报告（§四 n_trials 计账规范）
6. R-231 择时v2信号画像第一批报告（§四 n_trials=3 声明）
7. HP 现读：experiment-ledger.jsonl（89 行）、a9_timing_grid_table.csv（40 组）、a7b_summary.json
8. work/task-0341-out/a7c-dynamic-ic-table.csv、work/task-0339-notes.md、work/task-0342-notes.md、work/task-0363-notes.md（本任务笔记）
