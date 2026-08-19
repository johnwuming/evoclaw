#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0398: g3 护栏豁免改造的兼容性重算验证（D-20260819-G3CORR）
复刻 a13_score.py 的数据流与口径（ACTIVE=v5h_xsub、月度IC路径、同 n_trials），
唯一差异 = g3 使用新引擎的护栏豁免逻辑（ep._guard_exempt_pairs）。
预期：非 E1 因子化候选 score 与 a13_score_summary.json 逐位一致；E1 系列 corr 分量改善。
输出：results/a13_g3_reverify.json
"""
import os, sys, json, math
sys.path.insert(0, "/home/noname/quant-evolve/scripts")
os.chdir("/home/noname/quant-evolve")
import numpy as np
import pandas as pd
import evolution_pipeline as ep

RESULT = "results"
ACTIVE_ID = "v5h_xsub"
OUT = os.path.join(RESULT, "a13_g3_reverify.json")

CANDS = [
    ("a9_raw_universe", ["circ_mv", "ret120"], "原始宇宙对照翻案: 去四质量闸门(div/roe/roa/价帽), mv小市值排序+E1硬护栏+次新剔除, q3z_tr择时不变"),
    ("a9_ranksum_raw", ["circ_mv", "avg_amount_20d", "pb_inv", "roe_ttm", "ret120"], "ranksum四因子翻案: 去四闸门后 log_mv/amt20 低流动性+pb_inv价值+roe质量 ranksum 合成, E1硬护栏保留"),
    ("a13_rsraw_e1f05", ["circ_mv", "avg_amount_20d", "pb_inv", "roe_ttm", "mom_pen"], "E1因子化λ0.5: ranksum四因子排序分叠加动量惩罚 0.5*|clip(ret120,-1,0)|, 取代硬排除"),
    ("a13_rsraw_e1f10", ["circ_mv", "avg_amount_20d", "pb_inv", "roe_ttm", "mom_pen"], "E1因子化λ1.0: ranksum四因子排序分叠加动量惩罚 1.0*|clip(ret120,-1,0)|, 取代硬排除"),
    ("a13_rsraw_e1f15", ["circ_mv", "avg_amount_20d", "pb_inv", "roe_ttm", "mom_pen"], "E1因子化λ1.5: ranksum四因子排序分叠加动量惩罚 1.5*|clip(ret120,-1,0)|, 取代硬排除"),
    ("a13_rsraw_e1f10dz", ["circ_mv", "avg_amount_20d", "pb_inv", "roe_ttm", "mom_pen_dz"], "E1因子化λ1.0死区: 仅 ret120<-30% 段计罚(旧闸门域), (-30%,0) 死区不计罚"),
    ("a9_ranksum_quality", ["circ_mv", "avg_amount_20d", "pb_inv", "roe_ttm", "ret120"], "对照组: 质量闸门内 ranksum四因子(闸门不去除), E1硬护栏保留"),
]

stored = json.load(open(os.path.join(RESULT, "a13_score_summary.json")))
stored_map = {r["tag"]: r for r in stored["results"]}
n_trials_stored = stored.get("n_trials_cum")

active = ep.load_version(ACTIVE_ID)
act_factors = set((active.get("selection") or {}).get("factors", []))
ic_df = ep.load_ic_monthly()  # 新引擎 merged IC

report = {"task": "task-0398 D-20260819-G3CORR 兼容性重算", "active": ACTIVE_ID,
          "n_trials_current": ep.n_trials_cum(), "n_trials_stored": n_trials_stored,
          "rows": []}
ok_all = True
for tag, factors, logic in CANDS:
    st = stored_map.get(tag)
    if st is None:
        continue
    n_trials = st.get("n_trials") or n_trials_stored  # 冻结原评试验数，隔离台账漂移
    mL = json.load(open(os.path.join(RESULT, tag + "_locked_metrics.json")))
    reg = {"version_id": tag,
           "backtest_refs": {"metrics": {k: mL.get(k) for k in ("annual_return", "max_drawdown", "sharpe", "calmar")}},
           "selection": {"factors": factors}}
    gates = {}
    r12, err = ep.gate_icir(ic_df, factors, ep.GATE_CONFIG["oos_split_ym"])
    gates["g1_icir_is"], gates["g2_icir_oos"] = r12["gate1"], dict(r12["gate2"])
    if r12.get("icir_oos_annualized") is not None:
        gates["g2_icir_oos"]["icir_oos_annualized"] = r12["icir_oos_annualized"]
    # g3: 月度IC Pearson（a13 原口径）+ 新引擎护栏豁免
    new_factors = [f for f in factors if f not in act_factors]
    exempt = ep._guard_exempt_pairs(new_factors, active)
    mx, worst, pairs = 0.0, None, 0
    for f in new_factors:
        for g2f in sorted(act_factors):
            if (f, g2f) in exempt:
                continue
            if f in ic_df.columns and g2f in ic_df.columns:
                j = ic_df[[f, g2f]].dropna()
                if len(j) >= 24:
                    v = abs(float(np.corrcoef(j[f], j[g2f])[0, 1]))
                    pairs += 1
                    if v > mx:
                        mx, worst = v, (f, g2f)
    gates["g3_max_corr"] = ({"status": "PASS" if mx < ep.GATE_CONFIG["max_corr_max"] else "FAIL",
                             "max_abs_corr": round(mx, 4), "worst_pair": worst,
                             "n_pairs_resolved": pairs,
                             "new_factors": new_factors,
                             "guard_exempt_pairs": sorted([list(p) for p in exempt])}
                            if new_factors else
                            {"status": "N/A", "max_abs_corr": None})
    nav = pd.read_csv(os.path.join(RESULT, tag + "_locked_nav.csv"))["nav"].astype(float)
    rets = nav.pct_change().dropna().tolist()
    det, g4err = ep.deflated_sharpe(rets, n_trials)
    gates["g4_dsr"] = {"status": "PASS" if det["dsr"] >= ep.GATE_CONFIG["dsr_min"] else "FAIL", **det}
    gates["g5_logic"] = {"status": "PASS", "logic": logic}
    gates["g6_mdd_vs_parent"] = ep.gate_mdd_vs_parent(reg, active)
    sd = ep.score_composite(reg, gates, active)
    old = st["score"]
    same = (sd["score"] == old["score"]) and (sd["components"].get("corr") == old["components"].get("corr"))
    is_e1 = "e1f" in tag
    verdict = "IDENTICAL" if same else ("EXPECTED_DELTA(E1系列)" if is_e1 else "!!! DRIFT")
    if not same and not is_e1:
        ok_all = False
    report["rows"].append({
        "tag": tag, "score_new": sd["score"], "score_old": old["score"],
        "corr_comp_new": sd["components"].get("corr"), "corr_comp_old": old["components"].get("corr"),
        "max_corr_new": round(mx, 4), "max_corr_old": (st["gates"].get("g3_max_corr") or {}).get("max_abs_corr"),
        "exempt": sorted([list(p) for p in exempt]),
        "components_new": sd["components"], "components_old": old["components"],
        "dsr_new": det["dsr"], "n_trials": n_trials, "verdict": verdict})
    print("%-22s new=%.4f old=%.4f corr(%s→%s) maxρ(%s→%.4f) %s" % (
        tag, sd["score"], old["score"], old["components"].get("corr"), sd["components"].get("corr"),
        (st["gates"].get("g3_max_corr") or {}).get("max_abs_corr"), mx, verdict))
report["ok_all_non_e1_identical"] = ok_all
json.dump(report, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok_all_non_e1_identical:", ok_all, "→", OUT)
