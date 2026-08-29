#!/usr/bin/env python3
# task-0569 step② G0/G0④ anchor validation (window <= 2026-08-27, R-331 anchors)
import csv, json, math
from datetime import date

DATA = "/root/.openclaw/workspace/shared/results/work/task-0569/data"
CUT = "2026-08-27"  # R-331 anchor window
BAD = {  # R-331 bad-print windows (raw->hfq inherited)
    "sh511010": [["2014-03-10", "2014-03-12"], ["2016-01-15", "2016-01-19"],
                 ["2016-03-03", "2016-03-07"], ["2017-12-05", "2017-12-07"]],
    "sh511260": [["2017-08-24", "2017-08-24"]],
    "sh511090": [],
}
FIRST_FULL = {"sh511010": "2013-04", "sh511260": "2017-09", "sh511090": "2023-07"}
ANCHOR = {  # presence, strat_ann(gross), strat_corr_a13, strat_corr_gold
    "sh511010": (0.795, 0.0369, -0.085, 0.052),
    "sh511260": (0.815, 0.0375, -0.235, 0.062),
    "sh511090": (0.500, 0.0497, -0.384, -0.048),
}

def load_hfq(code):
    # E1 convention (root-caused 2026-08-30): E1's 'close' = API array idx4 = daily LOW; verified
    # zero-diff vs /tmp/t509 E1 artifacts on 6229 common days <=2026-08-27. G0 anchors are low-hfq based.
    ds, cs = [], []
    with open(f"{DATA}/{code}_hfq2.csv") as f:
        for row in csv.DictReader(f):
            ds.append(row["date"]); cs.append(float(row["low"]))
    # E1-structure interpolation: replace EVERY day in listed window, fwd iter c'[t]=sqrt(c'[t-1]*c_raw[t+1])
    n_bad = 0
    for w0, w1 in BAD.get(code, []):
        idx = [i for i, d in enumerate(ds) if w0 <= d <= w1]
        if not idx:
            continue
        i0, i1 = idx[0], idx[-1]
        if i0 == 0:  # 511260 first day: E1 used sqrt(self*next)=95.436
            cs[i0] = math.sqrt(cs[i0] * cs[i1 + 1])
            n_bad += 1
            continue
        prev = cs[i0 - 1]
        for i in range(i0, i1 + 1):
            cs[i] = math.sqrt(prev * cs[i + 1])
            prev = cs[i]
            n_bad += 1
    return ds, cs, n_bad

def month_key(d): return d[:7]

def monthly_series(ds, cs, code):
    # monthly last trading day; first full month onward
    last = {}
    for d, c in zip(ds, cs):
        if d <= CUT:
            last[month_key(d)] = c  # keeps last occurrence (dates sorted)
    keys = sorted(k for k in last if k >= FIRST_FULL[code])
    return keys, last

def sma_signal_all(ds, cs, keys, last):
    # SMA200 signal at each month-end; signal(m) applies to month m+1
    pos = {d: i for i, d in enumerate(ds)}
    sig = {}
    for k in keys:
        dlast = max(d for d in ds if d <= CUT and month_key(d) == k)
        i = pos[dlast]
        sig[k] = (1.0 if cs[i] > sum(cs[i - 199:i + 1]) / 200.0 else 0.0) if i >= 199 else 0.0
    return sig

def mmf_map():
    m = {}
    with open("/root/.openclaw/workspace/shared/results/04-投资研究/engines/gold/mmf_monthly_push.csv") as f:
        for row in csv.DictReader(f):
            m[month_key(row["month"])] = float(row["mmf_ret"])
    return m

def metrics(rets):
    n = len(rets)
    nav, peak, mdd = 1.0, 1.0, 0.0
    for r in rets:
        nav *= (1 + r)
        peak = max(peak, nav)
        mdd = min(mdd, nav / peak - 1)
    ann = nav ** (12 / n) - 1 if nav > 0 else -1
    mu = sum(rets) / n
    vol = (sum((r - mu) ** 2 for r in rets) / (n - 1)) ** 0.5 * math.sqrt(12)
    return dict(n=n, ann=ann, vol=vol, mdd=mdd, calmar=(ann / abs(mdd) if mdd < 0 else None))

