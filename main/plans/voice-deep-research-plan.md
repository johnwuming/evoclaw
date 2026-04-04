# 语音输入深度研究 — OpenClaw + Telegram 落地方案

> 目标：Telegram 语音输入 → 文字输出深度研究报告
> 核心指标：极致准确率 + 极致速度
> 2026-03-28

---

## 一、用户旅程

```
无名在 Telegram 按住语音按钮说话：
"帮我深度研究一下 2026 年 multi-agent 架构在 AI 编程助手中的应用"
        │
        ▼ (~3秒)
Telegram 发送 .ogg 语音消息
        │
        ▼ (~5-10秒)
OpenClaw 自动转录为文字，echo 确认：
📝 "帮我深度研究一下 2026 年 multi-agent 架构在 AI 编程助手中的应用"
        │
        ▼ (即时)
Lead Researcher 收到文字，判断复杂度=深度研究
        │
        ▼ (~30秒，并行)
4 个 Search Agent 并行搜索
        │
        ▼ (~20秒)
双 Reviewer 交叉验证
        │
        ▼ (~15秒)
Citation Agent + Writer Agent 生成报告
        │
        ▼
Telegram 收到文字报告（Markdown 格式）
```

**总耗时预估：3-5 分钟**（vs 人类手动研究 2-4 小时）

---

## 二、技术架构

### 语音输入链路

```
Telegram 语音 (.ogg Opus)
    │
    ▼
OpenClaw Media Understanding
    │
    ├─ 首选：智谱 GLM-ASR（通过 OpenAI 兼容 API）
    │  延迟：~3-5秒
    │  中文准确率：行业领先
    │  成本：免费额度 或 极低
    │
    ├─ 备选 1：本地 whisper-cpp
    │  延迟：~10-30秒（CPU）/ ~3-5秒（GPU）
    │  中文准确率：中等（large 模型较好）
    │  成本：$0（本地）
    │
    └─ 备选 2：OpenAI Whisper API
       延迟：~3-5秒
       中文准确率：高
       成本：$0.006/分钟
```

### 研究执行链路

```
转录文字 → Lead Researcher → Search Agents → Reviewers → Writer → 报告
            (GLM-5.1)       (GLM-5-turbo×4)  (GLM-5.1+5t)  (GLM-5.1)
```

### 输出链路

```
Writer Agent 生成 Markdown 报告
    │
    ▼
Telegram 文字消息（支持 Markdown 渲染）
    │
    ├─ 如果报告 > 4096 字符：分段发送
    └─ 可选：生成 PDF 发送（后续版本）
```

---

## 三、准确率优化策略

### 3.1 语音转录准确率（输入层）

| 策略 | 效果 | 实现 |
|------|------|------|
| **智谱 GLM-ASR 优先** | 中文识别率最高 | 配置为首选 provider |
| **echo 确认机制** | 用户可纠正转录错误 | `echoTranscript: true` |
| ** whisper 大模型备选** | 智谱不可用时兜底 | 安装 whisper-cpp + large 模型 |
| **安静环境提示** | 减少噪声干扰 | 首次使用时提示用户 |

### 3.2 搜索准确率（信息收集层）

| 策略 | 效果 | 实现 |
|------|------|------|
| **智谱 Web Search API** | 中文搜索最优 | 待配置（有 API key） |
| **双搜索引擎** | DuckDuckGo + 浏览器 Google 互补 | Search Agent 已实现 |
| **多轮搜索** | 不满足于第一页结果 | 最多 15 次工具调用 |
| **原文摘录** | 不改写，保留原始数据 | Search Agent `evidence` 字段 |
| **来源分级** | primary/secondary/tertiary | Reviewer A 评分依据 |

### 3.3 验证准确率（质量控制层）

| 策略 | 效果 | 实现 |
|------|------|------|
| **双 Reviewer 交叉验证** | 消除单一偏见 | v4.1 核心机制 |
| **多源交叉验证** | 单一来源上限 5 分 | Reviewer A 规则 |
| **分项检查** | 准确性和完整性分别判断 | Lead Phase 5 |
| **矛盾检测** | 发现不一致的声明 | Reviewer A contradictions |
| **迭代补充** | 质量不够就再搜一轮 | 最多 4 轮 |

### 3.4 报告准确率（输出层）

