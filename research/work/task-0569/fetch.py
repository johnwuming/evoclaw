#!/usr/bin/env python3
# task-0569 step① data fetch: Tencent day+hfq per-year x3 codes, Sina daily, qt snapshot
import json, os, time, urllib.request, csv

OUT = "/root/.openclaw/workspace/shared/results/work/task-0569/data"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
CODES = ["sh511010", "sh511260", "sh511090"]
YEARS = list(range(2013, 2027))

def get(url, binary=False, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                b = r.read()
                return b if binary else b.decode("utf-8", "ignore")
        except Exception as e:
            print(f"  retry{i+1} {e}")
            time.sleep(2 + i)
    raise RuntimeError(f"FAIL {url[:80]}")

def fetch_tx(code, fq):
    rows = {}
    for y in YEARS:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,{y}-01-01,{y}-12-31,640,{fq}"
        j = json.loads(get(url))
        d = j["data"][code]
        arr = d.get(f"{fq}day") or d.get("day")
        for k in arr:
            # [date, open, close, high, low, volume, ...]
            rows[k[0]] = (k[1], k[2], k[3], k[4], k[5])
        time.sleep(0.25)
    path = f"{OUT}/{code}_{fq}.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        if fq == "day":
            w.writerow(["date", "open", "close", "high", "low", "vol"])
        else:
            w.writerow(["date", "hc"])
        for dt in sorted(rows):
            v = rows[dt]
            w.writerow([dt] + list(v[:5]) if fq == "day" else [dt, v[1]])
    n = len(rows)
    ks = sorted(rows)
    print(f"{code} {fq}: n={n} {ks[0]}..{ks[-1]}")
    return path

for c in CODES:
    fetch_tx(c, "day")
    fetch_tx(c, "hfq")

# Sina daily (T3 sentinel) - datalen try 2000
for c in CODES:
    for dl in (2000, 1023):
        try:
            url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={c}&scale=240&ma=no&datalen={dl}"
            txt = get(url)
            j = json.loads(txt)
            with open(f"{OUT}/{c}_sina.csv", "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["day", "close"])
                for k in j:
                    w.writerow([k["day"], k["close"]])
            print(f"{c} sina: n={len(j)} {j[0]['day']}..{j[-1]['day']} (datalen={dl})")
            break
        except Exception as e:
            print(f"{c} sina datalen={dl} failed: {e}")
    time.sleep(0.5)

# qt snapshot (spread sentinel)
snap = get("http://qt.gtimg.cn/q=" + ",".join(CODES))
with open(f"{OUT}/qt_snapshot.txt", "w") as f:
    f.write(snap)
for line in snap.split(";"):
    line = line.strip()
    if "=" in line and "~" in line:
        var, val = line.split("=", 1)
        fs = val.split("~")
        if len(fs) > 12:
            print(f"{fs[2]} {fs[1]} price={fs[3]} bid1={fs[9]}x{fs[10]} ask1={fs[11]}x{fs[12]}")
print("FETCH DONE")
