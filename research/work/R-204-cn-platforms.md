# R-204 中国量化平台工作流与信息架构调研笔记

- 调研日期：2026-08-15
- 调研对象：聚宽 JoinQuant、米筐 RiceQuant、BigQuant、vnpy(VeighNa)、优矿 Uqer（补充）
- 方法说明：配置的 web_search 工具不可用，改用 web_fetch 直接抓取官方文档/GitHub 仓库，并用 Bing 检索定位入口。聚宽官网（joinquant.com）为前端渲染 SPA，docs.joinquant.com 域名当前无法解析，聚宽部分环节的官方一手佐证受限，已在文中明确标注资料可信度。

---

## 1. 聚宽 JoinQuant（joinquant.com）

**资料可信度**：官网描述与 jqdatasdk 仓库摘要为一手来源；模块划分细节部分来自第三方平台对比文章（rlut.cn）与知乎/雪球社区文章标题，仅作参考。

- **工作流全流程**：聚宽定位"全栈量化服务"：云端研究环境（在线 Notebook）→ 因子/策略编码 → 回测（支持按天/按分钟，事件驱动）→ 模拟交易（云端托管、按日定时运行，可绑定微信推送交易信号）→ 实盘（官方"高速实盘交易接口"+ 券商通道；社区主流方案是"聚宽 + QMT"桥接，即聚宽出信号、QMT 执行）。官方首页自述："为量化爱好者（宽客）量身打造的云平台……精准的回测功能、高速实盘交易接口"。来源：https://www.joinquant.com/ ；https://cn.bing.com/search?q=JoinQuant+%E8%81%9A%E5%AE%BD+%E5%B9%B3%E5%8F%B0+%E6%A8%A1%E6%8B%9F%E4%BA%A4%E6%98%93+...
- **核心模块与信息架构**（据第三方综述+社区内容）：我的策略（回测）、研究环境（Research，在线 Jupyter，配 jqdatasdk 数据）、模拟交易（单独列表页管理，展示每日收益/持仓/日志）、社区（策略分享与克隆）、帮助文档 API。新版入口为"聚宽 Everything"（everything.joinquant.com），并向本地化服务转型：jqdatasdk 是"简单易用的量化金融数据包"，官方自述提供"专业量化投研平台、本地数据服务"。来源：https://everything.joinquant.com/login ；https://github.com/JoinQuant/jqdatasdk
- **模拟盘→实盘桥接**：同一套策略 API（initialize/handle_data/run_daily 等回调 + order 函数族）在回测、模拟、实盘三个环境复用，保证代码一致性；实盘多为"聚宽信号 → QMT/miniqmt 执行"的松耦合桥接（社区方案：https://xueqiu.com/2203364439/365153915 、https://zhuanlan.zhihu.com/p/1981761871095800922 ，官方文档细节本次未能直接验证）。
- **借鉴点**：①"研究→回测→模拟→实盘"四段式云端动线，模拟盘作为实盘前的常驻检查点；②微信/消息推送把模拟盘信号送达用户，形成"人在环"的半自动实盘过渡；③数据 API（jqdatasdk）与平台解耦，研究可在本地进行。

## 2. 米筐 RiceQuant（ricequant.com）

**资料可信度**：官方文档与开源仓库，一手。

- **工作流全流程**（RQSDK 官方手册）：RQData（金融数据 API，2005 年至今 A 股行情、财务 Point-in-Time、风格因子等）→ RQFactor（因子投研：编写与检验）→ RQOptimizer（股票组合优化）→ RQAlpha-Plus（回测引擎，`rqalpha-plus run -f strategy.py -s -e -fq 1m --plot`）→ 实盘模拟（ricequant.com/algorithms 云端运行，微信/邮件推送交易信号）→ 实盘交易（RQAlpha 从"数据获取、算法交易、回测引擎，实盘模拟，实盘交易到数据分析"提供全套方案）。来源：https://www.ricequant.com/doc/rqsdk/index-rqsdk ；https://www.ricequant.com/doc/rqsdk/manual-rqsdk ；https://github.com/ricequant/rqalpha
- **核心模块与信息架构**：网页平台"投资研究"版块即基于 RQSDK，且整套环境可本地化（conda + VS Code/PyCharm，官方还提供 Claude Code/Cursor/Copilot 的 AI 编程工具配置指南）。四组件各司其职：rqdatac（数据）→ rqfactor（因子）→ rqoptimizer（优化）→ rqalpha_plus（回测，依赖前两者）。策略代码结构为 `init / before_trading / handle_bar / after_trading` 回调 + `update_universe` 股票池 + `order_*` 下单 API。社区策略管理：Ricequant 是"开放的量化算法交易社区，提供免费的回测和实盘模拟环境"，策略集中在 /algorithms 页运行与分享。来源：https://www.ricequant.com/doc/rqsdk/manual-rqsdk ；https://github.com/ricequant/rqalpha
- **回测引擎设计**：RQAlpha 采用 Mod 插件架构（Mod Hook）：sys_accounts（下单与持仓模型）、sys_simulation（模拟撮合与回测事件源）、sys_risk（事前风控）、sys_analyser（逐日订单/成交/持仓记录与风险指标输出 pickle/csv/plot）、sys_scheduler（定时任务）等。回测与模拟共用同一撮合抽象。来源：https://github.com/ricequant/rqalpha ；https://rqalpha.readthedocs.io/zh_CN/latest/intro/overview.html
- **模拟盘→实盘桥接**：策略本地/云端同一份代码，RQAlpha 的 mod 机制把"事件源 + 撮合"做成可替换件（sys_simulation 支持回测与模拟交易），实盘通过对接交易接口的 mod 扩展实现；数据层 RQData 统一供数避免研究/实盘数据不一致。
- **借鉴点**：①"数据/因子/优化/回测"四件套按依赖关系分层组合，是最清晰的个人量化工具链蓝本；②本地 IDE + 本地数据缓存（bundle）+ 云端模拟并行的双轨制；③回测结果输出为结构化 pickle（summary/portfolios/positions/trades），便于二次分析。

