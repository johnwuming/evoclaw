#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0398: 创建 a13_rsraw_e1f10dz registry 条目（status=candidate）"""
import json, os, datetime

HP = "/home/noname/quant-evolve"
os.chdir(HP)
rsr = json.load(open("model/registry/a9_ranksum_raw.json"))
mL = json.load(open("results/a13_rsraw_e1f10dz_locked_metrics.json"))
mF = json.load(open("results/a13_rsraw_e1f10dz_full_metrics.json"))

# nav 边界核实（eval_window 用）
import csv
with open("results/a13_rsraw_e1f10dz_locked_nav.csv") as f:
    rows = list(csv.DictReader(f))
lock_start, lock_end = rows[0]["date"], rows[-1]["date"]
with open("results/a13_rsraw_e1f10dz_full_nav.csv") as f:
    rowsF = list(csv.DictReader(f))
full_end = rowsF[-1]["date"]
bt_at = datetime.datetime.fromtimestamp(os.path.getmtime("results/a13_rsraw_e1f10dz_locked_metrics.json")).strftime("%Y-%m-%d %H:%M:%S")

reg = {
    "version_id": "a13_rsraw_e1f10dz",
    "status": "candidate",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "main_alias": "a13_rsraw_e1f10dz",
    "selection": {
        "strategy": "raw_universe_ranksum4",
        "params": {
            "sort": "ext",
            "ext_mode": "ranksum",
            "ext_specs": [["log_mv", 1.0, -1], ["amt20", 1.0, -1], ["pb_inv", 0.7, 1.0], ["roe", 0.3, 1.0]],
            "ext_filter_all": 1,
            "raw_universe": 1,
            "e1_guard": 0,
            "e1_lambda": 1.0,
            "e1_deadzone": 0.30,
            "xsub_days": 365.0,
            "n_hold": 20,
            "cost_model": "v2",
            "limit_board": "on",
            "min_amt": 0.0,
            "div_min": 0.02,
            "roe_min": 0.15,
            "roa_min": 0.1,
            "price_cap": 10.0,
            "capital_base": 10000000.0
        },
        "factors": ["circ_mv", "avg_amount_20d", "pb_inv", "roe_ttm", "mom_pen_dz"]
    },
    "timing": rsr["timing"],
    "data_snapshot": rsr["data_snapshot"],
    "code_ref": "scripts/a13_run.py C4(e1_lambda=1.0, e1_deadzone=0.30) + a9_common A9 patch; registry 化 task-0398 手工登记（D-20260819-G3CORR 口径下正式 evaluate）",
    "backtest_refs": {
        "endtoend": "results/a13_rsraw_e1f10dz_locked_nav.csv",
        "baseline": "results/a13_rsraw_e1f10dz_full_nav.csv",
        "metrics": {k: mL.get(k) for k in ("annual_return", "max_drawdown", "sharpe", "calmar",
                                            "cumulative_return", "monthly_win_rate", "years",
                                            "num_rebalance", "avg_holdings", "monthly_turnover_est")},
        "metrics_full": {k: mF.get(k) for k in ("annual_return", "max_drawdown", "sharpe", "calmar",
                                                 "cumulative_return", "monthly_win_rate", "years",
                                                 "num_rebalance", "avg_holdings", "monthly_turnover_est")},
        "eval_window": "locked %s~%s (AUDIT_LOCK_END 正式口径), full~%s" % (lock_start, lock_end, full_end),
        "snapshot_hash": rsr["backtest_refs"].get("snapshot_hash"),
        "stale_snapshot": False,
        "backtested_at": bt_at
    },
    "gate": {
        "logic": "E1因子化λ1.0死区: ranksum四因子排序分叠加动量惩罚 1.0*|clip(ret120,-1,0)| 仅 ret120<-30% 段计罚(旧闸门域), (-30%,0) 死区不计罚, 取代硬排除护栏"
    },
    "provenance": {
        "trigger": "task-0395 R-242 重评建议#2 + task-0398 g3 口径修正(用户 2026-08-19 15:04 批准 A 方案)",
        "parent": "a9_ranksum_raw",
        "report": "shared/results/05-量化投资/R-242-e1f10dz重评与corr口径复核.md"
    }
}
out = "model/registry/a13_rsraw_e1f10dz.json"
json.dump(reg, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
# 校验
r2 = json.load(open(out))
assert r2["selection"]["params"]["e1_lambda"] == 1.0
print("registry written:", out, "| lock", lock_start, "~", lock_end, "| full~", full_end, "| bt_at", bt_at)
