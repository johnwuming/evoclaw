# task-0416 过程笔记（重派运行，覆盖旧稿）

- 任务：R-256 多引擎架构与量化看板模块映射（task-0416）
- 运行时间：2026-08-21 13:18 起；13:18 任务中心置 running 成功
- 纪律：未读旧草稿报告/旧笔记；全部结论来自本次实查（代码行号均可溯源）
- server.js 实测 745,742 字节 / 13,707 行 → 只做结构抽取（grep/sed）

## 一、看板代码实查记录（tools/agent-dashboard/server.js）

### 1. 顶层导航（L6865-6868）
4 页：任务 / 用量 / 报告 / 量化。showPage() L7021。

### 2. 量化页结构
- 子Tab 声明：`_V5_TABS = ['data','factor','v5model','v5btlc','paper','v5hist']`（L8897，六Tab）
- qseg 按钮：L6837-6842（数据/因子/模型/回测/模拟实盘·灰度/迭代历史）
- quant-page 容器共 8 个：L6849-6857，其中 **quant-page-models（L6854）与 quant-page-btlc（L6855）无对应 qseg 按钮、不在 _V5_TABS** → 隐藏页（UI 不可达）
- 旧 localStorage 值 'models'/'btlc' 被映射到 v5model/v5btlc（L8987）→ 旧页确已被移出导航

### 3. 各可见子Tab 的前端取数（api() helper L6965）
- 头部：freshness（L8821, task-0329）+ consistency（L8844, task-0359）
- data：data-health + data-assets（L9628-9629）
- factor：factor-catalog（L9774）+ factor-ic-series 行展开（L10048/10110）+ data-health（L10137）
- v5model：active(+version) L9087 / active/pos L9088 / version-options L9089；registry 用于解释动态渲染（L12559, task-0387）
- v5btlc：active(+v) L9185 / active/curves(+v) L9186 / version-options L9187；排行表 v5RankTableHtml（L9283）用 version-options 数据
- paper：paper/summary|nav|trades|portfolio（L12174-12177）+ evolution/models→baseline/summary 链（L12179）+ run-status/crowding/risk-status/registry/timing（L12181-12185, task-0278 M4.4/M4.7/M4.8/M4.1 增强注释）
- v5hist：history L9434 + history/:id L9506 + reports/:id 报告查看 L12846/12869

### 4. 隐藏页 H1 = quant-page-models（控制面 M2.x）
loadModelsQuant（L10395），switchQuantTab 不调用它；唯一调用点 L10714（提交想法后刷新自身，而表单只存在于该隐藏页 → 实际不可达）。
取数（L10403-10415）：evolution/models, timing-config, timing, reports, timing-matrix, registry, decisions, pending, ideas, ledger, paper/summary。
渲染（L10870-10896）：择时研究档案（M2.3 旧9信号）、贡献矩阵（task-0288, M2.8/M3.1 替代）、M2.5 决策时间线、M2.6 Pending 确认、M2.7 想法池、M2.9 试验台账、操作队列徽章；quantEnqueueAction（L10703）= idea/rollback/confirm/reject 跨机写队列（POST quant/action）。

### 5. 隐藏页 H2 = quant-page-btlc（回测四层归因链 M3.0-M3.7）
loadBtlcQuant（L10905），switchQuantTab 不调用；唯一调用点 L10970（自身版本切换器 onclick）。
取数：btlc + reports + lifecycle（L10916-10918）。
renderBtlcPage（L11562）：版本切换器/四层归因链（renderBtlcAttributionChain L10974）/对照卡/净值图/分年度/危机段/walk-forward/历代最优/报告库（L11234）/E2E 曲线（btlcE2ELoad→e2e-curves L11374）/验证层（gates+dsr+q4b-contrast, loadQuantValidationLayer L11747, L11584/11624 挂载）/生命周期层（loadQuantLifecycleLayer L11854）。

### 6. 路由层僵尸证据（代码级）
- 显式弃用桩 quantDeprecated（fn L1829）：summary/nav/factors/evolution（L1833-1836）、microcap/status+phases（L2663-2664）、evolution/summary（L3508）= **7 条**
- 连字符旧 paper 4 条（L2015/2032/2056/2085）：KEEP_OLD_DATA_ARCHIVED 门控；全文件 grep 仅路由定义+文件路径注释，无任何前端 api() 调用；被斜杠版（L3553-3696）替代；旧文档 R-207/R-213 有提及（无活消费方）
- baseline/nav（L2751）、baseline/yearly（L2773）：全文各仅 1 处出现=路由定义本身，零前端引用；被 active/curves + baseline/summary 窗口机制替代
- endtoend（L3924, ~386 行逻辑）：零前端引用（前端 m.endtoend 均为字段访问非 API 调用）、零脚本引用 → 无调用者，但因体量大且不排除人工 curl 用途 → 判「待确认」

