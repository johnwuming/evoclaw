# task-0555 版本页历史迭代回测对照视图 — 过程笔记

日期: 2026-08-29 11:16 GMT+8 开始

## R-356 占用检查
- R-356 未被占用（grep rc=1）→ 使用 R-356

## 现状定位（VPS）
- BFF 端口 8180，LEDGER_DIR=/root/.openclaw/workspace/tools/quant-bff/live（systemd）；dataDir=live/data
- 现役文件: live/data/performance.json（vC-0, 156月, ann 0.1357/vol 0.0947/sharpe 1.4333/mdd -0.0908）+ live/data/nav_curves.csv（列 F1_quarterly）
- BFF 版本详情: GET /api/v1/portfolios/:id → loadPerformance 读 performance.json + curve_source.file 列 → nav_curve；版本不匹配→null（降级已有）
- 版本目录: live/data/versions/vC-0.json；版本列表 portfolios.json
- 前端 Version.jsx: Detail 内 PerformanceSection（四指标卡+NavChart SVG 358 宽 viewBox）；fmtPct 已有
- 口径（task-0549）: 月频月末净值基期1.0；ann=几何CAGR；vol=std(ddof=1)×√12；sharpe=ann/vol(0无风险)；maxDD=min(1-NAV/峰值)含1.0
- 约束: 禁改现役 performance.json/nav_curves.csv；新文件 version-scoped 如 performance.r309.json

## HP 实查计划
目标: 各历史版本 NAV/回测产物。线索: paper-nav.csv.r309-retired / f6_curves / gold shadow_nav

## HP 实查结果（2026-08-29）
- `results/archive/paper-nav.csv.r309-retired`：旧 paper 真实盘，仅 7 行（2026-08-14~08-24，日频），无月频回测曲线 → **残缺，跳过指标回填**（paper-summary.json.r309-retired: nav_per_unit 0.9832）
- `portfolio_v1/combo_selector/results/nav_curves.csv`：列 = month,A,gold,F0_buyhold50,F1_equal,F1_quarterly,F3_volparity,F4_erc,F5_b50_tilt65_80 → **历史迭代回测曲线主数据源**（F1_quarterly=现役 vC-0）
- `portfolio_v1/combo_selector/results/selector/`：vc0_F1_check.json / vc0_F6_check.json / vc0_F7a_check.json / vc0_F7a_monthly.csv（month,ret 156行）/ vc0_F7a_results.json / vc0_F7b_check.json
  - F6/F7b：仅有快照自算指标、**无曲线产物**（check json 无 curve 键）→ 非 0549 口径可重算 → **标注跳过**
  - F7a：月频 ret 曲线 156 月（2013-08~2026-07），metrics final_nav=5.251 → cumprod 重建 NAV 可核
  - F7a metrics 锚: ann=0.1361 vol=0.0891 sharpe=1.483 mdd=-0.068（window 2013-08-31~2026-07-31, 156月）
  - F6 metrics（仅参考）: ann=0.1911 vol=0.1568 sharpe=1.197 mdd=-0.1396
- `results/engines/gold/shadow_nav.csv`：157 行月频（2013-08~2026-08）对冲腿影子净值——属引擎腿非组合版本 → 不入版本对照，笔记留档
- `results/engines/a2/shadow_nav.csv`：日频 2006-01~2024-06 → 同上不入
- 任务书线索修正：「f6_curves」实查不存在；F6 无曲线。gold shadow_nav 为引擎腿非版本。

## 版本集决定
- 回填（0549 口径重算）：F0_buyhold50 / F1_equal / F3_volparity / F4_erc / F5_b50_tilt65_80（nav_curves.csv 各列）+ F7a（ret→cumprod 重建）
- 现役 vC-0：引用既有 performance.json，不重复
- 跳过清单（标注理由）：F6（无曲线）、F7b（无曲线）、r309 旧 paper（真实盘 7 交易日）
- 版本 scoped 文件（新增，VPS live/data/）：performance.F0_buyhold50.json 等 6 个 + nav_curves.F7a.csv + perf_history_index.json

## 指标回填结果（0549 口径重算，HP /tmp/t0555/compute.py）
| 版本 | 月数 | ann | vol | sharpe | mdd | 锚匹配 |
|---|---|---|---|---|---|---|
| F0_buyhold50 | 156 | 0.148614 | 0.124607 | 1.1927 | -0.129509 | ✓ all_results#F0_buyhold50 |
| F1_equal | 156 | 0.135377 | 0.092276 | 1.4671 | -0.082757 | ✓ |
| F3_volparity | 120(列前36月为空,2017-08起) | 0.0951 | 0.068804 | 1.3822 | -0.060453 | ✓ |
| F4_erc | 120 | 同 F3（ERC 与 volparity 该窗口收敛，锚一致） | | | | ✓ |
| F5_b50_tilt65_80 | 156 | 0.133653 | 0.091942 | 1.4537 | -0.08236 | ✗ 无锚（all_results 无此键，F5 键为空结构）→ cross_check_match=null |
| F7a | 156 | 0.136063 | 0.089057 | 1.5278 | -0.068012 | ✓ final_nav 5.25089≈5.251；其 sharpe1.483 为算术口径已注记 |

## 交付文件（VPS live/data/，全部新增，现役零改动）
- performance.{F0_buyhold50,F1_equal,F3_volparity,F4_erc,F5_b50_tilt65_80,F7a}.json ×6
- nav_curves.F7a.csv（月频 month,nav 156 行）
- perf_history_index.json（versions+skipped: F6/F7b/paper-r309）
- 现役校验：performance.json md5 e959d21a…（未动）；nav_curves.csv md5 9704a300…（与 curve_source 记录一致）
