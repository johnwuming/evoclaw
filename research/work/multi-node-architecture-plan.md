# OpenClaw 多节点 A2A 架构方案（VPS + HP）

## 目标
HP 电脑作为 OpenClaw 执行节点配对到 VPS Gateway，量化/开发 agent 在 HP 上直接执行任务（有 exec 权限），支持多轮交互协作。

## 当前基础设施

| 项 | VPS（主节点） | HP（待加入节点） |
|---|---|---|
| OpenClaw 版本 | 2026.7.1-2（pnpm global） | 有 openclaw 进程在跑（v22.23.1/node），版本未确认 |
| 角色 | Gateway（调度中枢） | Node Host（执行节点） |
| ZeroTier IP | 10.12.192.98 | 10.12.192.174 |
| 互连通性 | → HP SSH ✅（sshpass） | → VPS ping ✅（22ms） |
| openclaw.json | 完整配置（端口 12145） | 简易配置（mode:local, token） |
| node host | 未安装 | 未安装 |
| 已配对节点 | Paired: 0 | N/A |

## 架构图（目标状态）

```
用户 ← 微信 → VPS Gateway（12145）
                ├── 主 agent（秘书/调度）
                ├── 任务中心（状态管理）
                ├── 研究团队（VPS 本地）
                ├── 开发团队 Claude Code（VPS ACP）
                └── HP 节点（配对连接）
                      ├── quant agent（有 exec 权限）
                      │   → 直接跑回测/进化/数据处理
                      │   → 多轮交互：遇到问题问主 agent
                      └── dev agent（可选，HP 本地开发）
```

## 方案步骤 + 验证计划

---

### 步骤 1：确认 HP OpenClaw 版本兼容性
**目的**：确认 HP 上的 OpenClaw 版本与 VPS 兼容，支持 node host 功能

**操作**：
- SSH 到 HP，查 openclaw 版本
- 确认 node install/run 命令可用

**验证标准**：
- [ ] HP openclaw 版本 ≥ 2026.4.25（acpx 最低要求）
- [ ] `openclaw node install --help` 有输出
- [ ] `openclaw node run --help` 有输出

**风险**：HP 版本过旧 → 需要升级

---

### 步骤 2：HP Node Host 安装 + 配对到 VPS Gateway
**目的**：让 HP 成为 VPS Gateway 的一个配对节点

**操作**：
```bash
# 在 HP 上执行
openclaw node install \
  --host 10.12.192.98 \
  --port 12145 \
  --display-name "HP-量化执行节点"
openclaw node start
```

```bash
# 在 VPS 上批准配对
openclaw nodes pending     # 看到 HP 的请求
openclaw nodes approve     # 批准
```

**验证标准**：
- [ ] VPS 上 `openclaw nodes list` 显示 HP 节点 Paired
- [ ] VPS 上 `openclaw nodes describe --node HP-量化执行节点` 返回能力信息
- [ ] HP 上 `openclaw node status` 显示 active/connected
- [ ] 连接走 ZeroTier（10.12.192.x），不走公网

**风险**：
- Gateway 有 auth token → HP 需要带正确的 token 配对
- ZeroTier 连接可能不稳定 → 需要心跳/重连机制
- HP 在 NAT 后 → ZeroTier 直连已验证 OK（22ms 延迟）

---

### 步骤 3：验证 Node Invoke 能力（关键！）
**目的**：确认 VPS 能通过 `nodes invoke` 在 HP 上执行命令

**操作**：
```bash
# 查 HP 节点支持的 invoke 命令
openclaw nodes describe --node HP-量化执行节点 --json

# 尝试执行 shell 命令（具体 command 名取决于 node host 能力）
openclaw nodes invoke --node HP-量化执行节点 \
  --command "shell.eval" \
  --params '{"command":"echo NODE_INVOKE_OK && hostname"}'
```

**验证标准**：
- [ ] `nodes describe` 返回支持的 invoke command 列表
- [ ] 如果支持 shell.eval/exec → 直接验证命令执行
- [ ] 如果不支持 shell 命令 → 记录实际支持的命令，评估是否够用
- [ ] **这是 go/no-go 决策点**：如果 node host 不支持 shell 执行，需要 plan B

**风险**：
- node host 可能只支持 camera/screen/notify 等媒体命令，不支持 shell → 最大风险点
- Plan B：在 HP 上注册自定义 MCP 工具（`hp.exec`），通过 MCP bridge 暴露给 Gateway
- Plan C：HP 上跑独立 agent（不走 node host），通过 sessions_spawn + exec 工具

---

### 步骤 4：验证 Agent 在 HP 节点上的 Spawn 能力
**目的**：确认 VPS Gateway 能 spawn agent 到 HP 节点执行

