#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0333 A5 阶段4: 五门禁裁决 (evolution_pipeline.cmd_evaluate, 扩展IC数据)
- A5新增因子不在存量107因子IC文件内 → 内存 monkeypatch ep.load_ic_monthly 读扩展文件
  (a5_ic_monthly_ext.csv / a5_ic_corr_ext.csv), 不改任何管线代码
输出: results/a5_gate_table.json
"""
import os, sys, json, argparse
sys.path.insert(0, "/home/noname/quant-evolve/scripts")
import evolution_pipeline as ep

HP = "/home/noname/quant-evolve"
VERS = ["v4a_gqe1", "v4b_mve1", "v4c_gqpeg", "v4d_gqg1", "v4e_gqg1x"]

# ---- 内存 monkeypatch: IC 数据源换扩展文件 ----
_orig_load_ic = ep.load_ic_monthly
def _load_ic_ext():
    import pandas as pd
    p = os.path.join(HP, "results/a5_ic_monthly_ext.csv")
    return pd.read_csv(p, dtype={"ym": str})
ep.load_ic_monthly = _load_ic_ext

_orig_gate_corr = ep.gate_max_corr
def _gate_corr_ext(reg):
    import pandas as pd
    import numpy as np
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

# ---- 逐候选 evaluate ----
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
