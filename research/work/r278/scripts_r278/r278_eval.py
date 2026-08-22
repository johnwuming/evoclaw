#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r278_eval.py — task-0455 [R-278 §七.4] 判门 + 胜者五门评分 (评分制 v1.1 部署口径, 只读)
G0/G1/G2/G3 判门 → 胜者选择 → g1-g5 + score_composite + rank 池 (registry 零写入)
产物: results/work/r278/e2_results.json
"""
import os, sys, json, math
import numpy as np
import pandas as pd

os.chdir("/home/noname/quant-evolve")
sys.path.insert(0, "/home/noname/quant-evolve/scripts")
sys.path.insert(0, "/home/noname/quant-evolve")

RESULT = "results"
W278 = os.path.join(RESULT, "work", "r278")
TRUNC = "2026-08-13"          # R-253 纪律: 最后真实 mark 公共日
LOCK_END = pd.Timestamp("2024-06-28")   # 审计锁 (AUDIT_LOCK_END)

RUNS = {"base": "r278_g0_orig", "t1": "r278_t1_l07", "t2": "r278_t2_l08", "t3": "r278_t3_v20"}
LOGIC = ("PCR_oi(期权月末持仓认沽认购比) roll36m 分位<=0.30 贪婪态次月: 对新入场仓位降权/否决最弱新入场。"
         "机制: 期权持仓者不买保护=自满, 微盘顶部拥挤, 新入场承接均值回归下行 (R-272 E1 -2.04pp/胜率33.3%)。")

def load_nav(tag):
    df = pd.read_csv(os.path.join(RESULT, "%s_full_nav.csv" % tag),
                     parse_dates=["date"]).set_index("date")["nav"].astype(float)
    return df[df.index <= TRUNC]

def seg_metrics(nav):
    if len(nav) < 20 or nav.iloc[0] <= 0:
        return None
    years = (nav.index[-1] - nav.index[0]).days / 365.25
    ann = float(nav.iloc[-1] / nav.iloc[0]) ** (1.0 / years) - 1.0
    mdd = float((nav / nav.cummax() - 1.0).min())
    r = nav.pct_change().dropna()
    sharpe = float(r.mean() / r.std(ddof=1) * math.sqrt(252)) if len(r) > 20 and r.std(ddof=1) > 0 else None
    return {"annual_return": round(ann, 6), "max_drawdown": round(mdd, 6),
            "sharpe": round(sharpe, 4) if sharpe is not None else None, "n_days": int(len(nav)),
            "start": str(nav.index[0].date()), "end": str(nav.index[-1].date())}

def w_metrics(nav, lo=None, hi=None):
    s = nav
    if lo is not None: s = s[s.index >= lo]
    if hi is not None: s = s[s.index <= hi]
    return seg_metrics(s)

def next_ym(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return "%04d-%02d" % (y, m)

# ---- 数据 ----
states = pd.read_csv(os.path.join(W278, "pcroi_states.csv"), dtype={"ym": str})
sig_months = states.loc[states["active"] == 1, "ym"].tolist()
interv_months = sorted(set(next_ym(m) for m in sig_months))

navs = {k: load_nav(t) for k, t in RUNS.items()}
base = navs["base"]
mret = {}
for k, nv in navs.items():
    me = nv.resample("ME").last().pct_change().dropna()
    mret[k] = me
    assert len(me) > 230

def cond_excess(key, months=None):
    months = months or interv_months
    s = pd.Series(mret[key].values, index=mret[key].index.strftime("%Y-%m"))
    sb = pd.Series(mret["base"].values, index=mret["base"].index.strftime("%Y-%m"))
    idx = [i for i in months if i in s.index and i in sb.index]
    d = (s.loc[idx] - sb.loc[idx]) * 100.0
    return float(d.mean()), int(len(idx)), d

WINDOWS = {
    "full": (None, None),
    "sig": ("2017-02-01", None),
    "flagship": ("2024-01-01", "2024-02-29"),
    "holdout": ("2024-07-01", None),
}
metrics = {}
for k in RUNS:
    metrics[k] = {w: w_metrics(navs[k], lo, hi) for w, (lo, hi) in WINDOWS.items()}
    metrics[k]["locked"] = w_metrics(navs[k], None, LOCK_END)

# ---- G0 ----
g0 = json.load(open(os.path.join(W278, "g0_result.json")))
g0_pass = bool(g0["g0_pass"])

# ---- G1/G2/G3 ----
PRE_END = "2021-10"; POST_STA = "2021-11"
pre_m = [i for i in interv_months if i <= PRE_END + "-31"]
post_m = [i for i in interv_months if i >= POST_STA + "-01"]

res = {"g0": g0, "interv_months": interv_months, "n_interv": len(interv_months),
       "windows": {k: v for k, v in WINDOWS.items()},
       "metrics": metrics, "trials": {}}
for k in ("t1", "t2", "t3"):
    ce, n_ce, ce_series = cond_excess(k)
    ce_pre, n_pre, _ = cond_excess(k, pre_m)
    ce_post, n_post, _ = cond_excess(k, post_m)
    flag_impr = (abs(metrics["base"]["flagship"]["max_drawdown"]) -
                 abs(metrics[k]["flagship"]["max_drawdown"])) * 100.0  # 改善=|base|-|cand| (R-252 口径)
    full_drag = (metrics["base"]["full"]["annual_return"] - metrics[k]["full"]["annual_return"]) * 100.0
    full_mdd_det = (abs(metrics[k]["full"]["max_drawdown"]) -
                    abs(metrics["base"]["full"]["max_drawdown"])) * 100.0
    g1 = (ce > 0.0) and (flag_impr >= 0.30)
    g2 = (full_drag <= 0.30) and (full_mdd_det <= 0.5)
    g3 = (ce_pre > -0.30) and (ce_post > -0.30)
    res["trials"][k] = {
        "cond_excess_pp": round(ce, 4), "n_cond": n_ce,
        "cond_excess_pre_pp": round(ce_pre, 4), "n_pre": n_pre,
        "cond_excess_post_pp": round(ce_post, 4), "n_post": n_post,
        "flagship_mdd_impr_pp": round(flag_impr, 3),
        "full_ann_drag_pp": round(full_drag, 4),
        "full_mdd_deter_pp": round(full_mdd_det, 3),
        "G1": bool(g1), "G2": bool(g2), "G3": bool(g3),
        "e2_pass": bool(g1 and g2 and g3),
        "cond_series": {str(i): round(v, 4) for i, v in ce_series.items()},
    }

# ---- 胜者选择: 过门者 W-full ann 最高; 平手干预最轻 (λ0.8>λ0.7>veto) ----
order = ["t2", "t1", "t3"]
passed = [k for k in order if res["trials"][k]["e2_pass"]]
winner = None
if passed:
    winner = max(passed, key=lambda k: (metrics[k]["full"]["annual_return"],
                                        -order.index(k)))
res["winner"] = winner
res["any_e2_pass"] = bool(passed)

# ---- 胜者五门评分 (v1.1 部署口径, registry 只读) ----
if winner:
    import evolution_pipeline as EP
    reg_a13 = json.load(open("model/registry/a13_rsraw_e1f10dz.json"))
    act = EP.find_active()
    factors = reg_a13["selection"].get("factors", [])
    ic_df = EP.load_ic_monthly()
    r12, err = EP.gate_icir(ic_df, factors, EP.GATE_CONFIG["oos_split_ym"])
    g1g2 = r12 if r12 else {"gate1": {"status": "N/A", "note": err},
                            "gate2": {"status": "N/A", "note": err}}
    wl = metrics[winner]["locked"]
    wtag = RUNS[winner]
    lm_path = os.path.join(RESULT, "%s_locked_metrics.json" % wtag)
    lm = json.load(open(lm_path)) if os.path.exists(lm_path) else None
    mlock = lm or wl
    r_daily = navs[winner].pct_change().dropna().values
    dsr, derr = EP.deflated_sharpe(r_daily, EP.n_trials_cum())
    par_m = (act.get("backtest_refs") or {}).get("metrics") or {}
    det_pp = round((abs(mlock["max_drawdown"]) - abs(par_m["max_drawdown"])) * 100.0, 2) \
        if mlock.get("max_drawdown") and par_m.get("max_drawdown") else None
    gates = {
        "g1_icir_is": g1g2.get("gate1"), "g2_icir_oos": g1g2.get("gate2"),
        "g3_max_corr": {"status": "N/A",
                        "note": "无新因子: 因子集与在役逐字同 (R-254 T4 先例, N/A 重归一); "
                                "信号级去重: E1 corr(pcroi,rv)=-0.343 / Jac=0.04"},
        "g4_dsr": {"status": ("PASS" if (dsr or {}).get("dsr", 0) >= EP.GATE_CONFIG["dsr_min"]
                              else "FAIL"), **(dsr or {"note": derr})},
        "g5_logic": {"status": "PASS" if LOGIC.strip() else "FAIL", "logic": LOGIC},
        "g6_mdd_vs_parent": {"status": "N/A", "disabled": True,
                             "mdd_deterioration_pp": det_pp,
                             "note": "D-20260819-G6DEL 硬判定禁用, 数值入评分 dd 项"},
    }
    temp_reg = {"version_id": "r278_%s_pcr_conf" % winner, "status": "candidate",
                "backtest_refs": {"metrics": {
                    "annual_return": mlock.get("annual_return"),
                    "max_drawdown": mlock.get("max_drawdown"),
                    "sharpe": mlock.get("sharpe"),
                    "calmar": mlock.get("calmar") or (
                        round(mlock["annual_return"] / abs(mlock["max_drawdown"]), 4)
                        if mlock.get("calmar") is None and mlock.get("max_drawdown") else None)}},
                "selection": {"factors": factors}, "gate": {"logic": LOGIC}}
    sd = EP.score_composite(temp_reg, gates)
    pool = EP.score_rank_pool(temp_reg, sd["score"])
    rank = [i[0] for i in pool].index(temp_reg["version_id"]) + 1
    five_pass = all(gates[g]["status"] != "FAIL" for g in
                    ("g1_icir_is", "g2_icir_oos", "g4_dsr", "g5_logic"))
    res["scoring"] = {
        "winner": winner, "locked_metrics": mlock, "parent_locked": par_m,
        "gates": gates, "score": sd, "pool": [(i[0], round(s, 4)) for i, s in pool],
        "rank": rank, "five_gate_pass": bool(five_pass),
        "recommend_activate": bool(five_pass and rank == 1 and not sd["stat_warn"]),
        "n_trials_cum": EP.n_trials_cum(),
        "registry_note": "临时 reg 字典不落盘; registry 零写入 (task-0455 硬约束)",
    }

json.dump(res, open(os.path.join(W278, "e2_results.json"), "w"),
          ensure_ascii=False, indent=1, default=str)
print(json.dumps({"g0_pass": g0_pass, "winner": winner,
                  "trials": {k: {kk: vv for kk, vv in v.items() if kk != "cond_series"}
                             for k, v in res["trials"].items()},
                  "scoring_rank": (res.get("scoring") or {}).get("rank"),
                  "score": (res.get("scoring") or {}).get("score", {}).get("score")},
                 ensure_ascii=False, indent=1))
print("EVAL DONE")
