#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0333 A5 候选回测 runner: 成长×质量复合排序 + E1动量护栏 + G1加强 + PEG过滤 x v2b择时
- 基于 a4d_runner.py 的 patch 机制 (P1-P7 同款), 新增:
  P8: target 携带 growth/quality/momentum 列 (value_lookup + mom_lookup as-of)
  P9: sort=="gq" 成长×质量复合排序分支 (含 E1/G1/PEG 逻辑)
- 等价校验: 新开关全关 (sort=mv, 无 value_cols/mom_cols) == 原引擎 逐位一致 (diffs={})
用法: python3 /tmp/a5_runner.py screen|formal
"""
import os, sys, json, inspect, importlib.util, time
sys.path.insert(0, "/home/noname/quant-evolve/scripts")
sys.path.insert(0, "/home/noname/quant-evolve")
os.chdir("/home/noname/quant-evolve")
import numpy as np, pandas as pd

spec = importlib.util.spec_from_file_location("q4b", "/home/noname/quant-evolve/scripts/q4b_run_BC.py")
q4b = importlib.util.module_from_spec(spec); sys.argv=["q4b_run_BC.py","none"]
spec.loader.exec_module(q4b)
import backtest_dividend_quality_iter as engine
from audit_lock import AUDIT_LOCK_END

FULL=("2006-01-01","2026-08-31"); LOCKED=("2006-01-01",AUDIT_LOCK_END)
SCREEN=("2016-01-01","2026-08-31")
SEEDP={"sort":"mv","div_min":0.02,"roe_min":0.15,"roa_min":0.10,
       "n_hold":20,"price_cap":10.0,"min_amt":0.0}

SRC=inspect.getsource(engine.run_backtest)

# ---- P1 ext 排序分支(a2b/a2c 同款) ----
ANCHOR='kv[1]["circ_mv"] if pd.notna(kv[1]["circ_mv"]) else np.inf'
idx=SRC.find(ANCHOR); assert idx!=-1
start=SRC.rfind("            else:",0,idx); assert start!=-1
EXT_BRANCH=("""            elif sort == "ext":
                tdf = pd.DataFrame(target).T
                def _zext(s):
                    sd = s.std()
                    return (s - s.mean()) / sd if (sd is not None and not pd.isna(sd) and sd > 0) else s * 0.0
                _ef = str(cfg.get("ext_factor", ""))
                _wmv, _wext = [float(x) for x in (cfg.get("ext_weights") or [0.5, 0.5])]
                _vals = {}
                for _c in tdf.index:
                    _v = np.nan
                    try:
                        if _ef == "amount_cv":
                            _a = amt.get(_c)
                            _w = _a.loc[:d].tail(20).dropna() if _a is not None else None
                            if _w is not None and len(_w) >= 10 and float(_w.mean()) > 0:
                                _v = float(_w.std() / _w.mean())
                        elif _ef == "volatility_20d":
                            _r = rets.get(_c)
                            _w = _r.loc[:d].tail(21).dropna() if _r is not None else None
                            if _w is not None and len(_w) >= 15:
                                _v = float(_w.std())
                        else:
                            raise ValueError("unknown ext_factor " + _ef)
                    except Exception:
                        _v = np.nan
                    _vals[_c] = _v
                tdf["ext"] = pd.Series(_vals)
                tdf = tdf[tdf["ext"].notna() & tdf["circ_mv"].notna()]
                if not len(tdf):
                    ranked = []
                else:
                    tdf["score"] = _wmv * (-_zext(tdf["circ_mv"])) + _wext * (-_zext(tdf["ext"]))
                    ranked = sorted(tdf["score"].items(), key=lambda kv: -kv[1])
