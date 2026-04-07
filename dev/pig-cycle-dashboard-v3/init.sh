#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== 猪周期数据看板 v3 冒烟测试 ==="

# 1. 安装依赖
echo "[1/5] 安装依赖..."
pip install -q -r requirements.txt

# 2. 停止已有进程
echo "[2/5] 停止已有进程..."
lsof -ti:8050 | xargs kill -9 2>/dev/null || true

# 3. 启动应用
echo "[3/5] 启动应用..."
python app.py &
APP_PID=$!

# 4. 等待
echo "[4/5] 等待服务启动 (5s)..."
sleep 5

# 5. 检测
echo "[5/5] 检测 http://127.0.0.1:8050 ..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8050 || echo "000")

# 停止
kill $APP_PID 2>/dev/null || true
lsof -ti:8050 | xargs kill -9 2>/dev/null || true

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "=== PASS (HTTP $HTTP_CODE) ==="
    exit 0
else
    echo "=== FAIL (HTTP $HTTP_CODE) ==="
    exit 1
fi
