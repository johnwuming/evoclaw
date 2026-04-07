#!/bin/bash
cd /root/.openclaw/workspace-dev/pig-cycle-dashboard-v3
lsof -ti:8050 | xargs kill -9 2>/dev/null
sleep 1
python3 app.py &
sleep 6
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8050/