**操作**：
```bash
# 尝试 spawn 一个测试 agent 到 HP 节点
sessions_spawn({
  task: "在 HP 上运行 echo HELLO_FROM_HP && uname -a",
  node: "HP-量化执行节点",  # 或通过配置指定
  runtime: "subagent"
})
```

**验证标准**：
- [ ] spawn 成功，agent 在 HP 上执行
- [ ] agent 有 exec 权限（能运行 shell 命令）
- [ ] 结果回流到 VPS 主 agent
- [ ] agent 能访问 HP 上的量化环境（~/quant/ 等路径）

**风险**：
- spawn 可能不支持 `node` 参数 → 需要在 agent 配置里指定 `nodeHost`
- agent 工作目录映射（VPS workspace vs HP workspace 需要对齐）

---

### 步骤 5：验证 A2A 多轮通信
**目的**：确认 HP 节点上的 agent 能与 VPS 上的 agent/主 agent 多轮通信

**操作**：
```bash
# HP 上的 agent 遇到问题 → sessions_send 回主 agent
# 主 agent 回答 → HP agent 继续
```

**验证标准**：
- [ ] HP agent 能 sessions_send 到主 agent
- [ ] 主 agent 能 sessions_send 回 HP agent
- [ ] HP agent 能 sessions_send 到 VPS 上的其他 agent（如 claude-code-local）
- [ ] 多轮交互不丢失上下文

**风险**：
- 跨节点消息路由可能有延迟或丢失
- 需要确认 OpenClaw 的 A2A 消息是否支持跨节点

---

### 步骤 6：任务中心集成设计
**目的**：让任务中心 dispatch 能路由任务到 HP 节点

**操作**：
- 修改 dispatch.js 的 spawnAgentViaCLI，新增 HP 路由逻辑
- 或：在 openclaw.json 里给 quant-compute agent 配置 `nodeHost: "HP-量化执行节点"`

**验证标准**：
- [ ] 任务中心提交量化任务 → 自动路由到 HP 节点执行
- [ ] HP agent 有 exec 权限，能直接跑回测
- [ ] 结果自动回流，状态更新为 pending_review
- [ ] 主 agent 只需审核，不需要接管执行

**风险**：
- dispatch.js 改动可能影响现有流程 → 需要充分回归测试
- 任务超时逻辑需要调整（HP 执行可能更慢）

---

### 步骤 7：HP 量化环境就绪验证
**目的**：确认 HP 节点上的 agent 能访问所有量化资源

**验证标准**：
- [ ] Python + qlib + lightgbm 环境可用（conda envs: quant, rdagent4qlib）
- [ ] 数据目录可访问（~/quant/data/, ~/.qlib/）
- [ ] 脚本目录可访问（~/quant/scripts/, ~/quant/timing/）
- [ ] 结果目录可写（~/quant/results/）
- [ ] OpenClaw workspace 在 HP 上的路径正确

---

### 步骤 8：安全 + 容错设计
**目的**：确保系统安全且 HP 离线不影响 VPS

**验证标准**：
- [ ] HP 离线时，任务中心正确标记失败（不卡死）
- [ ] HP 在线时自动恢复连接
- [ ] 凭据不暴露（HP agent 通过 node host 通道执行，不走 SSH 密码）
- [ ] VPS Gateway 重启后，HP 节点自动重连

---

## 关键决策点

### 🔴 步骤 3 是最大风险点
如果 `openclaw node host` 不支持 shell 执行，整个方案需要调整：

| 结果 | 应对 |
|---|---|
| ✅ 支持 shell.exec/exec | 按计划继续 |
| ❌ 只支持媒体命令 | Plan B：HP 上注册自定义 MCP 工具 |
| ❌ 不支持 invoke | Plan C：HP 上跑独立 Gateway，通过 sessions_spawn 跨 Gateway 通信 |

### Plan B：自定义 MCP 工具
在 HP node host 上注册一个 MCP server，暴露 `hp.exec` / `hp.readFile` / `hp.writeFile` 工具，VPS Gateway 通过 MCP bridge 调用。

### Plan C：双 Gateway 架构
HP 上跑自己的 Gateway（已有 openclaw 进程），通过 OpenClaw 的远程 session 或 cron 机制跨 Gateway 通信。

---

## 当前状态 vs 目标状态

| 场景 | 当前（任务中心单轮） | 目标（多节点 A2A） |
|---|---|---|
| 量化回测 | 子 agent 写脚本 → 主 agent SSH 执行 | HP agent 自己写自己跑 |
| 遇到 bug | 标"待实跑" → 主 agent 修 | HP agent 自己修或问主 agent |
| 开发任务 | claude-code-local（VPS）→ 不碰 HP | VPS 开发 + HP 本地测试 |
| 完成率 | ~40%（主 agent 接管才能完成） | 预期 ~80%+（agent 自主执行） |
| 主 agent 负担 | 重（又调又干） | 轻（只调不干） |
