#!/usr/bin/env python
# task-0576: P2 gate design E1 profile scan (READ-ONLY on HP artifacts)
# MA trend gate (zz500 proxy) x spread momentum gate (zz500/hs300) on a13_rsraw_e1f10dz raw nav
import pandas as pd, numpy as np, json, sys

BASE = "/home/noname/quant-evolve"
OUT_SCAN = f"{BASE}/results/p2gate_task0576_scan.csv"
OUT_STATES = f"{BASE}/results/p2gate_task0576_states.csv"
OUT_JSON = f"{BASE}/results/p2gate_task0576_summary.json"

# ---------- load ----------
nav = pd.read_csv(f"{BASE}/results/a13_rsraw_e1f10dz_full_nav.csv", parse_dates=["date"]).set_index("date")
zz = pd.read_parquet(f"{BASE}/data/zz500_daily_20060101_20260808.parquet")[["date","close"]].set_index("date")
hs = pd.read_parquet(f"{BASE}/data/hs300_daily_20060101_20260808.parquet")[["date","close"]].set_index("date")
df = nav[["nav"]].join(zz.rename(columns={"close":"zz"}), how="inner").join(hs.rename(columns={"close":"hs"}), how="inner")
df = df.sort_index()
r = df["nav"].pct_change().fillna(0.0)  # strategy daily returns
dates = df.index

# ---------- validation vs registry ----------
dd_full = df["nav"]/df["nav"].cummax()-1
n_dd20 = int((dd_full <= -0.20).sum())
mdd_raw = float(dd_full.min())
tot = (1+r).prod(); ann_raw = tot**(252/len(r))-1
valid = {"ann_raw": round(ann_raw,4), "mdd_raw": round(mdd_raw,4), "n_dd20": n_dd20,
         "expect": "ann~0.2202 mdd~-0.3355 n_dd20=197(R-250/R-373)"}
print("VALIDATE:", json.dumps(valid), flush=True)

# ---------- metrics ----------
SEGMENTS = {
    "seg2015crash": ("2015-06-12","2015-07-08"),
    "seg2015long":  ("2015-06-12","2016-06-30"),
    "seg2024q1":    ("2024-01-02","2024-02-07"),
    "seg2026":      ("2026-05-26","2026-07-22"),
    "seg2014_12":   ("2014-12-01","2014-12-22"),
    "seg2020style": ("2020-09-10","2021-01-13"),
}
IS_END = "2017-12-31"

def perf(ret, whipsaw=None):
    navc = (1+ret).cumprod()
    dd = navc/navc.cummax()-1
    n = len(ret)
    ann = navc.iloc[-1]**(252/n)-1 if n>0 else np.nan
    vol = ret.std()*np.sqrt(252)
    sharpe = ann/vol if vol>0 else np.nan
    mdd = float(dd.min())
    return {"ann":round(float(ann),4),"mdd":round(mdd,4),"sharpe":round(float(sharpe),3),
            "calmar":round(float(ann/abs(mdd)),3) if mdd!=0 else np.nan}

def seg_ret(ret):
    out={}
    for k,(s,e) in SEGMENTS.items():
        w = ret.loc[s:e]
        out[k] = round(float((1+w).prod()-1),4) if len(w)>0 else None
    return out

def whipsaw_of(pos_sig):
    return int((pos_sig.diff().abs()>1e-9).sum())

# ---------- gate builders ----------
def ma_gate_pos(period, confirm, mapping):
    ma = df["zz"].rolling(period).mean()
    below = (df["zz"] < ma).astype(int)
    w = max(confirm,1)
    trig = below.rolling(w).min()==1
    state = np.ones(len(df))
    s = 1.0
    for i in range(len(df)):
        if trig.iloc[i]: s = 0.0
        elif bool(df["zz"].iloc[i] >= ma.iloc[i]): s = 1.0
        state[i] = s
    pos = pd.Series(state, index=df.index)
    if mapping=="half": pos = pos.where(pos>0, 0.5)  # off -> 0.5
    return pos

def mom_gate_pos(L):
    ratio = df["zz"]/df["hs"]
    mom = ratio/ratio.shift(L)-1
    return (mom>=0).astype(float).replace(0.0,0.0)  # 1 in, 0 out

