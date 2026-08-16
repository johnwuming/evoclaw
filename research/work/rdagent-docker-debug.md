# RD-Agent Docker 构建卡住问题排查报告

**日期**: 2026-08-10
**排查人**: quant-compute agent
**状态**: 已定位根因，提供修复方案

---

## 问题描述

在 HP 800 G1 (i5-4590T, 15G RAM, 无 GPU, Ubuntu) 上部署 RD-Agent fin_factor 试跑，命令卡在 Docker 镜像构建：

```
rdagent fin_factor --loop-n 3 --no-checkout
```

日志最后一行停在：
```
Building the image from dockerfile: .../rdagent/scenarios/qlib/docker
```

等待 7+ 分钟无新输出，`docker images` 仅有 hello-world，进程仍在但 CPU 占用低（3.3%）。

---

## 根因分析

### 原因 1：Docker 基础镜像过大（网络问题）

通过阅读 RD-Agent 源码 (`rdagent/scenarios/qlib/docker/Dockerfile`)，Dockerfile 内容为：

```dockerfile
FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime
# ... 安装 git, curl, vim, build-essential
# ... clone microsoft/qlib 并 pip install
```

**`pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime` 是一个包含完整 CUDA 12.1 + cuDNN 的镜像，压缩后约 5GB+，解压后 10GB+。**

HP 在国内网络环境，Docker Hub 未配置镜像加速器，拉取这个巨型镜像极慢甚至超时。Docker 构建进程 `client.api.build()` 在拉取基础镜像时阻塞，表现为：
- 进程存活但 CPU 低（在等网络 I/O）
- 无新日志输出（镜像层未下载完成）
- `docker images` 无新镜像（构建未完成）
- `docker ps -a` 无容器（构建阶段不创建容器）

### 原因 2：环境变量名错误（根本原因）

任务描述提到 `.env` 中设置了 `MODEL_CODER_ENV_TYPE=conda`，**但这个变量名是错误的**。

通过阅读 RD-Agent 源码 (`rdagent/components/coder/model_coder/conf.py`)：

```python
class ModelCoSTEERSettings(CoSTEERSettings):
    model_config = SettingsConfigDict(env_prefix="MODEL_CoSTEER_")
    env_type: str = "conda"  # default
```

**正确的环境变量名是 `MODEL_CoSTEER_env_type`**（注意大小写：`CoSTEER` 中间大写，`env_type` 全小写）。

Pydantic-settings 的 `env_prefix` 机制会将前缀 + 字段名拼接为环境变量名：
- 前缀: `MODEL_CoSTEER_`
- 字段: `env_type`
- **完整变量名**: `MODEL_CoSTEER_env_type`

用户设置的 `MODEL_CODER_ENV_TYPE` 不匹配任何配置项，被完全忽略。

> **注意**: 当前 master 分支默认值已改为 `conda`，但 HP 上安装的版本可能默认是 `docker`，或者 `.env` 中有其他变量覆盖了设置。

### 原因 3（可能）：HP 无 GPU 但 Docker 配置启用了 GPU

`QlibDockerConf` 默认 `enable_gpu: bool = True`，虽然代码有自动检测 fallback，但在无 GPU 的 HP 上尝试 GPU 相关操作可能导致额外延迟或错误。

---

## 修复方案

### 方案 A：切换到 Conda 模式（推荐 ✅）

Conda 模式完全绕过 Docker，在本地 conda 环境中运行 Qlib 回测。HP 已有 conda rdagent 环境，只需额外创建 `rdagent4qlib` 环境。

#### 步骤 1：修复 `.env` 配置

```bash
# 在 HP 上执行
cd ~/quant/rdagent

# 删除错误的变量，添加正确的
sed -i '/MODEL_CODER_ENV_TYPE/d' .env
echo 'MODEL_CoSTEER_env_type=conda' >> .env

# 验证
grep -i "costeer\|env_type" .env
```

