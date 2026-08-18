# task-0363 notes — n_trials 补账（R-234）

> 开始 2026-08-18 10:0x｜恢复点=本文件。边查边写，报告只从本文件取材。

## 1. 任务目标
R-226 P1 条目："n_trials 补账（E2 40 组择时网格/A7c 画像/现金曲线均未计入试验预算——多重检验风险属实，P1）"。A10-5："探索网格全部计入试验预算（DSR N 更新），PBO/White Reality Check 作为披露项"。本任务建立 n_trials_ledger 账目并给出存量欠账补登方案。

## 2. 三块核对结果（证据）

### 2.1 E2 择时网格 40 组 → 欠账 39
- 来源：R-222 §五（"E2 择时网格全景（40 组全，锚校验通过）"）+ HP `results/a9_timing_grid_table.csv`（41 行 = 40 组 + 表头，grid rows=40 ✓）
- 网格结构：MA{15,20,50,100,200}×q3z{on,off}×地板{0,10,18,30} = 40 组
- HP ledger（experiment-ledger.jsonl）A9 批仅 4 条：IT-A9-01(E1 raw)/02(E3 raw)/03(E3 quality)/04(E2 网格优胜组)，ntc=76-79
- 40 组中仅 IT-A9-04 作为"网格优胜"登记 1 trial；其余 39 组未逐一入账
- 结论：E2 网格消耗 40 trial，计入 1，**欠账 39**

### 2.2 A7c 画像（task-0341，动态 IC 画像）→ 欠账 17
- 来源：R-223 A7c 行（task-0341 动态有效性画像）+ work/task-0341-out/a7c-dynamic-ic-table.csv（18 行 = 17 因子变体 + 表头）
- 107 因子 IC 面板核验，产出 17 个因子变体的全周期/近24m/近36m/分段 IC 画像（a7c-dynamic-ic-table.csv 17 行）
- HP ledger 无 IT-A7c 条目（grep 确认 IT-A7c count=0）
- 结论：A7c 画像消耗 17 trial（因子 IC 核验自由度），计入 0，**欠账 17**

### 2.3 现金曲线（A7b，task-0339）→ 欠账 12
- 来源：R-223 A7b 行（task-0339 常驻现金曲线）+ HP `results/a7b_summary.json`（keys: baseline + cash_curve{00,10,20,30,40} + robust{e1_lo,e1_hi,ma_150,ma_250} + subsamples{2018_2021,2022_2026}）
- 回测次数 = 1 baseline + 5 cash + 4 robust + 2 subsample = 12 次
- HP ledger 无 IT-A7b 条目（grep 确认 IT-A7b count=0）
- 结论：现金曲线消耗 12 trial，计入 0，**欠账 12**（其中 baseline/cash_00 为已知基线 v4b_mve1 复核，严格新试验 10）

### 2.4 （附）择时v2信号画像 E1（task-0361 / R-231）→ 报告已声明 3，待入 HP 台账
- R-231 §3.2/§四："n_trials 计账：w∈{5,10,20} 三档=3，全部登记…建议随 E2 一并入台账（HP experiment-ledger 由主会话统一登记，本任务未触碰生产台账）"
- 结论：3 trial 已在报告内声明，尚未写入 HP experiment-ledger → **欠账 3（待入台账）**

## 3. 现行登记机制（质量要求2）
- **真源 = HP `results/experiment-ledger.jsonl`**（89 行：backtest 52 / evaluate 35 / None 2），每行含 `n_trials_cum` 字段，DSR g4 门槛直接消耗它（R-223 §3.4：DSR N 计数 = n_trials_cum 跨批次累计，v5h=85）
- 当前累计 DSR N = 86（ledger 内 max n_trials_cum=86，IT-A11-04；其后 v5j/v5k evaluate 亦 86）
- R-225（评分制）：只改 verdict 合成层（score_composite/score_rank_pool），**未新增 n_trials 登记机制**
- R-230 §四：定义了"实验分层 n_trials 计账"前向规范（E1≈40/E2=2/E3≈12，接 A9 76-79 续编），但当时尚未成为强制落账检查
- 结论：**无 VPS 侧统一 n_trials 台账**；机制散落 = HP ledger(n_trials_cum) + R-230 分层规范 + 各报告自声明。建议落点：本任务产出的 `n_trials_ledger.csv` 作为 VPS 只读披露/审计镜像，HP ledger 仍为唯一写入真源

## 4. 汇总数字（质量要求4）
- 三块（E2/A7c/A7b）合计消耗 = 40+17+12 = 69 trial；其中已计入 ledger = 1（IT-A9-04）；**欠账合计 = 68**
- 若含 R-231 E1 待入台账 3 → 总待补 = 71
- 当前 DSR N = 86 → 全部补登后调整 DSR N = 86 + 68 = 154（含 R-231 → 157）
- 未来预算池：按 R-230 分层规范，E2/E3 等后续探索须逐条写入 HP ledger，DSR N 随之更新；PBO/White Reality Check 作为披露项（R-226 A10-5）

## 5. 验收对照
- [ ] n_trials_ledger.csv 存在且行数 ≥3（4 数据行 + 合计）
- [ ] R-234 报告 ≥2KB
- [ ] README.md 含 R-234（顶部变更记录 + 底部索引表）
- [ ] 每类欠账数字可溯源（见 §2 证据列）
- [ ] 未修改 evolution_pipeline.py / registry / paper_engine / HP crontab（全程只读核对 + VPS 目录新增文件）

## 6. 结论建议（进报告 §五）
1. 存量补登：主会话在 A10-5 时把本 ledger 的欠账行写入 HP experiment-ledger（type=backtest/analysis，n_trials_cum 续 86 起），DSR N 更新为 154
2. 未来约束：探索网格（参数扫描/画像/现金曲线类）在批任务收口时**必须**逐参数组写入 ledger；R-230 分层规范升级为强制检查（缺账不给 REJECT/PASS 收口）
3. 披露：PBO/White Reality Check 作为 DSR 之外的披露项（R-226 A10-5 采纳）
