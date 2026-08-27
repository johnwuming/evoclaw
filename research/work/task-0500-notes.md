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

