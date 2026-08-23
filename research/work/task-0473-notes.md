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
