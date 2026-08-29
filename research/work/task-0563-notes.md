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
