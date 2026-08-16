#!/usr/bin/env bash
# a5_closeout_retry.sh - 运行 closeout, 遇 segfault 自动重试 (HP env scipy 间歇性损坏)
LOG=/tmp/a5_closeout_run.log
QPY=/home/noname/miniconda3/envs/quant/bin/python
cd /home/noname/quant-evolve || exit 1
for i in 1 2 3 4 5; do
  echo "=== closeout attempt $i $(date +%H:%M:%S) ===" >> $LOG
  $QPY /tmp/a5_closeout.py >> $LOG 2>&1
  RC=$?
  echo "attempt $i rc=$RC" >> $LOG
  if [ $RC -eq 0 ]; then
    echo "CLOSEOUT_OK" >> $LOG
    exit 0
  fi
  sleep 5
done
echo "CLOSEOUT_ALL_FAIL" >> $LOG
exit 1
