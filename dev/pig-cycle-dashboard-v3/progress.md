# 猪周期数据可视化看板 - 开发进度

## 2026-04-07
- 项目初始化：创建 PRODUCT.md、feature_list.json、init.sh、progress.md
- 基于 R-037 设计方案，共 12 个功能点，分 4 Phase 实施
- Phase 5：补充指标领先滞后传导图（F013）、投资标的日维度跟踪（F014）
  - 新增 /api/transmission 端点，返回传导链定义和各指标趋势
  - 新增 /api/stocks 端点，返回 8 只生猪产业链股票模拟日K数据
  - 前端新增 Tab 导航区域（指标传导链 / 投资标的跟踪）
  - 传导图使用 ECharts graph 展示 5 节点有向图，标注传导周期
  - 股票跟踪展示 K 线蜡烛图（红涨绿跌），支持点击切换个股
