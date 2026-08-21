#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r263_run.py — task-0426 [R-263 §十.3-4] csad 残差因子 E2 引擎级对照
  G0 : 同数据实现层对拍 — r263_g0_w0(R263 注入 w=0) vs r263_g0_orig(原 a9 路径, 无注入)
       唯一差异 = csad_resid 第5因子注入路径; 须 max|Δnav| < 1e-12 (w=0 时 IEEE s+±0.0≡s, 新项追加求和末位)
  M1.1 (w=0.3) / M1.2 (w=0.5): ext_specs 追加 ("csad_resid", w, -1) 负权第5因子, 引擎文件零改动
  NaN 政策(R-263 §二.5): 冻结面板缺失 → 0.0 中性贡献, 不剔股不插值
  复用 a13/a15 runner 路径(a9_common), 成本/护栏/择时与在役完全同参; FULL_RANGE 终点 2026-08-14(R-253 纪律)
  台账: IT-R263-01/02 每点跑完立即登记(先登记后判定); G0 不入台账
  dump: 每次调仓全池最终排序分(含 e1 惩罚)落盘 work/r263/dump_{tag}.parquet → G2 复合 IC 用
运行: nohup /home/noname/miniconda3/envs/quant/bin/python scripts/r263_run.py > logs/r263_run.log 2>&1 &
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
W263 = os.path.join(HP, "results/work/r263")
PANEL_PATH = os.path.join(W263, "csad_resid_monthly.csv")
PANEL_MD5 = open(PANEL_PATH + ".md5").read().split()[0]
import hashlib
assert hashlib.md5(open(PANEL_PATH, "rb").read()).hexdigest() == PANEL_MD5, "panel md5 mismatch"
_pf = pd.read_csv(PANEL_PATH, dtype={"ym": str, "code": str})
PANEL = dict(zip(zip(_pf["code"], _pf["ym"]), _pf["resid_z"].astype(float)))
LOG("frozen panel loaded: rows=%d md5=%s" % (len(_pf), PANEL_MD5))

# ---------------- R263 命名空间 ----------------
class _NS(object):
    pass
_R263 = _NS()
_R263.hits = {}
_R263.miss = {}
_R263.dumps = []

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
            _R263.miss[d] = _R263.miss.get(d, 0) + 1
            return 0.0
        _R263.hits[d] = _R263.hits.get(d, 0) + 1
        return float(v)
    except Exception:
        return 0.0
_R263.get = _get

def _dump(d, score):
    try:
        _R263.dumps.append((pd.Timestamp(d), dict(score)))
    except Exception:
        pass
_R263.dump = _dump

# ---------------- 链式补丁: a9 patch 源码 + R263 注入 ----------------
R263_INJECT = '''    # ---- R263 (task-0426): csad_resid 第5因子分支 + 全池排序分 dump ----
    OLD_FV = \'\'\'elif _name == "amihud20":\'\'\'
    NEW_FV = \'\'\'elif _name == "csad_resid":
                            _v = _R263.get(_c, d)
                        elif _name == "amihud20":\'\'\'
    assert SRC.count(OLD_FV) == 1, "R263 fval anchor=%d" % SRC.count(OLD_FV)
    SRC = SRC.replace(OLD_FV, NEW_FV)
    OLD_DM = \'\'\'ranked = sorted(_score.items(), key=lambda kv: -kv[1])\'\'\'
    NEW_DM = \'\'\'try:
                        _R263.dump(d, _score)
                    except Exception:
                        pass
                    ranked = sorted(_score.items(), key=lambda kv: -kv[1])\'\'\'
    assert SRC.count(OLD_DM) == 1, "R263 dump anchor=%d" % SRC.count(OLD_DM)
    SRC = SRC.replace(OLD_DM, NEW_DM)
'''

def build_patched_engine(engine):
    psrc = inspect.getsource(A9.patch_engine)
    a1 = '    mod = types.ModuleType("a9_engine")'
    a2 = "    mod.__dict__.update(engine.__dict__)"
    assert psrc.count(a1) == 1 and psrc.count(a2) == 1, "chain anchors"
    psrc = psrc.replace(a1, R263_INJECT + a1)
    psrc = psrc.replace(a2, a2 + '\n    mod.__dict__["_R263"] = _R263')
    g = dict(globals())
    exec(compile(psrc, "<patch_engine_r263>", "exec"), g)
    return g["patch_engine"](engine)

engine, q4b = load_engine()
run_a9, meta = build_patched_engine(engine)           # a9 链 + R263 注入
run_a9_orig, meta_orig = A9.patch_engine(engine)       # 原 a9 补丁路径(无注入) — G0 对拍基准
LOG("patch ok (a9 chain + R263 csad 5th-factor inject)", meta, "| orig", meta_orig)

