# R-265 csad 残差因子 M1.1 评分制 v1.1 报告（task-0427）

> 前序：R-257 E1 画像 → R-260 残差裁决（v2 口径）→ R-263 预注册 → R-264 E2 引擎级对照（G0–G2 PASS 胜者 M1.1，IT-R263-01）→ 本报告为评分制收口
> 类型：registry candidate 登记 + 评分制 v1.1（零回测、零引擎/pipeline/paper_engine/crontab 改动）
> 结论等级：**不过线（差 rank1 一条）——M1.1（csad_resid⁻，w=0.3）以 0.8732 居池内 rank2，落后在役 a13（0.8781，−0.0049）；stat_warn 无、holdout PASS。按三条件裁决不构成激活资格，a15_csad_resid 以 candidate 留档，负结果与差距数字归档如下**

## 一、背景与目标

R-264 E2 判门收口：M1.1（csad_resid 负权第 5 因子，w=0.3）G1/G2 PASS、G3 红旗未触发，按 R-263 §五胜出规则获评分制 v1.1 资格。本任务（链路自动推进授权范围内，评分制免请示、激活才是人工门）：① HP registry 登记 candidate 条目（不动 active/paper_engine/crontab）；② 按评分制 v1.1 部署口径（SCORE_CONFIG，R-225）算分量明细；③ 三条件裁决（rank1 + 无 stat_warn + holdout PASS）——过线=提交用户激活决策，不过线=差距归档，两个结局都合法（R-254 T4 先例）。

## 二、方法与数据来源

1. **评分脚本**：HP `scripts/r265_score_m11.py`（方式参照 r254_score_t4.py / rescore_20pct_v11.py），只调已部署函数 `gate_icir / gate_max_corr / deflated_sharpe / gate_mdd_vs_parent / score_composite / compute_holdout_metrics / score_rank_pool`；SCORE_CONFIG v1.1 权重与门槛一字不改（p/dsr 各 0.175，oos_calmar/oos_sharpe 各 0.125，is_calmar/is_sharpe 各 0.075，dd 0.10，corr 0.10，logic 0.05；g6 硬判定禁用 D-20260819-G6DEL；g3 含 G3CORR+G3SYM 豁免）。evolution_pipeline.py 零改动（md5 写前后一致 9c50b188…）。
2. **IC 口径（如实标注）**：csad_resid 无部署 `factor_ic_monthly`/`a13_supp_ic_monthly` IC 列——若走部署默认的因子级等权复合会**静默丢失该因子**，故 g1/g2 输入=引擎复合 IC 月度序列（R-264 由 r263 g0/m1 排序分 dump 产出的 `work/r263/ic_composite_r263_m1_w03.csv`，246 有效月，MIN_OBS=20）；4f 基准序列（`ic_composite_4f.csv`）同法作参考披露。单列输入下部署函数的 mean(axis=1)=复合 IC 本身，函数体零改动。
3. **g3 数据源**：r0422 `ic_monthly_residual.csv` 的 `ic_res_v2` 列（残差因子月度 IC 序列，2005-08 起）经脚本内 monkeypatch 内存注入 `load_ic_monthly`（不落盘、不改 supp 文件、调用后恢复）——等价部署函数第三数据源（月度 IC Pearson ≥24 月重叠）。**GUARD_CORR_CONFIG 豁免不触发**：csad_resid 非 ret120 替身名单（mom_pen/mom_pen_dz）成员，无 R-245 §3.3 的不对称豁免问题。
4. **holdout 口径**：`compute_holdout_metrics` 消费 full nav 终点截 2026-08-13 副本 `results/r263_m1_w03_full_nav_t0813.csv`（5007 行，新建，md5 9f1e28a5…），段起点 2024-07（SHADOW_CONFIG），沿 R-253/R-254/R-264 终点截断纪律。
5. **metrics 口径**：registry `metrics` 存 locked 窗值（2006-01-04→2024-06-28 与 a13 同窗：ann 0.2251 / mdd −0.3423 / sharpe 1.3386 / calmar 0.6578）；R-264 审计 full 数字（截 08-13）另存 `metrics_full_r263_audit_t0813`（full 0.2229/−0.3423，holdout 0.2046/−0.1780）。
6. **确定性**：两次干跑 summary 逐字节一致（ex scored_at 时间戳）后才 --write；n_trials=97（HISTORICAL_TRIAL_OFFSET 34 + 台账 63 条 backtest，部署口径实读）。

