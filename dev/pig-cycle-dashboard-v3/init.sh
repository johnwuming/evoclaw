#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== 猪周期看板 冒烟测试 ==="

# 1. Python 依赖检查
echo "[1/4] 检查 Python 依赖..."
python3 -c "import fastapi; import akshare; import uvicorn" 2>&1 || { echo "FAIL: Python 依赖缺失"; exit 1; }
echo "OK"

# 2. FastAPI 服务启动测试（后台运行）
echo "[2/4] 启动 FastAPI 服务..."
uvicorn app:app --host 127.0.0.1 --port 8765 &
API_PID=$!
sleep 3

# 3. API 端点测试
echo "[3/4] 测试 API 端点..."
for endpoint in "/api/overview" "/api/price?range=1y" "/api/profit?range=1y"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8765${endpoint}" || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  $endpoint → $HTTP_CODE OK"
    else
        echo "  $endpoint → $HTTP_CODE FAIL"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
done

# 4. 静态页面测试
echo "[4/4] 测试静态页面..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8765/" || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  / → $HTTP_CODE OK"
else
    echo "  / → $HTTP_CODE FAIL"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

kill $API_PID 2>/dev/null || true
echo ""
echo "=== 冒烟测试通过 ==="
