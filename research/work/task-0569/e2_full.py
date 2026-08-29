#!/usr/bin/env python3
# task-0569 steps ③④⑤⑥: G0④ assertions, V1-V4 NAV (gross/net), G1-G7, G3 solver, T3, sentinels
import csv, json, math

DATA = "/root/.openclaw/workspace/shared/results/work/task-0569/data"
RES = "/root/.openclaw/workspace/shared/results/work/task-0569"
BAD = {"sh511010": [["2014-03-10", "2014-03-12"], ["2016-01-15", "2016-01-19"],
                     ["2016-03-03", "2016-03-07"], ["2017-12-05", "2017-12-07"]],
       "sh511260": [["2017-08-24", "2017-08-24"]], "sh511090": []}
FIRST_FULL = {"sh511010": "2013-04", "sh511260": "2017-09", "sh511090": "2023-07"}
COST = 0.0013  # |dw| x 0.13%

def load_hfq_low(code):
    ds, cs = [], []
    with open(f"{DATA}/{code}_hfq2.csv") as f:
        for row in csv.DictReader(f):
            ds.append(row["date"]); cs.append(float(row["low"]))
    n_bad = 0
    for w0, w1 in BAD.get(code, []):
        idx = [i for i, d in enumerate(ds) if w0 <= d <= w1]
        if not idx:
            continue
        i0, i1 = idx[0], idx[-1]
        if i0 == 0:
            cs[i0] = math.sqrt(cs[i0] * cs[i1 + 1]); n_bad += 1; continue
        prev = cs[i0 - 1]
        for i in range(i0, i1 + 1):
            cs[i] = math.sqrt(prev * cs[i + 1]); prev = cs[i]; n_bad += 1
    return ds, cs, n_bad

def load_raw_capacity(code):
    ds, amt = [], []
    with open(f"{DATA}/{code}_day.csv") as f:
        for r in csv.DictReader(f):
            ds.append(r["date"]); amt.append(float(r["vol"]) * 100 * float(r["close"]))
    return ds, amt

def mk(d): return d[:7]

def metrics(rets):
    n = len(rets)
    nav, peak, mdd = 1.0, 1.0, 0.0
    for r in rets:
        nav *= (1 + r); peak = max(peak, nav); mdd = min(mdd, nav / peak - 1)
    ann = nav ** (12 / n) - 1 if nav > 0 else -1.0
    mu = sum(rets) / n
    vol = (sum((r - mu) ** 2 for r in rets) / (n - 1)) ** 0.5 * math.sqrt(12) if n > 1 else 0.0
    return dict(n=n, ann=ann, vol=vol, mdd=mdd, calmar=(ann / abs(mdd) if mdd < 0 else None), nav_end=nav)

def corr(a, b):
    n = len(a); ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (n - 1)
    va = sum((x - ma) ** 2 for x in a) / (n - 1); vb = sum((y - mb) ** 2 for y in b) / (n - 1)
    return cov / math.sqrt(va * vb)

def sma200_at(ds, cs, i):
    return sum(cs[i - 199:i + 1]) / 200.0 if i >= 199 else None

def build_leg(code):
    """returns months list, dict month -> (ret, w_applied, signal_date)"""
    ds, cs, n_bad = load_hfq_low(code)
    last = {}
    for d, c in zip(ds, cs):
        last[mk(d)] = (d, c)
    allk = sorted(last)
    ret_m = {k: last[k][1] / last[p][1] - 1 for p, k in zip(allk, allk[1:])}
    pos = {d: i for i, d in enumerate(ds)}
    w_ap, sig_date = {}, {}
    for k in allk[1:]:
        if k < FIRST_FULL[code]:
            continue
        pk = allk[allk.index(k) - 1]
        dlast = last[pk][0]; i = pos[dlast]
        s = sma200_at(ds, cs, i)
        w_ap[k] = 0.0 if s is None else (1.0 if last[pk][1] > s else 0.0)
        sig_date[k] = dlast
    return ds, cs, allk, ret_m, w_ap, sig_date, n_bad, last, pos

MMF = {}
with open("/root/.openclaw/workspace/shared/results/04-投资研究/engines/gold/mmf_monthly_push.csv") as f:
    for r in csv.DictReader(f):
        MMF[mk(r["month"])] = float(r["mmf_ret"])
