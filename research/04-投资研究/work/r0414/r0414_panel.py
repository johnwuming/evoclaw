#!/usr/bin/env python3
# task-0414 阶段A: 自建月频面板(8特征+R+MASK, W1口径) + ranksum4 基准IC
import os, sys, json, time, hashlib
import numpy as np, pandas as pd
from scipy.stats import spearmanr

HP = "/home/noname/quant-evolve"
OUT = f"{HP}/results/work/r0414"
KLINE_DIR = f"{HP}/data/all_stocks_qfq"
MONTHS = pd.period_range("2006-01", "2026-07", freq="M")
FEATS = ["log_mv","log_amt20","pb_inv","roe_ttm","ret_20d","ret_60d","vol_60d","turn_20d"]
MIN_LISTED_DAYS = 120
t0 = time.time()
log = open(f"{OUT}/panel_run.log","w")

# --- PIT 财务: ths_ttm_panel equity/roe_ttm by avail_date ---
ths = pd.read_parquet(f"{HP}/data/derived/ths_ttm_panel.parquet")
ths = ths[["code","report_date","equity","roe_ttm","avail_date"]].copy()
ths["avail_date"] = pd.to_datetime(ths["avail_date"])
ths = ths.dropna(subset=["avail_date"]).sort_values(["code","avail_date"])
ths = ths.drop_duplicates(["code","avail_date"], keep="last")
month_ends = pd.to_datetime([str(p)+"-28" for p in MONTHS])  # as-of 月末锚
fin = {}
for code, g in ths.groupby(ths["code"].astype(str)):
    g = g.sort_values("avail_date")
    ad = g["avail_date"].values
    pos = np.searchsorted(ad, month_ends, side="right") - 1  # 最后一个 avail<=月末
    ok = pos >= 0
    eq = np.full(len(month_ends), np.nan); roe = np.full(len(month_ends), np.nan)
    eq[ok] = g["equity"].values[pos[ok]]
    roe[ok] = g["roe_ttm"].values[pos[ok]]
    fin[code] = (eq, roe)
print(f"PIT fin ready: {len(fin)} codes {time.time()-t0:.0f}s", file=log, flush=True)

files = sorted(f for f in os.listdir(KLINE_DIR) if f.endswith("_daily_qfq.parquet"))
n_codes = len(files); n_month = len(MONTHS)
mpos = {p:i for i,p in enumerate(MONTHS)}
F = np.full((n_codes, n_month, len(FEATS)), np.nan, dtype=np.float32)
R = np.full((n_codes, n_month), np.nan, dtype=np.float32)
MASK = np.zeros((n_codes, n_month), dtype=bool)
codes = []
for i, fn in enumerate(files):
    code = fn.replace("_daily_qfq.parquet",""); codes.append(code)
    try:
        df = pd.read_parquet(os.path.join(KLINE_DIR, fn))
    except Exception: continue
    if df is None or len(df) < 60: continue
    df.columns = [str(c).strip().lower() for c in df.columns]
    need = ["date","close","volume","amount","turnover","outstanding_share"]
    if not all(c in df.columns for c in need): continue
    df["date"] = pd.to_datetime(df["date"]); df = df.sort_values("date").reset_index(drop=True)
    if len(df) < 60: continue
    dym = df["date"].dt.to_period("M")
    # 月末锚行: 每月最后一行
    last_idx_all = df.groupby(dym).tail(1).index
    ym_all = dym.loc[last_idx_all]
    keep = ym_all.isin(mpos).values
    idx_keep = last_idx_all[keep]
    sub = df.loc[idx_keep].copy(); sub["ym"] = ym_all[keep]
    if len(sub)==0: continue
    poss = np.array([mpos[p] for p in sub["ym"]])
    # 特征(全部只用当月末及以前数据)
    amt20 = df["amount"].rolling(20, min_periods=10).mean().loc[idx_keep]
    turn20 = df["turnover"].rolling(20, min_periods=10).mean().loc[idx_keep]
    ret20 = (df["close"]/df["close"].shift(20)-1.0).loc[idx_keep]
    ret60 = (df["close"]/df["close"].shift(60)-1.0).loc[idx_keep]
    dret = df["close"].pct_change()
    vol60 = dret.rolling(60, min_periods=30).std().loc[idx_keep]
    mclose = sub["close"].values.astype(float)
    osh = sub["outstanding_share"].values.astype(float)
    cmv = mclose*osh
    logmv = np.log(np.maximum(cmv,1.0))
    lamt = np.log(np.maximum(amt20.values.astype(float),1.0))
    eq, roe = fin.get(code, (np.full(n_month,np.nan),)*2)[0], fin.get(code, (None,None))[1]
    eqv = (fin[code][0] if code in fin else np.full(n_month, np.nan))[poss]
    roev = (fin[code][1] if code in fin else np.full(n_month, np.nan))[poss]
    with np.errstate(divide="ignore", invalid="ignore"):
        pb_inv = np.where((eqv>0)&(cmv>0), eqv/np.where(cmv>0,cmv,np.nan), np.nan)  # =1/pb, PIT
    vals = [logmv, lamt, pb_inv, roev, ret20.values, ret60.values, vol60.values, turn20.values]
    for k,v in enumerate(vals):
        F[i, poss, k] = np.asarray(v, dtype=np.float32)
    # 月收益
    mser = pd.Series(mclose, index=sub["ym"].values)
    cres = mser.reindex(MONTHS)
    rets = cres.pct_change().values
    R[i, poss] = rets[poss]
    # MASK (W1口径)
    cdays = df.assign(n=1).groupby(dym)["n"].sum().reindex(MONTHS).cumsum().fillna(0)
    mvols = df.groupby(dym)["volume"].sum().reindex(MONTHS).fillna(0)
    valid = (cdays.values[poss]>=MIN_LISTED_DAYS)&(mclose>0)&np.isfinite(mclose)&(mvols.values[poss]>0)
    MASK[i, poss] = valid
    if (i+1)%1000==0: print(f"{i+1}/{n_codes} {time.time()-t0:.0f}s", file=log, flush=True)

