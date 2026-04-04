# 语音输入方案 — Telegram 语音 → 准确文字

> 只解决"语音 → 文字"这一层，任务执行和输出保持现有方式不变
> 2026-03-28

---

## 问题定义

无名通过 Telegram 发送语音消息，需要：
1. **极致准确率** — 转录错误会直接影响后续任务质量
2. **极致速度** — 语音 → 文字的延迟越小越好
3. **中文优先** — 日常使用以中文为主

## 方案对比

| 方案 | 中文准确率 | 延迟 | 成本 | OpenClaw 支持 |
|------|-----------|------|------|--------------|
| **GLM-ASR（CLI wrapper）** | ⭐⭐⭐⭐⭐ 最强 | ~3-5秒 | ¥0.06/分钟 | ✅ CLI 模式 |
| OpenAI Whisper API | ⭐⭐⭐⭐ 高 | ~3-5秒 | $0.006/分钟 | ✅ 原生 |
| Groq Whisper | ⭐⭐⭐⭐ 高 | ~1-2秒（最快） | 免费额度 | ✅ 原生 |
| 本地 whisper-cpp large-v3 | ⭐⭐⭐ 中高 | ~10-30秒(CPU) | $0 | ✅ CLI 模式 |
| 本地 whisper-cpp tiny | ⭐⭐ 中 | ~2-5秒(CPU) | $0 | ✅ CLI 模式 |
| Edge TTS (反向) | ❌ 只能 TTS | — | — | ❌ |

**结论：GLM-ASR 作为首选（中文最强），Groq Whisper 作为极速备选，本地 whisper 兜底。**

---

## 推荐方案：GLM-ASR + Groq 双链路

```
Telegram 语音 (.ogg)
    │
    ▼
OpenClaw Audio Pipeline
    │
    ├─ ① GLM-ASR（首选，CLI wrapper）
    │   延迟：3-5秒 | 中文准确率：SOTA
    │   支持：中英文 + 8种方言 | 热词提升专有名词
    │   限制：≤30秒音频（足够，Telegram 语音通常 <60秒）
    │
    ├─ ② Groq Whisper large-v3（备选，原生）
    │   延迟：1-2秒 | 中文准确率：高
    │   需要配置 GROQ_API_KEY
    │
    └─ ③ 本地 whisper-cpp（兜底，离线）
        延迟：5-30秒 | 中文准确率：中
        完全离线，任何网络问题都不怕
```

OpenClaw 按顺序尝试，第一个成功就停止。

---

## 实施步骤

### Step 1：部署 GLM-ASR CLI wrapper（5分钟）

已创建：`~/workspace/scripts/glm-asr-cli.py`

```bash
# 确认可执行
chmod +x ~/.openclaw/workspace/scripts/glm-asr-cli.py

# 测试（需要先设环境变量）
ZAI_API_KEY="f5852d8d..." python3 ~/.openclaw/workspace/scripts/glm-asr-cli.py test.ogg
```

### Step 2：配置 openclaw.json（2分钟）

```json5
{
  tools: {
    media: {
      audio: {
        enabled: true,
        echoTranscript: true,
        echoFormat: '📝 "{transcript}"',
        maxBytes: 20971520,  // 20MB
        models: [
          // ① 首选：GLM-ASR（中文最强）
          {
            type: "cli",
            command: "python3",
            args: [
              "/home/noname/.openclaw/workspace/scripts/glm-asr-cli.py",
              "{{MediaPath}}"
            ],
            timeoutSeconds: 30,
            env: {
              // 从 models.json 的 zai provider 读取
              ZAI_API_KEY: "f5852d8d..."
            }
          },
          // ② 备选：Groq Whisper（极速）
          // {
          //   provider: "groq",
          //   model: "whisper-large-v3-turbo"
          // },
          // ③ 兜底：本地 whisper（离线）
          // {
          //   type: "cli",
          //   command: "whisper-cli",
          //   args: ["--model", "/path/to/ggml-large-v3.bin", "{{MediaPath}}"],
          //   timeoutSeconds: 60
          // }
        ]
      }
    }
  }
}
```

### Step 3：确保 ZAI_API_KEY 可用

智谱 key 在 `agents/main/agent/models.json` 的 `zai` provider 下。
OpenClaw CLI 模式支持 `env` 字段传入环境变量，或者直接在 openclaw.json 顶层设 env：

```json5
{
  env: {
    ZAI_API_KEY: "f5852d8d..."  // 同 models.json 中的 key
  }
}
```

### Step 4：测试（2分钟）

1. 在 Telegram 发一条语音消息
2. 观察 echo 确认是否正确
3. 确认转录文字被正确传递给后续任务

---

## GLM-ASR 关键优势

### 1. 上下文智能理解
不同于传统 ASR 的逐字识别，GLM-ASR 基于语言模型上下文优化输出，转录结果更接近自然表达（同音字纠错、标点自动添加）。

### 2. 热词支持
可通过 `hotwords` 参数提升特定领域词汇识别率：
```python
hotwords=["multi-agent", "OpenClaw", "GLM-5", "智谱"]
```
后续可扩展 wrapper 支持热词配置。

### 3. 方言支持
8 种中国方言覆盖，如果无名有口音或偶尔说方言也能识别。

### 4. 流式转录
支持 `stream: true`，未来可扩展为"边说边转录"的实时体验。

---

## 成本

| 使用频率 | GLM-ASR 费用 |
|---------|-------------|
| 每天 10 条 30 秒语音 | ¥0.03/天 ≈ ¥1/月 |
| 每天 50 条 | ¥0.15/天 ≈ ¥4.5/月 |
| 每月 1000 条 | ¥5 |

几乎可忽略。

---

## GLM-ASR 的限制

| 限制 | 影响 | 缓解 |
|------|------|------|
| 音频 ≤ 30 秒 | 超长语音被截断 | Telegram 语音通常 <60秒；超长语音需分段 |
| 仅支持 wav/mp3 | Telegram 默认 .ogg 需转换 | wrapper 中添加 ffmpeg 转码 |
| 依赖网络 | 离线不可用 | 本地 whisper 兜底 |

### OGG 转码问题

Telegram 语音默认编码是 **Opus in OGG**，而 GLM-ASR 只支持 **wav/mp3**。

需要在 wrapper 中加 ffmpeg 转码：

```python
import subprocess, tempfile

def convert_to_wav(ogg_path: str) -> str:
    wav_path = ogg_path + ".wav"
    subprocess.run([
        "ffmpeg", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path
    ], check=True, capture_output=True)
    return wav_path
```

让我更新 wrapper。

---

## 待办

- [ ] 更新 glm-asr-cli.py 加入 ogg→wav 转码
- [ ] 确认 ffmpeg 是否已安装
- [ ] 配置 openclaw.json audio 部分
- [ ] 端到端测试 Telegram 语音 → 文字
- [ ] （可选）申请 Groq API key 作为极速备选
- [ ] （可选）安装 whisper-cpp 作为离线兜底