## 三、核心发现（结论先行）

### 3.1 三条件裁决：不过线（2/3 过，差 rank1）

| 条件 | 结果 | 数字 |
|---|---|---|
| rank1（池内第一） | **✗** | **rank2**：a13 0.8781 > **M1.1 0.8732** > a14_crowdf2 0.8584 > v4a_mf0_trr 0.8088 |
| 无 stat_warn | ✓ | g2 p 单侧 0.6143 ≥ 0.01；DSR 0.9999 ≥ 0.90 |
| holdout PASS | ✓ | 2024-07-01→2026-08-13 ann 0.2052 ≥ 0.6×0.2251=0.1351；mdd −0.1780 较 locked 改善 16.43pp ≤ 10pp 容限 |

**结论：M1.1 不构成激活资格。** csad 残差因子在统计健康（p 1.0 满档 / DSR 0.9999 / holdout 宽裕通过）与信息正交性（max|ρ| 0.2932 → corr 满档）上全部成立，G2 的机制增量（locked 复合 ICIR +0.0455）在评分口径下不足以转化为对在役的 locked 窗绩效净优势——locked ann +0.49pp 但 sharpe −1.29%（换手 +14.92pp 抬高日波动）。无激活动作，candidate 留档。

### 3.2 分量明细（总分 0.8732 = 满分 1.0 加权和；missing_weight 0.0、flags 空、无 partial）

| 分量 | 权重 | 得分 | 依据 |
|---|---|---|---|
| p | 0.175 | 1.0 | g2 OOS 单侧 p=0.6143（≥0.20 满档；OOS mean IC 0.10368 > IS 0.09588，引擎复合 IC 口径） |
| dsr | 0.175 | 0.999 | DSR 0.9999（T=4490，n_trials=97） |
| oos_calmar | 0.125 | 0.503 | locked 0.6578 vs a13 0.6562（rel +0.24%，零增量=0.5） |
| oos_sharpe | 0.125 | 0.4839 | locked 1.3386 vs a13 1.3561（rel −1.29%） |
| is_calmar | 0.075 | 1.0 | 0.6578/0.60 封顶 |
| is_sharpe | 0.075 | 1.0 | 1.3386/1.20 封顶 |
| dd | 0.10 | 1.0 | locked mdd −0.3423 vs −0.3355，恶化 0.68pp ≤ 2pp 免罚带 |
| corr | 0.10 | 1.0 | max\|ρ\|=0.2932（csad_resid vs mom_pen_dz，230 月 Pearson；vs 其余四因子 −0.12/+0.09/+0.12/+0.18）≤ 0.5 满档 |
| logic | 0.05 | 1.0 | 预注册机制说明 ≥20 字 |

门禁判定：g1 PASS（引擎复合 ICIR_IS 年化 2.4314，179 月；4f 参考 2.2338）/ g2 PASS（icir_oos 2.2459，42 月止 2024-06 审计锁内）/ g3 PASS（0.2932 < 0.7）/ g4 PASS / g5 PASS / g6 N/A(disabled，数值入 dd)。g3 与 g1/g2 的 IC 数据源差异见 §二.2–3（覆盖度：6 因子中 5 个有部署 IC 列，csad_resid 用 r263/r0422 产物替代，未编造；面板对引擎池覆盖 80.03%）。

### 3.3 差距归因（−0.0049 vs a13）