def apply_pos(pos):
    sig = pos.shift(1).fillna(1.0)  # yesterday's state -> today's position (no look-ahead)
    return r*sig, sig

# ---------- overlap utilities ----------
dd20_mask = dd_full <= -0.20
zzret = df["zz"].pct_change()
rv20 = zzret.rolling(20).std()*np.sqrt(252)
thr = rv20.expanding(min_periods=250).quantile(0.7).shift(1)
rv_high = (rv20 > thr).fillna(False)

def overlap(riskoff_mask):
    A, B, C = riskoff_mask, dd20_mask, rv_high
    ab, ac = (A&B).sum(), (A&C).sum()
    return {
        "riskoff_days": int(A.sum()),
        "dd20_days_covered": int(ab), "coverage_of_dd20": round(float(ab)/max(int(B.sum()),1),3),
        "precision_dd20": round(float(ab)/max(int(A.sum()),1),3),
        "jaccard_dd20": round(float(ab)/max(int((A|B).sum()),1),3),
        "rvhigh_days_covered": int(ac), "coverage_of_rvhigh": round(float(ac)/max(int(C.sum()),1),3),
        "jaccard_rvhigh": round(float(ac)/max(int((A|C).sum()),1),3),
    }

# ---------- run all configs ----------
rows = []
states = pd.DataFrame(index=df.index)
states["dd"] = dd_full
states["dd20"] = dd20_mask.astype(int)
states["rv_high"] = rv_high.astype(int)

configs = []
for p in [20,60]:
    for c in [0,2]:
        for m in ["full","half"]:
            configs.append(("MA", f"MA{p}_c{c}_{m}", dict(period=p,confirm=c,mapping=m)))
for L in [20,60,120]:
    configs.append(("MOM", f"MOM_L{L}", dict(L=L)))

raw_perf = perf(r); raw_seg = seg_ret(r)
for kind, name, kw in configs:
    pos = ma_gate_pos(**kw) if kind=="MA" else mom_gate_pos(**kw)
    ret, sig = apply_pos(pos)
    pf_full, pf_is, pf_oos = perf(ret), perf(ret.loc[:IS_END]), perf(ret.loc[IS_END:])
    segs = seg_ret(ret)
    ov = overlap(sig<1.0)
    row = {"config":name,"kind":kind,
           "ann":pf_full["ann"],"mdd":pf_full["mdd"],"sharpe":pf_full["sharpe"],"calmar":pf_full["calmar"],
           "whipsaw":whipsaw_of(sig),"whipsaw_yr":round(whipsaw_of(sig)/(len(sig)/252),2),
           "is_ann":pf_is["ann"],"is_mdd":pf_is["mdd"],"is_sharpe":pf_is["sharpe"],
           "oos_ann":pf_oos["ann"],"oos_mdd":pf_oos["mdd"],"oos_sharpe":pf_oos["sharpe"],
           **{f"ov_{k}":v for k,v in ov.items()}, **segs}
    rows.append(row)
    states[f"pos_{name}"] = sig

# ---------- ddc15 same-nav simulation (R-243 C4a mechanics) ----------
navs = df["nav"].values
posv = np.ones(len(navs)); state = 1.0; hwm = navs[0]; trough = navs[0]
for i in range(len(navs)):
    x = navs[i]
    hwm = max(hwm, x)
    if state==1.0:
        if x/hwm-1 <= -0.15:
            state=0.5; trough=x
    else:
        trough = min(trough, x)
        if x >= trough*1.05: state=1.0
    posv[i] = state
pos_ddc = pd.Series(posv, index=df.index)
ret_ddc, sig_ddc = apply_pos(pos_ddc)
pf_full, pf_is, pf_oos = perf(ret_ddc), perf(ret_ddc.loc[:IS_END]), perf(ret_ddc.loc[IS_END:])
ov = overlap(sig_ddc<1.0)
rows.append({"config":"DDC15_sim","kind":"DDC","ann":pf_full["ann"],"mdd":pf_full["mdd"],
    "sharpe":pf_full["sharpe"],"calmar":pf_full["calmar"],"whipsaw":whipsaw_of(sig_ddc),
    "whipsaw_yr":round(whipsaw_of(sig_ddc)/(len(sig_ddc)/252),2),
    "is_ann":pf_is["ann"],"is_mdd":pf_is["mdd"],"is_sharpe":pf_is["sharpe"],
    "oos_ann":pf_oos["ann"],"oos_mdd":pf_oos["mdd"],"oos_sharpe":pf_oos["sharpe"],
    **{f"ov_{k}":v for k,v in ov.items()}, **seg_ret(ret_ddc)})