## 3. BigQuant（bigquant.com）

**资料可信度**：官网首页自述、官方文档与 AI 策略广场，一手。

- **工作流全流程**：数据平台（PB 级金融数据）→ 因子研究（2000+ 基础因子库 + 表达式引擎自定义衍生因子，"因子构建与分析……更快发现有效因子"）→ 模型（自动机器学习、超参搜索、滚动训练）→ 策略（可视化建模 + Python 代码无缝互转："模块化的可视化开发环境，与 python 代码版无缝集成"）→ 回测 → 模拟交易 → 实盘（官网自述"实盘交易模拟交易、实盘交易无缝对接"；社区讨论实盘走 QMT 链路）。来源：https://bigquant.com/ ；https://bigquant.com/doc/index.html
- **核心模块与信息架构**（官网主导航即信息架构）：首页 / 编写策略 / 数据平台 / 因子研究 / 我的交易 / 量化学院 / 知识库（wiki）。知识库 wiki 是社区核心：策略分享（每篇附因子逻辑、调仓规则、绩效）、大赛（北大金融 AI 智能体大赛等，含提交运行与私榜）、CoWork（AI 助手）使用心得、直播课文字稿。AI 策略广场（/square/ai）以卡片流展示策略（标题含年化/累计收益/最大回撤），点击进入策略详情可克隆。旗舰版提供 AIStudio Connector：本地 VS Code 经 SSH 连接云端 AIStudio 开发环境。来源：https://bigquant.com/wiki ；https://bigquant.com/square/ai ；https://bigquant.com/wiki/doc/hWARH1GWVP
- **因子库组织方式**：文档将"因子库（data_features）"列为数据目录的一级条目，与历史数据、财报、宏观并列；因子用表达式引擎（big_expr）定义，交易引擎（module_trade）负责撮合执行。来源：https://bigquant.com/doc/index.html
- **模拟盘→实盘桥接**：官方口径"模拟交易、实盘交易无缝对接"（同一策略对象在两种模式间切换）；细节页面为登录后内容，本次未直接验证。
- **借鉴点**：①可视化 DAG/模块化建模与代码双向转换，降低策略流水线的搭建成本，同时不锁死代码逃生门；②表达式因子引擎（`close/lag(close,N)-1` 一类表达式直接定义因子）是个人因子库最省事的组织方式；③"知识库=策略库+课程+大赛"的社区信息架构，策略卡片携带标准化绩效元数据便于筛选。

## 4. vnpy / VeighNa（github.com/vnpy/vnpy）

**资料可信度**：GitHub README、官方文档、Gitee 源码镜像，一手。

