#!/usr/bin/env python
# task-0576 follow-up: MONTHLY-EXECUTED gate variants (ride a13 monthly rebalance, zero extra whipsaw cost)
import pandas as pd, numpy as np, json

BASE = "/home/noname/quant-evolve"
nav = pd.read_csv(f"{BASE}/results/a13_rsraw_e1f10dz_full_nav.csv", parse_dates=["date"]).set_index("date")
st = pd.read_csv(f"{BASE}/results/p2gate_task0576_states.csv", parse_dates=["date"]).set_index("date")
r = nav["nav"].pct_change().fillna(0.0)
df = nav[["nav"]].join(st, how="inner").sort_index()
r = r.reindex(df.index).fillna(0.0)

SEGMENTS = {
    "seg2015crash": ("2015-06-12","2015-07-08"),
    "seg2015long":  ("2015-06-12","2016-06-30"),
    "seg2024q1":    ("2024-01-02","2024-02-07"),
    "seg2026":      ("2026-05-26","2026-07-22"),
    "seg2014_12":   ("2014-12-01","2014-12-22"),
    "seg2020style": ("2020-09-10","2021-01-13"),
}
IS_END = "2017-12-31"
dd = df["nav"]/df["nav"].cummax()-1
dd20 = dd <= -0.20

def perf(ret):
    navc = (1+ret).cumprod(); n=len(ret)
    dd2 = navc/navc.cummax()-1
    ann = navc.iloc[-1]**(252/n)-1
    vol = ret.std()*np.sqrt(252)
    return {"ann":round(float(ann),4),"mdd":round(float(dd2.min()),4),
            "sharpe":round(float(ann/vol),3),"calmar":round(float(ann/abs(float(dd2.min()))),3)}

def seg_ret(ret):
    return {k: round(float((1+ret.loc[s:e]).prod()-1),4) for k,(s,e) in SEGMENTS.items() if len(ret.loc[s:e])>0}

pos_cols = [c for c in df.columns if c.startswith("pos_")]
# month-end sampled signals -> held constant next month
me = df[pos_cols].resample("ME").last()
me_next = me.shift(1)  # previous month-end state
daily_m = me_next.reindex(df.index, method="ffill").fillna(1.0)

rows=[]
def add(name, sig):
    ret = r*sig
    pf_f, pf_i, pf_o = perf(ret), perf(ret.loc[:IS_END]), perf(ret.loc[IS_END:])
    wh = int((sig.diff().abs()>1e-9).sum())
    A = sig<1.0
    ab=int((A&dd20).sum())
    rows.append({"config":name,"ann":pf_f["ann"],"mdd":pf_f["mdd"],"sharpe":pf_f["sharpe"],"calmar":pf_f["calmar"],
        "whipsaw_yr":round(wh/(len(sig)/252),2),
        "is_ann":pf_i["ann"],"is_mdd":pf_i["mdd"],"oos_ann":pf_o["ann"],"oos_mdd":pf_o["mdd"],"oos_sharpe":pf_o["sharpe"],
        "cov_dd20":round(ab/max(int(dd20.sum()),1),3),"prec_dd20":round(ab/max(int(A.sum()),1),3),
        **seg_ret(ret)})
    return ret

for c in pos_cols:
    add("M_"+c.replace("pos_",""), daily_m[c])

# combo monthly: min(MA20_c0_full, MOM_L20) sampled monthly
combo = daily_m[["pos_MA20_c0_full","pos_MOM_L20"]].min(axis=1)
add("M_COMBO_MA20c0full+MOML20", combo)

out=pd.DataFrame(rows)
out.to_csv(f"{BASE}/results/p2gate_task0576_scan_monthly.csv", index=False)
print(out[["config","ann","mdd","sharpe","calmar","whipsaw_yr","is_mdd","oos_mdd","cov_dd20","prec_dd20","seg2015crash","seg2024q1","seg2026","seg2014_12","seg2020style"]].to_string(), flush=True)
print("DONE")
