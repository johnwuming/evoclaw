#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r0438 代理验证 v2：年度分块控内存。同 v1 口径（见 proxy_pe.py 头注）。"""
import pandas as pd, numpy as np, json, time, gc
HP = "/home/noname/quant-evolve"
OUT = f"{HP}/results/work/r0438"
t0 = time.time()

f = pd.read_parquet(f"{HP}/data/derived/factor_registry_financial_panel.parquet",
                    columns=["code", "ym", "roe_ttm", "equity", "total_shares"])
f["code"] = f["code"].astype(str).str.zfill(6)
f = f[(f.roe_ttm.notna()) & (f.equity > 0) & (f.total_shares > 0)]
f["np_ttm"] = f.roe_ttm * f.equity
f = f[f.np_ttm != 0]
months = pd.period_range("2005-06", "2026-08", freq="M").astype(str)
parts = []
for c, g in f.groupby("code"):
    s = g.drop_duplicates("ym").set_index("ym")[["np_ttm", "total_shares"]].reindex(months).ffill()
    s["code"] = c
    parts.append(s)
fp = pd.concat(parts).reset_index().rename(columns={"index": "ym"})
fp["total_shares"] = fp.total_shares.astype("float32")
fp["np_ttm"] = fp.np_ttm.astype("float64")
del f, parts; gc.collect()
print(f"[{time.time()-t0:.0f}s] panel ready rows={len(fp)}", flush=True)

daily_rows = []
for Y in range(2014, 2027):
    m = pd.read_parquet(f"{HP}/data/all_stocks_merged.parquet", columns=["date", "code", "volume", "amount"],
                        filters=[("date", ">=", pd.Timestamp(f"{Y}-01-01")), ("date", "<=", pd.Timestamp(f"{Y}-12-31"))])
    m["code"] = m["code"].astype(str).str.zfill(6)
    m = m[m.code.str[:2].isin(["00", "30", "60", "68"]) & (m.volume > 0)]
    m["ym"] = m.date.dt.strftime("%Y-%m")
    d = m.merge(fp, on=["code", "ym"], how="inner")
    del m; gc.collect()
    d = d[(d.np_ttm.notna()) & (d.total_shares > 0)]
    rawpx = (d.amount / d.volume).astype("float64")
    mc = rawpx * d.total_shares.astype("float64")
    ep = d.np_ttm / mc
    ok = (rawpx > 0) & (mc > 0) & np.isfinite(ep)
    dd = pd.DataFrame({"date": d.date[ok], "mc": mc[ok], "ep": ep[ok]})
    del d, rawpx, mc, ep; gc.collect()
    def day_pe(g):
        q = g.mc.quantile(0.20)
        sel = g[g.mc <= q]
        med = sel.ep.median()
        return pd.Series({"pe_eq": (1.0 / med) if med > 0 else np.nan,
                          "n_sel": len(sel), "n_all": len(g)})
    yr = dd.groupby("date").apply(day_pe, include_groups=False).reset_index()
    daily_rows.append(yr)
    print(f"[{time.time()-t0:.0f}s] {Y} done days={len(yr)} med_nsel={yr.n_sel.median()}", flush=True)
    del dd, yr; gc.collect()

daily = pd.concat(daily_rows).sort_values("date").reset_index(drop=True)
daily.to_csv(f"{OUT}/pe_micro_eq_daily.csv", index=False)
print(f"[{time.time()-t0:.0f}s] daily pe rows={len(daily)} nan={int(daily.pe_eq.isna().sum())}", flush=True)

def trail_pct(s, w=756):
    return s.rolling(w, min_periods=w).apply(lambda x: float((x[-1] >= x).mean()), raw=True)

pe3 = pd.read_csv(f"{OUT}/pe_lg_hs300.csv", parse_dates=["日期"])[["日期", "滚动市盈率"]].rename(
    columns={"日期": "date", "滚动市盈率": "pe300"}).set_index("date")
pe1 = pd.read_csv(f"{OUT}/pe_lg_zz1000.csv", parse_dates=["日期"])[["日期", "滚动市盈率"]].rename(
    columns={"日期": "date", "滚动市盈率": "pe1000"}).set_index("date")
sig = daily.dropna(subset=["pe_eq"]).set_index("date")[["pe_eq"]].join(pe3, how="inner").join(pe1, how="inner")
sig["spread_micro"] = np.log(sig.pe_eq / sig.pe300)
sig["spread_1000"] = np.log(sig.pe1000 / sig.pe300)
sig["p1_micro"] = trail_pct(sig.spread_micro)
sig["p1_1000"] = trail_pct(sig.spread_1000)
sig["lv_micro"] = trail_pct(np.log(sig.pe_eq))
sig["lv_1000"] = trail_pct(np.log(sig.pe1000))
me = sig.dropna(subset=["p1_micro", "p1_1000"]).copy()
me.index = pd.to_datetime(me.index)
me.resample("ME").last().to_csv(f"{OUT}/proxy_signal.csv")
meta = {"n_days": len(sig), "first_day": str(sig.index.min().date()), "last_day": str(sig.index.max().date()),
        "n_months": int((~me.resample("ME").last().p1_micro.isna()).sum()),
        "nan_pe_days": int(daily.pe_eq.isna().sum()),
        "median_n_sel": float(daily.n_sel.median())}
json.dump(meta, open(f"{OUT}/proxy_meta.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(meta, ensure_ascii=False), flush=True)
print(f"[{time.time()-t0:.0f}s] ALL DONE", flush=True)
