# task-0500 实施报告：前端量化模块去重合并（R-321 合并①②③+死代码清理）

日期：2026-08-27 ｜ 状态：主体完成，等主 agent 终验

## 改动清单
1. 合并① B1 徽标行瘦身：v5EngineEvalFrontHtml() 去掉与 M3/B5 同源的 ann/mdd/calmar 指标数字，只留状态徽章+corr+来源标注（备份对照：旧版含 8 处指标渲染）
2. 合并② B2 影子对比图移位：新增 v5ShadowCompareHtml()，从回测 Tab 首屏移入 B8 引擎级生命周期折叠面板（因子/模型卡之后、生命周期层之前）；折叠态 canvas 零尺寸问题用 r315DrawShadowCmp() 可见性守卫+展开重画解决；Chart 实例先销毁防 "already in use"
3. 合并③ 会话级量化 API 缓存：_qapiCache，TTL 30s，覆盖 registry / active/curves / engines / engines/:id/shadow-nav / version-options / data-health；同会话 Tab 切换复用在途请求与响应；force 三通道：单调用 qforce / quantCacheClear() 全清 / 页面重新可见自动清
4. 死代码清理：loadModelsQuant / loadBtlcQuant 死岛引用全部移除（旧 4 处 → 0）；factor 死簇删除

## 体积变化
- server.js：825,520B (14,942行) → 718,178B (13,309行)，-107,342B (-1,633行)

## 验证结果
- node --check server.js PASS
- 内嵌前端 JS 单独提取 node --check PASS（内嵌字符串不校验的盲区已补查，1/1 OK）
- agent-dashboard.service active，页面 HTTP 200
- 关键 API 全部 200：f6-curves / engines / version-options / data-health / active/curves
- B2 已位于生命周期折叠面板内（grep 证实插入点），B1 无重复指标数字

## 回滚方式
cp server.js.bak-task0500 server.js && systemctl restart agent-dashboard
