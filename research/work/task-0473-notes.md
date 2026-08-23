# task-0473 回测·生命周期升级为引擎级生命周期视图（过程笔记）

## 任务
在现有 回测·生命周期 Tab（v5btlc）上升级，不新建页面：
1. 引擎切换器（遍历 engines.json，默认 A）
2. 每引擎因子/模型区块（registry selection.params.ext_specs / selection / timing；A2 显示 overlay{w,parent}）
3. 层级标注（层1 vs 层2 哑层）
4. 兼容降级、bodyScrollW=390 无横滚、console 零 error
5. 零硬编码引擎 ID
6. 验证：node --check + 重启 + playwright 抽查

## 2026-08-23 探索记录
- engines.json 位于 /root/.openclaw/workspace-quant/results/engines.json（5999B），已落盘 /tmp/engines.json。
- 引擎列表：
  - A: active, registry entry=a13_rsraw_e1f10dz, hp_dir=~/quant-evolve/model/registry, signal_desc=微盘市值倾斜选股 + q3z×EW-MA200 择时内化, timing_internal=true, layer3.tabs=[v5model,v5btlc,v5hist,paper], api_prefix=/api/quant, shadow.mode=none
  - A2: shadow, type=sub_engine_overlay, parent=A, overlay{w:0.5, w_source:...}, registry entry=a14_crowdf2, hp_dir=~/quant-evolve/model/registry, layer3.tabs=[], api_prefix=/api/quant/engines/A2, shadow.mode=cross_engine
- R-290 §4.1 引擎级生命周期视图：数据全部来自 engines.json 遍历 + per-engine 端点；复用 task-0468 遍历框架（renderCrossEngineShadowCard）。
- R-290 §4.3：模型/回测/迭代历史页加引擎切换器（默认 A）。
- R-290 §五.1：层级标注「层1 · A 的子引擎叠加臂 parent=A · overlay w=0.5」vs「层2 中央风控：哑层待激活」。
- R-290 §五.5：server.js 无 git 基线 → 本任务先建基线提交。

## server.js 关键行号（grep 结果）
- renderV5Btlc L9564（回测 Tab 主渲染）
- qLifecycle 数据加载 L12182-12194；qLifecycleSetCaliber L12199；qLifecycleToggleD L12209
- qLifecyclePipeline L12235；qLifecycleShadow L12296；qLifecycleTimeline L12329；qLifecycleLedgerTable L12358；qLifecycleScatterSection L12403
- renderLifecycleLayer L12482（五区块组装）
- /api/quant/lifecycle 端点 L2573
- /api/quant/engines 端点 L3680
- /api/quant/engines/:id/shadow-nav L3742；扁平别名 L3786
- renderCrossEngineShadowCard L12913（task-0468 遍历框架先例）
- /api/quant/registry L2430；/api/quant/timing-config L2416；/api/quant/timing L2213

## 基线
- git 基线已建：baseline: pre-0473（server.js 提交前快照，便于回滚）
=== baseline confirmed ===
efe8142 baseline: pre-0473 已建（--allow-empty 因为 server.js 与 HEAD 无 diff）

## 2026-08-23 继续（重试后）
- renderV5Btlc 结构：版本选择器 + 标题 + 指标卡 + nav 曲线 + 全版本排行表；body.innerHTML = html; 然后 v5DrawNav / quantHScrollGuard()。
- /api/quant/lifecycle 返回 {ok, decisions, ledger, n_trials, decision_source, shadow_watch, registry{active,versions,baseline_version,archived_count}, note}。
- /api/quant/engines 返回 {ok, available, engines:[{engine_id,name,status,parent,type,layer1,layer3,shadow{...},audit}]}（不含 overlay！/engines 映射里没 overlay）。注意：engines 端点未透传 overlay，需补充或从 layer1 取。
- /api/quant/engines/:id/shadow-nav 返回 points + parent + type + shadow。
- /api/quant/registry 返回 {ok, available, versions, active_version_id, pending_versions, n_versions}。
- qLifecycle 状态：_qLifecycle = { caliber, data, expandD }；loadQuantLifecycleLayer() 调 api('quant/lifecycle') → renderLifecycleLayer(data) + drawLifecycleScatter(data)。
- renderLifecycleLayer = 标题 + desc + qLifecyclePipeline + qLifecycleShadow + qLifecycleTimeline + qLifecycleLedgerTable + qLifecycleScatterSection。
- renderCrossEngineShadowCard（模拟实盘页）遍历 engines 渲染徽标 + 影子卡，是 task-0468 遍历先例。

## 2026-08-23 继续（重试后第二轮）
- loadV5BtlcQuant：Promise.all 拉 active/curves/version-options → renderV5Btlc。renderV5Btlc 输出 版本选择器/标题/指标卡/nav曲线/排行表。
- quantLifecycleRoot 在哪里被渲染？需要 grep 确认 v5btlc Tab 里生命周期层如何嵌入（可能独立 region，或需在 renderV5Btlc 内追加）。

## 2026-08-23 继续（重试后第三轮）
【关键发现】当前 UI 的「回测」Tab = quant-page-v5btlc → loadV5BtlcQuant → renderV5Btlc（版本选择器/指标卡/nav/排行表），**不含生命周期层**。quantLifecycleRoot 只在旧版 renderBtlcPage（quant-page-btlc，L7187/L11894）里，而 quant-page-btlc 不在 _V5_TABS 中（_V5_TABS=[data,factor,v5model,v5btlc,paper,v5hist]），实际 UI 不展示生命周期层。
- 结论：任务要求「在现有回测 Tab 上升级为引擎级生命周期视图」= 把生命周期层（5 区块）+ 引擎切换器 + 因子/模型区块整合进 renderV5Btlc（当前回测 Tab）。
- playwright 验证：v5btlc 页 bodyScrollW=390（无横滚）、console 零 error；页面文本无「生命周期/决策时间线/实验台账/影子观察/迭代轨迹/培育管线」→ 确认当前不含生命周期层。