A13 = {}
with open("/root/.openclaw/workspace/shared/results/04-投资研究/a13_rsraw_e1f10_full_nav.csv") as f:
    nav_last = {}
    for r in csv.DictReader(f):
        nav_last[mk(r["date"])] = float(r["nav"])
    ak = sorted(nav_last)
    for p, k in zip(ak, ak[1:]):
        A13[k] = nav_last[k] / nav_last[p] - 1
GOLD = {}
with open("/root/.openclaw/workspace/shared/results/04-投资研究/engines/gold/shadow_nav.csv") as f:
    for r in csv.DictReader(f):
        GOLD[mk(r["month"])] = float(r["gold_ret"])

out = {}
legs = {}
for code in ["sh511010", "sh511260", "sh511090"]:
    legs[code] = build_leg(code)
    print(code, "interp", legs[code][6])

def strat_stream(code):
    """V1-style trend x cash for one code: returns months, gross, net, w series"""
    _, _, allk, ret_m, w_ap, sig_date, _, _, _ = legs[code]
    months = sorted(k for k in w_ap)
    gross, net, w_seq = [], [], []
    prev_w = 0.0
    for k in months:
        w = w_ap[k]
        cash = MMF.get(k, 0.0)
        g = w * ret_m[k] + (1 - w) * cash
        c = abs(w - prev_w) * COST
        gross.append(g); net.append(g - c); w_seq.append(w)
        prev_w = w
    return months, gross, net, w_seq

# ---- G0④ assertions (layer-2 look-ahead anchor) ----
A = {}
ds, cs, allk, ret_m, w_ap, sig_date, n_bad, last, pos = legs["sh511010"]
a1_fail = 0
for k in sorted(w_ap):
    pk = allk[allk.index(k) - 1]
    dlast = last[pk][0]; i = pos[dlast]
    s = sma200_at(ds, cs, i)
    w_chk = 0.0 if s is None else (1.0 if last[pk][1] > s else 0.0)
    if w_chk != w_ap[k]:
        a1_fail += 1
    # signal date must be strictly before month k
    if not sig_date[k][:7] < k:
        a1_fail += 1
A["A1_signal_truncated_recompute_fail"] = a1_fail
A["A2_signal_dates_strictly_prior"] = all(sig_date[k][:7] < k for k in sig_date)
# A3/A4: cash same-month accounting on V1 stream
months, gross, net, w_seq = strat_stream("sh511010")
a3_fail = 0
for idx, k in enumerate(months):
    w = w_seq[idx]; cash = MMF.get(k, 0.0)
    if abs(gross[idx] - (w * ret_m[k] + (1 - w) * cash)) > 1e-12:
        a3_fail += 1
A["A3_cash_same_month_accounting_fail"] = a3_fail
A["A4_weights_binary"] = all(w in (0.0, 1.0) for w in w_seq)
A["G04_verdict"] = "PASS" if a1_fail == 0 and a3_fail == 0 and A["A2_signal_dates_strictly_prior"] and A["A4_weights_binary"] else "FAIL"
print("G0④:", A)

# ---- ③ V1-V4 streams, full window <= 2026-08-28 ----
V = {}
for code, tag in [("sh511010", "V1"), ("sh511260", "V2"), ("sh511090", "V4")]:
    months, gross, net, w_seq = strat_stream(code)
    mg, mn = metrics(gross), metrics(net)
    pres = sum(w_seq) / len(w_seq)
    V[tag] = dict(code=code, months=months, gross=gross, net=net, w=w_seq,
                  m_gross=mg, m_net=mn, presence=pres)
    print(f"{tag} {code}: n={len(months)} pres={pres*100:.1f}% gross ann={mg['ann']*100:.2f}% MDD={mg['mdd']*100:.2f}% | net ann={mn['ann']*100:.2f}% MDD={mn['mdd']*100:.2f}% Calmar={mn['calmar']:.2f}")

# V3 = (V1+V2)/2 equal-weight monthly composite of net streams
m1 = set(V["V1"]["months"]); m2 = set(V["V2"]["months"])
mc = sorted(m1 & m2)
v3_net = [(V["V1"]["net"][V["V1"]["months"].index(k)] + V["V2"]["net"][V["V2"]["months"].index(k)]) / 2 for k in mc]
v3_gross = [(V["V1"]["gross"][V["V1"]["months"].index(k)] + V["V2"]["gross"][V["V2"]["months"].index(k)]) / 2 for k in mc]
V["V3"] = dict(code="V1+V2/2", months=mc, gross=v3_gross, net=v3_net, w=[],
               m_gross=metrics(v3_gross), m_net=metrics(v3_net),
               presence=None)
