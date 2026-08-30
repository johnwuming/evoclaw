#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t0576_e1_combo_gate.py — task-0576 E1 组合增量画像（纯只读研究，工作副本脚本）
组合闸 = 微盘指数(等权代理 M_micro_ew / zz500) MA 趋势状态闸 × 大小盘价差动量(zz500/hs300 20日动量)
判门 = 相对现役 q3z 择时门(MA15_base 日频代理) + ddc15(0.15/0.5/0.05) 的增量
产出(全部落 HP ~/quant-evolve/work_tmp_task0576/)：
  t0576_overlap.json / t0576_grid_full.csv / t0576_baselines.json / t0576_wf.json / t0576_series_top.csv
不修改 results/ 内任何在役文件。
"""
import os, json, math
import numpy as np
import pandas as pd

HP = "/home/noname/quant-evolve"
OUT = os.path.join(HP, "work_tmp_task0576")
R = os.path.join(HP, "results")
os.makedirs(OUT, exist_ok=True)
DAYS = 243.0

def log(*a): print("[t0576]", *a, flush=True)

def save_json(obj, name):
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=str)
    log("saved", name)

# ---------------- load ----------------
nav = pd.read_csv(os.path.join(R, "a13_rsraw_e1f10dz_full_nav.csv"), parse_dates=["date"]).set_index("date")
nav_a13 = nav["nav"].astype(float)
nav_ddc15 = pd.read_csv(os.path.join(R, "a15_ddc15_full_nav.csv"), parse_dates=["date"]).set_index("date")["nav"].astype(float)
pos_q3z_raw = pd.read_csv(os.path.join(R, "timing_v2/a12_pos_micro.csv"), parse_dates=["date"]).set_index("date")["MA15_base"].astype(float)

sig = pd.read_parquet(os.path.join(R, "timing_v2/signal_series.parquet"))
if not isinstance(sig.index, pd.DatetimeIndex):
    try:
        sig.index = pd.to_datetime(sig.index)
    except Exception:
        sig.index = pd.to_datetime(sig[sig.columns[0]])
micro_raw = sig["M_micro_ew"].astype(float)

def load_close(name):
    df = pd.read_parquet(os.path.join(HP, "data", name))
    if not isinstance(df.index, pd.DatetimeIndex):
        for c in df.columns:
            if "date" in str(c).lower() or "time" in str(c).lower():
                df = df.set_index(c); break
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
    cols = [c for c in df.columns if "close" in str(c).lower()]
    assert cols, f"no close col in {name}: {list(df.columns)}"
    return df[cols[0]].astype(float)

hs_raw = load_close("hs300_daily_20060101_20260808.parquet")
zz_raw = load_close("zz500_daily_20060101_20260808.parquet")
log("loaded a13=%s ddc15=%s micro=%s hs=%s zz=%s q3z=%s" % (nav_a13.shape, nav_ddc15.shape, micro_raw.shape, hs_raw.shape, zz_raw.shape, pos_q3z_raw.shape))

cal = nav_a13.index
def to_cal(s, tag):
    x = s.reindex(cal).ffill()
    log("align %-9s first=%s last=%s" % (tag, x.first_valid_index().date(), x.last_valid_index().date()))
    return x

micro = to_cal(micro_raw, "micro_ew"); zz = to_cal(zz_raw, "zz500"); hs = to_cal(hs_raw, "hs300"); pq = to_cal(pos_q3z_raw, "MA15_base")

r_a13 = nav_a13.pct_change().fillna(0.0)
dd_raw = nav_a13 / nav_a13.cummax() - 1.0
dd20 = (dd_raw <= -0.20)
log("dd20 days =", int(dd20.sum()))

# ---------------- RV (R-250 口径复刻) ----------------
lr = np.log(micro)
rv20 = lr.diff().rolling(20).std() * math.sqrt(252)
rv_q = rv20.rolling(756, min_periods=250).quantile(0.7).shift(1)
rv_hi = (rv20 > rv_q).fillna(False)

# 与 r250/rv_monthly.csv 月末状态比对
rv_match = None
try:
    rvm = pd.read_csv(os.path.join(R, "r250/rv_monthly.csv"), index_col=0)
    rvm.index = pd.to_datetime(rvm.index.astype(str))
    me = rv_hi.groupby(rv_hi.index.to_period("M")).apply(lambda x: x.iloc[-1])
    me.index = me.index.to_timestamp()
    common = rvm.index.intersection(me.index)
    ref = (rvm.loc[common, "rv_state"] == "high").values
    mine = me.loc[common].values.astype(bool)
    rv_match = float((ref == mine).mean())
    log("RV monthly state match vs r250: %.3f over %d months" % (rv_match, len(common)))
except Exception as e:
    log("rv_monthly compare failed:", e)

# ---------------- 信号 ----------------
ratio = zz / hs
mom20 = ratio.pct_change(20)
mom60 = ratio.pct_change(60)
G20 = np.where(mom20.notna(), (mom20 >= 0).astype(float), 1.0)
G20 = pd.Series(G20, index=cal)
G60 = np.where(mom60.notna(), (mom60 >= 0).astype(float), 1.0)
G60 = pd.Series(G60, index=cal)

def confirm_state(raw_state, K):
    s = raw_state.astype(int); n = len(s)
    if K <= 0:
        return s.copy()
    out = np.empty(n, dtype=int); cur = s[0]; out[0] = cur; cnt = 0
    for i in range(1, n):
        if s[i] == cur:
            cnt = 0
        else:
            cnt += 1
            if cnt >= K:
                cur = s[i]; cnt = 0
        out[i] = cur
    return out

def trend_state(px, nper):
    ma = px.rolling(nper).mean()
    s = np.where(ma.notna(), (px >= ma).astype(float), 1.0)  # 暖机中性满仓
    return pd.Series(s, index=cal)

def map_pos(S, G, kind):
    S = np.asarray(S, dtype=float); G = np.asarray(G, dtype=float)
    if kind == "bin_half":
        p = np.where(S >= 0.5, 1.0, 0.0)
    elif kind == "tri":
        p = (S + G) / 2.0
    elif kind == "floor":
        p = np.where(S >= 0.5, 1.0, 0.5)
        p = p * np.where(G >= 0.5, 1.0, 0.5)
    else:
        raise ValueError(kind)
    return pd.Series(p, index=cal)

def gate_nav(pos):
    return (1.0 + r_a13 * pos.shift(1).fillna(1.0)).cumprod()

def metrics(series):
    ret = series.pct_change().dropna()
    yrs = len(ret) / DAYS
    ann = (series.iloc[-1] / series.iloc[0]) ** (1.0 / yrs) - 1.0
    mdd = float((series / series.cummax() - 1.0).min())
    vol = float(ret.std() * math.sqrt(DAYS))
    shp = ann / vol if vol > 0 else None
    cal_ = ann / abs(mdd) if mdd < 0 else None
    return {"ann": round(float(ann), 4), "mdd": round(mdd, 4), "calmar": round(cal_, 3) if cal_ else None,
            "sharpe": round(shp, 3) if shp else None, "vol": round(vol, 4)}

def seg_stat(series, d0, d1):
    x = series.loc[d0:d1]
    if len(x) < 2:
        return None
    return {"mdd": round(float((x / x.cummax() - 1.0).min()), 4), "ret": round(float(x.iloc[-1] / x.iloc[0] - 1.0), 4)}

SEGS = {"E2015": ("2015-06-16", "2016-06-30"), "E201412": ("2014-12-01", "2015-01-05"),
        "E2020style": ("2020-09-10", "2021-02-10"), "E2024Q1": ("2024-01-02", "2024-02-29"),
        "E2026": ("2026-05-26", "2026-08-14")}

def gate_diag(pos):
    d = pos.diff().fillna(0.0)
    return {"changes": int((d != 0).sum()), "turnover_abs": round(float(d.abs().sum()), 1),
            "cost_ann_est": round(float(d.abs().sum() * 0.0015 / (len(pos) / DAYS)), 4), "mean_pos": round(float(pos.mean()), 3)}

# ---------------- Stage 1: RV 重叠度检验（先于网格） ----------------
S_rep = confirm_state(trend_state(micro, 20).values, 2)          # 代表组合：micro MA20 K=2
G_rep = G20
pos_rep = map_pos(S_rep, G_rep, "tri")
ro_any = pos_rep < 0.999            # 任何降仓日
ro_hard = pos_rep <= 0.5            # 深度降仓日
trend_only = pd.Series(np.where(np.asarray(S_rep) >= 0.5, 1.0, 0.0), index=cal) < 0.999
spread_only = G_rep < 0.5

def ovl(a, b, name_b):
    A, B = a.values.astype(bool), b.values.astype(bool)
    both = (A & B).sum(); jac = both / (A | B).sum() if (A | B).sum() else 0.0
    return {"P(%s|%s)" % (name_b, "X") if False else "p_b_given_a": round(float(B[A].mean()) if A.sum() else None, 3),
            "p_a_given_b": round(float(A[B].mean()) if B.sum() else None, 3),
            "jaccard": round(float(jac), 3), "n_a": int(A.sum()), "n_b": int(B.sum())}

overlap = {
    "rep_combo": "micro MA20 K=2 map_tri; ro_any=pos<1 (n=%d), ro_hard=pos<=0.5 (n=%d)" % (int(ro_any.sum()), int(ro_hard.sum())),
    "rv_hi_days": int(rv_hi.sum()),
    "dd20_days": int(dd20.sum()),
    "ro_any_vs_rvhi": ovl(ro_any, rv_hi, "rvhi"),
    "ro_hard_vs_rvhi": ovl(ro_hard, rv_hi, "rvhi"),
    "rvhi_vs_dd20": ovl(rv_hi, dd20, "dd20"),
    "ro_any_vs_dd20": ovl(ro_any, dd20, "dd20"),
    "ro_hard_vs_dd20": ovl(ro_hard, dd20, "dd20"),
    "trendonly_vs_rvhi": ovl(trend_only, rv_hi, "rvhi"),
    "spreadonly_vs_rvhi": ovl(spread_only, rv_hi, "rvhi"),
    "corr_1pos_vs_rvhi": round(float(np.corrcoef((1 - pos_rep).values, rv_hi.astype(float).values)[0, 1]), 3),
}
# 与现役 q3z 代理的关系（增量关键）
q33 = pq.quantile(1/3.0); q66 = pq.quantile(2/3.0)
q_low = pq <= q33; q_high = pq >= q66
overlap["q3z_terciles"] = {"q33": round(float(q33), 3), "q66": round(float(q66), 3)}
overlap["ro_any_vs_q3z_low"] = ovl(ro_any, q_low, "q3zlow")
overlap["ro_any_given_q3z_high"] = round(float(ro_any[q_high].mean()), 3)  # q3z 高仓时组合闸仍降仓的比例=风格/趋势独立信息
overlap["ro_hard_given_q3z_high"] = round(float(ro_hard[q_high].mean()), 3)
overlap["q3z_mean_on_ro_any"] = round(float(pq[ro_any].mean()), 3)
overlap["q3z_mean_on_ro_off"] = round(float(pq[~ro_any].mean()), 3)
# 分段触发（mean pos）
seg_fire = {}
for k, (d0, d1) in SEGS.items():
    seg_fire[k] = {"pos_rep_mean": round(float(pos_rep.loc[d0:d1].mean()), 3),
                   "q3z_mean": round(float(pq.loc[d0:d1].mean()), 3),
                   "ro_any_pct": round(float(ro_any.loc[d0:d1].mean()), 3)}
overlap["seg_fire"] = seg_fire
save_json(overlap, "t0576_overlap.json")

# ---------------- Stage 2: 网格全期 ----------------
rows = []
pos_store = {}
for tag, px in [("micro", micro), ("zz500", zz)]:
    for nper in [20, 60]:
        S_raw = trend_state(px, nper)
        for K in [0, 1, 2, 3]:
            S = confirm_state(S_raw.values, K)
            for kind in ["bin_half", "tri", "floor"]:
                pos = map_pos(S, G20, kind)
                nv = gate_nav(pos)
                m = metrics(nv); g = gate_diag(pos)
                row = {"ma_tag": tag, "nper": nper, "K": K, "map": kind}
                row.update(m); row.update(g)
                for sk, (d0, d1) in SEGS.items():
                    row["seg_" + sk] = seg_stat(nv, d0, d1)["mdd"] if seg_stat(nv, d0, d1) else None
                rows.append(row)
                pos_store["%s|%d|%d|%s" % (tag, nper, K, kind)] = pos
grid = pd.DataFrame(rows).sort_values("calmar", ascending=False)
grid.to_csv(os.path.join(OUT, "t0576_grid_full.csv"), index=False)
log("grid rows=%d best5:\n%s" % (len(grid), grid.head(5)[["ma_tag", "nper", "K", "map", "ann", "mdd", "calmar"]].to_string()))

# ---------------- 基线与叠加 ----------------
def ddc_sim(r, pos_other, thresh=0.15, reduce_to=0.5, recover=0.05):
    """引擎语义复刻：pos 由前一日 dd 状态决定，作用于当日收益"""
    rv_ = r.values; po = pos_other.reindex(r.index).ffill().values
    n = len(r); posd = 1.0; nav = 1.0; peak = 1.0; out = np.empty(n)
    for i in range(n):
        nav *= (1.0 + rv_[i] * po[i] * posd)
        peak = max(peak, nav)
        cur_dd = nav / peak - 1.0
        if posd > 0.999 and cur_dd <= -thresh:
            posd = reduce_to
        elif posd < 0.999 and cur_dd >= -recover:
            posd = 1.0
        out[i] = posd
    return pd.Series(out, index=r.index)

# ddc 模拟器验证：raw×ddc_sim vs a15_ddc15 实际（a15 自带 q3z，预期有差，另验 stack）
pos_ddc_raw = ddc_sim(r_a13, pd.Series(1.0, index=cal))
nav_sim_ddc_raw = (1 + r_a13 * pos_ddc_raw).cumprod()

nav_q3z = gate_nav(pq)
pos_ddc_base = ddc_sim(r_a13, pq)
nav_stack_base = (1 + r_a13 * pq * pos_ddc_base).cumprod()

base = {
    "raw": {"metrics": metrics(nav_a13), "diag": {"mean_pos": 1.0}, "segs": {k: seg_stat(nav_a13, *v) for k, v in SEGS.items()}},
    "q3z_proxy_only": {"metrics": metrics(nav_q3z), "diag": gate_diag(pq), "segs": {k: seg_stat(nav_q3z, *v) for k, v in SEGS.items()}},
    "ddc15_actual_a15": {"metrics": metrics(nav_ddc15), "segs": {k: seg_stat(nav_ddc15, *v) for k, v in SEGS.items()},
                          "note": "a15_ddc15_full 实际回测（自带 q3z×EW-MA200 择时）"},
    "sim_ddc_on_raw": {"metrics": metrics(nav_sim_ddc_raw), "diag": gate_diag(pos_ddc_raw),
                        "segs": {k: seg_stat(nav_sim_ddc_raw, *v) for k, v in SEGS.items()}},
    "stack_base_q3z_plus_ddcsim": {"metrics": metrics(nav_stack_base), "diag": gate_diag(pq * pos_ddc_base),
                                    "segs": {k: seg_stat(nav_stack_base, *v) for k, v in SEGS.items()}},
    "ddc_sim_validator_note": "sim(stack≈a15) 对比见 baselines['stack_vs_a15_gap']",
}
# stack_base vs a15_ddc15 全期差异（代理保真度参考）
b = base["stack_base_q3z_plus_ddcsim"]["metrics"]; a = base["ddc15_actual_a15"]["metrics"]
base["stack_vs_a15_gap"] = {"d_ann": round(b["ann"] - a["ann"], 4), "d_mdd": round(b["mdd"] - a["mdd"], 4)}
save_json(base, "t0576_baselines.json")

# ---------------- Stage 3: 叠加候选（top 组合 + 全组合择优） ----------------
top5 = grid.head(5)
stack_rows = []
for _, gr in top5.iterrows():
    key = "%s|%d|%d|%s" % (gr["ma_tag"], int(gr["nper"]), int(gr["K"]), gr["map"])
    pos = pos_store[key]
    pos_ddc = ddc_sim(r_a13, pq * pos)
    nv = (1 + r_a13 * pq * pos * pos_ddc).cumprod()
    stack_rows.append({"combo": key, **metrics(nv), "diag": gate_diag(pq * pos * pos_ddc),
                        "segs": {k: seg_stat(nv, *v) for k, v in SEGS.items()}})
sb = base["stack_base_q3z_plus_ddcsim"]["metrics"]
for sr in stack_rows:
    sr["d_mdd_vs_stack_base"] = round(sr["mdd"] - sb["mdd"], 4)
    sr["d_ann_vs_stack_base"] = round(sr["ann"] - sb["ann"], 4)
    sr["d_calmar_vs_stack_base"] = round(sr["calmar"] - sb["calmar"], 3)
save_json({"stack_base_metrics": sb, "stack_comb": stack_rows}, "t0576_stack_comb.json")

# ---------------- Stage 4: Walk-forward ----------------
def calmar_is(pos, d0, d1):
    nv = gate_nav(pos).loc[d0:d1]
    if len(nv) < 100: return -9.0
    ret = nv.pct_change().dropna(); yrs = len(ret) / DAYS
    ann = (nv.iloc[-1] / nv.iloc[0]) ** (1 / yrs) - 1.0
    mdd = float((nv / nv.cummax() - 1.0).min())
    return ann / abs(mdd) if mdd < 0 else -9.0

WF = [("WF1", "2006-01-04", "2015-12-31", "2016-01-01", "2021-12-31"),
      ("WF2", "2006-01-04", "2021-12-31", "2022-01-01", "2026-08-14")]
wf_out = []
for wname, is0, is1, o0, o1 in WF:
    best, best_c = None, -9.0
    for key, pos in pos_store.items():
        c = calmar_is(pos, is0, is1)
        if c > best_c:
            best_c, best = c, key
    pos = pos_store[best]
    nv_o = gate_nav(pos).loc[o0:o1]
    sb_o = nav_stack_base.loc[o0:o1]
    pos_ddc_o = ddc_sim(r_a13.loc[o0:o1], (pq * pos).loc[o0:o1])
    nv_stack_o = (1 + r_a13.loc[o0:o1] * pq.loc[o0:o1] * pos.loc[o0:o1] * pos_ddc_o).cumprod()
    wf_out.append({"wf": wname, "is_window": [is0, is1], "oos_window": [o0, o1],
                    "selected": best, "is_calmar": round(best_c, 3),
                    "oos_comb_only": {"metrics": metrics(nv_o), "segs": {k: seg_stat(nv_o, *v) for k, v in SEGS.items() if seg_stat(nv_o, *v)}},
                    "oos_stack_base": {"metrics": metrics(sb_o)},
                    "oos_stack_comb": {"metrics": metrics(nv_stack_o)}})
    log("WF done", wname, best)
save_json({"walk_forward": wf_out}, "t0576_wf.json")

# ---------------- Series 落盘（溯源用） ----------------
best_key = grid.iloc[0]
bkey = "%s|%d|%d|%s" % (best_key["ma_tag"], int(best_key["nper"]), int(best_key["K"]), best_key["map"])
pos_best = pos_store[bkey]
pos_ddc_best = ddc_sim(r_a13, pq * pos_best)
ser = pd.DataFrame({
    "nav_raw": nav_a13, "nav_q3z": nav_q3z, "nav_stack_base": nav_stack_base,
    "nav_stack_comb_best": (1 + r_a13 * pq * pos_best * pos_ddc_best).cumprod(),
    "nav_ddc15_actual": nav_ddc15, "pos_MA15_base": pq,
    "pos_comb_best": pos_best, "pos_ddc_base": pos_ddc_base, "pos_ddc_comb": pos_ddc_best,
    "dd_raw": dd_raw, "rv_hi": rv_hi.astype(float),
}, index=cal)
ser.to_csv(os.path.join(OUT, "t0576_series_top.csv"))
log("series saved; best combo =", bkey)
log("ALL DONE")
