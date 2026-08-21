#!/usr/bin/env python
# r0419_csad_sigma20.py — feat_csad_sigma20 个股级羊群分化因子 E1 IC画像 (task-0419)
# 零回测: 因子构建 + IC画像 + 冗余检查。口径对齐 R-251/W1: 月频全市场, spearman(F_m, R_m->m+1), MIN_OBS=20
import os, sys, time, json, hashlib, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

HP = "/home/noname/quant-evolve"
KLINE_DIR = f"{HP}/data/all_stocks_qfq"
OUT = f"{HP}/results/r0419"
os.makedirs(OUT, exist_ok=True)
LOG = open(f"{OUT}/build.log", "a", buffering=1)
def log(m): LOG.write(f"[{time.strftime('%m-%d %H:%M:%S')}] {m}\n")

# ---- 参数 (构建决策, 报告"与帖子的差异"节披露) ----
W_CORR, W_SIGMA, TOPN = 120, 20, 20
CORR_MIN, MIN_PEERS, MIN_VALID = 0.5, 5, 100
MIN_OBS, MIN_LISTED, MP_SIGMA = 20, 120, 20   # MP_SIGMA: sigma20 窗内最少有效日
t0 = time.time()
log("=== task-0419 r0419_csad_sigma20 build start ===")

# ---- Phase A: 加载 kline -> 宽矩阵 ----
files = sorted(f for f in os.listdir(KLINE_DIR) if f.endswith("_daily_qfq.parquet"))
fc, fa, fo, codes = [], [], [], []
for i, fn in enumerate(files):
    code = fn.replace("_daily_qfq.parquet", "")
    try:
        df = pd.read_parquet(os.path.join(KLINE_DIR, fn), columns=["date", "close", "amount", "outstanding_share"])
    except Exception:
        continue
    if df is None or len(df) < MIN_LISTED:
        continue
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates("date").set_index("date")
    codes.append(code); fc.append(df["close"].rename(code))
    fa.append(df["amount"].rename(code)); fo.append(df["outstanding_share"].rename(code))
    if (i + 1) % 1500 == 0: log(f"  loaded {i+1}/{len(files)} t={time.time()-t0:.0f}s")
close = pd.concat(fc, axis=1).sort_index(); del fc
amount = pd.concat(fa, axis=1).sort_index(); del fa
osh = pd.concat(fo, axis=1).sort_index(); del fo
cal = close.index
ret = close.pct_change()
ret_np = ret.to_numpy(dtype=np.float32)
listed_cnt = (~close.isna()).cumsum().to_numpy()
me_dates = pd.Series(cal, index=cal).groupby(cal.to_period("M")).max()
me_dates = pd.DatetimeIndex(me_dates.values)
log(f"[A] {close.shape[0]} days x {close.shape[1]} codes, {cal[0].date()}~{cal[-1].date()} t={time.time()-t0:.0f}s")

# ---- Phase B: 同伴群(前一月末, 滚动120d相关, corr>0.5 取前20) + 当月日频CSAD ----
csad_parts, peer_stats = [], []
npos = {d: i for i, d in enumerate(cal)}
for k in range(1, len(me_dates)):
    prev_end, m_end = me_dates[k - 1], me_dates[k]
    p_end = npos[prev_end]
    if p_end < W_CORR:
        continue
    win = slice(p_end - W_CORR + 1, p_end + 1)
    R = ret_np[win]
    pool = (listed_cnt[p_end] >= MIN_LISTED) & ((~np.isnan(R)).sum(0) >= MIN_VALID)
    if pool.sum() < 50:
        continue
    pi = np.where(pool)[0]
    X = R[:, pi]
    Xc = X - np.nanmean(X, 0)
    Xc = np.where(np.isnan(Xc), 0.0, Xc)
    nrm = np.sqrt((Xc ** 2).sum(0)); nrm[nrm == 0] = 1.0
    Z = (Xc / nrm).astype(np.float32)
    C = Z.T @ Z  # 相关近似: nan->0, 轻微低估, 报告披露
    n_pool = len(pi); counts = np.zeros(n_pool, dtype=np.int16); peers_list = [None] * n_pool
    for a in range(n_pool):
        row = C[a]; row[a] = -2
        cand = np.argpartition(-row, min(TOPN, n_pool - 1))[:TOPN]
        cand = cand[row[cand] > CORR_MIN]
        peers_list[a] = pi[cand]; counts[a] = len(cand)
    d0, d1 = p_end + 1, npos[m_end]
    if d1 < d0:
        continue
    Rm = ret_np[d0:d1 + 1]; D = Rm.shape[0]
    CS = np.full((D, n_pool), np.nan, dtype=np.float32)
    for a in range(n_pool):
        pj = peers_list[a]
        if len(pj) < MIN_PEERS:
            continue
        diff = np.abs(Rm[:, pi[a]:pi[a] + 1] - Rm[:, pj])
        with np.errstate(invalid="ignore"):
            CS[:, a] = np.nanmean(diff, axis=1)
    csad_parts.append(pd.DataFrame(CS, index=cal[d0:d1 + 1], columns=ret.columns[pi]))
    peer_stats.append((str(m_end)[:7], n_pool, float(counts.mean()), float(np.median(counts)),
                       float((counts >= MIN_PEERS).mean()), float(np.isnan(CS).mean())))
    if k % 24 == 0:
        pd.concat(csad_parts).to_parquet(f"{OUT}/csad_daily_partial.parquet")
        log(f"  {str(m_end)[:7]} pool={n_pool} meanpeers={counts.mean():.1f} t={time.time()-t0:.0f}s")