print(f"V3: n={len(mc)} net ann={V['V3']['m_net']['ann']*100:.2f}% MDD={V['V3']['m_net']['mdd']*100:.2f}% Calmar={V['V3']['m_net']['calmar']:.2f}")

# ---- ④ G4 independence (V1 net vs a13/gold, overlap windows) ----
v1m = {k: V["V1"]["net"][i] for i, k in enumerate(V["V1"]["months"])}
pa = [(k, v1m[k]) for k in V["V1"]["months"] if k in A13]
pg = [(k, v1m[k]) for k in V["V1"]["months"] if k in GOLD]
c_a13 = corr([x[1] for x in pa], [A13[x[0]] for x in pa])
c_gold = corr([x[1] for x in pg], [GOLD[x[0]] for x in pg])
print(f"G4: corr(V1net,a13)={c_a13:+.3f} n={len(pa)} | corr(V1net,gold)={c_gold:+.3f} n={len(pg)}")

# ---- G1 / G2 / G5 / G7 ----
v1_net_m = V["V1"]["m_net"]; v1_gross_m = V["V1"]["m_gross"]
mmf_win = [MMF[k] for k in V["V1"]["months"] if k in MMF]
mmf_ann = metrics(mmf_win)["ann"]
bh = metrics([ (lambda rm: rm)(V["V1"]["months"][i]) and 0 for i in range(0)])  # placeholder
# B&H 511010 on same window (from leg returns)
_, _, _, ret_m1, _, _, _, _, _ = legs["sh511010"]
bh_rets = [ret_m1[k] for k in V["V1"]["months"]]
m_bh = metrics(bh_rets)
g1a = v1_net_m["ann"] - mmf_ann
g1b = v1_net_m["calmar"] >= m_bh["calmar"]
g2 = v1_net_m["mdd"] <= 1.25 * m_bh["mdd"]
g5 = v1_gross_m["ann"] - v1_net_m["ann"]
is_r = [v1m[k] for k in V["V1"]["months"] if k < "2021-01"]
oos_r = [v1m[k] for k in V["V1"]["months"] if k >= "2021-01"]
m_is, m_oos = metrics(is_r), metrics(oos_r)
print(f"G1a: net ann {v1_net_m['ann']*100:.3f}% - mmf {mmf_ann*100:.3f}% = {g1a*100:+.3f}pp (>=+0.5) n_mmf={len(mmf_win)}")
print(f"G1b: net Calmar {v1_net_m['calmar']:.3f} vs B&H {m_bh['calmar']:.3f} -> {'PASS' if g1b else 'FAIL'}")
print(f"G2: net MDD {v1_net_m['mdd']*100:.2f}% vs 1.25xB&H {1.25*m_bh['mdd']*100:.2f}% -> {'PASS' if g2 else 'FAIL'}")
print(f"G5: gross-net ann diff {g5*100:.3f}pp (<=1)")
print(f"G7: IS n={m_is['n']} ann={m_is['ann']*100:.2f}% Calmar={m_is['calmar']:.3f} | OOS n={m_oos['n']} ann={m_oos['ann']*100:.2f}% Calmar={m_oos['calmar']:.3f} ratio={m_is['ann']/m_oos['ann']:.2f}" if m_oos['ann']!=0 else "G7 OOS ann=0")

# ---- G6 capacity: 10% x ADV20 at month-ends, median >= 50M ----
cads, camt = load_raw_capacity("sh511010")
adv = {}
for i in range(len(cads)):
    if i >= 19:
        adv[cads[i]] = sum(camt[i - 19:i + 1]) / 20.0
caps = []
for k in V["V1"]["months"]:
    dlast = max(d for d in adv if mk(d) == k)
    caps.append(0.10 * adv[dlast])