""")
SRC2=SRC[:start]+EXT_BRANCH+SRC[start:]

# ---- P2 inv_vol 加权(a2c 同款) ----
OLD2=("""            w = 1.0 / len(new_pool) if new_pool else 0.0
            pending_holdings = {c: w for c in new_pool}""")
NEW2=("""            if new_pool and str(cfg.get("weight_mode", "")) == "inv_vol":
                _iv = {}
                for _c in new_pool:
                    _v = float("nan")
                    try:
                        _r = rets.get(_c)
                        _w20 = _r.loc[:d].tail(21).dropna() if _r is not None else None
                        if _w20 is not None and len(_w20) >= 15 and float(_w20.std()) > 0:
                            _v = 1.0 / float(_w20.std())
                    except Exception:
                        _v = float("nan")
                    _iv[_c] = _v
                _ok = {c: v for c, v in _iv.items() if v == v and v > 0}
                if len(_ok) == len(new_pool) and len(_ok) > 0:
                    _s = sum(_ok.values())
                    pending_holdings = {c: v / _s for c, v in _ok.items()}
                else:
                    w = 1.0 / len(new_pool)
                    pending_holdings = {c: w for c in new_pool}
            else:
                w = 1.0 / len(new_pool) if new_pool else 0.0
                pending_holdings = {c: w for c in new_pool}""")
assert SRC2.count(OLD2)==1; SRC2=SRC2.replace(OLD2,NEW2)

# ---- P3 rank_buffer(a2c 同款) ----
OLD3="""            target_pool = [c for c, _ in ranked[:n_hold]]"""
NEW3=("""            _buf_n = int(cfg.get("rank_buffer", 0) or 0)
            if _buf_n > 0 and ranked:
                _rank_of = {c: i for i, (c, _) in enumerate(ranked)}
                _kept = sorted([c for c in holdings if _rank_of.get(c, 10**9) < n_hold + _buf_n],
                               key=lambda c: _rank_of[c])[:n_hold]
                _slots = max(n_hold - len(_kept), 0)
                _keptset = set(_kept)
                _newb = [c for c, _ in ranked[:n_hold] if c not in _keptset][:_slots]
                target_pool = _kept + _newb
            else:
                target_pool = [c for c, _ in ranked[:n_hold]]""")
assert SRC2.count(OLD3)==1; SRC2=SRC2.replace(OLD3,NEW3)

# ---- P4 vt_target(a2c 同款) ----
OLD4="""        eff_ret = day_ret * pos_ratio * timing_ratio"""
NEW4=("""        _vt_t = cfg.get("vt_target", None)
        if _vt_t is not None and float(_vt_t) > 0 and len(nav_history) >= 63:
            _vals = [x[1] for x in nav_history[-63:]]
            _dr = [(_vals[_i + 1] / _vals[_i] - 1.0) for _i in range(len(_vals) - 1)]
            _mu = sum(_dr) / len(_dr)
            _vv = sum((x - _mu) ** 2 for x in _dr) / (len(_dr) - 1)
            _rv = (_vv * 252.0) ** 0.5
            _vt_ratio = min(1.0, max(float(cfg.get("vt_floor", 0.3)), float(_vt_t) / _rv)) if _rv > 0 else 1.0
        else:
            _vt_ratio = 1.0
        eff_ret = day_ret * pos_ratio * timing_ratio * _vt_ratio""")
assert SRC2.count(OLD4)==1; SRC2=SRC2.replace(OLD4,NEW4)

# ---- P5 dd_trigger(a2c 同款) ----
OLD5="""        eff_ret = day_ret * pos_ratio * timing_ratio * _vt_ratio"""
NEW5=("""        _dd_trig = cfg.get("dd_trigger", None)
        _dd_ratio = 1.0
        if _dd_trig is not None and float(_dd_trig) < 0 and len(nav_history) >= 2:
            _st = cfg.setdefault("_dd_state", {"on": False})
            _vals5 = [x[1] for x in nav_history]
            _peak5 = max(_vals5)
            _dd5 = _vals5[-1] / _peak5 - 1.0
            if (not _st["on"]) and _dd5 <= float(_dd_trig):
                _st["on"] = True
            elif _st["on"] and _dd5 >= float(cfg.get("dd_restore", -0.03)):
                _st["on"] = False
            if _st["on"]:
                _dd_ratio = float(cfg.get("dd_cut", 0.5))
        eff_ret = day_ret * pos_ratio * timing_ratio * _vt_ratio * _dd_ratio""")
assert SRC2.count(OLD5)==1; SRC2=SRC2.replace(OLD5,NEW5)

# ---- P6/P8(新): target 携带 value+momentum 列 (lookup as-of, 不改 panel) ----
OLD6=("""                target[code] = {
                    "circ_mv": fund.loc[code, "circ_mv"],
                    "div_yield_ttm": fund.loc[code, "div_yield_ttm"],
                    "roe_ttm": fund.loc[code, "roe_ttm"],
                    "roa_ttm": fund.loc[code, "roa_ttm"],
                    "price": price,
                }""")
NEW6=("""                _vcols = cfg.get("value_cols") or []
                _mcols = cfg.get("mom_cols") or []
                _vrow = {}
                _vlk = mk.get("value_lookup") if isinstance(mk, dict) else None
                if _vlk is not None:
                    _vdf = _vlk.get(code)
                    if _vdf is not None and len(_vdf):
                        _vl = _vdf[_vdf.index <= d]
                        if len(_vl):
                            _last = _vl.iloc[-1]
                            for _vc in _vcols + _mcols:
                                if _vc in _last.index and pd.notna(_last[_vc]):
                                    _vrow[_vc] = _last[_vc]
                _mlk = mk.get("mom_lookup") if isinstance(mk, dict) else None
                if _mlk is not None:
                    _mdf = _mlk.get(code)
                    if _mdf is not None and len(_mdf):
                        _ml = _mdf[_mdf.index <= d]
                        if len(_ml):
                            _lastm = _ml.iloc[-1]
                            for _mc in _mcols:
                                if _mc in _lastm.index and pd.notna(_lastm[_mc]):
                                    _vrow[_mc] = _lastm[_mc]
                target[code] = {
                    "circ_mv": fund.loc[code, "circ_mv"],
                    "div_yield_ttm": fund.loc[code, "div_yield_ttm"],
                    "roe_ttm": fund.loc[code, "roe_ttm"],
                    "roa_ttm": fund.loc[code, "roa_ttm"],
                    "price": price,
                    **_vrow,
                }""")
assert SRC2.count(OLD6)==1; SRC2=SRC2.replace(OLD6,NEW6)

# ---- P9(新): sort=="gq" 成长×质量复合排序 (插到 sort=="div" 分支前) ----
GQ_BRANCH=("""            elif sort == "gq":
                tdf = pd.DataFrame(target).T
                for _c in ["revenue_yoy","net_profit_yoy","profit_accel","buf_quality","cf_np_ratio","peg_np","ret120","dist250h"]:
                    if _c not in tdf.columns:
                        tdf[_c] = np.nan
                def _zg(s):
                    sd = s.std()
                    return (s - s.mean()) / sd if (sd is not None and not pd.isna(sd) and sd > 0) else s * 0.0
                _wmv, _wgq = [float(x) for x in (cfg.get("gq_weights") or [0.6, 0.4])]
                tdf["grw"] = _zg(tdf["revenue_yoy"]) + _zg(tdf["net_profit_yoy"]) + 0.5 * _zg(tdf["profit_accel"])
                tdf["qly"] = _zg(tdf["buf_quality"]) + _zg(tdf["cf_np_ratio"])
                tdf["gq"] = _zg(tdf["grw"]) + _zg(tdf["qly"])
                tdf["score"] = _wmv * (-_zg(tdf["circ_mv"])) + _wgq * _zg(tdf["gq"])
                # E1 动量护栏: ret120 < -30% 排除 (买入时深跌)
                if cfg.get("e1_guard"):
                    tdf = tdf[tdf["ret120"].isna() | (tdf["ret120"] > -0.30)]
                # G1 加强: 接近年高点(dist250h>-10%) 且 ret120>0 → 加分
                if cfg.get("g1_boost"):
                    _g1 = (tdf["dist250h"] > -0.10) & (tdf["ret120"] > 0)
                    tdf["score"] = tdf["score"] + _g1.astype(float) * float(cfg.get("g1_bonus", 0.5))
                # PEG<2 软过滤 (价值降级为过滤)
                if cfg.get("peg_max"):
                    tdf = tdf[tdf["peg_np"].isna() | (tdf["peg_np"] < float(cfg["peg_max"]))]
                tdf = tdf[tdf["circ_mv"].notna()]
                if not len(tdf):
                    ranked = []
                else:
                    ranked = sorted(tdf["score"].items(), key=lambda kv: -kv[1])
