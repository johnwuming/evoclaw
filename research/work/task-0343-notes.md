# task-0343 过程笔记 2026-08-17 13:10:00

## 阶段1 数据源勘察（13:10-13:15）
- QUANT_REPORTS_DIR=/root/.openclaw/workspace-quant/results（347文件，locked/full metrics+nav+yearly+holdings+trades 全在）
- versions-manifest.json 58KB：dict{generated_at, active=v5h_xsub, versions[56]}，每条含 version_id/strategy_prefix/status/strategy/registered_at/windows{full,locked各含annual_return,max_drawdown,sharpe,calmar,cumulative_return,monthly_win_rate,period_start/end,years,num_rebalance}/files_note
- registry VPS侧已同步：/root/.openclaw/workspace-quant/model/registry/*.json（v5h_xsub.json 3KB，13:02 刚同步，新鲜）
  - 结构：version_id/status/created_at/main_alias/selection{strategy,params{sort,ext_factor,ext_weights,e1_guard,mom_cols,xsub_days},factors[]}/timing{enabled,type,params{layer,q_key,trend,combine},description,signal,data_source}/data_snapshot/code_ref/backtest_refs{endtoend,baseline,metrics{含avg_holdings,monthly_turnover_est},metrics_full}/gate/provenance/activated_at
- decision-log.jsonl 36KB 已同步（model/decision-log.jsonl），每行 ts/decision_id/type/version/trigger/metrics/expected_impact/rollback_condition
- a7_v5h_xsub_formal_locked_metrics.json 字段：annual_return .1574/max_drawdown -.298/sharpe .9983/calmar .5283/monthly_win_rate .6109/monthly_turnover_est .3197/avg_holdings 19.53 + 参数字段(div_min .02/roe_min .15/roa_min .1/price_cap 10/n_hold 20/sort ext/cost_model v2/limit_board on)
- **pos_ratio.csv 不存在**（VPS+HP 都没有）；timing 仓位需合成 = q3z×trend_f
- HP 数据源（ssh -p 2222 noname@10.12.192.174, python=/home/noname/miniconda3/envs/quant/bin/python）：
  - results/timing_signals_iter4.csv：248行月度 2006-01~2026-08，f_q_q3z∈[0.6,1.0]
  - results/a2cx_ew_trend_signal.csv：260行月度 2005-01~2026-08，ew_idx+ma200+trend_f∈{0.6,1.0}
  - data/hs300_daily_20060101_20260808.parquet：5003行日线 date/open/high/low/close/volume，2006-01-04起
- 同步链路（scripts/auto_sync_notify.py）：
  - do_rsync: HP results/→shared/results/04-投资研究/（几乎全量，只排除 EXCLUDES）
  - mirror_quant_results: HP results/→workspace-quant/results/（MIRROR_INCLUDES 白名单：seedB_*,q4b*,*_full/locked_metrics.json,*_full/locked_nav.csv,*_full/locked_yearly.csv,versions-manifest.json）
  - Step1.5/push_now: model/(registry/,main.json,decision-log.jsonl)+manifest+ledger→workspace-quant/（已覆盖 registry/decision-log/ledger ✓ 无需补）
  - **需补**：新基准/仓位文件加 --include=dash_*.csv 进 MIRROR_INCLUDES
- 结论：基准数据齐全（hs300 parquet + ew_idx csv），在 HP 一次性生成 dash_pos_ratio.csv + dash_bench_monthly.csv 落盘 results/，改 sync include 即全自动

## 阶段2 server.js 结构勘察（13:15-13:25）
- express 单文件；量化屏 #screen-quant：quantSeg 5按钮(data/factor/models/btlc/paper) + 5个 .quant-page div；switchQuantTab@8220 白名单分派；loadQuant@8294 恢复 localStorage quantTab（默认factor）
- _QUANT_BODY_ID@8247 供 quantShouldSkip 签名跳渲染；quantHScrollGuard 已有横滚兜底
- Chart.js 本地 /chart.umd.min.js（5534），CSP 允许 unsafe-inline；btlcE2EDraw@10035 是现成折线图范式（可仿写）
- 关键后端件：readJsonFile@1805 / readCsvLines@2174 / loadQuantManifest / quantActiveVersion（main.json→manifest.active）/ quantBaselineResolve（manifest→strategy_prefix→metrics文件路径）
- /api/quant/models@2872 已做 registry+manifest 合并（56版本）
- /api/quant/decisions@2423 读 model/decision-log.jsonl（records 含 version 字段）
- e2e-curves@3834：shared/04-投资研究/e2e_curves/ 有 index_hs300.csv（日频 2006→2026-08-07，date,close）→ **沪深300基准现成**
- systemd: agent-dashboard.service；重启 systemctl restart agent-dashboard

## 方案定稿
- **同步清单：零改动**。registry/decision-log（Step1.5 model/）、ledger+manifest、timing_signals_iter4.csv+a2cx_ew_trend_signal.csv（do_rsync→shared/04-投资研究/）、metrics/nav（MIRROR_INCLUDES）全部已覆盖；hs300 在 e2e_curves（一次性采集，图注标截至日）
- **HP 侧：零改动**。仓位曲线=q3z(f_q_q3z)×trend_f 在 VPS 端实时合成；微盘基准=a2cx ew_idx 列
- server.js 新增 5 API：/api/quant/active、/active/pos、/active/curves、/history(分页)、/history/:id
- 模板引擎：quantExplainVersion(reg, metricsJson) 纯函数分三层（选股/择时/交易），未知参数兜底 k=v
- 前端：quantSeg 换 3 按钮（模型/回测/迭代历史→v5model/v5btlc/v5hist），新增3个 quant-page div + 3 loader/renderer；旧页面 div 与全部旧 API 保留不删

## 阶段3 实施与验收（13:18-13:35）
### 改动（仅 server.js，640KB→684KB，备份 server.js.bak-dashv5-08171318）
后端新增（/api/quant/freshness 前插入）：
- 模板引擎纯函数：quantTplSelection/quantTplTrading/quantTplTiming + quantExplainVersion（参数缺失块自动跳过；未知机制兜底"机制: xxx（参数: k=v）"；零 LLM）
- ① GET /api/quant/active：active版本+locked/full指标+三层解释（metrics文件→registry.backtest_refs→manifest.windows 三级回退）
- ② GET /api/quant/active/pos：pos=q3z(timing_signals_iter4.csv f_q_q3z)×trend_f(a2cx_ew_trend_signal.csv)，248月度点，VPS端实时合成
- ③ GET /api/quant/active/curves：策略nav(locked+full,周频降采样) + hs300(e2e_curves/index_hs300.csv归一) + ewmicro(a2cx ew_idx月频归一)
- ④ GET /api/quant/history?page&page_size：manifest 56版+registry特征+decision-log最新摘要，active置顶
- ⑤ GET /api/quant/history/:versionId：registry+双窗metrics+模板解释+该版全部决策记录
前端：
- quantSeg 5按钮→3按钮（模型v5model/回测v5btlc/迭代历史v5hist）；旧5个 quant-page div 与全部旧API/旧loader保留（仅无UI入口）
- 三页loader/renderer：指标卡6张(年化/回撤/夏普/卡玛/月胜率/月换手)+locked/full切换；解释三层卡；仓位Chart面积图(0~105%)；nav三线对比图(窗口重归一+全期/3y/1y)；历史分页列表(10/页)+点开报告式详情(locked+full指标+机制解释+决策时间线)
- switchQuantTab/loadQuant/_QUANT_BODY_ID 适配新tab，旧 localStorage 值映射到新页；30s 定时刷新走签名守卫不变
- CSS：.v5-metric-grid/.v5-chip/.v5-hist-row 等（3列自适应，无横向溢出）
修复1个bug：v5SeriesStats 对前向填充首部 null 除法产生 Infinity%（改为跳过首尾null）；策略曲线指标窗口与实际绘制窗口对齐

### 验收结果（全部通过）
1. node --check ✓（两次：初版+修bug后）
2. 5个新API全 200 且 JSON 可解析 ✓；active 端点含 v5h_xsub 15.74%/-29.8%/0.9983/0.5283/61.1%/32% 与分层解释 ✓
3. 无头浏览器（google-chrome headless + CDP）：
   - 390x844：三页+历史详情+历史列表 scrollW=375 ≤390 ✓ 无横向滚动
   - 1440x900：三页正常 1425 ✓
   - 截图8张：dashv5-{v5model,v5btlc,v5hist,v5hist-list}-{390x844,1440x900}.png
   - 内容级验证（innerText提取）：模型页=版本徽章+6指标卡+三层解释+仓位图(最新2026-08-31仓位56%=q3z0.94×0.60)；回测页=指标+三线图(策略15.3%/沪深300 8.1%/微盘等权17.0%)；历史页=56版分页列表+详情报告 ✓
4. 旧API回归：models/baseline/summary/decisions/freshness/e2e-curves 全200 ✓；nginx 8052 入口 200 ✓
5. 空态：history/nonexist_v99 → ok:true available:false note 提示，无500 ✓

### 同步链路结论（零改动）
registry/decision-log（Step1.5 model/镜像）、manifest+ledger、timing/a2cx csv（do_rsync→shared/04-投资研究/）、metrics/nav（MIRROR_INCLUDES）均已自动同步，本次确认无需改 auto_sync_notify.py；HP 侧零改动。新版本 activate → main.json/registry/metrics/nav 30分钟内同步 → 所有新API动态解析 active → 看板自动切换，全自动闭环。
基准数据说明：沪深300=e2e_curves 一次性采集(截至2026-08-07，图注标注)；微盘等权=a2cx ew_idx(月频,随同步更新)
