# task-0612 过程笔记 — A2 阶段二：清洁账本发布+BFF 刷新+0608 并入+0609 通知

## 输入与路径（开工前核实）
- staging 产物：HP ~/quant-evolve/output/staging_gold_a2/（7 文件）；本地镜像 shared/results/work/task-0610-staging-mirror/（5 文件）
- 生产账本：HP ~/quant-evolve/results/engines/gold/shadow_nav.csv（旧 sha256=1bec2035...49a2814bd，157 行，2026-08 行为激活日 stub px 9.564）
- paper_state.json（内嵌 audit，无独立 audit 文件）：HP 同目录
- 预期发布 diff（R-394 阶段一定义）：wdiff 34 行=33 语义月+1 舍入行（2014-07-31 |Δw|≈4.6e-5）；另有 2026-08-31 行 stub 修正（gold_ret +13.412%→+8.324%，px 9.564→9.135 月末值）——staging a2fixed 已含该修正，wdiff 不含此行（w 两版均 0）
- BFF/看板消费链（已实查）：HP 账本 →（auto_sync 每 30 分 rsync）→ VPS 镜像 /root/.openclaw/workspace-quant/results/engines/gold/shadow_nav.csv → agent-dashboard:8055 /api/quant/engines/gold_trend_sma200/shadow-nav；当前镜像仍旧账本（157 点 nav 2.60456，末行 ret 0.13412）
- 已知不刷新项（超范围，报告注明）：quant-bff live/data/nav_curves.authoritative.csv 的 gold 列（vC-0 权威展示 58/42 双腿链，R-379 冻结口径）与考核链仍消费旧数据，需另行批准后重建

## 执行日志（边查边写）
