#!/usr/bin/env python
# r0422_csad_vol_neutral.py — task-0422: feat_csad_sigma20 波动率中性化残差 IC 裁决（零回测）
# 预登记门槛(不可改): 残差 |ICIR| >= 0.25 → csad 有独立信息(E2 预注册); < 0.25 → 波动率族替代表达(归档)
# 主裁决版 = v2 双中性化(vol20+vol120); v1 单中性化(vol20) 参照; v3 加 idio120 代理 补充参照
# 口径对齐 r0419: W1 池(上市>=120/当月有交易/有下月收益), 去极值 1%/99% + zscore, spearman(F_m, R_m->m+1), MIN_OBS=20
import os, sys, time, json, hashlib, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from scipy.stats import spearmanr

HP = "/home/noname/quant-evolve"
KLINE_DIR = f"{HP}/data/all_stocks_qfq"
R0419 = f"{HP}/results/r0419"
OUT = f"{HP}/results/work/r0422"
os.makedirs(OUT, exist_ok=True)
LOG = open(f"{OUT}/build.log", "a", buffering=1)
def log(m): LOG.write(f"[{time.strftime('%m-%d %H:%M:%S')}] {m}\n")

MIN_LISTED, MIN_OBS = 120, 20
W20, W120, MP20 = 20, 120, 15
DROP_YM = "2026-07"   # 主口径剔除(次月为部分月), 与 r0419 一致
t0 = time.time()
log("=== task-0422 r0422 csad vol-neutral residual IC start ===")

# ---- Phase A: 加载 close (同 r0419, 免 amount/osh) ----
files = sorted(f for f in os.listdir(KLINE_DIR) if f.endswith("_daily_qfq.parquet"))
fc, kept = [], 0
for fn in files:
    code = fn.replace("_daily_qfq.parquet", "")
    try:
        df = pd.read_parquet(os.path.join(KLINE_DIR, fn), columns=["date", "close"])
    except Exception:
        continue
    if df is None or len(df) < MIN_LISTED:
        continue
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates("date").set_index("date")
    fc.append(df["close"].rename(code)); kept += 1
close = pd.concat(fc, axis=1).sort_index(); del fc
cal = close.index
ret = close.pct_change()
ret_np = ret.to_numpy(dtype=np.float32)
me_dates = pd.Series(cal, index=cal).groupby(cal.to_period("M")).max()
me_dates = pd.DatetimeIndex(me_dates.values)
npos = {d: i for i, d in enumerate(cal)}
log(f"[A] close {close.shape} kept={kept} {cal[0].date()}~{cal[-1].date()} t={time.time()-t0:.0f}s")

me_close = close.loc[me_dates]
mret = me_close.pct_change(); mret.index = mret.index.to_period("M")
nxt = mret.shift(-1)

szzs = pd.read_parquet(f"{HP}/data/szzs_daily_20060101_20260808.parquet")
szzs["date"] = pd.to_datetime(szzs["date"])
mkt = szzs.sort_values("date").set_index("date")["close"].pct_change().reindex(cal).to_numpy(dtype=np.float32)

vol20d = ret.rolling(W20, min_periods=MP20).std()

fv = pd.read_csv(f"{R0419}/csad_sigma20_monthly.csv", dtype={"ym": str, "code": str})
fv["ym"] = fv["ym"].astype(str)

def winsor(v):
    lo, hi = v.quantile([0.01, 0.99]); return v.clip(lo, hi)
def zsc(v):
    return (v - v.mean()) / (v.std() + 1e-12)
def ols_res(X, y):
    A = np.column_stack([np.ones(len(y))] + [X[:, j] for j in range(X.shape[1])])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = A @ coef
    e = y - yhat
    r2 = 1.0 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return e, r2

