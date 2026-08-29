# task-0563 notes 2026-08-29 15:14:59
started

## 1. R-336 §4.4 组合级风险闸门阈值表（口径基准，原文摘录）
- 回撤分级闸门：<5% 正常 / 5–10% 提级审查 / 10–15% 降仓×0.5 / >15% 熔断停新仓（组合级）
- 波动率目标化：target_vol 8%，再平衡带 ±2pp（参数位，Phase B 校准）（组合级）
- sleeve 级 ddc：≤−20% ×0.5，回补 −5%（ddc_th20_rd50_rc5 原样保留）；参数存 sleeve 版本对象，不进 portfolio_version.risk_control（§1.2⑤）
- 运行时持仓相关性：滚动 20 日两腿相关性 >0.85 且上升 → 防御性降仓；>0.90 → 提级审查（定义出处 §7.5.4）
- 裁决顺序 v1.1：熔断硬上限 > 组合级裁决 > 单腿级裁决；任一熔断（单腿 ddc>20% 或组合回撤>15%）立即停不可覆盖；§7.5.3
- 文件：R-336-破而后立量化系统目标架构与迁移方案.md 行238-247

## 2. R-359 审计结论（R1/R2/R3 三连缺）
- R1 回撤分级闸门四带仪表：无渲染；risk/gates 无 portfolio_dd_gate；HP 无当前回撤带位产物。补齐：HP 产回撤监控 JSON（NAV 序列可算）→ BFF risk/gates 补字段 → 前端仪表卡；口径注明宪章 vs 目标带双轨
- R2 波动率带（8%±2pp）：risk_control.vol_target=null，无 realized vol 监控产物；在役组合 realized vol 20日
- R3 两腿 20 日相关性三档旗（0.75/0.85/0.90）：无相关性监控产物；HP 日频收益算 20 日 rolling corr → 投影 → BFF → 前端三档旗
- BFF 12 端点 200 + 2 端点 404（risk/drift 404，drift 数据揉进 risk/gates）
- 代码定位：Overview.jsx（60s 轮询）、Risk.jsx（断路器+四维漂移+recon）、api.js（EVENT_TYPES 17）
- 页面实测 390×844 scrollWidth 均 390（无横向滚动纪律基线）
- 注意：R-359 说三档旗 0.75/0.85/0.90，R-336 §4.4 只有 0.85/0.90 两档 → 需查 R-342/R-344 找 0.75 档出处

## 3. R-355/R-358 传输通道要点
- R-355：HP→VPS 无既有 rsync 文件通道；最接近模式是 VPS→HP 拉取式 sshpass+scp -O；HP 每分钟 collect-metrics.sh HTTP 推送（非文件通道）；导出脚本范式：VPS 仓 tools/quant-bff/live/export/hp_export_metrics.py + HP 副本 portfolio_v1/governance/export/，幂等（generated_at 取源 mtime）+ 原子写 tmp+fsync+rename + --check；月频挂点方案 B 待批（未落 crontab）
- R-358：既有通道 auto_sync_notify.py（/root/.openclaw/workspace-quant/scripts/），cron 每30分钟增量 cron-auto-sync + 每日03:00全量；MIRROR_INCLUDES 有 --include=baseline-paper-*，覆盖 baseline-paper-nav.csv/trades/portfolio.json/summary.json 四件套；镜像落 /root/.openclaw/workspace-quant/results/
- R-358 BFF 新端点范式：src/nav-series.js + config.js paperNavPath（env PAPER_NAV_FILE）+ app.js 注册路由（.catch(next)，不套 ledgerDerived）；契约 nav_series@v1；降级语义 200+null 不 503；npm test 38/38
- R-358 前端范式：api.js fetchNavSeries + Overview.jsx SVG 轻量曲线（viewBox 自适应）+ 口径标注；390×844 验证 bodyScrollW=390
- BFF 端口 127.0.0.1:8180；quant-bff.service；线上 https://www.zhengqiangnan.cn/quantv6/

## 4. R-342 §3.4 risk/gates 契约草案（既有出处！）
- GET /api/v1/risk/gates → {portfolio_dd_gate{drawdown_pct,band,action}, vol{target,realized,in_band}, sleeves_ddc[{id,state,drawdown,th}], correlation{pair,corr_20d,flag:0.75/0.85/0.90}, circuit_breaker{state,reason}}
- 契约约定：JSON、UTC ISO8601、cursor 分页、无写操作；三档相关性 flag 对应 §7.5.4 的 0.75/0.85/0.90 分级（R-342 行208/213）
- R-342 关键决策：三落点分工——计算与写入全在 HP，VPS 只持只读镜像，Dashboard 纯只读消费者；390px 硬约束全局 overflow-x hidden（决策9）
- R-342 §3.1 portfolio_version schema 有 drawdown_gates: {lt5:normal, 5_10:escalated_review, 10_15:cut_half, gt15:circuit_break}
- 待办：读 R-336 §7.5.4 拿 0.75 档定义；读 R-342 §4.3 轮询分频、§4.4 390px 规范