def corr(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (n - 1)
    va = sum((x - ma) ** 2 for x in a) / (n - 1)
    vb = sum((y - mb) ** 2 for y in b) / (n - 1)
    return cov / math.sqrt(va * vb)

MMF = mmf_map()
res = {}
for code in ["sh511010", "sh511260", "sh511090"]:
    ds, cs, n_bad = load_hfq(code)
    keys, last = monthly_series(ds, cs, code)
    sig = sma_signal_all(ds, cs, keys, last)
    # monthly returns
    allk = sorted(last)
    ret_m = {k: last[k] / last[prev] - 1 for prev, k in zip(allk, allk[1:])}
    # strategy gross: w(m-1) applied to month m; cash = mmf if avail else 0
    w_applied, strat = {}, {}
    for k in keys:
        prev = allk[allk.index(k) - 1]
        w = sig[prev] if prev in sig else 0.0  # warm-up months -> 0
        w_applied[k] = w
        cash = MMF.get(k, 0.0)
        strat[k] = w * ret_m[k] + (1 - w) * cash
    mk = sorted(strat)
    r_strat = [strat[k] for k in mk]
    r_bh = [ret_m[k] for k in mk]
    m_s, m_b = metrics(r_strat), metrics(r_bh)
    pres = sum(w_applied.values()) / len(mk)
    res[code] = dict(presence=pres, ann=m_s["ann"], mdd_s=m_s["mdd"], calmar_s=m_s["calmar"],
                     bh_ann=m_b["ann"], bh_mdd=m_b["mdd"], bh_calmar=m_b["calmar"],
                     n_months=len(mk), first=mk[0], last=mk[-1], n_bad_interp=n_bad,
                     keys=mk, strat=strat, bh=ret_m)
    a = ANCHOR[code]
    dp = (pres - a[0]) * 100
    da = (m_s["ann"] / a[1] - 1) * 100
    print(f"{code}: n={len(mk)} {mk[0]}..{mk[-1]} interp={n_bad}")
    print(f"  presence {pres*100:.1f}% vs {a[0]*100:.1f}% dev={dp:+.2f}pp (<=0.5)")
    print(f"  strat_ann {m_s['ann']*100:.2f}% vs {a[1]*100:.2f}% reldev={da:+.1f}% (<=5%)  [B&H {m_b['ann']*100:.2f}% MDD {m_b['mdd']*100:.2f}% Calmar {m_b['calmar']:.2f}]")
    print(f"  strat MDD {m_s['mdd']*100:.2f}% Calmar {m_s['calmar']:.2f}")

# corr matrix (strategy level) vs a13 / gold
a13m = {}
with open("/root/.openclaw/workspace/shared/results/04-投资研究/a13_rsraw_e1f10_full_nav.csv") as f:
    rows = [r for r in csv.DictReader(f)]
    nav_last = {}
    for r in rows:
        nav_last[month_key(r["date"])] = float(r["nav"])
    ak = sorted(nav_last)
    for p, k in zip(ak, ak[1:]):
        a13m[k] = nav_last[k] / nav_last[p] - 1
goldm = {}
with open("/root/.openclaw/workspace/shared/results/04-投资研究/engines/gold/shadow_nav.csv") as f:
    for r in csv.DictReader(f):
        goldm[month_key(r["month"])] = float(r["gold_ret"])

print("\ncorr(strategy, a13/gold):")
for code in res:
    mk = res[code]["keys"]
    pa = [(k, res[code]["strat"][k]) for k in mk if k in a13m]
    pg = [(k, res[code]["strat"][k]) for k in mk if k in goldm]
    ca = corr([x[1] for x in pa], [a13m[x[0]] for x in pa])
    cg = corr([x[1] for x in pg], [goldm[x[0]] for x in pg])
    a = ANCHOR[code]
    print(f"{code}: vs a13 {ca:+.3f} (anchor {a[2]:+.3f}, dev {abs(ca-a[2]):.3f}<=0.02, n={len(pa)})  vs gold {cg:+.3f} (anchor {a[3]:+.3f}, dev {abs(cg-a[3]):.3f}, n={len(pg)})")
    res[code]["corr_a13"] = ca; res[code]["corr_gold"] = cg

# verdict
ok = True
for code in res:
    a = ANCHOR[code]; r = res[code]
    ok &= abs((r["presence"] - a[0]) * 100) <= 0.5
    ok &= abs(r["ann"] / a[1] - 1) * 100 <= 5
    ok &= abs(r["corr_a13"] - a[2]) <= 0.02
    ok &= abs(r["corr_gold"] - a[3]) <= 0.02
print("\nG0 verdict:", "PASS" if ok else "FAIL")
json.dump({c: {k: v for k, v in res[c].items() if k not in ("keys", "strat", "bh")} for c in res},
          open("/root/.openclaw/workspace/shared/results/work/task-0569/g0_result.json", "w"), indent=1)
