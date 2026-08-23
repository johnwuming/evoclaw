# task-0470 架构评估过程笔记（R-290）

> 任务：按 R-256/R-259 四层多引擎架构重估系统。纯设计，零代码改动。
> 2026-08-23 17:21 启动。恢复点：本文档。

## 0. 任务元信息
- taskId: task-0470，expected_output: R-290（路径字段写 01-AI行业研究/，经核实为陈旧值；R-2xx 量化文档全在 05-量化投资/，报告落 05-量化投资/）
- 主 agent 已答 ①A2 非中央风控（是 A 的 sub_engine_overlay，层1 防御叠加臂）②模型页择时仓位趋势 = q3z×EW-MA200 仓位系数（层1 内化择时），与中央风控（层2 哑层）不冲突。本任务聚焦 ③。
- 必读：R-256（四层架构+模块映射+S0-S4 基座）、R-259（施工图：engines schema/影子泛化/中央风控三组件/组合对账/S0-S4 清单）、R-282（A2=sub_engine_overlay 资格来源）、R-286（engines.json A+A2 落地）。

## 1. 现状核实（2026-08-23 17:21）
- engines.json（VPS 镜像 /root/.openclaw/workspace-quant/results/engines.json，5999 字节，8/23 13:44）只有 A(active) + A2(shadow, sub_engine_overlay, parent=A)。
- 目录结构确认：05-量化投资/ 有 R-256~R-289 全部量化文档；01-AI行业研究/ 无 R-doc。
- 中央风控层2 三组件哑层：单引擎 w=100%，初值留白（引用现状，不重查）。

## 2. 文档阅读笔记（边查边写）

（后续逐篇追加）

## 2.1 R-256 阅读笔记（2026-08-21，task-0416，纯规划）
### 四层架构（用户定调）
- 层0 共享数据基础设施：采集/PIT/快照/退市，服务所有引擎，不隶属任何引擎。
- 层1 引擎层（N 可插拔同构）：信号/选股 + 择时与回撤内化（引擎自己消化择时，顶层不做方向择时）+ 独立 NAV + 独立 registry 版本线 + 影子观察通道。实例 A=在役 a13_rsraw_e1f10dz（微盘选股）；候选 B=全A行业轮动（E1 达线 R-255，待 E2）。
- 层2 中央风控层（独立横切，不属于任何引擎）：战略配置器（N 引擎权重按风险贡献定）+ 再平衡带宽（偏离机械拉回，不追近期表现）+ 组合级回撤门（保险性质）。哑层、无方向观点。单引擎 w=100% 无事可做，第二引擎上线才激活。
- 层3 组合与呈现层：组合净值=Σ wi×NAVi（N 通用聚合）+ 各引擎独立呈现。
- 引擎上线路径：双 NAV 影子观察先行（参照 a12_s2_reb R-248），影子期满再谈真金；信号层合并远期。

### 看板现状判定（R-256 核心发现）
1. 看板是事实上的「引擎A单机版」：六子Tab 全部围绕 a13 单 registry 版本线；/api/quant/registry 无 engine 概念，多 active 并存按 created_at 取最新（L2410）——单引擎假设代码残留，多引擎化第一缺口。
2. 层2 中央风控零组件：risk-status/crowding 是引擎A监控（挂 paper 页），不是组合级风控。
3. 两隐藏页僵尸 UI：控制面页 H1（quant-page-models，M2.5-M2.9）+ 四层归因链页 H2（quant-page-btlc，M3.0-M3.7）代码完整、取数正常、被移出 Tab 序列不可达。判「迭代（复活）」。R-259 建议复活 H2。
4. 13 条路由可删（3 组：7 quantDeprecated + 4 连字符 paper + 2 baseline）+ endtoend 待确认。
5. 影子观察「有后端、无前台」：lifecycle 端点已实现 shadowWatch 扫双 registry 的 gate.shadow_watch（L2614-2624），唯一前台消费点在隐藏页 H2。

### 模块映射要点（四分类：复用12/迭代6含复活2/删3组13条/新增4）
- 复用：数据健康/数据资产盘点/同步管道/因子页/模型页/回测页/模拟实盘页/timing 系/risk-status/crowding/报告页等。
- 迭代：头部新鲜度一致性（N≥2 按引擎分列）、迭代历史（per-engine 时间线）、registry 双目录（引擎→registry 线显式映射）、影子观察后端（跨引擎+前台复活）、H1/H2 复活。
- 新增（全等触发）：N1 引擎B全链路实例化（触发：B过E2+批准上影子）；N2 中央风控仪表（触发：S4 第二引擎真金上线）；N3 组合净值聚合页（触发：S4）；N4 引擎清单元数据 engines 概念（触发：S2 影子通道实例化时一并落地，最大结构缺口）。
- S0-S4 路线图：S0 路由清障+隐藏页处置（无前置）；S1 B 过 E2（纯文档）；S2 影子通道通用接入首实例（N4+B 影子，B过E2+批准）；S3 影子期 3-6 月；S4 中央风控激活（N2+N3，影子期满+真金批准）。

