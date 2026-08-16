#!/usr/bin/env bash
# a5_boot.sh - import test + fully-detached A5 screen launch (survives SSH drop)
STATUS=/tmp/a5_status.log
echo "BOOT_START $(date +%H:%M:%S)" > $STATUS
QPY=/home/noname/miniconda3/envs/quant/bin/python
cd /home/noname/quant-evolve || { echo "CD_FAIL" >> $STATUS; exit 1; }
echo "--- import test ---" >> $STATUS
timeout 90 $QPY -c "
import sys
sys.path.insert(0,'/home/noname/quant-evolve/scripts')
sys.path.insert(0,'/home/noname/quant-evolve')
import importlib.util
spec=importlib.util.spec_from_file_location('q4b','scripts/q4b_run_BC.py')
q4b=importlib.util.module_from_spec(spec); sys.argv=['x','none']
spec.loader.exec_module(q4b)
import backtest_dividend_quality_iter as engine
from audit_lock import AUDIT_LOCK_END
print('IMPORTS_OK')
" >> $STATUS 2>&1
if ! grep -q IMPORTS_OK $STATUS; then
  echo "IMPORT_FAIL" >> $STATUS
  exit 1
fi
# detached relaunch of screen
setsid nohup $QPY /tmp/a5_runner.py screen > /tmp/a5_screen.log 2>&1 < /dev/null &
echo "SCREEN_PID $!" >> $STATUS
echo "BOOT_DONE $(date +%H:%M:%S)" >> $STATUS
