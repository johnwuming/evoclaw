# task-0392 过程笔记：agent-dashboard readRegistryVersions 正则修复 + 模型 Tab 旧回退文案动态化

## 现场勘察

### registry 目录实际文件形态（ls /root/.openclaw/workspace-quant/model/registry/）
- 纯数字命名：`v1.1.json` `v1.2.json` `v1.3.json` `v1.4.json` `v0_seed.json`
- 字母+下划线命名：`v5h_xsub.json` `a12_s2_reb.json` `v4a_mf0_trr.json` `v1k_q5z.json` `v6a_def.json` 等（共 ~52 个 .json）
- 需排除的非 registry 文件：`*.json.bak`、`*.json.bak-task0384-20260819`、`*.main.json.snapshot`（均不以 .json 结尾）
- 结论：全部 registry .json 文件形态 = 首字符字母 + [a-z0-9._]* + .json

### 根因确认（server.js 744856 字节，>30KB 只 grep/sed 局部读）
- L2318 `readRegistryVersions()`：`.filter(f => /^v[\d.]+\.json$/.test(f))` → 只匹配 v1.1~v1.4，漏掉 v5h_xsub / a12_s2_reb 等
- L2440-2448 `/api/quant/pending`：task-0383 当次绕开，本地宽扫描 `/^v[\w.]+\.json$/i`，注释「共享 readRegistryVersions 不动」——但该本地正则仍要求 v 开头，`a12_s2_reb.json` 两边都漏（本次要修的正是共享函数）
- 调用点：L2335(readRegistryActive) / L2409(registry API) / L2615(archived) / L4227 / L4314 / L4436
- 模型 Tab 旧回退文案：L10743 `renderTimingContributionMatrix` 中 `var caliber = tm.caliber || '全部跑在 v1.4 选股基线，与 bt_v1.4 同快照同区间';` ——硬编码 v1.4 兜底文案

## 修改方案
1. L2321 正则 `/^v[\d.]+\.json$/` → `/^[a-z][a-z0-9._]*\.json$/i`（覆盖字母开头命名；.bak/.snapshot 不以 .json 结尾自然排除；version_id 二次过滤仍在）
2. L2440-2448 pending 端点：改用共享 readRegistryVersions()，删除重复本地扫描与过时注释（行为变化 = a12_* 等字母版本可进 pending 列表，即本任务目的）
3. L10743 caliber 兜底文案动态化：从 registry active 版本号生成，无 registry 时降级通用文案

## 改动实施（备份：server.js.bak-task0392-20260819-094423，744856 字节）

共 5 处编辑，`node --check` 通过：

1. **L2318 readRegistryVersions 正则**：`/^v[\d.]+\.json$/` → `/^[a-z][a-z0-9._]*\.json$/i`，加 task-0392 注释说明覆盖范围与排除逻辑
2. **L2447 /api/quant/pending**：删除 task-0383 本地宽扫描（`/^v[\w.]+\.json$/i`，仍漏 a12_*），回归共享 readRegistryVersions()，注释更新
3. **L10734 renderTimingContributionMatrix**：签名加 `activeVersionId` 参数；caliber 兜底文案 `'全部跑在 v1.4 选股基线，与 bt_v1.4 同快照同区间'` → 动态 `'全部跑在 ' + (activeVersionId || '当前 registry active') + ' 选股基线，与对应回测同快照同区间'`
4. **L10877 调用点**：传入 `activeReg ? activeReg.version_id : null`（renderModelsQuant 内）
5. **L10790 renderModelsQuant activeReg 选取**：多 active 并存（v1.4/v5h_xsub）时按 created_at 取最新，与服务端 readRegistryActive 语义对齐，避免 readdir 哈希序不确定性导致选中旧 v1.4（正则放宽引入的新边界）

## registry 关键事实（改动前实测）
- status 分布：candidate 35 / active 2 / pending 9 / retired 3 / sota 2（共 52 个 .json）
- 两个 active：v1.4(2026-08-15)、v5h_xsub(2026-08-17) → readRegistryActive 按 created_at 应返回 v5h_xsub
- timing-matrix 数据文件自带 caliber 字段（HP 生成，含 v1.4 字样，属数据内容非渲染兜底，不在本次范围）

## 验证记录（服务重启后实测）