## 2.2 R-259 阅读笔记（2026-08-21，task-0420，施工图）
### engines.json schema（缺口1，R-256 N4 补全）
- 选型 b：真源 HP ~/quant-evolve/model/registry/engines.json（与 registry 同目录）→ pull-hp-metrics 扩展同步到 VPS → server.js 启动读取，缺失/解析失败降级硬编码单引擎 A（看板永不因 engines.json 启动失败）。
- schema_version=1；引擎字段：engine_id/name/status(active|shadow|off)/layer1.registry(hp_dir,entry,version_line)/layer1.nav_source(kind,path_hp,frequency,sync)/layer1.signal_desc/layer1.timing_internal/layer3.tabs/api_prefix/shadow.mode(none|cross_engine)/shadow.since/nav_path/required_clean_evals/audit(created_at,by,changes append-only)。
- 单引擎→N 迁移：一次性初始化脚本（S2 首步）从实况生成 A 条目，校验 engine_id=A 与 registry active 一致才落盘；看板降级切换文件驱动对 A 零变化。B/C 接入=append+audit，纯增量。

### 影子通道跨引擎泛化（缺口2）
- 与 a12 版本内影子正交并存：跨引擎影子记 engines.json shadow.mode；版本内影子留 registry gate.shadow_watch（晋升语义）。a12 机制不动。
- 通用影子接入契约四条件：①E2 预注册判胜门槛过②评分制 v1.1 过③用户显式批准④engines.json 登记+影子 NAV 管道+数据管道连续 2 月度点无断供（先空跑）。
- 影子数据管道：HP b_shadow_engine.py 月频「真数据假交易」；落 HP results/engines/b/shadow_nav.csv（month,nav,ret,weights_json）；每月 2 日 19:35 更新；看板端点 /api/quant/engines（清单+状态）+/api/quant/engines/B/shadow-nav；前台=H2 内影子清单复活+paper 页并列。
- 影子期治理：engines_shadow_evaluate.py 每月 3 日 09:35 跑 → shadow.evals[] → clean_evals 计数。终止判据：连续 N 月低于门槛/corr(A,B) 超上限/数据断供≥K 月/用户手动。晋升一律人工确认，不设自动上岗。

### 中央风控三组件参数化（缺口3，初值全 ⏳ 留白）
- 战略配置器：风险贡献法 ERC（输入各引擎月收益，W 建议36月，σ/corr 窗口；等波动起步迭代收敛；clip+归一；季度重算，**重算结果须用户确认才生效**）。极端规则：N=1→w=1；N=2 且 |corr|>0.85 切换等波动封顶+告警+人工；新引擎历史<12月用影子数据补窗口标「影子混合估计」；off 剔除重算。
- 再平衡带宽：相对+绝对双规则（|w_actual−w_target|/w_target>band_rel 或 >band_abs）；漂移公式 w_actual_i(t)=w_i(t−1)(1+r_i(t))/Σ...；机械执行：触发→下月调仓窗口一次性拉回，不分批不追表现。
- 组合回撤门：组合净值峰值回撤>gate_dd → 整体降仓系数 φ 等比缩放全部引擎敞口（层2 唯一仓位动作）；恢复=收复至峰值×(1−gate_dd×recov_ratio)或最长降仓期。
- 与引擎内风控协调三规则：①先动层级（引擎内先动、组合门兜底；多数引擎已自降则门照常叠加）②总敞口下限 floor_exposure 防过度叠加③恢复独立（引擎内各自恢复、组合门独立计时）。

### 组合 NAV 对账（缺口4）
- NAV_p(t)=Σ w_i(t)×NAV_i(t)，w 为阶梯函数（相邻再平衡点间固定）；再平衡=每月首个交易日；月内冻结；封闭式无外部申赎；影子期可选「影子参考组合」仅展示不入对账。
- 对账三校验：①逐月分解一致性 NAV_p(t)/NAV_p(t−1)=Σ w_i×(NAV_i(t)/NAV_i(t−1)) tol 1e-6 ②端点手工重算③权重守恒 Σw=1。命令 portfolio_recon.py。

### S0 执行清单（缺口6）+ 回滚验收（缺口7）
- S0.0 基线（server.js 未被 git 跟踪实锤，必须先 git add 基线或 .bak）；S0.5 隐藏页拍板（先于删路由）；S0.1 删 D-1（7 桩+L1829 fn）；S0.2 删 D-2（L2015/2032/2056/2085）；S0.3 删 D-3（L2751/2773）；S0.4 endtoend 依赖 S0.5（H2 复活→保留，e2e-curves 是 H2 数据源）；S0.6 全局验证（node --check、restart、4 端点冒烟、路由数 54→41）。
- 隐藏页两选项：甲复活（推荐，H2 是影子前台唯一既有消费点，乙会与 S2 冲突=重复建设）；乙下线（S2 前台改 paper 页内嵌）。
- S2 回滚：删 engines.json B 条目即回单引擎，看板读不到自动降级硬编码 A。
- S4 回滚：三组件独立开关 engines.json layer2.enabled=false；权重回退=audit 上一目标。
- 与 R-256 冲突 4 条：D-2 行号勘误、S0.0 基线新增、隐藏页明确推荐甲、engines.json 初始化加校验+降级。