""")
div_anchor = SRC2.find('            elif sort == "div":')
assert div_anchor != -1
SRC3 = SRC2[:div_anchor] + GQ_BRANCH + SRC2[div_anchor:]

G = dict(engine.__dict__)
exec(compile(SRC3, "<run_backtest_a5>", "exec"), G)
run_backtest_a5 = G["run_backtest"]

def base_cfg(out_prefix, **kw):
    cfg = dict(engine.DEFAULTS); cfg.update(SEEDP)
    cfg.update(cost_model="v2", limit_board="on", capital_base=1e7,
               force_save_artifacts=1, out_prefix=out_prefix)
    cfg.update(kw); return cfg

def metrics_of(m):
    return {k: m.get(k) for k in ["annual_return","max_drawdown","sharpe","calmar",
            "cumulative_return","monthly_win_rate","years","num_rebalance","avg_holdings","monthly_turnover_est"]}

def cmp_metrics(m, ref_json, m_ref=None):
    ref = m_ref if m_ref is not None else json.load(open(ref_json))
    diffs = {}
    for k in ["annual_return","max_drawdown","sharpe","calmar","num_rebalance","cumulative_return"]:
        a,b = m.get(k), ref.get(k)
        ra = round(float(a), 4) if a is not None else None
        rb = round(float(b), 4) if b is not None else None
        if ra != rb: diffs[k] = (ra, rb)
    return diffs

t_start=time.time()
print("加载全量池市场(需数分钟)...", flush=True)
mk = q4b.load_fullpool_market(verbose=False)
print("市场加载完成", flush=True)

# ---- 基本面 lookup (从 a4d_value_panel 取 growth/quality 字段) ----
vp = pd.read_parquet("/home/noname/quant-evolve/results/a4d_value_panel.parquet")
vp["code"] = vp["code"].astype(str).str.zfill(6)
vp["date"] = pd.to_datetime(vp["date"])
GQCOLS = ["revenue_yoy","net_profit_yoy","profit_accel","buf_quality","cf_np_ratio","peg_np"]
vp = vp[["code","date"]+GQCOLS].sort_values(["code","date"])
vlk = {}
for c, g in vp.groupby("code"):
    g2 = g.drop_duplicates("date").set_index("date")
    vlk[c] = g2
mk["value_lookup"] = vlk
print("value_lookup codes:", len(vlk), flush=True)

# ---- 动量 lookup: ret120 / dist250h (从日线 close 计算, as-of) ----
closes = mk["closes"]
mom_lookup = {}
for code, cl in closes.items():
    if cl is None or len(cl) < 260:
        continue
    cl = cl.sort_index()
    r120 = cl / cl.shift(120) - 1.0
    d250 = cl / cl.rolling(250).max() - 1.0
    df = pd.DataFrame({"ret120": r120, "dist250h": d250})
    mom_lookup[code] = df
mk["mom_lookup"] = mom_lookup
print("mom_lookup codes:", len(mom_lookup), flush=True)

# ---- 择时仓位序列 (v2b_trr 血统: q3z × EW-MA200 双信号) ----
import macro_timing_layer_iter4 as mtl4
sig = mtl4.build_timing_signals_iter4({})
pos_q3z = mtl4.compute_pos_ratio_iter4(sig, {}, type_key="q3z", save=False)
rets_all = mk["rets"]
ew_ret = pd.DataFrame(rets_all).mean(axis=1)
ew_idx = (1.0 + ew_ret.fillna(0.0)).cumprod()
ma200 = ew_idx.rolling(200).mean()
ew_m = ew_idx.resample("ME").last(); ma_m = ma200.resample("ME").last()
trend_f = pd.Series(np.where(ew_m > ma_m, 1.0, 0.6), index=ew_m.index)
trend_f[ma_m.isna()] = 1.0
pos_tr = trend_f.reindex(pos_q3z.index).fillna(1.0)
pos_q3z_tr = (pos_q3z * pos_tr)
POS = {"q3z": pos_q3z, "q3z_tr": pos_q3z_tr}
print("pos means:", {k: round(float(v.mean()),3) for k,v in POS.items()}, flush=True)

# ---- 等价性校验: 原引擎 vs 本 runner(新开关全关), 必须逐位一致 ----
print("== 等价性校验(a5 runner, 原引擎 vs patched 开关全关) ==", flush=True)
def run_ref(market, cfg, rng):
    mkt2 = dict(market)
    mkt2["panel"] = market["panel"]
    return engine.run_backtest(cfg, market=mkt2, date_range=rng)

for tag, rng in [("full", FULL), ("locked", LOCKED)]:
    mk["timing_pos"] = pos_q3z_tr
    cfgR = base_cfg("a5x_ref_%s" % tag)
    m_ref = run_ref(mk, cfgR, rng)
    cfgE = base_cfg("a5x_equiv_%s" % tag)
    m_eq = run_backtest_a5(cfgE, market=mk, date_range=rng)
    mk.pop("timing_pos", None)
    d = cmp_metrics(m_eq, None, m_ref)
    print("  %s diffs:" % tag, d, flush=True)
    if d: raise SystemExit("EQUIV_FAIL_%s" % tag)
    na = pd.read_csv("results/a5x_equiv_%s_nav.csv" % tag)["nav"]
    nb = pd.read_csv("results/a5x_ref_%s_nav.csv" % tag)["nav"]
    same = int((na.values == nb.values).sum())
    print("  %s nav rows eq/ref=%d/%d exact=%d" % (tag, len(na), len(nb), same), flush=True)
    if same != len(na) or same != len(nb):
        raise SystemExit("EQUIV_NAV_MISMATCH_%s" % tag)
print("  -> EQUIV_OK (patched 开关全关 == 原引擎 逐位一致)", flush=True)

MODE = sys.argv[1] if len(sys.argv) > 1 else "screen"
RANGE = {"screen": SCREEN, "formal_full": FULL, "formal_locked": LOCKED}

summary = {"task":"task-0333 A5","generated_at":time.strftime("%Y-%m-%d %H:%M:%S"),
           "mode":MODE,"equiv_check":{"method":"原引擎 vs patched 开关全关(同一市场, nav 逐位一致)","full_ok":True,"locked_ok":True},
           "candidates":{}}

GQ_BASE = dict(value_cols=GQCOLS, mom_cols=["ret120","dist250h"])
CANDS = [
    ("v4a_gqe1", dict(sort="gq", gq_weights=[0.6,0.4], e1_guard=True, **GQ_BASE), "q3z_tr"),
    ("v4b_mve1", dict(sort="gq", gq_weights=[1.0,0.0], e1_guard=True, **GQ_BASE), "q3z_tr"),
    ("v4c_gqpeg", dict(sort="gq", gq_weights=[0.6,0.4], e1_guard=True, peg_max=2.0, **GQ_BASE), "q3z_tr"),
    ("v4d_gqg1", dict(sort="gq", gq_weights=[0.5,0.5], e1_guard=True, g1_boost=True, g1_bonus=0.5, **GQ_BASE), "q3z_tr"),
    ("v4e_gqg1x", dict(sort="gq", gq_weights=[0.5,0.5], e1_guard=True, g1_boost=True, g1_bonus=0.5, **GQ_BASE), None),
]

if MODE == "screen":
    for ver, kw, pk in CANDS:
        mk["timing_pos"] = POS[pk] if pk else None
        try:
            out = "a5_%s_screen" % ver
            cfg = base_cfg(out, **kw)
            m = run_backtest_a5(cfg, market=mk, date_range=RANGE["screen"])
            summary["candidates"].setdefault(ver, {})["screen"] = metrics_of(m)
            print("  %s: ann=%.4f mdd=%.4f sharpe=%.3f calmar=%.3f" % (ver,
                m["annual_return"], m["max_drawdown"], m["sharpe"], m["calmar"]), flush=True)
        finally:
            mk.pop("timing_pos", None)
else:
    for ver, kw, pk in CANDS:
        print("== 候选 %s (pos=%s) ==" % (ver, pk), flush=True)
        for tag in ["formal_locked", "formal_full"]:
            rng = RANGE[tag]
            out = "a5_%s_%s" % (ver, tag)
            cfg = base_cfg(out, **kw)
            mk["timing_pos"] = POS[pk] if pk else None
            try:
                m = run_backtest_a5(cfg, market=mk, date_range=rng)
            finally:
                mk.pop("timing_pos", None)
            summary["candidates"].setdefault(ver, {})[tag] = metrics_of(m)
            print("  %s %s: ann=%.4f mdd=%.4f sharpe=%.3f calmar=%.3f" % (ver, tag,
                m["annual_return"], m["max_drawdown"], m["sharpe"], m["calmar"]), flush=True)

with open("/home/noname/quant-evolve/results/a5_backtest_summary_%s.json" % MODE, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)
print("A5_%s_DONE" % MODE.upper(), round(time.time()-t_start,1), "s", flush=True)
