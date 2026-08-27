# task-0500 过程笔记（前端量化模块去重合并，R-321 实施）

- 日期：2026-08-27
- 对象：/root/.openclaw/workspace/tools/agent-dashboard/server.js（825520B / 14942 行）
- 备份：server.js.bak-task0500 ✅（2026-08-27 08:10 创建）
- 服务：agent-dashboard.service（active running）
- 约束：只动前端渲染层与前端数据缓存；禁止改 /api/quant/* 端点行为；禁改 HP 侧

## T0 计划（按 R-321 §四）

1. 合并① B1 徽标行去重复指标（L9921-9965）
2. 合并② B2 影子对比图移入 B8 折叠面板（L9966-10011 → B8 内）
3. 合并③ 会话级 API 缓存 TTL 30s（registry/active/curves/engines/shadow-nav/version-options/data-health）
4. 死代码清理：死岛 L11377-12836+14029 簇、factor 死簇 ~190 行、onFactorGroupToggle 修指向 factorRegistryRoot
5. 验证：node --check + 服务重启 + 六 Tab curl + 5 API + grep 死簇=0

## T1 引用核查结论（2026-08-27 08:15）

死岛 L11376-11877（models 链）+ L11879-12829（btlc 链）逐函数 grep 外部引用：
- 唯一存活：`qColor`（L11419，被 L13226+ paper Tab 引用）→ 迁出到生命周期层区，不删
- `_baselineVersionList` 外部引用仅 L9464（visibilitychange 失效行）→ 该行改为 quantCacheClear()
- 其余 55 个函数 + 15 个顶层 var 全部零外部引用 → 整块删除
- `openQuantReportDetail` L14028-14079：4 个调用点（L12205/12239/12598/12599）全在死岛内 → 删
- `loadQuantLifecycleLayer` L12836：仅死岛 renderBtlcPage（L12567/12607）调用，quantLifecycleRoot 只在死岛内创建 → 删（_qLifecycle var 与其余 qLifecycle* 保留，活代码在用）
- factor 死簇：buildMergedFactorSummary/factorRowsFromSummary/factorFilterRows/renderFactorTable/factorTableRoot/onFactorSearch/onFactorPage/renderFactorIcChart+_factorIcChartSeq/_factorData/_factorSearch/_factorPage/_factorPageSize → 删；_factorCollapsed 保留（新版注册表 L10923 在用）；copyFactorId 保留（L10947 在用）；onFactorGroupToggle 重写指向 factorRegistryRoot+_factorV2（修复新版分组折叠静默失效 bug）
- 死 DOM：quant-page-models/quant-page-btlc div（L7425-7426）、CSS #quantBtlcBody 选择子、_QUANT_BODY_ID models/btlc 键 → 清
- 注释残留 renderFactorTable 字样 L10786/L10802 → 改写（保证验收 grep=0）

## T2 B1/B2/B8 结构确认（08:16）

- v5EngineEvalFrontHtml（L9921-10011）= ①徽标行+②影子对比图+③F6 图；renderV5Btlc 在 L9836 调用
- r315LcPanelHtml body = v5EngineSwitcherHtml + #quantV5EngineRegion（v5EngineRegionHtml = 引擎因子/模型卡 + renderLifecycleLayer）
- B2 插入点：v5EngineRegionHtml 内、因子/模型卡之后、renderLifecycleLayer 之前（R-321 §五 顺序）
- 折叠态 canvas 0 尺寸问题：仿 v5DrawEngineScatter 模式——r315DrawShadowCmp() 可见性守卫 + r315ToggleLc 展开时重画；固定 canvas id + Chart 实例销毁防 "already in use"