- **唯一失分点=oos 两分量**：M1.1 相对在役的 locked 窗增量是「年化 +0.49pp、calmar +0.24%、sharpe −1.29%」的混合近零增量（映射后 0.503/0.4839），而 a13 当年评估（vs 其时基准）的 oos 分量为正增量（a13 registry 旧格式无分量明细，按满分量恒等式反解其 oos 合计 0.1283，单分量≈0.511）。
- **换手是 sharpe 折损的直接嫌疑**：月换手 0.5965 vs 在役 0.4473（+14.92pp，R-264 已披露，成本 v2 逐股计价已在 NAV 中）——年化仍 +0.49pp 说明因子信息真实，但重排成本与波动侵蚀把信息率吃平。
- **csad 的正交性优势在评分制下无额外奖励**：corr 0.2932 满档即封顶（≤0.5 都=1.0），与 a9 案（corr 0.7555 被罚）相反方向——正交新信息源的边际价值在此口径中只通过 oos 分量间接计价。
- **量化缺口**：oos_sharpe 从 0.4839 提到 ~0.51+（追平 a13 所需）需相对增量 ≥+1%——即 locked sharpe 从 1.3386 提到 ~1.370，在换手已 +14.9pp 的结构下需 w 显著降低或残差口径更强，两者都超出 R-263 停止规则（禁止换口径/加密网格复活）。

### 3.4 holdout 弱势与评分制 OOS 分量的关系（用户知情义务，R-263 §五.4）

R-264 硬披露：M1.1 holdout ann 0.2046 vs 在役 0.2578（**−5.32pp**）、MDD −0.1780 vs −0.1613（−1.67pp），因子尾段残差 ICIR −0.269（衰减区）。与评分制的关系须说清三点：

1. **该 −5.32pp 没有直接进入总分**：评分制的 oos_calmar/oos_sharpe 分量度量的是 locked 窗（2006-01~2024-06）相对在役增量，**不是** holdout 段；holdout 只进三条件门（ann ≥ 0.6×locked + mdd 容限 10pp），本例宽裕通过（0.2052 ≫ 0.1351，mdd 反而改善 16.43pp）。
2. **若 M1.1 是 rank1，−5.32pp 将是激活决策的首要逆风**：三条件全过的候选在提交用户激活决策时，近 26 月落后在役 5.3pp 年化是必须摆在桌面的数字（R-263 §六「holdout 全部落在衰减区」的设计使然）。本次以 rank2 归档，该逆风连同 post-hoc 自由度警示（残差口径是看数据后引入，E2 成功率先验本应下调）一并留档供复看。
3. **方向判断留给用户**：csad_resid 是「机制真实（G2 +0.0455）、统计健康、近段衰减」的进攻性候选——评分制 v1.1 的 OOS 分量集中于 locked 窗绩效而 holdout 只设宽门槛，若用户想显式惩罚近段衰减，可考虑（需另立项+批准）评分制 v1.2 讨论 holdout 分量；若想保留该信息源，降权接入（w<0.3）或作观察因子亦须全新预注册，本档案不构成依据。

### 3.5 registry 变更与完整性