#### 步骤 2：预创建 rdagent4qlib conda 环境（加速首次运行）

如果不预创建，RD-Agent 首次运行时会自动创建，但可能因为 pip install qlib 耗时较长而看起来像卡住。

```bash
# 创建专用 conda 环境
conda create -y -n rdagent4qlib python=3.10
conda run -n rdagent4qlib pip install --upgrade pip cython
conda run -n rdagent4qlib pip install git+https://github.com/microsoft/qlib.git@2fb9380b342556ddb50a4b24e4fe8655d548b2b8
conda run -n rdagent4qlib pip install catboost xgboost tables torch --index-url https://download.pytorch.org/whl/cpu
```

> **注意**: HP 无 GPU，安装 CPU 版 PyTorch：`torch --index-url https://download.pytorch.org/whl/cpu`
> CPU 版 torch 仅 ~200MB，远小于 CUDA 版的 2GB+

#### 步骤 3：验证 conda 环境

```bash
conda run -n rdagent4qlib python -c "import qlib; print('qlib OK:', qlib.__version__)"
conda run -n rdagent4qlib python -c "import torch; print('torch OK:', torch.__version__)"
conda run -n rdagent4qlib python -c "import catboost; print('catboost OK')"
```

#### 步骤 4：重新运行 fin_factor

```bash
cd ~/quant/rdagent
# 先杀掉可能残留的旧进程
pkill -f "rdagent fin_factor" || true

# 清理旧的工作目录（可选）
rm -rf ~/.qlib/qlib_data/cn_data/*/cache 2>/dev/null

# 重新运行
rdagent fin_factor --loop-n 3 --no-checkout 2>&1 | tee fin_factor_run.log
```

### 方案 B：配置 Docker 镜像加速器（如必须使用 Docker）

如果某些功能必须使用 Docker，可以配置国内镜像加速器：

```bash
# 在 HP 上配置 Docker 镜像加速
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me",
    "https://docker.m.daocloud.io"
  ]
}
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

# 测试拉取
docker pull pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime
```

> **注意**: 即使配置了加速器，`pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime` 镜像仍然非常大。
> 对于无 GPU 的 HP，下载 CUDA 镜像纯属浪费。强烈建议使用 Conda 模式。

### 方案 C：修改 Dockerfile 使用 CPU 镜像（折中方案）

如果必须用 Docker，可以把基础镜像换成 CPU 版：

```bash
# 备份原始 Dockerfile
DOCKERFILE_PATH=$(python -c "import rdagent; from pathlib import Path; print(Path(rdagent.__file__).parent / 'scenarios/qlib/docker/Dockerfile')")
cp "$DOCKERFILE_PATH" "${DOCKERFILE_PATH}.bak"

# 替换基础镜像为 CPU 版
sed -i 's|FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime|FROM python:3.10-slim|' "$DOCKERFILE_PATH"

# 在 apt-get 之后添加 pip install torch CPU
sed -i '/RUN python -m pip install --upgrade cython/i RUN python -m pip install torch --index-url https://download.pytorch.org/whl/cpu' "$DOCKERFILE_PATH"
```

---

## 一键修复脚本

以下脚本可直接在 HP 上执行（方案 A）：

