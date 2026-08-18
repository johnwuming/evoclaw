#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
a4b_run.py — task-0364 [A4b 阶段A] 价值过滤器 + 成长×质量复合 候选回测 + 五门禁
结构1: mv 排序主干 + PEG 过滤闸 (s1a PEG<2 / s1b PEG<1.5 / s1c PEG≤60分位)
结构2: 成长复合 × buf_quality 锚 (s2a 均衡z / s2b ranksum / s2c 成长主导z)
五门禁: g1_ic / g2_icir / g3_turnover / g4_capacity / g5_corr
运行: nohup /home/noname/miniconda3/envs/quant/bin/python scripts/a4b_run.py > logs/a4b_run.log 2>&1 &
断点可续: 每候选 skip-if-done(full+locked metrics 双存在)
PIT: PE 用 ths_ttm_panel avail_date as-of; growth 用 fin_deep_monthly_panel_ak(usable_from 月频, 与 W1/A4D 同机制)
"""
import os, sys, json, time
import numpy as np
import pandas as pd

sys.path.insert(0, "/home/noname/quant-evolve/scripts")
sys.path.insert(0, "/home/noname/quant-evolve")
os.chdir("/home/noname/quant-evolve")

from a9_common import (RESULT, LOCK_END, load_engine, build_timing, compute_metrics,
                       write_dual_artifacts, stage_log, NUM_KEYS)
import inspect, types
import macro_timing_layer_iter4 as mtl4

t0 = time.time()
def LOG(*a):
    print("[%6.0fs]" % (time.time() - t0), *a, flush=True)

# ---------------- a4b patch: a9 补丁 + peg 过滤闸 + 新因子列 ----------------
def patch_engine_a4b(engine):
    import a9_common
    SRC = inspect.getsource(engine.run_backtest)

    # PA/PV/PC/PC2/PB/PD/PE 与 a9_common 相同锚点, 但 PB/PD 扩展
    OLD_A = '''                if pd.isna(fund.loc[code, "div_yield_ttm"]) or fund.loc[code, "div_yield_ttm"] < div_min:
                    continue
                if pd.isna(fund.loc[code, "roe_ttm"]) or fund.loc[code, "roe_ttm"] <= roe_min:
                    continue
                if pd.isna(fund.loc[code, "roa_ttm"]) or fund.loc[code, "roa_ttm"] <= roa_min:
                    continue
                price = closes[code].get(d, np.nan)
                if pd.isna(price) or price >= price_cap or price <= 0:
                    continue'''
    NEW_A = '''                price = closes[code].get(d, np.nan)
                if pd.isna(price) or price <= 0:
                    continue
                if not _rawu:
                    if pd.isna(fund.loc[code, "div_yield_ttm"]) or fund.loc[code, "div_yield_ttm"] < div_min:
                        continue
                    if pd.isna(fund.loc[code, "roe_ttm"]) or fund.loc[code, "roe_ttm"] <= roe_min:
                        continue
                    if pd.isna(fund.loc[code, "roa_ttm"]) or fund.loc[code, "roa_ttm"] <= roa_min:
                        continue
                    if price >= price_cap:
                        continue'''
    assert SRC.count(OLD_A) == 1, "PA anchor"
    SRC = SRC.replace(OLD_A, NEW_A)

    OLD_V = '''    sort = cfg["sort"]
    score_weights'''
    NEW_V = '''    sort = cfg["sort"]
    _rawu = bool(cfg.get("raw_universe", 0))
    score_weights'''
    assert SRC.count(OLD_V) == 1, "PV anchor"
    SRC = SRC.replace(OLD_V, NEW_V)

    OLD_C = '''            if not target:
                ranked = []'''
    NEW_C = '''            if cfg.get("e1_guard"):
                for code in list(target):
                    cser = closes.get(code)
                    s = cser.loc[:d] if cser is not None else None
                    if s is None or len(s) < 121:
                        continue
                    try:
                        r120 = float(s.iloc[-1]) / float(s.iloc[-121]) - 1.0
                    except Exception:
                        continue
                    if r120 < -0.30:
                        del target[code]
            _xd = float(cfg.get("xsub_days", 0) or 0)
            if _xd > 0:
                for code in list(target):
                    fd = first_last[code][0]
                    if (d - fd).days < _xd:
                        del target[code]
            if not target:
                ranked = []'''
    assert SRC.count(OLD_C) == 1, "PC anchor"
    SRC = SRC.replace(OLD_C, NEW_C)

    # PEG 过滤闸 (结构1): peg_filter 绝对阈值 / peg_filter_q 横截面分位; peg_na_keep=1 缺失保留
    OLD_G = '''            if not target:
                ranked = []'''
    NEW_G = '''            _pf = cfg.get("peg_filter")
            _pfq = cfg.get("peg_filter_q")
            if _pf is not None or _pfq is not None:
                _nk = int(cfg.get("peg_na_keep", 0))
                _vals = []
                if _pfq is not None:
                    for _t in target.values():
                        _v = _t.get("peg_np")
                        if _v is not None and not pd.isna(_v):
                            _vals.append(float(_v))
                _thr = float(_pf) if _pf is not None else (
                    float(np.quantile(_vals, float(_pfq))) if _vals else None)
                if _thr is not None:
                    for code in list(target):
                        _v = target[code].get("peg_np")
                        if _v is None or pd.isna(_v):
                            if _nk:
                                continue
                            del target[code]
                            continue
                        if float(_v) > _thr:
                            del target[code]
            if not target:
                ranked = []'''
    assert SRC.count(OLD_G) == 1, "PEG gate anchor"
    SRC = SRC.replace(OLD_G, NEW_G)

    OLD_B = '''            else:
                ranked = sorted(target.items(), key=lambda kv: (kv[1]["circ_mv"] if pd.notna(kv[1]["circ_mv"]) else np.inf))'''
    NEW_B = '''            elif str(cfg.get("ext_mode", "")) in ("zscore", "ranksum"):
                _mode = str(cfg.get("ext_mode"))
                tdf = pd.DataFrame(target).T
                _specs = cfg.get("ext_specs") or []
                _fa = int(cfg.get("ext_filter_all", 1))
                def _fval(_c, _name):
                    _v = np.nan
                    try:
                        if _name == "circ_mv":
                            _v = float(tdf.loc[_c, "circ_mv"])
                        elif _name == "log_mv":
                            _x = tdf.loc[_c, "circ_mv"]
                            _v = float(np.log(_x)) if (pd.notna(_x) and float(_x) > 0) else np.nan
                        elif _name == "amt20":
                            _a = amt.get(_c)
                            _w = _a.loc[:d].tail(20).dropna() if _a is not None else None
                            if _w is not None and len(_w) >= 10 and float(_w.mean()) > 0:
                                _v = float(_w.mean())
                        elif _name in ("pe_ttm", "peg_np", "npg", "rvg", "gpersist", "grw", "bufq"):
                            if _name in tdf.columns:
                                _v = float(tdf.loc[_c, _name])
                    except Exception:
                        _v = np.nan
                    return _v
                _ok = pd.Series(True, index=tdf.index)
                for _name, _wgt, _sgn in _specs:
                    _fv = pd.Series({c: _fval(c, _name) for c in tdf.index})
                    tdf["f_" + _name] = _fv
                    if float(_wgt) != 0.0 or _fa:
                        _ok &= _fv.notna()
                tdf = tdf[_ok]
                if not len(tdf):
                    ranked = []
                else:
                    _score = None
                    for _name, _wgt, _sgn in _specs:
                        _col = tdf["f_" + _name]
                        if _mode == "zscore":
                            _sd = _col.std()
                            _tr = (_col - _col.mean()) / _sd if (_sd is not None and not pd.isna(_sd) and _sd > 0) else _col * 0.0
                        else:
                            _tr = _col.rank(pct=True)
                        _con = float(_wgt) * float(_sgn) * _tr
                        _score = _con if _score is None else _score + _con
                    ranked = sorted(_score.items(), key=lambda kv: -kv[1])
            else:
                ranked = sorted(target.items(), key=lambda kv: (kv[1]["circ_mv"] if pd.notna(kv[1]["circ_mv"]) else np.inf))'''
    assert SRC.count(OLD_B) == 1, "PB anchor"
    SRC = SRC.replace(OLD_B, NEW_B)

    OLD_T = '''                    "price": price,
                }'''
    NEW_T = '''                    "price": price,
                    "pe_ttm": (fund.loc[code, "pe_ttm"] if "pe_ttm" in fund.columns else np.nan),
                    "peg_np": (fund.loc[code, "peg_np"] if "peg_np" in fund.columns else np.nan),
                    "npg": (fund.loc[code, "npg"] if "npg" in fund.columns else np.nan),
                    "rvg": (fund.loc[code, "rvg"] if "rvg" in fund.columns else np.nan),
                    "gpersist": (fund.loc[code, "gpersist"] if "gpersist" in fund.columns else np.nan),
                    "grw": (fund.loc[code, "grw"] if "grw" in fund.columns else np.nan),
                    "bufq": (fund.loc[code, "bufq"] if "bufq" in fund.columns else np.nan),
                }'''
    assert SRC.count(OLD_T) == 1, "PD anchor"
    SRC = SRC.replace(OLD_T, NEW_T)

    OLD_R = '''    return metrics'''
    NEW_R = '''    return metrics, nav_df, trade_log, holdings_log'''
    assert SRC.count(OLD_R) == 1, "PE anchor"
    SRC = SRC.replace(OLD_R, NEW_R)

    mod = types.ModuleType("a4b_engine")
    mod.__dict__.update(engine.__dict__)
    exec(compile(SRC, "<a4b_patched>", "exec"), mod.__dict__)
    return mod.run_backtest, {"orig": len(SRC) - 999, "patched": len(SRC)}

# ---------------- 因子面板 (PIT) ----------------
def a4b_merge_factors(mk):
    HP = "/home/noname/quant-evolve"
    p = pd.read_parquet(os.path.join(HP, "data/derived/fundamentals_monthly.parquet"))
    p = p[["code", "date", "div_yield_ttm", "circ_mv", "roe_ttm", "roa_ttm"]].copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.sort_values("date")
    ths = pd.read_parquet(os.path.join(HP, "data/derived/ths_ttm_panel.parquet"))
    ths = ths[["code", "net_profit_ttm", "avail_date"]].dropna(subset=["avail_date"])
    ths["avail_date"] = pd.to_datetime(ths["avail_date"])
    ths = ths.sort_values(["code", "avail_date"]).drop_duplicates(["code", "avail_date"], keep="last")
    m = pd.merge_asof(p, ths, by="code", left_on="date", right_on="avail_date", direction="backward")
    eq = m["net_profit_ttm"].astype(float); mv = m["circ_mv"].astype(float)
    m["pe_ttm"] = np.where((eq > 0) & (mv > 0), mv / eq, np.nan)
    deep = pd.read_parquet(os.path.join(HP, "data/derived/fin_deep_monthly_panel_ak.parquet"))
    deep = deep[["code", "ym", "net_profit_yoy", "revenue_yoy", "growth_persist", "gp_margin", "cf_np_ratio", "debt_to_asset"]].copy()
    deep["m_end"] = pd.to_datetime(deep["ym"]) + pd.offsets.MonthEnd(0)
    deep = deep.dropna(subset=["m_end"]).sort_values(["code", "m_end"]).drop_duplicates(["code", "m_end"], keep="last")
    m = pd.merge_asof(m.sort_values("date"), deep, by="code", left_on="date", right_on="m_end", direction="backward")
    pe = m["pe_ttm"].astype(float); npg = m["net_profit_yoy"].astype(float)
    m["peg_np"] = np.where((pe > 0) & (npg > 0), pe / npg, np.nan)
    m = m.rename(columns={"net_profit_yoy": "npg", "revenue_yoy": "rvg", "growth_persist": "gpersist"})
    def _z(s):
        sd = s.std()
        return (s - s.mean()) / sd if (pd.notna(sd) and sd > 0) else s * np.nan
    g = m.groupby("date")
    zn, zr, zp = g["npg"].transform(_z), g["rvg"].transform(_z), g["gpersist"].transform(_z)
    ncnt = (zn.notna().astype(int) + zr.notna().astype(int) + zp.notna().astype(int))
    grw_num = zn.fillna(0) + zr.fillna(0) + zp.fillna(0)
    m["grw"] = np.where(ncnt > 0, grw_num / ncnt.clip(lower=1), np.nan)
    zq1, zq2, zq3, zq4 = g["roe_ttm"].transform(_z), g["gp_margin"].transform(_z), g["cf_np_ratio"].transform(_z), g["debt_to_asset"].transform(_z)
    qcnt = (zq1.notna().astype(int) + zq2.notna().astype(int) + zq3.notna().astype(int) + zq4.notna().astype(int))
    bufq_num = zq1.fillna(0) + zq2.fillna(0) + zq3.fillna(0) - zq4.fillna(0)
    m["bufq"] = np.where(qcnt >= 2, bufq_num / qcnt.clip(lower=1), np.nan)
    keep = ["code", "date", "div_yield_ttm", "circ_mv", "roe_ttm", "roa_ttm",
            "pe_ttm", "peg_np", "npg", "rvg", "gpersist", "grw", "bufq"]
    mk["panel"] = m[keep]
    cov = {c: round(float(m[c].notna().mean()), 4) for c in ["pe_ttm", "peg_np", "npg", "gpersist", "grw", "bufq"]}
    LOG("[factors] panel rows=%d cov=%s" % (len(m), json.dumps(cov)))
    return cov

# ---------------- 主流程 ----------------
engine, q4b = load_engine()
run_bt, pmeta = patch_engine_a4b(engine)
LOG("patch ok", pmeta)

mk = q4b.load_fullpool_market(verbose=False)
LOG("market loaded codes=%d" % len(mk["codes"]))
cov = a4b_merge_factors(mk)

sig = mtl4.build_timing_signals_iter4({})
pos_incumbent = build_timing(mk, sig, mtl4, ma_window=200, floor=0.30, q3z_on=True)
LOG("q3z_tr timing mean=%.3f" % pos_incumbent.mean())

BASE = dict(sort="ext", div_min=0.02, roe_min=0.15, roa_min=0.10, n_hold=20,
            price_cap=10.0, min_amt=0.0, drawdown_control=0, cost_model="v2",
            limit_board="on", capital_base=1e7,
            dd_thresh=0.20, dd_reduce=0.5, dd_recover=0.05,
            cost_rate=0.001, limit_up_pct=0.098, ext_filter_all=1, e1_guard=1, xsub_days=365.0)
FULL_RANGE = ("2006-01-01", "2026-08-31")

CANDS = [
    ("a4b_s1a_peg2",   dict(ext_mode="zscore", ext_specs=[("amt20", 0.0, -1), ("circ_mv", 1.0, -1)], peg_filter=2.0),
     "结构1: mv主干(v5h骨架)+PEG<2 (na剔除)"),
    ("a4b_s1b_peg15",  dict(ext_mode="zscore", ext_specs=[("amt20", 0.0, -1), ("circ_mv", 1.0, -1)], peg_filter=1.5),
     "结构1: mv主干+PEG<1.5 (na剔除)"),
    ("a4b_s1c_pegq60", dict(ext_mode="zscore", ext_specs=[("amt20", 0.0, -1), ("circ_mv", 1.0, -1)], peg_filter_q=0.6, peg_na_keep=1),
     "结构1: mv主干+PEG≤60分位 (na保留)"),
    ("a4b_s2a_gqblend", dict(ext_mode="zscore", ext_specs=[("amt20", 0.0, -1), ("circ_mv", 0.6, -1), ("grw", 0.2, 1.0), ("bufq", 0.2, 1.0)]),
     "结构2: 0.6·(-z mv)+0.2·grw+0.2·bufq 均衡复合"),
    ("a4b_s2b_gqrank", dict(ext_mode="ranksum", ext_specs=[("log_mv", 1.0, -1), ("npg", 0.6, 1.0), ("bufq", 0.6, 1.0), ("gpersist", 0.3, 1.0)]),
     "结构2: ranksum(-log_mv, npg, bufq, gpersist)"),
    ("a4b_s2c_growdom", dict(ext_mode="zscore", ext_specs=[("amt20", 0.0, -1), ("circ_mv", 0.5, -1), ("grw", 0.35, 1.0), ("bufq", 0.15, 1.0)]),
     "结构2: 0.5·(-z mv)+0.35·grw+0.15·bufq 成长主导"),
]

def stage_done(tag):
    for w in ("full", "locked"):
        if not os.path.exists(os.path.join(RESULT, "%s_%s_metrics.json" % (tag, w))):
            return False
    return True

results = {}
for tag, over, desc in CANDS:
    if stage_done(tag):
        LOG("skip", tag)
        continue
    cfg = dict(BASE); cfg.update(over)
    cfg["out_prefix"] = tag + "_full"
    cfg["force_save_artifacts"] = 1
    mk["timing_pos"] = pos_incumbent
    try:
        mF, nav_df, trade_log, holdings_log = run_bt(cfg, market=mk, date_range=FULL_RANGE)
    finally:
        mk.pop("timing_pos", None)
    mL = write_dual_artifacts(tag, mF, nav_df, trade_log, holdings_log,
                              {"cand": tag, "desc": desc, "cfg": {k: v for k, v in over.items()}})
    navH = nav_df[nav_df.index > LOCK_END]["nav"].astype(float)
    hH = [h for h in holdings_log if h["date"] > LOCK_END]
    mH = compute_metrics(navH, {}, hH, len(hH))
    json.dump(mH, open(os.path.join(RESULT, "%s_holdout_metrics.json" % tag), "w"), ensure_ascii=False, indent=2, default=str)
    LOG("%s: full ann=%.4f mdd=%.4f | lock ann=%.4f mdd=%.4f | hold ann=%.4f mdd=%.4f" % (
        tag, mF["annual_return"], mF["max_drawdown"], mL["annual_return"], mL["max_drawdown"],
        mH["annual_return"], mH["max_drawdown"]))
    results[tag] = {"full": {k: mF.get(k) for k in NUM_KEYS}, "locked": {k: mL.get(k) for k in NUM_KEYS},
                    "holdout": {k: mH.get(k) for k in NUM_KEYS}}
    stage_log({"stage": tag, "ok": True, "desc": desc,
               "full": results[tag]["full"], "locked": results[tag]["locked"], "holdout": results[tag]["holdout"]})

# ---------------- IC 阶段 (选股得分月度 IC, 质量宇宙) ----------------
LOG("IC stage...")
from scipy.stats import spearmanr
closes = mk["closes"]
mclose = pd.DataFrame({c: s.resample("ME").last() for c, s in closes.items()})
panel = mk["panel"]
def piv(col):
    return panel.pivot_table(index="date", columns="code", values=col, aggfunc="last")
pmv, pdiv, proe, proa = piv("circ_mv"), piv("div_yield_ttm"), piv("roe_ttm"), piv("roa_ttm")
ppeg, pnpg, prvg, pgp = piv("peg_np"), piv("npg"), piv("rvg"), piv("gpersist")
pgrw, pbufq, ppe = piv("grw"), piv("bufq"), piv("pe_ttm")
fwd = mclose.shift(-1) / mclose - 1.0
months = sorted(set(pmv.index) & set(mclose.index))
months = [m for m in months if m <= mclose.index[-1]]

def zcs(df):
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)

IC_SPECS = {
    "a4b_s1a_peg2":   {"specs": [("circ_mv", 1.0, -1)], "peg_abs": 2.0},
    "a4b_s1b_peg15":  {"specs": [("circ_mv", 1.0, -1)], "peg_abs": 1.5},
    "a4b_s1c_pegq60": {"specs": [("circ_mv", 1.0, -1)], "peg_q": 0.6},
    "a4b_s2a_gqblend": {"specs": [("circ_mv", 0.6, -1), ("grw", 0.2, 1.0), ("bufq", 0.2, 1.0)]},
    "a4b_s2b_gqrank": {"specs": [("circ_mv", 1.0, -1), ("npg", 0.6, 1.0), ("bufq", 0.6, 1.0), ("gpersist", 0.3, 1.0)]},
    "a4b_s2c_growdom": {"specs": [("circ_mv", 0.5, -1), ("grw", 0.35, 1.0), ("bufq", 0.15, 1.0)]},
}
FACTOR_DF = {"circ_mv": pmv, "grw": pgrw, "bufq": pbufq, "npg": pnpg, "gpersist": pgp,
             "peg_np": ppeg, "pe_ttm": ppe}
ic_rows = []
for mth in months:
    px = mclose.loc[mth]; fw = fwd.loc[mth]
    mv = pmv.loc[mth] if mth in pmv.index else None
    if mv is None:
        continue
    dv = pdiv.loc[mth] if mth in pdiv.index else pd.Series(dtype=float)
    re_ = proe.loc[mth] if mth in proe.index else pd.Series(dtype=float)
    ra = proa.loc[mth] if mth in proa.index else pd.Series(dtype=float)
    base_ok = (dv.reindex(mv.index) >= 0.02) & (re_.reindex(mv.index) > 0.15) & \
              (ra.reindex(mv.index) > 0.10) & (px.reindex(mv.index) < 10) & mv.notna()
    row = {"ym": str(mth.date())[:7]}
    for tag, sp in IC_SPECS.items():
        cols = {}
        ok = base_ok.copy()
        for name, w, s in sp["specs"]:
            f = FACTOR_DF[name].loc[mth] if mth in FACTOR_DF[name].index else pd.Series(dtype=float)
            f = f.reindex(mv.index)
            cols[name] = f
            ok &= f.notna()
        if "peg_abs" in sp:
            fpeg = ppeg.loc[mth].reindex(mv.index) if mth in ppeg.index else pd.Series(dtype=float)
            ok &= fpeg.notna() & (fpeg < sp["peg_abs"])
        elif "peg_q" in sp:
            fpeg = ppeg.loc[mth].reindex(mv.index) if mth in ppeg.index else pd.Series(dtype=float)
            avail = fpeg[fpeg.notna()]
            if len(avail) >= 10:
                thr = avail.quantile(sp["peg_q"])
                ok &= fpeg.notna() & (fpeg <= thr)
        sub = ok[ok]
        if len(sub) < 20:
            row[tag] = np.nan
            continue
        sc = None
        for name, w, s in sp["specs"]:
            f = cols[name][sub.index].astype(float)
            mu, sd = f.mean(), f.std()
            zz = (f - mu) / sd if (pd.notna(sd) and sd > 0) else f * 0.0
            con = w * s * zz
            sc = con if sc is None else sc + con
        row[tag] = spearmanr(sc, fw.reindex(sub.index)).correlation
    ic_rows.append(row)
icdf = pd.DataFrame(ic_rows).set_index("ym")
icdf.to_csv(os.path.join(RESULT, "a4b_ic_monthly.csv"))
lockM = icdf[icdf.index <= "2024-06"]
holdM = icdf[icdf.index > "2024-06"]

# ---------------- 容量 / 相关性 / 门禁 ----------------
def capacity_from_holdings(hpath, amt, cap_name=None):
    try:
        h = pd.read_csv(hpath)
    except Exception:
        return None
    vals = []
    for _, r in h.iterrows():
        try:
            d = pd.Timestamp(r["date"]); held = str(r.get("held") or "").split("|")
            held = [c for c in held if c and c != "nan"]
            if len(held) < 5:
                continue
            amts = []
            for c in held:
                a = amt.get(c)
                if a is None:
                    continue
                w20 = a.loc[:d].tail(20).dropna()
                if len(w20) >= 10:
                    amts.append(float(w20.mean()))
            if len(amts) >= 5:
                vals.append(0.05 * float(np.mean(amts)) * len(amts))
        except Exception:
            continue
    return float(np.median(vals)) / 1e8 if vals else None   # 亿元

v5h_hold_path = os.path.join(RESULT, "a7_v5h_xsub_formal_full_holdings.csv")
cap_v5h = capacity_from_holdings(v5h_hold_path, mk["amt"])
LOG("capacity v5h_xsub = %.3f 亿" % (cap_v5h or -1))

def nav_monthly_rets(path):
    try:
        nv = pd.read_csv(path, parse_dates=["date"]).set_index("date")["nav"]
        return nv.resample("ME").last().pct_change().dropna()
    except Exception:
        return None

ref_rets = {}
for name, pat in [("v5h_xsub", "a7_v5h_xsub_formal_full_nav.csv"), ("v2b_trr", "a2c_v2b_trr_formal_full_nav.csv")]:
    p = os.path.join(RESULT, pat)
    if not os.path.exists(p):
        import glob as _g
        cand = _g.glob(os.path.join(RESULT, pat.replace("_formal", "*")))
        p = cand[0] if cand else p
    r = nav_monthly_rets(p)
    if r is not None:
        ref_rets[name] = r
LOG("ref navs loaded:", list(ref_rets.keys()))

INC_ANN = {"v5h_xsub": 0.1574, "v2b_trr": 0.1515}
INC_MDD = {"v5h_xsub": -0.2980, "v2b_trr": -0.2986}

gate_table = {}
summary_cands = {}
for tag, over, desc in CANDS:
    try:
        mF = json.load(open(os.path.join(RESULT, "%s_full_metrics.json" % tag)))
        mL = json.load(open(os.path.join(RESULT, "%s_locked_metrics.json" % tag)))
        mH = json.load(open(os.path.join(RESULT, "%s_holdout_metrics.json" % tag)))
    except FileNotFoundError:
        gate_table[tag] = {"verdict": "MISSING", "desc": desc}
        continue
    icL = icdf[tag].dropna() if tag in icdf else pd.Series(dtype=float)
    icLock = lockM[tag].dropna() if tag in lockM else pd.Series(dtype=float)
    icHold = holdM[tag].dropna() if tag in holdM else pd.Series(dtype=float)
    mean_ic_L = float(icLock.mean()) if len(icLock) else None
    icir_L = float(icLock.mean() / icLock.std()) if len(icLock) > 2 and icLock.std() > 0 else None
    mean_ic_H = float(icHold.mean()) if len(icHold) else None
    capC = capacity_from_holdings(os.path.join(RESULT, "%s_full_holdings.csv" % tag), mk["amt"])
    candR = nav_monthly_rets(os.path.join(RESULT, "%s_full_nav.csv" % tag))
    corrs = {}
    for rn, rr in ref_rets.items():
        if candR is not None:
            j = pd.concat([candR, rr], axis=1).dropna()
            if len(j) > 24:
                corrs[rn] = round(float(j.iloc[:, 0].corr(j.iloc[:, 1])), 4)
    turn = mF.get("monthly_turnover_est")
    g1 = (mean_ic_L is not None and mean_ic_L > 0)
    g2 = (icir_L is not None and icir_L >= 0.25 and (mean_ic_H is None or mean_ic_H > 0))
    g3 = (turn is not None and turn <= 0.60)
    g4 = (capC is not None and cap_v5h is not None and capC >= 0.7 * cap_v5h)
    g5 = (len(corrs) > 0 and max(corrs.values()) < 0.97)
    verdict = "PASS" if all([g1, g2, g3, g4, g5]) else "REJECT"
    gate_table[tag] = {
        "verdict": verdict, "desc": desc,
        "gates": {"g1_ic_locked": "PASS" if g1 else "FAIL",
                  "g2_icir": "PASS" if g2 else "FAIL",
                  "g3_turnover": "PASS" if g3 else "FAIL",
                  "g4_capacity": "PASS" if g4 else "FAIL",
                  "g5_corr": "PASS" if g5 else "FAIL"},
        "ic": {"mean_ic_locked": round(mean_ic_L, 4) if mean_ic_L is not None else None,
               "icir_m_locked": round(icir_L, 4) if icir_L is not None else None,
               "mean_ic_holdout": round(mean_ic_H, 4) if mean_ic_H is not None else None,
               "n_months_locked": int(len(icLock)), "n_months_holdout": int(len(icHold))},
        "capacity_yi": round(capC, 4) if capC is not None else None,
        "capacity_v5h_yi": round(cap_v5h, 4) if cap_v5h is not None else None,
        "corr_vs_incumbent": corrs,
        "metrics_locked": {k: mL.get(k) for k in NUM_KEYS},
        "metrics_full": {k: mF.get(k) for k in NUM_KEYS},
        "metrics_holdout": {k: mH.get(k) for k in NUM_KEYS},
        "vs_bloodline": {
            "ann_minus_best_inc_pp": round((mL.get("annual_return", 0) - max(INC_ANN.values())) * 100, 2),
            "mdd_gap_vs_best_inc_pp": round((mL.get("max_drawdown", 0) - min(INC_MDD.values())) * 100, 2)},
    }
    summary_cands[tag] = {"desc": desc, "locked": gate_table[tag]["metrics_locked"],
                          "holdout": gate_table[tag]["metrics_holdout"], "verdict": verdict}
    LOG("%s verdict=%s icL=%s icirL=%s cap=%.3f亿 corr=%s" % (tag, verdict,
        gate_table[tag]["ic"]["mean_ic_locked"], gate_table[tag]["ic"]["icir_m_locked"], capC or -1, corrs))

json.dump(gate_table, open(os.path.join(RESULT, "a4b_gate_table.json"), "w"), ensure_ascii=False, indent=2)
summary = {
    "task": "task-0364 A4b 阶段A 价值过滤器+成长×质量复合",
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "n_trials": len(CANDS),
    "factor_coverage": cov,
    "incumbents": {"v5h_xsub": "15.74%/-29.80%", "v2b_trr": "15.15%/-29.86%"},
    "bloodline_bar": "新血统线: locked 年化 ≥ max(inc)+2pp 且 MDD 恶化 ≤2pp; 五门禁全过",
    "candidates": summary_cands,
    "gate_table": "results/a4b_gate_table.json",
    "peg_def": "pe_ttm(circ_mv/net_profit_ttm, avail_date PIT) / net_profit_yoy(fin_deep ak 面板 usable_from 月频), 仅 yoy>0",
    "bufq_def": "mean(z(roe_ttm)+z(gp_margin)+z(cf_np_ratio)-z(debt_to_asset)) 月度横截面",
    "grw_def": "mean(z(net_profit_yoy), z(revenue_yoy), z(growth_persist)) 月度横截面",
}
json.dump(summary, open(os.path.join(RESULT, "a4b_backtest_summary.json"), "w"), ensure_ascii=False, indent=2)
LOG("a4b_run.py 全部完成")