rows, qrows, volrows = [], [], []
for ym in sorted(fv["ym"].unique()):
    pe = pd.Period(ym)
    if pe not in nxt.index:
        continue
    medate = [d for d in me_dates if d.to_period("M") == pe]
    if not medate or medate[0] not in npos:
        continue
    medate = medate[0]; mend = npos[medate]
    if mend < W120:
        continue
    sub = fv[fv["ym"] == ym].set_index("code")["feat_csad_sigma20"]
    nr = nxt.loc[pe]; live = nr.notna()
    F = sub.loc[[c for c in sub.index if c in close.columns and bool(live.get(c, False))]]
    if len(F) < MIN_OBS:
        continue
    v20 = vol20d.loc[medate].reindex(F.index)
    ci = [close.columns.get_loc(c) for c in F.index]
    Rw = ret_np[mend - W120 + 1:mend + 1][:, ci]
    mw = mkt[mend - W120 + 1:mend + 1]
    okm = ~np.isnan(mw)
    mkt_ok = bool(okm.sum() >= 60)          # szzs 起点 2006-01; 不足则 vol120 不做市场 mask
    if mkt_ok:
        Rw2 = Rw[okm, :]; mwv = mw[okm]
    else:
        Rw2 = Rw; mwv = None
    Rw2 = np.where(np.isnan(Rw2), 0.0, Rw2)
    vol120_v = pd.Series(Rw2.std(0), index=F.index)
    if mkt_ok:
        mz = (mwv - mwv.mean()) / (mwv.std() + 1e-12)
        beta_v = (Rw2 * mz[:, None]).mean(0) / (mz.var() + 1e-12)
        idio_v = pd.Series((Rw2 - beta_v[None, :] * mz[:, None]).std(0), index=F.index)
    else:
        idio_v = pd.Series(np.nan, index=F.index)   # v3 缺 2006-03 前月份, 披露
    volrows.append(pd.DataFrame({"ym": ym, "code": F.index, "vol20": v20.values,
                                 "vol120": vol120_v.values, "idio120": idio_v.values}))
    D = pd.DataFrame({"F": F, "v20": v20, "v120": vol120_v}).dropna()
    if len(D) < MIN_OBS:
        continue
    D3 = D.join(idio_v.rename("idio")).dropna()
    Dw = D.apply(winsor)
    Fp = zsc(Dw["F"]); Rn = nr.loc[D.index]
    row = {"ym": ym, "n": int(len(D)), "n3": int(len(D3)),
           "ic_raw": float(spearmanr(Fp, Rn)[0]),
           "rho_vol20": float(spearmanr(Fp, Dw["v20"])[0]),
           "rho_vol120": float(spearmanr(Fp, Dw["v120"])[0])}
    e1, r2_1 = ols_res(Dw[["v20"]].to_numpy(), Dw["F"].to_numpy())
    e2, r2_2 = ols_res(Dw[["v20", "v120"]].to_numpy(), Dw["F"].to_numpy())
    row["r2_v1"], row["r2_v2"] = r2_1, r2_2
    e3, r2_3 = (None, None)
    if len(D3) >= MIN_OBS:
        D3w = D3.apply(winsor)
        e3, r2_3 = ols_res(D3w[["v20", "v120", "idio"]].to_numpy(), D3w["F"].to_numpy())
        Rn3 = nr.loc[D3.index]
        row["r2_v3"] = r2_3
    for tag, e, RR in [("v1", e1, Rn), ("v2", e2, Rn), ("v3", e3, Rn3 if e3 is not None else Rn)]:
        if e is None:
            continue
        ep = pd.Series(e, index=Dw.index if tag != "v3" else D3.index)
        ep = zsc(winsor(ep))
        row[f"ic_res_{tag}"] = float(spearmanr(ep, RR.loc[ep.index])[0])
        q = pd.qcut(ep.rank(method="first"), 5, labels=False) + 1
        qr = RR.loc[ep.index].groupby(q.values).mean()
        for i in range(1, 6):
            qrows.append({"ym": ym, "ver": tag, f"Q{i}": float(qr.get(i, np.nan))})
    rows.append(row)
    if len(rows) % 60 == 0:
        log(f"  {ym} n={len(D)} t={time.time()-t0:.0f}s")

icdf = pd.DataFrame(rows)
icdf.to_csv(f"{OUT}/ic_monthly_residual.csv", index=False)
qdf = pd.DataFrame(qrows)
qdf.to_csv(f"{OUT}/quintile_monthly_residual.csv", index=False)
pd.concat(volrows, ignore_index=True).to_csv(f"{OUT}/vol_panel_monthly.csv", index=False)
log(f"[B] months={len(icdf)} t={time.time()-t0:.0f}s")

# ---- Phase C: 统计 ----
ref = pd.read_csv(f"{R0419}/ic_monthly.csv", dtype={"ym": str})
mrg = icdf.merge(ref[["ym", "ic"]].rename(columns={"ic": "ic_ref"}), on="ym", how="left")
val_corr = float(mrg[["ic_raw", "ic_ref"]].corr().iloc[0, 1])

fic = pd.read_csv(f"{HP}/results/factor_ic_monthly.csv", dtype={"ym": str})
mrg2 = icdf.merge(fic[["ym", "volatility_20d", "idiosyncratic_vol"]], on="ym", how="left")

def stats(ic):
    ic = pd.Series(ic).dropna()
    mean, std = ic.mean(), ic.std()
    return {"n": int(len(ic)), "ic_mean": round(float(mean), 5), "ic_std": round(float(std), 5),
            "icir": round(float(mean / std), 3), "t": round(float(mean / std * np.sqrt(len(ic))), 2),
            "ic_neg_share": round(float((ic < 0).mean()), 3)}