## 5. R-336 §7.5.4 相关性三档定义（唯一出处）
- 0.75 = 入池筛查阈值（平时测，衔接 G-S5 与 R-335 两腿相关性上限）；改相关性筛查阈值(0.75)须升版本走完整流水线（§7.6）
- 运行时监控：滚动 20 日持仓相关性，任意两腿 >0.85 且呈上升趋势 → 自动防御性降仓（先发防御，不等熔断）
- 0.90 = 提级审查；与 §7.1 RET-4 衔接
- 裁决顺序唯一出处 §7.5.3：熔断硬上限（>15%组合回撤或单腿ddc>20%立即停）> 组合级裁决 > 单腿级裁决，同向取更保守

## 6. R-342 §4.3/§4.4 展示与实时性
- 风控闸门区块：轮询 120s；回撤四带仪表（<5/5-10/10-15/>15）、target_vol vs 实测±2pp带、两腿20日相关性+三档旗、D1-D4漂移、断路器；交互=超带项自动置顶+红沿、点开看事件溯源
- 轮询总原则：总览 60s / 其余 300s / 风控 120s，HTTP 轮询不用 SSE

## 7. R-344 PRD 风控页验收（§4.2-1 与区块⑤）
- 六组闸门=回撤带/波动带/相关性/漂移四维/断路器/退役监视占位；P0 验收：全部呈现「当前值+带宽+状态」三元组无一空白
- 回撤：四带仪表；波动率带：目标8%实测±2pp带内外；相关性：20日对照0.75筛查/0.85防御降仓/0.90提级审查；漂移D1-D4各带内/超带+连续超带期数；断路器：未触发/触发含原因时间；退役RET-1..4=P1余量
- 交互P0：超带置顶+红沿、点闸门→事件页定位risk事件；风控轮询120s（与事件同频）
- 依据：R-342 §4.3 + R-336 §4.4/§6.1/§7.2/§7.5.4

## 8. HP 盘点（只读）开始

## 9. HP crontab 在役项盘点（只读，未动）
- 30 16 * * 1-5 paper_engine.py --action daily（今日16:30实跑，勿碰）
- 45 16 * * 1-5 risk_patrol.py → 产出 results/risk-status.json + risk-events.jsonl + notifications-queue.jsonl
- 10 8 * * 1-5 portfolio_v1/shadow_recon.py → drift-*/recon-* 影子产物
- 每分钟 collect-metrics.sh HTTP 推送（系统指标，非文件通道）；10 * * * * notify_hub.py
- 0 18 * * 1-5 cron_qfq_daily.py（A股日线更新 data/stocks_hfq）
- 0 9 * * 6 evolution_pipeline cycle（周六，今日）
- risk_patrol.py 覆盖=退出纪律（drawdown_vs_hwm 主序列 i3_abs_s1 回测 track record + rolling 超额 + sharpe 对比），≠ R-336 §4.4 组合级三闸门，无重合产物

## 10. 数据可得性核验（三组闸门逐项）
- 回撤四带：baseline-paper-nav.csv 10 obs（2026-08-14~08-28，末值 1.00993 新高 drawdown=0）→ BFF 镜像现算立即可用；HP paper daily 每交易日 16:30 追加
- 波动率带：同 NAV 序列 20 日滚动年化 vol；obs=10<20 → insufficient_obs；约 2 周后窗口满（到 9 月中）
- 两腿相关性：vC-0 两腿=equity_sleeve(a13_rsraw_e1f10dz) + hedge_sleeve_gold，配置权重 58/42（task-0542）
  - equity 腿日频：a13_rsraw_e1f10dz_full_nav.csv（2006-01-04~2026-08-14，回测止于 8/14，镜像 VPS 已有 8/19 版）
  - gold 腿：results/engines/gold/shadow_nav.csv 仅月频（2013-08~2026-08，列 month/gold_ret/mmf_ret/gross/net/nav）；HP data/ 无黄金日频数据（只有 stocks_hfq）
  - 结论：日频两腿相关性当前不可算 → insufficient_data；paper holdings 现为 8 只股票纯 equity 敞口
- sleeve ddc 数据可从两腿 NAV 各自现算（后续项，非 P0 三缺）

