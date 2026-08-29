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