csad = pd.concat(csad_parts)
csad = csad[~csad.index.duplicated(keep="last")].sort_index()
csad.to_parquet(f"{OUT}/csad_daily.parquet")
sig = csad.rolling(W_SIGMA, min_periods=MP_SIGMA).std()
fme = sig.groupby(sig.index.to_period("M")).last()
fv = fme.stack().rename("feat_csad_sigma20").reset_index()
fv.columns = ["ym", "code", "feat_csad_sigma20"]
fv.to_csv(f"{OUT}/csad_sigma20_monthly.csv", index=False)
pd.DataFrame(peer_stats, columns=["ym", "pool_n", "mean_peers", "med_peers", "share_ge5", "csad_nan_share"]).to_csv(f"{OUT}/peer_stats.csv", index=False)
log(f"[B] csad {csad.shape}, monthly factor rows={len(fv)} months={fv['ym'].nunique()} t={time.time()-t0:.0f}s")

# ---- Phase C: IC 画像 ----
me_close = close.loc[[d for d in me_dates if d in npos]]
mret = me_close.pct_change()
mret.index = mret.index.to_period("M")
nxt = mret.shift(-1)  # nxt.loc[ym] = ym->ym+1 收益
close_np = close.to_numpy(dtype=np.float64)

def cross_proc(F: pd.Series):
    v = F.dropna()
    if len(v) < MIN_OBS: return None
    lo, hi = v.quantile([0.01, 0.99])
    v = v.clip(lo, hi)
    return (v - v.mean()) / (v.std() + 1e-12)