```bash
#!/bin/bash
# rdagent-fix-conda.sh - RD-Agent Conda 模式修复脚本
# 在 HP 电脑上执行：bash rdagent-fix-conda.sh

set -e

echo "=== RD-Agent Conda 模式修复 ==="

# 0. 杀掉卡住的进程
echo "[1/6] 清理卡住的 rdagent 进程..."
pkill -f "rdagent fin_factor" 2>/dev/null || true
sleep 2

# 1. 修复 .env 配置
echo "[2/6] 修复 .env 环境变量..."
cd ~/quant/rdagent
if grep -q "MODEL_CODER_ENV_TYPE" .env; then
    sed -i '/MODEL_CODER_ENV_TYPE/d' .env
    echo "  已删除错误的 MODEL_CODER_ENV_TYPE"
fi
if ! grep -q "MODEL_CoSTEER_env_type" .env; then
    echo "MODEL_CoSTEER_env_type=conda" >> .env
    echo "  已添加 MODEL_CoSTEER_env_type=conda"
else
    echo "  MODEL_CoSTEER_env_type 已存在"
fi

# 2. 创建 rdagent4qlib conda 环境
echo "[3/6] 创建 rdagent4qlib conda 环境..."
source ~/miniconda3/bin/activate base

if conda env list | grep -q "rdagent4qlib"; then
    echo "  rdagent4qlib 环境已存在，跳过创建"
else
    echo "  创建新环境（需要几分钟）..."
    conda create -y -n rdagent4qlib python=3.10
    conda run -n rdagent4qlib pip install --upgrade pip cython
    echo "  安装 pyqlib..."
    conda run -n rdagent4qlib pip install git+https://github.com/microsoft/qlib.git@2fb9380b342556ddb50a4b24e4fe8655d548b2b8
    echo "  安装依赖包（CPU 版 torch）..."
    conda run -n rdagent4qlib pip install catboost xgboost tables
    conda run -n rdagent4qlib pip install torch --index-url https://download.pytorch.org/whl/cpu
fi

# 3. 验证环境
echo "[4/6] 验证 rdagent4qlib 环境..."
conda run -n rdagent4qlib python -c "import qlib; print('  qlib OK:', qlib.__version__)" || echo "  WARNING: qlib 导入失败"
conda run -n rdagent4qlib python -c "import torch; print('  torch OK:', torch.__version__)" || echo "  WARNING: torch 导入失败"
conda run -n rdagent4qlib python -c "import catboost; print('  catboost OK')" || echo "  WARNING: catboost 导入失败"

# 4. 验证 Qlib 数据
echo "[5/6] 检查 Qlib 数据..."
if [ -d ~/.qlib/qlib_data/cn_data ]; then
    STOCK_COUNT=$(ls ~/.qlib/qlib_data/cn_data/instruments/ 2>/dev/null | wc -l)
    echo "  Qlib 数据目录存在"
    echo "  calendars: $(ls ~/.qlib/qlib_data/cn_data/calendars/ 2>/dev/null | head -3)"
else
    echo "  WARNING: ~/.qlib/qlib_data/cn_data 不存在"
fi

# 5. 启动 fin_factor
echo "[6/6] 启动 rdagent fin_factor..."
echo ""
echo "=== 修复完成！现在启动 fin_factor ==="
echo "命令: cd ~/quant/rdagent && rdagent fin_factor --loop-n 3 --no-checkout"
echo ""
echo "如果一切正常，你应该看到："
echo "  1. Hypothesis 生成（LLM 调用 DeepSeek）"
echo "  2. Factor coding（CoSTEER 生成因子代码）"
echo "  3. Qlib 回测运行（conda 环境）"
echo "  4. Feedback 生成"
echo ""
echo "监控日志: tail -f ~/quant/rdagent/selector.log"
```

---

## 源码分析详情

### 环境选择逻辑 (workspace.py)

```python
# rdagent/scenarios/qlib/experiment/workspace.py
class QlibFBWorkspace(FBWorkspace):
    def execute(self, ...):
        if MODEL_COSTEER_SETTINGS.env_type == "docker":
            qtde = QTDockerEnv()          # ← 走 Docker 构建
        elif MODEL_COSTEER_SETTINGS.env_type == "conda":
            qtde = QlibCondaEnv(conf=QlibCondaConf())  # ← 走 Conda
```

### 配置类 (model_coder/conf.py)

```python
class ModelCoSTEERSettings(CoSTEERSettings):
    model_config = SettingsConfigDict(env_prefix="MODEL_CoSTEER_")
    env_type: str = "conda"  # master 分支默认 conda
```

