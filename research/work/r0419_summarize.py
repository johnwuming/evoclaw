#!/usr/bin/env python
# r0419_summarize.py — 从已落盘的月度文件重建 r0419_summary.json + md5 (task-0419)
import json, hashlib, time
import numpy as np, pandas as pd

HP = "/home/noname/quant-evolve"
OUT = f"{HP}/results/r0419"
icdf = pd.read_csv(f"{OUT}/ic_monthly.csv", dtype={"ym": str})
qdf = pd.read_csv(f"{OUT}/quintile_monthly.csv", dtype={"ym": str})
cdf = pd.read_csv(f"{OUT}/xs_corr_monthly.csv", dtype={"ym": str})
ps = pd.read_csv(f"{OUT}/peer_stats.csv", dtype={"ym": str})
fv = pd.read_csv(f"{OUT}/csad_sigma20_monthly.csv", dtype={"ym": str})

ic = icdf["ic"].dropna()
mean_ic, std_ic = ic.mean(), ic.std()
icir, tval = mean_ic / std_ic, mean_ic / std_ic * np.sqrt(len(ic))
n5 = len(ic) // 5
seg5 = {}
for si in range(5):
    chunk = ic.iloc[si * n5:(si + 1) * n5] if si < 4 else ic.iloc[4 * n5:]
    lo = icdf["ym"].iloc[si * n5]; hi = icdf["ym"].iloc[min((si + 1) * n5, len(icdf)) - 1]
    seg5[f"seg{si+1}"] = {"ym": f"{lo}~{hi}", "ic": round(float(chunk.mean()), 5),
                          "icir": round(float(chunk.mean() / chunk.std()), 3),
                          "neg_share": round(float((chunk < 0).mean()), 3), "n": int(len(chunk))}
t3 = len(ic) // 3
ter = {"early": ic.iloc[:t3], "mid": ic.iloc[t3:2 * t3], "late": ic.iloc[2 * t3:]}
qdf["spread"] = qdf["Q5"] - qdf["Q1"]; spr = qdf["spread"].dropna()
red = {p: {"mean_rho": round(float(g["rho"].mean()), 3), "p90_abs": round(float(g["rho"].abs().quantile(0.9)), 3)}
       for p, g in cdf.groupby("peer")}
cat = pd.read_csv(f"{HP}/results/factor_ic_monthly.csv"); cat["ym"] = cat["ym"].astype(str)
myic = icdf.set_index("ym")["ic"]; icc = {}
for f in ["market_cap_log", "avg_amount_20d", "roe_ttm", "volatility_20d", "idiosyncratic_vol", "amihud_illiquidity"]:
    if f in cat.columns:
        j = pd.concat([myic, cat.set_index("ym")[f]], axis=1).dropna()
        if len(j) > 30: icc[f] = round(float(j.corr().iloc[0, 1]), 3)
crow = pd.read_csv(f"{HP}/results/r250/crowding_monthly.csv")
crow = crow.rename(columns={crow.columns[0]: "ym"}); crow["ym"] = crow["ym"].astype(str)
j = pd.concat([myic.rename("ic"), crow.set_index("ym")["shr_roll20"]], axis=1).dropna()
icc["crowding_level"] = round(float(j.corr().iloc[0, 1]), 3) if len(j) > 30 else None
qmean = {f"Q{i}": round(float(qdf[f"Q{i}"].mean()), 5) for i in range(1, 6)}
summary = {
    "task": "task-0419", "factor": "feat_csad_sigma20", "built": time.strftime("%Y-%m-%d %H:%M"),
    "params": {"W_CORR": 120, "W_SIGMA": 20, "TOPN": 20, "CORR_MIN": 0.5, "MIN_PEERS": 5, "MIN_VALID": 100,
               "corr_approx": "nan->0 standardized inner product (valid>=100/120 in window)"},
    "coverage": {"factor_months": int(fv["ym"].nunique()), "ic_months": int(len(ic)),
                 "mean_n": int(icdf["n"].mean()), "mean_nan_share": round(float(icdf["nan_share"].mean()), 4),
                 "ic_ym_range": f"{icdf['ym'].min()}~{icdf['ym'].max()}",
                 "peer_mean": round(float(ps["mean_peers"].mean()), 1),
                 "peer_ge5_share": round(float(ps["share_ge5"].mean()), 3),
                 "pool_n_first_last": [int(ps["pool_n"].iloc[0]), int(ps["pool_n"].iloc[-1])]},
    "ic_profile": {"ic_mean": round(float(mean_ic), 5), "ic_std": round(float(std_ic), 5),
                   "icir": round(float(icir), 3), "t": round(float(tval), 2),
                   "ic_neg_share": round(float((ic < 0).mean()), 3)},
    "segments5": seg5,
    "tertile": {s: {"ic": round(float(c.mean()), 5), "icir": round(float(c.mean() / c.std()), 3)} for s, c in ter.items()},
    "quintiles": {"mean_ret": qmean, "spread_mean": round(float(spr.mean()), 5),
                  "spread_t": round(float(spr.mean() / spr.std() * np.sqrt(len(spr))), 2),
                  "spread_neg_share": round(float((spr < 0).mean()), 3)},
    "redundancy_xs": red, "ic_series_corr": icc,
    "gate": {"threshold": "|ICIR|>=0.25 & segment-stable sign & |rho|<0.6 vs in-service", "icir_pass": bool(abs(icir) >= 0.25)},
}
with open(f"{OUT}/r0419_summary.json", "w") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1, default=str)
md5 = hashlib.md5(open(f"{OUT}/csad_sigma20_monthly.csv", "rb").read()).hexdigest()
open(f"{OUT}/csad_sigma20_monthly.csv.md5", "w").write(md5 + "\n")
print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