## registry 数据结构（a13_rsraw_e1f10dz.json / a14_crowdf2.json）
- 顶层：version_id/status/created_at/main_alias/selection/timing/data_snapshot/code_ref/backtest_refs/gate/provenance/activated_at（A2 另有 overlay）
- selection: {strategy, params, factors}
- selection.params: {sort, ext_mode, ext_specs, ext_filter_all, raw_universe, e1_guard, e1_lambda, e1_deadzone, xsub_days, n_hold, cost_model, limit_board, min_amt, div_min, roe_min, roa_min, price_cap, capital_base, (A2 另有 crowding_mod)}
- selection.params.ext_specs: [["log_mv",1.0,-1],["amt20",1.0,-1],["pb_inv",0.7,1.0],["roe",0.3,1.0]] → [因子, 权重, 方向]
- selection.params.sort="ext"; n_hold=20
- timing: {enabled:true, type:"q3z_x_ew_trend_overlay", params:{layer,q_key,trend,combine}, description, ...}
- /api/quant/registry 返回 versions = readRegistryVersions() 完整 JSON 对象（含 selection/timing/overlay）
- engines.json layer1.registry.entry 与 registry 文件名一致（a13_rsraw_e1f10dz / a14_crowdf2）

## 下一步
1. 读 decision-log.jsonl / experiment-ledger.jsonl 结构（per-engine 过滤依据）
2. 读 v5VersionSelHtml / quantConceptBadge / esc / fmtID 等前端辅助（复用）
3. 设计并实现 renderV5Btlc 升级：引擎切换器 + 因子/模型区块 + 层级标注 + 5 生命周期区块（按引擎过滤）
4. 验证

## 2026-08-23 继续（重试后第四轮）
- 当前状态：server.js 无改动（git diff 空），基线 efe8142 已建。
- 已确认：decisions 有 version 字段（v0_seed/v1a_score/a13_rsraw_e1f10dz/a14_crowdf2 等），per-engine 过滤依据可用 version 字段；ledger 无 strategy 匹配 a14；shadow_watch 只有 a12_s2_reb（A 引擎管道）。
- a14_crowdf2.json 顶层有 overlay 字段（A2 的 registry 条目含 overlay），/api/quant/engines 端点不透传 overlay → 需在引擎端点补充 overlay，或前端直接从 /api/quant/registry 的对应版本对象读 overlay。
- 实施计划：
  1. server.js 后端 /api/quant/engines 补 overlay 透传（enghgine.overlay）。
  2. 前端 renderV5Btlc 顶部加引擎切换器（从 /api/quant/engines 遍历，默认 A）。
  3. 每引擎因子/模型区块（registry 条目 selection.params.ext_specs + selection + timing + A2 overlay + 层级标注）。
  4. 5 生命周期区块按引擎过滤（管线/影子/决策/台账/散点）——决策按 version 匹配引擎 registry entry 前缀。
  5. 兼容降级 + bodyScrollW=390 + console 零 error。

## 2026-08-24 00:2x 实现落地（本轮）
- 应用 12 处 edit：node --check 通过（SYNTAX_OK），git diff +220/-8。
- 改动清单：
  1. /api/quant/engines 透传 registry_ref + overlay（A2 overlay{w,parent} 前端可用）
  2. loadV5BtlcQuant Promise.all 增拉 engines/lifecycle/registry；默认引擎=首个 active（零硬编码）
  3. renderV5Btlc 顶部插入引擎切换器 + #quantV5EngineRegion + v5DrawEngineScatter
  4. 新增 v5 系列函数：v5EngineEntryPrefix/v5AllPrefixes/v5FilterLcForEngine/v5LayerAnnotation/v5EngineFactorModelBlock/v5EngineSwitcherHtml/v5EngineRegionHtml/v5SetEngine/v5DrawEngineScatter
  5. _v5State 增 engine/lcFiltered；新增 _v5Engines/_v5Lc/_v5Reg
  6. _qLifecycle 增 engineLabel/scatterChart（防重复创建 Chart）
  7. qLifecycleSetCaliber/qLifecycleToggleD 优先重渲染 v5 区
  8. qLifecyclePipeline/renderLifecycleLayer 标题引擎参数化
  9. drawLifecycleScatter 销毁旧 Chart 实例

## 2026-08-24 00:3x 验证通过
- node --check server.js：SYNTAX_OK（+220/-8，12 处 edit）
- systemctl restart agent-dashboard：active
- curl /api/quant/engines：A active（registry_ref=a13_rsraw_e1f10dz）+ A2 shadow（parent=A, registry_ref=a14_crowdf2, overlay.w=0.5 透传成功）
- curl /api/quant/lifecycle + /api/quant/registry：正常（A 在役链路零回归）
- playwright（python 1.58，390x844，正确导航 量化→回测 tab）：
  - SWITCHER_TITLE: 🧭 引擎级生命周期视图 ✓
  - A 视图：层1/层2 中央风控/因子模型/在役 全 True
  - 切 A2：overlay / parent=A / w=0.5 / 叠加臂 / 层1 / 层2风控 / a14 / 因子模型 / log_mv·低值优先 全 True
  - bodyScrollW=390（无横滚）✓，console 零 error ✓
- 说明：此前两轮 playwright 失败根因=未先切「量化」页+点击了错误的「回测」文本（dashboard 页面默认不在 quant 视图）；改为 showPage('quant') → switchQuantTab('v5btlc') 后全绿。
