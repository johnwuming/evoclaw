# task-0501 过程笔记 —— 量化迭代全流程节点化分析（阶段A证据收集）

日期：2026-08-27。任务：只做证据收集与结构化发现；不写正式报告。
材料范围：R-206/R-320/R-321 + 当前实现（本地代码/文档）。禁止 SSH HP。

## 问题索引
- Q1：单模型一轮迭代全流程节点序列 vs 多模型中央风控节点序列，可合并点
- Q2：以「每节点=通用模块」视角盘点重复建设，给出合并抽象候选
- Q3：逐节点可视化必要性（人工决策频率、异常排查价值）+ 保留时重复模块处置建议

---

## [证据1] R-320 抽取（来源：shared/results/05-量化投资/R-320-量化系统抽象合并精简方案.md，task-0498 产出，2026-08-27）

### 双系统/双通道重复（对应 Q2 重复建设盘点）
| # | 功能 | 双方实现 | 状态 |
|---|---|---|---|
| D1 | 模型/版本展示 | 旧 loadModelsQuant(server.js L11377) vs 新 loadV5ModelQuant(L9658)；后端 /api/quant/models vs active/version-options | 旧套死 UI 零入口 |
| D2 | 回测归因/净值 | 旧 renderBtlc* L11900-12543 vs 新 v5btlc L9756；btlc API vs active/curves+f6-curves | 旧套零入口 |
| D3 | 指标采集回传 | push ingest(L5959) vs pull-hp-metrics.sh(每2分钟) | 双写同一 VPS metrics.db |
| D4 | 结果同步 HP→VPS | auto_sync_notify.py vs sync_to_vps.sh(孤儿) + hp_api_server /sync(无调用方) | 3 套机制仅 1 套在用 |
| D5 | 跨机动作编排 | quantEnqueueAction+POST quant/action（入口死）vs hp_api_server /run+/backtest（零调用） | 两套均无人消费 |
| D6 | 因子进化 | p3_3_evolution_standalone.py(939行,旧自包含,半月cron) vs evolution_pipeline.py(1605行,registry版,周六cron) | 双 cron 并行 ⭐核心 |
| D7 | paper 引擎 | paper_engine.py(A股) vs paper_engine_gold.py(黄金) | 有意隔离设计；建议抽公共层 quant_common |
| D8 | 影子净值 | engines/:id/shadow-nav + engines/shadow-nav 双路由(L3756/3800) | 前端只用动态拼接版 |
| D10 | 因子目录 | factor_catalog v1/v2/v3 三代文件并存(L1862-64优先级降级链) | 数据层三代冗余 |

### 死码规模
- 60 个后端量化端点中 29 个死（14 零引用含 7 deprecated 桩 + 15 死树独占：btlc/e2e-curves/reports×2/dsr/gates/q4b-contrast/timing-config/timing-matrix/decisions/pending/ideas/ledger/models/baseline-meta）
- 死 UI 树 server.js L11377-12836+14029（版本切换器/归因链/净值图/生命周期层/报告详情完整仍在），约 1500+ 行可删
- HP 182 脚本中 107 孤儿（无 cron/无引用/无 import）

### R-320 合并方案要点（模块收敛映射）
- 单一数据通道、单一渲染体系、死码先证据后删、HP 冻结在役件零改动
- P0 清死码 → P1 通道收敛（停 pull-hp-metrics、停 hp_api_server、孤儿移档）→ P2 抽象重构（factor_catalog v3 单源、paper/gold 公共层、p3_3 停用评估、前端 v5 组件化）
- 在役管线（HP crontab 实查）：refresh_data(周日)→evolution_pipeline cycle(周六)/p3_3(半月)→paper_engine daily/rebalance/validate→risk_patrol→collect_crowding→notify_hub(时)→w6退市月采→a10/a12月度→qfq双cron→crowding快照→gold三cron→metrics每分钟push

