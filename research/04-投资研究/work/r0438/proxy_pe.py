#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r0438 代理验证：自算微盘等权 PE（市值后20% EP中位数倒数）→ 同式价差信号
R-270 §二.3.b 前置。PIT: factor_registry_financial_panel（pit_disclosure_map usable_from 对齐，
merge_asof backward + 月度 ffill），np_ttm = roe_ttm*equity，total_shares 同面板。
市值 = merged amount/volume（未复权 VWAP）× total_shares。主板前缀 {00,30,60,68}。
输出: r0438/pe_micro_eq_daily.csv, r0438/proxy_signal.csv
"""
import pandas as pd, numpy as np, json, time
HP = "/home/noname/quant-evolve"
OUT = f"{HP}/results/work/r0438"
t0 = time.time()

# ---- 财务面板（PIT 月度）----
f = pd.read_parquet(f"{HP}/data/derived/factor_registry_financial_panel.parquet",
                    columns=["code", "ym", "roe_ttm", "equity", "total_shares"])
f["code"] = f["code"].astype(str).str.zfill(6)
f = f[(f.roe_ttm.notna()) & (f.equity > 0) & (f.total_shares > 0)]
f["np_ttm"] = f.roe_ttm * f.equity
f = f[f.np_ttm != 0]
print(f"[{time.time()-t0:.0f}s] panel filtered rows={len(f)} codes={f.code.nunique()}", flush=True)

# 月度网格内 code 内 ffill（面板 ym 为可得月，直接最近 ym<=当月亦 PIT；这里先做 ym 全网格 ffill）
months = pd.period_range("2005-06", "2026-08", freq="M").astype(str)
parts = []
for c, g in f.groupby("code"):
    s = g.drop_duplicates("ym").set_index("ym")[["np_ttm", "total_shares"]]
    s = s.reindex(months).ffill()
    s["code"] = c
    parts.append(s)
fp = pd.concat(parts).reset_index().rename(columns={"index": "ym"})
print(f"[{time.time()-t0:.0f}s] panel expanded rows={len(fp)}", flush=True)

# ---- 日频行情 ----
m = pd.read_parquet(f"{HP}/data/all_stocks_merged.parquet", columns=["date", "code", "volume", "amount"])
m["code"] = m["code"].astype(str).str.zfill(6)
m = m[m.date >= pd.Timestamp("2013-01-01")]
m = m[m.code.str[:2].isin(["00", "30", "60", "68"])]
m["ym"] = m.date.dt.strftime("%Y-%m")
m = m[m.volume > 0]
print(f"[{time.time()-t0:.0f}s] merged rows={len(m)} codes={m.code.nunique()}", flush=True)

d = m.merge(fp, on=["code", "ym"], how="inner")
d = d[(d.np_ttm.notna()) & (d.total_shares > 0)]
d["rawpx"] = d.amount / d.volume
d = d[d.rawpx > 0]
d["mc"] = d.rawpx * d.total_shares
d["ep"] = d.np_ttm / d.mc
d = d[(d.mc > 0) & np.isfinite(d.ep)]
print(f"[{time.time()-t0:.0f}s] joined rows={len(d)}", flush=True)

# ---- 每日：市值后 20% 的 EP 中位数倒数 ----
def day_pe(g):
    q = g.mc.quantile(0.20)
    sel = g[g.mc <= q]
    med = sel.ep.median()
    return pd.Series({"pe_eq": (1.0 / med) if med > 0 else np.nan,
                      "n_sel": len(sel), "n_all": len(g)})
daily = d.groupby("date").apply(day_pe, include_groups=False).reset_index()
daily.to_csv(f"{OUT}/pe_micro_eq_daily.csv", index=False)
print(f"[{time.time()-t0:.0f}s] daily pe done rows={len(daily)} "
      f"nan_pe_days={int(daily.pe_eq.isna().sum())}", flush=True)

# ---- 同式价差信号 ----
def trail_pct(s, w=756):
    return s.rolling(w, min_periods=w).apply(lambda x: float((x[-1] >= x).mean()), raw=True)

pe3 = pd.read_csv(f"{OUT}/pe_lg_hs300.csv", parse_dates=["日期"])
pe3 = pe3[["日期", "滚动市盈率"]].rename(columns={"日期": "date", "滚动市盈率": "pe300"}).set_index("date")
pe1 = pd.read_csv(f"{OUT}/pe_lg_zz1000.csv", parse_dates=["日期"])
pe1 = pe1[["日期", "滚动市盈率"]].rename(columns={"日期": "date", "滚动市盈率": "pe1000"}).set_index("date")

sig = daily.dropna(subset=["pe_eq"]).set_index("date")[["pe_eq"]].join(pe3, how="inner").join(pe1, how="inner")
sig["spread_micro"] = np.log(sig.pe_eq / sig.pe300)
sig["spread_1000"] = np.log(sig.pe1000 / sig.pe300)
sig["p1_micro"] = trail_pct(sig.spread_micro)
sig["p1_1000"] = trail_pct(sig.spread_1000)
sig["lv_micro"] = trail_pct(np.log(sig.pe_eq))
sig["lv_1000"] = trail_pct(np.log(sig.pe1000))
me = sig.dropna(subset=["p1_micro", "p1_1000"]).copy()
me.index = pd.to_datetime(me.index)
me_m = me.resample("ME").last()
me_m.to_csv(f"{OUT}/proxy_signal.csv")
meta = {"n_days": len(sig), "first_day": str(sig.index.min().date()), "last_day": str(sig.index.max().date()),
        "n_months": len(me_m), "first_month": str(me_m.index.min().date()), "last_month": str(me_m.index.max().date()),
        "nan_pe_days": int(daily.pe_eq.isna().sum()),
        "median_n_sel": float(daily.n_sel.median())}
json.dump(meta, open(f"{OUT}/proxy_meta.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(meta, ensure_ascii=False), flush=True)
print(f"[{time.time()-t0:.0f}s] ALL DONE", flush=True)
