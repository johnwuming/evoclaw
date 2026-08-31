#!/usr/bin/env python3
# task-0606: 账本对账 + 污染月名单 + 反事实净值（本地只读）
import pandas as pd, numpy as np, json

BASE = "/root/.openclaw/workspace/shared/results"
sig = pd.read_csv(f"{BASE}/work/task-0606-hp-signals.csv", parse_dates=["Unnamed: 0"]).rename(columns={"Unnamed: 0": "me"}).set_index("me")
led = pd.read_csv(f"{BASE}/04-投资研究/engines/gold/shadow_nav.csv", parse_dates=["month"]).set_index("month")
COST = 0.0013

# 账本行 t 的信号月末 = 上一个日历月末 → sig 整体前移一位（按位置）
sig_prev = sig.shift(1)  # row t of sig_prev = signal at month-end t-1
# map: ledger month -> sig_prev at same month-end label
common = led.index.intersection(sig_prev.index)
led = led.loc[common]; sp = sig_prev.loc[common]

res = pd.DataFrame({
    "w_applied": led["w_applied"], "w_eng_recomputed": sp["w_eng"], "w_true": sp["w_asof"],
    "gold_ret": led["gold_ret"], "mmf_ret": led["mmf_ret"],
    "gross": led["gross"], "net": led["net"], "nav": led["nav"],
    "prev_me_is_cal_nan": sp["is_cal_nan"].astype(bool),
    "prev_me_is_warmup_nan": sp["is_warmup_nan"].astype(bool),
})
res["agree_engine_vs_ledger"] = (res["w_eng_recomputed"] - res["w_applied"]).abs() < 1e-4  # 账本存4位小数

# 成本模型自洽性验证：net ?= gross - COST*|dw|
dw = res["w_applied"].diff().abs(); dw.iloc[0] = abs(res["w_applied"].iloc[0] - 0.0)
net_recomputed = res["gross"] - dw * COST
res["cost_model_ok"] = (net_recomputed - res["net"]).abs() < 1e-9

# 污染行：上月末为日历NaN 且 w_true != w_applied（引擎 NaN→0，故即 w_true>0）
res["contaminated"] = res["prev_me_is_cal_nan"] & ((res["w_true"] - res["w_applied"]).abs() > 1e-9)
cont = res[res["contaminated"]].copy()
cont["pnl_diff_gross"] = (cont["w_true"] - cont["w_applied"]) * cont["gold_ret"]
cont["net_gain"] = cont["pnl_diff_gross"] > 0

# 反事实净值（w_true 全路径替换，同成本模型）
wt = res["w_true"]
gross_t = wt * res["gold_ret"] + (1 - wt) * res["mmf_ret"]
dwt = wt.diff().abs(); dwt.iloc[0] = abs(wt.iloc[0] - 0.0)
net_t = gross_t - dwt * COST
nav_true = (1 + net_t).cumprod()
nav_act = led["nav"]

def mdd(nav):
    dd = 1 - nav / nav.cummax()
    i = dd.idxmax()
    return float(dd.max()), str(i.date())

mdd_act, when_act = mdd(nav_act)
mdd_true, when_true = mdd(nav_true)

out = {
    "n_rows": int(len(res)),
    "engine_w_vs_ledger_agree": int(res["agree_engine_vs_ledger"].sum()),
    "cost_model_ok": int(res["cost_model_ok"].sum()),
    "n_contaminated_rows": int(res["contaminated"].sum()),
    "contaminated_months": [d.strftime("%Y-%m") for d in cont.index],
    "contaminated_detail": [
        {"month": d.strftime("%Y-%m"), "w_applied": round(r.w_applied, 4), "w_true": round(r.w_true, 4),
         "gold_ret": round(r.gold_ret, 4), "gross_pnl_diff": round(r.pnl_diff_gross, 5)}
        for d, r in cont.iterrows()],
    "contaminated_helped": int((cont["net_gain"] == False).sum()),   # w_true>0 但当月 gold 跌 → 躁损避雷（bug 反而帮忙）
    "contaminated_hurt": int((cont["net_gain"] == True).sum()),
    "sum_monthly_gross_diff": round(float(cont["pnl_diff_gross"].sum()), 5),
    "nav_end_actual": round(float(nav_act.iloc[-1]), 6),
    "nav_end_true": round(float(nav_true.iloc[-1]), 6),
    "nav_diff_end": round(float(nav_true.iloc[-1] - nav_act.iloc[-1]), 6),
    "mdd_actual": round(mdd_act, 6), "mdd_actual_when": when_act,
    "mdd_true": round(mdd_true, 6), "mdd_true_when": when_true,
    "ann_actual": round(float(nav_act.iloc[-1] ** (12 / len(nav_act)) - 1), 6),
    "ann_true": round(float(nav_true.iloc[-1] ** (12 / len(nav_true)) - 1), 6),
}
with open(f"{BASE}/work/task-0606-results.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
res.to_csv(f"{BASE}/work/task-0606-ledger-join.csv")
cont.to_csv(f"{BASE}/work/task-0606-contaminated.csv")
print(json.dumps({k: v for k, v in out.items() if k != "contaminated_detail"}, ensure_ascii=False, indent=1))
print("DETAIL:")
for d in out["contaminated_detail"]:
    print(d)