states["pos_DDC15_sim"] = sig_ddc

# baseline row
rows.insert(0, {"config":"RAW","kind":"BASE","ann":raw_perf["ann"],"mdd":raw_perf["mdd"],
    "sharpe":raw_perf["sharpe"],"calmar":raw_perf["calmar"],"whipsaw":0,"whipsaw_yr":0,
    "is_ann":perf(r.loc[:IS_END])["ann"],"is_mdd":perf(r.loc[:IS_END])["mdd"],"is_sharpe":perf(r.loc[:IS_END])["sharpe"],
    "oos_ann":perf(r.loc[IS_END:])["ann"],"oos_mdd":perf(r.loc[IS_END:])["mdd"],"oos_sharpe":perf(r.loc[IS_END:])["sharpe"],
    **{f"ov_{k}":None for k in overlap(dd20_mask)}, **raw_seg})

# ---------- combo (IS-best MA x IS-best MOM by IS calmar) ----------
mas = [x for x in rows if x["kind"]=="MA"]
moms = [x for x in rows if x["kind"]=="MOM"]
best_ma = max(mas, key=lambda x: x["is_sharpe"]); best_mom = max(moms, key=lambda x: x["is_sharpe"])
pos_combo = states[f"pos_{best_ma['config']}"].clip(upper=states[f"pos_{best_mom['config']}"], axis=0)
ret_cb, sig_cb = apply_pos(states[f"pos_{best_ma['config']}"]*0 + pos_combo)  # pos_combo already in position space; re-derive signal
# NOTE: pos_combo built from signals (already shifted); do not shift again
sig_cb = pos_combo
ret_cb = r*sig_cb
pf_full, pf_is, pf_oos = perf(ret_cb), perf(ret_cb.loc[:IS_END]), perf(ret_cb.loc[IS_END:])
ov = overlap(sig_cb<1.0)
rows.append({"config":f"COMBO_{best_ma['config']}+{best_mom['config']}","kind":"COMBO",
    "ann":pf_full["ann"],"mdd":pf_full["mdd"],"sharpe":pf_full["sharpe"],"calmar":pf_full["calmar"],
    "whipsaw":whipsaw_of(sig_cb),"whipsaw_yr":round(whipsaw_of(sig_cb)/(len(sig_cb)/252),2),
    "is_ann":pf_is["ann"],"is_mdd":pf_is["mdd"],"is_sharpe":pf_is["sharpe"],
    "oos_ann":pf_oos["ann"],"oos_mdd":pf_oos["mdd"],"oos_sharpe":pf_oos["sharpe"],
    **{f"ov_{k}":v for k,v in ov.items()}, **seg_ret(ret_cb)})
states["pos_COMBO"] = sig_cb
best_combo_name = f"COMBO_{best_ma['config']}+{best_mom['config']}"

out = pd.DataFrame(rows)
out.to_csv(OUT_SCAN, index=False)
states.to_csv(OUT_STATES)
summary = {"validate":valid, "best_ma":best_ma["config"], "best_mom":best_mom["config"],
           "best_combo":best_combo_name, "n_rows":len(out),
           "rv_high_days":int(rv_high.sum()), "dd20_days":n_dd20}
json.dump(summary, open(OUT_JSON,"w"), ensure_ascii=False, indent=1)
print("SUMMARY:", json.dumps(summary), flush=True)
print(out[["config","ann","mdd","sharpe","calmar","whipsaw_yr","is_mdd","oos_mdd","ov_coverage_of_dd20","ov_precision_dd20","ov_jaccard_dd20"]].to_string(), flush=True)
print("DONE", flush=True)
