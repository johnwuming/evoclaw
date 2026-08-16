# OpenClaw Token 消耗分布分析与优化方案

**调研日期**: 2026-07-07  
**调研人**: research-lead 子代理  
**数据来源**: 本地 sessions.json、openclaw.json 配置、OpenClaw 官方文档

---

## 一、今日 Token 消耗总览

### 总消耗估算: ~214,000+ tokens（已统计会话）

> 注：不含 main 主会话和当前运行中的子代理，实际消耗更高。

---

## 二、Token 消耗分布明细

### 2.1 Main Agent 会话

| 会话 | Session ID | 输入Tokens | 输出Tokens | 缓存读取 | 总Tokens | 状态 |
|------|-----------|-----------|-----------|---------|---------|------|
| 微信直聊 | 02614ad1 | 4,401 | 729 | 127,744 | 129,083 | 完成 |
| 主会话 | 99bdf975 | - | - | - | - | 完成 |
| Cron: test-acp | 23e3922a | 19,531 | 4 | 4,992 | 24,523 | 完成 |
| Cron: manual-test | 8b8d63e0 | ~19,000 | ~4 | ~5,000 | ~24,000 | 完成 |

### 2.2 Research-Lead Agent 会话

| 会话 | Session ID | 输入Tokens | 输出Tokens | 缓存读取 | 总Tokens | 状态 |
|------|-----------|-----------|-----------|---------|---------|------|
| 主会话 | 887410bc | 39,936 | 661 | 0 | 13,930 | 完成 |
| 子代理(Cron触发) | 7be0dfcf | 10,033 | 6 | 0 | 10,033 | 完成 |
| 子代理(Main触发) | 044b2afa | 64,350 | 9,901 | 133,056 | 36,622 | 完成 |
| 当前子代理 | 632e04e4 | - | - | - | - | 运行中 |

### 2.3 Token 消耗分布饼图（估算）

```
微信直聊会话     ████████████████████████████  129,083 (60%)
Cron任务(2个)   ██████                        48,523 (23%)
子代理(3个)      █████                         60,585 (17%)
主会话           ██                            ~未知
```

---

## 三、Token 消耗构成分析

### 3.1 系统提示词开销（每次请求的固定成本）

| 组成部分 | Main Agent | Research-Lead | 说明 |
|---------|-----------|---------------|------|
| 系统提示词总字符 | 43,346 | 31,120 | 每次请求固定发送 |
| ├ 项目上下文 | 13,330 | 12,410 | AGENTS.md + SOUL.md 等 |
| ├ 非项目上下文 | 30,016 | 18,710 | 系统指令、安全规则等 |
| Skills 提示词 | 13,437 (29个) | 8,670 (22个) | 技能描述注入 |
| 工具Schema | 34,317-38,234 | 5,940-10,946 | 工具定义JSON |

**关键发现**: Main Agent 每次请求的系统提示词+技能+工具Schema约 90,000+ 字符（≈22,500 tokens），这是每次请求的**固定开销**。

### 3.2 主要 Token 消耗源

#### 🔴 系统提示词固定开销 (最大消耗源)
- Main Agent: ~22,500 tokens/请求
- Research-Lead: ~11,000 tokens/请求
- 每次心跳、Cron任务、用户消息都会产生这个开销

#### 🟡 Skills 加载（29个技能，13,437字符）
不需要的技能仍然加载：
- `tencentcloud-lighthouse-skill`: 1,194 字符
- `self-improvement`: 699 字符
- `web-tools-guide`: 662 字符
- `find-skill-skillhub`: 435 字符
- `tavily-search`: 508 字符
- `tencent-docs`: 564 字符
- 以及其他多个不常用技能

#### 🟡 MCP 工具 Schema（~6,000+ 字符）
- Luckin 咖啡 MCP: 11个工具，~3,500 字符（每次请求都加载）
- web-search-prime MCP: ~1,151 字符
- zhipu-reader MCP: ~1,008 字符
- zread MCP: ~967 字符

#### 🟡 心跳机制
- 每30分钟触发一次完整会话轮次
- 每次心跳 = 完整系统提示词 + 上下文 = ~22,500 tokens (Main Agent)
- 一天48次心跳 ≈ 1,080,000 tokens 理论最大值

#### 🟡 Cron 测试任务
- test-acp: 24,523 tokens
- manual-test: ~24,000 tokens
- 这些是测试任务，不产生实际价值

#### 🟢 缓存利用（正面发现）
- 微信会话缓存读取: 127,744 tokens（有效减少实际计费）
- 子代理缓存读取: 133,056 tokens