- 新增 candidate：`model/registry/a15_csad_resid.json`（status=candidate；parent=a13_rsraw_e1f10dz；selection 逐参复刻在役 C4 + ext_specs 追加 `("csad_resid", 0.3, -1)`；factors=在役 5 因子 + csad_resid；timing 与在役逐字同；provenance 含 R-263 预注册/R-264 引用/因子定义（v2 双中性化残差 w=0.3 负权第 5 因子）/冻结面板 md5 416019cf…/池覆盖 80.03% 与有效权重 14.69%/换手与 holdout 弱势披露/「不自动激活」约定；backtest_refs 指向 bt_r263_m1_w03_20260821 产物）。
- 备份：`model/registry.bak.20260821_task0427.tar.gz`（39.2KB，沿 R-245/R-254 命名惯例，写前全量）。
- **diff 校验**：写前 50 个 registry json md5 快照 vs 写后，**仅新增 a15_csad_resid.json 一行**；在役 a13 条目 md5 346450f7… 逐字未变 ✓；evolution_pipeline.py md5 写前后一致 ✓。
- 回写字段（沿 R-245 惯例）：gate.score 0.8732 / score_components / score_flags 空 / stat_warn false / rank_in_pool 2 / score_holdout / ic_coverage（含 csad_resid 缺部署 IC 列的如实标注与替代口径）/ scored{task-0427, at, run_id, baseline_active}；manifest `gen_versions_manifest.py` rc=0（107 versions，active=a13_rsraw_e1f10dz）✓。
- 零回测、零引擎/pipeline/paper_engine/crontab 改动；HP scripts/ 仅新增分析脚本 r265_score_m11.py，results/ 新增 3 文件（summary、nav_t0813 副本、manifest 重生成）。

## 四、结论与建议

1. **M1.1 评分制 v1.1 收口=不过线**：0.8732/rank2/无警示/holdout PASS，差 rank1 一条（−0.0049 vs a13）。按三条件裁决不提交激活决策；a15_csad_resid 以 candidate 留档，无任何 status 变更。csad 因子线（R-257→R-265）完整走完「画像达线 → 残差裁决 → E2 过门 → 评分落败」闭环，负结果合法且高价值。
2. **两次 E2 胜者同败于 rank1（R-254 T4 −0.0197、R-265 M1.1 −0.0049）**印证 R-263 §五.5 先验：评分制 v1.1 的 oos 分量结构下，弱改进候选难胜在役的正增量遗产；且两案失分机理不同（T4=零增量，M1.1=增量被换手/波动侵蚀）——对后续 E2 立项的启示：进攻性因子须预登记换手门或在 G1 内含信息率口径，否则机制增量会以 sharpe 形式漏失。
3. **可复现**：`python scripts/r265_score_m11.py`（干跑）/`--write`；两次干跑 summary 逐位一致已验证。

## 五、来源清单（HP 路径 + md5）

| 文件 | md5/说明 |
|---|---|
| results/r263_m1_w03_{full,locked}_nav.csv + _metrics.json | IT-R263-01 产物（R-264 一致：full md5 67ca21d6…） |
| results/r263_m1_w03_full_nav_t0813.csv（本任务新建截断副本） | 9f1e28a509abc598a03866af21a99431（5007 行） |
| results/work/r263/ic_composite_{r263_m1_w03,4f}.csv | 引擎复合 IC 月度序列（g1/g2 输入） |
| results/work/r0422/ic_monthly_residual.csv | ic_res_v2 列（g3 数据源；md5 3bcf930b…，R-263 §八锚定） |
| results/work/r263/csad_resid_monthly.csv | 416019cf5368bde27c289949069f6193（冻结面板） |
| results/work/r263/e2_results.json | R-264 判门与窗口数字（vs_in_service_pp 等唯一取材源） |
| results/r265_m11_score_summary.json | 本任务评分汇总（两次干跑一致） |
| model/registry/a15_csad_resid.json | fb986264b3078de2874d71fb9e225062 |
| model/registry.bak.20260821_task0427.tar.gz | 写前全量备份 39.2KB |
| scripts/r265_score_m11.py | 本任务分析脚本（只调部署函数 + g3 内存注入） |
| scripts/evolution_pipeline.py | 80340B / md5 9c50b188…，未修改（写前后一致） |
| results/versions-manifest.json | 重生成 rc=0（107 versions，active=a13_rsraw_e1f10dz） |
| 参考 | R-263 预注册、R-264 对照报告、R-254 T4 评分先例、R-245 评分制先例、R-225 SCORE_CONFIG v1.1、台账 IT-R263-01 |

过程笔记：shared/results/work/task-0427-notes.md（逐点核验记录）。
