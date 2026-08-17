#!/bin/bash
# Push a7c deliverables to HP results/ via HTTP API (SSH throttled)
KEY=$(cat /root/.openclaw/workspace-quant/scripts/.hp-api-key)
DIR=/root/.openclaw/workspace/shared/results/work/task-0341-out
for f in a7c-dynamic-ic-table.md a7c-dynamic-ic-table.csv a7c-dynamic-ic-table.json a7c-dynamic-ic-report.md a7c-iteration-report.md a7c-rolling-ic-series.json; do
  B64=$(base64 -w0 "$DIR/$f")
  CMD="echo $B64 | base64 -d > ~/quant-evolve/results/$f && echo OK_$f \$(wc -c < ~/quant-evolve/results/$f)"
  RESP=$(timeout 60 curl -s -m 55 -H "X-API-Key: $KEY" "http://10.12.192.174:8060/run" -H "Content-Type: application/json" -d "{\"command\":\"$CMD\"}" | head -c 500)
  echo "== $f: $RESP"
done
