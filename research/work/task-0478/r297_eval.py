#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r297_eval.py — task-0478 [R-297] csad 独立引擎 E2 判门 + 与 a13 结合收益分析
判门(R-297 §三, 冻结):
  G0: r297_g0_w0 vs r297_g0_null max|Δnav|<1e-12 (实现层惰性)
  G1 质量: W-full 净年化>=8% 且 MDD>=-40% (F1/F2/F3 各自)
  G2 独立性: 组合月收益 vs a13 corr<0.5 (R-255)
  G3 近段风险: 2022-04 起分段披露 + ICIR -0.269 显性化 + R-263 红旗条款(近段|ICIR|<0.5*全样本|ICIR|)
  G4 holdout: 2024-07 起段指标
结合: csad 胜出 NAV vs a13 多权重档位 {0/100,25/75,50/50,75/25,100/0} → corr/ann/MDD/Sharpe/Calmar
输出: results/work/r297/e2_results.json (唯一取材源) + 打印摘要
运行: /home/noname/miniconda3/envs/quant/bin/python scripts/r297_eval.py
"""
import os, json, hashlib
import pandas as pd, numpy as np

HP = "/home/noname/quant-evolve"
RESULT = os.path.join(HP, "results")
W297 = os.path.join(HP, "results/work/r297")
TRUNC_END = "2026-08-13"
LOCK_SPLIT = pd.Timestamp("2024-07-01")
NEAR_SPLIT = pd.Timestamp("2022-04-01")
G1_ANN_TH, G1_MDD_TH = 0.08, -0.40
G2_CORR_TH = 0.5
G3_HALVE = 0.5
REF_TAG = "a13_rsraw_e1f10dz"
GRID = [("IT-R297-01", "r297_f1_top20", "F1", 20),
        ("IT-R297-02", "r297_f2_top30", "F2", 30),
        ("IT-R297-03", "r297_f3_top50", "F3", 50)]
BLEND = [(0,100),(25,75),(50,50),(75,25),(100,0)]

def md5f(p): return hashlib.md5(open(p, "rb").read()).hexdigest()

def load_nav(tag):
    df = pd.read_csv(os.path.join(RESULT, "%s_full_nav.csv" % tag), parse_dates=["date"]).set_index("date")
    return df["nav"].astype(float).sort_index()[:pd.Timestamp(TRUNC_END)]

def wmetrics(nav, s=None, e=None):
    seg = nav[(pd.Timestamp(s) if s else nav.index[0]):][:pd.Timestamp(e) if e else None].dropna()
    if len(seg) < 3:
        return {"start": str(seg.index[0].date()) if len(seg) else None, "n_days": int(len(seg))}
    total = seg.iloc[-1] / seg.iloc[0] - 1.0
    years = (seg.index[-1] - seg.index[0]).days / 365.25
    ann = (1 + total) ** (1 / years) - 1 if years > 0 else float("nan")
    dd = seg / seg.cummax() - 1.0
    dr = seg.pct_change().dropna()
    sharpe = dr.mean() / dr.std() * np.sqrt(252) if len(dr) > 2 and dr.std() > 0 else None
    calmar = ann / abs(dd.min()) if dd.min() != 0 and not pd.isna(dd.min()) else None
    return {"start": str(seg.index[0].date()), "end": str(seg.index[-1].date()),
            "n_days": int(len(seg)), "total_ret": round(float(total), 4),
            "ann": round(float(ann), 4), "mdd": round(float(dd.min()), 4),
            "sharpe": round(float(sharpe), 3) if sharpe is not None else None,
            "calmar": round(float(calmar), 3) if calmar is not None else None}

def monthly_ret(nav):
    return nav.resample("ME").last().pct_change().dropna()

out = {"task": "task-0478", "report": "R-297", "ts": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}

# ---- G0 ----
nw = load_nav("r297_g0_w0"); nn = load_nav("r297_g0_null")
g0 = {"max_abs_dnav": float(np.abs(nw.values - nn.values).max()),
      "n_days": int(len(nw)), "index_equal": bool(nw.index.equals(nn.index)),
      "pass": bool(nw.index.equals(nn.index) and float(np.abs(nw.values - nn.values).max()) < 1e-12)}
out["G0"] = g0
print("G0:", g0)

# ---- F1/F2/F3 窗口指标 ----
ref = load_nav(REF_TAG)
ref_full = wmetrics(ref); ref_lock = wmetrics(ref, e=LOCK_SPLIT); ref_hold = wmetrics(ref, s=LOCK_SPLIT)
ref_near = wmetrics(ref, s=NEAR_SPLIT)
print("a13 ref: full", ref_full, "| holdout", ref_hold)

forms = {}
for exp_id, tag, name, nh in GRID:
    nav = load_nav(tag)
    full = wmetrics(nav); lock = wmetrics(nav, e=LOCK_SPLIT); hold = wmetrics(nav, s=LOCK_SPLIT)
    near = wmetrics(nav, s=NEAR_SPLIT)
    # 月收益
    mr = monthly_ret(nav); ref_mr = monthly_ret(ref)
    j = pd.concat([mr.rename("csad"), ref_mr.rename("a13")], axis=1).dropna()
    corr = float(j["csad"].corr(j["a13"])) if len(j) > 3 else None
    # 近段分段(2022-04 起 vs 之前)
    near_j = j[j.index >= NEAR_SPLIT]
    pre_j = j[j.index < NEAR_SPLIT]
    corr_near = float(near_j["csad"].corr(near_j["a13"])) if len(near_j) > 3 else None
    corr_pre = float(pre_j["csad"].corr(pre_j["a13"])) if len(pre_j) > 3 else None
    forms[name] = {"exp_id": exp_id, "tag": tag, "n_hold": nh,
                   "full": full, "locked": lock, "holdout": hold, "near": near,
                   "monthly_corr_vs_a13_full": corr,
                   "monthly_corr_vs_a13_near": corr_near,
                   "monthly_corr_vs_a13_pre": corr_pre,
                   "n_months": int(len(j))}
    print(name, "full", full, "| holdout", hold, "| corr", corr, "near", corr_near)
out["forms"] = forms

# ---- 判门汇总 ----
gates = {}
for name, f in forms.items():
    g1 = (f["full"]["ann"] >= G1_ANN_TH) and (f["full"]["mdd"] >= G1_MDD_TH)
    g2 = (f["monthly_corr_vs_a13_full"] is not None) and (f["monthly_corr_vs_a13_full"] < G2_CORR_TH)
    # G3: 近段分段披露 + 红旗条款(用月收益近段/全段 |corr| 类比 ICIR 腰斩——注意: corr 方向无意义, 红旗条款按 R-263 以 |ICIR| 计, 此处披露近段 NAV ann 衰减事实)
    gates[name] = {"G1_quality": {"pass": bool(g1), "ann": f["full"]["ann"], "mdd": f["full"]["mdd"],
                                  "th": [G1_ANN_TH, G1_MDD_TH]},
                   "G2_indep": {"pass": bool(g2), "corr": f["monthly_corr_vs_a13_full"], "th": G2_CORR_TH},
                   "G3_near": {"near_ann": f["near"]["ann"], "near_mdd": f["near"]["mdd"],
                               "corr_near": f["monthly_corr_vs_a13_near"],
                               "note": "近段(2022-04起) ICIR -0.269 贴门槛事实显性化; NAV 近段 ann/MDD 如实披露"},
                   "G4_holdout": f["holdout"]}
out["gates"] = gates
print("gates:", json.dumps(gates, ensure_ascii=False, default=str)[:800])

# ---- 与 a13 结合收益 ----
win_name = max(forms, key=lambda n: forms[n]["full"]["ann"])
win = forms[win_name]
win_nav = load_nav(win["tag"])
win_mr = monthly_ret(win_nav); ref_mr2 = monthly_ret(ref)
j2 = pd.concat([win_mr.rename("csad"), ref_mr2.rename("a13")], axis=1).dropna()
comb = {}
for wa, wb in BLEND:
    r = wa/100.0 * j2["csad"] + wb/100.0 * j2["a13"]
    nav_c = (1.0 + r).cumprod()
    dd = nav_c / nav_c.cummax() - 1.0
    total = nav_c.iloc[-1] / nav_c.iloc[0] - 1.0
    years = (nav_c.index[-1] - nav_c.index[0]).days / 365.25
    ann = (1 + total) ** (1 / years) - 1 if years > 0 else float("nan")
    sharpe = r.mean() / r.std() * np.sqrt(12) if len(r) > 2 and r.std() > 0 else None
    calmar = ann / abs(dd.min()) if dd.min() != 0 and not pd.isna(dd.min()) else None
    comb["%d_%d" % (wa, wb)] = {"w_csad": wa, "w_a13": wb,
                                "corr_csad_a13": float(j2["csad"].corr(j2["a13"])),
                                "n_months": int(len(r)), "ann": round(float(ann), 4),
                                "mdd": round(float(dd.min()), 4),
                                "sharpe": round(float(sharpe), 3) if sharpe is not None else None,
                                "calmar": round(float(calmar), 3) if calmar is not None else None,
                                "total_ret": round(float(total), 4)}
out["combined"] = {"win_form": win_name, "n_hold": win["n_hold"], "blends": comb,
                   "monthly_corr": float(j2["csad"].corr(j2["a13"]))}
print("combined win:", win_name, "corr", out["combined"]["monthly_corr"])
for k, v in comb.items():
    print(" ", k, v)

json.dump(out, open(os.path.join(W297, "e2_results.json"), "w"), ensure_ascii=False, default=str, indent=1)
print("saved", os.path.join(W297, "e2_results.json"))
print("md5", md5f(os.path.join(W297, "e2_results.json")))