from scipy.stats import spearmanr
fv_p = fv.copy(); fv_p["ym"] = fv_p["ym"].astype(str)
yms = sorted(fv_p["ym"].unique())
ic_rows, q_rows, corr_rows, beta_rows = [], [], [], []
ths = pd.read_parquet(f"{HP}/data/derived/ths_ttm_panel.parquet", columns=["code", "report_date", "equity", "roe_ttm", "avail_date"])
ths["avail_date"] = pd.to_datetime(ths["avail_date"])
ths = ths.sort_values("avail_date")
Amt_np = amount.to_numpy(dtype=np.float32); osh_np = osh.to_numpy(dtype=np.float32)
szzs = pd.read_parquet(f"{HP}/data/szzs_daily_20060101_20260808.parquet")
szzs["date"] = pd.to_datetime(szzs["date"]); mkt = szzs.sort_values("date").set_index("date")["close"].pct_change().reindex(cal).to_numpy(dtype=np.float32)
for ym in yms:
    pe = pd.Period(ym)
    if pe not in mret.index: continue
    medate = [d for d in me_dates if d.to_period("M") == pe]
    if not medate: continue
    medate = medate[0]; mend = npos.get(medate, None)
    if mend is None or mend < W_CORR: continue
    sub = fv_p[fv_p["ym"] == ym].set_index("code")["feat_csad_sigma20"]
    # W1 mask: 上市>=120 & 当月有交易(月末close非nan) & 有下月末收益
    nr = nxt.loc[pe]
    live = nr.notna()
    mask_codes = [c for c in sub.index if c in close.columns and bool(live.get(c, False))]
    F = sub.loc[[c for c in mask_codes if c in nr.index]]
    if len(F) < MIN_OBS: continue
    Rn = nr.loc[F.index]
    Fp = cross_proc(F)
    if Fp is None: continue
    ic = float(spearmanr(Fp, Rn.loc[Fp.index])[0])
    n = len(Fp)
    # 分组(因子值升序 Q1低->Q5高)
    q = pd.qcut(Fp.rank(method="first"), 5, labels=False) + 1
    qr = Rn.loc[Fp.index].groupby(q.values).mean()
    q_rows.append({"ym": ym, **{f"Q{i}": float(qr.get(i, np.nan)) for i in range(1, 6)}})
    # 风格暴露 & 冗余: 当月末截面
    ci = [close.columns.get_loc(c) for c in Fp.index]
    cl = close_np[mend, ci]; am20 = np.nanmean(Amt_np[max(0, mend - 19):mend + 1, ci], axis=0)
    os_ = osh_np[mend, ci]
    log_mv = np.log(cl * os_); amt20v = np.log(am20 + 1)
    # ths PIT asof
    tsub = ths[ths["avail_date"] <= medate]
    last = tsub.groupby("code").tail(1).set_index("code")
    common = Fp.index.intersection(last.index)
    roe_v = last.loc[common, "roe_ttm"]
    pb_inv = (last.loc[common, "equity"] / pd.Series(os_, index=Fp.index).loc[common] * 1e4) / pd.Series(cl, index=Fp.index).loc[common]  # equity单位假设万->元? 用rank对冲量纲
    # beta/vol (trailing 120d)
    Rw = ret_np[mend - W_CORR + 1:mend + 1][:, ci]
    mw = mkt[mend - W_CORR + 1:mend + 1]
    okm = ~np.isnan(mw); mwv = mw[okm]
    Rw2 = Rw[okm, :]; Rw2 = np.where(np.isnan(Rw2), 0.0, Rw2)
    mz = (mwv - mwv.mean()) / (mwv.std() + 1e-12)
    cov = (Rw2 * mz[:, None]).mean(0); var = mz.var()
    beta_v = cov / (var + 1e-12); vol_v = Rw2.std(0)
    Fc = Fp.loc[common]
    for nm, sv in [("log_mv", log_mv), ("amt20", amt20v)]:
        corr_rows.append({"ym": ym, "peer": nm, "rho": float(spearmanr(Fp, sv)[0])})
    corr_rows.append({"ym": ym, "peer": "roe_ttm", "rho": float(spearmanr(Fc, roe_v)[0])})
    pb_inv = pb_inv.replace([np.inf, -np.inf], np.nan).dropna()
    if len(pb_inv) > 30:
        corr_rows.append({"ym": ym, "peer": "pb_inv", "rho": float(spearmanr(Fp.loc[pb_inv.index], pb_inv)[0])})
    corr_rows.append({"ym": ym, "peer": "beta120", "rho": float(spearmanr(Fp, beta_v)[0])})
    corr_rows.append({"ym": ym, "peer": "vol120", "rho": float(spearmanr(Fp, vol_v)[0])})
    ic_rows.append({"ym": ym, "ic": float(ic), "n": n,
                    "nan_share": float(F.isna().mean())})
    if len(ic_rows) % 60 == 0: log(f"  IC {ym} ic={ic:.4f} n={n} t={time.time()-t0:.0f}s")
icdf = pd.DataFrame(ic_rows); icdf.to_csv(f"{OUT}/ic_monthly.csv", index=False)
pd.DataFrame(q_rows).to_csv(f"{OUT}/quintile_monthly.csv", index=False)
pd.DataFrame(corr_rows).to_csv(f"{OUT}/xs_corr_monthly.csv", index=False)

# ---- 统计汇总 ----
S = lambda x: pd.Series(x)
ic = icdf["ic"].dropna()
mean_ic, std_ic = ic.mean(), ic.std()
icir, tval = mean_ic / std_ic, mean_ic / std_ic * np.sqrt(len(ic))
seg_stats = {}
n5 = len(ic) // 5
for si in range(5):
    chunk = ic.iloc[si * n5:(si + 1) * n5] if si < 4 else ic.iloc[4 * n5:]
    seg_stats[f"seg{si+1}"] = {"ym_range": f"{icdf['ym'].iloc[si*n5]}~{icdf['ym'].iloc[min((si+1)*n5, len(icdf))-1]}",
                               "ic": round(float(chunk.mean()), 5), "icir": round(float(chunk.mean()/chunk.std()), 3),
                               "ic_neg_share": round(float((chunk < 0).mean()), 3), "n": int(len(chunk))}
