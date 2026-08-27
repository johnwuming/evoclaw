# task-0513 笔记（边查边写）

## 编号核对
- 全目录 ls：最大 R-334（R-328~R-334 连续占用，无 R-323/326/327/335）
- 本报告编号：**R-335**

## 输入文件大小
- R-334 文件存在，路径：/root/.openclaw/workspace/shared/results/05-量化投资/R-334-量化架构简化重构调整版方案.md
- README.md = 186KB（只 tail 日志区）

## [证据A] R-334 表②要点（组件处置基线）
- engines.json 双落盘+30处硬编码：收敛为 model/registry 单份，改 server.js 读路径 L2120/L2711（GM15）
- 五门禁两代字段（G0-G6 vs g1-g6）：合并→统一门禁 schema，注册式 gate spec（GM6）
- 影子观察三实现（_shadow_update/engines_shadow_evaluate_gold/a12_shadow_eval）：合并→合一，复活 R-259 通用版（GM7）
- paper_engine vs paper_engine_gold：保留有意隔离，抽公共层 quant_common（D7/GM9）
- 进化双轨 D6：合并单轨=evolution_pipeline，停 p3_3 cron 需用户批准
- FactorMAD 辩论：OpenClaw 双子代理最小版，产物走既有 N4-N8 链路，不新增落地通道
- qlib 迁移：双轨验证后裁决，口径对齐四项（PIT/qfq/涨跌停掩码/成本模型）

## [证据B] task-0501-notes 关键事实（两版本线实证）
- registry 线（全自动）：evolution_pipeline 五操作 backtest/evaluate/activate/rollback/override；STATUS_ENUM candidate→pending→active→sota→retired；g1-g6 门禁（icir_is_min=0.5, oos_p_min=0.05, max_corr_max=0.7, dsr_min=0.95, logic 非空, MDD恶化≤2pp 一票否决）；PASS⇒_do_activate 自动（R-220#8/task-0345）
- engines.json 线（半自动）：多引擎状态机 schema_version 1；engine A: status=active, layer1.registry.entry=a13_rsraw_e1f10dz；A2=sub_engine_overlay(a14_crowdf2 w=0.5) status=shadow；layer3.tabs 声明引擎→UI映射；gold 引擎不在快照清单=状态机与真实在役集滞后
- 口径漂移警告：任务书所述「五门禁 IC/ICIR/turnover/容量/相关性」与在役 g1-g6 不一致——报告须以 g1-g6 为组件级现状，组合级新增维度另列
- 留痕碎片化：6 种载体（decision-log/experiment-ledger/history/switch_log/n_trials_ledger/cycle-report）
- paper_engine v3：六 action init/daily/rebalance/validate/shadow/timing；guard_override_and_drift 进程内防漂移；rsync_to_vps 内置第6条同步通道
- 甲流程 N1-N10 vs 乙流程 C1-C8 对照已建；可合并点 6 个（data_gate/event_bus/shadow_service/sync_channel/scoring_core/notify_hub）

## [证据C] R-318 中央风控层2（组合=事后叠加的实锤）
- 架构三选一取 α 中央补位器：层2 独立进程，只写 results/layer2/，两引擎 state/NAV 各自独立，层2 只读不写
- 组合净值公式：NAV_L2 = A_total + sleeve_value；backfill_notional = total_A × (1 − ddc_scale)
- ddc 语义：满仓且受控净值回撤≤-0.20→×0.5；降仓中回撤≥-0.05→回补；T 收盘判定 T+1 生效；判定跑在 A 腿补丁内（权威），层2 只读 state.ddc
- 基线：A 引擎 paper_engine.py 70504B cron 16:30 UTC daily；gold paper_engine_gold.py 16474B 07:40 UTC daily；gold status=active_paper（08-25 批准）
- 关键易错点：只补 ddc 释放部分，A 腿择时闲置现金不补黄金
