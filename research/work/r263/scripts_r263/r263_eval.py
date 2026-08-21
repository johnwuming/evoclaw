#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r263_eval.py — task-0426 [R-263 §十.5] 判门 G1/G2/G3 + 全窗口指标落盘 e2_results.json
门槛(R-263 §五, 一字不改):
  G0(前置): r263_g0_w0 vs r263_g0_orig max|Δnav|<1e-12; g0_orig 4dp 血统锚警报(vs 22.39%/-33.55%, 0.1pp)
  G1 主门: W-full ann>=0.2209 且 W-full MDD>=-0.3455
  G2 增量门: locked(2006-01~2024-06) 复合IC ICIR(5f,w) - ICIR(4f) > 0; ΔIC均值副指标
  G3 holdout 红旗(披露不否决): holdout |ICIR(5f)| < 0.5*full |ICIR(5f)| → 红旗(用户知情后才可进评分制)
复合IC口径: dump 的引擎最终排序分(加权秩和+e1惩罚, pct-rank, csad 逆序) × 次持有期收益 spearman,
  池=引擎合格池(_ok 过滤后全池), MIN_OBS=20; 末日调仓无完整次月 → 不入 IC 序列(披露)
窗口 NAV 口径沿 R-253: 终点统一截 2026-08-13(最后真实 mark 公共日), ann=(1+total)^(365.25/days)-1
选择规则(§五): W-full ann 最高 → w 小者 → MDD 优者
"""
import os, json, hashlib
import pandas as pd, numpy as np
from scipy.stats import spearmanr

HP = "/home/noname/quant-evolve"
RESULT = os.path.join(HP, "results")
W263 = os.path.join(HP, "results/work/r263")
KLINE_DIR = f"{HP}/data/all_stocks_qfq"

REF_TAG = "a13_rsraw_e1f10dz"
TRUNC_END = "2026-08-13"
LOCK_SPLIT = pd.Timestamp("2024-07-01")
MIN_OBS = 20
G1_ANN_TH, G1_MDD_TH = 0.2209, -0.3455
G3_HALVE = 0.5
GRID = [("IT-R263-01", "r263_m1_w03", "M1.1", 0.3),
        ("IT-R263-02", "r263_m1_w05", "M1.2", 0.5)]

def md5f(p): return hashlib.md5(open(p, "rb").read()).hexdigest()

def load_nav(tag):
    df = pd.read_csv(os.path.join(RESULT, "%s_full_nav.csv" % tag), parse_dates=["date"]).set_index("date")
    return df["nav"].astype(float).sort_index()[:pd.Timestamp(TRUNC_END)]

def wmetrics(nav, s=None, e=None):
    seg = nav[(pd.Timestamp(s) if s else nav.index[0]):][:pd.Timestamp(e) if e else None].dropna()
    total = seg.iloc[-1] / seg.iloc[0] - 1.0
    years = (seg.index[-1] - seg.index[0]).days / 365.25
    ann = (1 + total) ** (1 / years) - 1 if years > 0 else float("nan")
    dd = seg / seg.cummax() - 1.0
    dr = seg.pct_change().dropna()
    return {"start": str(seg.index[0].date()), "end": str(seg.index[-1].date()),
            "n_days": int(len(seg)), "total_ret": round(float(total), 4),
            "ann": round(float(ann), 4), "mdd": round(float(dd.min()), 4),
            "mdd_date": str(dd.idxmin().date()),
            "sharpe": round(float(dr.mean() / dr.std() * np.sqrt(252)), 3) if len(dr) > 2 else None}

def parse_set(s):
    if not isinstance(s, str) or not s.strip():
        return set()
    return set(x for x in s.split("|") if x)

# ---------------- 复合 IC 序列 ----------------
def load_close_matrix():
    files = sorted(f for f in os.listdir(KLINE_DIR) if f.endswith("_daily_qfq.parquet"))
    fc = []
    for fn in files:
        code = fn.replace("_daily_qfq.parquet", "")
        try:
            df = pd.read_parquet(os.path.join(KLINE_DIR, fn), columns=["date", "close"])
        except Exception:
            continue
        if df is None or len(df) < 120:
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").drop_duplicates("date").set_index("date")
        fc.append(df["close"].rename(code))
    close = pd.concat(fc, axis=1).sort_index()
    return close

def composite_ic(tag, close):
    """dump → 每调仓日 spearman(最终排序分, 次持有期收益); 末日无完整次月不计"""
    dmp = pd.read_parquet(os.path.join(W263, "dump_%s.parquet" % tag))
    dmp["date"] = pd.to_datetime(dmp["date"])
    dates = sorted(dmp["date"].unique())
    nxt_date = {d: dates[i + 1] for i, d in enumerate(dates[:-1])}
    rows = []
    for d, sub in dmp.groupby("date", sort=True):
        d2 = nxt_date.get(d)
        if d2 is None:
            rows.append({"date": d, "ic": np.nan, "n": 0, "note": "last_no_fwd"})
            continue
        if d2 not in close.index or d not in close.index:
            rows.append({"date": d, "ic": np.nan, "n": 0, "note": "no_close"})
            continue
        p0 = close.loc[d]; p1 = close.loc[d2]
        fwd = (p1 / p0 - 1.0).reindex(sub["code"].values)
        sc = pd.Series(sub["score"].values, index=sub["code"].values)
        m = pd.DataFrame({"sc": sc, "fwd": fwd}).dropna()
        if len(m) < MIN_OBS:
            rows.append({"date": d, "ic": np.nan, "n": int(len(m)), "note": "min_obs"})
            continue
        rows.append({"date": d, "ic": float(spearmanr(m["sc"], m["fwd"])[0]), "n": int(len(m)), "note": ""})
    return pd.DataFrame(rows)

def ic_stats(icdf, mask):
    ic = icdf.loc[mask, "ic"].dropna()
    if len(ic) < 5:
        return {"n": int(len(ic)), "ic_mean": None, "icir": None}
    m, s = float(ic.mean()), float(ic.std())
    return {"n": int(len(ic)), "ic_mean": round(m, 5), "ic_std": round(s, 5), "icir": round(m / s, 4)}

def overlap_stats(tag):
    df_t = pd.read_csv(os.path.join(RESULT, "%s_full_holdings.csv" % tag), parse_dates=["date"])
    df_r = pd.read_csv(os.path.join(RESULT, "%s_full_holdings.csv" % REF_TAG), parse_dates=["date"])
    rt = df_r.set_index("date")["target"]
    jac, ov = [], []
    for _, row in df_t.iterrows():
        d = row["date"]
        if d not in rt.index:
            continue
        a, b = parse_set(row["target"]), parse_set(rt.loc[d])
        if not b:
            continue
        jac.append(len(a & b) / len(a | b))
        ov.append(len(a & b) / len(b))
    return {"n_dates": len(jac), "jaccard_mean": round(float(np.mean(jac)), 4),
            "jaccard_min": round(float(np.min(jac)), 4),
            "overlap_over_base_mean": round(float(np.mean(ov)), 4)}

def mjson(tag):
    return json.load(open(os.path.join(RESULT, "%s_full_metrics.json" % tag)))

# ---------------- 主流程 ----------------
out = {"task": "task-0426", "date": "2026-08-21", "pre_registration": "R-263",
       "n_trials": 2,
       "engine": "a13/a15 runner 同参复用 + R263 第5因子注入(ext_specs 追加, 引擎文件零改动)",
       "thresholds": {"G1_full_ann_min": G1_ANN_TH, "G1_full_mdd_min": G1_MDD_TH,
                      "G2_locked_icir_increment": ">0 (vs 4f)", "G3_holdout_halve": G3_HALVE},
       "window_convention": {"nav_trunc_end": TRUNC_END,
                             "note": "R-253 纪律: 双方最后真实 mark 公共日; locked=2006-01~2024-06; holdout=2024-07-01→"}}

# 参照系(在役旧产物 + 同数据基准)
nav_ref = load_nav(REF_TAG)
nav_g0o = load_nav("r263_g0_orig")
out["reference"] = {
    "in_service_tag": REF_TAG,
    "in_service_windows": {"full": wmetrics(nav_ref), "holdout": wmetrics(nav_ref, "2024-07-01")},
    "g0_orig_same_data": {"full": wmetrics(nav_g0o), "holdout": wmetrics(nav_g0o, "2024-07-01")},
}
rf = out["reference"]["in_service_windows"]
rfo = out["reference"]["g0_orig_same_data"]
ref_ok = (abs(rf["full"]["ann"] - 0.2239) <= 5e-4 and abs(rf["full"]["mdd"] + 0.3355) <= 5e-4
          and abs(rf["holdout"]["ann"] - 0.2574) <= 5e-4)
out["reference_crosscheck_vs_R263"] = {
    "pass": bool(ref_ok),
    "expect": {"full_ann": 0.2239, "full_mdd": -0.3355, "holdout_ann": 0.2574},
    "note": "在役旧产物 qfq 微漂移 ≤1.4e-07(R-253 已证), 4dp 不变"}

# G0
nav_g0 = load_nav("r263_g0_w0")
same_idx = nav_g0.index.equals(nav_g0o.index)
dmax = float(np.abs(nav_g0.values - nav_g0o.values).max()) if same_idx else None
al = nav_g0.reindex(nav_ref.index)
drift = float(np.abs(al.values - nav_ref.values).max())
mO = mjson("r263_g0_orig")
a_diff = abs(mO["annual_return"] - 0.2239) * 100
m_diff = abs(mO["max_drawdown"] + 0.3355) * 100
out["g0"] = {"basis": "同数据实现层对拍: R263注入(w=0) vs 原a9路径(r263_g0_orig), 同数据同截断",
             "nav_md5_w0": md5f(os.path.join(RESULT, "r263_g0_w0_full_nav.csv")),
             "nav_md5_orig": md5f(os.path.join(RESULT, "r263_g0_orig_full_nav.csv")),
             "dates_equal": bool(same_idx), "n_days": int(len(nav_g0)),
             "max_abs_nav_diff": dmax, "pass": bool(same_idx and dmax is not None and dmax < 1e-12),
             "bloodline_4dp": {"g0_orig_ann": mO["annual_return"], "g0_orig_mdd": mO["max_drawdown"],
                               "ann_diff_pp": round(a_diff, 4), "mdd_diff_pp": round(m_diff, 4),
                               "alert": bool(a_diff > 0.1 or m_diff > 0.1)},
             "drift_vs_old_artifact_max": drift,
             "note": "G0 不入台账(R-253 先例); drift 量级沿 R-253 披露(qfq 重写微漂移+端点伪影)"}

# 复合 IC(需 close 矩阵, ~1min)
print("loading close matrix...", flush=True)
close = load_close_matrix()
ic4 = composite_ic("r263_g0_w0", close)     # w=0 → 4因子复合分(池与分数=在役同构)
ic4.to_csv(os.path.join(W263, "ic_composite_4f.csv"), index=False)
full_mask_4 = ic4["ic"].notna()
st4 = {"full": ic_stats(ic4, full_mask_4),
       "locked": ic_stats(ic4, ic4["date"] < LOCK_SPLIT),
       "holdout": ic_stats(ic4, ic4["date"] >= LOCK_SPLIT)}
out["ic_4f"] = st4
print("4f IC done:", st4, flush=True)

# 两点网格
grid = []
for exp_id, tag, tid, w in GRID:
    nav = load_nav(tag)
    wf = wmetrics(nav)
    wh = wmetrics(nav, "2024-07-01")
    mF = mjson(tag)
    # G2/G3: 5f 复合 IC
    ic5 = composite_ic(tag, close)
    ic5.to_csv(os.path.join(W263, "ic_composite_%s.csv" % tag), index=False)
    st5 = {"full": ic_stats(ic5, ic5["ic"].notna()),
           "locked": ic_stats(ic5, ic5["date"] < LOCK_SPLIT),
           "holdout": ic_stats(ic5, ic5["date"] >= LOCK_SPLIT)}
    d_icir = (st5["locked"]["icir"] - st4["locked"]["icir"]
              if st5["locked"]["icir"] is not None and st4["locked"]["icir"] is not None else None)
    m5, m4 = st5["locked"]["ic_mean"], st4["locked"]["ic_mean"]
    d_ic_mean = round(m5 - m4, 5) if m5 is not None and m4 is not None else None
    g1 = bool(wf["ann"] >= G1_ANN_TH and wf["mdd"] >= G1_MDD_TH)
    g2 = bool(d_icir is not None and d_icir > 0)
    halve = (st5["holdout"]["icir"] is not None and st5["full"]["icir"] is not None
             and abs(st5["holdout"]["icir"]) < G3_HALVE * abs(st5["full"]["icir"]))
    covd = json.load(open(os.path.join(W263, "cov_%s.json" % tag)))
    covs = [h / t if t else 0 for h, t in covd.values()]
    w5n = float(np.sqrt(1 + 1 + 0.49 + 0.09 + w * w))
    rec = {"exp_id": exp_id, "tag": tag, "trial": tid, "csad_w": w,
           "nav_md5": md5f(os.path.join(RESULT, "%s_full_nav.csv" % tag)),
           "windows": {"full": wf, "holdout": wh},
           "vs_in_service_pp": {"full_ann": round((wf["ann"] - rf["full"]["ann"]) * 100, 2),
                                "full_mdd": round((wf["mdd"] - rf["full"]["mdd"]) * 100, 2),
                                "holdout_ann": round((wh["ann"] - rf["holdout"]["ann"]) * 100, 2)},
           "gates": {"G1_full_ann_mdd": g1,
                     "G1_margins": {"ann": round(wf["ann"] - G1_ANN_TH, 4), "mdd": round(wf["mdd"] - G1_MDD_TH, 4)},
                     "G2_locked_icir_increment": g2,
                     "G2_detail": {"icir_5f_locked": st5["locked"]["icir"], "icir_4f_locked": st4["locked"]["icir"],
                                   "delta_icir": None if d_icir is None else round(d_icir, 4),
                                   "delta_ic_mean_locked": d_ic_mean},
                     "G3_holdout_redflag": bool(halve),
                     "G3_detail": {"holdout_icir_5f": st5["holdout"]["icir"], "full_icir_5f": st5["full"]["icir"],
                                   "halve_line": None if (st5["full"]["icir"] is None or st5["full"]["icir"] == 0)
                                   else round(G3_HALVE * abs(st5["full"]["icir"]), 4)},
                     "all_pass_G1G2": bool(g1 and g2)},
           "ic_5f": st5,
           "pool_coverage": {"mean": round(float(np.mean(covs)), 4),
                             "effective_weight_share": round(w / w5n * float(np.mean(covs)), 4),
                             "nominal_weight_share": round(w / w5n, 4)},
           "holdings_jaccard_vs_inservice": overlap_stats(tag),
           "turnover": {"monthly_turnover_est": mF.get("monthly_turnover_est"),
                        "vs_g0_orig_pp": round((mF.get("monthly_turnover_est", 0)
                                                - mjson("r263_g0_orig").get("monthly_turnover_est", 0)) * 100, 2)},
           }
    grid.append(rec)
    print(tid, "G1:", g1, "G2:", g2, "G3flag:", halve, flush=True)
out["grid"] = grid

# 胜者选择(§五: W-full ann 最高 → w 小 → MDD 优)
passers = [g for g in grid if g["gates"]["all_pass_G1G2"]]
if passers:
    win = sorted(passers, key=lambda g: (-g["windows"]["full"]["ann"], g["csad_w"], -g["windows"]["full"]["mdd"]))[0]
    out["verdict"] = {"outcome": "PASS", "winner": {"exp_id": win["exp_id"], "tag": win["tag"], "csad_w": win["csad_w"]},
                      "rule": "R-263 §五: W-full ann 最高 → w 较小 → MDD 较优",
                      "next": "获评分制 v1.1 资格(不激活/不动 registry active; 另任务)"}
else:
    out["verdict"] = {"outcome": "FAIL_ALL", "next": "csad 因子线关闭, 归档负结果(R-263 §七.2)"}
redflagged = [g["exp_id"] for g in grid if g["gates"]["G3_holdout_redflag"]]
out["verdict"]["g3_redflag_trials"] = redflagged
out["verdict"]["g3_redflag_note"] = "红旗不自动否决; 进评分制前须用户知情确认(R-263 §五.4/§七.4)"

with open(os.path.join(W263, "e2_results.json"), "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("verdict:", json.dumps(out["verdict"], ensure_ascii=False))
print("e2_results.json written")
