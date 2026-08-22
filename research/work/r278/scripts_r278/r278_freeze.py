#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r278_freeze.py — task-0455 [R-278 §七.1] 冻结 PCR_oi 信号状态 + 双锚校验
从 results/r272/monthly_panel.csv (R-272 E1 沉淀) 导出 pcroi_states.csv (ym/pcroi_pct/active)。
锚校验: 贪婪月 n=27 且 next-mkt 均值=-1.98% (R-272 §三.1 逐位一致), 失败即退出非零。
"""
import os, sys, json, hashlib
import pandas as pd

os.chdir("/home/noname/quant-evolve")
W = "results/work/r278"
os.makedirs(W, exist_ok=True)

panel = pd.read_csv("results/r272/monthly_panel.csv", dtype={"ym": str})
assert panel["ym"].is_unique, "ym not unique"
s = panel[["ym", "pcroi_pct"]].copy()
s["active"] = ((s["pcroi_pct"] <= 0.30) & s["pcroi_pct"].notna()).astype(int)
out = os.path.join(W, "pcroi_states.csv")
s.to_csv(out, index=False)
md5 = hashlib.md5(open(out, "rb").read()).hexdigest()

act = s[s["active"] == 1]
n_act = len(act)
nxt = panel.set_index("ym").loc[act["ym"], "mkt_next"].mean() * 100
ok_n = (n_act == 27)
ok_m = abs(nxt - (-1.98)) < 0.005
summary = {
    "task": "task-0455 R-278 freeze",
    "source": "results/r272/monthly_panel.csv",
    "source_md5": hashlib.md5(open("results/r272/monthly_panel.csv", "rb").read()).hexdigest(),
    "out": out, "out_md5": md5,
    "threshold": "pcroi_pct<=0.30 (roll36m min24, R-272 frozen)",
    "n_valid": int(s["pcroi_pct"].notna().sum()),
    "n_active": int(n_act),
    "active_next_mkt_mean_pct": round(float(nxt), 4),
    "anchor_n27_pass": bool(ok_n), "anchor_mean_pass": bool(ok_m),
    "active_months": act["ym"].tolist(),
}
json.dump(summary, open(os.path.join(W, "freeze_summary.json"), "w"),
          ensure_ascii=False, indent=1)
print(json.dumps({k: summary[k] for k in
                  ("out_md5", "n_valid", "n_active", "active_next_mkt_mean_pct",
                   "anchor_n27_pass", "anchor_mean_pass")}, ensure_ascii=False))
if not (ok_n and ok_m):
    print("FREEZE ANCHOR FAIL"); sys.exit(3)
print("FREEZE OK")
