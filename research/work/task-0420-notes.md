# task-0420 过程笔记：多引擎实施方案补全（R-259）

## 0. 任务状态
- 16:26 task-0420 置 running ✓
- 编号确认：全库 find R-2[45]*/R-26*，实存最大 R-256（05-量化投资）；R-257/R-258 未落盘（并行任务预占：R-257 未知归属，R-258=task-0421 B 预注册）。本报告取 **R-259** ✓

## 1. 材料读取结论

### R-256（基座，16.5KB 全读）
- 四层架构：层0 共享数据 / 层1 引擎层(N 个同构：信号+择时内化+独立NAV+独立registry版本线+影子通道) / 层2 中央风控（战略配置器+再平衡带宽+组合回撤门，哑层无方向观点）/ 层3 组合呈现（Σwi×NAVi）
- 关键事实：
  - `/api/quant/registry` 无 engine 概念，多 active 取 created_at 最新（L2410）= 单引擎假设残留
  - 影子后端已存在：lifecycle 端点 shadowWatch 扫双 registry 的 gate.shadow_watch（L2614-2624），前台唯一消费点在隐藏页 H2
  - 两个隐藏页：H1=quant-page-models（控制面），H2=quant-page-btlc（归因链），代码完整但无 qseg 按钮不在 _V5_TABS（L6854/6855 vs L8897）
  - 13 条可删路由分 3 组：D-1 七条 quantDeprecated 弃用桩（L1829 fn；L1833-1836、L2663-2664、L3508）；D-2 四条连字符旧 paper 路由（paper-summary/paper-nav/paper-trades/paper-portfolio，被斜杠版 L3553-3696 替代）；D-3 baseline/nav+baseline/yearly（L2751/L2773，零引用）；另有 endtoend（L3924 约 386-392 行）待确认
  - S0-S4 阶段：S0 清障（无前置）/ S1 B过E2 / S2 影子通道+N4 / S3 影子期3-6月 / S4 中央风控激活
  - 新增 N1-N4 全部「等触发不实施」；N4=engines 元数据是「最大结构缺口」，触发=S2
- 我的任务=R-256 判定的 7 项缺口设计补全，不推翻其定调

### R-248（a12 影子机制，7.8KB 全读）
- 三层结构：L1 月度 evaluate（evolution_pipeline.py cmd_evaluate，只读 registry+nav csv+factor_ic）/ L2 nav 刷新（重跑引擎，mtime 检测降级，接口预留默认关）/ L3 晋升守卫（clean_evals≥required−1 时 exit 42 转人工）
- 语义：clean_evals 0→1→2 自动累加，第 3 期（可能触发自动上岗链 _do_activate）拦截转人工；stat_warn=True 清零
- 机制要点：cron 建议 HP 每月 2 日 17:10；flock 幂等；notifications-queue.jsonl 通知链
- **泛化差异（本设计核心）**：a12 是「同引擎内候选版本 vs 在役版本的影子」（registry 版本线内部 gate.shadow_watch）；跨引擎影子是「引擎 B 的独立 NAV vs 引擎 A 的 NAV」——两个引擎 nav 来自不同管线（A=paper_engine 日频；B=行业指数月频回测/影子）

### R-255（引擎 B E1 画像，5.9KB 全读）
- k=1 行业动量 Top5 达线：245 触发、四五年分段全正、与 a13 相关仅 0.135
- 数据：申万一级 31 行业月频，HP results/work/r0415/sw_industry_monthly.csv（322 月），akshare sw_index_first_info()+index_hist_sw(period=month)，采集限速 0.4s
- 截面演化 16→28→31 行业；E2 待做：成本敏感性/宇宙稳健性/北交所 stock 级排除
- B 若过 E2 进影子：NAV 产出形态=月频调仓的指数级组合（非 stock 级）

### R-252（预注册纪律先例，读前 6KB）
- 预注册要素：假设先行/信号定义逐字复刻/PIT 规则分段/网格+n_trials 上限/判胜门槛先定后跑/一经登记不可改
- task-0421(R-258) 将为 B 写 E2 预注册——本设计只引用其「判胜门槛」占位，不替定数字

## 2. 待补查
- task-0418 crowding 快照 cron+锁存+告警模式（§5 B 数据运维参照）
- registry 目录实况（engines.json 迁移路径设计输入）
- pull-hp-metrics.sh 数据流（NAV 管道现状）
