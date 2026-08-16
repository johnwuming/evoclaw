#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0333 A5 阶段4: 候选 registry 注册 + ledger (fork 自 parent, IT-A5-01..05, features 字段)
不修改任何管线代码。"""
import os, sys, json, time, copy
sys.path.insert(0, "/home/noname/quant-evolve/scripts")
import evolution_pipeline as ep

HP = "/home/noname/quant-evolve"
summary = ep.load_json(os.path.join(HP, "results/a5_backtest_summary_none.json"))
cands = summary["candidates"]
snap = ep.compute_data_snapshot()
print("equiv:", summary.get("equiv_check"))

PARENT_FACTORS = ["div_yield_ttm", "roe_ttm", "roa_ttm", "circ_mv"]

TIMING_TRR = {"enabled": True, "type": "q3z_x_ew_trend_overlay",
    "params": {"layer": "macro_timing_layer_iter4 + a5 EW-trend",
               "q_key": "q3z(win36,zscore,hi1.0,cut0.40,w_min0.3)",
               "trend": "池内等权指数(含退市)月末收盘 vs MA200, 破位×0.6",
               "combine": "月度乘法合成, 无重裁剪(自然下限0.18)"},
    "description": "q3z × 趋势二信号 [v2b_trr 血统]",
    "signal": "EW指数月末<MA200 → ×0.6; 与q3z仓位系数相乘",
    "data_source": "全池日线收益(含退市, 无幸存者偏差)", "data_update": "日频(月度采样)",
    "disable_switch": "temp_override 可TTL关闭"}
NO_TIMING = {"enabled": False, "type": "", "params": {}, "description": "无择时层",
    "signal": "", "data_source": "", "data_update": "", "disable_switch": ""}

GQCOLS = ["revenue_yoy","net_profit_yoy","profit_accel","buf_quality","cf_np_ratio","peg_np"]
MOMCOLS = ["ret120","dist250h"]

def gq_params(wmv, wgq, **extra):
    p = {"sort": "gq", "gq_weights": [wmv, wgq], "value_cols": GQCOLS, "mom_cols": MOMCOLS}
    p.update(extra)
    return p

SPEC = {
    "v4a_gqe1": {"it": "IT-A5-01", "parent": "v2b_trr",
        "params": gq_params(0.6, 0.4, e1_guard=True), "timing": TIMING_TRR,
        "factors": PARENT_FACTORS + ["revenue_yoy","net_profit_yoy","profit_accel","buf_quality","cf_np_ratio","ret120"],
        "features": {"sort_key": "gq(0.6mv+0.4gq)", "e1_guard": "ret120>-30%", "g1_boost": False,
                     "peg_filter": None, "timing": "q3z_tr", "dim_changed": "sort_mv→gq + E1护栏"},
        "logic": ("成长×质量复合排序(0.6·(-z mv)+0.4·z(gq), gq=z(grw)+z(qly)) + E1动量护栏(ret120>-30%) "
                  "+ v2b_trr双信号择时; a4d证该宇宙价值IC全负故价值不作主键, postmortem证E1砍20.8%尾部亏损/误杀12.1%赢家, "
                  "任务骨架a: 成长×质量替换纯mv + E1 + v2b择时")},
    "v4b_mve1": {"it": "IT-A5-02", "parent": "v2b_trr",
        "params": gq_params(1.0, 0.0, e1_guard=True), "timing": TIMING_TRR,
        "factors": PARENT_FACTORS + ["ret120"],
        "features": {"sort_key": "mv(纯)", "e1_guard": "ret120>-30%", "g1_boost": False,
                     "peg_filter": None, "timing": "q3z_tr", "dim_changed": "仅加E1护栏(对照)"},
        "logic": ("纯mv排序 + E1动量护栏 + v2b择时; 任务骨架b: 纯护栏增量验证对照——隔离E1对现役v2b_trr的边际贡献, "
                  "postmortem E1证据为纯过滤机制不依赖排序")},
    "v4c_gqpeg": {"it": "IT-A5-03", "parent": "v2b_trr",
        "params": gq_params(0.6, 0.4, e1_guard=True, peg_max=2.0), "timing": TIMING_TRR,
        "factors": PARENT_FACTORS + ["revenue_yoy","net_profit_yoy","profit_accel","buf_quality","cf_np_ratio","peg_np","ret120"],
        "features": {"sort_key": "gq(0.6mv+0.4gq)", "e1_guard": "ret120>-30%", "g1_boost": False,
                     "peg_filter": "peg_np<2(软)", "timing": "q3z_tr", "dim_changed": "gqe1 + PEG<2软过滤"},
        "logic": ("任务骨架c: 在a基础上加PEG<2软过滤——价值降级为过滤而非排序(a4d证价值排序无alpha, 但postmortem E3系高股息陷阱"
                  "提示极端高估值小盘可能是接飞刀; PEG过滤测'过滤性价值'是否止损降MDD")},
    "v4d_gqg1": {"it": "IT-A5-04", "parent": "v2b_trr",
        "params": gq_params(0.5, 0.5, e1_guard=True, g1_boost=True, g1_bonus=0.5), "timing": TIMING_TRR,
        "factors": PARENT_FACTORS + ["revenue_yoy","net_profit_yoy","profit_accel","buf_quality","cf_np_ratio","ret120","dist250h"],
        "features": {"sort_key": "gq3(0.5mv+0.5gq)", "e1_guard": "ret120>-30%", "g1_boost": "dist250h>-10%&ret120>0加分",
                     "peg_filter": None, "timing": "q3z_tr", "dim_changed": "三维混合 + G1加强"},
        "logic": ("任务骨架d: 成长×质量×小市值三维混合 + G1加强(接近年高点dist250h>-10%且ret120>0加分项) + v2b择时; "
                  "postmortem G1 avg+21.2%/胜率78.4%为最强赢面信号, 与E1护栏叠加")},
    "v4e_gqg1x": {"it": "IT-A5-05", "parent": "v0_seed",
        "params": gq_params(0.5, 0.5, e1_guard=True, g1_boost=True, g1_bonus=0.5), "timing": NO_TIMING,
        "factors": PARENT_FACTORS + ["revenue_yoy","net_profit_yoy","profit_accel","buf_quality","cf_np_ratio","ret120","dist250h"],
        "features": {"sort_key": "gq3(0.5mv+0.5gq)", "e1_guard": "ret120>-30%", "g1_boost": "dist250h>-10%&ret120>0加分",
                     "peg_filter": None, "timing": None, "dim_changed": "d的裸选股版(无择时, 归因对照)"},
        "logic": ("任务骨架e: d的裸选股版(无择时)——归因对照, 量化择时对MDD的贡献; "
                  "a2c Calmar不变式预期: 无择时年化升但MDD大幅恶化")},
}

keep = ["annual_return", "max_drawdown", "sharpe", "calmar",
        "cumulative_return", "monthly_win_rate", "years", "num_rebalance",
        "avg_holdings", "monthly_turnover_est"]

for ver, sp in SPEC.items():
    win = cands[ver]
    lm, fm = win["formal_locked"], win["formal_full"]
    parent = ep.load_version(sp["parent"])
    reg = copy.deepcopy(parent)
    reg["version_id"] = ver
    reg["status"] = "candidate"
    reg["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    reg["main_alias"] = ver
    reg["selection"] = dict(parent["selection"])
    reg["selection"]["params"] = dict(sp["params"])
    reg["selection"]["factors"] = sp["factors"]
    reg["timing"] = sp["timing"]
    reg["gate"] = {"icir_is": None, "icir_oos": None, "max_corr": None, "dsr": None,
                   "logic": sp["logic"], "n_trial": None, "verdict": None, "note": sp["features"]["dim_changed"]}
    reg["provenance"] = {"trigger": "task-0333 A5 fork (成长×质量+动量护栏+价值降级批次)",
                         "parent": sp["parent"], "report": None}
    reg.pop("main_snapshot", None)
    refs = {
        "endtoend": f"results/a5_{ver}_formal_locked_nav.csv",
        "baseline": f"results/a5_{ver}_formal_full_nav.csv",
        "metrics": {k: lm[k] for k in keep},
        "metrics_full": f"results/a5_{ver}_formal_locked_metrics.json",
        "eval_window": "locked 2006-01-01~2024-06-30 (AUDIT_LOCK_END, 正式口径)",
        "full_window": {"metrics": {k: fm[k] for k in keep},
                        "metrics_file": f"results/a5_{ver}_formal_full_metrics.json"},
        "snapshot_hash": snap["hash"], "stale_snapshot": False,
        "backtested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    reg["data_snapshot"] = {"kline_as_of": snap["kline_as_of"], "hash": snap["hash"], "note": snap.get("hash_method")}
    reg["backtest_refs"] = refs
    ep.save_version(reg)
    ep.ledger_append("backtest", ver,
                     metrics={"experiment_id": sp["it"], "features": sp["features"],
                              "full": {k: fm[k] for k in keep},
                              "locked": {k: lm[k] for k in keep}},
                     data_snapshot=reg.get("data_snapshot"), phash=ep.params_hash(reg))
    print("  %s (%s) parent=%s locked_ann=%.4f mdd=%.4f sharpe=%.3f refs+ledger OK" % (
        ver, sp["it"], sp["parent"], lm["annual_return"], lm["max_drawdown"], lm["sharpe"]))
print("A5_POST_BT_DONE")
