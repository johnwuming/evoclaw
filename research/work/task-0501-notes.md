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
