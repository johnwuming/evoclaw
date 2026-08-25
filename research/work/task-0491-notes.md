task-0491 notes init

## 09:28 现状确认
- VPS `/root/.openclaw/workspace-quant/results/engines/` 为空；engines.json 旧版 5999B（A active + A2 shadow，A2 nav_path=results/engines/a2/shadow_nav.csv）。
- server.js: QUANT_REPORTS_DIR=/root/.openclaw/workspace-quant/results；`/api/quant/engines/:id/shadow-nav` 映射 = nav_path 去 `results/` 前缀后 join QUANT_REPORTS_DIR；缺文件时 fallback 平铺 shadow_nav.csv（source=flat）。
- **发现关键问题**：parseShadowNavCsv 固定取第 2 列为 nav。a2 CSV 表头 `date,nav` 没问题；gold CSV 表头 `month,w_applied,gold_ret,mmf_ret,gross,net,nav`，nav 在第 7 列 → 直接同步后解析会错（会把 w_applied 当 nav）。
  → **改 server.js 理由**：需增强 parseShadowNavCsv——若表头存在则按表头列名定位 nav 列；无表头行为不变。属于解析器增强而非映射逻辑改动，向后兼容 a2。
- shared 副本四件套（04-投资研究/engines/gold/）：shadow_nav.csv 158 行(2013-08..2026-08, 末点 nav=2.6046)、shadow_nav_seed.csv 同、mmf_monthly_push.csv、paper_state.json(08-25 06:10 新于其他文件)。
- paper_state.json 关键字段：status=active_paper, current_weight=0.0, open{month:2026-08, nav_open:1.0, stub:true}, last_signal{month_end:2026-07-31, px:8.433, sma200:9.479, vol60_ann:0.220, w_signal:0.0}, marks=[{date:2026-08-24,px:9.564,nav:1.0}...], months=[]（未结月）。

## 09:36 VPS 侧同步完成（步骤1）
- 备份：`results/engines.json.bak-task0491-20260825-093559`（旧版 5999B）
- 新 engines.json = HP registry 版（md5 3b07d833…，14649B）：A active / A2 shadow / gold_trend_sma200 active(standalone_active, shadow.mode=standalone_b, nav_path=results/engines/gold/shadow_nav.csv, evals 1 条 ann=0.0759 mdd=-0.059 calmar=1.286 corr_A_gold=-0.040, promotion 有激活记录)
- engines/gold/ 四件套 md5 与 HP 一致（shadow_nav=seed=3654c3e8…, mmf=cc8de822…, paper=f709177f…）
- HP 拉取通道：scp SFTP 不可用（subsystem request failed），用 ssh+cat 逐文件取。

## 09:38 端点实测（同步后、改码前）
- GET /api/quant/engines → ok:true, 3 引擎含 gold（active, evals=1）✓
- GET /api/quant/engines/gold_trend_sma200/shadow-nav → ok, source=nav_path, points=157, 末点 2026-08-31 ✓，**但 nav 全错（读到第2列 w_applied=0）→ 必须增强 parseShadowNavCsv 按表头定位 nav 列**（已批准例外：server.js 新增端点+解析器增强）
- paper_state.json：marks=1 条 {date:2026-08-24, px:9.564, nav:1.0}，months=[]，无 updated_at 字段（用文件 mtime）

## 09:40 server.js 改动完成（语法 OK，服务重启 active）
1. parseShadowNavCsv 表头驱动列定位（nav 列按表头名找，兼容 gold 第7列 + a2 date,nav 第2列；无表头保持原行为）
2. 新端点 GET /api/quant/engines/:id/paper（路径由 shadow.nav_path 目录推导 paper_state.json；缺文件 ok:false；返回 status/current_weight/last_signal{px,sma200,vol60}/marks/open/months_closed/activated_at(registry promotion)/updated_at）
3. loadPaperQuant：shList filter 加 standalone_b；enginePaper fetch + sig + 传参
4. renderCrossEngineShadowCard：standalone_b 单线图 + 已激活徽标 + eval 摘要（ann/mdd/calmar/corr_*）+ paper 实时小区块（激活日期/仓位 w/mark NAV/marks 数/已结月）
5. 调用处 13346 传 enginePaper

## 09:42 端点实测（改码+重启后）
- GET /api/quant/engines/gold_trend_sma200/shadow-nav → ok, source=nav_path, points=157（2013-08-31 nav=1.0038 … 2026-08-31 nav=2.6046），nonzero=157 ✓
- GET /api/quant/engines/gold_trend_sma200/paper → ok, available, status=active_paper, current_weight=0, months_closed=0, activated_at=2026-08-25T00:35:00+08:00, last_signal{month_end:2026-07-31, px:8.433, sma200:9.4791, vol60_ann:0.2201, w_signal:0}, marks=1 {date:2026-08-24, nav:1, px:9.564}, open{month:2026-08, w:0, nav_open:1} ✓
