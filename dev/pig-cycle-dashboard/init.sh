#!/usr/bin/env bash
# 冒烟测试 — 猪周期数据看板
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Smoke Test ==="

# 1. Python import
python3 -c "from app import app; print('OK: app imports')"

# 2. DB init
python3 -c "from db import init_db; init_db(); print('OK: db init')"

# 3. Data collection
python3 -c "from collector import collect_daily, collect_weekly; collect_daily(); collect_weekly(); print('OK: data collection')"

# 4. Check data
python3 -c "
from db import get_conn
import pandas as pd
d = pd.read_sql('SELECT count(*) as c FROM daily_prices WHERE hog_price IS NOT NULL', get_conn())
assert d.iloc[0,0] > 0, 'no daily hog_price data'
w = pd.read_sql('SELECT count(*) as c FROM weekly_indicators', get_conn())
assert w.iloc[0,0] > 0, 'no weekly data'
print('OK: data validation')
"

# 5. App can build layout
python3 -c "
from app import app, render_tab
html = render_tab('tab-dash', None, None)
assert html is not None
print('OK: render tab')
"

echo "=== All smoke tests passed ==="
