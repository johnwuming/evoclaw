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

## 验证结果
- build：✓ built in 3.65s（index-BKdH4lmu.js 207.19kB / index-gK_P45PD.css 29.23kB）
- npm test：engine-copy assertions: 39 passed
- grep quantv6 dist/assets/：命中 dist/assets/index-BKdH4lmu.js

## 无头自查（390x844，t0588-headless-check.cjs）
- bodyScrollW=390 / docScrollW=390 无横滚
- goldHead「目标权重 41.97%（设计）」、警示行「⚠ 实际未建仓：runtime 为 60% 股票 + 40% 现金，无黄金腿（R-377 核验）」、状态注「（引擎状态，非实际持仓）」、chip「模拟运行中」保留
- equityNote「设计权重 58.03%；runtime 实际 60% 权益 + 40% 现金（含择时）· 依据 R-377 实测核验」
- CHECK_PASS

## 修改文件
- tools/quant-dashboard/src/pages/Version.jsx（4 处）
- tools/quant-dashboard/src/styles.css（末尾 +3 类）
- tools/quant-dashboard/scripts/t0588-headless-check.cjs（新增自查脚本）
