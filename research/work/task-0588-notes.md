# task-0588 过程笔记（B9 黄金腿卡改口径）

## 起点
- Version.jsx 27963B（<30KB 可全读）；styles.css 35182B（>30KB，只 grep）。
- 目标：黄金腿卡「目标权重（设计）+实际未建仓警示」；股票腿卡 runtime 标注；构建+测试+390 无头自查。

## 核验点
- 无头自查基建：scripts/t0578-static-server.cjs（8981 静态 dist + /quantv6/api/ → 127.0.0.1:8180）；参照脚本 t0575-headless-check.cjs（.ver-head 展开 → .sleeve-pos-card / .sleeve-gold 断言 + bodyScrollW）。
- 黄金腿卡位置：PaperViews 内 `{showGold && (...)}` 块；权重行 `.sleeve-w`「权重 {fmtPct(goldW)}」；goldW 动态取 weight_solution.weights.hedge_sleeve_gold。
- 股票腿卡 = 「持仓明细（账本投影）」卡；设计权重可动态取 weights.equity_sleeve。
- styles.css 有 --amber(#ffc53d)/--red 变量；.sleeve-note 已存在（11px muted）。

## 改动方案
- Version.jsx：①黄金腿 `.sleeve-w` 改「目标权重 X%（设计）」；②新增 `.sleeve-warning` 警示行（R-377 核验 60/40）；③运行状态 chip 后加「（引擎状态，非实际持仓）」注；④股票腿卡头部下加 `.sleeve-runtime-note`：「设计权重 X%；runtime 实际 60% 权益 + 40% 现金（含择时）· R-377 核验」。
- styles.css 末尾追加 3 个类，零新依赖，api.js/App.jsx/hooks.js 不动。
