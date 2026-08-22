#!/usr/bin/env python3
# G5 容量门数据补采: bond_zh_hs_cov_daily 仅对入选过的券补采 (R-285 冻结口径)
# 限频 sleep>=0.5s, 重试<=2, 全局时限 200s
import pandas as pd, json, os, time, sys

OUT = "/tmp/r286_daily"
os.makedirs(OUT, exist_ok=True)
TRADES = "/root/.openclaw/workspace/work/r286/e2_trades.jsonl"

# 入选券(含 hold/buy/sell/delist 全部动作涉及 code)
codes = set()
for line in open(TRADES):
    codes.add(json.loads(line)["code"])
codes = sorted(codes)
print("unique codes:", len(codes), flush=True)

import akshare as ak

def fetch(code):
    # 东财符号: 12x/11x 开头: sz/sh 依代码前缀 (12=深, 11=沪, 404/405 特殊)
    if code.startswith("12") or code.startswith("404") or code.startswith("405"):
        sym = "sz" + code
    else:
        sym = "sh" + code
    df = ak.bond_zh_hs_cov_daily(symbol=sym)
    df.to_parquet(f"{OUT}/{code}.parquet")
    return len(df)

ok, fail = [], []
t0 = time.time()
for i, c in enumerate(codes):
    if time.time() - t0 > 200:
        print("TIME CAP reached at", i, flush=True)
        break
    if os.path.exists(f"{OUT}/{c}.parquet"):
        ok.append(c); continue
    for attempt in range(2):
        try:
            n = fetch(c)
            ok.append(c)
            break
        except Exception as e:
            if attempt == 1:
                fail.append((c, str(e)[:80]))
                print("FAIL", c, str(e)[:80], flush=True)
            time.sleep(0.5)
    time.sleep(0.5)
print("ok", len(ok), "fail", len(fail), "time", round(time.time()-t0, 1), "s", flush=True)
json.dump({"ok": ok, "fail": fail}, open(f"{OUT}/_summary.json", "w"), ensure_ascii=False, indent=1)
print("DONE_G5_FETCH")