### 第一轮（仅正则修复后）
- `node --check` 通过；`systemctl restart agent-dashboard` → `is-active` = active
- /api/quant/registry：n_versions=51（旧正则下仅 4），a12_s2_reb / v5h_xsub / v6a_def 全部可见 ✓
- 但 active_version_id=v1.4：暴露端点用 `versions.find(active)`（数组序）与 readRegistryActive（created_at 最新）不一致

### 追加修复（第 6 处编辑）
- /api/quant/registry 的 active 指针改 `readRegistryActive() || find(active)`，加注释

### 第二轮（全部改动后）
- node --check 通过，重启后 is-active=active
- /api/quant/registry：n_versions=51，active_version_id=**v5h_xsub**（不再是旧 v1.4）✓
- /api/quant/timing-config：active_version=v5h_xsub，source=registry/v5h_xsub ✓
- /api/quant/pending：9 个 pending（v1k_q5z/v2a_deep 等字母命名可见；a12_s2_reb 为 candidate 状态故不在 pending 列表，属正常）✓

## 浏览器实测（google-chrome headless + playwright-core，viewport 390×844）

### 可见「模型」Tab（v5model → loadV5ModelQuant）
- 页面无横向滚动：scrollWidth=390 = clientWidth，hasHScroll=false ✓（task-0326 加固层仍在）
- 该 Tab 数据走 quant/active + version-options（main.json/manifest 源），本就显示 v5h_xsub，与修复后语义一致

### renderModelsQuant 路径（任务书指定路径，页面上下文直调 loadModelsQuant({force:true})）
- 当前生效卡：**「当前生效（作战室 · 控制面）🏛 v5h_xsub ACTIVE 在役」** ✓（修复前因旧正则只剩 v1.x → 恒显 v1.4）
- 待确认 9（pending 端点数据）；模拟盘/择时层卡片正常渲染，textLen 31419
- 贡献矩阵 caliber 显示 HP 数据文件自带文案（tm.caliber 非空，属数据内容，下次 HP 同步自然更新；渲染兜底已改动态）
- 兜底文案函数单测（页面上下文）：
  - renderTimingContributionMatrix({rows:[…]}, 'v5h_xsub') → 含「全部跑在 v5h_xsub 选股基线」✓
  - 传 null → 「全部跑在 当前 registry active 选股基线」✓
  - 输出不含硬编码 bt_v1.4 ✓

### 数据源澄清（审查结论）
- 可见模型 Tab = v5model（loadV5ModelQuant，quant/active 源）；renderModelsQuant 是 M2「选股·择时模型」旧页（quant-page-models，想法提交后 force 重渲染），两者并存，本次按任务书修的 renderModelsQuant 路径
- /api/quant/version-options（v5 排行表）走 versions-manifest.json，不受正则影响
- M3.0 版本切换器为 <select> 下拉，51 个 option 不改变布局宽度；排行表版本列有 max-width+ellipsis 截断

## 服务状态
- 重启两次（追加 registry active 指针修复前后），最终 is-active=active
- journalctl 09:44 起无 error/fatal/exception
- 备份：server.js.bak-task0392-20260819-094423（744856 字节，改动前原样）

## 改动 diff 摘要（共 6 处，全部在 server.js）
1. L2321 readRegistryVersions 正则放宽 `/^v[\d.]+\.json$/` → `/^[a-z][a-z0-9._]*\.json$/i`
2. L2447 /api/quant/pending 回归共享 readRegistryVersions（删 task-0383 本地宽扫描）
3. L10734 renderTimingContributionMatrix 加 activeVersionId 参数，caliber 兜底文案动态化
4. L10877 调用点传入 activeReg.version_id
5. L10790 renderModelsQuant activeReg 多 active 时按 created_at 取最新（对齐 readRegistryActive）
6. L2410 /api/quant/registry active 指针改 readRegistryActive() 优先（多 active 时稳定报最新）

## 验收对照
- node --check：通过（两次）
- systemctl is-active agent-dashboard：active
- /api/quant/registry：n_versions=51（旧 4），a12_s2_reb/v5h_xsub/v6a_def 可见，active_version_id=v5h_xsub（非 v1.4）✓
- /api/quant/timing-config：active_version=v5h_xsub，source=registry/v5h_xsub ✓
- /api/quant/pending：9 个 pending，字母命名可见 ✓
- /api/quant/btlc：active_version_id=v5h_xsub，available=true，归因层缺数据优雅降级 ✓
- 390px 无横向滚动（真无头浏览器实测）✓
