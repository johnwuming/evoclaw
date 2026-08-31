#!/usr/bin/env python3
# task-0605: 两腿 6.94pp MDD 分歧溯源复算脚本（只读数据，产物落 work/）
import csv, json, math

BASE = "/root/.openclaw/workspace/shared/results"
QC = "/root/.openclaw/workspace/tools/quant-bff/live/data"

def load_a_alone():
    rows = []
    with open(f"{BASE}/04-投资研究/f6_curves/a_alone_nav.csv") as f:
        for r in csv.DictReader(f):
            rows.append((r["date"], float(r["nav"])))
    return rows

def load_gold():
    rows = []
    with open(f"{BASE}/04-投资研究/engines/gold/shadow_nav.csv") as f:
        for r in csv.DictReader(f):
            rows.append((r["month"], float(r["gold_ret"])))
    return rows

def load_navcurves():
    a = {}
    with open(f"{QC}/nav_curves.csv") as f:
        for r in csv.DictReader(f):
            a[r["month"]] = float(r["A"])
    return a

def nav_to_ret(rows):
    # 首月收益 = nav/1 - 1（净值从 2013-07-31=1 起算，首月含完整 2013-08 收益）
    rets = []
    prev = 1.0
    for d, v in rows:
        rets.append((d, v / prev - 1.0))
        prev = v
    return rets

def perf(rets):
    nav = 1.0
    peak = 1.0
    mdd = 0.0
    navs = []
    for _, r in rets:
        nav *= (1 + r)
        navs.append(nav)
        peak = max(peak, nav)
        mdd = min(mdd, nav / peak - 1)
    n = len(rets)
    ann = nav ** (12 / n) - 1
    vol = (sum(r * r for _, r in rets) / n) ** 0.5 * math.sqrt(12)
    sharpe = ann / vol if vol > 0 else None  # rf=0 简化口径
    calmar = ann / abs(mdd) if mdd != 0 else None
    return {"n": n, "ann": round(ann * 100, 4), "vol": round(vol * 100, 4),
            "mdd": round(mdd * 100, 4), "sharpe": round(sharpe, 3) if sharpe else None,
            "calmar": round(calmar, 3) if calmar else None,
            "final_nav": round(nav, 6)}

def two_leg(a_rets, g_map, wA, rebalance=True, cost=0.0):
    # 静态 wA/(1-wA) 月度再平衡组合；cost=双腿换手成本率，按 |Δw| 计
    out = []
    curA, curG = wA, 1 - wA  # 月初再平衡到位
    for d, ra in a_rets:
        rg = g_map[d]
        rp = curA * ra + curG * rg
        if cost > 0 and rebalance:
            # 月末漂移后再平衡的换手
            endA = curA * (1 + ra) / (1 + rp)
            turn = abs(endA - wA) / max(wA, 1e-9) * wA  # 换手占总资产比例
            rp -= cost * (abs(endA - wA))
        out.append((d, rp))
        curA, curG = wA, 1 - wA  # 月度再平衡
    return out

def buyhold(a_rets, g_map, wA):
    out = []
    curA, curG = wA, 1 - wA
    for d, ra in a_rets:
        rg = g_map[d]
        rp = curA * ra + curG * rg
        out.append((d, rp))
        curA = curA * (1 + ra) / (1 + rp)
        curG = 1 - curA
    return out

results = {}
a_rows = load_a_alone()
g_rows = load_gold()
g_map = {d: r for d, r in g_rows}
a_rets = nav_to_ret(a_rows)

# 0) 单腿参照
results["A_alone"] = perf(a_rets)
results["gold_alone"] = perf([(d, g_map[d]) for d, _ in a_rets])

# 1) 主复算：a_alone + gold_ret, 0.58/0.42, 月度再平衡, 无成本, 2013-08..2026-07 (n=156)
results["main_5842_n156"] = perf(two_leg(a_rets, g_map, 0.58))

# 2) 买入持有漂移
results["bh_5842_n156"] = perf(buyhold(a_rets, g_map, 0.58))

# 3) 展示口径精确权重 0.5803/0.4197 + 双腿 0.13% 成本（近似 task-0602 实现）
results["disp_5803_cost_n156"] = perf(two_leg(a_rets, g_map, 0.5803, cost=0.0013))
results["disp_5803_nocost_n156"] = perf(two_leg(a_rets, g_map, 0.5803))

# 4) 同窗 2016-08..2026-07（对 R-372 表内 n=121 口径近似，缺 2026-08）
w = [(d, r) for d, r in a_rets if d >= "2016-08-31"]
results["same_2016_5842_n120"] = perf(two_leg(w, g_map, 0.58))

# 5) MDD 深挖：逐年最深处
rets = two_leg(a_rets, g_map, 0.58)
nav, peak, dd_series = 1.0, 1.0, []
for d, r in rets:
    nav *= (1 + r)
    peak = max(peak, nav)
    dd_series.append((d, round((nav / peak - 1) * 100, 2)))
worst = sorted(dd_series, key=lambda x: x[1])[:8]
results["worst_dd_points_5842"] = worst

# 6) A 腿自身最深回撤点（月频）
nav, peak, ddA = 1.0, 1.0, []
for d, r in a_rets:
    nav *= (1 + r)
    peak = max(peak, nav)
    ddA.append((d, round((nav / peak - 1) * 100, 2)))
results["worst_dd_A_alone"] = sorted(ddA, key=lambda x: x[1])[:5]

# 7) 2015 段单月收益对比（验证两序列 2015 股灾表现）
results["A_2015_months"] = [(d, round(r * 100, 2)) for d, r in a_rets if d.startswith("2015")]
results["gold_2015_months"] = [(d, round(g_map[d] * 100, 2)) for d, _ in a_rets if d.startswith("2015")]

with open(f"{BASE}/work/task-0605-results.json", "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print(json.dumps(results, ensure_ascii=False, indent=1))