## 11. 传输通道核验（零新增成立）
- auto_sync_notify.py（VPS cron 每30min cron-auto-sync + 每日03:00全量）MIRROR_INCLUDES 已覆盖：baseline-paper-*、*_full_nav.csv、*_locked_nav.csv、risk-status.json、crowding-indicators.json、engines/、engines/**（gold 四件套）
- VPS 镜像实存：/root/.openclaw/workspace-quant/results/{baseline-paper-nav.csv(8/29 10:43), risk-status.json(8/29 00:45), a13_rsraw_e1f10dz_full_nav.csv(8/19), engines/gold/shadow_nav.csv(8/24)}
- drift/recon 到 BFF live/ = task-0545 手动只读拷贝（非自动通道）；risk-status.json 已自动镜像但 BFF 未消费

## 12. BFF 现状
- quant-bff.service: LEDGER_DIR=/root/.openclaw/workspace/tools/quant-bff/live, PORT 8180, 127.0.0.1
- risk/gates = src/risk-gates.js assembleRiskGates()，app.js:391 ledgerDerived 包装（账本503联动）；现返回 keys: run_date/circuit_breaker/drift/recon/pending_risks——缺 portfolio_dd_gate/vol/sleeves_ddc/correlation
- config.js: reconDir=live/recon, driftDir=live/drift, dataDir=live/data, paperNavPath=/root/.openclaw/workspace-quant/results/baseline-paper-nav.csv（task-0560 加）
- 先例：nav-series.js 独立镜像文件源现算 summary（drawdown_pct/mdd/nav_chg_1d），.catch(next) 不套 ledgerDerived；降级 200+null
- 前端 Risk.jsx 已有：断路器卡/D1-D4 漂移卡超带置顶连超计数/对账三视角/pending 关联，120s 轮询（task-0545）

## 13. 方案要点定稿（写报告依据）
- 推荐 BFF 镜像现算（R-358 先例）为 Phase 1：零 HP 改动、零传输新增、零 crontab 变更；HP 权威产物列为后续增强（方案 A，需批准 cron/挂点）
- 相关性闸门 Phase 1 = insufficient_data + 三档阈值结构展示；Phase 2 = HP 侧两腿日频收益产物任务（gold 日频数据源为决策点：黄金ETF日线采集 vs paper 持仓重建 vs 等 mmf/gold 月频升级）
- 回撤双轨口径：目标四带（5/10/15，R-336 §4.4）为主仪表 + 宪章带（25/35，vC-0 risk_control.in_service_charter）标注
- vol realized 窗口 20 日（R-359 建议）；相关性上升趋势判定建议 corr(t)>corr(t-5) 初版口径 Phase B 标定
- 契约 risk_gates@v2 纯新增；缺失值三态 ok/insufficient_obs/unavailable；200 不 503；数字小数单位
- 拆分：T1 BFF 扩展（回撤+vol）、T2 前端三卡、T3 相关性 HP 日频产物（依赖 D-1 决策）、T4 HP 权威产物增强（可选）
- 回滚：git revert BFF+前端 rebuild；数据面零改动

## 14. R-362 重派复核证据（2026-08-29 17:08-17:12，第二次 run）

背景：task-0563 于 15:42 完成（R-361）并审核通过；17:06 主 agent 重派，指令产出 R-362。本 run 对 R-361 全部关键事实独立复核：

1. R-336 §4.4 原文（行 238-247）：四带 5/10/15、target_vol 8%±2pp（Phase B 校准）、sleeve ddc ≤−20%×0.5 回补 −5%（ddc_th20_rd50_rc5）、相关性 >0.85 且上升防御降仓 / >0.90 提级审查（出处 §7.5.4）、裁决顺序 v1.1 三段式（熔断硬上限>组合级>单腿级）。§7.5.4 原文（行 360-364）：0.75 入池筛查 / 0.85+上升 防御降仓 / 0.90 提级审查。✅ 与 R-361 引用逐字一致。
2. BFF risk-gates.js assembleRiskGates（行 164-186）：仅返回 run_date/circuit_breaker/drift/recon/pending_risks，无 dd/vol/corr → BFF 侧三连缺属实。✅
3. MIRROR_INCLUDES（auto_sync_notify.py 行 78-97）：baseline-paper-*、*_full_nav.csv、risk-status.json、engines/** 全覆盖。✅
4. VPS crontab：*/30 cron-auto-sync（在役，task-0279）+ 0 3 full sync → 零 crontab 变更成立。✅
5. 镜像实存：workspace-quant/results/ 下 baseline-paper-nav.csv（末行 2026-08-28,1.00993）、a13_rsraw_e1f10dz_full_nav.csv、engines/gold/shadow_nav.csv 三件齐。✅
6. HP 只读抽验：baseline-paper-nav.csv 12 行（≈11 obs，较 R-361 时 +1 日）、shadow_nav.csv 158 行月频 2013-08 起（列 month,w_applied,gold_ret,mmf_ret,gross,net,nav）、a13 NAV 5009 行（回测日频止 data_cut）；data/ 首屏无黄金日频源。✅
7. Risk.jsx（8.6KB）：断路器卡+DimCard（漂移）+PerspectiveCard（对账三视角）+120s 轮询，无回撤/波动率/相关性卡 → 前端侧三连缺属实。✅

结论：R-361 方案结论全部成立，R-362 作为终版承接（补复核证据，方案本体无变更）。
