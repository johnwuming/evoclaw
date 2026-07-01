# dispatch.js 派发机制改造方案评估

> **文档类型**：架构方案评估 | **日期**：2026-07-01 | **状态**：决策待定
> **背景**：任务中心 dispatch.js 当前通过 flag 文件 + 心跳拾取方式派发任务，存在派发延迟和主 agent 耦合问题

---

## 一、现有架构（方案1：flag + 心跳拾取）

### 流程
```
dispatch.js（crontab 每2分钟）
  → 检测 pending 任务
  → 写 flag 文件（.dispatch-pending-{team}.json）
  → 等主 agent 心跳拾取（最慢30min）
  → 主 agent 读 flag → 删除 flag → sessions_spawn
  → 子 agent 执行
  → completion event 回到主 agent
  → 主 agent 检查交付物 → 用自己的话汇报用户
```

### dispatch.js 四个函数
1. `processCompletions()` — 读 .task-completions.jsonl 标记 done
2. `detectStaleTasks()` — 检测超时（grace period 内无活跃子 agent）标记 failed
3. `retryFailed()` — 自动重试 failed 任务（最多 max_retries 次）
4. `dispatchPending()` — 写 flag 文件通知主 agent ← **唯一需要改的**

### 优点
- 主 agent 质量把关：先读交付物确认质量，再用自己的话汇报
- prompt 质量高：主 agent 构造完整 prompt（含 R-121 约束 + 输出约束）
- 零改动成本：已稳定运行

### 缺点
- **派发延迟**：最慢等 30min 心跳才能 spawn（task-0041 实际卡在这里）
- **主 agent 耦合**：每次心跳要检查 flag、spawn、yield，消耗主 agent token
- **心跳单点依赖**：心跳不执行 → 任务永远派不出去（6/29 教训）

---

## 二、方案2：dispatch.js 直接 cron add

### 流程
```
dispatch.js（crontab 每2分钟）
  → 检测 pending 任务
  → 调 openclaw cron add --at now（直接创建 isolated cron job）
  → 子 agent 立即启动
  → 完成后 announce 直接发用户微信
  → dispatch.js 下轮读 .task-completions.jsonl 更新 DB
```

### 核心改动（dispatchPending 函数重写，~30行）
```javascript
// 现在：写 flag 文件
fs.writeFileSync(`${FLAGS_DIR}/.dispatch-pending-${teamId}.json`, JSON.stringify({
  taskId, title, agent, team, ts
}));

// 改后：直接调 CLI
execSync(`openclaw cron add \
  --name "task-${taskId}" \
  --at now \
  --agent ${agent} \
  --session isolated \
  --delete-after-run \
  --announce \
  --channel openclaw-weixin \
  --to "${wechatId}" \
  --account "${accountId}" \
  --timeout-seconds ${timeout} \
  --message '${prompt}'`);
```

### 已验证的 CLI 参数（2026-07-01 实测）
| 参数 | 验证结果 | 说明 |
|------|----------|------|
| `--agent research-lead` | ✅ | isolated session + 指定 agent |
| `--agent claude`（ACP） | ✅ | ACP 也能通过 cron isolated 触发 |
| `--announce` + `--channel/to/account` | ✅ | 完成后直接发微信 |
| `--at now` / `--at +1h` | ✅ | 一次性任务，立即或定时执行 |
| `--delete-after-run` | ✅ | 执行后自动清理 |
| `--timeout-seconds` | ✅ | 可控超时 |
| `--no-deliver` | ✅ | 不通知用户（用于混合方案） |
| `--light-context` | ✅ | 轻量上下文（减少 token） |

### CLI vs HTTP API 对比（2026-07-01 实测）

两种调用 gateway 的路径：

```
路径 A（CLI）: dispatch.js → fork openclaw 进程 → WebSocket → gateway → 创建 cron job
路径 B（HTTP）: dispatch.js → POST /tools/invoke → gateway → 直接 sessions_spawn
```

| 维度 | CLI cron add | HTTP API /tools/invoke |
|------|-------------|----------------------|
| **本质** | 创建 cron job → 调度器接管执行 | 直接调用 sessions_spawn 工具 |
| **进程开销** | 每次 fork node 进程（~200ms） | HTTP 请求（~10ms） |
| **参数传递** | 命令行参数（需转义特殊字符） | JSON body（无转义问题） |
| **错误处理** | execSync exit code + stderr | HTTP status + JSON error |
| **执行时机** | cron 调度器中转（--at now 近乎即时） | 同步即时 |
| **中转环节** | 多一层 cron 调度 | 直达 gateway |
| **认证** | CLI 自动读取 token | 手动传 Bearer token |
| **gateway 挂了** | 同样失败 | 同样失败 |
| **实测连通性** | ✅ 已验证 | ✅ 已验证（sessions_list 正常返回） |

**结论**：HTTP API 更轻量直接（少一层 cron 调度中转），但 CLI 更简单（不用管 token 和 HTTP）。对 dispatch.js（每2分钟跑一次的脚本）来说，两者都可行。建议用 HTTP API（路径 B），因为：
1. 无进程 fork 开销
2. JSON body 避免 shell 转义地狱（prompt 中的引号/换行）
3. 错误信息更精确（JSON vs stderr）
4. gateway token 已知（openclaw.json 中 `7349ea95da4fa0e07b89f5ef44a951bd26478778ef6a95d7`）

