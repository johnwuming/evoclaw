#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t0579_merged_ruling.py — task-0579 微盘P2趋势闸合并裁决复算（纯只读研究，零改在役）
Qa: MA20 日频闸（zz500, confirm=0, full/half）净改善，成本主口径=在役 cost_model v2，敏感性=平坦15/30bp
Qb: 闸 × ddc15 叠加 vs 各自单独（两层仓位变更对称按 v2 计价）
Qc: 全期 + WF 双窗 OOS + 五痛段 → E2 预注册合并裁决依据
新产物仅 results/t0579_*；脚本与日志在本工作副本目录。
"""
import os, sys, json, math, bisect
import numpy as np
import pandas as pd

sys.path.insert(0, "/home/noname/quant-evolve/scripts")
from cost_model_v2 import estimate_cost

HP = "/home/noname/quant-evolve"
R = os.path.join(HP, "results")
OUT = os.path.join(HP, "work_tmp_task0579")
KLINE = os.path.join(HP, "data", "all_stocks_qfq")
DAYS = 243.0
CAP = 1e7
os.makedirs(OUT, exist_ok=True)

def log(*a): print("[t0579]", *a, flush=True)
def savej(obj, name):
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=str)
    log("saved", name)

# ---------------- 数据 ----------------
nav_raw = pd.read_csv(os.path.join(R, "a13_rsraw_e1f10dz_full_nav.csv"), parse_dates=["date"]).set_index("date")["nav"].astype(float)
cal = nav_raw.index
r = nav_raw.pct_change().fillna(0.0)
log("nav loaded", nav_raw.shape, nav_raw.index[0].date(), nav_raw.index[-1].date())

def load_close(name):
    df = pd.read_parquet(os.path.join(HP, "data", name))
    if not isinstance(df.index, pd.DatetimeIndex):
        for c in df.columns:
            if "date" in str(c).lower() or "日期" in str(c):
                df = df.set_index(c); break
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
    cols = [c for c in df.columns if "close" in str(c).lower()]
    assert cols, f"no close col in {name}"
    return df[cols[0]].astype(float)

zz = load_close("zz500_daily_20060101_20260808.parquet").reindex(cal).ffill()

hold = pd.read_csv(os.path.join(R, "a13_rsraw_e1f10dz_full_holdings.csv"), parse_dates=["date"])
hold = hold[hold["num_target"].fillna(0) > 0]
reb_dates = sorted(hold["date"].tolist())
hold_map = {row["date"]: [c for c in str(row["target"]).split("|") if c] for _, row in hold.iterrows()}
all_codes = sorted({c for v in hold_map.values() for c in v})
log("holdings: %d reb dates, %d unique codes" % (len(reb_dates), len(all_codes)))

KL = {}
n_missing = 0
for c in all_codes:
    p = os.path.join(KLINE, c + ".parquet")
    if not os.path.exists(p):
        KL[c] = None; n_missing += 1; continue
    df = pd.read_parquet(p)
    dcol = next((x for x in df.columns if "日期" in str(x) or "date" in str(x).lower()), None)
    acol = next((x for x in df.columns if str(x) == "成交额" or "amount" in str(x).lower()), None)
    if dcol is None or acol is None:
        KL[c] = None; n_missing += 1; continue
    s = df.set_index(pd.to_datetime(df[dcol]))[acol].astype(float).sort_index()
    KL[c] = (s.index.values.astype("datetime64[ns]").astype(np.int64), s.values)
log("klines loaded, missing=%d" % n_missing)

def adv20(code, d):
    v = KL.get(code)
    if v is None: return np.nan
    di, av = v
    dd = np.int64(pd.Timestamp(d).value)   # ns since epoch，与 di 同型
    pos = int(np.searchsorted(di, dd, side="right"))
    if pos < 10: return np.nan
    win = av[max(0, pos - 20):pos]
    return float(np.nanmean(win)) if len(win) >= 10 else np.nan

# ---------------- 信号与状态 ----------------
ma20 = zz.rolling(20).mean()
S = pd.Series(np.where(ma20.notna(), (zz >= ma20).astype(float), 1.0), index=cal)
gate_full = S.shift(1).fillna(1.0)                 # 0/1
gate_half = (0.5 + 0.5 * S).shift(1).fillna(1.0)   # 0.5/1

def ddc_sim(r_stream):
    """引擎语义复刻（E1 同款）：当日先按 P=1 结算，再按 cur_dd 切换状态"""
    rv_ = r_stream.values
    n = len(rv_); posd = 1.0; nav = 1.0; peak = 1.0; out = np.empty(n)
    for i in range(n):
        nav *= (1.0 + rv_[i] * posd)
        peak = max(peak, nav)
        cur_dd = nav / peak - 1.0
        if posd > 0.999 and cur_dd <= -0.15:
            posd = 0.5
        elif posd < 0.999 and cur_dd >= -0.05:
            posd = 1.0
        out[i] = posd
    return pd.Series(out, index=r_stream.index)

ONES = pd.Series(1.0, index=cal)
CONFIGS = {
    "RAW": ONES,
    "DDC15": None,  # 占位，下面统一生成
    "GATE_FULL": gate_full,
    "GATE_HALF": gate_half,
}

def build(P_gate):
    r_cfg = r * P_gate
    ddc = ddc_sim(r_cfg)
    P = P_gate * ddc
    return {"r_cfg": r_cfg, "ddc": ddc, "P": P, "nav_gross": (1.0 + r_cfg * ddc).cumprod()}

cfgs = {}
cfgs["RAW"] = {"r_cfg": r, "ddc": ONES, "P": ONES, "nav_gross": nav_raw / nav_raw.iloc[0]}
cfgs["DDC15"] = build(ONES)
cfgs["GATE_FULL"] = build(gate_full)
cfgs["GATE_HALF"] = build(gate_half)
cfgs["GATE_FULL_DDC15"] = build(gate_full)      # P 同 build 内（gate×ddc）
cfgs["GATE_HALF_DDC15"] = build(gate_half)
log("configs built")

# ---------------- 成本应用 ----------------
def apply_cost(cfg, mode):
    """mode: none | v2 | flat15 | flat30；返回 (nav_net, cost_series, n_fallback)"""
    P, nav_g = cfg["P"], cfg["nav_gross"]
    if mode == "none":
        return nav_g.copy(), pd.Series(0.0, index=cal), 0
    dP = P.diff().fillna(0.0)
    cost = pd.Series(0.0, index=cal)
    n_fb = 0
    switch = dP[dP.abs() > 1e-12].index
    for d in switch:
        loc = cal.get_loc(d)
        if loc == 0: continue
        dpv = abs(float(dP.loc[d]))
        if dpv < 1e-9: continue
        if mode.startswith("flat"):
            cf = dpv * (0.0015 if mode == "flat15" else 0.0030)
        else:
            prev_d = cal[loc - 1]
            ri = bisect.bisect_right(reb_dates, prev_d) - 1
            if ri < 0: continue
            codes = hold_map[reb_dates[ri]]
            n_ = len(codes)
            if n_ == 0: continue
            w = 1.0 / n_
            port_val = float(nav_g.iloc[loc - 1]) * CAP
            side = "sell" if dP.loc[d] < 0 else "buy"
            tot = 0.0
            for c in codes:
                a = adv20(c, prev_d)
                est = estimate_cost(dpv * w * port_val, a, side=side)
                if est is None:
                    tot += 0.0005 * w; n_fb += 1   # 引擎兜底：legacy 一半（单边5bp）
                else:
                    tot += est["total_bps"] / 1e4 * w
            cf = min(tot, 0.05)
        cost.loc[d] = cf
    nav_net = nav_g * (1.0 - cost).cumprod()
    return nav_net, cost, n_fb

# ---------------- 指标 ----------------
def metrics(nav):
    ret = nav.pct_change().dropna()
    yrs = len(ret) / DAYS
    ann = (nav.iloc[-1] / nav.iloc[0]) ** (1.0 / yrs) - 1.0
    mdd = float((nav / nav.cummax() - 1.0).min())
    vol = float(ret.std() * math.sqrt(DAYS))
    return {"ann": round(float(ann), 4), "mdd": round(mdd, 4),
            "calmar": round(float(ann) / abs(mdd), 3) if mdd < 0 else None,
            "sharpe": round(float(ann) / vol, 3) if vol > 0 else None}

def sub_metrics(nav, d0, d1):
    x = nav.loc[d0:d1]
    if len(x) < 30: return None
    yrs = len(x) / DAYS
    ann = (x.iloc[-1] / x.iloc[0]) ** (1.0 / yrs) - 1.0
    mdd = float((x / x.cummax() - 1.0).min())
    return {"ann": round(float(ann), 4), "mdd": round(mdd, 4),
            "calmar": round(float(ann) / abs(mdd), 3) if mdd < 0 else None}

SEGS = {"E2015": ("2015-06-16", "2016-06-30"), "E201412": ("2014-12-01", "2015-01-05"),
        "E2020style": ("2020-09-10", "2021-02-10"), "E2024Q1": ("2024-01-02", "2024-02-29"),
        "E2026": ("2026-05-26", "2026-08-14")}
OOS = {"OOS1_2016_2021": ("2016-01-01", "2021-12-31"), "OOS2_2022_202608": ("2022-01-01", "2026-08-14")}

# ---------------- 主循环 ----------------
rows = []
series_audit = {"nav_raw": cfgs["RAW"]["nav_gross"]}
for name, cfg in cfgs.items():
    P = cfg["P"]; dP = P.diff().fillna(0.0)
    yrs = len(cal) / DAYS
    diag = {"switches_yr": round(float((dP != 0).sum()) / yrs, 2),
            "turnover_yr": round(float(dP.abs().sum()) / yrs, 1)}
    for mode in ["none", "v2", "flat15", "flat30"]:
        navn, cost, nfb = apply_cost(cfg, mode)
        m = metrics(navn)
        cdrag = round(float(cost.sum()) / yrs * 100, 3)
        row = {"config": name, "mode": mode, **m, **diag, "cost_pp_yr": cdrag, "n_fallback": nfb}
        for on, (d0, d1) in OOS.items():
            row[on] = sub_metrics(navn, d0, d1)
        for sk, (d0, d1) in SEGS.items():
            row["seg_" + sk] = sub_metrics(navn, d0, d1)["mdd"] if sub_metrics(navn, d0, d1) else None
        rows.append(row)
        if mode in ("none", "v2"):
            series_audit["nav_%s_%s" % (name, mode)] = navn
            if mode == "v2":
                series_audit["cost_%s_v2" % name] = cost
    log("config done", name)

tbl = pd.DataFrame(rows)
tbl.to_csv(os.path.join(OUT, "t0579_merged_ruling_table.csv"), index=False)
pd.DataFrame(series_audit).to_csv(os.path.join(OUT, "t0579_series_audit.csv"))
log("table + series saved")

# ---------------- 摘要 JSON ----------------
def g(config, mode, field):
    m = tbl[(tbl["config"] == config) & (tbl["mode"] == mode)].iloc[0]
    return m[field]

summary = {
    "anchors": {
        "raw_mdd_full": g("RAW", "none", "mdd"),
        "raw_ann_full": g("RAW", "none", "ann"),
        "gate_full_gross": {"ann": g("GATE_FULL", "none", "ann"), "mdd": g("GATE_FULL", "none", "mdd"), "e1_ref": {"ann": 0.1917, "mdd": -0.1551}},
        "gate_half_gross": {"ann": g("GATE_HALF", "none", "ann"), "mdd": g("GATE_HALF", "none", "mdd"), "e1_ref": {"ann": 0.2143, "mdd": -0.2043}},
        "ddc15_sim": {"ann": g("DDC15", "none", "ann"), "mdd": g("DDC15", "none", "mdd"), "e1_ref_mdd": -0.2529},
        "gate_full_switches_yr": g("GATE_FULL", "none", "switches_yr"),
    },
    "qa_cost": {},
    "qb_overlay": {},
    "qc_oos": {},
}
for cname in ["GATE_FULL", "GATE_HALF"]:
    summary["qa_cost"][cname] = {
        "gross": {"ann": g(cname, "none", "ann"), "mdd": g(cname, "none", "mdd"), "calmar": g(cname, "none", "calmar")},
        "v2": {"ann": g(cname, "v2", "ann"), "mdd": g(cname, "v2", "mdd"), "calmar": g(cname, "v2", "calmar"), "cost_pp_yr": g(cname, "v2", "cost_pp_yr")},
        "flat15": {"ann": g(cname, "flat15", "ann"), "mdd": g(cname, "flat15", "mdd"), "cost_pp_yr": g(cname, "flat15", "cost_pp_yr")},
        "flat30": {"ann": g(cname, "flat30", "ann"), "mdd": g(cname, "flat30", "mdd"), "cost_pp_yr": g(cname, "flat30", "cost_pp_yr")},
        "raw_ref": {"ann": g("RAW", "none", "ann"), "mdd": g("RAW", "none", "mdd"), "calmar": g("RAW", "none", "calmar")},
    }
for cname in ["DDC15", "GATE_FULL", "GATE_HALF", "GATE_FULL_DDC15", "GATE_HALF_DDC15"]:
    summary["qb_overlay"][cname] = {
        "gross": {"ann": g(cname, "none", "ann"), "mdd": g(cname, "none", "mdd"), "calmar": g(cname, "none", "calmar")},
        "v2": {"ann": g(cname, "v2", "ann"), "mdd": g(cname, "v2", "mdd"), "calmar": g(cname, "v2", "calmar"), "cost_pp_yr": g(cname, "v2", "cost_pp_yr")},
        "OOS1_v2": g(cname, "v2", "OOS1_2016_2021"),
        "OOS2_v2": g(cname, "v2", "OOS2_2022_202608"),
    }
summary["qc_oos"] = {c: {"v2_%s" % k: g(c, "v2", k) for k in OOS} for c in
                     ["RAW", "DDC15", "GATE_FULL", "GATE_HALF", "GATE_FULL_DDC15", "GATE_HALF_DDC15"]}
summary["segs_v2_mdd"] = {c: {sk: g(c, "v2", "seg_" + sk) for sk in SEGS} for c in
                          ["RAW", "DDC15", "GATE_FULL", "GATE_HALF", "GATE_FULL_DDC15", "GATE_HALF_DDC15"]}
savej(summary, "t0579_merged_ruling.json")
log("ALL DONE")