LOG("加载全量池市场(数分钟)...")
mk = q4b.load_fullpool_market(verbose=False)
LOG("市场加载完成 codes=%d" % len(mk["codes"]))
cov = merge_pb_into_panel(mk)
sig = mtl4.build_timing_signals_iter4({})
pos_incumbent = build_timing(mk, sig, mtl4, ma_window=200, floor=0.30, q3z_on=True)
LOG("q3z_tr 择时构建完成: mean=%.3f" % pos_incumbent.mean())

BASE = dict(sort="mv", div_min=0.02, roe_min=0.15, roa_min=0.10, n_hold=20,
            price_cap=10.0, min_amt=0.0, drawdown_control=0, cost_model="v2",
            limit_board="on", capital_base=1e7,
            dd_thresh=0.20, dd_reduce=0.5, dd_recover=0.05,
            cost_rate=0.001, limit_up_pct=0.098)
# R-253 纪律: FULL_RANGE 终点 2026-08-14(在役产物数据终点; 当前 kline 已到 08-20, 不截断则多 4 行)
FULL_RANGE = ("2006-01-01", "2026-08-14")
SUM_SPECS = [("log_mv", 1.0, -1), ("amt20", 1.0, -1), ("pb_inv", 0.7, 1.0), ("roe", 0.3, 1.0)]
E1F10DZ = dict(sort="ext", ext_mode="ranksum", ext_specs=SUM_SPECS,
               ext_filter_all=1, raw_universe=1, e1_guard=0, xsub_days=365.0,
               e1_lambda=1.0, e1_deadzone=0.30)

def specs5(w):
    return SUM_SPECS + [("csad_resid", float(w), -1)]

def stage_done(tag):
    for w in ("full", "locked"):
        if not os.path.exists(os.path.join(RESULT, "%s_%s_metrics.json" % (tag, w))):
            return False
    return True

def save_dump(tag):
    if not _R263.dumps:
        return
    recs = [(d, c, s) for d, m in _R263.dumps for c, s in m.items()]
    df = pd.DataFrame(recs, columns=["date", "code", "score"])
    df.to_parquet(os.path.join(W263, "dump_%s.parquet" % tag), index=False)
    covd = {str(d): [_R263.hits.get(d, 0), _R263.hits.get(d, 0) + _R263.miss.get(d, 0)]
            for d, _ in _R263.dumps}
    json.dump(covd, open(os.path.join(W263, "cov_%s.json" % tag), "w"))
    LOG("dump saved %s: dates=%d rows=%d" % (tag, len(_R263.dumps), len(df)))
    _R263.dumps = []
    _R263.hits = {}
    _R263.miss = {}

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

# ---------------- G0 对拍门(R-253 改良版) ----------------
def _nav(tag):
    return pd.read_csv(os.path.join(RESULT, "%s_full_nav.csv" % tag),
                       parse_dates=["date"]).set_index("date")["nav"].astype(float)

def g0_check():
    new = _nav("r263_g0_w0")
    orig = _nav("r263_g0_orig")
    if not new.index.equals(orig.index):
        return False, None, "index mismatch n_new=%d n_orig=%d" % (len(new), len(orig))
    dmax = float(np.abs(new.values - orig.values).max())
    ref = _nav("a13_rsraw_e1f10dz")
    al = new.reindex(ref.index)
    drift = float(np.abs(al.values - ref.values).max())
    return (dmax < 1e-12), dmax, "impl-parity max|dnav|=%.3e (n=%d); drift-vs-old-artifact max=%.3e" % (dmax, len(new), drift)

# ---------------- 台账(先登记后判定: 每点跑完立即登记, 判定在 eval 阶段) ----------------
def ledger_has(exp_id):
    p = os.path.join(RESULT, "experiment-ledger.jsonl")
    if not os.path.exists(p):
        return False
    for line in open(p, encoding="utf-8"):
        if '"%s"' % exp_id in line:
            return True
    return False

