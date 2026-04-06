#!/usr/bin/env python3
"""安装脚本 — 安装依赖 + 初始化数据库"""
import subprocess, sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
print("[✓] 依赖安装完成")

from db import init_db
init_db()
print("[✓] 数据库初始化完成")

from collector import collect_daily, collect_weekly
print("[...] 正在采集数据...")
collect_daily()
collect_weekly()
print("[✓] 数据采集完成")
print("\n启动: gunicorn --bind 127.0.0.1:8050 --workers 1 --timeout 120 app:server")