#### 🔴 长会话上下文膨胀
- 微信会话: 304 条消息
- 工具结果可缩减字符: 51,628 字符
- 预估提示词 tokens: 136,640

---

## 四、优化方案

### 方案 1: 精简 Skills 列表 ⭐⭐⭐⭐⭐
**预期节省**: ~2,000-3,000 tokens/请求

**问题**: Main Agent 加载了 29 个技能，很多不常用。

**建议**:
```json5
// 在 agents.list[].main 中配置只需要的技能
{
  "id": "main",
  "skills": [
    "acp-router", "browser-automation", "canvas", "clawhub",
    "diagram-maker", "healthcheck", "lightclawbot-cron",
    "meme-maker", "node-connect", "notion", "qqbot-channel",
    "qqbot-media", "qqbot-remind", "skill-creator", "spike",
    "taskflow", "tmux", "weather"
  ]
}
```

**移除建议**:
- `tencentcloud-lighthouse-skill` (1,194 字符) - 很少使用
- `self-improvement` (699 字符) - 实验性功能
- `web-tools-guide` (662 字符) - 可合并到 TOOLS.md
- `find-skill-skillhub` (435 字符) - 按需加载
- `tavily-search` (508 字符) - 已有 web-search-prime MCP
- `tencent-docs` (564 字符) - 按需加载
- `github` (337 字符) - 按需加载
- `python-debugpy` (348 字符) - 按需加载
- `node-inspect-debugger` (360 字符) - 按需加载
- `video-frames` (312 字符) - 按需加载
- `taskflow-inbox-triage` (374 字符) - 特定场景使用

### 方案 2: 禁用不常用 MCP 服务器 ⭐⭐⭐⭐⭐
**预期节省**: ~3,000-4,000 tokens/请求

**问题**: Luckin 咖啡 MCP 的 11 个工具定义在每次请求中都发送。

**建议**:
```json5
// 方式1: 完全禁用不常用的 MCP
{
  "mcp": {
    "servers": {
      "luckin": { "enabled": false },  // 需要时手动启用
      "zread": { "enabled": false }    // 需要时手动启用
    }
  }
}

// 方式2: 如果 OpenClaw 支持 MCP 按需加载，配置为按需
```

### 方案 3: 降低心跳频率 ⭐⭐⭐⭐
**预期节省**: ~50-75% 心跳 token 消耗

**问题**: 30 分钟一次心跳太频繁。

**建议**:
```json5
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "2h"  // 从 30m 改为 2h
      }
    }
  }
}
```

### 方案 4: 清理测试 Cron 任务 ⭐⭐⭐⭐
**预期节省**: ~48,000 tokens/天（每次执行）

**问题**: `test-acp` 和 `manual-test` 是测试任务，消耗大量 token。

**建议**:
```bash
# 列出 cron 任务
openclaw cron list

# 删除测试任务
openclaw cron delete 46755c58-fa52-4e31-b653-f58ad6704f22  # test-acp
openclaw cron delete c2da97d0-9689-4a48-b7b2-126337f8098f  # manual-test
```

### 方案 5: 启用会话修剪 (Session Pruning) ⭐⭐⭐⭐
**预期节省**: ~5,000-10,000 tokens/长会话

**问题**: 微信会话有 304 条消息，51,628 字符可缩减的工具结果。

**建议**:
```json5
{
  "agents": {
    "defaults": {
      "pruning": {
        "enabled": true,
        "maxToolResultChars": 5000  // 限制单个工具结果字符数
      }
    }
  }
}
```

### 方案 6: 更激进的压缩策略 ⭐⭐⭐
**预期节省**: 减少长会话上下文膨胀

**问题**: 当前 compaction 模式为 "safeguard"（保守）。

**建议**:
```json5
{
  "agents": {
    "defaults": {
      "compaction": {
        "mode": "default",           // 更激进的压缩
        "keepRecentTokens": 15000,   // 保留最近的 token 数（默认 20000）
        "truncateAfterCompaction": true,  // 压缩后截断转录
        "maxActiveTranscriptBytes": 500000  // 触发压缩的字节阈值
      }
    }
  }
}
```

### 方案 7: 子代理使用更便宜的模型 ⭐⭐⭐
**预期节省**: 降低子代理成本

**问题**: 子代理使用 glm-5.2（与主代理相同），成本较高。

**建议**:
```json5
{
  "agents": {
    "defaults": {
      "subagents": {
        "model": "volcengine-agent-plan/doubao-seed-2.0-mini"  // 更便宜的模型
      }
    }
  }
}
```