- **事件驱动引擎架构**：`vnpy/event/engine.py`（145 行）实现极简事件引擎：`Event(type, data)` 对象 + `Queue` 队列 + 后台分发线程（`_run` 取事件→`_process` 按类型分发到 `handlers[type]`，再分发给 general handlers）+ 独立 Timer 线程每秒生成 `eTimer` 事件。核心 API：`put / register / unregister / register_general`。整个交易程序以此为中心：`run.py` 标准启动为 `EventEngine() → MainEngine(event_engine) → add_gateway(CtpGateway) → add_app(CtaStrategyApp) → MainWindow`。来源：https://github.com/vnpy/vnpy/blob/master/vnpy/event/engine.py ；https://github.com/vnpy/vnpy
- **模块体系**：三层结构——核心框架（event 事件引擎、trader 主引擎、gateway 交易接口如 CTP/XTP/IB 约 20 余个、database 数据库适配器、datafeed 数据服务适配器如迅投/RQData/TuShare/Wind）、策略应用（cta_strategy CTA 引擎、portfolio_strategy 组合策略、spread_trading 价差、option_master 期权、algo_trading 算法执行 TWAP/Iceberg、script_trader 脚本）、工具（cta_backtester 图形化回测、data_manager/data_recorder 数据管理与录制、risk_manager 事前风控、paper_account 本地仿真、web_trader、rpc_service 分布式）。4.0 新增 vnpy.alpha 模块（受 Qlib 启发）：dataset（因子特征工程，含 Alpha158）→ model（Lasso/LightGBM/MLP 统一 API）→ strategy（截面多标的/时序单标的）→ lab（投研流程管理：数据、训练、信号、回测一体）。来源：https://github.com/vnpy/vnpy ；https://www.vnpy.com/docs/cn/index.html
- **回测与实盘共用代码的机制**：CTA 策略模板类的 `on_bar/on_tick/on_trade` 等回调与 `buy/sell` 接口在回测器（cta_backtester 加载历史数据逐根推送）与实盘引擎（EventEngine 订阅行情推送）中是同一套代码，差别只在数据来源与订单去向——撮合层被抽象掉了。策略以"类 → 实例"管理：同一策略类可生成多实例交易多品种，参数（parameters 列表）与变量（variables 列表）由 UI 自动识别渲染。实盘启动前必须"初始化"：load_bar 回放约 10 天历史 K 线恢复指标 + 从 cta_strategy_data.json 载入缓存变量（持仓、移动止损高点等交易状态），保证与上次退出时状态一致。来源：https://www.vnpy.com/docs/cn/community/app/cta_strategy.html ；https://www.vnpy.com/docs/cn/community/app/cta_backtester.html
- **模拟与实盘统一设计**：paper_account 本地仿真模块接管所有委托（合约的"交易接口"列显示为 PAPER），基于实时盘口按到价成交规则撮合，且"委托成交后，先推送委托状态更新 OrderData，再推送成交信息 TradeData，和实盘交易中的顺序一致"；持仓落盘持久化。回测/仿真/实盘三种模式对策略代码完全透明。来源：https://www.vnpy.com/docs/cn/community/app/paper_account.html
- **借鉴点**：①回测-实盘一致性的黄金范式：策略只面向回调接口编程，数据源与订单路由由框架注入；②策略实例化（参数/变量声明式暴露给 UI）天然支持参数优化与多品种并行；③"初始化=历史回放+状态缓存恢复"是从模拟走向无人值守实盘的关键工程细节；④事件引擎仅百行代码，个人系统完全可以自持。

## 5. 优矿 Uqer（uqer.datayes.com，补充）

**资料可信度**：官网可访问但页面为前端渲染，仅目录页与第三方综述可用，细节有限。

- 通联数据（DataYes）2015 年推出的量化平台，定位机构级；官网现称"优矿 - 大数据时代的量化投资"，labs 版块为"数据分析平台，提供 AI 赋能的投资工具和数据包"。数据为核心竞争力（依托通联数据体系：行情、基本面、因子/风险模型），研究环境为在线 Notebook，数据调用走 UQER SDK + Token 凭证。来源：https://uqer.datayes.com/ ；https://uqer.datayes.com/labs/ ；https://uqer.datayes.com/help/faq/
- 工作流模块划分、模拟盘→实盘机制的官方一手资料**未找到**（帮助文档为 SPA 无法抓取正文）；第三方综述称其覆盖"回测、优化和实盘，免费版限制较多"，此点仅作参考。来源：https://www.rlut.cn/news/liang-hua-jiao-yi-hui-ce-ping-tai-shen-du-dui-bi-ju-kuan-mi-kuang-you-kuang-san-da-ping-tai-he-xin-q.html
- 借鉴点：数据 Token 化的 SDK 调用模式（本地研究环境 + 云端数据服务）与聚宽 jqdatasdk 同构。

---

## 6. 横向对比与对个人量化的总体借鉴

| 维度 | 聚宽 | 米筐 | BigQuant | vnpy |
|---|---|---|---|---|
| 形态 | 云平台+本地数据 SDK | 云平台+本地 SDK（RQSDK） | 云平台（AIStudio）+本地 IDE 连接 | 纯本地开源框架 |
| 工作流核心 | 研究→回测→模拟→实盘 | 数据→因子→优化→回测→模拟/实盘 | 数据→因子(DAG)→ML模型→策略→模拟→实盘 | 数据→策略类→回测→仿真→实盘 |
| 一致性机制 | 同一套策略 API 贯穿三环境 | Mod 插件替换事件源/撮合 | 官方称模拟/实盘无缝对接 | 回调接口统一，路由由框架注入 |

**对个人量化最值得抄的设计**（按优先级）：
1. **vnpy 的回调抽象 + 状态恢复**：策略代码与运行模式解耦，实盘启动时历史回放+状态缓存，是代码一致性最强的方案；
2. **米筐的四组件分层**（数据/因子/优化/回测）+ 回测输出结构化文件，便于自动化流水线；
3. **BigQuant 的表达式因子引擎 + 可视化/代码双向**：因子以表达式形式沉淀为可检索库；
4. **聚宽的模拟盘消息推送**：模拟→实盘之间加"人在环"检查点，用微信/IM 推送降低冷启动风险。

（完）