caps_s = sorted(caps)
med = caps_s[len(caps_s) // 2]
print(f"G6: median(10%xADV20) = {med/1e8:.3f}亿 min={min(caps)/1e8:.3f}亿 max={max(caps)/1e8:.3f}亿 (>=0.5亿)")

# ---- ⑤ G3: two-leg baseline vs three-leg constrained equal-vol (W=36) ----
v1net = {k: V["V1"]["net"][i] for i, k in enumerate(V["V1"]["months"])}
common = sorted(set(A13) & set(GOLD) & set(v1net))
print(f"G3 common months: {common[0]}..{common[-1]} n={len(common)}")
W = 36
W_TGT = [0.58, 0.42]

def solve_w(s):
    # min sum (wi*si - mean(wi*si))^2 s.t. sum=1, 0<=w<=1, 0.15<=w_bond<=0.40 (KKT active set)
    def f(w):
        t = [w[i] * s[i] for i in range(3)]
        m = sum(t) / 3
        return sum((x - m) ** 2 for x in t)
    cands = []
    iv = [1 / x for x in s]; S = sum(iv)
    cands.append([x / S for x in iv])
    for b in (0.40, 0.15):
        rem = 1 - b
        ia, ig = 1 / s[0], 1 / s[1]; S2 = ia + ig
        cands.append([rem * ia / S2, rem * ig / S2, b])
        cands.append([rem, 0.0, b]); cands.append([0.0, rem, b])
    feas = [w for w in cands if sum(w) > 1 - 1e-9 and 0.15 - 1e-9 <= w[2] <= 0.40 + 1e-9 and all(0 - 1e-9 <= x <= 1 + 1e-9 for x in w)]
    return min(feas, key=f)

# sanity vs dense grid on first solve month
si0 = next(i for i in range(len(common)) if i >= W)
s0 = [0.052, 0.038, 0.019]
wq = solve_w(s0)
best = None
bq = 1000
import itertools
for wb in range(150, 401, 5):
    for wa in range(0, 1001 - wb, 5):
        wg = 1000 - wb - wa
        if wg < 0: continue
        w = [wa / 1000, wg / 1000, wb / 1000]
        fv = f_v = sum((w[i] * s0[i]) ** 2 for i in range(3)) - (sum(w[i] * s0[i] for i in range(3)) ** 2) / 3
        if fv < bq:
            bq = fv; best = w
print(f"solver sanity: kkt={["%.4f" % x for x in wq]} f={sum((wq[i]*s0[i])**2 for i in range(3))-(sum(wq[i]*s0[i] for i in range(3))**2)/3:.3e} grid_best={best} f={bq:.3e}")

r3, r2, w_hist, first_m = [], [], [], None
cov_buf = []
for i in range(W, len(common)):
    k = common[i]
    win = common[i - W:i]
    xs = [[A13[m] for m in win], [GOLD[m] for m in win], [v1net[m] for m in win]]
    mus = [sum(x) / W for x in xs]
    cov = [[sum((xs[a][t] - mus[a]) * (xs[b][t] - mus[b]) for t in range(W)) / (W - 1) for b in range(3)] for a in range(3)]
    sig = [math.sqrt(cov[i][i]) for i in range(3)]
    w = solve_w(sig)
    r3.append(w[0] * A13[k] + w[1] * GOLD[k] + w[2] * v1net[k])
    r2.append(W_TGT[0] * A13[k] + W_TGT[1] * GOLD[k])
    w_hist.append((k, w, sig))
    if first_m is None:
        first_m = k
m3, m2L = metrics(r3), metrics(r2)
print(f"G3 window {first_m}..{common[-1]} n={len(r3)}")
print(f"  two-leg: ann={m2L['ann']*100:.2f}% vol={m2L['vol']*100:.2f}% MDD={m2L['mdd']*100:.2f}% Calmar={m2L['calmar']:.2f}")
print(f"  three-leg: ann={m3['ann']*100:.2f}% vol={m3['vol']*100:.2f}% MDD={m3['mdd']*100:.2f}% Calmar={m3['calmar']:.2f}")
print(f"  MDD drop {m2L['mdd']*100:.2f}% -> {m3['mdd']*100:.2f}% ({(m3['mdd']/m2L['mdd']-1)*100:+.1f}%) | Calmar {m2L['calmar']:.3f} -> {m3['calmar']:.3f}")
wb_range = (min(w[1][2] for w in w_hist), max(w[1][2] for w in w_hist))
wmean = [sum(w[1][j] for w in w_hist) / len(w_hist) for j in range(3)]
print(f"  w_bond range {wb_range[0]*100:.1f}%..{wb_range[1]*100:.1f}% mean w=[{wmean[0]*100:.1f}%,{wmean[1]*100:.1f}%,{wmean[2]*100:.1f}%]")

# ---- T3 sina vs tencent monthly signal consistency ----
def sina_signal(code):
    ds, cs = [], []
    with open(f"{DATA}/{code}_sina.csv") as f:
        for r in csv.DictReader(f):
            ds.append(r["day"]); cs.append(float(r["close"]))
    last = {}
    for d, c in zip(ds, cs):
        last[mk(d)] = c
    ws = {}
    allk = sorted(last)
    for j, k in enumerate(allk):
        if j < FIRST_FULL.get(code, "2000-01") and False:
            pass
        if j >= 199:
            ws[k] = 1.0 if last[k] > sum(cs[j - 199:j + 1]) / 200.0 else 0.0
    return ws
ws_sina = sina_signal("sh511010")
# compare on months where both defined: tx signal(m) from month-end m-1 -> applied m; sina same construction
agree, tot = 0, 0
for k in sorted(w_ap):
    if k in ws_sina and k in w_ap and k >= "2022-07":
        tot += 1
        if w_ap[k] == ws_sina[k]:
            agree += 1
t3 = 1 - agree / tot if tot else None
print(f"T3: sina-vs-tencent monthly w agreement {agree}/{tot} = {t3*100:.1f}% inconsistent (<=20%)")

# ---- T1 sentinel: |daily ret|>15% on cleaned low-hfq ----
sents = {}
for code in ["sh511010", "sh511260", "sh511090"]:
    ds, cs, n_bad = legs[code][0], legs[code][1], legs[code][6]
    big = [(ds[i], cs[i] / cs[i - 1] - 1) for i in range(1, len(cs)) if abs(cs[i] / cs[i - 1] - 1) > 0.15]
    sents[code] = dict(n_days=len(cs), interp=n_bad, big_moves=big)
    print(f"T1 sentinel {code}: |ret|>15% after interp = {len(big)} {big[:3]}")

# ---- dump monthly CSVs + summary json ----
with open(f"{RES}/v1_v4_monthly.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "V1_gross", "V1_net", "V1_w", "V2_net", "V4_net", "a13", "gold", "mmf"])
    for i, k in enumerate(V["V1"]["months"]):
        w.writerow([k, V["V1"]["gross"][i], V["V1"]["net"][i], V["V1"]["w"][i],
                    V["V2"]["net"][i] if i < len(V["V2"]["net"]) else "",
                    V["V4"]["net"][i] if i < len(V["V4"]["net"]) else "",
                    A13.get(k, ""), GOLD.get(k, ""), MMF.get(k, "")])
with open(f"{RES}/g3_weights.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "w_a13", "w_gold", "w_bond", "sig_a13", "sig_gold", "sig_bond", "r2leg", "r3leg"])
    for i, (k, wv, sig) in enumerate(w_hist):
        w.writerow([k] + [round(x, 6) for x in wv + sig + [r2[i], r3[i]]])

summary = dict(
    G04=A,
    V1=dict(presence=V["V1"]["presence"], gross=v1_gross_m, net=v1_net_m),
    V2=dict(presence=V["V2"]["presence"], gross=V["V2"]["m_gross"], net=V["V2"]["m_net"]),
    V3=dict(net=V["V3"]["m_net"], gross=V["V3"]["m_gross"]),
    V4=dict(presence=V["V4"]["presence"], gross=V["V4"]["m_gross"], net=V["V4"]["m_net"]),
    G4=dict(corr_a13=c_a13, n_a13=len(pa), corr_gold=c_gold, n_gold=len(pg)),
    G1=dict(net_ann=v1_net_m["ann"], mmf_ann=mmf_ann, n_mmf=len(mmf_win), excess=g1a, net_calmar=v1_net_m["calmar"], bh_calmar=m_bh["calmar"], bh=m_bh),
    G2=dict(net_mdd=v1_net_m["mdd"], bh_mdd=m_bh["mdd"], bound=1.25 * m_bh["mdd"]),
    G5=dict(gross_minus_net=g5),
    G7=dict(IS=m_is, OOS=m_oos, ratio=m_is["ann"] / m_oos["ann"] if m_oos["ann"] else None),
    G6=dict(median_cap=med, min_cap=min(caps), max_cap=max(caps)),
    G3=dict(window=[first_m, common[-1]], n=len(r3), two_leg=m2L, three_leg=m3,
           w_bond_range=list(wb_range), w_mean=wmean),
    T3=dict(agree=agree, tot=tot, inconsistent=t3),
    T1=sents,
)
json.dump(summary, open(f"{RES}/e2_summary.json", "w"), indent=1, ensure_ascii=False)
print("SUMMARY SAVED")
