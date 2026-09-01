# R-394 A2 阶段一：gold 引擎 asof 语义修复与全历史重算 staging

- **任务**：task-0610 阶段一（A2 修复实施上半场）；执行：主 agent 派发 subagent，2026-09-01 10:12–13:05 北京时间
- **规格依据**：R-391 §5 修复方案（用户已批准 A2，09:59 拍板升级 B 建仓闸门）
- **状态**：**staging 完成，禁发布**。生产账本/shadow_nav.csv/paper_state（含 audit）零改动；生产脚本两文件已按规格修复（本就属阶段一范围）
- **本地产物镜像**：`work/task-0610-staging-mirror/`；HP 权威产物：`10.12.192.174:~/quant-evolve/output/staging_gold_a2/`

## 1. 结论速览

修复 asof/ffill 语义后全历史重算（157 个月，2013-08-31~2026-08-31），与 R-391 反事实**逐位一致**：

| 维度（157 行同窗） | 旧账本（缺陷语义） | 新账本（staging） | 变化 |
|---|---|---|---|
| 终点净值 | 2.6046 | **3.1707** | +21.7% |
| 年化收益 | 7.59% | **9.22%** | +1.63pp |
| 年化波动 | 6.85% | **8.42%** | +1.57pp |
| 最大回撤 | −5.90% | **−8.09%** | 深 2.19pp |
| 月收益 corr(a13) | 0.0798 | **0.0411** | −0.039 |

R-391 反事实方向（终点 2.6046→3.1707、ann 7.59→9.22、MDD 5.90→8.09）全部逐位复现；vol 与 corr 为本次新增维度。**该清洁口径即 B 建仓闸门权重计算的输入底座**（权重本身待用户人工门）。

## 2. 备份（修复前，HP `~/quant-evolve/backup/`）

- 归档：`task0610_preA2_20260901_023404.tar.gz`（16916B，含两脚本 + `results/engines/gold/` 全目录）
- sha256 清单：`task0610_preA2_20260901_023404.sha256`，关键项：
  - `scripts/paper_engine_gold.py` = `a193182a22e8…8211dbbff`
  - `scripts/engines_shadow_nav_gold.py` = `1293dc617bf0…87486c0684caf`
  - `results/engines/gold/shadow_nav.csv` = `1bec2035195b…a49a2814bd`
  - `results/engines/gold/paper_state.json` = `3a31a515cfc3…743eeb85c6a05d91`
- 生产文件 mtime 快照：`backup/mtimes_before_task0610.txt`（注：HP 无独立 `paper_state.audit` 文件，审计在 paper_state.json 内）

## 3. 代码修复本体（R-391 §5 原方案，逐行）

两文件同构缺陷行（各恰 2 行，`reindex(m.index)` → `reindex(m.index, method="ffill")`）：

```python
sma200 = s.rolling(SMA_N).mean().reindex(m.index, method="ffill")
vol60  = s.pct_change().dropna().rolling(VOL_N).std().reindex(m.index, method="ffill") * np.sqrt(252)
```

- `scripts/paper_engine_gold.py`（compute_signals L86-87）→ sha256 `0d6fe3ee3653…375f618f9`
- `scripts/engines_shadow_nav_gold.py`（compute_signals L78-79）→ sha256 `d2730dc94d58…2f262d5a02931bf`
- 打补丁脚本带 `count==1` 断言；两文件 `py_compile` 通过；最小 diff：`staging_gold_a2/fix_asof.diff`（26 行）
- 热身期（<200 交易日）仍 NaN→w=0，早期行为不变（NaN 月修复后恰剩 10 个热身月）

## 4. 行为差异最小证明

| 指标 | 缺陷语义 | 修复语义 |
|---|---|---|
| sma200 月末 NaN 月数 | 60 | 10（全为热身） |
| 其中 NaN 且 w_true≠0（被强制归零） | 33 | 0 |

- 新旧逐月 diff（`wdiff_months.csv`）：**34 行 = 33 语义变更月 + 1 舍入行**。舍入行为 2014-07-31（|Δw|≈4.6e-5 < R-391 自定 5e-5 舍入阈值，账本 4 位小数存储所致），非语义变化
- 33 个语义月与 R-391 表2 污染月清单一致（首 2014-09-30 w 0→1.0，末 2026-06-30 w 0→0.3171）
- **R-391 小勘误**：NaN 月 61 实为 **60**——2026-08-31 为周一交易日（腾讯有行情行，引擎 daily cron 08-31 07:40 UTC 亦实际运行），R-391 误记为周日；不影响其结论与修复方案

