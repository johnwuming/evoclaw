task-0491 notes init

## 09:28 现状确认
- VPS `/root/.openclaw/workspace-quant/results/engines/` 为空；engines.json 旧版 5999B（A active + A2 shadow，A2 nav_path=results/engines/a2/shadow_nav.csv）。
- server.js: QUANT_REPORTS_DIR=/root/.openclaw/workspace-quant/results；`/api/quant/engines/:id/shadow-nav` 映射 = nav_path 去 `results/` 前缀后 join QUANT_REPORTS_DIR；缺文件时 fallback 平铺 shadow_nav.csv（source=flat）。
- **发现关键问题**：parseShadowNavCsv 固定取第 2 列为 nav。a2 CSV 表头 `date,nav` 没问题；gold CSV 表头 `month,w_applied,gold_ret,mmf_ret,gross,net,nav`，nav 在第 7 列 → 直接同步后解析会错（会把 w_applied 当 nav）。
  → **改 server.js 理由**：需增强 parseShadowNavCsv——若表头存在则按表头列名定位 nav 列；无表头行为不变。属于解析器增强而非映射逻辑改动，向后兼容 a2。
- shared 副本四件套（04-投资研究/engines/gold/）：shadow_nav.csv 158 行(2013-08..2026-08, 末点 nav=2.6046)、shadow_nav_seed.csv 同、mmf_monthly_push.csv、paper_state.json(08-25 06:10 新于其他文件)。
- paper_state.json 关键字段：status=active_paper, current_weight=0.0, open{month:2026-08, nav_open:1.0, stub:true}, last_signal{month_end:2026-07-31, px:8.433, sma200:9.479, vol60_ann:0.220, w_signal:0.0}, marks=[{date:2026-08-24,px:9.564,nav:1.0}...], months=[]（未结月）。
