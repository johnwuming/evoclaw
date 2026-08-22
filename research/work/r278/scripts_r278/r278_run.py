#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r278_run.py — task-0455 [R-278 §七.2-3] PCR 情绪新入场调制 E2 引擎级对照
  G0: λ=1/veto=0 恒不触发注入 vs 原 a9 补丁路径 — 同数据同截断逐位一致 (max|Δnav|=0)
  T1: 新入场降权 λ=0.7 | T2: λ=0.8 | T3: 确认项否决 ⌈0.2×len(added)⌉ 最弱新入场
实现 (R-278 §三, 引擎文件零改动, r252_run.py 补丁链同构):
  ① veto 注入点: added 计算行后, 干预月否决 ranksum 序末 k 只 (同步收缩 target_pool/added)
  ② 权重块: 干预月 留仓=1/den, 新入场=λ/den, den=n_ret+λ·n_add (满仓无现金)
  ③ 成本v2 买入笔 order_amt 按实际目标权重 (×wbuy; 非干预月 wbuy=1.0 位逐位不变)
  λ=1 且 veto=0 → 全走原字面分支 → G0 结构保证
信号: work/r278/pcroi_states.csv (冻结, md5 校验), _prev_month_key(d) 前一自然月 PIT
运行: nohup /home/noname/miniconda3/envs/quant/bin/python scripts/r278_run.py > logs/r278_run.log 2>&1 &
"""
import os, sys, json, time, inspect, types, hashlib
import pandas as pd, numpy as np

sys.path.insert(0, "/home/noname/quant-evolve/scripts")
sys.path.insert(0, "/home/noname/quant-evolve")
os.chdir("/home/noname/quant-evolve")

import a9_common as A9
from a9_common import (RESULT, LOCK_END, load_engine, merge_pb_into_panel,
                       build_timing, write_dual_artifacts, stage_log, diff_metrics)
import macro_timing_layer_iter4 as mtl4

t0 = time.time()
def LOG(*a):
    print("[%7.1fs]" % (time.time() - t0), *a, flush=True)

W278 = os.path.join(RESULT, "work", "r278")
STATES = pd.read_csv(os.path.join(W278, "pcroi_states.csv"),
                     dtype={"ym": str}).set_index("ym")
STATES_MD5 = hashlib.md5(open(os.path.join(W278, "pcroi_states.csv"), "rb").read()).hexdigest()
assert STATES.index.is_unique
LOG("frozen pcr_oi states loaded: n=%d md5=%s" % (len(STATES), STATES_MD5))

ACTIVE_TH = 0.30

class _NS(object):
    pass
_R278 = _NS()
_R278._wb = {}
_R278.LAM = 1.0
_R278.VETO = 0.0

def _prev_month_key(ts):
    y, m = ts.year, ts.month - 1
    if m == 0:
        y, m = y - 1, 12
    return "%04d-%02d" % (y, m)

def _sig_pct(d):
    pm = _prev_month_key(pd.Timestamp(d))
    if pm not in STATES.index:
        return None
    v = STATES.loc[pm, "pcroi_pct"]
    return None if pd.isna(v) else float(v)

def _lam(d):
    p = _sig_pct(d)
    if p is None or p > ACTIVE_TH:
        return 1.0
    return float(_R278.LAM)

def _veto_frac(d):
    p = _sig_pct(d)
    if p is None or p > ACTIVE_TH:
        return 0.0
    return float(_R278.VETO)

_R278.lam = _lam
_R278.veto_frac = _veto_frac
_R278.wbuy = lambda c: _R278._wb.get(c, 1.0)

# ---------------- 链式补丁: a9 patch 源码 + R278 调制块 ----------------
R278_INJECT = '''    # ---- R278 (task-0455): PCR 新入场调制 (veto + 降权 + 买入成本实际权重) ----
    OLD_A = \'\'\'            added = [c for c in target_pool if c not in holdings]\'\'\'
    NEW_A = \'\'\'            added = [c for c in target_pool if c not in holdings]
            _vf = _R278.veto_frac(d)
            if _vf > 0.0 and added:
                _k = int(np.ceil(_vf * len(added)))
                if _k >= len(added):
                    _k = len(added)
                _cut = set(added[len(added) - _k:])
                target_pool = [c for c in target_pool if c not in _cut]
                added = [c for c in added if c not in _cut]\'\'\'
    assert SRC.count(OLD_A) == 1, "R278 veto anchor=%d" % SRC.count(OLD_A)
    SRC = SRC.replace(OLD_A, NEW_A)

    OLD_W = \'\'\'            w = 1.0 / len(new_pool) if new_pool else 0.0
            pending_holdings = {c: w for c in new_pool}\'\'\'
    NEW_W = \'\'\'            _R278._wb = {}
            _lam278 = _R278.lam(d)
            _addset = set(added)
            _nadd = sum(1 for c in new_pool if c in _addset)
            if _lam278 < 1.0 and _nadd > 0:
                _nret = len(new_pool) - _nadd
                _den = float(_nret) + _lam278 * float(_nadd)
                _npl = float(len(new_pool))
                _ph = {}
                for c in new_pool:
                    if c in _addset:
                        _wi = _lam278 / _den
                        _R278._wb[c] = _wi * _npl
                    else:
                        _wi = 1.0 / _den
                    _ph[c] = _wi
                pending_holdings = _ph
            else:
                w = 1.0 / len(new_pool) if new_pool else 0.0
                pending_holdings = {c: w for c in new_pool}\'\'\'
    assert SRC.count(OLD_W) == 1, "R278 weight anchor=%d" % SRC.count(OLD_W)
    SRC = SRC.replace(OLD_W, NEW_W)

    OLD_C = \'\'\'                        adv20 = float(win.mean()) if len(win) >= 10 else np.nan
                        order_amt = port_val * w_each
                        r = estimate_cost(order_amt, adv20, side="buy")
                        if r is None:
                            total_cost_frac += cost_rate * 0.5
                        else:
                            total_cost_frac += r["total_bps"] / 1e4 * w_each\'\'\'
    NEW_C = \'\'\'                        adv20 = float(win.mean()) if len(win) >= 10 else np.nan
                        _wbm = _R278.wbuy(c)
                        order_amt = port_val * w_each * _wbm
                        r = estimate_cost(order_amt, adv20, side="buy")
                        if r is None:
                            total_cost_frac += cost_rate * 0.5
                        else:
                            total_cost_frac += r["total_bps"] / 1e4 * (w_each * _wbm)\'\'\'
    assert SRC.count(OLD_C) == 1, "R278 cost anchor=%d" % SRC.count(OLD_C)
    SRC = SRC.replace(OLD_C, NEW_C)
'''

def build_patched_engine(engine):
    psrc = inspect.getsource(A9.patch_engine)
    a1 = '    mod = types.ModuleType("a9_engine")'
    a2 = "    mod.__dict__.update(engine.__dict__)"
    assert psrc.count(a1) == 1 and psrc.count(a2) == 1, "chain anchors"
    psrc = psrc.replace(a1, R278_INJECT + a1)
    psrc = psrc.replace(a2, a2 + '\n    mod.__dict__["_R278"] = _R278')
    g = dict(globals())
    exec(compile(psrc, "<patch_engine_r278>", "exec"), g)
    return g["patch_engine"](engine)

engine, q4b = load_engine()
run_a9, meta = build_patched_engine(engine)          # a9 链 + R278 调制注入
run_a9_orig, meta_orig = A9.patch_engine(engine)      # 原 a9 补丁路径(无注入) — G0 实现层对拍基准
LOG("patch ok (a9 chain + R278 modulation)", meta, "| orig", meta_orig)

LOG("加载全量池市场(数分钟)...")
mk = q4b.load_fullpool_market(verbose=False)
LOG("市场加载完成 codes=%d" % len(mk["codes"]))
TD_END = str(pd.DatetimeIndex(mk["trade_dates"]).max().date())
LOG("market trade_dates end=%s (kline_as_of 披露)" % TD_END)
cov = merge_pb_into_panel(mk)
sig = mtl4.build_timing_signals_iter4({})
pos_incumbent = build_timing(mk, sig, mtl4, ma_window=200, floor=0.30, q3z_on=True)
LOG("q3z_tr 择时构建完成: mean=%.3f" % pos_incumbent.mean())

BASE = dict(sort="mv", div_min=0.02, roe_min=0.15, roa_min=0.10, n_hold=20,
            price_cap=10.0, min_amt=0.0, drawdown_control=0, cost_model="v2",
            limit_board="on", capital_base=1e7,
            dd_thresh=0.20, dd_reduce=0.5, dd_recover=0.05,
            cost_rate=0.001, limit_up_pct=0.098)
# R-253 纪律: FULL_RANGE 终点=在役产物数据终点 2026-08-14; 窗口指标另统一截 2026-08-13
FULL_RANGE = ("2006-01-01", "2026-08-14")
SUM_SPECS = [("log_mv", 1.0, -1), ("amt20", 1.0, -1), ("pb_inv", 0.7, 1.0), ("roe", 0.3, 1.0)]
E1F10DZ = dict(sort="ext", ext_mode="ranksum", ext_specs=SUM_SPECS,
               ext_filter_all=1, raw_universe=1, e1_guard=0, xsub_days=365.0,
               e1_lambda=1.0, e1_deadzone=0.30)

LEDGER = os.path.join(RESULT, "experiment-ledger.jsonl")

def ledger_add(run_id, note, params):
    e = {"run_id": run_id,
         "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
         "type": "backtest", "version": "-",
         "code_ref": "scripts/r278_run.py a9 patch chain + R278 modulation@task-0455 (R-278 预注册照单: 引擎/registry/paper_engine/crontab 零改动)",
         "params_hash": None,
         "data_snapshot": {"pcr_states": "results/work/r278/pcroi_states.csv",
                           "pcr_states_md5": STATES_MD5,
                           "kline_as_of": TD_END,
                           "window": "2006-01-01..2026-08-14, metrics end 2026-08-13",
                           "note": note, "params": params}}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
    LOG("ledger + %s" % run_id)

def stage_done(tag):
    for w in ("full", "locked"):
        if not os.path.exists(os.path.join(RESULT, "%s_%s_metrics.json" % (tag, w))):
            return False
    return True

def run_stage(tag, cfg_over, meta_extra, runner=None):
    if stage_done(tag):
        LOG("skip", tag, "(done)")
        return None
    _run = runner or run_a9
    cfg = dict(BASE); cfg.update(cfg_over)
    cfg["out_prefix"] = tag + "_full"
    cfg["force_save_artifacts"] = 1
    echo = {k: cfg.get(k) for k in ["sort", "cost_model", "limit_board", "capital_base",
                                    "div_min", "roe_min", "roa_min", "n_hold", "price_cap", "min_amt"]}
    echo["raw_universe"] = int(cfg.get("raw_universe", 0))
    echo["e1_guard"] = int(cfg.get("e1_guard", 0))
    echo["e1_lambda"] = cfg.get("e1_lambda", 0)
    echo["e1_deadzone"] = cfg.get("e1_deadzone", 0)
    echo["xsub_days"] = cfg.get("xsub_days", 0)
    echo.update(meta_extra or {})
    mk["timing_pos"] = pos_incumbent
    try:
        mF, nav_df, trade_log, holdings_log = _run(cfg, market=mk, date_range=FULL_RANGE)
    finally:
        mk.pop("timing_pos", None)
    mL = write_dual_artifacts(tag, mF, nav_df, trade_log, holdings_log, echo)
    LOG("%s: full ann=%.4f mdd=%.4f sharpe=%.3f | locked ann=%.4f mdd=%.4f sharpe=%.3f" % (
        tag, mF["annual_return"], mF["max_drawdown"], mF["sharpe"],
        mL["annual_return"], mL["max_drawdown"], mL["sharpe"]))
    stage_log({"stage": tag, "ok": True,
               "full": {k: mF.get(k) for k in ("annual_return", "max_drawdown", "sharpe", "calmar")},
               "locked": {k: mL.get(k) for k in ("annual_return", "max_drawdown", "sharpe", "calmar")}})
    return mF, mL

# ---------------- G0 对拍门 (同数据同截断, R-253 纪律) ----------------
_R278.LAM, _R278.VETO = 1.0, 0.0
run_stage("r278_g0_orig", E1F10DZ, {"stage": "g0_orig"}, runner=run_a9_orig)
run_stage("r278_g0_lam1", E1F10DZ, {"stage": "g0_lam1(lam=1,veto=0 恒不触发)"})

def _nav(tag):
    return pd.read_csv(os.path.join(RESULT, "%s_full_nav.csv" % tag),
                       parse_dates=["date"]).set_index("date")["nav"].astype(float)

new = _nav("r278_g0_lam1"); orig = _nav("r278_g0_orig")
if not new.index.equals(orig.index):
    raise SystemExit("G0 FAIL: index mismatch n_new=%d n_orig=%d" % (len(new), len(orig)))
g0_dmax = float(np.abs(new.values - orig.values).max())
LOG("G0 parity: max|dnav| = %.6e (n=%d)" % (g0_dmax, len(new)))
ref = _nav("a13_rsraw_e1f10dz")
j = new.index.intersection(ref.index)
drift = float(np.abs(new.loc[j].values - ref.loc[j].values).max())
LOG("disclosure: vs 旧在役产物 max|dnav| = %.3e (qfq 重写漂移, R-253 同源)" % drift)
g0_pass = (g0_dmax == 0.0)
json.dump({"g0_dmax": g0_dmax, "n": int(len(new)), "g0_pass": g0_pass,
           "drift_vs_old_artifact": drift},
          open(os.path.join(W278, "g0_result.json"), "w"))
if not g0_pass:
    raise SystemExit("G0 FAIL: 实现缺陷, 修复重跑 (R-278 §四)")
LOG("G0 PASS (逐位一致)")

# ---------------- 网格 T1/T2/T3 (n_trials=3, 先登记后判定) ----------------
_R278.LAM, _R278.VETO = 0.7, 0.0
run_stage("r278_t1_l07", E1F10DZ, {"stage": "t1_lam0.7"})
ledger_add("bt_r278_t1_lam07_20260823", "R-278 T1: 干预月新入场降权 λ=0.7",
           {"form": "deweight_new", "lam": 0.7, "veto_frac": 0.0, "signal": "pcroi_pct<=0.30 roll36m 月末"})

_R278.LAM, _R278.VETO = 0.8, 0.0
run_stage("r278_t2_l08", E1F10DZ, {"stage": "t2_lam0.8"})
ledger_add("bt_r278_t2_lam08_20260823", "R-278 T2: 干预月新入场降权 λ=0.8",
           {"form": "deweight_new", "lam": 0.8, "veto_frac": 0.0, "signal": "pcroi_pct<=0.30 roll36m 月末"})

_R278.LAM, _R278.VETO = 1.0, 0.2
run_stage("r278_t3_v20", E1F10DZ, {"stage": "t3_veto20%最弱新入场"})
ledger_add("bt_r278_t3_veto20_20260823", "R-278 T3: 干预月否决 added 排名最弱 ⌈0.2·len(added)⌉",
           {"form": "veto_weakest_new", "lam": 1.0, "veto_frac": 0.2, "signal": "pcroi_pct<=0.30 roll36m 月末"})

LOG("ALL RUNS DONE g0=%s t1/t2/t3 ok" % g0_pass)