### 方案 8: 配置会话自动重置 ⭐⭐⭐
**预期节省**: 防止上下文无限增长

**问题**: 微信会话 304 条消息，上下文持续增长。

**建议**:
```json5
{
  "session": {
    "reset": {
      "mode": "daily",
      "atHour": 4
    },
    "resetByType": {
      "direct": { "mode": "idle", "idleMinutes": 180 }  // 3小时不活跃则重置
    }
  }
}
```

### 方案 9: 精简工作区文件 ⭐⭐
**预期节省**: ~1,000-2,000 tokens/请求

**问题**: AGENTS.md (9,013 字符) + SOUL.md (1,797 字符) + 其他文件 = 14,001 字符项目上下文。

**建议**: 精简 AGENTS.md，移除不常用的指导内容，合并重复信息。

### 方案 10: 优化模型 Fallback 配置 ⭐⭐
**预期节省**: 减少因 fallback 导致的额外请求

**问题**: deepseek-v4-pro 因 billing 原因 fallback 到 glm-5.2，可能导致重复请求。

**建议**:
```json5
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "volcengine-agent-plan/glm-5.2",  // 直接使用可用模型
        "fallbacks": [
          "glmcode/GLM-5.2",
          "glmcode/glm-4.5-air"  // 更便宜的 fallback
        ]
      }
    }
  }
}
```

---

## 五、优化优先级排序

| 优先级 | 方案 | 预期节省 | 实施难度 | 风险 |
|-------|------|---------|---------|------|
| P0 | 禁用不常用 MCP 服务器 | 3,000-4,000 tokens/请求 | 低 | 低（按需启用） |
| P0 | 精简 Skills 列表 | 2,000-3,000 tokens/请求 | 低 | 低（按需启用） |
| P0 | 清理测试 Cron 任务 | 48,000 tokens/天 | 低 | 无 |
| P1 | 降低心跳频率 | 50-75% 心跳消耗 | 低 | 中（响应延迟） |
| P1 | 启用会话修剪 | 5,000-10,000 tokens/长会话 | 中 | 低 |
| P1 | 更激进的压缩策略 | 减少上下文膨胀 | 中 | 中（信息丢失） |
| P2 | 子代理使用更便宜模型 | 降低子代理成本 | 低 | 中（质量下降） |
| P2 | 配置会话自动重置 | 防止上下文增长 | 低 | 中（会话中断） |
| P3 | 精简工作区文件 | 1,000-2,000 tokens/请求 | 中 | 低 |
| P3 | 优化 Fallback 配置 | 减少重复请求 | 低 | 低 |

---

## 六、实施建议

### 立即执行（P0）
1. 删除 `test-acp` 和 `manual-test` Cron 任务
2. 在 `openclaw.json` 中禁用 `luckin` 和 `zread` MCP 服务器
3. 为 Main Agent 配置精简的 skills 列表

### 本周执行（P1）
4. 将心跳频率从 30m 改为 1h 或 2h
5. 启用会话修剪
6. 调整压缩策略为 `default` 模式

### 逐步优化（P2-P3）
7. 为子代理配置更便宜的模型
8. 配置会话自动重置策略
9. 精简 AGENTS.md 和其他工作区文件
10. 优化模型 Fallback 链

---

## 七、预估优化效果

| 优化项 | 每次请求节省 | 每日节省估算 |
|-------|------------|------------|
| 禁用 MCP | 3,500 tokens | ~84,000 tokens (24次请求) |
| 精简 Skills | 2,500 tokens | ~60,000 tokens |
| 清理 Cron | - | ~48,000 tokens |
| 降低心跳 | - | ~500,000+ tokens |
| 会话修剪 | 8,000 tokens | ~16,000 tokens |
| **合计** | ~14,000 tokens/请求 | ~708,000 tokens/天 |

**预期总体降幅**: 60-70% 的日常 token 消耗可通过以上优化减少。

---

## 附录：数据来源

- `/home/ubuntu/.openclaw/agents/main/sessions/sessions.json` - Main Agent 会话数据
- `/home/ubuntu/.openclaw/agents/research-lead/sessions/sessions.json` - Research-Lead 会话数据
- `/home/ubuntu/.openclaw/openclaw.json` - OpenClaw 配置文件
- `https://docs.openclaw.ai/concepts/session` - 会话管理文档
- `https://docs.openclaw.ai/concepts/compaction` - 压缩机制文档
- `https://docs.openclaw.ai/gateway/configuration` - 配置参考文档
- `https://docs.openclaw.ai/help/faq` - FAQ 文档
