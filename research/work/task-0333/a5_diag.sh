#!/usr/bin/env bash
# a5_diag.sh - robust import/startup diagnostic for a5_runner.py (writes to file, survives SSH drop)
{
echo "=== A5 DIAG $(date +%H:%M:%S) ==="
cd /home/noname/quant-evolve || { echo "CD_FAIL"; exit 1; }
QPY=/home/noname/miniconda3/envs/quant/bin/python
echo "--- step1: q4b import ---"
timeout 60 $QPY -c "
import sys
sys.path.insert(0, '/home/noname/quant-evolve/scripts')
sys.path.insert(0, '/home/noname/quant-evolve')
import importlib.util
spec = importlib.util.spec_from_file_location('q4b', 'scripts/q4b_run_BC.py')
q4b = importlib.util.module_from_spec(spec); sys.argv=['x','none']
spec.loader.exec_module(q4b)
print('Q4B_OK')
" 2>&1
echo "--- step2: engine import ---"
timeout 60 $QPY -c "
import sys
sys.path.insert(0, '/home/noname/quant-evolve/scripts')
sys.path.insert(0, '/home/noname/quant-evolve')
import backtest_dividend_quality_iter as engine
print('ENGINE_OK')
from audit_lock import AUDIT_LOCK_END
print('AUDIT_OK', AUDIT_LOCK_END)
" 2>&1
echo "--- step3: macro timing import ---"
timeout 60 $QPY -c "
import sys
sys.path.insert(0, '/home/noname/quant-evolve/scripts')
sys.path.insert(0, '/home/noname/quant-evolve')
import macro_timing_layer_iter4 as mtl4
print('MTL_OK')
" 2>&1
echo "--- step4: a5_runner syntax ---"
timeout 30 $QPY -c "import ast; ast.parse(open('/tmp/a5_runner.py').read()); print('SYNTAX_OK')" 2>&1
echo "=== A5_DIAG_DONE ==="
} > /tmp/a5_diag.log 2>&1
