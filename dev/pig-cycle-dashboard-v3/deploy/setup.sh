#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== 猪周期看板 一键部署 ==="

# 1. Install Python dependencies
echo "[1/5] 安装 Python 依赖..."
pip install -r requirements.txt -q

# 2. First data collection
echo "[2/5] 首次数据采集..."
if [ -f collector.py ]; then
    python3 collector.py
else
    echo "  跳过：collector.py 不存在"
fi

# 3. Install systemd service
echo "[3/5] 安装 systemd 服务..."
cp "$PROJECT_DIR/deploy/pig-dashboard.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable pig-dashboard
systemctl restart pig-dashboard
echo "  服务已启动并设为开机自启"

# 4. Install Nginx config
echo "[4/5] 安装 Nginx 配置..."
if command -v nginx &>/dev/null; then
    cp "$PROJECT_DIR/deploy/pig-dashboard.nginx" /etc/nginx/sites-available/pig-dashboard
    ln -sf /etc/nginx/sites-available/pig-dashboard /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    echo "  Nginx 配置已安装并重载"
else
    echo "  跳过：Nginx 未安装，服务仅通过 8765 端口访问"
fi

# 5. Verify
echo "[5/5] 验证..."
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8765/api/overview" || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  API 验证通过 ✓"
else
    echo "  API 验证失败 ($HTTP_CODE)，请检查日志: journalctl -u pig-dashboard -f"
fi

echo ""
echo "=== 部署完成 ==="
echo "  本地访问: http://127.0.0.1:8765"
echo "  查看日志: journalctl -u pig-dashboard -f"
