#!/usr/bin/env python3
# task-0414: 五分段稳定性 + 五分位分组单调性 + 达线判定
import json
import numpy as np, pandas as pd
OUT = "/home/noname/quant-evolve/results/work/r0414"
d = np.load(f"{OUT}/panel.npz", allow_pickle=True)
F, R, MASK = d["F"], d["R"], d["MASK"]
months = [str(x) for x in d["months"]]
n_codes, n_month, _ = F.shape
SIGN = np.array([-1.0,-1.0,1.0,1.0])

def seg_stats(ic):
    ic = np.asarray(ic, float); n = len(ic)
    k = n//5
    segs = []
    for s in range(5):
        x = ic[s*k:(s+1)*k] if s<4 else ic[4*k:]
        segs.append(round(float(np.nanmean(x)/np.nanstd(x,ddof=1)),4))
    return segs

def quintile_panel(score_fn, tag):
    """逐月五分位(按score), 组内等权 mean(R[m+1]); 返回 Q1..Q5 时序均值"""
    qm = np.zeros((n_month,5)); cnt = np.zeros(n_month)
    for m in range(n_month-1):
        ok = MASK[:,m] & np.isfinite(R[:,m+1])
        if ok.sum()<100: continue
        sc = score_fn(m, ok)
        if sc is None: continue
        q = pd.Series(sc).rank(pct=True).values
        r = R[ok,m+1]
        for qi in range(5):
            lo,hi = qi/5,(qi+1)/5
            sel = (q>lo)&(q<=hi) if qi<4 else (q>lo)&(q<=1.0)
            qm[m,qi] = np.nanmean(r[sel]) if sel.sum()>10 else np.nan
        cnt[m]=1
    valid = cnt>0
    avg = np.nanmean(qm[valid],axis=0)
    mono = np.all(np.diff(avg)>0)
    return [round(float(x),5) for x in avg], bool(mono), int(valid.sum())

res = {}
# ranksum 基准
rk_ic = pd.read_csv(f"{OUT}/ranksum4_ic_monthly.csv")
def rs_fn(m, ok):
    X4 = F[ok,m,:4]*SIGN
    rk = pd.DataFrame(X4).rank(pct=True)
    return rk.mean(axis=1).values
avg_rs, mono_rs, nm_rs = quintile_panel(rs_fn, "ranksum4")
res["ranksum4"] = {"icir":float(rk_ic["ic"].mean()/rk_ic["ic"].std(ddof=1)),
    "mean_ic":float(rk_ic["ic"].mean()),"n_months":int(len(rk_ic)),
    "segments_icir":seg_stats(rk_ic["ic"]),"quintiles_avg_nextret":avg_rs,"quintile_monotonic":mono_rs}
for tag in ["D","O"]:
    try:
        ic = pd.read_csv(f"{OUT}/lgbm_ic_monthly_{tag}.csv")
    except Exception:
        continue
    def lgb_fn(m, ok, tag=tag):
        f = f"{OUT}/lgbm_scores_{tag}_{months[m]}.npy"
        import os
        if not os.path.exists(f): return None
        sc = np.load(f)  # 与 ok 顺序一致由训练脚本保证(同 MASK[:,m]&finite)
        return sc
    avg_q, mono_q, nm_q = quintile_panel(lgb_fn, tag)
    res[f"lgbm_{tag}"] = {"icir":float(ic["ic"].mean()/ic["ic"].std(ddof=1)),
        "mean_ic":float(ic["ic"].mean()),"n_months":int(len(ic)),
        "segments_icir":seg_stats(ic["ic"]),"quintiles_avg_nextret":avg_q,"quintile_monotonic":mono_q}
    res[f"lgbm_{tag}"]["delta_icir_vs_ranksum"] = res[f"lgbm_{tag}"]["icir"] - res["ranksum4"]["icir"]
json.dump(res, open(f"{OUT}/analysis.json","w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