| 策略 | 效果 | 实现 |
|------|------|------|
| **只使用 verified findings** | 未验证的信息不进报告 | Writer Agent 只收 score≥7 |
| **引用标注** | 每个事实可追溯 | Writer 必须标注 [1][2] |
| **知识缺口诚实标注** | 不编造 | "未知"比编造更有价值 |
| **中文报告** | 用户语言匹配 | Writer 语言匹配规则 |

---

## 四、速度优化策略

### 4.1 时间分解（深度研究场景）

| 阶段 | 耗时 | 优化手段 |
|------|------|---------|
| 语音转录 | 3-5秒 | 智谱 GLM-ASR（vs 本地 whisper 30秒） |
| 复杂度判断 | 2秒 | Lead 本地判断，无需 LLM 调用 |
| Search Agent ×4 并行 | 30-60秒 | 并行 spawn，GLM-5-turbo 快模型 |
| Reviewer ×2 并行 | 20-30秒 | 并行 spawn |
| Citation Agent | 10-15秒 | web_fetch 批量验证 |
| Writer Agent | 15-20秒 | GLM-5.1 强写作 |
| **总计** | **~3-5 分钟** | |

### 4.2 速度 vs 准确率的平衡

**关键洞察：不是所有问题都需要深度研究。**

```
用户语音输入
    │
    ▼
Lead 判断复杂度
    │
    ├─ 简单事实（~10秒）
    │   1 Search Agent → 直接回答
    │   准确率：中等 | 速度：极快
    │
    ├─ 中等分析（~1分钟）
    │   2-3 Search Agent → 1 Reviewer → 直接回答
    │   准确率：高 | 速度：快
    │
    └─ 深度研究（~3-5分钟）
        4 Search Agent → 双 Reviewer → Writer → 完整报告
        准确率：极高 | 速度：可接受
```

### 4.3 进一步加速的手段

| 手段 | 加速效果 | 准确率影响 | 建议 |
|------|---------|-----------|------|
| 减少 Search Agent 到 2-3 个 | -30% 时间 | -10% 覆盖 | 简单/中等场景使用 |
| Reviewer 只用 1 个 | -15% 时间 | -15% 验证强度 | 低风险场景使用 |
| 跳过 Citation Agent | -10% 时间 | 引用不规范 | 快速模式使用 |
| Search Agent 用更小模型 | -20% 时间 | -5% 提取质量 | GLM-5-turbo 已是最优平衡 |
| 缓存常见问题结果 | -80% 时间（命中时） | 无影响 | 后续版本实现 |

---

## 五、配置方案

### 5.1 openclaw.json 配置

```json5
{
  // === 语音转录 ===
  tools: {
    media: {
      audio: {
        enabled: true,
        echoTranscript: true,
        echoFormat: "📝 \"{transcript}\"\n\n正在启动深度研究...",
        maxBytes: 20971520,
        models: [
          // 首选：智谱 GLM-ASR（如果支持 OpenAI 兼容音频 API）
          // {
          //   provider: "zai",
          //   model: "glm-asr",
          //   baseUrl: "https://open.bigmodel.cn/api/paas/v4"
          // },
          // 备选：OpenAI Whisper（需 API key）
          // {
          //   provider: "openai",
          //   model: "gpt-4o-mini-transcribe"
          // },
          // 兜底：本地 whisper-cpp
          {
            type: "cli",
            command: "whisper-cli",
            args: ["--model", "/usr/share/whisper/ggml-large-v3.bin", "{{MediaPath}}", "--output-txt"],
            timeoutSeconds: 60
          }
        ]
      }
    }
  },

  // === 研究 Agent 配置 ===
  agents: {
    defaults: {
      model: {
        primary: "zai/glm-5.1"
      },
      subagents: {
        maxSpawnDepth: 2,
        maxConcurrent: 8,
        maxChildrenPerAgent: 5,
        runTimeoutSeconds: 600,
        model: "zai/glm-5-turbo"
      }
    }
  }
}
```

### 5.2 需要安装的组件

| 组件 | 用途 | 安装方式 | 优先级 |
|------|------|---------|--------|
| **whisper-cpp** | 本地语音转录兜底 | `sudo apt install whisper-cpp` 或源码编译 | 高 |
| **whisper 模型** | large-v3 中文最优 | 下载 ggml-large-v3.bin 到 /usr/share/whisper/ | 高 |
| **智谱 GLM-ASR** | 首选中文转录 | 验证 OpenClaw 是否支持 zai provider 音频 | 中 |
| **智谱 Web Search** | 中文搜索 | 配置 MCP Server 或 API 调用 | 中 |

