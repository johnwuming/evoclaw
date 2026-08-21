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

## 2. 补查结论（16:40 前）

### task-0408 crowding 快照先例（cron+锁存+告警模板）
- cron `35 19 1 * *` + `flock -n /tmp/snapshot_crowding.lock` + append-only 同月幂等 [skip] + 锁「最近完整月」
- 通知走 notifications-queue.jsonl → notify_hub → auto_sync → VPS
- 采集源周频（周日 07:00 collect_crowding.py），qfq 日更工作日 18:00
- 注：任务书提的 task-0418 实为媒体解析任务，快照先例真身是 task-0408（R-252 上游链路确认）

### HP registry 实况（ssh noname@10.12.192.174:22）
- model/registry/ 含 a13_rsraw_e1f10dz.json（A 在役）、a12_s2_reb.json（版本内影子）、a14_crowdf2.json、a9_ranksum_raw.json、v0_seed.json + v1/v2 历史线 + *.main.json.snapshot 备份
- HP crontab 关键行：a12 evaluate 每月2日17:10；a10 monitor 每月3日09:05；qfq 日更工作日18:00；qfq 周日 init+rebuild 18:00；crowding 快照 1日19:35；notify_hub 每小时10分；W6 退市 1日06:00

### server.js 锚点复核（grep，未全读）
- D-1 七条 quantDeprecated：L1833/1834/1835/1836/2663/2664/3508（fn L1829）✓
- D-2 连字符四条：**L2015/2032/2056/2085（R-256 行号勘误：实际在文件前部）**；斜杠版 L3553/3585/3645/3677 ✓
- D-3：L2751 baseline/nav、L2773 baseline/yearly ✓；D-4 endtoend L3924 ✓
- 隐藏页 div：L6854 quant-page-models、L6855 quant-page-btlc ✓；_V5_TABS L8897（六 Tab）✓
- **重大发现：server.js 未被 git 跟踪**（git ls-files 报错 + status 显示 `??` untracked，仓库末次提交 2026-08-02）→ R-256 的 git 分支回滚设想当前不可直接用，S0 需先建基线（本设计新增 S0.0）
- 量化 GET 路由计数：54 条；agent-dashboard.service systemd 在役 ✓

## 3. 设计决策（边写边记）
1. engines.json 放 HP registry 同目录（选型 b），VPS 侧经 pull-hp-metrics 扩展同步至 workspace-quant/model/registry/，看板启动读取、缺失降级硬编码单引擎 A
2. 跨引擎影子状态记 engines.json，不进 registry gate.shadow_watch（保 a12 版本内影子语义纯净，两机制正交并存）
3. 中央风控初值全部留白（⏳ 标注）；配置器 ERC 框架+伪代码；组合门与引擎内择时协调三规则（先动顺序/总敞口下限/恢复独立计时）
4. 组合 NAV：月频再平衡窗口、w 阶梯函数、无外部现金流假设、对账三校验+命令设计 portfolio_recon.py
5. B 数据运维：月1日19:05 采集+19:35 快照错峰（不对——采集19:05与快照19:35同日不冲突，错峰30min）；断供预案重试3次+跨日至3日+备用源人工补数
6. S0 顺序：S0.0 基线 git 化 → S0.5 隐藏页拍板（影响 S0.4）→ D-1/D-2/D-3 各一组一 commit → S0.4 endtoend（依赖 H2 复活决策）→ S0.6 冒烟+路由数对账 54→41
7. 隐藏页推荐选项甲（复活）：论据=H2 是影子前台唯一消费点，选乙则 S2 要重建前台

## 4. 工具输出累计
~85KB（受控）