def segstats(col):
    d = icdf[icdf["ym"] != DROP_YM]
    ic = d[col].dropna()
    if len(ic) < 50:
        return None
    n5 = len(ic) // 5
    yms = d.loc[ic.index, "ym"]
    out = {}
    for si in range(5):
        chunk = ic.iloc[si * n5:(si + 1) * n5] if si < 4 else ic.iloc[4 * n5:]
        cy = yms.iloc[si * n5:(si + 1) * n5] if si < 4 else yms.iloc[4 * n5:]
        out[f"seg{si+1}"] = {"range": f"{cy.iloc[0]}~{cy.iloc[-1]}", **stats(chunk)}
    return out

def qstats(tag):
    d = qdf[qdf["ver"] == tag].set_index("ym")
    sp = d["Q5"] - d["Q1"]
    return {"q_mean_next_ret": {f"Q{i}": round(float(d[f"Q{i}"].mean()), 5) for i in range(1, 6)},
            "q5_q1_per_month": round(float(sp.mean()), 5),
            "spread_t": round(float(sp.mean() / sp.std() * np.sqrt(len(sp))), 2),
            "spread_neg_share": round(float((sp < 0).mean()), 3), "n_months": int(len(sp))}

def ver_block(col):
    main = stats(icdf.loc[icdf["ym"] != DROP_YM, col])
    allm = stats(icdf[col])
    return {"main_excl_2026-07": main, "incl_partial_2026-07": allm,
            "segments": segstats(col), "quintiles": qstats(col.replace("ic_res_", ""))}

summary = {
    "task": "task-0422", "factor": "feat_csad_sigma20 (r0419)", "built": time.strftime("%Y-%m-%d %H:%M"),
    "verdict_threshold_abs_icir": 0.25, "main_verdict_version": "v2 dual (vol20+vol120)",
    "versions": {"v1": "neutralize vol20", "v2": "neutralize vol20+vol120 (主裁决)",
                 "v3": "neutralize vol20+vol120+idio120proxy (补充; 2006-03 前无市场数据缺月)"},
    "validation": {
        "raw_ic_vs_r0419_ic_series_corr": round(val_corr, 4),
        "raw_ic_main": stats(icdf.loc[icdf["ym"] != DROP_YM, "ic_raw"]),
        "rho_factor_vol120_mean_p90": [round(float(icdf["rho_vol120"].mean()), 3),
                                        round(float(icdf["rho_vol120"].quantile(0.9)), 3)],
        "rho_factor_vol20_mean": round(float(icdf["rho_vol20"].mean()), 3),
        "target": "r0419 ic=-0.0920/icir=-0.796/n=251; xs rho vol120 mean 0.442 p90 0.574"},
    "raw_ic": {"main": stats(icdf.loc[icdf["ym"] != DROP_YM, "ic_raw"]), "all": stats(icdf["ic_raw"])},
    "v1_vol20": ver_block("ic_res_v1"),
    "v2_vol20_vol120": ver_block("ic_res_v2"),
    "v3_with_idio_proxy": ver_block("ic_res_v3"),
    "regression_r2_mean": {k: round(float(icdf[k].dropna().mean()), 3) for k in ["r2_v1", "r2_v2", "r2_v3"]},
    "ic_series_corr_vs_prod_factors": {
        "res_v2_vs_volatility_20d": round(float(mrg2[["ic_res_v2", "volatility_20d"]].corr().iloc[0, 1]), 3),
        "res_v2_vs_idiosyncratic_vol": round(float(mrg2[["ic_res_v2", "idiosyncratic_vol"]].corr().iloc[0, 1]), 3),
        "res_v1_vs_idiosyncratic_vol": round(float(mrg2[["ic_res_v1", "idiosyncratic_vol"]].corr().iloc[0, 1]), 3),
        "res_v3_vs_idiosyncratic_vol": round(float(mrg2[["ic_res_v3", "idiosyncratic_vol"]].corr().iloc[0, 1], ) if mrg2["ic_res_v3"].notna().sum() > 20 else float("nan"), 3)},
    "coverage": {"months_ic": int(len(icdf)), "mean_n": round(float(icdf["n"].mean()), 0),
                 "mean_n3": round(float(icdf["n3"].mean()), 0)},
}
with open(f"{OUT}/r0422_summary.json", "w") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)

for fn in ["ic_monthly_residual.csv", "quintile_monthly_residual.csv", "vol_panel_monthly.csv",
           "r0422_summary.json", "r0422_csad_vol_neutral.py"]:
    p = os.path.join(OUT, fn)
    os.system(f"md5sum {p} >> {OUT}/md5.txt")
log(f"[C] done. main v2 icir={summary['v2_vol20_vol120']['main_excl_2026-07']['icir']} t={time.time()-t0:.0f}s")
print(json.dumps({"v2_main": summary["v2_vol20_vol120"]["main_excl_2026-07"],
                  "v1_main": summary["v1_vol20"]["main_excl_2026-07"],
                  "validation": summary["validation"]}, ensure_ascii=False))
