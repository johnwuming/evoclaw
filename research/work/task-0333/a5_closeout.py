#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0333 A5 阶段4收口: 批次决策 (0 activate 预期, 战役目标未达)
- 逐候选门禁 + 战役目标对照表写入 results/a5_campaign_table.json
- decision-log D-20260817-A5-01 批次收口
"""
import os, sys, json, time
sys.path.insert(0, "/home/noname/quant-evolve/scripts")
import evolution_pipeline as ep

HP = "/home/noname/quant-evolve"

# 战役目标 (locked 口径)
TARGET = {"annual_return": 0.25, "max_drawdown": -0.20, "sharpe": 1.2}

# 现役对照
active = ep.find_active()
act_m = (active.get("backtest_refs") or {}).get("metrics") or {}
print("active:", active.get("version_id"), {k: act_m.get(k) for k in ["annual_return","max_drawdown","sharpe"]})

gate_table = ep.load_json(os.path.join(HP, "results/a5_gate_table.json"))
summary = ep.load_json(os.path.join(HP, "results/a5_backtest_summary_none.json"))

rows = {}
for ver, g in gate_table.items():
    lm = summary["candidates"].get(ver, {}).get("formal_locked", {})
    gap = {
        "ann_gap_pp": round((TARGET["annual_return"] - lm.get("annual_return", 0)) * 100, 2),
        "mdd_gap_pp": round((TARGET["max_drawdown"] - lm.get("max_drawdown", 0)) * 100, 2),
        "sharpe_gap": round(TARGET["sharpe"] - lm.get("sharpe", 0), 3),
    }
    better_than_active = (
        lm.get("annual_return", 0) > act_m.get("annual_return", 0) and
        lm.get("max_drawdown", 0) > act_m.get("max_drawdown", 0) and
        lm.get("sharpe", 0) > act_m.get("sharpe", 0)
    )
    rows[ver] = {
        "verdict": g.get("verdict"),
        "gates": g.get("gates"),
        "locked": {k: round(lm.get(k, 0), 4) for k in ["annual_return","max_drawdown","sharpe","calmar"]},
        "gap_vs_target": gap,
        "better_than_active": bool(better_than_active),
        "action": "activate" if (g.get("verdict") == "PASS" and better_than_active) else
                  ("pending" if g.get("verdict") == "PASS" else "reject"),
    }

with open(os.path.join(HP, "results/a5_campaign_table.json"), "w", encoding="utf-8") as f:
    json.dump({"target": TARGET, "active": active.get("version_id"), "rows": rows,
               "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}, f, ensure_ascii=False, indent=1)

n_pass = sum(1 for r in rows.values() if r["verdict"] == "PASS")
n_activate = sum(1 for r in rows.values() if r["action"] == "activate")
print("PASS:", n_pass, "activate:", n_activate)
for ver, r in rows.items():
    print(ver, r["verdict"], r["action"], r["locked"], "gap:", r["gap_vs_target"], "better:", r["better_than_active"])

# decision-log 批次收口
ep.decision_log("a5_batch_closeout", "/".join(rows.keys()) if rows else "none",
    trigger="task-0333 A5 batch closeout (成长×质量+动量护栏+价值降级批次)",
    metrics_summary=(
        f"5候选: PASS={n_pass}, activate={n_activate}; "
        f"战役目标 25%/-20%/1.2 全部未达; 现役 v2b_trr({act_m.get('annual_return',0)*100:.2f}%/"
        f"{act_m.get('max_drawdown',0)*100:.2f}%/{act_m.get('sharpe',0):.3f}) 未被严格超越; "
        "成长×质量复合IC为负(IC预检已证)在回测中未增alpha; E1护栏单加(MDD -28.99%)略优现役但年化/Sharpe降"
    ),
    expected_impact="0 activate; 结论: 当前宇宙+择时框架下 25%/-20%/1.2 无交点(Calmar不变式), 下一批需换赛道(见报告)",
    rollback_condition="不适用",
    phash=None, data_snapshot=ep.compute_data_snapshot())
print("A5_CLOSEOUT_DONE")