### 优点
- **派发即时**：不等心跳，dispatch.js 直接触发
- **主 agent 解放**：不再需要 spawn 和 yield
- **消除心跳单点依赖**

### 缺点
- **通知质量降低**：announce 直发子 agent 原文（含元数据、格式粗糙）
- **丧失交付物检查**：主 agent 不再先读交付物确认质量
- **prompt 质量降低**：dispatch.js 只有 title，需在 JS 中拼 prompt 模板
- **ACP 质量约束**：R-121 的完成回报要求需硬编码到 dispatch.js
- **DB 状态延迟**：announce 先发通知，DB 可能还显示 running（最多 2min 延迟）

---

## 三、方案1.5（推荐）：混合方案

### 流程
```
dispatch.js（crontab 每2分钟）
  → 检测 pending 任务
  → 调 openclaw cron add --at now --no-deliver（直接创建，不通知用户）
  → 子 agent 立即启动
  → 完成后写 .task-completions.jsonl
  → 主 agent 心跳检测到新完成 → 读交付物 → 质量检查 → 用自己的话汇报用户
```

### 核心原则
- **派发层去耦合**：dispatch.js 直接 spawn，不经主 agent
- **通知层保留质量**：主 agent 心跳检查 completions，改写后汇报

### 改动清单

**dispatch.js 改动（~30行）：**
- `dispatchPending()` 函数：flag 文件写入 → CLI cron add 调用
- 新增 prompt 模板构造逻辑（研究团队 / ACP 各一套）
- 新增 wechatId / accountId 配置常量

**AGENTS.md 心跳流程改动：**
- 删除 Step 2（检查 dispatch flag 文件）——不再需要
- 新增：心跳检查 .task-completions.jsonl 的新记录 → 读交付物 → 汇报

**保留不变的函数：**
- `processCompletions()` — 不变
- `detectStaleTasks()` — 不变
- `retryFailed()` — 不变

### 优点
- ✅ 派发即时（不等心跳）
- ✅ 主 agent 解放（不再需要 spawn 和 yield）
- ✅ 通知质量保留（主 agent 改写后汇报）
- ✅ 改动最小（dispatch.js 改 ~30 行 + AGENTS.md 微调）
- ✅ ACP prompt 质量可控（dispatch.js 用模板拼）

### 唯一妥协
- 完成通知仍有心跳延迟（最多 30min），但派发不再延迟
- 如需即时通知，可对特定任务类型用 `--announce`（接受质量降低）

---

## 四、三方案对比矩阵

| 维度 | 方案1（现有） | 方案2（全直发） | 方案1.5（混合） |
|------|--------------|----------------|----------------|
| 派发即时性 | ⚠️ 最慢30min | ✅ 立即 | ✅ 立即 |
| 主agent解放 | ❌ 耦合 | ✅ 完全 | ✅ 派发解放，汇报保留 |
| 通知质量 | ✅ 主agent改写 | ⚠️ 子agent原文 | ✅ 主agent改写 |
| 交付物检查 | ✅ 有 | ❌ 无 | ✅ 有 |
| prompt质量 | ✅ 主agent构造 | ⚠️ JS模板拼接 | ⚠️ JS模板拼接 |
| ACP支持 | ✅ 手动spawn | ✅ cron触发 | ✅ cron触发 |
| DB状态一致 | ✅ 即时 | ⚠️ 最多2min延迟 | ⚠️ 最多2min延迟 |
| 失败处理 | ✅ 超时检测+重试 | ✅ 同左 | ✅ 同左 |
| 改动量 | 0 | ~30行 | ~30行+AGENTS.md |
| 心跳依赖 | ❌ 派发依赖心跳 | ✅ 不依赖 | ⚠️ 汇报依赖心跳 |
| 完成通知延迟 | 心跳延迟 | 即时 | 心跳延迟 |

---

## 五、风险评估

### 方案1.5 的潜在问题

| 风险 | 影响 | 缓解 |
|------|------|------|
| dispatch.js 的 execSync 调用失败 | 任务不被派发 | 加 try-catch + 日志 + 下轮自动重试 |
| CLI cron add 参数中有特殊字符 | prompt 被截断 | 用 stdin 传递 message 或 JSON 文件 |
| openclaw CLI 不可用（PATH 问题） | 全部派发失败 | dispatch.js 中硬编码 PATH（已有） |
| prompt 模板不够灵活 | 某些任务类型不适用 | 预留 escape hatch：DB 中 spawn_config 字段存自定义 prompt |
| cron job 堆积（未清理） | 资源浪费 | --delete-after-run + 定期清理 |

### 不改的风险（维持方案1）

| 风险 | 影响 |
|------|------|
| task-0041 重现 | 任务提交后迟迟不派发 |
| 心跳失败 | 所有 pending 任务卡死 |
| 主 agent token 浪费 | 每次 spawn + yield 消耗上下文 |

---

## 六、建议

**推荐方案1.5（混合方案）**，理由：
1. 解决了最痛的派发延迟问题
2. 保留了主 agent 的质量把关价值
3. 改动量可控（~30行 + AGENTS.md 微调）
4. 回退成本低（如果不好用，改回 flag 模式即可）

### 实施步骤
1. ACP 改造 dispatch.js 的 `dispatchPending()` 函数
2. 更新 AGENTS.md 心跳流程（删除 flag 检查，新增 completions 检查）
3. 测试：提交一个测试任务验证全链路
4. 回归：确认 processCompletions / detectStaleTasks / retryFailed 不受影响