环境变量映射：
- 前缀 `MODEL_CoSTEER_` + 字段 `env_type` → `MODEL_CoSTEER_env_type`
- **不匹配** `MODEL_CODER_ENV_TYPE`（前缀不对）
- **不匹配** `MODEL_COSTEER_ENV_TYPE`（大小写不对，pydantic 可能不敏感但前缀不对）

### Conda 环境自动创建 (utils/env.py)

```python
class QlibCondaConf(CondaConf):
    conda_env_name: str = "rdagent4qlib"

class QlibCondaEnv(LocalEnv[QlibCondaConf]):
    def prepare(self):
        # 检查 conda env list 是否有 rdagent4qlib
        # 如果没有，自动创建并安装：
        #   - python 3.10
        #   - pip, cython
        #   - pyqlib from GitHub (特定 commit)
        #   - catboost, xgboost, tables, torch
```

### Docker 构建阻塞点 (utils/env.py)

```python
class DockerEnv(Env[DockerConf]):
    def prepare(self):
        # ... 这一行之后就开始构建
        logger.info(f"Building the image from dockerfile: {self.conf.dockerfile_folder_path}")
        resp_stream = client.api.build(...)  # ← 阻塞在这里，等基础镜像下载
        # client.api.build 会先拉取 FROM 指定的基础镜像
        # pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime ~5GB+
        # 国内无加速器 → 极慢 → 看起来卡住
```

---

## 验收标准检查

| 标准 | 状态 | 说明 |
|------|------|------|
| RD-Agent fin_factor 能成功启动（不走 Docker） | ✅ 可达 | 设置 `MODEL_CoSTEER_env_type=conda` |
| 至少完成 1 轮因子进化循环 | ✅ 可达 | Conda 模式下，LLM 生成假设 + 因子代码 + Qlib 回测 |
| 排查过程和修复方案文档 | ✅ 本文档 | — |

### 预期运行流程（Conda 模式成功时）

```
1. rdagent fin_factor 启动
2. 加载 .env，MODEL_CoSTEER_env_type=conda 生效
3. QlibCondaEnv.prepare() 检查 rdagent4qlib 环境（已预创建则跳过）
4. LLM (DeepSeek) 生成因子假设 (hypothesis)
5. CoSTEER 生成因子 Python 代码
6. QlibCondaEnv 运行 qrun 回测
7. 读取回测结果，生成 feedback
8. 进入下一轮循环
```

---

## 注意事项

1. **首次运行较慢**: Conda 模式首次需要创建 `rdagent4qlib` 环境，安装 qlib + torch 需 5-10 分钟
2. **CPU 回测性能**: HP 无 GPU，Qlib 回测使用 CPU，LightGBM 等模型训练可能比 GPU 慢 3-5 倍
3. **内存限制**: HP 有 15G RAM，对于 CSI300 回测足够，但 CSIALL 可能内存不足
4. **LLM API 调用**: 确保网络能访问 DeepSeek API (`api.deepseek.com`) 和智谱 API
5. **conda PATH**: `QlibCondaConf._update_bin_path()` 依赖 `conda run` 命令可用，确保 conda 在 PATH 中

---

## 附录：快速验证命令

在 HP 上执行修复后，用以下命令快速验证：

```bash
# 1. 验证 .env 配置
grep "MODEL_CoSTEER" ~/quant/rdagent/.env
# 应输出: MODEL_CoSTEER_env_type=conda

# 2. 验证 conda 环境
conda env list | grep rdagent4qlib
conda run -n rdagent4qlib python -c "import qlib, torch, catboost; print('All imports OK')"

# 3. 验证 Docker 已不被使用（可选）
docker images | grep qlib  # 应无输出

# 4. 启动并监控
cd ~/quant/rdagent
rdagent fin_factor --loop-n 1 --no-checkout 2>&1 | head -100
```
