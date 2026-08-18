#!/usr/bin/env python3
import os
# -*- coding: utf-8 -*-
"""task-0361 补充分析：分段胜率 / 微盘载体敏感性 / SPREAD 阈值诊断（读 out/signal_series.parquet）"""
import json
import numpy as np
import pandas as pd

DATA = "/root/tv2data"
df = pd.read_parquet(os.path.join(DATA, "out", "signal_series.parquet")) if False else pd.read_parquet(DATA + "/out/signal_series.parquet")
df.index = pd.to_datetime(df.index)
out = {}

# 1) SPREAD 阈值诊断
for c in ["breadth", "SPREAD5", "SPREAD10", "SPREAD20"]:
    s = df[c]
    out[c] = {"max": round(float(s.max()), 4), "p99": round(float(s.quantile(0.99)), 4),
              "p95": round(float(s.quantile(0.95)), 4),
              "days_ge_085": int((s >= 0.85).sum())}

# 2) 分段子段胜率（B1 / C / REB / FLOW；载体 M 与 M_micro_ew 双口径）
segs = {"2006-2015": ("2006-01-01", "2015-12-31"), "2016-2026": ("2016-01-01", "2026-12-31"),
        "full": ("2006-01-01", "2026-12-31")}
sigs = ["SPREAD5_top", "REB_bottom", "FLOW_pos_cross", "dd60", "dev15", "rsi14", "B1_oversold", "C_crisis"]

def seg_stats(carrier):
    res = {}
    for carrier_name in ([carrier] if isinstance(carrier, str) else carrier):
        M = df[carrier_name]
        fwd15 = M.shift(-15) / M - 1
        res[carrier_name] = {}
        for s in sigs:
            flag = df["flag_" + s]
            for seg, (lo, hi) in segs.items():
                m = (df.index >= lo) & (df.index <= hi)
                v = (flag & pd.Series(m, index=df.index)).values
                idx = np.where(v)[0]
                if len(idx) == 0:
                    res[carrier_name].setdefault(s, {})[seg] = {"n": 0}
                    continue
                brk = np.where(np.diff(idx) > 1)[0]
                starts = np.r_[idx[0], idx[brk + 1]]
                fs = [fwd15.iloc[i] for i in starts if i + 15 < len(df)]
                fs = [f for f in fs if np.isfinite(f)]
                top = s.startswith("SPREAD")
                hits = [(f < 0 if top else f > 0) for f in fs]
                res[carrier_name].setdefault(s, {})[seg] = {
                    "n": len(fs),
                    "win": None if not hits else round(float(np.mean(hits)), 4),
                    "fwd15_mean": None if not fs else round(float(np.mean(fs)), 4),
                }
    return res

out["by_segment_M"] = seg_stats("M")
out["by_segment_Mmicro"] = seg_stats("M_micro_ew")

# 3) 关键 episode 日期清单（SPREAD5_top / C_crisis / B1 前10 / REB 前10 按 fwd15 排序）
eps = pd.read_csv(DATA + "/out/episodes_all.csv")
lists = {}
for s in ["SPREAD5_top", "C_crisis"]:
    sub = eps[eps.signal == s]
    lists[s] = sub.to_dict("records")
for s in ["B1_oversold", "REB_bottom"]:
    sub = eps[eps.signal == s].dropna(subset=["fwd15"])
    lists[s + "_top8_by_fwd15"] = sub.sort_values("fwd15", ascending=False).head(8).to_dict("records")
    lists[s + "_worst5"] = sub.sort_values("fwd15").head(5).to_dict("records")
out["key_episodes"] = lists

# 4) M vs M_micro_ew 基础对比
for c in ["M", "M_micro_ew"]:
    s = df[c].dropna()
    yrs = (s.index[-1] - s.index[0]).days / 365.25
    dd = s / s.cummax() - 1
    out[c + "_stats"] = {"ann": round(float((s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1), 4),
                         "mdd": round(float(dd.min()), 4), "n": len(s)}
r = df[["M", "M_micro_ew"]].pct_change().corr().iloc[0, 1]
out["M_vs_Mmicro_daily_corr"] = round(float(r), 4)

with open(DATA + "/out/supplement.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, indent=1, default=str)[:6000])
