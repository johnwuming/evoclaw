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
