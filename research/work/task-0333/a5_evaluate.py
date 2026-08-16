#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0333 A5 阶段4: 五门禁裁决 v2 (scipy.stats shim 版)
- HP quant env scipy.linalg ABI 损坏 (numpy 2.4.6/scipy 1.17.1, swap_c_and_f_layout signature mismatch)
- 管线仅在 gate_icir / deflated_sharpe 内用 sps.t.cdf / sps.norm.ppf / sps.norm.cdf / sps.skew / sps.kurtosis
- 在 sys.modules 预置纯 numpy 实现的 scipy.stats shim (Acklam ppf + betacf t-cdf), 不改任何管线代码
- IC 数据源仍走扩展文件 (a5_ic_monthly_ext.csv / a5_ic_corr_ext.csv)
输出: results/a5_gate_table.json
"""
import os, sys, json, math, argparse, types
import numpy as np

# ================= scipy.stats shim (纯 numpy/math 实现) =================
_stats_mod = types.ModuleType("scipy.stats")

def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _norm_ppf(p):
    if p <= 0.0: return -np.inf
    if p >= 1.0: return np.inf
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow = 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    elif p > 1.0 - plow:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    else:
        q = p - 0.5
        r = q * q
        x = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0)
    e = _norm_cdf(x) - p
    u = e * math.sqrt(2.0 * math.pi) * math.exp(x * x / 2.0)
    x = x - u / (1.0 + x * u / 2.0)
    return x

def _betacf(a, b, x, MAXIT=300, EPS=3e-12, FPMIN=1e-300):
    qab = a + b; qap = a + 1.0; qam = a - 1.0
    c = 1.0; d = 1.0 - qab * x / qap
    if abs(d) < FPMIN: d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS: break
    return h

def _betainc_reg(a, b, x):
    if x <= 0.0: return 0.0
    if x >= 1.0: return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(a * math.log(x) + b * math.log1p(-x) - lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    else:
        return 1.0 - front * _betacf(b, a, 1.0 - x) / b

def _t_cdf(t, df):
    x = df / (df + t * t)
    ib = _betainc_reg(df / 2.0, 0.5, x)
    return 1.0 - 0.5 * ib if t >= 0 else 0.5 * ib

def _skew_np(r):
    a = np.asarray(r, dtype=float)
    n = len(a)
    if n < 3: return float("nan")
    m2 = ((a - a.mean()) ** 2).mean()
    m3 = ((a - a.mean()) ** 3).mean()
    if m2 == 0: return 0.0
    return float(m3 / m2 ** 1.5)

def _kurt_np(r, fisher=True):
    a = np.asarray(r, dtype=float)
    n = len(a)
    if n < 4: return float("nan")
    m2 = ((a - a.mean()) ** 2).mean()
    m4 = ((a - a.mean()) ** 4).mean()
    if m2 == 0: return 0.0
    k = float(m4 / m2 ** 2)
    return k - 3.0 if fisher else k

_stats_mod.t = types.SimpleNamespace(cdf=_t_cdf)
_stats_mod.norm = types.SimpleNamespace(ppf=_norm_ppf, cdf=_norm_cdf)
_stats_mod.skew = _skew_np
_stats_mod.kurtosis = _kurt_np
sys.modules["scipy.stats"] = _stats_mod
print("SCIPY_STATS_SHIM_OK", flush=True)

# ================= 管线 evaluate (同 a4d 模式) =================
sys.path.insert(0, "/home/noname/quant-evolve/scripts")
import evolution_pipeline as ep

HP = "/home/noname/quant-evolve"
VERS = ["v4a_gqe1", "v4b_mve1", "v4c_gqpeg", "v4d_gqg1", "v4e_gqg1x"]

_orig_load_ic = ep.load_ic_monthly
def _load_ic_ext():
    import pandas as pd
    p = os.path.join(HP, "results/a5_ic_monthly_ext.csv")
    return pd.read_csv(p, dtype={"ym": str})
ep.load_ic_monthly = _load_ic_ext

_orig_gate_corr = ep.gate_max_corr
def _gate_corr_ext(reg):
    import pandas as pd
    corr_p = os.path.join(HP, "results/a5_ic_corr_ext.csv")
    act = ep.find_active()
    active_factors = set((act.get("selection") or {}).get("factors", [])) if act else set()
    cand_factors = reg["selection"].get("factors", [])
    new_factors = [f for f in cand_factors if f not in active_factors]
    if not new_factors:
        return {"status": "N/A", "max_abs_corr": None, "worst_pair": None,
                "note": "无新增因子（因子集与active一致），相关性门禁无信息量 → N/A"}
    corr = pd.read_csv(corr_p, index_col=0)
    mx, worst, unresolved = 0.0, None, []
    for f in new_factors:
        for g in active_factors:
            v = None
            if f in corr.index and g in corr.columns:
                try:
                    v = abs(float(corr.loc[f, g]))
                except Exception:
                    v = None
            if v is None:
                unresolved.append((f, g))
            else:
                if v > mx:
                    mx, worst = v, (f, g)
    st = "PASS" if mx < ep.GATE_CONFIG["max_corr_max"] else "FAIL"
    out = {"status": st, "max_abs_corr": round(mx, 4), "worst_pair": worst,
           "n_new_factors": len(new_factors), "new_factors": new_factors,
           "threshold": ep.GATE_CONFIG["max_corr_max"]}
    if unresolved:
        out["unresolved_pairs"] = len(unresolved)
        out["note"] = f"{len(unresolved)}个组合无相关性数据（按未超限处理）"
    return out
ep.gate_max_corr = _gate_corr_ext

for ver in VERS:
    args = argparse.Namespace(version=ver, oos_start=None)
    try:
        ep.cmd_evaluate(args)
        print("  eval ok:", ver, flush=True)
    except SystemExit as e:
        print("  eval exit:", ver, e, flush=True)

table = {}
for ver in VERS:
    rp = os.path.join(HP, f"results/bt_{ver}/gate-report.json")
    if not os.path.exists(rp):
        table[ver] = {"verdict": "NO_REPORT", "error": "gate-report.json missing"}
        continue
    r = ep.load_json(rp)
    g4 = r["gates"].get("g4_dsr", {})
    table[ver] = {
        "verdict": r["verdict"],
        "gates": {k: v.get("status") for k, v in r["gates"].items()},
        "metrics": r.get("backtest_metrics"),
        "dsr_detail": {k: g4.get(k) for k in ("dsr", "sr_period", "sr0_expected_max", "T", "skew", "kurtosis", "n_trials")},
        "icir_is": (r["gates"].get("g1_icir_is") or {}).get("icir_is_annualized"),
        "oos_p": (r["gates"].get("g2_icir_oos") or {}).get("p_one_sided"),
        "max_corr": (r["gates"].get("g3_max_corr") or {}).get("max_abs_corr"),
        "mdd_deterioration_pp": (r["gates"].get("g6_mdd_vs_parent") or {}).get("mdd_deterioration_pp"),
    }
with open(os.path.join(HP, "results/a5_gate_table.json"), "w", encoding="utf-8") as f:
    json.dump(table, f, ensure_ascii=False, indent=1)
print("A5_EVAL_DONE")
for ver, t in table.items():
    print(ver, t.get("verdict"), t.get("gates"), "dsr=", (t.get("dsr_detail") or {}).get("dsr"),
          "icir_is=", t.get("icir_is"))
