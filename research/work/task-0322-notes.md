# task-0322 过程笔记（QTV4-P2 验证层开发）

## 2026-08-16 21:40- 调研阶段

### 数据源核验
1. **设计文档已读**（R-214，11.2KB）：§1.5 ID前缀体系、§2 六层结构（②因子③模型④验证层）、§4 数据来源映射。核心：五门禁 g1基准/g2 OOS IC/g3 MDD非平凡化/g4 DSR≥0.95/g5经济逻辑。
2. **v0_seed.json**（VPS model/，830B）：version=v0_seed, strategy=dividend_quality_smallcap_seedB, params{div_min:0.02,roe_min:0.15,roa_min:0.10,sort:mv,n_hold:20,price_cap:10}, factors=[div_yield_ttm,roe_ttm,roa_ttm,circ_mv], context{universe全量池,cost v2,一字板,audit_lock 2024-06-30}, registered_at 2026-08-16 19:30。注意：v0_seed 的 factors 是4个（种子B原始参数），与 q4b 统一参数（div 2.5%/n_hold 30）不同——两套口径并存，registry 为准。
3. **q4b metrics 实测值**（VPS q4b/*.json python 逐字段）：
   - B_full 0.2576 / B_locked 0.2614（legacy, limit off）
   - C_full 0.2647 / C_locked 0.2688（v2, limit on）
   - BUB_full -0.014 (-1.40%) MDD -0.9815 / BUB_locked 0.0327 / -0.9457
   - **A 组 6 个 json 在 VPS 与 HP q4b/ 均不存在**（前序已落盘=旧 results 已归档清空）。A 组数值取 q4b-fullpool-baseline-final.md 报告表格：A_full 25.73%/111.09%/-70.00%/0.9133, A_locked 26.11%/71.79%/-70.00%/0.9074。API 对 A 组返回时带 note「A 组 metrics 文件已归档，数值取自 q4b-final 报告」。
4. **q4b-final 报告三结论**（对照卡文案来源）：
   - B−A=+0.03pp 幸存者偏差可忽略（财务门禁天然挡退市股，DELIST 强平 3 笔正常出清）
   - C−B=+0.71pp（full）/+0.74pp（locked）成本v2+一字板增量，Sharpe 0.932>0.914
   - BUB 无财务过滤→崩：full -1.40%·-98.15%，2024-2026 尾部退市股集中暴露
5. **HP model/archive-20260816/registry/**：v1.1(4632B)/v1.2(2732B)/v1.3(2829B)/v1.4(2898B) 已 scp 到 /tmp/task0322-reg/。结构：{version_id,status(sota/retired/candidate/active),created_at,main_alias,selection:{strategy,params,factors},timing:{enabled,type,params,description},data_snapshot{snapshot_id,as_of,...}}。
   - v1.1: sota, 2026-08-15 00:26, main_alias v1.1_timing_v4_i4_q3z, selection(dividend_quality_smallcap, div 0.025/roe 0.15/roa 0.1/price_cap 10/n_hold 30/min_amt 0), timing=i4_q3z(ma120/vol60/tvol 0.25/...)
   - v1.3 = DSR 0.93<0.95 被 REJECT 的案例（任务书给定，用作 DSR 曲线标注点）
   - /root/backups sudo 不可用（无 tty/密码失败），但 archive-20260816 直读已够，tar 不再需要。

### server.js 结构（590KB，只做定点搜索）
- API 路由区 ~1805-2700：旧 /api/quant/summary|nav|factors|evolution 已弃用（勿挂回 UI）；factor-catalog @1976；baseline @2678+；btlc @3484。
- 前端：quant-tab 段按钮 @6003（qseg-btlc 回测·生命周期），quant-page-btlc 容器 @6009。
- fmtID @7932, quantConceptBadge @7941（P1 已交付，直接复用）。
- CSS .quant-table @5818，#screen-quant 缩放 @5842。

### 实施计划
1. 备份 server.js
2. 新增 API：/api/quant/gates、/api/quant/dsr、/api/quant/q4b-contrast、/api/quant/models、/api/quant/q4b-metrics?（不需要，contrast 直读文件）；factor-catalog 改造读 v3 + 采用版本列
3. registry archive-cache 落盘 workspace-quant/results/model/archive-cache.json
4. 前端：btlc 页新增 验证层分区（五门禁面板+DSR曲线+口径切换+A/B/C对照）+ 模型层分区（版本切换器）+ 因子表升级
5. 验收 5 条命令

## 实施进展
- [x] 备份 server.js.bak-task0322-20260816-214211
- [x] archive-cache.json（v1.1-v1.4，HP archive-20260816 缓存）落盘 model/
- [x] 新增 4 个 API（server.js @2754-2880）：q4b-contrast/gates/dsr/models，node --check 通过
  - q4b-contrast：A 组缺文件→取 q4b-final 报告值（25.73/26.11）+note；B/C/BUB 直读文件
  - gates：v0_seed 基线五门禁 N/A 中性态
  - dsr：静态锚点（n=22/174 DSR 0.9715 pass，v1.3 DSR 0.93 reject）
  - models：v0_seed active + archive v1.1-v1.4