### 7. 数据与基建
- QUANT_REPORTS_DIR = QUANT_BASELINE_DIR = /root/.openclaw/workspace-quant/results（638 文件：各版本 full/locked nav+metrics+yearly）
- registry 双目录：MODEL_REGISTRY_DIR=results/model（L2832）+ QUANT_REGISTRY_DIR=model/registry（L2315, HP 直写）；model/registry 实况：a12_s2_reb.json（影子线）、a13_rsraw_e1f10dz.json（在役=引擎A）、a14_crowdf2.json（candidate）、a9_ranksum_raw.json、v0_seed.json
- /api/quant/registry（L2410）：**单引擎假设残留**——多 active 并存按 created_at 取最新（task-0392 注释）；无 engine 参数
- 影子观察后端已存在：lifecycle 端点内 shadowWatch 扫两 registry 目录 gate.shadow_watch（L2614-2624, task-0383 机制/task-0379 人工登记/task-0353）——但 lifecycle 前端只在隐藏页 H2 调用 → 影子数据有后端无前台
- HP→VPS 同步：scripts/pull-hp-metrics.sh（scp HP metrics.db + sqlite ATTACH 去重合并，cron */2）
- ⚠ 侧发现：pull-hp-metrics.sh 内硬编码 HP SSH 密码（L8 HP_PASS="123456"）——与 TOOLS.md 秘密约定冲突，建议另行处理（不属本报告范围，仅记录）
- W6 数据资产：data-assets 端点读 w6-snapshots/w6-delisted-summary/w6-pit-summary + 灰卡缓存 hfq（L2243-2270）→ 层0 PIT/快照/退市基建已有产物

## 二、旧文档对照
- R-205（15KB）：旧四Tab（数据·因子/模型/回测·生命周期/模拟实盘）审查，发现因子全显示不通过/9信号只用3/K线新鲜度FAIL等问题
- R-206 v4（26.6KB）：五Tab 设计（数据/因子/模型/回测/模拟实盘）+ M1.1-M4.8 模块清单 + 后端版本体系
- R-207（23.9KB）：产品说明书，五Tab 定稿 + registry 版本对象 + API 设计（8055）
- 与代码不一致：①实际六Tab（+v5hist 迭代历史，task-0343 定序；paper 灰度恢复 task-0376）②M2.5-M2.9/M3.0 已实现但被移出 Tab 序列成隐藏页 ③M4.7 微盘风控卡被弃用（microcap 2 路由成桩），风控改由 risk-status/crowding 在 paper 页承担（task-0278 注释）④API 数量与弃用状态文档未更新

## 三、四层映射判定（草稿）
- 层0：data-health/data-assets/W6 管道/HP 同步/freshness+consistency → 复用为主；N 引擎时 freshness 分列+行业指数通道 = 迭代（B 触发）
- 层1：v5model/v5btlc/v5hist/paper 四页 = 引擎A实例 → 复用；多引擎并列/多 registry/影子前台/两隐藏页复活 = 迭代
- 层2：**现无任何组件**（risk-status/crowding 现属引擎A监控挂 paper 页）；战略配置器/再平衡带宽/组合回撤门 = 新增（等触发）；单引擎期 w=100% 无事可做=时序巧合非架构归属
- 层3：组合净值 Σwi×NAVi 聚合页 = 新增；报告/任务/用量页 = 通用基建复用
- 删除：7 桩路由 + 4 连字符 paper + 2 baseline 子路由（共 13 条，3 组）；endtoend 待确认
- 新增：N1 引擎B全链路通道实例化、N2 中央风控仪表、N3 组合净值页、N4 引擎清单元数据（engines 概念缺口：version-options/registry 均单 active 假设，task-0392 注释为证）

## 四、实施顺序
S0 路由清障+隐藏页处置拍板（与B无关可独立）→ S1 B 过 E2（纯文档）→ S2 影子通道首次实例化 → S3 影子期 3-6 月 → S4 中央风控激活。
