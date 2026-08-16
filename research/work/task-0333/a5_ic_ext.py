#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0333 A5 阶段4前置: 扩展IC数据 (growth/quality/momentum 因子月度IC)
输出: results/a5_ic_monthly_ext.csv (a4d扩展107+9 + A5新增列)
      results/a5_ic_corr_ext.csv
      results/a5_value_ic_monthly.csv
IC口径与W1一致: 月频, spearman, 方向调整(正=按使用方向有预测力)
"""
import os, sys, time
sys.path.insert(0, "/home/noname/quant-evolve/scripts")
os.chdir("/home/noname/quant-evolve")
import numpy as np, pandas as pd
HP = "/home/noname/quant-evolve"; t0 = time.time()

# ---- 基本面因子 (a4d_value_panel: growth/quality/value 已PIT对齐) ----
P = pd.read_parquet(f"{HP}/results/a4d_value_panel.parquet")
P["code"] = P["code"].astype(str).str.zfill(6)
P["ym"] = P["date"].dt.to_period("M").astype(str)

m = pd.read_parquet(f"{HP}/data/all_stocks_merged.parquet", columns=["date","code","close"])
m["code"] = m["code"].astype(str).str.zfill(6)
m["ym"] = pd.to_datetime(m["date"]).dt.to_period("M").astype(str)
mc = m.groupby(["code","ym"])["close"].last().reset_index()
mc["ret"] = mc.groupby("code")["close"].pct_change()  # 同月收益 (W1/a4d口径)

# ---- 动量因子 (ret120/dist250h: 120交易日收益 / 距250日高点) ----
m2 = m.copy()
m2 = m2.sort_values(["code","date"])
m2["ret120"] = m2.groupby("code")["close"].transform(lambda s: s / s.shift(120) - 1.0)
m2["dist250h"] = m2.groupby("code")["close"].transform(lambda s: s / s.rolling(250).max() - 1.0)
mom = m2.dropna(subset=["ret120","dist250h"]).groupby(["code","ym"])[["ret120","dist250h"]].last().reset_index()

FACT = ["revenue_yoy","net_profit_yoy","profit_accel","buf_quality","cf_np_ratio","peg_np","ret120","dist250h"]
DIR  = {"revenue_yoy":1,"net_profit_yoy":1,"profit_accel":1,"buf_quality":1,
        "cf_np_ratio":1,"peg_np":-1,"ret120":1,"dist250h":1}
rows = []
for ymi, g in mc.groupby("ym"):
    ynext = g[["code","ret"]].rename(columns={"ret":"ret_fwd"})
    X = P[P["ym"]==ymi][["code"]+FACT[:6]].merge(ynext, on="code", how="inner")
    X = X.merge(mom[mom["ym"]==ymi][["code","ret120","dist250h"]], on="code", how="left")
    rec = {"ym": str(ymi)}
    for ind in FACT:
        x = X[[ind,"ret_fwd"]].dropna()
        rec[ind] = x[ind].corr(x["ret_fwd"], method="spearman") * DIR[ind] if len(x) >= 30 else np.nan
    rows.append(rec)
df = pd.DataFrame(rows)
df.to_csv(f"{HP}/results/a5_value_ic_monthly.csv", index=False)
print("[1] a5_value_ic_monthly.csv", df.shape, round(time.time()-t0,1), "s", flush=True)

# ---- 扩展月度IC: a4d扩展(107+9) + A5新增列 ----
base = pd.read_csv(f"{HP}/results/a4d_ic_monthly_ext.csv", dtype={"ym": str})
ext = base.merge(df, on="ym", how="left")
ext.to_csv(f"{HP}/results/a5_ic_monthly_ext.csv", index=False)
print("[2] a5_ic_monthly_ext.csv", ext.shape, flush=True)

cols = list(ext.columns[1:])
corr = ext[cols].corr()
corr.round(4).to_csv(f"{HP}/results/a5_ic_corr_ext.csv")
print("[3] a5_ic_corr_ext.csv", corr.shape, flush=True)
print("A5_IC_EXT_DONE", round(time.time()-t0,1), "s", flush=True)
