# task-0586 笔记 2026-08-30 15:27:28

## 现状确认
- app.js 20KB（可全读）；config.dataDir=live/data（portfoliosHandler 同源）。
- 旧 overviewHandler：active_pv/sleeves 取自 ctx.projection.composites.active_pv_id（账本 promotion 链）→ 无 executed 事件 → null/[]。
- live/data/portfolios.json：vC-0 status=paper，note 明确「status 以快照文件为权威」。
- versions/vC-0.json：weight_solution.weights={equity_sleeve:0.5802969609176188, hedge_sleeve_gold:0.41970303908238105}；sleeves.<id>.component_ref 有 engine_id/status（A/active；gold_trend_sma200/active_paper）。
- overview.json 仅 nav_series=[]，无 sleeve_stub（nav 口径红线：保持现状 null，本批不动）。
- 改前基线：/overview → active_pv:null sleeves:[]；/portfolios /events?limit=1 /health 均 200（快照存 /tmp/0586-*.json）。

## 改动方案
- 新增 deriveActivePv(config)：portfolios.json → status∈{active,paper}，优先 active，同档 created_ts 最新；无候选→null。
- 新增 deriveSleeves(config,id)：versions/<id>.json → weight_solution.weights 逐条 {id,weight,nav:null,mdd:null,engine:{engine_id,status}|null}；versions 或 weight_solution 缺失→[]；ID_RE 防 traversal。
- overviewHandler 仅替换 active_pv/sleeves 推导源（账本→文件）；nav/nav_chg_1d/mdd/drawdown_pct/last_event_ts/reconciliation_ok 及 ledgerDerived 门卫零变化；删除 sleeve_stub 读取（本就无此键，per-sleeve nav/mdd 无权威源→null 如实，R-377）。

## 验证摘录（2026-08-30 15:39）
- node --check src/app.js → SYNTAX_OK；systemctl restart quant-bff → active
- 验收命令输出：
  `{'portfolio_version_id': 'vC-0', 'status': 'paper'} [('equity_sleeve', 0.5803), ('hedge_sleeve_gold', 0.4197)]`
- /overview 完整 sleeves：equity_sleeve 0.5803 nav=null mdd=null engine={A,active}；hedge_sleeve_gold 0.4197 nav=null mdd=null engine={gold_trend_sma200,active_paper}；nav/nav_chg_1d/mdd/drawdown_pct 保持 null（口径红线，B8 范围）
- 回归抽查：/portfolios 200 (items:1)、/events?limit=1 200、/health 200 (ready/status 正常)、/portfolios/vC-0 200
- 前端：零改动（Overview.jsx 兜底已工作，/overview 现供给同形数据，无需微调）
- 修改文件：仅 tools/quant-bff/src/app.js（数据文件 mtime 未变，全部只读）；git 中 tools/quant-bff 整体 untracked（既有状态），AGENTS.md 等改动为本次任务前已存在
- 降级语义：portfolios.json/versions 缺失→readJsonWithTimeout ENOENT→null/[]；ledgerDerived 门卫、overview.json nav_series 逻辑零变化
