#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r297_run.py — task-0478 [R-297] csad 独立引擎 E2 回测（csad_resid_z 唯一排序核）
  G0 : 实现层惰性对拍 — r297_g0_w0(csad w=0 注入, 全0分) vs r297_g0_null(无注入路径)
       唯一差异 = csad_resid 注入路径; w=0 时贡献严格 0.0 → 两跑须 max|Δnav| < 1e-12
  F1/F2/F3 : ext_specs=[("csad_resid",1.0,-1)] 唯一排序核, n_hold=20/30/50 等权多头
  NaN 政策(R-263 §二.5): 面板缺失 → 0.0 中性贡献, 不剔股不插值 (0.0 非 NaN 通过 ext_filter_all)
  池同 a13: raw_universe=1(四闸门关), xsub_days=365, e1_guard=0; e1_lambda=0(纯 csad 排序核)
  成本 v2(ADV20 平方根冲击) + cost_rate 0.001 + limit_board on; 择时=满仓(独立引擎测纯选股 alpha)
  FULL_RANGE 2006-01-01..2026-08-14(R-253 纪律)
运行: nohup /home/noname/miniconda3/envs/quant/bin/python scripts/r297_run.py > logs/r297_run.log 2>&1 &
"""
import os, sys, json, time, inspect, types
import pandas as pd, numpy as np

sys.path.insert(0, "/home/noname/quant-evolve/scripts")
sys.path.insert(0, "/home/noname/quant-evolve")
os.chdir("/home/noname/quant-evolve")

import a9_common as A9
from a9_common import (RESULT, LOCK_END, load_engine, merge_pb_into_panel,
                       build_timing, write_dual_artifacts, stage_log)
import macro_timing_layer_iter4 as mtl4

t0 = time.time()
def LOG(*a):
    print("[%7.1fs]" % (time.time() - t0), *a, flush=True)

HP = "/home/noname/quant-evolve"
W297 = os.path.join(HP, "results/work/r297")
os.makedirs(W297, exist_ok=True)
PANEL_PATH = os.path.join(HP, "results/work/r263/csad_resid_monthly.csv")
import hashlib
PANEL_MD5 = hashlib.md5(open(PANEL_PATH, "rb").read()).hexdigest()
assert PANEL_MD5 == "416019cf5368bde27c289949069f6193", "panel md5 mismatch"
_pf = pd.read_csv(PANEL_PATH, dtype={"ym": str, "code": str})
PANEL = dict(zip(zip(_pf["code"], _pf["ym"]), _pf["resid_z"].astype(float)))
LOG("frozen panel loaded: rows=%d md5=%s" % (len(_pf), PANEL_MD5))

# ---------------- R297 命名空间 ----------------
class _NS(object):
    pass
_R297 = _NS()
_R297.hits = {}
_R297.miss = {}

def _prev_month_key(ts):
    y, m = ts.year, ts.month - 1
    if m == 0:
        y, m = y - 1, 12
    return "%04d-%02d" % (y, m)

def _get(code, d):
    try:
        ym = _prev_month_key(pd.Timestamp(d))
        v = PANEL.get((code, ym))
        if v is None or not np.isfinite(v):
            _R297.miss[d] = _R297.miss.get(d, 0) + 1
            return 0.0
        _R297.hits[d] = _R297.hits.get(d, 0) + 1
        return float(v)
    except Exception:
        return 0.0
_R297.get = _get

# ---------------- 链式补丁: a9 patch 源码 + R297 csad 唯一因子注入 ----------------
# G0 设计(R-253/R-264 改良版): G0W0(w=0 注入, 读面板) vs G0N(null, csad_resid 分支返回常量 0.0 不读面板)
#  两者 w=0 → 贡献均严格 0.0, 全池全 0 分 → 同稳定序 → NAV 须逐位一致(max|Δnav|<1e-12)
#  null 分支存在(避免 ext_filter_all 过滤掉全池), 但值恒定 0.0 → 唯一差异 = 面板读取路径
R297_INJECT = '''    # ---- R297 (task-0478): csad_resid 唯一排序核分支 ----
    OLD_FV = \'\'\'elif _name == "amihud20":\'\'\'
    NEW_FV = \'\'\'elif _name == "csad_resid":
                            _v = _R297.get(_c, d)
                        elif _name == "amihud20":\'\'\'
    assert SRC.count(OLD_FV) == 1, "R297 fval anchor=%d" % SRC.count(OLD_FV)
    SRC = SRC.replace(OLD_FV, NEW_FV)
'''
R297_INJECT_NULL = '''    # ---- R297 null (task-0478): csad_resid 常量 0.0(不读面板, 惰性对照) ----
    OLD_FV = \'\'\'elif _name == "amihud20":\'\'\'
    NEW_FV = \'\'\'elif _name == "csad_resid":
                            _v = 0.0
                        elif _name == "amihud20":\'\'\'
    assert SRC.count(OLD_FV) == 1, "R297-null fval anchor=%d" % SRC.count(OLD_FV)
    SRC = SRC.replace(OLD_FV, NEW_FV)
'''

def build_patched_engine(engine, null_inject=False):
    psrc = inspect.getsource(A9.patch_engine)
    a1 = '    mod = types.ModuleType("a9_engine")'
    a2 = "    mod.__dict__.update(engine.__dict__)"
    assert psrc.count(a1) == 1 and psrc.count(a2) == 1, "chain anchors"
    inj = R297_INJECT_NULL if null_inject else R297_INJECT
    psrc = psrc.replace(a1, inj + a1)
    psrc = psrc.replace(a2, a2 + '\n    mod.__dict__["_R297"] = _R297')
    g = dict(globals())
    exec(compile(psrc, "<patch_engine_r297>", "exec"), g)
    return g["patch_engine"](engine)

engine, q4b = load_engine()
run_b, meta = build_patched_engine(engine, null_inject=False)          # csad 注入路径
run_null, meta_null = build_patched_engine(engine, null_inject=True)   # 无注入(G0 null)
LOG("patch ok (r297 csad sole-kernel inject)", meta, "| null", meta_null)

LOG("加载全量池市场(数分钟)...")
mk = q4b.load_fullpool_market(verbose=False)
LOG("市场加载完成 codes=%d" % len(mk["codes"]))
cov = merge_pb_into_panel(mk)
# 独立引擎: 满仓(无 q3z 择时), timing_pos 全 1.0
trade_dates = pd.DatetimeIndex(sorted(mk["panel"]["date"].unique()))
pos_full = pd.Series(1.0, index=trade_dates)
LOG("满仓择时构建完成(独立引擎纯选股): n_dates=%d" % len(pos_full))

BASE = dict(sort="mv", div_min=0.02, roe_min=0.15, roa_min=0.10, n_hold=20,
            price_cap=10.0, min_amt=0.0, drawdown_control=0, cost_model="v2",
            limit_board="on", capital_base=1e7,
            dd_thresh=0.20, dd_reduce=0.5, dd_recover=0.05,
            cost_rate=0.001, limit_up_pct=0.098)
FULL_RANGE = ("2006-01-01", "2026-08-14")
CSAD_SPECS = [("csad_resid", 1.0, -1)]   # 唯一排序核, 负向
ZERO_SPECS = [("csad_resid", 0.0, -1)]   # G0 w=0

def eng_cfg(specs, n_hold):
    return dict(sort="ext", ext_mode="ranksum", ext_specs=specs,
                ext_filter_all=1, raw_universe=1, e1_guard=0, xsub_days=365.0,
                e1_lambda=0.0, e1_deadzone=0.0, n_hold=n_hold)

def stage_done(tag):
    for w in ("full", "locked"):
        if not os.path.exists(os.path.join(RESULT, "%s_%s_metrics.json" % (tag, w))):
            return False
    return True

def run_stage(tag, cfg_over, meta_extra, runner=None):
    if stage_done(tag):
        LOG("skip", tag, "(done)")
        return None
    _run = runner or run_b
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
    echo["ext_specs"] = cfg.get("ext_specs")
    echo.update(meta_extra or {})
    mk["timing_pos"] = pos_full
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

# ---------------- G0 对拍(实现层惰性) ----------------
def _nav(tag):
    return pd.read_csv(os.path.join(RESULT, "%s_full_nav.csv" % tag),
                       parse_dates=["date"]).set_index("date")["nav"].astype(float)

def g0_check():
    new = _nav("r297_g0_w0")
    null = _nav("r297_g0_null")
    if not new.index.equals(null.index):
        return False, None, "index mismatch n_new=%d n_null=%d" % (len(new), len(null))
    dmax = float(np.abs(new.values - null.values).max())
    return (dmax < 1e-12), dmax, "impl-parity max|dnav|=%.3e (n=%d)" % (dmax, len(new))

# ---------------- 台账(先登记后判定) ----------------
def ledger_append(exp_id, tag, n_hold, mF, mL):
    entry = {
        "run_id": "bt_%s_20260824" % tag,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "backtest", "version": "-",
        "code_ref": "scripts/r297_run.py@task-0478 (a9_common.patch_engine 链式: ext_specs=[csad_resid 唯一负权], 引擎文件零改动)",
        "params_hash": None,
        "data_snapshot": {"kline_as_of": "2026-08-20",
                          "panel": "results/work/r263/csad_resid_monthly.csv",
                          "panel_md5": PANEL_MD5,
                          "note": "R-297 csad 独立引擎 E2 预注册网格"},
        "metrics": {
            "experiment_id": exp_id,
            "features": {"universe": "raw全宇宙(四质量闸门全关) + xsub365 + e1_guard=0",
                         "sort": "ranksum(csad_resid_z 唯一排序核, 负向)",
                         "n_hold": n_hold, "csad_sign": -1,
                         "nan_policy": "面板缺失置0中性贡献(R-263 §二.5), 不剔股不插值",
                         "e1_lambda": 0.0, "e1_deadzone": 0.0,
                         "timing": "满仓(独立引擎纯选股, 无 q3z)"},
            "full": {k: mF.get(k) for k in ("annual_return", "max_drawdown", "sharpe", "calmar")},
            "locked": {k: mL.get(k) for k in ("annual_return", "max_drawdown", "sharpe", "calmar")},
        },
        "logic": "R-297 §二 预注册网格点: csad_resid_z 唯一选股排序核(负向), Top-N 等权多头, 独立引擎与 a13 零权重重叠",
    }
    with open(os.path.join(RESULT, "experiment-ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

def load_metrics_pair(tag):
    mF = json.load(open(os.path.join(RESULT, "%s_full_metrics.json" % tag)))
    mL = json.load(open(os.path.join(RESULT, "%s_locked_metrics.json" % tag)))
    return mF, mL

# ---------------- 主流程 ----------------
RUNS = [
    ("r297_g0_w0",  "G0W0", ZERO_SPECS, 20, None),
    ("r297_g0_null","G0N",  ZERO_SPECS, 20, run_null),
    ("r297_f1_top20","F1",  CSAD_SPECS, 20, None),
    ("r297_f2_top30","F2",  CSAD_SPECS, 30, None),
    ("r297_f3_top50","F3",  CSAD_SPECS, 50, None),
]
EXP_ID = {"F1": "IT-R297-01", "F2": "IT-R297-02", "F3": "IT-R297-03"}

for tag, tid, specs, nh, runner in RUNS:
    cfg = eng_cfg(specs, nh)
    LOG("== %s %s n_hold=%d specs=%s ==" % (tid, tag, nh, specs))
    run_stage(tag, cfg, {"experiment": "R-297 E2", "n_hold": nh, "panel_md5": PANEL_MD5}, runner=runner)
    if tid == "G0W0":
        continue
    if tid == "G0N":
        ok, dmax, msg = g0_check()
        LOG("G0 对拍(实现层惰性):", msg, "=>", "PASS" if ok else "FAIL")
        stage_log({"stage": "R297_G0_gate_impl_parity", "ok": bool(ok), "max_abs_nav_diff": dmax})
        if not ok:
            LOG("!!! G0 失败 — csad 注入在 w=0 下非惰性, 中止(R-297 §五)")
            sys.exit(3)
        continue
    mF, mL = load_metrics_pair(tag)
    exp_id = EXP_ID[tid]
    # 简单台账去重
    p = os.path.join(RESULT, "experiment-ledger.jsonl")
    if not any('"%s"' % exp_id in line for line in (open(p, encoding="utf-8") if os.path.exists(p) else [])):
        ledger_append(exp_id, tag, nh, mF, mL)
        LOG("ledger appended:", exp_id)
    else:
        LOG("ledger already has", exp_id)

LOG("r297_run.py 全部完成 (G0 惰性对拍 + F1/F2/F3 + 台账 3 点)")