def ledger_append(exp_id, tag, w, mF, mL):
    entry = {
        "run_id": "bt_%s_20260821" % tag,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "backtest", "version": "-",
        "code_ref": "scripts/r263_run.py@task-0426 (a9_common.patch_engine 链式追加 R263: ext_specs 第5因子 csad_resid 负权注入(NaN置0中性), 引擎文件零改动)",
        "params_hash": None,
        "data_snapshot": {"kline_as_of": "2026-08-20",
                          "panel": "results/work/r263/csad_resid_monthly.csv",
                          "panel_md5": PANEL_MD5,
                          "factor_md5": "e9ad0b82851126442174f3eda4d2e105",
                          "vol_panel_md5": "3ad82499f91ad9a678d5704cffb422a0",
                          "note": "R-263 E2 csad 残差因子预注册网格"},
        "metrics": {
            "experiment_id": exp_id,
            "features": {"universe": "raw全宇宙(四质量闸门全关)",
                         "sort": "ranksum(log_mv/amt20/pb_inv0.7/roe0.3 + csad_resid_z 负权)",
                         "csad_w": w, "csad_sign": -1,
                         "nan_policy": "面板缺失置0中性贡献(R-263 §二.5), 不剔股不插值",
                         "e1_lambda": 1.0, "e1_deadzone": 0.30, "xsub": "365d 保留",
                         "timing": "q3z_tr(MA200,w_min0.30) 不变"},
            "full": {k: mF.get(k) for k in ("annual_return", "max_drawdown", "sharpe", "calmar")},
            "locked": {k: mL.get(k) for k in ("annual_return", "max_drawdown", "sharpe", "calmar")},
        },
        "logic": "R-263 §三.2 预注册网格点: ext ranksum 追加第5因子 csad_resid⁻(w), 因子形态只改横截面相对排序, 总仓位/成本/护栏/择时与在役同参",
    }
    with open(os.path.join(RESULT, "experiment-ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

def load_metrics_pair(tag):
    mF = json.load(open(os.path.join(RESULT, "%s_full_metrics.json" % tag)))
    mL = json.load(open(os.path.join(RESULT, "%s_locked_metrics.json" % tag)))
    return mF, mL

# ---------------- 主流程 ----------------
RUNS = [
    ("r263_g0_w0",   "G0W0", 0.0),
    ("r263_g0_orig", "G0B",  None),   # 原 a9 路径基准(无注入, specs4)
    ("r263_m1_w03",  "M11",  0.3),
    ("r263_m1_w05",  "M12",  0.5),
]
EXP_ID = {"M11": "IT-R263-01", "M12": "IT-R263-02"}

for tag, tid, w in RUNS:
    if tid == "G0B":
        LOG("== G0B %s 原 a9 补丁路径基准(无注入, specs4) ==" % tag)
        run_stage(tag, E1F10DZ, {"experiment": "R-263 E2 G0 实现层对拍基准",
                                 "note": "原 a9_common.patch_engine, 无 R263 注入"}, runner=run_a9_orig)
        ok, dmax, msg = g0_check()
        LOG("G0 对拍门(实现层):", msg, "=>", "PASS" if ok else "FAIL")
        stage_log({"stage": "R263_G0_gate_impl_parity", "ok": bool(ok), "max_abs_nav_diff": dmax})
        # 4dp 血统锚警报检查(vs 在役 full_metrics 22.39%/-33.55%, 容差 0.1pp) — 警报级非门控
        mO = json.load(open(os.path.join(RESULT, "%s_full_metrics.json" % "r263_g0_orig")))
        a_diff = abs(mO["annual_return"] - 0.2239) * 100
        m_diff = abs(mO["max_drawdown"] - (-0.3355)) * 100
        LOG("G0 4dp 血统锚: ann=%.6f(Δ%.3fpp) mdd=%.6f(Δ%.3fpp) => %s" % (
            mO["annual_return"], a_diff, mO["max_drawdown"], m_diff,
            "OK" if (a_diff <= 0.1 and m_diff <= 0.1) else "ALERT(暂停判读复查谱系)"))
        if not ok:
            LOG("!!! G0 实现层对拍失败 — R263 注入在 w=0 下非惰性, 中止(R-263 §七.1)")
            save_dump("r263_g0_w0")
            sys.exit(3)
        continue
    cfg5 = dict(E1F10DZ); cfg5["ext_specs"] = specs5(w)
    LOG("== %s %s csad_w=%.1f ==" % (tid, tag, w))
    r = run_stage(tag, cfg5, {"experiment": "R-263 E2", "csad_w": w, "panel_md5": PANEL_MD5})
    save_dump(tag)
    if tid == "G0W0":
        continue  # 门检在 G0B 后统一做
    exp_id = EXP_ID[tid]
    if r is not None:
        mF, mL = r
    else:
        mF, mL = load_metrics_pair(tag)
    if not ledger_has(exp_id):
        ledger_append(exp_id, tag, w, mF, mL)
        LOG("ledger appended:", exp_id)
    else:
        LOG("ledger already has", exp_id)

LOG("r263_run.py 全部完成 (G0 实现层对拍 + M1.1/M1.2 + 台账 2 点 + dumps)")
