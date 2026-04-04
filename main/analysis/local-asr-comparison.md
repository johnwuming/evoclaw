# 本地开源语音识别方案对比

> Telegram 语音(.ogg) → 文字，中文优先
> 2026-03-28

---

## 方案总览

| 方案 | ⭐ Stars | 中文准确率 | 速度(CPU) | 模型大小 | 安装复杂度 | 适合场景 |
|------|---------|-----------|----------|---------|-----------|---------|
| **SenseVoice-Small** | 7.9k | ⭐⭐⭐⭐⭐ 中文最强 | **70ms/10秒音频**（比 Whisper-Large 快 15x） | ~234M | 中 | **🏆 首选：中文准确率最高+速度最快** |
| **GLM-ASR-Nano** | 779 | ⭐⭐⭐⭐⭐ 开源SOTA | 需 GPU（1.5B参数） | 1.5B | 高 | 有GPU时的最优选择 |
| **whisper.cpp large-v3** | 48.1k | ⭐⭐⭐⭐ 高 | ~10-30秒 | ~1.5G | 低 | 英文强、生态成熟、CPU友好 |
| **faster-whisper large-v3** | 21.8k | ⭐⭐⭐⭐ 高（同Whisper） | ~5-15秒（4x加速） | ~1.5G | 中 | Whisper加速版 |
| **OpenAI Whisper** | 96.8k | ⭐⭐⭐⭐ 高 | ~30-60秒 | ~1.5G | 低 | 原版，最稳定 |
| **FunASR (Paraformer)** | 15.4k | ⭐⭐⭐⭐ 高（阿里出品） | 快 | ~220M | 中 | 中文专精+工具链完整 |
| **sherpa-onnx** | 11.2k | ⭐⭐⭐⭐ 依赖模型 | 快 | 取决于模型 | 中 | OpenClaw 已内置支持 |

---

## 🏆 推荐：SenseVoice-Small + whisper.cpp 双链路

### 为什么选 SenseVoice-Small

1. **中文准确率超过 Whisper-Large**（阿里达摩院基准测试）
   - AISHELL-1、AISHELL-2、Wenetspeech 全部领先
   - 40万小时数据训练，支持 50+ 语言

2. **速度碾压**
   - 10秒音频仅需 70ms（非自回归架构）
   - 比 Whisper-Large 快 **15 倍**
   - 比 Whisper-Small 快 **5 倍**

3. **额外能力**
   - 语音情感识别（自动检测语气）
   - 音频事件检测（笑声、咳嗽、掌声）
   - 支持粤语、英语、日语、韩语

4. **模型小**
   - 仅 ~234M 参数
   - CPU 推理完全可行

5. **已导出 ONNX**
   - funasr-onnx pip 包直接安装
   - 可集成到 whisper.cpp 或 sherpa-onnx

### 为什么还要 whisper.cpp 兜底

- SenseVoice 依赖 Python + PyTorch/ONNX 运行时
- whisper.cpp 纯 C 实现，零依赖，极其稳定
- 英文场景 whisper large-v3 仍有优势
- OpenClaw 已内置 sherpa-onnx/whisper-cli 自动检测

---

## 最终方案

```
Telegram 语音 (.ogg)
    │
    ▼ OpenClaw Audio Pipeline
    │
    ├─ ① SenseVoice-Small（首选，CLI wrapper）
    │   70ms/10秒 | 中文准确率最高 | 234M 参数
    │   需要：pip install funasr-onnx + ffmpeg
    │
    ├─ ② GLM-ASR API（付费备选，已有 wrapper）
    │   3-5秒 | 中文最强 | ¥0.06/分钟
    │   需要网络
    │
    └─ ③ whisper.cpp（兜底，离线）
        5-30秒 | 英文强 | 已内置支持
        需要：whisper-cpp + large-v3 模型
```

---

## 安装步骤

### Step 1：安装 ffmpeg（所有方案都需要）

```bash
sudo apt install ffmpeg
```

### Step 2：安装 SenseVoice-Small（首选）

```bash
# 安装 ONNX 运行时版本（轻量，不依赖 PyTorch）
pip install funasr-onnx

# 下载模型（首次运行自动下载，或手动）
# 模型会缓存到 ~/.cache/modelscope/
```

CLI wrapper（已创建）：

```bash
# ~/.openclaw/workspace/scripts/sensevoice-cli.py
# 用法：sensevoice-cli.py <audio_path>
# 输出：转录文字到 stdout
```

### Step 3：配置 openclaw.json

```json5
{
  tools: {
    media: {
      audio: {
        enabled: true,
        echoTranscript: true,
        echoFormat: '📝 "{transcript}"',
        models: [
          // ① SenseVoice（中文最强+最快）
          {
            type: "cli",
            command: "python3",
            args: [
              "/home/noname/.openclaw/workspace/scripts/sensevoice-cli.py",
              "{{MediaPath}}"
            ],
            timeoutSeconds: 30
          },
          // ② GLM-ASR API（付费，中文最强）
          {
            type: "cli",
            command: "python3",
            args: [
              "/home/noname/.openclaw/workspace/scripts/glm-asr-cli.py",
              "{{MediaPath}}"
            ],
            timeoutSeconds: 30,
            env: {
              ZAI_API_KEY: "你的key"
            }
          }
          // ③ whisper.cpp（OpenClaw 自动检测，无需配置）
        ]
      }
    }
  }
}
```

---

## 各方案详细对比

### SenseVoice-Small（阿里达摩院）

**优势**
- 中文准确率开源最高（AISHELL-1/2/WeNet 全部领先 Whisper）
- 速度极快：非自回归架构，10秒音频 70ms
- 模型小：~234M，CPU 可跑
- 额外能力：情感识别+事件检测
- ONNX 导出：funasr-onnx 零 PyTorch 依赖

**劣势**
- 社区较小（7.9k stars vs Whisper 96.8k）
- 需要下载 ModelScope 模型（中国网络友好）
- 英文准确率不如 Whisper-Large

### GLM-ASR-Nano（智谱开源版）

**优势**
- 开源 SOTA：平均错误率 4.10（开源最低）
- 方言支持极强（粤语+8种官话）
- 小声识别能力强
- 17 种语言

**劣势**
- 1.5B 参数，CPU 推理很慢（需 GPU）
- 需要 transformers 5.0.0（从源码安装）或 PyTorch
- 安装复杂度高
- 社区太小（779 stars）

### whisper.cpp（ggerganov）

**优势**
- 纯 C 实现，零依赖
- 生态最成熟（48.1k stars）
- OpenClaw 已内置支持
- 支持 GPU 加速
- 多种量化格式（int8/fp16/fp32）

**劣势**
- 中文不如 SenseVoice
- CPU 上 large-v3 较慢（10-30秒）
- 模型大（1.5G）

### faster-whisper（SYSTRAN）

**优势**
- 基于 CTranslate2，比原版快 4 倍
- 内存占用更低（4bit 量化）
- API 兼容原版 Whisper

**劣势**
- 仍需 PyTorch 或 CTranslate2
- CPU 加速不如 SenseVoice 的非自回归架构

### FunASR + Paraformer（阿里）

**优势**
- 完整工具链：ASR + VAD + 标点恢复 + 说话人分离
- Paraformer 中文专精
- 15.4k stars，社区活跃

**劣势**
- 依赖较重
- 整合复杂
- SenseVoice 已是它的精神继任者