## [证据2] R-321 抽取（来源：shared/results/05-量化投资/R-321-前端可视化模块精简方案.md，task-0499 产出）

### 活 UI 模块清单（六 Tab 共 36 可见模块）
- 数据(2)：D1 数据健康校验卡组、D2 资产盘点表
- 因子(4)：F1 类型Tab栏、F2 因子注册表(行展开36月IC)、F3 在役IC监控、F4 相关性簇
- 模型 v5model(5)：M1 版本选择器、M2 头卡、M3 指标卡×6+窗口chips、M4 解释三层卡、M5 择时仓位趋势图
- 回测 v5btlc(8)：B1 引擎评估徽标行、B2 影子趋势对比图(A2+gold)、B3 F6组合回测图、B4 版本选择器(与M1同组件)、B5 指标卡×6(与M3同组件)、B6 策略vs基准净值图、B7 全版本排行表、B8 引擎级生命周期折叠面板（内含：引擎切换器/引擎因子模型卡/生命周期层=管线qLifecyclePipeline→影子观察→决策时间线→实验台账→迭代轨迹散点）
- 模拟实盘 paper(12)：P0 一致性徽标、P1 策略描述行、P2 指标卡×6、P3 运行状态条(mtime红绿灯)、P4 净值曲线(择时双轴)、P5 跨引擎影子卡、P6 持仓可解释表、P7 交易记录、P8 运行版本卡(registry一致性)、P9 拥挤度卡、P10 退出纪律卡、P11 参数&采纳因子
- 迭代历史 v5hist(3)：H1 分页列表、H2 legacy开关、H3 详情抽屉(选股参数→Gate评估verdict→Locked指标卡→Full指标卡→机制解释→决策记录)
- 公共横件(2)：quantConsistDot 一致性自检点、quantFreshness 数据更新条

### 信息重复矩阵（对应 Q2/Q3）
- 净值曲线重复：active 引擎回测净值在活 UI 出现 **3 处**（B6 主图/B3 F6 图/P5 影子卡 parent 线）；gold 影子净值 **3 处**（B2/B3/P5）；A2 影子净值 2 处；指数叠加 2 处
- 指标数字重复：同维度指标（年化/回撤/夏普/卡玛）活 UI 至少 **9 个渲染点**，其中 M3==B5 同组件同源、B1 徽标行 A 类回退与 M3/B5 完全同值（最高优先去重）
- 端点跨 Tab 重复拉取：registry/active-curves/engines/shadow-nav/version-options/data-health 均被多 Tab 重复请求
- 非实质重复（保留）：版本列表 3 形态（下拉交互/排行对比/分页流水）、持仓 P6 与交易 P7 各唯一

### R-321 合并方案（不动模块总数，靠折叠+瘦身+去重）
- 合并① B1 徽标行去指标数字只留状态徽章；合并② B2 影子对比图移入 B8 生命周期折叠；合并③ 会话级数据缓存 TTL30s
- 删：死岛 A1-A9+B'1-B'12 前端 + factor 死簇(~190行) + 修 onFactorGroupToggle 折叠 bug
- 死岛独有信息评估结论：无高优先级复活项；「回测深度分析」（年度收益/危机段/WF三窗OOS/历代最优，btlcBuild* 动态计算有真数据）为 P2 可选复活项——建议并入 v5hist 详情抽屉折叠区而非复活整页
- DSR 折扣曲线是硬编码假数据(L12806-12816)；五门禁面板读 8月16日 v0_seed 中性态为死数据——gate 核心信息已在 H3「Gate 评估」区呈现

### 效果图关键架构洞察（节点化视角）
生命周期层已形成流程叙事：「管线 → 影子观察中 → 决策时间线 → 实验台账 → 迭代轨迹散点」= 把进化迭代流程映射成了 UI 序列。v5hist 详情抽屉 = 单轮迭代的完整报告（参数/Gate/Locked/Full/机制/决策）。这两者是「节点化」现状最好的前端载体。