## 5. 对账（全部可重跑）

- 新账本（staging）内部对账：w_applied ≡ 修复语义 w_sig.shift(1)，157/157 allclose 通过
- 旧账本=缺陷语义复证：w_applied ≡ 缺陷语义 w_sig.shift(1)，157/157 allclose 通过（复核 R-391 既有结论）
- 逐月净差与 R-391 口径说明：R-391 表2 为毛收益差 `(w_true−w_applied)×gold_ret`；本报告 d_net 为净账本差（含货基腿与 0.13% 成本），方向一致、量级略大（如 2014-09：毛 −4.89pp vs 净 −5.11pp）

## 6. 生产零改动证明（主 agent 验收点）

修复后复测（HP，2026-09-01 03:09 UTC 后）：

| 文件 | mtime | sha256 vs 备份 |
|---|---|---|
| results/engines/gold/shadow_nav.csv | 2026-08-24 15:13:35 UTC（未变） | 一致 `1bec…14bd` |
| results/engines/gold/paper_state.json | 2026-08-31 07:40:03 UTC（未变，系 cron 旧写） | 一致 `3a31…5d91` |
| results/engines/gold/mmf_monthly_push.csv | — | 一致 `a5c5…aff99` |

仅两脚本 mtime/sha 变化（即修复本体，预期内）。未触碰 evolution_pipeline / registry / paper_engine / crontab。

## 7. R-389 L50 errata 草稿（落盘 staging，未动 R-389 原文、未追加 paper_state.audit）

HP `output/staging_gold_a2/errata_R389_L50_draft.md`（全文另见本地镜像）。要点：L50「gold 引擎当月 w_applied=0，月收益 +0.04%，接住了组合」在修复语义下应为 **w=0.3171、6 月净收益 −3.40%**（部分避险而非完全接住），展示口径一线最深回撤将变深；「逐月差 >2pp 月份 54/156」需以修复后账本重算。波及 R-380/R-386/R-388 引用句，阶段二统一标注。

## 8. 复算命令（HP，~/quant-evolve）

```bash
/home/noname/miniconda3/envs/quant/bin/python output/staging_gold_a2/recompute_full_history.py
# 输出 compare_results.json / wdiff_months.csv / shadow_nav_a2fixed.csv / gold_daily_used.csv
```

数据：腾讯 fqkline sh518880 qfq 日频 3184 行（2013-07-29~2026-08-31），与引擎 daily 同源；mmf 用生产 `mmf_monthly_push.csv`（缺月会硬报错，不臆造）。a13 口径：`results/a13x_equiv_v5h_full_nav.csv` 日频→月末 resample→pct_change，与 gold 月 net 求相关（n≈156）。

## 9. 观察项（不阻塞，移交阶段二）

1. 生产 shadow_nav.csv 与 shadow_nav_seed.csv **字节相同**（sha256 同），mtime=08-24 15:13 UTC，但内容含 2026-08-31 行（gold_ret +13.41%）——疑种子一次性构建后 `cp -p` 保留时间戳；阶段二重发布时一并厘清
2. 修复后首个真实受益月：2026-10-31（周六）月末信号，11-03 append 时按 asof 取值（若信号非零）
3. 今日（09-01）15:40 北京 daily cron 起以修复语义产出 paper_state 信号；09-03 append/evaluate cron 所写账本行（2026-08）新旧语义碰巧同值（w=0），无缝过渡

## 10. 阶段二预告（本阶段禁做，待用户/流程触发）

生产账本重发布 + 旧账本版本化（shadow_nav_preR391.csv）、nav_curves.csv 走 BFF 管线刷新、R-380/R-386/R-388/R-389 引用数字新旧对照独立报告、task-0608 更正事件（北京 15:45 gold cron 落盘后）、R-389 L50 errata 正式落稿。

---

*产物索引：HP `~/quant-evolve/backup/task0610_preA2_20260901_023404.{tar.gz,sha256}`、`~/quant-evolve/output/staging_gold_a2/`（7 文件）；本地 `work/task-0610-staging-mirror/`（5 文件）、笔记 `work/task-0610-phase1-notes.md`。*