### 5.3 安装 whisper-cpp

```bash
# 方式 1：apt（如果可用）
sudo apt install whisper-cpp

# 方式 2：源码编译（推荐，支持 GPU）
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
cmake -B build -DWHISPER_CUDA=ON  # 如有 GPU
cmake --build build -j
sudo cp build/bin/whisper-cli /usr/local/bin/

# 下载 large-v3 模型（中文最优）
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
sudo mkdir -p /usr/share/whisper
sudo mv ggml-large-v3.bin /usr/share/whisper/

# 测试
whisper-cli --model /usr/share/whisper/ggml-large-v3.bin test.ogg --output-txt
```

---

## 六、Lead Researcher 语音模式适配

在 Lead 提示词开头增加语音模式检测：

```
<VoiceMode>
当收到包含 [Audio] 标记的消息时：
1. 用户的原始语音已被转录为文字
2. 检查 echoTranscript 是否与转录一致（用户可能已纠正）
3. 按正常流程处理转录后的文字
4. 如果语音很短（< 10 字）且像简单问题，直接回答不做深度研究
5. 如果语音较长或明确要求"深度研究/调研/分析"，启动完整研究流程
</VoiceMode>
```

---

## 七、准确率 vs 速度决策矩阵

| 场景 | 触发条件 | Search | Review | Writer | 预期耗时 | 准确率 |
|------|---------|--------|--------|--------|---------|--------|
| **快速问答** | <10字，简单问题 | 0 | 0 | 0 | ~10秒 | 中 |
| **标准查询** | 10-50字，事实性问题 | 1 | 0 | 0 | ~30秒 | 中高 |
| **对比分析** | "A vs B"、"比较" | 2-3 | 1(A) | 0 | ~1分钟 | 高 |
| **深度研究** | "深度研究/调研/分析"、>50字 | 4 | 2(A+B) | 1 | ~3-5分钟 | 极高 |
| **极速模式** | 用户明确说"快速" | 2 | 0 | 0 | ~30秒 | 中 |

---

## 八、实施步骤

### Phase 1：语音输入（~30分钟）
1. 安装 whisper-cpp + large-v3 模型
2. 配置 openclaw.json audio 部分
3. 测试 Telegram 语音消息转录
4. 验证 echo 确认功能

### Phase 2：研究团队集成（~1小时）
1. 将 v4.1 提示词集成到 Lead 的 AGENTS.md 或 skill 中
2. 配置 subagent 参数（maxSpawnDepth, model 等）
3. 测试简单问题快速回答

### Phase 3：端到端测试（~30分钟）
1. 发送语音："2026年 AI agent 深度研究的最佳实践"
2. 验证：转录 → 复杂度判断 → 搜索 → 审核 → 报告 全链路
3. 检查报告质量和引用完整性

### Phase 4：优化（持续）
1. 根据测试结果调整 Search Agent 数量
2. 配置智谱 Web Search API（中文搜索）
3. 验证智谱 GLM-ASR 音频转录（如果支持）

---

## 九、成本估算

| 组件 | 单次深度研究 | 简单问答 |
|------|------------|---------|
| 语音转录（whisper 本地） | $0 | $0 |
| 语音转录（OpenAI API） | ~$0.01 | ~$0.001 |
| GLM-5.1（Lead + Reviewer A + Writer） | ~50k token | ~5k token |
| GLM-5-turbo（Search ×4 + Reviewer B + Citation） | ~80k token | 0 |
| **总计** | **~130k token，$0** | **~5k token，$0** |

全部使用智谱免费模型，成本为 $0。

---

## 十、风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 语音转录错误 | 研究方向偏移 | echo 确认 + 用户可纠正 |
| DuckDuckGo 限流 | 搜索质量下降 | 浏览器 Google 备选 |
| 模型输出格式错误 | 流程中断 | JSON 容错解析 |
| 报告超过 Telegram 4096 字符 | 发送失败 | 分段发送 |
| 深度研究耗时过长 | 用户等待焦虑 | 即时反馈"正在研究中..." |

### Telegram 长报告处理

```python
# Lead 在发送报告时的逻辑
if len(report) > 4000:
    # 分段发送，每段 < 4000 字符
    # 在段落边界（## 或 \n\n）处切分
    chunks = split_at_headers(report, max_len=4000)
    for i, chunk in enumerate(chunks):
        send(chunk)
        if i < len(chunks) - 1:
            send("（续...）")
```
