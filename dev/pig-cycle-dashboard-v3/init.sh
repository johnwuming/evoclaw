#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== 猪周期看板 冒烟测试 ==="

# 1. Python 依赖检查
echo "[1/5] 检查 Python 依赖..."
python3 -c "import fastapi; import akshare; import uvicorn" 2>&1 || { echo "FAIL: Python 依赖缺失"; exit 1; }
echo "  OK"

# 2. FastAPI 服务启动测试（后台运行）
echo "[2/5] 启动 FastAPI 服务..."
uvicorn app:app --host 127.0.0.1 --port 8765 &
API_PID=$!
sleep 3

cleanup() { kill $API_PID 2>/dev/null || true; }
trap cleanup EXIT

# Verify service is running
if ! kill -0 $API_PID 2>/dev/null; then
    echo "FAIL: 服务启动失败"
    exit 1
fi
echo "  OK (PID=$API_PID)"

# 3. API 端点测试
echo "[3/5] 测试 API 端点..."
ENDPOINTS=(
    "/api/overview"
    "/api/price?range=1y"
    "/api/price?range=3y"
    "/api/price?range=5y"
    "/api/price?range=all"
    "/api/cycle-compare"
    "/api/seasonality"
    "/api/details?limit=5"
    "/api/profit?range=1y"
    "/api/cost?range=1y"
)
FAIL=0
for endpoint in "${ENDPOINTS[@]}"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8765${endpoint}" || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  $endpoint → $HTTP_CODE OK"
    else
        echo "  $endpoint → $HTTP_CODE FAIL"
        FAIL=1
    fi
done

if [ "$FAIL" = "1" ]; then
    echo "FAIL: 部分 API 端点测试未通过"
    exit 1
fi

# 4. 静态页面测试
echo "[4/5] 测试静态页面..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8765/" || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  / → $HTTP_CODE OK"
else
    echo "  / → $HTTP_CODE FAIL"
    exit 1
fi

# 5. 静态资源测试
echo "[5/5] 测试静态资源..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8765/static/index.html" || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  /static/index.html → $HTTP_CODE OK"
else
    echo "  /static/index.html → $HTTP_CODE FAIL"
    exit 1
fi

echo ""
echo "=== 冒烟测试全部通过 ==="