codes_arr = np.array(codes)
np.savez_compressed(f"{OUT}/panel.npz", F=F, R=R, MASK=MASK, months=np.array([str(p) for p in MONTHS]),
                    codes=codes_arr, feats=np.array(FEATS))
md5 = hashlib.md5(open(f"{OUT}/panel.npz","rb").read()).hexdigest()
nmask = MASK.sum()
cov = {f: float(np.isfinite(F[:,:,k])[MASK].mean()) for k,f in enumerate(FEATS)}
json.dump({"n_codes":int(n_codes),"n_month":int(n_month),"mask_rows":int(nmask),
           "feature_coverage_in_mask":cov,"md5_panel":md5,
           "months":f"{MONTHS[0]}~{MONTHS[-1]}","runtime_sec":round(time.time()-t0,1)},
          open(f"{OUT}/panel_meta.json","w"), ensure_ascii=False, indent=1)

# --- ranksum4 基准 IC (同口径) ---
SIGN = np.array([-1.0,-1.0,1.0,1.0])  # log_mv neg, amt20 neg, pb_inv pos, roe pos
ic_rows = []
for m in range(n_month-1):
    rnext = R[:,m+1]
    ok = MASK[:,m] & np.isfinite(rnext)
    if ok.sum()<20: continue
    comp = np.full(ok.sum(), np.nan)
    X4 = F[ok, m, :4]*SIGN  # (n,4)
    rk = pd.DataFrame(X4).rank(pct=True)
    comp = rk.mean(axis=1).values
    okf = np.isfinite(comp)
    if okf.sum()<20: continue
    rho,_ = spearmanr(comp[okf], rnext[ok][okf])
    ic_rows.append({"ym":str(MONTHS[m]),"ic":round(float(rho),6),"n":int(okf.sum())})
pd.DataFrame(ic_rows).to_csv(f"{OUT}/ranksum4_ic_monthly.csv", index=False)
ic = np.array([r["ic"] for r in ic_rows])
json.dump({"n_months":len(ic),"mean_ic":float(np.nanmean(ic)),
           "icir":float(np.nanmean(ic)/np.nanstd(ic,ddof=1)),
           "ic_positive":float(np.mean(ic>0))},
          open(f"{OUT}/ranksum4_summary.json","w"), indent=1)
print(f"DONE {time.time()-t0:.0f}s mask={nmask} ranksum_icir={np.nanmean(ic)/np.nanstd(ic,ddof=1):.4f}", file=log, flush=True)