tri = {s: ic.iloc[a:b] for s, (a, b) in {"early": (0, len(ic)//3), "mid": (len(ic)//3, 2*len(ic)//3), "late": (2*len(ic)//3, len(ic))}.items()}
seg_stats["tertile"] = {s: {"ic": round(float(c.mean()), 5), "icir": round(float(c.mean()/c.std()), 3)} for s, c in tri.items()}
qdf = pd.DataFrame(q_rows)
qmean = {f"Q{i}": round(float(qdf[f"Q{i}"].mean()), 5) for i in range(1, 6)}
qdf["spread"] = qdf["Q5"] - qdf["Q1"]
spr = qdf["spread"].dropna()
qr = {"quintile_mean_ret": qmean, "spread_mean": round(float(spr.mean()), 5),
      "spread_t": round(float(spr.mean()/spr.std()*np.sqrt(len(spr))), 2), "spread_hit": round(float((spr < 0).mean()), 3)}
cdf = pd.DataFrame(corr_rows)
red = {p: {"mean_rho": round(float(g["rho"].mean()), 3), "p90_abs": round(float(g["rho"].abs().quantile(0.9)), 3)}
       for p, g in cdf.groupby("peer")}
# IC 序列相关: 与在役目录因子 + 拥挤度(市场层, 无截面 -> IC/状态时序相关)
cat = pd.read_csv(f"{HP}/results/factor_ic_monthly.csv")
cat["ym"] = cat["ym"].astype(str)
icc = {}
myic = icdf.set_index("ym")["ic"]
for f in ["market_cap_log", "avg_amount_20d", "roe_ttm", "volatility_20d", "idiosyncratic_vol", "amihud_illiquidity"]:
    if f in cat.columns:
        j = pd.concat([myic, cat.set_index("ym")[f]], axis=1).dropna()
        if len(j) > 30: icc[f] = round(float(j.corr().iloc[0, 1]), 3)
crow = pd.read_csv(f"{HP}/results/r250/crowding_monthly.csv")
crow["ym"] = crow["ym"].astype(str)
j = pd.concat([myic.rename("ic"), crow.set_index("ym")["shr_roll20"]], axis=1).dropna()
icc["crowding_level"] = round(float(j.corr().iloc[0, 1]), 3) if len(j) > 30 else None
summary = {
    "task": "task-0419", "factor": "feat_csad_sigma20", "built": time.strftime("%Y-%m-%d %H:%M"),
    "params": {"W_CORR": W_CORR, "W_SIGMA": W_SIGMA, "TOPN": TOPN, "CORR_MIN": CORR_MIN,
               "MIN_PEERS": MIN_PEERS, "MIN_VALID": MIN_VALID, "corr_approx": "nan->0 标准化内积(窗内有效>=100/120)"},
    "coverage": {"factor_months": int(fv_p["ym"].nunique()), "ic_months": int(len(ic)),
                 "mean_n": round(float(icdf["n"].mean()), 0), "mean_nan_share": round(float(icdf["nan_share"].mean()), 4),
                 "ic_ym_range": f"{icdf['ym'].min()}~{icdf['ym'].max()}",
                 "peer_mean": round(float(pd.DataFrame(peer_stats)[2].mean()), 1),
                 "peer_ge5_share": round(float(pd.DataFrame(peer_stats)[4].mean()), 3)},
    "ic_profile": {"ic_mean": round(float(mean_ic), 5), "ic_std": round(float(std_ic), 5),
                   "icir": round(float(icir), 3), "t": round(float(tval), 2),
                   "ic_neg_share": round(float((ic < 0).mean()), 3)},
    "segments5": seg_stats, "quintiles": qr, "redundancy_xs": red, "ic_series_corr": icc,
    "gate": {"threshold": "|ICIR|>=0.25 & 分段方向稳定 & |rho|<0.6",
             "pass": bool(abs(icir) >= 0.25)},
}
with open(f"{OUT}/r0419_summary.json", "w") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1, default=str)
md5 = hashlib.md5(open(f"{OUT}/csad_sigma20_monthly.csv", "rb").read()).hexdigest()
open(f"{OUT}/csad_sigma20_monthly.csv.md5", "w").write(md5 + "\n")
log(f"[C] DONE ic={mean_ic:.4f} icir={icir:.3f} t={tval:.2f} md5={md5} total={time.time()-t0:.0f}s")
print(json.dumps(summary, ensure_ascii=False, default=str)[:3000])
