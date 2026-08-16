# Qlib + RD-Agent 本地 HP 部署适用性评估与替代方案

> **报告编号**: R-195  
> **类别**: 量化投资  
> **日期**: 2026-08-10  
> **状态**: 完稿  
> **关联报告**: R-194（OpenClaw 与 RD-Agent 结合方案）、R-187（AI时代个人量化投资全景）、RD-Agent Docker 排查报告

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [HP 硬件现状与瓶颈分析](#2-hp-硬件现状与瓶颈分析)
3. [Qlib+RD-Agent 对硬件的真实要求](#3-qlibrd-agent-对硬件的真实要求)
4. [RD-Agent 在国内环境的可用性](#4-rd-agent-在国内环境的可用性)
5. [替代方案全面对比](#5-替代方案全面对比)
6. [结论与推荐路径](#6-结论与推荐路径)
7. [时间成本与金钱成本估算](#7-时间成本与金钱成本估算)
8. [实施建议与下一步](#8-实施建议与下一步)

---

## 1. 执行摘要

### 核心结论：有条件适合，但条件苛刻，推荐混合模式

**HP 电脑（i5-4590T / 15G RAM / 无 GPU / 80G 磁盘）可以运行 RD-Agent Conda 模式的因子进化循环，但仅限于 CSI300 股票池，且速度较慢。** 一轮完整的因子进化循环（假设→编码→回测→反馈）预计需要 15-30 分钟，其中瓶颈不在 CPU 回测本身，而在 LLM API 调用的多次往返。

**关键发现：**

| 维度 | 结论 | 详情 |
|------|------|------|
| **CSI300 回测** | ✅ 可行 | 内存占用 4-8GB，15G 足够 |
| **CSIALL（全市场）** | ❌ 不可行 | 峰值内存 ~28.5GB（Qlib Issue #2097），15G 远不够 |
| **CPU 回测速度** | ⚠️ 可接受 | LightGBM 在 CPU 上反而可能比 GPU 快（小数据集），CSI300 单轮训练 2-5 分钟 |
| **Docker 模式** | ❌ 不推荐 | 5GB+ CUDA 镜像无意义，HP 无 GPU |
| **Conda 模式** | ✅ 推荐路径 | 绕过 Docker，直接在本地 conda 环境运行 |
| **磁盘空间** | ⚠️ 需监控 | 80G 可用，但 trace+workspace 每月增长 2-5GB |
| **LLM API** | ✅ 稳定 | DeepSeek API 国内直连，延迟低 |

**最优推荐：方案 D（混合模式）** — VPS（OpenClaw 编排 + LLM 调用）+ HP 本地（Qlib 回测执行），兼顾成本和可用性。

---

## 2. HP 硬件现状与瓶颈分析

### 2.1 硬件规格

| 组件 | 规格 | 评估 |
|------|------|------|
| **CPU** | Intel i5-4590T @ 2.0GHz (4C4T, Haswell, 2014) | ⚠️ 性能约为现代 i3 的 50%，PassMark 评分 ~3700 |
| **内存** | 15GB DDR3 | ✅ 勉强够 CSI300，不够 CSIALL |
| **GPU** | 无（Intel HD4600 核显） | ❌ 无法运行深度学习模型（LSTM/Transformer） |
| **磁盘** | 80GB 可用 | ⚠️ 需定期清理，否则 3-6 个月可能满 |
| **网络** | 国内家庭宽带 | ⚠️ 访问 GitHub/Docker Hub 慢，但 DeepSeek API 直连快 |

### 2.2 已知问题（来自 RD-Agent Docker 排查报告）

根据 `shared/results/work/rdagent-docker-debug.md` 的详细排查：

1. **Docker 镜像过大**：RD-Agent 的 Dockerfile 使用 `pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime` 基础镜像（压缩 5GB+，解压 10GB+），HP 无 GPU，下载纯属浪费
2. **环境变量名错误**：`.env` 中 `MODEL_CODER_ENV_TYPE=conda` 是错误变量名，正确为 `MODEL_CoSTEER_env_type=conda`（Pydantic Settings 前缀机制）
3. **国内网络拉取 Docker 镜像极慢**：无镜像加速器时，5GB 镜像可能需要数小时甚至超时失败

### 2.3 瓶颈排序

```
最大瓶颈：磁盘空间（80G） > 内存（15G） > CPU 性能 > 网络
```

CPU 性能反而不是最大瓶颈——因为主要时间消耗在 LLM API 调用的等待上，而非本地计算。

---

## 3. Qlib+RD-Agent 对硬件的真实要求

### 3.1 Qlib 回测在纯 CPU 上的性能

#### 3.1.1 回测时间分解

一轮 RD-Agent 因子进化循环的完整步骤和预估耗时（HP i5-4590T 环境）：

| 步骤 | 操作 | 主要耗时 | HP 预估时间 | 瓶颈 |
|------|------|----------|-----------|------|
| 1. 假设生成 | LLM 生成因子假设 | DeepSeek API 调用 1-3 次 | 30-90 秒 | API 延迟 |
| 2. 代码生成 | CoSTEER 生成因子代码 | LLM API 调用 2-5 次 | 60-180 秒 | API 延迟 |
| 3. 因子计算 | 在 Qlib 中计算新因子值 | CPU 轻量计算 | 10-30 秒 | CPU |
| 4. 模型训练 | LightGBM 训练（CSI300） | CPU 多核训练 | **120-300 秒** | CPU |
| 5. 组合回测 | Qlib portfolio 回测 | CPU 计算收益/IC | 30-60 秒 | CPU |
| 6. 反馈生成 | LLM 分析回测结果 | DeepSeek API 调用 1-2 次 | 30-60 秒 | API 延迟 |
| 7. 环境管理 | Conda 环境准备/清理 | 文件 I/O | 10-30 秒 | 磁盘 |
| **合计** | — | — | **约 5-12 分钟** | API > CPU |

**关键发现：LLM API 调用占总时间的 50-60%，而非 CPU 计算。** 这意味着 i5-4590T 的性能劣势影响有限——即使 CPU 快 3 倍，总循环时间也只缩短 30-40%。

#### 3.1.2 LightGBM CPU vs GPU 性能

出人意料的发现：对于 Qlib 的 CSI300 日频数据量级，**LightGBM 在 CPU 上可能比 GPU 更快**。

- LightGBM 官方基准测试显示：对于小到中等数据集（<100万样本），GPU 的数据传输开销可能超过计算收益
- Reddit 实测案例：LightGBM 46 次训练+回测，CPU 130 秒 vs GPU 250 秒（GPU 反而慢 2 倍）
- Qlib 的 Alpha158 因子集 + CSI300（约 300 只股票 × 8 年日线），训练数据约 60 万行 × 158 列——这是典型的 CPU 友好规模
- Qlib 博客实测（现代 CPU）：数据加载 9 秒 + LightGBM 训练 <30 秒
- **HP i5-4590T 约为现代 i5 性能的 40-50%**，预估训练时间放大约 2-2.5 倍

#### 3.1.3 深度学习模型的限制

CPU 上的深度学习模型（LSTM/Transformer/GRU）速度极慢：
- Qlib 的 LSTM 模型在 CSI300 上训练（现代 CPU）约需 10-30 分钟/epoch
- HP 上可能需要 30-60 分钟/epoch，完整训练（50 epochs）需 25-50 小时
- **结论：HP 上 RD-Agent 的模型优化（fin_model/fin_quant）只能使用 LightGBM/XGBoost，不能使用深度学习模型**

### 3.2 内存需求

| 场景 | 预估峰值内存 | HP 15G 是否足够 |
|------|-------------|----------------|
| Qlib 数据加载（CSI300） | 1-2 GB | ✅ |
| Alpha158 因子计算（CSI300） | 2-4 GB | ✅ |
| LightGBM 训练（CSI300） | +1-2 GB | ✅ |
| Qlib 回测 + 组合分析 | +1-2 GB | ✅ |
| RD-Agent Python 进程 | 0.5-1 GB | ✅ |
| **CSI300 总计** | **5-9 GB** | **✅ 足够** |
| | | |
| Qlib 数据加载（CSIALL 全市场） | 5-8 GB | ⚠️ 紧张 |
| Alpha360 因子计算（CSIALL） | 15-20 GB | ❌ 不足 |
| **CSIALL 峰值（Issue #2097 实测）** | **~28.5 GB** | **❌ 远不够** |

**关键数据来源**：Qlib GitHub Issue #2097 明确报告，使用 instrument="all" 时，仅数据集初始化的峰值内存就达到 ~28.5GB，32GB 机器都可能 OOM。

**结论**：
- **CSI300（沪深300）**：15G 内存充足，可正常运行 ✅
- **CSI500（中证500）**：15G 内存勉强够，建议减少因子数量 ⚠️
- **CSIALL（全A股）**：完全不可行，需要 32GB+ 内存 ❌

### 3.3 磁盘消耗

| 项目 | 大小 | 说明 |
|------|------|------|
| Qlib 数据（CSI300，2008-2024） | ~0.5-1 GB | 日线 OHLCV + 复权因子 |
| Qlib 数据（CSIALL，2008-2024） | ~2-3 GB | 全市场日线数据 |
| Conda 环境（rdagent4qlib） | ~3-5 GB | Python + Qlib + LightGBM + torch CPU |
| RD-Agent 本体 | ~200 MB | pip install rdagent |
| **每轮循环 workspace** | **50-200 MB** | 因子代码 + 回测结果 + 缓存 |
| **每轮循环 trace** | **10-50 MB** | pickle 格式的假设/代码/反馈记录 |
| **每轮循环日志** | **1-5 MB** | stdout 日志 |

**长期运行磁盘增长估算：**

| 运行规模 | 每轮均耗 | 总磁盘消耗 | HP 80G 可用空间占比 |
|---------|---------|-----------|-------------------|
| 10 轮（单次实验） | ~100 MB | ~1 GB（含环境） | 1.3% |
| 100 轮（1 周连续跑） | ~100 MB | ~10 GB + 5 GB 环境 = ~15 GB | 18.8% |
| 500 轮（1 月连续跑） | ~100 MB | ~50 GB + 5 GB = ~55 GB | 68.8% |
| 1000 轮（2 月连续跑） | ~100 MB | ~100 GB | ⚠️ 超限 |

**结论**：HP 80G 磁盘支持约 500-600 轮连续进化循环。需定期清理旧 trace 或配置自动轮转。10 轮/周的频率可以运行约 8-10 个月。

---

## 4. RD-Agent 在国内环境的可用性

### 4.1 DeepSeek API 稳定性

**结论：稳定可用 ✅**

- DeepSeek API（`api.deepseek.com`）在国内直连，无需代理
- 延迟：北京/上海地区 RTT 20-50ms
- DeepSeek-V4-Flash 定价：
  - 输入（缓存未命中）：1 元/百万 tokens
  - 输入（缓存命中）：0.02 元/百万 tokens
  - 输出：2 元/百万 tokens
- RD-Agent 论文报告单轮优化成本 < $10（约 70 元人民币），使用 DeepSeek 可进一步降低至 3-5 元/轮

**单轮成本估算（DeepSeek-V4-Flash）**：

| 步骤 | 预估 tokens（输入+输出） | 预估费用 |
|------|------------------------|---------|
| 假设生成（1-3 次 API） | ~10K 输入 + ~2K 输出 | ~0.02 元 |
| 代码生成（2-5 次 API） | ~20K 输入 + ~5K 输出 | ~0.05 元 |
| 反馈生成（1-2 次 API） | ~5K 输入 + ~1K 输出 | ~0.01 元 |
| Embedding（知识库 RAG） | ~5K tokens | ~0.005 元 |
| **单轮合计** | — | **约 0.05-0.15 元** |

> 注：以上为最乐观估算。实际中由于 prompt 较长（包含历史 trace、知识库上下文等），单轮可能在 0.5-3 元。即便按 3 元/轮，100 轮成本仅 300 元。

### 4.2 智谱 Embedding 稳定性

RD-Agent 需要 Embedding 模型做知识库 RAG。推荐配置：
- **SiliconFlow BAAI/bge-m3**（官方推荐）：免费额度大，稳定
- **智谱 embedding-3**：国内直连，0.5 元/百万 tokens

两者均国内直连，稳定可用。

### 4.3 GitHub 与 pip 网络瓶颈

**结论：一次性问题，不影响长期运行 ⚠️→✅**

| 操作 | 频率 | 网络问题 | 解决方案 |
|------|------|---------|---------|
| `pip install rdagent` | 一次性 | PyPI 国内可能慢 | 使用清华/阿里镜像 |
| `pip install pyqlib`（GitHub 源码） | 一次性 | GitHub clone 慢 | 使用 gitclone.com 或手动下载 |
| Qlib 数据下载 | 一次性 | Yahoo Finance 可能被墙 | 使用本地已有数据 |
| Conda 包安装 | 一次性 | conda 通道慢 | 配置清华 conda 镜像 |
| DeepSeek API 调用 | 每轮 | ✅ 国内直连无问题 | — |

**关键认识**：所有网络瓶颈都是**一次性安装问题**。一旦环境搭建完成，长期运行中只有 DeepSeek API 调用（国内直连），网络不再是瓶颈。

### 4.4 长期运行可维护性

| 维护项目 | 频率 | 难度 | 说明 |
|---------|------|------|------|
| 磁盘清理 | 每周 | ⭐ 低 | 清理旧 trace/workspace |
| Conda 环境更新 | 每月 | ⭐⭐ 中 | RD-Agent 版本升级 |
| 数据更新 | 每周/每月 | ⭐⭐ 中 | Qlib 数据增量更新 |
| 故障恢复 | 不确定 | ⭐⭐⭐ 中高 | 需要了解 RD-Agent 内部机制 |
| API 密钥续费 | 每月 | ⭐ 低 | DeepSeek 余额充值 |

**主要风险**：RD-Agent 的 Session pickle 机制在异常中断后可能损坏，需要手动清理 `__session__/` 目录重启。但 RD-Agent 支持 `--checkout` 断点续跑，降低了此风险。

---

## 5. 替代方案全面对比

### 5.1 五种替代方案详解

#### 方案 A：VPS 跑 RD-Agent（全云端）

**架构**：OpenClaw（VPS）→ RD-Agent（VPS）→ Qlib 回测（VPS）

**配置要求**：
- 最小配置：4 核 CPU / 8GB RAM / 50GB SSD（CSI300）
- 推荐配置：8 核 CPU / 16GB RAM / 100GB SSD（CSI500）
- 不需要 GPU（LightGBM CPU 即可）

**腾讯云 VPS 价格（2025-2026）**：
- 轻量 4 核 4G：79-188 元/年（促销新用户价）
- CVM 4 核 8G：约 800-1500 元/年
- CVM 8 核 16G：约 2000-3500 元/年

**优点**：
- 网络稳定，不受家庭网络影响
- 可选 GPU 实例（按需开启）
- 不占用 HP 资源
- 自动备份/快照

**缺点**：
- 需要持续付费（年费 200-3500 元）
- CSIALL 仍需更高配 VPS（16G+ 内存）
- 需要迁移 Qlib 数据到 VPS

#### 方案 B：本地跑简化版（Qlib + 手动因子循环）

**架构**：OpenClaw quant-compute Agent → SSH → HP 本地 Qlib 回测

**核心思路**：不使用 RD-Agent 的自动循环，而是由 OpenClaw 的 quant-compute Agent 手动驱动：
1. quant-compute 用 LLM 生成因子假设
2. 用 LLM 生成因子代码
3. SSH 到 HP 执行 `qrun` 回测
4. 解析结果，LLM 分析反馈
5. 人工或半自动决定下一步

**优点**：
- 实现简单（R-194 方案 A 的核心思路）
- 资源需求最低（只需 Qlib + Python，不需 RD-Agent 全栈）
- 可控性强，每步可审核
- 无额外成本

**缺点**：
- 失去 RD-Agent 的自动进化能力
- 人工干预多，效率低
- 无法 7x24 自动运行
- 知识管理和 trace 需要自行实现

#### 方案 C：云端按需跑（GPU 实例）

**架构**：按需启动云端 GPU/CPU 实例 → 运行 RD-Agent → 完成后销毁

**适用场景**：每月只需 1-2 次大批量因子进化

**成本估算**（AutoDL/阿里云抢占式）：
- CPU 实例（8核16G）：1-2 元/小时
- GPU 实例（T4 16G）：2-4 元/小时
- 每次运行 8 小时（约 20-50 轮循环）：16-32 元
- 每月 2 次：32-64 元/月

**优点**：
- 按需付费，无固定成本
- 可选强大配置（32G+ 内存跑 CSIALL）
- 灵活选择 CPU/GPU

**缺点**：
- 每次需要重新部署环境（或制作自定义镜像）
- 数据需要同步/上传
- 无法持续运行
- 运维复杂度高

#### 方案 D：混合模式（VPS 编排 + 本地回测）⭐ 推荐

**架构**：

```
┌──────────────────────────────────────────────────────────┐
│  腾讯云 VPS（OpenClaw 大本营）                             │
│  ├── main Agent（任务分发）                                │
│  ├── quant-compute Agent（LLM 调用 + 因子假设生成）        │
│  ├── research-lead Agent（审核 + 知识管理）                │
│  └── DeepSeek API 调用（低延迟）                          │
│         │ SSH / Zerotier                                   │
│         ▼                                                  │
│  HP 本地工作站（计算节点）                                  │
│  ├── Qlib 回测环境（Conda，CSI300 数据）                   │
│  ├── LightGBM 因子训练                                     │
│  └── 结果暂存 + 定期清理                                   │
│         │                                                  │
│         ▼ 回测结果（CSV/JSON）                             │
│  VPS 接收 → 分析 → 入库 → 通知                             │
└──────────────────────────────────────────────────────────┘
```

**核心思路**：
- VPS 负责"思考"：LLM 假设生成、代码生成、反馈分析（这些都是 API 调用，不吃本地资源）
- HP 负责"计算"：Qlib 回测执行（纯 CPU，不需要网络）
- 两者的分工完美匹配各自的优势

**优点**：
- 最大化利用现有资源（HP 免费 + VPS 已有）
- HP 只跑 Qlib 回测，资源压力大幅降低
- VPS 网络好，LLM API 调用无延迟
- 可以实现 R-194 方案 A（CLI 执行）的最简形态
- 成本最低（VPS 已有，HP 已有，只花 DeepSeek API 费用）

**缺点**：
- 需要 SSH 通道稳定（已通过 Zerotier 解决）
- 回测任务串行（HP 一次只能跑一个）
- HP 故障时无冗余

**实现复杂度**：⭐⭐（低，R-194 方案 A 早已规划好）

#### 方案 E：其他开源量化框架

如果放弃 Qlib+RD-Agent，是否有更轻量的替代？

| 框架 | 定位 | 轻量性 | AI 因子挖掘 | A股支持 | 适合 HP？ |
|------|------|--------|-----------|---------|----------|
| **Qlib + RD-Agent** | AI 量化研究平台 | 重（需 5G+ 环境） | ✅ 自动进化 | ✅ 原生 | ⚠️ 有条件 |
| **Backtrader** | 事件驱动回测 | ⭐ 极轻（纯 Python） | ❌ 需自建 | ⚠️ 需适配 | ✅ 完全适合 |
| **VectorBT** | 向量化极速回测 | ⭐ 轻 | ❌ 需自建 | ✅ | ✅ 完全适合 |
| **VnPy** | 全栈量化交易 | ⭐⭐ 中等 | ❌ 无 | ✅ 原生 CTP | ✅ 适合 |
| **Alphalens** | 因子分析工具 | ⭐ 极轻 | ❌ 无（仅分析） | ✅ | ✅ 完全适合 |
| **Zipline** | 事件驱动回测 | ⭐⭐ 中等 | ❌ 无 | ⚠️ 需适配 | ✅ 适合 |
| **BigQuant/聚宽** | 云端 AI 量化 | ⭐（云端零本地） | ✅ 内置 | ✅ | ✅ 无需本地资源 |

**关键分析**：

根据 R-187 的工具链全景评估，这些框架与 Qlib+RD-Agent **不是同一层级**的替代品：

- **Backtrader / VectorBT / VnPy** 是回测框架，不包含 AI 因子自动挖掘能力。用它们替代 Qlib+RD-Agent，等于放弃自动化因子进化，回到手动研究模式。
- **Alphalens** 仅做因子分析（IC 计算、分层回测），不包含回测引擎。
- **VnPy** 强在实盘交易（CTP 接口），弱在 AI 因子研究。如果未来需要实盘对接，VnPy 可作为补充。
- **云端平台（聚宽/BigQuant）** 可以完全绕过本地部署，但数据导出受限、定制化能力弱。

**结论**：如果目标是 **AI 驱动的自动因子进化**，目前没有比 Qlib+RD-Agent 更轻量的开源替代。如果只需 **手动回测**，Backtrader/VectorBT 更轻量且完全适合 HP。

### 5.2 五方案横向对比表

| 维度 | 方案 A（VPS 全跑） | 方案 B（本地简化） | 方案 C（云端按需） | 方案 D（混合模式）⭐ | 方案 E（其他框架） |
|------|:-:|:-:|:-:|:-:|:-:|
| **首年成本** | 200-3500 元 | 0 元 | 400-800 元 | **0-100 元** | 0 元 |
| **设置难度** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | **⭐⭐** | ⭐⭐ |
| **自动化程度** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | **⭐⭐⭐⭐** | ⭐ |
| **HP 资源压力** | 无 | 高 | 无 | **中（仅回测）** | 低 |
| **CSI300 支持** | ✅ | ✅ | ✅ | **✅** | ✅ |
| **CSIALL 支持** | ⚠️ 需高配 | ❌ | ✅ | **❌** | ❌ |
| **深度学习模型** | ⚠️ 需 GPU VPS | ❌ | ✅ | **❌** | ❌ |
| **7x24 自动运行** | ✅ | ❌ | ⚠️ | **✅** | ❌ |
| **网络稳定性** | ✅ | ⚠️ 家庭网络 | ✅ | **✅** | ⚠️ |
| **维护复杂度** | ⭐⭐ 中 | ⭐ 低 | ⭐⭐⭐ 高 | **⭐⭐ 中** | ⭐ 低 |
| **推荐指数** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | **⭐⭐⭐⭐⭐** | ⭐⭐ |

---

## 6. 结论与推荐路径

### 6.1 总体结论

**Qlib+RD-Agent 在 HP 本地部署：有条件适合**

具体条件如下：

| 条件 | 要求 | HP 现状 | 达标？ |
|------|------|---------|--------|
| 使用 Conda 模式（非 Docker） | `MODEL_CoSTEER_env_type=conda` | 已排查确认 | ✅ |
| 股票池限定 CSI300 | 内存 < 10GB | CSI300 峰值 ~9GB | ✅ |
| 不使用深度学习模型 | 仅 LightGBM/XGBoost | CPU 版可运行 | ✅ |
| 磁盘定期清理 | 每月清理旧 trace | 80G 可用 | ✅（需运维） |
| DeepSeek API 余额充足 | 每月 50-200 元 | 需充值 | ✅ |
| SSH 通道稳定 | VPS→HP Zerotier | 已配置 | ✅ |

**如果需要 CSIALL 或深度学习模型，HP 不适合，需要云端方案。**

### 6.2 推荐最优路径：方案 D（混合模式）

**第一阶段（立即启动，1-2 周）：方案 B → 方案 D 过渡**

1. 修复 HP 上的 RD-Agent Conda 配置（修正 `MODEL_CoSTEER_env_type`）
2. 手动跑通 1-3 轮 `rdagent fin_factor --loop_n 3`（CSI300）
3. 验证端到端流程：假设→代码→回测→反馈
4. 通过 OpenClaw quant-compute Agent SSH 触发执行（R-194 方案 A）

**第二阶段（2-4 周）：方案 D 稳定运行**

1. VPS 上的 quant-compute Agent 负责所有 LLM API 调用
2. HP 仅执行 Qlib 回测（通过 SSH 发送命令和接收结果）
3. 定时任务（Cron）每周自动启动 10-20 轮进化
4. 结果自动入库 + 微信通知

**第三阶段（可选，1-3 月后）：按需补充云端算力**

1. 如需 CSIALL 或深度学习模型，按需启动云端实例（方案 C）
2. 制作自定义镜像（含 RD-Agent 环境），5 分钟内启动
3. 每月成本控制在 50-100 元

### 6.3 不推荐立即做的事

- ❌ 不要在 HP 上使用 Docker 模式（5GB CUDA 镜像毫无意义）
- ❌ 不要尝试在 HP 上跑 CSIALL 全市场回测（会 OOM）
- ❌ 不要在 HP 上训练 LSTM/Transformer 模型（太慢）
- ❌ 不要购买高配 VPS 专门跑 RD-Agent（方案 A 性价比不如方案 D）
- ❌ 不要急于切换到其他框架（方案 E 放弃了 AI 自动进化能力）

---

## 7. 时间成本与金钱成本估算

### 7.1 时间成本

| 阶段 | 任务 | 预估时间 | 前置条件 |
|------|------|---------|---------|
| **环境修复** | 修复 .env 配置 + 创建 rdagent4qlib 环境 | 2-4 小时 | HP 可 SSH |
| **首次验证** | 跑通 1 轮 fin_factor | 30-60 分钟 | 环境就绪 |
| **3 轮进化** | 完整跑通 3 轮循环 | 1-3 小时 | 首轮成功 |
| **OpenClaw 集成** | quant-compute SSH 触发 + 结果回传 | 4-8 小时 | 3 轮成功 |
| **Cron 自动化** | 定时任务 + 通知 + 清理脚本 | 4-8 小时 | OpenClaw 集成 |
| **总计** | MVP 到自动化运行 | **约 2-3 周**（含调试 buffer） | — |

### 7.2 金钱成本

| 项目 | 单次成本 | 月度成本 | 年度成本 | 说明 |
|------|---------|---------|---------|------|
| DeepSeek API | — | 50-200 元 | 600-2400 元 | 按每周 50 轮估算 |
| SiliconFlow Embedding | — | <10 元 | <120 元 | 知识库 RAG |
| VPS（已有） | — | 0（已付费） | 0 | OpenClaw 大本营 |
| HP（已有） | — | 0（电费忽略） | 0 | 计算节点 |
| 云端按需实例（可选） | 16-32 元 | 32-64 元 | 384-768 元 | 仅需 CSIALL 时 |
| **年度总计** | — | **50-200 元** | **600-2400 元** | 不含可选云端 |

> 对比：如购买专业量化终端（Wind/iFinD），年费 2-20 万元。RD-Agent 方案的成本不到其 1/10。

---

## 8. 实施建议与下一步

### 8.1 立即可执行的修复步骤

根据 RD-Agent Docker 排查报告的结论，修复 HP 环境的精确步骤：

```bash
# 1. 修复环境变量名（最关键的修复）
cd ~/quant/rdagent
sed -i '/MODEL_CODER_ENV_TYPE/d' .env
echo 'MODEL_CoSTEER_env_type=conda' >> .env

# 2. 创建 rdagent4qlib conda 环境（CPU 版）
conda create -y -n rdagent4qlib python=3.10
conda run -n rdagent4qlib pip install --upgrade pip cython
conda run -n rdagent4qlib pip install \
  -i https://pypi.tuna.tsinghua.edu.cn/simple \
  pyqlib catboost xgboost tables
conda run -n rdagent4qlib pip install \
  torch --index-url https://download.pytorch.org/whl/cpu

# 3. 验证环境
conda run -n rdagent4qlib python -c \
  "import qlib, torch, catboost; print('All OK')"

# 4. 启动测试（1 轮验证）
cd ~/quant/rdagent
rdagent fin_factor --loop-n 1 --no-checkout 2>&1 | tee test_run.log
```

### 8.2 OpenClaw 集成的最小实现

R-194 方案 A 的核心命令模板：

```bash
# quant-compute Agent 通过 SSH 触发 RD-Agent
ssh hp-workstation 'cd ~/quant/rdagent && \
  conda run -n rdagent fin_factor \
    --loop_n 10 \
    --all_duration 8h \
    --checkout \
  2>&1 | tee logs/rdagent_$(date +%Y%m%d_%H%M%S).log'
```

### 8.3 磁盘清理 Cron

```bash
# 每周清理 30 天前的 trace 和 workspace
# crontab -e
0 3 * * 0 find ~/quant/rdagent/git_ignore_folder/ -type f -mtime +30 -delete
0 3 * * 0 find ~/quant/rdagent/__session__/ -type f -mtime +30 -delete
```

### 8.4 关键风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| HP 硬件故障 | 中 | 高（计算中断） | 重要结果及时回传 VPS；考虑方案 C 作为 fallback |
| DeepSeek API 涨价 | 高 | 中 | RD-Agent 单轮成本极低（<3 元），涨价影响有限 |
| RD-Agent 版本升级破坏兼容 | 低 | 中 | 锁定版本 `pip install rdagent==X.Y.Z` |
| CSI300 因子饱和 | 中 | 低 | 适时扩展到 CSI500 或行业中性化因子 |
| Qlib 数据过时 | 低 | 中 | 配置定时数据更新（每周） |

---

## 附录 A：HP 与各方案的适用性速查

```
HP 适合什么？
├── ✅ Qlib CSI300 回测（LightGBM）
├── ✅ 因子计算和 IC 分析
├── ✅ RD-Agent Conda 模式（CSI300 + LightGBM）
├── ⚠️ Qlib CSI500 回测（紧张但可行）
├── ❌ Qlib CSIALL 回测（内存不足）
├── ❌ 深度学习模型训练（LSTM/Transformer，CPU 太慢）
├── ❌ RD-Agent Docker 模式（5GB CUDA 镜像无意义）
└── ❌ 大规模参数搜索（CPU 性能限制）
```

## 附录 B：决策树

```
是否需要 AI 自动因子进化？
├── 否 → 方案 B（本地 Qlib + 手动循环）或方案 E（Backtrader/VectorBT）
└── 是 → 是否需要 CSIALL 或深度学习模型？
    ├── 是 → 方案 C（云端按需）+ 方案 D（混合）
    └── 否 → 方案 D（混合模式：VPS 编排 + HP 本地回测）⭐
```

## 附录 C：引用的已有调研结论

### 引用 R-194（OpenClaw 与 RD-Agent 结合方案）
- RD-Agent 的 Flask 后端提供完整 HTTP API，可作为常驻服务（方案 B 的技术基础）
- RD-Agent 支持通过环境变量 `MODEL_CoSTEER_env_type` 切换 Docker/Conda 模式
- 推荐方案 A（CLI 执行）作为 MVP，1-2 天可跑通——本报告的方案 D 正是基于此
- RD-Agent 的单轮成本 < $10（论文数据），使用 DeepSeek 可进一步降低

### 引用 R-187（AI 时代个人量化投资全景）
- Qlib 被评为 ⭐⭐⭐⭐⭐ AI 量化平台，内置 Alpha158/Alpha360 因子库
- 个人投资者最适合的方向是多因子选股策略（月度调仓，30-50 只持仓）
- A 股短期反转因子 IC 0.04-0.06，是最稳定的有效因子
- AI/LLM 增强可贡献年化 3-10 个百分点的 alpha 增量
- 过拟合是个人量化的头号杀手——RD-Agent 的自动进化可能加剧过拟合风险，需严格的样本外验证

### 引用 RD-Agent Docker 排查报告
- 根因 1：Docker 基础镜像 `pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime` 压缩后 5GB+
- 根因 2：环境变量名错误（`MODEL_CODER_ENV_TYPE` vs 正确的 `MODEL_CoSTEER_env_type`）
- 根因 3：HP 无 GPU 但 Docker 默认启用 GPU 配置
- 修复方案 A（推荐）：切换到 Conda 模式，安装 CPU 版 PyTorch（仅 ~200MB）

---

> **报告作者**: research-lead Agent  
> **审核状态**: 待审核  
> **最后更新**: 2026-08-10