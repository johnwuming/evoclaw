#!/bin/bash
# rdagent-fix-conda.sh - RD-Agent Conda 模式修复脚本
# 在 HP 电脑上执行：bash rdagent-fix-conda.sh
# 用法：sshpass -p '123456' ssh noname@10.12.192.174 'bash -s' < rdagent-fix-conda.sh

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
