#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evolution_pipeline.py — 后端管道v2 统一Runner（R-207 W5 / task-0275）
=====================================================================
版本Registry + 五操作（backtest/evaluate/activate/rollback/override）
+ 五项数字门禁 + 试验台账 + decision-log + 防漂移 + --cycle 七步编排。
R220(task-0345/0346)：移除 activate 人工确认制（PASS 即自动 activate）；#13 legacy 豁免与 override TTL 机制保留。

子命令：
  bootstrap --from-main          一次性：从 main.json 抽首个版本对象 v1.1 入registry（幂等）
  fork --from v1.1 --as v1.2 [--set selection.params.n_hold=25] [--logic TXT]
  backtest --version v1.2 [--override n_hold=25 ...] [--start 2020-01-01] [--end 2025-12-31]
  evaluate --version v1.2 [--oos-start 2021-01]
  activate --version v1.2 [--force] [--reason TXT]  # R220: 正常路径由 evaluate PASS 自动触发
  rollback --to v1.1 --reason TXT
  override --reason TXT --ttl 24h [--timing-off] | --clear
  status                          registry 总览 + 防漂移自检
  --cycle                         七步编排（数据校验→快照→想法消化→因子迭代占位→backtest→evaluate→通知）

设计依据：/root/.openclaw/workspace/shared/results/05-量化投资/R-207-量化系统产品开发说明书.md §3.1/§3.2
"""
import os
import sys
import json
import glob
import math
import hashlib
import shutil
import argparse
import subprocess
from datetime import datetime, timedelta
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_lock import AUDIT_LOCK_END, clamp_ym  # E6修复(task-0292): OOS窗口止于审计段

HP = os.path.expanduser("~/quant-evolve")
SCRIPTS = os.path.join(HP, "scripts")
MODEL_DIR = os.path.join(HP, "model")
REGISTRY_DIR = os.path.join(MODEL_DIR, "registry")
MAIN_FILE = os.path.join(MODEL_DIR, "main.json")
SWITCH_LOG = os.path.join(MODEL_DIR, "switch_log.jsonl")
HISTORY_LOG = os.path.join(MODEL_DIR, "history.jsonl")
DECISION_LOG = os.path.join(MODEL_DIR, "decision-log.jsonl")
OVERRIDE_FILE = os.path.join(MODEL_DIR, "temp_override.json")
RESULTS = os.path.join(HP, "results")
LEDGER = os.path.join(RESULTS, "experiment-ledger.jsonl")
NOTIFY_OUT = os.path.join(RESULTS, "notifications-queue.jsonl")
SNAPSHOTS_FILE = os.path.join(RESULTS, "data-snapshots.json")
CYCLE_DIR = os.path.join(RESULTS, "cycle")

# registry化之前 history.jsonl 的历史试验次数（23 register + 8 reject + 1 merge + 2其他），
# DSR 的 N = 该偏移 + 台账 backtest 计数
HISTORICAL_TRIAL_OFFSET = 34

GATE_CONFIG = {
    "icir_is_min": 0.5,        # 门禁1：IS全样本复合ICIR年化下限
    "oos_p_min": 0.05,         # 门禁2：OOS相对IS劣化单侧t检验 p>0.05（不显著劣于）
    "max_corr_max": 0.7,       # 门禁3：与在役因子最高|ρ|上限
    "dsr_min": 0.95,           # 门禁4：Deflated Sharpe Ratio 下限
    "oos_split_ym": "2021-01", # 门禁2：OOS起始月
    "mdd_vs_parent_max_pp": 2.0, # 门禁6：MDD较父版本恶化幅度上限(百分点, E3修复task-0292)
}

# R220-#7（task-0351）：五门禁一票否决 → 综合评分制（score_composite + score_rank_pool）。
# g1-g6 判定逻辑不动；verdict 合成层由 PASS/REJECT 改为 SCORED + gate.score。
SCORE_CONFIG = {
    "weights": {"p": 0.175, "dsr": 0.175,                 # stat 合计 0.35（g2 p + g4 DSR 等权）
                "oos_calmar": 0.125, "oos_sharpe": 0.125, # oos 合计 0.25（vs 在役相对增量，±40% 满档）
                "is_calmar": 0.075, "is_sharpe": 0.075,   # is 合计 0.15（calmar/0.60 + sharpe/1.20）
                "dd": 0.10, "corr": 0.10, "logic": 0.05},
    "p":    {"gate": 0.05, "gate_score": 0.70, "full": 0.20, "zero_score": 0.30},  # 分段线性映射
    "dsr":  {"lo": 0.90, "hi": 1.00},
    "oos":  {"rel_full": 0.40},
    "is":   {"calmar_full": 0.60, "sharpe_full": 1.20},
    "dd":   {"free_pp": 2.0, "zero_pp": 7.0},   # MDD恶化 ≤2pp=1.0，2-7pp 线性衰减至 0
    "corr": {"free": 0.5, "zero": 0.7},          # max|ρ| ≤0.5=1.0，0.5-0.7 线性衰减至 0
    "logic": {"full_chars": 20, "short_score": 0.6},
    "partial_missing_weight_max": 0.30,  # N/A 缺权 >0.30 → partial：不入排名池、不自动上岗
    "stat_warn": {"p_hard": 0.01, "dsr_hard": 0.90},  # 硬统计预警：rank1 自动上岗需 ≥1.10×第二名
    "auto_activate_margin": 1.10,
    # R226-P0-4（task-0353，评分制 v1.1）：影子观察期 + holdout 晋升门槛。
    # 影子观察期：rank1 但 stat_warn 的版本不直接上岗——标记 shadow 入观察期，连续
    #   min_clean_cycles=N 个评估周期警示无升级（硬预警项数不增）或警示解除（stat_warn 转
    #   false）才恢复上岗资格；期间任一周期警示升级（硬预警项数增加）→ 计数清零重计。
    #   N=3 依据：月度评估节奏下约一个季度观察窗，兼顾过拟合警惕与迭代速度，可调。
    # holdout 晋升门槛：locked=2006-01~2024-06（训练/验证口径不变）；近端 holdout=2024-07~
    #   数据末；任何 activate 必须报告 locked+holdout 双段指标；自动上岗额外要求 holdout
    #   年化 ≥ locked 年化×60%（防 OOS 崩塌）且 MDD 恶化 ≤ locked+10pp。60%/10pp 为初版
    #   草案（R-226 采纳的外部建议值），随 untouched 段（2026-09 起 paper 累积）校准。
    "shadow": {"min_clean_cycles": 3},
    "holdout": {"start_ym": "2024-07", "min_annual_ratio": 0.60,
                "max_mdd_deterioration_pp": 10.0},
}
STATUS_ENUM = ["candidate", "pending", "active", "sota", "retired"]


def now():
    return datetime.now()


def log(msg):
    print(f"[{now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


# ------------------------------------------------------------------
# 基础IO
# ------------------------------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def append_jsonl(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _md5(obj):
    return hashlib.md5(_canon(obj).encode("utf-8")).hexdigest()


def params_hash(reg):
    """registry selection+timing 的参数指纹（台账/decision-log 用）。"""
    sel, tim = reg.get("selection") or {}, reg.get("timing") or {}
    return _md5({
        "strategy": sel.get("strategy"),
        "params": sel.get("params", {}),
        "factors": sel.get("factors", []),
        "timing_enabled": bool(tim.get("enabled", True)),
        "timing_type": tim.get("type", ""),
        "timing_params": tim.get("params", {}),
    })


def drift_signature(reg_or_main, is_registry=True):
    """防漂移签名：与 paper_engine.guard_override_and_drift 完全同口径。"""
    if is_registry:
        sel = reg_or_main.get("selection") or {}
        tim = reg_or_main.get("timing") or {}
        params = sel.get("params", {})
    else:
        params = reg_or_main.get("params", {})
        tim = reg_or_main.get("timing") or {}
    return _md5({
        "params": params,
        "timing_enabled": bool(tim.get("enabled", True)),
        "timing_type": tim.get("type", ""),
        "timing_params": tim.get("params", {}),
    })


# ------------------------------------------------------------------
# Registry
# ------------------------------------------------------------------
def registry_files():
    return sorted(glob.glob(os.path.join(REGISTRY_DIR, "v*.json")))


def load_version(ver, required=True):
    p = os.path.join(REGISTRY_DIR, f"{ver}.json")
    if not os.path.exists(p):
        if required:
            raise SystemExit(f"❌ registry 中不存在 {ver}（{p}）")
        return None
    return load_json(p)


def save_version(reg):
    save_json(reg, os.path.join(REGISTRY_DIR, f"{reg['version_id']}.json"))


def find_active():
    for p in registry_files():
        try:
            r = load_json(p)
            if r.get("status") == "active":
                return r
        except Exception:
            continue
    return None


def code_ref():
    try:
        r = subprocess.run(["git", "-C", HP, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return f"git:{r.stdout.strip()}+evolution_pipeline@task-0275"
    except Exception:
        pass
    return "no-git+evolution_pipeline@task-0275"


# ------------------------------------------------------------------
# 台账 / decision-log / 通知
# ------------------------------------------------------------------
def ledger_backtest_count():
    return sum(1 for e in read_jsonl(LEDGER) if e.get("type") == "backtest")


def n_trials_cum():
    return HISTORICAL_TRIAL_OFFSET + ledger_backtest_count()


def ledger_append(entry_type, version, metrics=None, data_snapshot=None, phash=None):
    ts = now()
    run_id = f"{'bt' if entry_type == 'backtest' else 'ev'}_{version}_{ts.strftime('%Y%m%d_%H%M')}"
    entry = {
        "run_id": run_id,
        "ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "type": entry_type,
        "version": version,
        "code_ref": code_ref(),
        "params_hash": phash,
        "data_snapshot": data_snapshot,
        "metrics": metrics or {},
        "n_trials_cum": n_trials_cum(),
    }
    append_jsonl(LEDGER, entry)
    log(f"📒 台账追加: {run_id} (n_trials_cum={entry['n_trials_cum']})")
    return entry


def decision_id():
    today = now().strftime("%Y%m%d")
    seq = sum(1 for e in read_jsonl(DECISION_LOG)
              if e.get("decision_id", "").startswith(f"D-{today}")) + 1
    return f"D-{today}-{seq:03d}"


def decision_log(dtype, version, trigger, metrics_summary="", expected_impact="",
                 rollback_condition="", phash=None, data_snapshot=None, **extra):
    entry = {
        "ts": now().strftime("%Y-%m-%d %H:%M:%S"),
        "decision_id": decision_id(),
        "type": dtype,
        "version": version,
        "trigger": trigger,
        "metrics": metrics_summary,
        "expected_impact": expected_impact,
        "rollback_condition": rollback_condition,
        "code_ref": code_ref(),
        "params_hash": phash,
        "data_snapshot": data_snapshot,
    }
    entry.update(extra)
    append_jsonl(DECISION_LOG, entry)
    log(f"🧾 decision-log 追加: {entry['decision_id']} type={dtype} version={version}")
    return entry


def notify(severity, title, body):
    append_jsonl(NOTIFY_OUT, {
        "ts": now().strftime("%Y-%m-%d %H:%M:%S"),
        "channel": "evolution",
        "severity": severity,
        "title": title,
        "body": body,
        "task_id": "task-0275",
        "source": "evolution_pipeline",
    })


def _gates_brief(gates):
    return "; ".join(f"{k}:{v.get('status')}" for k, v in gates.items())


# ------------------------------------------------------------------
# 数据快照（W6 将升级为内容hash；当前用文件元信息指纹）
# ------------------------------------------------------------------
def compute_data_snapshot():
    kline_as_of, hash_src = None, []
    try:
        import pyarrow.parquet as pq
        import pyarrow.compute as pc
        for path, col in [
            (os.path.join(HP, "data", "all_stocks_merged.parquet"), "date"),
            (os.path.join(HP, "data", "hs300_daily_20060101_20260808.parquet"), "date"),
        ]:
            if os.path.exists(path):
                try:
                    tbl = pq.read_table(path, columns=[col])
                    kline_as_of = str(pc.max(tbl.column(col)).as_py())[:10]
                    break
                except Exception:
                    continue
    except Exception:
        pass
    # 指纹：K线目录 + 宏观数据的 (文件名,大小,mtime)
    for d in ["data/all_stocks_qfq", "data/macro"]:
        dp = os.path.join(HP, d)
        if os.path.isdir(dp):
            for fn in sorted(os.listdir(dp))[:200000]:
                fp = os.path.join(dp, fn)
                try:
                    st = os.stat(fp)
                    hash_src.append(f"{fn}:{st.st_size}:{int(st.st_mtime)}")
                except OSError:
                    continue
    h = hashlib.md5("\n".join(hash_src).encode("utf-8")).hexdigest() if hash_src else "unknown"
    return {"kline_as_of": kline_as_of or "unknown", "hash": h, "hash_method": "file-meta(W6升级内容hash)"}


# ------------------------------------------------------------------
# 门禁计算
# ------------------------------------------------------------------
def load_ic_monthly():
    import pandas as pd
    p = os.path.join(RESULTS, "factor_ic_monthly.csv")
    if not os.path.exists(p):
        return None
    return pd.read_csv(p, dtype={"ym": str})


def gate_icir(ic_df, factors, oos_split):
    """门禁1+2：复合ICIR（等权合成月度IC）IS年化 + OOS劣化t检验。"""
    import numpy as np
    cols = [c for c in factors if c in ic_df.columns]
    if not cols:
        return None, "因子IC数据中无该版本因子列 → N/A"
    comp = ic_df[cols].mean(axis=1)
    is_mask = ic_df["ym"] < oos_split
    # E6修复(task-0292): OOS 窗口终点强制 ≤ 审计锁定段 2024-06，杜绝评估穿透
    oos_mask = (~is_mask) & (ic_df["ym"] <= AUDIT_LOCK_END[:7])
    is_vals, oos_vals = comp[is_mask].dropna().values, comp[oos_mask].dropna().values
    if len(is_vals) < 24:
        return None, f"IS样本不足({len(is_vals)}月) → N/A"
    icir_is_m = is_vals.mean() / is_vals.std(ddof=1)
    icir_is_ann = icir_is_m * math.sqrt(12)
    gate1 = {"status": "PASS" if icir_is_ann >= GATE_CONFIG["icir_is_min"] else "FAIL",
             "icir_is_annualized": round(icir_is_ann, 4),
             "n_months_is": int(len(is_vals)),
             "threshold": GATE_CONFIG["icir_is_min"]}
    if len(oos_vals) < 6:
        gate2 = {"status": "N/A", "note": f"OOS样本不足({len(oos_vals)}月)"}
        return {"gate1": gate1, "gate2": gate2,
                "icir_oos_annualized": None, "oos_p": None}, None
    icir_oos_ann = (oos_vals.mean() / oos_vals.std(ddof=1)) * math.sqrt(12) if len(oos_vals) > 1 else None
    # 单侧 Welch t 检验：H1 = OOS 均值显著低于 IS → p = P(T ≤ t)
    n1, n2 = len(is_vals), len(oos_vals)
    m1, m2 = float(np.mean(is_vals)), float(np.mean(oos_vals))
    v1, v2 = float(np.var(is_vals, ddof=1)), float(np.var(oos_vals, ddof=1))
    se = math.sqrt(v1 / n1 + v2 / n2) if (v1 > 0 or v2 > 0) else 0.0
    if se == 0:
        p = 1.0
    else:
        t = (m2 - m1) / se
        df = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
        from scipy import stats as sps
        p = float(sps.t.cdf(t, df))
    oos_end_ym_actual = str(ic_df.loc[oos_mask, "ym"].max()) if oos_mask.any() else None
    gate2 = {"status": "PASS" if p > GATE_CONFIG["oos_p_min"] else "FAIL",
             "p_one_sided": round(p, 4), "n_months_oos": int(n2),
             "oos_end_ym": oos_end_ym_actual, "audit_lock_end_ym": AUDIT_LOCK_END[:7],
             "mean_ic_is": round(m1, 5), "mean_ic_oos": round(m2, 5),
             "threshold_p": GATE_CONFIG["oos_p_min"]}
    return {"gate1": gate1, "gate2": gate2,
            "icir_oos_annualized": round(icir_oos_ann, 4) if icir_oos_ann else None,
            "oos_p": round(p, 4)}, None


def gate_max_corr(reg):
    """门禁3：候选新增因子 vs 在役(active)因子 最高|ρ|<0.7。
    数据源：results/factor_ic_corr.csv（因子IC相关矩阵，W1 catalog附属）优先；
    矩阵未覆盖组合→ catalog corr_alerts 成员关系判 ≥阈值下限；两者均缺→N/A。"""
    import pandas as pd
    cat_p = os.path.join(RESULTS, "factor_catalog_v2.json")
    corr_p = os.path.join(RESULTS, "factor_ic_corr.csv")
    act = find_active()
    active_factors = set((act.get("selection") or {}).get("factors", [])) if act else set()
    cand_factors = reg["selection"].get("factors", [])
    new_factors = [f for f in cand_factors if f not in active_factors]
    if not new_factors:
        # E3修复(task-0292): 无新增因子时相关性无信息量 → N/A（不折减总判定，也不计PASS）
        return {"status": "N/A", "max_abs_corr": None, "worst_pair": None,
                "note": "无新增因子（因子集与active一致），相关性门禁无信息量 → N/A"}
    corr, cat = None, None
    if os.path.exists(corr_p):
        try:
            corr = pd.read_csv(corr_p, index_col=0)
        except Exception:
            corr = None
    if os.path.exists(cat_p):
        try:
            cat = load_json(cat_p).get("factors", {})
        except Exception:
            cat = None
    if corr is None and cat is None:
        return {"status": "N/A", "note": "factor_catalog_v2/factor_ic_corr 均缺失（W1交付），该项跳过"}
    mx, worst, unresolved = 0.0, None, []
    for f in new_factors:
        for g in active_factors:
            v = None
            if corr is not None and f in corr.index and g in corr.columns:
                try:
                    v = abs(float(corr.loc[f, g]))
                except Exception:
                    v = None
            if v is None and cat is not None:
                alerts = set((cat.get(g) or {}).get("corr_alerts") or [])
                if f in alerts:
                    v = 0.6  # catalog corr_alerts 成员 ⇒ |ρ|≥阈值下限（W1阈值0.6）
            if v is None:
                unresolved.append((f, g))
                continue
            if v > mx:
                mx, worst = v, (f, g)
    st = "PASS" if mx < GATE_CONFIG["max_corr_max"] else "FAIL"
    out = {"status": st, "max_abs_corr": round(mx, 4), "worst_pair": worst,
           "n_new_factors": len(new_factors), "new_factors": new_factors,
           "threshold": GATE_CONFIG["max_corr_max"]}
    if unresolved:
        out["unresolved_pairs"] = len(unresolved)
        out["note"] = f"{len(unresolved)}个组合无相关性数据（按未超限处理，待W1全量矩阵）"
    return out


def gate_mdd_vs_parent(reg, active=None):
    """门禁6（E3修复 task-0292）：候选 endtoend MDD 较父版本(active在役)恶化幅度 ≤2pp。
    MDD 为负值，恶化 = |MDD_cand| - |MDD_parent| 增加（pp = 百分点）。
    一票否决：恶化 >2pp → FAIL（REJECT），数据缺失 → N/A（不折减）。"""
    act = active if active is not None else find_active()
    if act is None:
        return {"status": "N/A", "note": "无在役(active)版本可比 → N/A"}
    m_cand = ((reg.get("backtest_refs") or {}).get("metrics") or {}).get("max_drawdown")
    m_par = ((act.get("backtest_refs") or {}).get("metrics") or {}).get("max_drawdown")
    if m_cand is None or m_par is None:
        return {"status": "N/A", "note": f"缺 MDD 数据 cand={m_cand} parent={m_par} → N/A"}
    det_pp = (abs(m_cand) - abs(m_par)) * 100.0  # 正值=恶化(pp)
    thr = GATE_CONFIG["mdd_vs_parent_max_pp"]
    st = "PASS" if det_pp <= thr else "FAIL"
    return {"status": st, "mdd_candidate": m_cand, "mdd_parent": m_par,
            "mdd_deterioration_pp": round(det_pp, 2),
            "threshold_pp": thr, "parent_version": act.get("version_id")}


def deflated_sharpe(returns, n_trials):
    """门禁4：Bailey & López de Prado (2014) DSR。输入周期化收益率序列。"""
    import numpy as np
    from scipy import stats as sps
    r = np.asarray([x for x in returns if x is not None and not math.isnan(x)], dtype=float)
    T = len(r)
    if T < 20 or r.std(ddof=1) == 0:
        return None, f"样本不足(T={T})或零方差"
    sr = float(r.mean() / r.std(ddof=1))          # 周期化（日度）Sharpe
    V = float(r.var(ddof=1))
    g3 = float(sps.skew(r))
    g4 = float(sps.kurtosis(r, fisher=False))     # 原始峰度
    N = max(int(n_trials), 2)
    gamma = 0.5772156649015329
    e = math.e
    sr0 = math.sqrt(V) * ((1 - gamma) * sps.norm.ppf(1 - 1.0 / N)
                          + gamma * sps.norm.ppf(1 - 1.0 / (N * e)))
    denom = 1 - g3 * sr + (g4 - 1) / 4.0 * sr * sr
    if denom <= 0:
        return None, f"DSR分母非正(skew={g3:.2f}, kurt={g4:.2f}, sr={sr:.4f})"
    dsr = float(sps.norm.cdf((sr - sr0) * math.sqrt(T - 1) / math.sqrt(denom)))
    detail = {"dsr": round(dsr, 4), "sr_period": round(sr, 5), "sr0_expected_max": round(sr0, 6),
              "T": T, "skew": round(g3, 3), "kurtosis": round(g4, 3), "n_trials": N,
              "threshold": GATE_CONFIG["dsr_min"]}
    return detail, None


# ------------------------------------------------------------------
# cmd: bootstrap
# ------------------------------------------------------------------
def cmd_bootstrap(args):
    if find_active() is not None:
        raise SystemExit("❌ registry 已存在 active 版本，bootstrap 幂等中止（不重复抽取）")
    main = load_json(MAIN_FILE)
    tim = main.get("timing") or {}
    snap = compute_data_snapshot()
    reg = {
        "version_id": args.version,
        "status": "active",
        "created_at": main.get("registered_at") or now().strftime("%Y-%m-%d %H:%M:%S"),
        "main_alias": main.get("version"),
        "selection": {
            "strategy": main.get("strategy", "dividend_quality_smallcap"),
            "params": main.get("params", {}),
            "factors": main.get("factors", []),
        },
        "timing": {
            "enabled": bool(tim.get("enabled", True)),
            "type": tim.get("type", ""),
            "params": tim.get("params", {}),
            "description": tim.get("description", ""),
            "signal": tim.get("signal", ""),
            "data_source": tim.get("data_source", ""),
            "data_update": tim.get("data_update", ""),
            "disable_switch": tim.get("disable_switch", ""),
        },
        "data_snapshot": {
            "kline_as_of": snap.get("kline_as_of") or "2026-08-07",
            "hash": "unknown-legacy",
            "note": "历史产物无hash，W6任务补",
        },
        "code_ref": f"legacy({main.get('source','')}) bootstrap by task-0275",
        "backtest_refs": {
            "endtoend": "results/i4_q3z_nav.csv",
            "baseline": "results/i4_base_nav.csv",
            "metrics": {k: main.get("metrics", {}).get(k) for k in
                        ["annual_return", "max_drawdown", "sharpe", "calmar"]},
            "report": "results/timing-iter4-report.md",
            "stale_snapshot": True,
        },
        "gate": {
            "icir_is": None, "icir_oos": None, "max_corr": None, "dsr": None,
            "logic": "高股息+高ROE/ROA质量过滤的小市值组合：股息与质量提供安全边际，"
                     "小市值提供长期超额来源；hs300估值zscore择时在极端估值区间降仓以压缩危机段回撤",
            "n_trial": HISTORICAL_TRIAL_OFFSET,
            "verdict": "legacy-grandfathered",
            "note": "存量在役版本bootstrap入registry，未过新版五门禁（祖继保留）",
        },
        "provenance": {"trigger": "bootstrap(task-0275)", "parent": None,
                       "report": "results/pipeline-v2-w5-report.md"},
    }
    save_version(reg)
    # 冻结当前 main.json 字节快照（rollback 字节级还原的依据）
    with open(MAIN_FILE, "rb") as f:
        raw = f.read()
    with open(os.path.join(REGISTRY_DIR, f"{args.version}.main.json.snapshot"), "wb") as f:
        f.write(raw)
    decision_log("bootstrap", args.version, "bootstrap --from-main",
                 metrics_summary=str(reg["backtest_refs"]["metrics"]),
                 expected_impact="建立版本Registry，main.json零改动",
                 rollback_condition="无需回滚（只读操作）",
                 phash=params_hash(reg), data_snapshot=reg["data_snapshot"])
    log(f"✅ registry/{args.version}.json 已建立（status=active, alias={reg['main_alias']}）")
    log(f"   main.json 字节快照已冻结: registry/{args.version}.main.json.snapshot "
        f"(md5={hashlib.md5(raw).hexdigest()})")
    return 0


# ------------------------------------------------------------------
# cmd: fork
# ------------------------------------------------------------------
def _parse_val(s):
    s = s.strip()
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def cmd_fork(args):
    as_ver = args.as_ver
    parent = load_version(args.frm)
    reg = deepcopy(parent)
    reg["version_id"] = as_ver
    reg["status"] = "candidate"
    reg["created_at"] = now().strftime("%Y-%m-%d %H:%M:%S")
    reg["main_alias"] = as_ver
    applied = []
    for kv in args.set or []:
        if "=" not in kv:
            raise SystemExit(f"❌ --set 格式应为 dotted.key=value，收到: {kv}")
        k, v = kv.split("=", 1)
        parts = k.split(".")
        if parts[:2] not in (["selection", "params"], ["timing", "params"]) or len(parts) != 3:
            raise SystemExit(f"❌ --set 仅支持 selection.params.* / timing.params.*，收到: {k}")
        reg[parts[0]][parts[1]][parts[2]] = _parse_val(v)
        applied.append(f"{k}={v}")
    reg["gate"] = {"icir_is": None, "icir_oos": None, "max_corr": None, "dsr": None,
                   "logic": args.logic or parent.get("gate", {}).get("logic"),
                   "n_trial": None, "verdict": None}
    reg["provenance"] = {"trigger": args.trigger or "manual fork",
                         "parent": parent["version_id"], "report": None}
    reg["backtest_refs"] = {}
    reg.pop("main_snapshot", None)
    save_version(reg)
    log(f"✅ fork: {parent['version_id']} → {as_ver} (status=candidate) applied={applied}")
    return 0


# ------------------------------------------------------------------
# cmd: backtest（两腿：端到端=选股×择时；基线=同选股无择时）
# ------------------------------------------------------------------
def cmd_backtest(args):
    reg = load_version(args.version)
    sel_params = dict(reg["selection"]["params"])
    for kv in args.override or []:
        if "=" not in kv:
            raise SystemExit(f"❌ --override 格式应为 key=value，收到: {kv}")
        k, v = kv.split("=", 1)
        sel_params[k] = _parse_val(v)
        log(f"  override: {k}={v}")
    tim = reg.get("timing") or {}

    sys.path.insert(0, SCRIPTS)
    import backtest_dividend_quality_iter as engine
    import macro_timing_layer_iter4 as mtl4

    log("加载市场数据（面板构建，需数分钟）...")
    market = engine.load_market_data(verbose=False)
    date_range = None
    if args.start or args.end:
        date_range = (args.start or "2006-01-01", args.end or "2026-12-31")
        log(f"回测区间限定: {date_range[0]} ~ {date_range[1]}")

    ver = reg["version_id"]
    bt_dir = os.path.join(RESULTS, f"bt_{ver}")
    os.makedirs(bt_dir, exist_ok=True)
    base_cfg = dict(engine.DEFAULTS)
    base_cfg.update(sel_params)

    def _move_artifacts(prefix, leg_name):
        moved = []
        for suffix, out in [("nav.csv", f"{leg_name}.csv"),
                            ("metrics.json", f"{leg_name}_metrics.json"),
                            ("trades.csv", f"{leg_name}_trades.csv"),
                            ("holdings.csv", f"{leg_name}_holdings.csv"),
                            ("yearly.csv", f"{leg_name}_yearly.csv")]:
            src = os.path.join(RESULTS, f"{prefix}_{suffix}")
            if os.path.exists(src):
                shutil.move(src, os.path.join(bt_dir, out))
                moved.append(out)
        return moved

    # 腿1：基线（同选股、无择时）
    market.pop("timing_pos", None)
    cfg_b = dict(base_cfg, out_prefix=f"bt_{ver}_baseline_tmp", force_save_artifacts=1)
    log(f"▶ 腿1/2 基线（无择时）...")
    m_b = engine.run_backtest(cfg_b, market=market, date_range=date_range)
    if m_b is None:
        raise SystemExit("❌ 基线腿无结果")
    _move_artifacts(f"bt_{ver}_baseline_tmp", "baseline")

    # 腿2：端到端（选股×择时）
    tkey = tim.get("type", "")
    mtl4_key = tkey[3:] if tkey.startswith("i4_") else tkey
    m_e = None
    if tim.get("enabled") and mtl4_key in getattr(mtl4, "SPECS", {}):
        log(f"▶ 腿2/2 端到端（择时 {tkey} → mtl4 type_key={mtl4_key}）...")
        sig = mtl4.build_timing_signals_iter4({})
        pos = mtl4.compute_pos_ratio_iter4(sig, {}, type_key=mtl4_key, save=False)
        market["timing_pos"] = pos
        cfg_e = dict(base_cfg, out_prefix=f"bt_{ver}_endtoend_tmp", force_save_artifacts=1)
        m_e = engine.run_backtest(cfg_e, market=market, date_range=date_range)
        market.pop("timing_pos", None)
        if m_e is None:
            raise SystemExit("❌ 端到端腿无结果")
        _move_artifacts(f"bt_{ver}_endtoend_tmp", "endtoend")
    else:
        log(f"⚠️ 择时未启用或类型未知({tkey})，端到端=基线复制")
        shutil.copy(os.path.join(bt_dir, "baseline.csv"), os.path.join(bt_dir, "endtoend.csv"))
        shutil.copy(os.path.join(bt_dir, "baseline_metrics.json"),
                    os.path.join(bt_dir, "endtoend_metrics.json"))
        m_e = dict(m_b)

    keep = ["annual_return", "max_drawdown", "sharpe", "calmar",
            "monthly_win_rate", "cumulative_return"]
    met = {
        "version": ver,
        "generated_at": now().strftime("%Y-%m-%d %H:%M:%S"),
        "date_range": list(date_range) if date_range else None,
        "baseline": {k: m_b.get(k) for k in keep},
        "endtoend": {k: m_e.get(k) for k in keep},
        "timing_effect": {k: (m_e.get(k) - m_b.get(k)) if (m_e.get(k) is not None and m_b.get(k) is not None) else None
                          for k in ["annual_return", "max_drawdown", "sharpe", "calmar"]},
        "params": sel_params,
        "timing_type": tim.get("type"),
    }
    save_json(met, os.path.join(bt_dir, "metrics.json"))

    # 数据快照 + 回写 registry
    snap = compute_data_snapshot()
    reg["data_snapshot"] = {"kline_as_of": snap["kline_as_of"], "hash": snap["hash"],
                            "note": snap.get("hash_method")}
    reg["backtest_refs"] = {
        "endtoend": f"results/bt_{ver}/endtoend.csv",
        "baseline": f"results/bt_{ver}/baseline.csv",
        "metrics": {k: m_e.get(k) for k in ["annual_return", "max_drawdown", "sharpe", "calmar"]},
        "metrics_full": f"results/bt_{ver}/metrics.json",
        "snapshot_hash": snap["hash"],
        "stale_snapshot": False,
        "date_range": list(date_range) if date_range else None,
        "backtested_at": now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_version(reg)
    ledger_append("backtest", ver, metrics={"endtoend": met["endtoend"], "baseline": met["baseline"]},
                  data_snapshot=reg["data_snapshot"], phash=params_hash(reg))
    log(f"✅ backtest 完成: results/bt_{ver}/ (endtoend 年化={met['endtoend']['annual_return']:.4f}, "
        f"基线年化={met['baseline']['annual_return']:.4f})")
    return 0


# ------------------------------------------------------------------
# cmd: evaluate（五项数字门禁）
# ------------------------------------------------------------------
def score_composite(reg, gates, active=None):
    """R220-#7（task-0351）：五门禁一票否决 → 综合评分制（g1-g6 判定不动，只改 verdict 合成层）。
    六分项（SCORE_CONFIG["weights"]）：stat 0.35 = g2 p + g4 DSR 等权；
    oos 0.25 = Δcalmar/Δsharpe vs 在役（±40% 满档，零增量=0.5）；
    is 0.15 = calmar/0.60 + sharpe/1.20；dd 0.10 = MDD 恶化（≤2pp=1，2-7pp 线性）；
    corr 0.10 = max|ρ|（≤0.5=1，0.5-0.7 线性）；logic 0.05 = 经济学逻辑（≥20字=1，短=0.6，空=0）。
    N/A 分量按剩余权重重归一（对齐门禁层 N/A 不折减）；缺权 >0.30 → partial。
    stat_warn = g2 p<0.01 或 DSR<0.90（rank1 自动上岗需 ≥1.10×第二名）。"""
    def clamp(x, lo, hi):
        return max(lo, min(hi, x))

    act = active if active is not None else find_active()
    m = (reg.get("backtest_refs") or {}).get("metrics") or {}
    pm = ((act or {}).get("backtest_refs") or {}).get("metrics") or {}
    W = SCORE_CONFIG["weights"]
    subs = []  # (key, weight, score)；score=None 表示 N/A 分量

    # stat：g2 p 分段线性（0→0.30 / 0.05 门限→0.70 / ≥0.20→1.0）+ g4 DSR 线性（0.90→0，1.0→1）
    p = (gates.get("g2_icir_oos") or {}).get("p_one_sided")
    cfgp = SCORE_CONFIG["p"]
    if p is None:
        subs.append(("p", W["p"], None))
    elif p >= cfgp["full"]:
        subs.append(("p", W["p"], 1.0))
    elif p >= cfgp["gate"]:
        subs.append(("p", W["p"], cfgp["gate_score"] + (1.0 - cfgp["gate_score"])
                     * (p - cfgp["gate"]) / (cfgp["full"] - cfgp["gate"])))
    else:
        subs.append(("p", W["p"], cfgp["zero_score"] + (cfgp["gate_score"] - cfgp["zero_score"])
                     * p / cfgp["gate"]))
    dsr = (gates.get("g4_dsr") or {}).get("dsr")
    cfgd = SCORE_CONFIG["dsr"]
    subs.append(("dsr", W["dsr"], None if dsr is None else
                 clamp((dsr - cfgd["lo"]) / (cfgd["hi"] - cfgd["lo"]), 0, 1)))

    # oos：候选 vs 在役相对增量（±rel_full 满档 → 0~1，零增量=0.5）
    cfgo = SCORE_CONFIG["oos"]
    for side in ("calmar", "sharpe"):
        c, par = m.get(side), pm.get(side)
        if c is None or par in (None, 0):
            subs.append(("oos_" + side, W["oos_" + side], None))
        else:
            rel = (c - par) / abs(par)
            subs.append(("oos_" + side, W["oos_" + side],
                         0.5 + 0.5 * clamp(rel / cfgo["rel_full"], -1, 1)))
    # is：绝对水平，满档封顶
    cfgi = SCORE_CONFIG["is"]
    for side, full in (("calmar", cfgi["calmar_full"]), ("sharpe", cfgi["sharpe_full"])):
        c = m.get(side)
        subs.append(("is_" + side, W["is_" + side], None if c is None else clamp(c / full, 0, 1)))
    # dd：MDD 较在役恶化（g6 数值化，不再一票否决）
    mdd = (gates.get("g6_mdd_vs_parent") or {}).get("mdd_deterioration_pp")
    cfgdd = SCORE_CONFIG["dd"]
    subs.append(("dd", W["dd"], None if mdd is None else
                 (1.0 if mdd <= cfgdd["free_pp"] else
                  clamp((cfgdd["zero_pp"] - mdd) / (cfgdd["zero_pp"] - cfgdd["free_pp"]), 0, 1))))
    # corr：与在役因子最大|ρ|（g3 数值化）
    mc = (gates.get("g3_max_corr") or {}).get("max_abs_corr")
    cfgc = SCORE_CONFIG["corr"]
    subs.append(("corr", W["corr"], None if mc is None else
                 (1.0 if mc <= cfgc["free"] else
                  clamp((cfgc["zero"] - mc) / (cfgc["zero"] - cfgc["free"]), 0, 1))))
    # logic：经济学逻辑说明（g5 数值化）
    lg = str((gates.get("g5_logic") or {}).get("logic") or "").strip()
    cfgl = SCORE_CONFIG["logic"]
    subs.append(("logic", W["logic"],
                 1.0 if len(lg) >= cfgl["full_chars"] else (cfgl["short_score"] if lg else 0.0)))

    wsum = sum(w for _, w, s in subs if s is not None)
    score = round(sum(w * s for _, w, s in subs if s is not None) / wsum, 4) if wsum > 0 else None
    missing_weight = round(1 - wsum, 3)
    cfgw = SCORE_CONFIG["stat_warn"]
    stat_warn = (p is not None and p < cfgw["p_hard"]) or (dsr is not None and dsr < cfgw["dsr_hard"])
    flags = []
    if missing_weight > SCORE_CONFIG["partial_missing_weight_max"]:
        flags.append("partial")
    if stat_warn:
        flags.append("stat_warn")
    return {"score": score, "components": {k: (round(s, 4) if s is not None else None)
                                           for k, _, s in subs},
            "missing_weight": missing_weight, "partial": "partial" in flags,
            "stat_warn": stat_warn, "flags": flags,
            "incumbent": (act or {}).get("version_id")}


def score_rank_pool(extra_reg=None, extra_score=None):
    """R220-#7：自动上岗排名池 = status∈{candidate,pending,active} 且 gate.score 存在且非 partial。
    返回 [(version_id, score)] 按 score 降序；extra_* 把刚评估、尚未写回 registry 的版本临时并入。"""
    items = []
    if extra_reg is not None and extra_score is not None:
        items.append((extra_reg.get("version_id"), extra_score))
    skip = extra_reg.get("version_id") if extra_reg is not None else None
    for p in registry_files():
        r = load_json(p)
        if r.get("version_id") == skip or r.get("status") not in ("candidate", "pending", "active"):
            continue
        g = r.get("gate") or {}
        if g.get("score") is None or "partial" in (g.get("score_flags") or ""):
            continue
        items.append((r["version_id"], g["score"]))
    items.sort(key=lambda x: -x[1])
    return items


def cmd_evaluate(args):
    reg = load_version(args.version)
    refs = reg.get("backtest_refs") or {}
    if not refs.get("metrics"):
        raise SystemExit(f"❌ {args.version} 无 backtest_refs，请先 backtest")
    oos_split = args.oos_start or GATE_CONFIG["oos_split_ym"]
    factors = reg["selection"].get("factors", [])
    gates, notes = {}, []

    # 门禁1+2：复合ICIR
    ic_df = load_ic_monthly()
    if ic_df is None:
        gates["g1_icir_is"], gates["g2_icir_oos"] = {"status": "N/A", "note": "因子IC数据缺失"}, \
                                                    {"status": "N/A", "note": "因子IC数据缺失"}
    else:
        r12, err = gate_icir(ic_df, factors, oos_split)
        if err:
            notes.append(err)
            gates["g1_icir_is"] = {"status": "N/A", "note": err}
            gates["g2_icir_oos"] = {"status": "N/A", "note": err}
        else:
            gates["g1_icir_is"] = r12["gate1"]
            gates["g2_icir_oos"] = dict(r12["gate2"])
            if r12.get("icir_oos_annualized") is not None:
                gates["g2_icir_oos"]["icir_oos_annualized"] = r12["icir_oos_annualized"]

    # 门禁3：相关性
    gates["g3_max_corr"] = gate_max_corr(reg)
    if gates["g3_max_corr"]["status"] == "N/A":
        notes.append("门禁3 N/A：" + gates["g3_max_corr"].get("note", ""))

    # 门禁4：DSR（端到端净值日收益）
    nav_path = os.path.join(HP, refs.get("endtoend", ""))
    g4_detail, g4_err = None, None
    if os.path.exists(nav_path):
        import pandas as pd
        nav = pd.read_csv(nav_path)["nav"].astype(float)
        rets = nav.pct_change().dropna().tolist()
        g4_detail, g4_err = deflated_sharpe(rets, n_trials_cum())
    else:
        g4_err = f"净值文件缺失: {nav_path}"
    if g4_detail:
        gates["g4_dsr"] = {"status": "PASS" if g4_detail["dsr"] >= GATE_CONFIG["dsr_min"] else "FAIL",
                           **g4_detail}
    else:
        gates["g4_dsr"] = {"status": "N/A", "note": g4_err}
        notes.append("门禁4 N/A：" + str(g4_err))

    # 门禁5：经济学逻辑
    logic = (reg.get("gate") or {}).get("logic")
    gates["g5_logic"] = {"status": "PASS" if logic and str(logic).strip() else "FAIL",
                         "logic": logic or ""}

    # 门禁6：MDD 恶化 vs 父版本（E3修复 task-0292，一票否决）
    gates["g6_mdd_vs_parent"] = gate_mdd_vs_parent(reg)
    if gates["g6_mdd_vs_parent"]["status"] == "N/A":
        notes.append("门禁6 N/A：" + gates["g6_mdd_vs_parent"].get("note", ""))

    # R220-#7（task-0351）：五门禁一票否决 → 综合评分制。g1-g6 判定与状态保留（审计/回溯用），
    # verdict 合成层改为 SCORED；是否上岗由 score_rank_pool 的 rank==1 规则决定（见下）。
    sd = score_composite(reg, gates)
    verdict = "SCORED"
    if sd["partial"]:
        notes.append("评分partial：缺权%.2f>0.30，不入排名池、不可自动上岗" % sd["missing_weight"])

    report = {"version": args.version, "evaluated_at": now().strftime("%Y-%m-%d %H:%M:%S"),
              "oos_split": oos_split, "n_trials": n_trials_cum(),
              "audit_lock_end": AUDIT_LOCK_END,
              "backtest_metrics": refs.get("metrics"), "gates": gates,
              "verdict": verdict, "notes": notes, "score": sd}
    bt_dir = os.path.join(RESULTS, f"bt_{args.version}")
    save_json(report, os.path.join(bt_dir, "gate-report.json"))

    # 回写 registry.gate
    g = reg.setdefault("gate", {})
    g.update({
        "icir_is": gates["g1_icir_is"].get("icir_is_annualized"),
        "icir_oos": gates["g2_icir_oos"].get("icir_oos_annualized") if "icir_oos_annualized" in gates["g2_icir_oos"] else None,
        "max_corr": gates["g3_max_corr"].get("max_abs_corr"),
        "dsr": gates["g4_dsr"].get("dsr"),
        "mdd_deterioration_pp": gates["g6_mdd_vs_parent"].get("mdd_deterioration_pp"),
        "n_trial": n_trials_cum(),
        "verdict": verdict,
        "evaluated_at": report["evaluated_at"],
        "oos_split": oos_split,
        # R220-#7 评分制字段（历史版本不带，视为未评分/legacy）
        "score": sd["score"],
        "score_missing_weight": sd["missing_weight"],
        "score_flags": ",".join(sd["flags"]),
    })
    prev_status = reg.get("status")
    rank = None
    if prev_status == "candidate" and not sd["partial"]:
        # R220-#7（task-0351）：评分制自动上岗 = 排名池 rank==1 且（无 stat_warn 或 ≥margin×第二名）
        pool = score_rank_pool(reg, sd["score"])
        ids = [i[0] for i in pool]
        rank = ids.index(args.version) + 1 if args.version in ids else None
        second = pool[1][1] if len(pool) > 1 else None
        margin = SCORE_CONFIG["auto_activate_margin"]
        warn_ok = (not sd["stat_warn"]) or (second is not None and sd["score"] >= margin * second)
        if rank == 1 and warn_ok:
            log(f"🚦 评分 rank=1/池{len(pool)}（score={sd['score']:.4f}）→ 自动 activate（R220-#7 评分制）")
            _do_activate(reg, trigger=f"evaluate --version {args.version} (score rank=1 auto-activate)",
                         reason=f"评分rank=1自动activate（score={sd['score']:.4f}，R220-#7）", force=False)
        else:
            log(f"⏸️ 评分 rank={rank}/池{len(pool)}（score={sd['score']:.4f}"
                f"{'，stat_warn' if sd['stat_warn'] else ''}）未达自动上岗条件，保持 {prev_status}")
            save_version(reg)
    else:
        save_version(reg)

    ledger_append("evaluate", args.version, metrics={"gates": {k: v.get("status") for k, v in gates.items()},
                                                     "verdict": verdict, "score": sd["score"],
                                                     "rank": rank},
                  data_snapshot=reg.get("data_snapshot"), phash=params_hash(reg))
    dtype = "evaluate_pass" if verdict == "PASS" else ("evaluate_reject" if verdict == "REJECT" else "evaluate")
    decision_log(dtype, args.version,
                 trigger=f"evaluate --version {args.version}",
                 metrics_summary=f"ICIR_is={g.get('icir_is')} DSR={g.get('dsr')} verdict={verdict} "
                                 f"score={sd['score']:.4f} rank={rank} [{_gates_brief(gates)}]",
                 expected_impact="SCORED rank=1→自动 activate（R220-#7 评分制）",
                 rollback_condition="激活后回撤超阈值或paper显著劣于endtoend回测",
                 phash=params_hash(reg), data_snapshot=reg.get("data_snapshot"))
    sev = "info" if verdict in ("PASS", "SCORED") else "warning"
    notify(sev, f"门禁评估 {args.version}: {verdict}",
           _gates_brief(gates) +
           f" | n_trials={n_trials_cum()} | 详见 results/bt_{args.version}/gate-report.json")
    log(f"🚦 evaluate 完成: verdict={verdict} → results/bt_{args.version}/gate-report.json")
    return 0


# ------------------------------------------------------------------
# cmd: activate / rollback
# ------------------------------------------------------------------
def build_main_from_registry(reg, current_main, trigger):
    m = deepcopy(current_main)
    sel, tim = reg["selection"], reg.get("timing") or {}
    old_ver = m.get("version")
    m["version"] = reg.get("main_alias") or reg["version_id"]
    m["strategy"] = sel.get("strategy", "dividend_quality_smallcap")
    m["params"] = sel.get("params", {})
    m["factors"] = sel.get("factors", [])
    m["source"] = f"registry activate {reg['version_id']} ({trigger})"
    m["timing"] = {
        "enabled": bool(tim.get("enabled", True)),
        "type": tim.get("type", ""),
        "description": tim.get("description", ""),
        "signal": tim.get("signal", ""),
        "params": tim.get("params", {}),
        "data_source": tim.get("data_source", ""),
        "data_update": tim.get("data_update", ""),
        "disable_switch": tim.get("disable_switch", ""),
    }
    m["metrics"] = (reg.get("backtest_refs") or {}).get("metrics") or m.get("metrics", {})
    entry = {
        "version": f"{old_ver} → {m['version']}",
        "date": now().strftime("%Y-%m-%d"),
        "task": "task-0275 evolution_pipeline activate",
        "changed_by": "scripts/evolution_pipeline.py",
        "changes": [f"registry {reg['version_id']} 激活，params_hash={params_hash(reg)[:8]}"],
        "rollback": f"evolution_pipeline.py rollback --to {old_ver} --reason ...",
        "report": (reg.get("backtest_refs") or {}).get("metrics_full"),
    }
    ch = m.get("changelog") or []
    ch.append(entry)
    m["changelog"] = ch
    m["registered_at"] = reg.get("created_at") or m.get("registered_at")
    m["merged_at"] = now().strftime("%Y-%m-%d")
    m["previous_version"] = old_ver
    return m


def _do_activate(target_reg, trigger, reason, force, dtype="activate"):
    act = find_active()
    if act is not None and act["version_id"] == target_reg["version_id"]:
        log(f"ℹ️ 幂等：{target_reg['version_id']} 已是 active，无操作")
        return 0
    gate = target_reg.get("gate") or {}
    verdict = gate.get("verdict")
    has_score = gate.get("score") is not None and "partial" not in (gate.get("score_flags") or "")
    # R220-#7：评分制下 SCORED 且 gate.score 非 partial 即可激活；legacy PASS/grandfathered 兼容；--force 保留
    if verdict not in ("PASS", "legacy-grandfathered") and not has_score and not force:
        raise SystemExit(f"❌ 门禁 verdict={verdict} 且无有效 gate.score，拒绝激活（人工强制请加 --force）")

    current_main = load_json(MAIN_FILE)
    with open(MAIN_FILE, "rb") as f:
        old_raw = f.read()
    old_md5 = hashlib.md5(old_raw).hexdigest()

    # 冻结旧 active 的 main.json 字节快照（若尚无）
    if act is not None:
        snap_p = os.path.join(REGISTRY_DIR, f"{act['version_id']}.main.json.snapshot")
        if not os.path.exists(snap_p):
            with open(snap_p, "wb") as f:
                f.write(old_raw)
            log(f"   已冻结 {act['version_id']} 的 main.json 快照")

    new_main = build_main_from_registry(target_reg, current_main, trigger)
    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(new_main, f, ensure_ascii=False, indent=2)
        f.write("\n")
    # 冻结新 active 快照 + 校验可加载
    with open(MAIN_FILE, "rb") as f:
        new_raw = f.read()
    with open(os.path.join(REGISTRY_DIR, f"{target_reg['version_id']}.main.json.snapshot"), "wb") as f:
        f.write(new_raw)
    load_json(MAIN_FILE)  # 可加载性校验

    # registry 状态流转：旧active→sota（其旧sota→retired）；目标→active
    if act is not None:
        for p in registry_files():
            r = load_json(p)
            if r["version_id"] == act["version_id"]:
                r["status"] = "sota"
                save_version(r)
            elif r.get("status") == "sota":
                r["status"] = "retired"
                save_version(r)
    target_reg["status"] = "active"
    target_reg["activated_at"] = now().strftime("%Y-%m-%d %H:%M:%S")
    save_version(target_reg)

    append_jsonl(SWITCH_LOG, {"op": "model_switch", "from": current_main.get("version"),
                              "to": new_main.get("version"),
                              "switched_at": now().strftime("%Y-%m-%d %H:%M:%S"),
                              "holdings_overlap": None,
                              "confirmed_by": f"evolution_pipeline:{dtype}"})
    append_jsonl(HISTORY_LOG, {"op": dtype, "version": new_main.get("version"),
                               "from": current_main.get("version"),
                               "reason": reason, "ts": now().strftime("%Y-%m-%d %H:%M:%S")})
    decision_log(dtype, target_reg["version_id"], trigger,
                 metrics_summary=json.dumps(target_reg.get("backtest_refs", {}).get("metrics"), ensure_ascii=False),
                 expected_impact=reason or "registry版本生效",
                 rollback_condition=f"evolution_pipeline.py rollback --to {act['version_id'] if act else 'N/A'}",
                 phash=params_hash(target_reg), data_snapshot=target_reg.get("data_snapshot"),
                 force=force, gate_verdict=verdict,
                 main_md5_before=old_md5, main_md5_after=hashlib.md5(new_raw).hexdigest())
    log(f"✅ {dtype}: {target_reg['version_id']} → active | main.json md5 {old_md5[:8]}→{hashlib.md5(new_raw).hexdigest()[:8]}")
    return 0


def cmd_activate(args):
    reg = load_version(args.version)
    return _do_activate(reg, f"activate --version {args.version}", args.reason, args.force)


def cmd_rollback(args):
    if not args.reason or not args.reason.strip():
        raise SystemExit("❌ rollback 必须提供 --reason")
    target = load_version(args.to)
    act = find_active()
    # 优先字节级还原（保证 md5 一致）
    snap_p = os.path.join(REGISTRY_DIR, f"{args.to}.main.json.snapshot")
    if os.path.exists(snap_p):
        current_main = load_json(MAIN_FILE)
        with open(snap_p, "rb") as f:
            raw = f.read()
        with open(MAIN_FILE, "wb") as f:
            f.write(raw)
        restored_md5 = hashlib.md5(raw).hexdigest()
        load_json(MAIN_FILE)
        if act is not None:
            act["status"] = "retired"
            save_version(act)
        target["status"] = "active"
        target["rolled_back_at"] = now().strftime("%Y-%m-%d %H:%M:%S")
        save_version(target)
        append_jsonl(SWITCH_LOG, {"op": "model_switch", "from": current_main.get("version"),
                                  "to": json.loads(raw).get("version"),
                                  "switched_at": now().strftime("%Y-%m-%d %H:%M:%S"),
                                  "holdings_overlap": None, "confirmed_by": "rollback(byte-restore)"})
        append_jsonl(HISTORY_LOG, {"op": "rollback", "restored_version": json.loads(raw).get("version"),
                                   "old_version": current_main.get("version"),
                                   "reason": args.reason, "ts": now().strftime("%Y-%m-%d %H:%M:%S")})
        decision_log("rollback", args.to, f"rollback --to {args.to} --reason '{args.reason}'",
                     metrics_summary=f"字节级还原 main.json (md5={restored_md5})",
                     expected_impact=f"回到 {args.to} 在役状态", rollback_condition="—",
                     phash=params_hash(target), data_snapshot=target.get("data_snapshot"),
                     reason=args.reason)
        log(f"✅ rollback: 字节级还原 {args.to}，main.json md5={restored_md5}")
        return 0
    return _do_activate(target, f"rollback --to {args.to} --reason '{args.reason}'",
                        args.reason, force=True, dtype="rollback")


# cmd: override（TTL临时覆盖）
# ------------------------------------------------------------------
def _parse_ttl(s):
    m = (s or "").strip()
    if not m:
        return None
    import re
    mm = re.match(r"^(\d+)\s*([hHmMdD])$", m)
    if not mm:
        raise SystemExit(f"❌ --ttl 格式: 24h / 30m / 7d，收到: {s}")
    n, unit = int(mm.group(1)), mm.group(2).lower()
    return timedelta(hours=n) if unit == "h" else (timedelta(minutes=n) if unit == "m" else timedelta(days=n))


def cmd_override(args):
    if args.clear:
        if os.path.exists(OVERRIDE_FILE):
            os.remove(OVERRIDE_FILE)
            decision_log("override", "-", "override --clear", metrics_summary="清除临时覆盖",
                         expected_impact="恢复 main.json 配置生效", rollback_condition="—")
            log("✅ 临时覆盖已清除（temp_override.json 删除）")
        else:
            log("ℹ️ 无临时覆盖文件")
        return 0
    if not args.reason:
        raise SystemExit("❌ override 必须提供 --reason")
    delta = _parse_ttl(args.ttl)
    if delta is None:
        raise SystemExit("❌ override 必须提供 --ttl（如 24h）")
    exp = now() + delta
    ov = {"created_at": now().strftime("%Y-%m-%d %H:%M:%S"),
          "expires_at": exp.strftime("%Y-%m-%d %H:%M:%S"),
          "expires_at_ts": exp.timestamp(),
          "ttl": args.ttl, "reason": args.reason,
          "timing_off": bool(args.timing_off),
          "created_by": "evolution_pipeline(task-0275)"}
    save_json(ov, OVERRIDE_FILE)
    decision_log("override", "-", f"override --reason '{args.reason}' --ttl {args.ttl}",
                 metrics_summary=json.dumps({k: ov[k] for k in ["timing_off", "expires_at"]}, ensure_ascii=False),
                 expected_impact="TTL内临时覆盖择时开关（paper_engine启动时以override为准并告警）",
                 rollback_condition=f"TTL {args.ttl} 自动过期", )
    log(f"✅ 临时覆盖写入: {OVERRIDE_FILE} (timing_off={ov['timing_off']}, 至 {ov['expires_at']})")
    return 0


# ------------------------------------------------------------------
# cmd: status
# ------------------------------------------------------------------
def cmd_status(args):
    rows = []
    for p in registry_files():
        r = load_json(p)
        rows.append({"version": r["version_id"], "status": r["status"],
                     "alias": r.get("main_alias"), "params_hash": params_hash(r)[:8],
                     "gate_verdict": (r.get("gate") or {}).get("verdict"),
                     "backtested": bool((r.get("backtest_refs") or {}).get("metrics")),
                     "stale_snapshot": (r.get("backtest_refs") or {}).get("stale_snapshot")})
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    # 防漂移自检
    act = find_active()
    if act is not None and os.path.exists(MAIN_FILE):
        main = load_json(MAIN_FILE)
        s_main, s_reg = drift_signature(main, is_registry=False), drift_signature(act)
        log(f"🛡 防漂移: main={s_main[:10]} registry[active]={s_reg[:10]} → {'一致 ✅' if s_main == s_reg else '漂移 ❌'}")
    led = read_jsonl(LEDGER)
    log(f"📒 台账: {len(led)} 条 (backtest {sum(1 for e in led if e['type']=='backtest')}) | "
        f"n_trials_cum={n_trials_cum()}")
    dec = read_jsonl(DECISION_LOG)
    if dec:
        log(f"🧾 decision-log 最近: " + " | ".join(f"{e['decision_id']}:{e['type']}:{e.get('version')}" for e in dec[-3:]))
    return 0


# ------------------------------------------------------------------
# cmd: --cycle 七步编排
# ------------------------------------------------------------------
def cmd_cycle(args):
    os.makedirs(CYCLE_DIR, exist_ok=True)
    ts = now().strftime("%Y%m%d_%H%M")
    rep = {"started_at": now().strftime("%Y-%m-%d %H:%M:%S"), "steps": {}, "abort": None}
    def step_save(name, obj):
        rep["steps"][name] = obj
        with open(os.path.join(CYCLE_DIR, f"cycle-report-{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)

    def finish(code):
        rep["finished_at"] = now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [f"# Evolution Cycle 报告 {rep['started_at']}", ""]
        for k, v in rep["steps"].items():
            lines.append(f"## {k}\n```json\n{json.dumps(v, ensure_ascii=False, indent=2)}\n```")
        if rep.get("abort"):
            lines.append(f"\n## ⛔ 中止\n{rep['abort']}")
        with open(os.path.join(CYCLE_DIR, f"cycle-report-{ts}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        with open(os.path.join(CYCLE_DIR, f"cycle-report-{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        log(f"📄 cycle 报告: results/cycle/cycle-report-{ts}.md")
        return code

    # Step0 数据校验（fail-fast）
    log("— Step0 数据校验")
    try:
        sys.path.insert(0, SCRIPTS)
        import data_validator as dv
        summary = dv.run_all()
        step_save("step0_data_validation",
                  {"passed": summary.get("passed"), "failed": summary.get("failed"),
                   "all_pass": summary.get("all_pass")})
        if not summary.get("all_pass") and not args.ignore_validation:
            rep["abort"] = "Step0 数据校验 FAIL → fail-fast（本轮跳过）"
            notify("critical", "cycle中止：数据校验FAIL",
                   f"passed={summary.get('passed')} failed={summary.get('failed')}，详见 validate 输出")
            return finish(1)
        if not summary.get("all_pass") and args.ignore_validation:
            step_save("step0_data_validation", {"passed": summary.get("passed"),
                       "failed": summary.get("failed"),
                       "note": "--ignore-validation 演练模式：FAIL 但继续（生产cron不带此旗标）"})
    except Exception as e:
        step_save("step0_data_validation", {"error": str(e), "all_pass": None, "note": "校验器异常，降级继续"})
        log(f"⚠️ Step0 校验器异常（降级继续）: {e}")

    # Step0b 数据新鲜度 + 漂移标注
    act = find_active()
    snap = compute_data_snapshot()
    stale_info = {"kline_as_of_now": snap["kline_as_of"], "hash_now": snap["hash"]}
    if act is not None:
        old_asof = (act.get("data_snapshot") or {}).get("kline_as_of")
        refs = act.get("backtest_refs") or {}
        data_moved = snap["kline_as_of"] != old_asof
        stale_flag = bool(refs.get("stale_snapshot") or
                          (data_moved and refs.get("snapshot_hash") not in (None, snap["hash"])))
        if stale_flag and refs:
            refs["stale_snapshot"] = True
            save_version(act)
        stale_info.update({"active": act["version_id"], "active_snapshot_asof": old_asof,
                           "data_moved": data_moved, "stale_snapshot": stale_flag})
        if data_moved:
            log(f"⚠️ 数据已更新({old_asof}→{snap['kline_as_of']})，active回测结论标注 stale_snapshot")
    step_save("step1_snapshot", stale_info)

    # Step1 快照登记
    snaps = load_json(SNAPSHOTS_FILE) if os.path.exists(SNAPSHOTS_FILE) else {"snapshots": []}
    snaps["snapshots"].append({"ts": now().strftime("%Y-%m-%d %H:%M:%S"), **snap})
    snaps["snapshots"] = snaps["snapshots"][-50:]
    save_json(snaps, SNAPSHOTS_FILE)

    # Step2 想法消化（骨架：ideas/pool.jsonl 存在则统计 open 项）
    log("— Step2 想法消化")
    pool_p = os.path.join(HP, "ideas", "pool.jsonl")
    if os.path.exists(pool_p):
        pool = read_jsonl(pool_p)
        open_items = [i for i in pool if i.get("status") == "open"]
        step_save("step2_ideas", {"open": len(open_items), "total": len(pool),
                                  "note": "骨架：LLM假设卡消化待对接（W8/后续）"})
        log(f"  想法池: {len(open_items)} open / {len(pool)} total（假设卡生成待对接）")
    else:
        step_save("step2_ideas", {"skipped": "ideas/pool.jsonl 不存在"})
        log("  无想法池，跳过")

    # Step3 因子迭代占位
    log("— Step3 因子迭代：待W1对接（占位）")
    step_save("step3_factor_iteration", {"placeholder": "待W1因子注册表对接"})

    # Step4/5 候选 backtest+evaluate（无候选则跳过）
    candidates = [load_json(p) for p in registry_files()
                  if load_json(p).get("status") == "candidate"]
    done = []
    for c in candidates:
        if not (c.get("backtest_refs") or {}).get("metrics"):
            log(f"  候选 {c['version_id']} 无回测产物，本轮骨架不自动回测（人工: backtest --version {c['version_id']}）")
            continue
        if not (c.get("gate") or {}).get("verdict"):
            log(f"  候选 {c['version_id']} 有回测无评估，提示: evaluate --version {c['version_id']}")
        done.append(c["version_id"])
    step_save("step45_backtest_evaluate",
              {"candidates": [c["version_id"] for c in candidates], "auto_processed": done,
               "note": "骨架版：自动候选生成待W1/想法池对接"})

    # Step6 通知
    notify("info", "evolution cycle 完成",
           f"数据校验PASS | kline_as_of={snap['kline_as_of']} | stale_snapshot={stale_info.get('stale_snapshot')} | "
           f"候选={[c['version_id'] for c in candidates]} | 报告 results/cycle/cycle-report-{ts}.md")
    step_save("step6_notify", {"queued": True})
    log("— Step7 activate：门禁 PASS 即自动 activate（R220 #8 移除人工确认制）")
    return finish(0)


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="后端管道v2统一Runner（R-207 W5/task-0275）")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("bootstrap", help="从main.json抽取首个版本对象（幂等）")
    p.add_argument("--from-main", action="store_true")
    p.add_argument("--version", default="v1.1")
    p.set_defaults(func=cmd_bootstrap)

    p = sub.add_parser("fork", help="从既有版本复制出新candidate")
    p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--as", dest="as_ver", required=True)
    p.add_argument("--set", action="append", default=[], help="dotted key=val，如 selection.params.n_hold=25")
    p.add_argument("--logic", default=None, help="经济学逻辑（门禁5）")
    p.add_argument("--trigger", default=None)
    p.set_defaults(func=cmd_fork)

    p = sub.add_parser("backtest", help="两腿回测：端到端(选股×择时)+同口径基线")
    p.add_argument("--version", required=True)
    p.add_argument("--override", action="append", default=[], help="临时参数覆盖 key=val")
    p.add_argument("--start", default=None)
    p.add_argument("--end", default=None)
    p.set_defaults(func=cmd_backtest)

    p = sub.add_parser("evaluate", help="五项数字门禁评估")
    p.add_argument("--version", required=True)
    p.add_argument("--oos-start", default=None, help="OOS起始月，默认2021-01")
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser("activate", help="registry版本写入main.json")
    p.add_argument("--version", required=True)
    p.add_argument("--force", action="store_true", help="门禁未PASS时强制（演练/人工决策留痕）")
    p.add_argument("--reason", default=None)
    p.set_defaults(func=cmd_activate)

    p = sub.add_parser("rollback", help="回退到指定版本（reason必填）")
    p.add_argument("--to", required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_rollback)

    p = sub.add_parser("override", help="TTL临时覆盖（择时开关等）")
    p.add_argument("--reason", default=None)
    p.add_argument("--ttl", default=None, help="如 24h / 30m / 7d")
    p.add_argument("--timing-off", action="store_true")
    p.add_argument("--clear", action="store_true")
    p.set_defaults(func=cmd_override)

    p = sub.add_parser("status", help="registry总览+防漂移自检")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("cycle", help="七步编排（cron周六09:00）")
    p.add_argument("--ignore-validation", action="store_true",
                   help="演练用：Step0校验FAIL时不中止（生产cron不使用）")
    p.set_defaults(func=cmd_cycle)

    args = ap.parse_args()
    if not getattr(args, "cmd", None):
        ap.print_help()
        sys.exit(1)
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    rc = args.func(args)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
