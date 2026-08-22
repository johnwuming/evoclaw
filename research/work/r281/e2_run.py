#!/usr/bin/env python3
# task-0463 R-285 冻结契约执行: 可转债轮动 E2 回测
# V1 主试验(唯一判胜) + V2 敏感性(无黑名单, 仅披露) + IC 衰减监控(信用过滤后 universe)
# 冻结参数来源: shared/results/work/r281/e2_prereg.json (sha256 bcd2fe4f...), 零事后修改
import pandas as pd, numpy as np, json, os, re

OUT = "/root/.openclaw/workspace/work/r286"
os.makedirs(OUT, exist_ok=True)

# ---------- 1. 数据加载 ----------
PANEL = "/root/.openclaw/workspace/work/r281/panel_daily.parquet"
COVLIST = "/tmp/r281/cov_list.parquet"
panel = pd.read_parquet(PANEL)
lst = pd.read_parquet(COVLIST)

meta = lst.copy()
meta["code"] = meta["债券代码"].astype(str).str.zfill(6)
meta["list_dt"] = pd.to_datetime(meta["上市时间"], errors="coerce")
meta["issue_sz"] = pd.to_numeric(meta["发行规模"], errors="coerce")
meta = meta[["code", "债券简称", "list_dt", "issue_sz", "信用评级"]].rename(columns={"信用评级": "rating_raw"})

def parse_rating(r):
    if r is None or (isinstance(r, float) and np.isnan(r)):
        return None
    s = str(r).strip()
    s = re.sub(r"sti$", "", s)
    m = re.match(r"^([ABC]{1,3})([+-]?)", s)
    if not m:
        return None
    return m.group(1) + m.group(2)

RANK = {"AAA": 1, "AA+": 2, "AA": 3, "AA-": 4, "A+": 5, "A": 6, "A-": 7,
        "BBB+": 8, "BBB": 9, "BBB-": 10, "BB+": 11, "BB": 12, "BB-": 13,
        "B+": 14, "B": 15, "B-": 16, "CCC": 17, "CC": 18, "C": 19}
meta["rating_parsed"] = meta["rating_raw"].map(parse_rating)
meta["rating_rank"] = meta["rating_parsed"].map(RANK)

BLACKLIST = ["搜特", "蓝盾", "鸿达", "正邦", "全筑", "帝欧", "岭南", "中装", "起步", "花王", "普利", "广汇"]
meta["blacklisted"] = meta["债券简称"].astype(str).apply(lambda x: any(k in x for k in BLACKLIST))

# ---------- 2. 月末快照(不带 gap 过滤) ----------
panel = panel.sort_values(["code", "date"])
panel["ym"] = panel["date"].dt.to_period("M")
me = panel.groupby(["code", "ym"]).tail(1).copy()
me = me.merge(meta, on="code", how="left")
me["mdate"] = me["ym"].dt.to_timestamp(how="end").dt.normalize()

# 动量: 20交易日 (daily, per bond)
mom = []
for c, g in panel.drop_duplicates(["code", "date"]).groupby("code"):
    g = g.sort_values("date").set_index("date")["close"]
    s = (g / g.shift(20) - 1).rename("mom")
    mom.append(pd.DataFrame({"code": c, "date": s.index, "mom": s.values}))
momdf = pd.concat(mom, ignore_index=True)
me = me.merge(momdf, on=["code", "date"], how="left")

maxdt = panel.groupby("code")["date"].max().rename("max_date")
me = me.merge(maxdt, on="code", how="left")

# ---------- 3. 过滤链 (R-285 §2.1 顺序固定) ----------
def filter_universe(me, use_blacklist=True):
    f = me.copy()
    f = f[f["list_dt"].notna() & (f["list_dt"] <= f["mdate"] - pd.Timedelta(days=25))]
    f = f[f["rating_rank"].notna() & (f["rating_rank"] <= 4)]
    if use_blacklist:
        f = f[~f["blacklisted"]]
    f = f[f["issue_sz"].notna() & (f["issue_sz"] >= 2.0)]
    f = f[f["close"].notna()]
    return f

# ---------- 4. 因子得分 ----------
def compute_scores(f):
    f = f.copy()
    f["P"] = 1.0 - f["close"].rank(method="average", pct=True)  # 价格越低分越高
    f["D"] = (-(f["close"] + f["prem"])).rank(method="average", pct=True)  # 双低越低分越高
    f["M"] = f["mom"].rank(method="average", pct=True)
    f[["P", "D", "M"]] = f[["P", "D", "M"]].fillna(0.5)
    f["S"] = 0.7 * f["P"] + 0.3 * f["D"] - 0.1 * f["M"]
    f["s_rank"] = f["S"].rank(method="average", ascending=False)
    return f

# ---------- 5. 回测 ----------
def run_backtest(use_blacklist=True):
    N, BUFFER, COST = 15, 25, 0.001
    form = [m for m in sorted(me["ym"].unique())
            if pd.Period("2018-01", "M") <= m <= pd.Period("2026-06", "M")]  # 103 建仓月
    ret_months = [m for m in sorted(me["ym"].unique())
                  if pd.Period("2018-02", "M") <= m <= pd.Period("2026-07", "M")]  # 102 收益月

    close_pivot = me.pivot_table(index="ym", columns="code", values="close")
    close_pivot = close_pivot.reindex(sorted(close_pivot.index)).ffill()

    holdings = {}          # code -> weight(1/15)
    nav = 1.0
    nav_pts = []           # (ym, nav) ym=建仓月末
    ret_pts = []           # (ym, ret) ym=收益月
    trades = []            # {ym, code, action, price}
    skip_events = []

    for idx, m in enumerate(form):
        # --- 当月收益: 用 m-1 月末建仓的 holdings, 观察 m 月末收盘 ---
        if idx == 0:
            ret_m = 0.0
        else:
            prev_m = form[idx - 1]
            ret_m = 0.0
            for code, w in holdings.items():
                if code not in close_pivot.columns:
                    continue
                p_prev = close_pivot.loc[prev_m, code] if prev_m in close_pivot.index else np.nan
                p_now = close_pivot.loc[m, code] if m in close_pivot.index else np.nan
                if pd.notna(p_prev) and pd.notna(p_now) and p_prev > 0:
                    ret_m += w * (p_now / p_prev - 1)
        nav *= (1 + ret_m)
        ret_pts.append({"ym": str(m), "ret": ret_m})

        # --- 月末调仓(信号=月末快照, 成交=同收盘价近似) ---
        f = filter_universe(me[me["ym"] == m], use_blacklist)
        mdate_now = me[me["ym"] == m]["mdate"].iloc[0] if len(me[me["ym"] == m]) else None
        if len(f) < 30:
            skip_events.append({"ym": str(m), "n_candidates": int(len(f))})
            cost_frac = 0.0
            sold = bought = 0
        else:
            f = compute_scores(f)
            cand_ranks = dict(zip(f["code"], f["s_rank"]))
            new_hold, sold = {}, 0
            for code, w in holdings.items():
                md = maxdt.get(code, None)
                delisted = pd.notna(md) and mdate_now is not None and md < mdate_now
                if delisted:
                    sold += 1
                    trades.append({"ym": str(m), "code": code, "action": "delist_sell",
                                   "price": float(close_pivot.loc[m, code]) if m in close_pivot.index and code in close_pivot.columns else None})
                    continue
                if code in cand_ranks and cand_ranks[code] <= BUFFER:
                    new_hold[code] = 1.0 / N
                elif code not in cand_ranks:
                    new_hold[code] = 1.0 / N  # 停牌无观测 -> 按最后收盘持有
                else:
                    sold += 1
                    trades.append({"ym": str(m), "code": code, "action": "sell",
                                   "price": float(close_pivot.loc[m, code]) if m in close_pivot.index else None})
            need = N - len(new_hold)
            bought = 0
            if need > 0:
                fill = f[~f["code"].isin(new_hold.keys())].sort_values("S", ascending=False).head(need)
                for code in fill["code"]:
                    new_hold[code] = 1.0 / N
                    bought += 1
                    trades.append({"ym": str(m), "code": code, "action": "buy",
                                   "price": float(close_pivot.loc[m, code]) if m in close_pivot.index else None})
            holdings = {c: 1.0 / N for c in new_hold}
            cost_frac = COST * (sold + bought) / N if new_hold else 0.0
        nav *= (1 - cost_frac)
        nav_pts.append({"ym": str(m), "nav": nav, "n_held": len(holdings),
                        "n_sold": sold, "n_bought": bought, "n_cand": int(len(f)),
                        "turnover": (sold + bought) / 2.0 / N if idx > 0 else bought / N,
                        "cost_frac": cost_frac})

    # --- 最后一个月收益: 2026-07 (用 2026-06 建仓的 holdings) ---
    last_m = form[-1]
    ret_last = 0.0
    for code, w in holdings.items():
        if code not in close_pivot.columns:
            continue
        p_prev = close_pivot.loc[last_m, code] if last_m in close_pivot.index else np.nan
        p_now = close_pivot.loc[pd.Period("2026-07", "M"), code] if pd.Period("2026-07", "M") in close_pivot.index else np.nan
        if pd.notna(p_prev) and pd.notna(p_now) and p_prev > 0:
            ret_last += w * (p_now / p_prev - 1)
    nav *= (1 + ret_last)
    ret_pts.append({"ym": "2026-07", "ret": ret_last})
    nav_pts.append({"ym": "2026-07", "nav": nav, "n_held": len(holdings), "n_sold": 0,
                    "n_bought": 0, "n_cand": 0, "turnover": 0.0, "cost_frac": 0.0})

    navdf = pd.DataFrame(nav_pts)
    retdf = pd.DataFrame(ret_pts)
    return navdf, retdf, trades, skip_events

def ann_from_monthly(ret_series):
    if len(ret_series) == 0:
        return np.nan
    return ((1 + ret_series).prod()) ** (12.0 / len(ret_series)) - 1

def mdd_from_nav(nav_series):
    return (nav_series / nav_series.cummax() - 1).min()

# ---------- 6. 基准 000832 ----------
bch = pd.read_parquet("/tmp/r281/csi_cb_index.parquet")
bch = bch.rename(columns={"日期": "date", "收盘": "close"})
bch["date"] = pd.to_datetime(bch["date"])
bch = bch.drop_duplicates("date").sort_values("date")
bch["ym"] = bch["date"].dt.to_period("M")
bch_me = bch.groupby("ym").tail(1).set_index("ym")["close"]
bch_me = bch_me.reindex(sorted(bch_me.index)).ffill()
bch_mret = bch_me.pct_change().fillna(0.0)

# ---------- 7. V1 主试验 ----------
navdf, retdf, trades, skips = run_backtest(use_blacklist=True)
navdf.to_csv(f"{OUT}/e2_nav_monthly.csv", index=False)
retdf.to_csv(f"{OUT}/e2_ret_monthly.csv", index=False)
with open(f"{OUT}/e2_trades.jsonl", "w") as fh:
    for t in trades:
        fh.write(json.dumps(t, ensure_ascii=False) + "\n")
with open(f"{OUT}/e2_skip_events.json", "w") as fh:
    json.dump(skips, fh, ensure_ascii=False, indent=1)

main = retdf[(retdf["ym"] >= "2018-02") & (retdf["ym"] <= "2026-07")]
pre = retdf[(retdf["ym"] >= "2018-02") & (retdf["ym"] <= "2022-07")]
post = retdf[(retdf["ym"] >= "2022-08") & (retdf["ym"] <= "2026-07")]
mnav = navdf[(navdf["ym"] >= "2018-02") & (navdf["ym"] <= "2026-07")]

mids = [pd.Period(x, "M") for x in main["ym"]]
bmain = bch_mret.loc[mids]
bpre = bch_mret.loc[[pd.Period(x, "M") for x in pre["ym"]]]
bpost = bch_mret.loc[[pd.Period(x, "M") for x in post["ym"]]]

res = {}
res["G1"] = {"port_ann": float(ann_from_monthly(main["ret"])),
             "bench_ann": float(ann_from_monthly(bmain)),
             "excess_pp": float((ann_from_monthly(main["ret"]) - ann_from_monthly(bmain)) * 100),
             "pass": bool(ann_from_monthly(main["ret"]) - ann_from_monthly(bmain) >= 0.05)}
res["G2"] = {"mdd": float(mdd_from_nav(mnav["nav"])), "pass": bool(mdd_from_nav(mnav["nav"]) >= -0.20)}
res["G3"] = {"pre_excess_pp": float((ann_from_monthly(pre["ret"]) - ann_from_monthly(bpre)) * 100),
             "post_excess_pp": float((ann_from_monthly(post["ret"]) - ann_from_monthly(bpost)) * 100),
             "pass": bool(ann_from_monthly(pre["ret"]) - ann_from_monthly(bpre) > 0 and
                          ann_from_monthly(post["ret"]) - ann_from_monthly(bpost) > 0)}
res["G4"] = {"mean_oneway_turnover": float(navdf[(navdf["ym"] >= "2018-02") & (navdf["ym"] <= "2026-06")]["turnover"].mean()),
             "pass": bool(navdf[(navdf["ym"] >= "2018-02") & (navdf["ym"] <= "2026-06")]["turnover"].mean() <= 0.40)}
res["V1_stats"] = {"n_months": int(len(main)),
                   "cum_ret": float((1 + main["ret"]).prod() - 1),
                   "ann": float(ann_from_monthly(main["ret"])),
                   "mdd": float(mdd_from_nav(mnav["nav"])),
                   "win_rate": float((main["ret"] > 0).mean()),
                   "mean_turnover": float(navdf[(navdf["ym"] >= "2018-02") & (navdf["ym"] <= "2026-06")]["turnover"].mean()),
                   "pre_n": int(len(pre)), "post_n": int(len(post)),
                   "pre_ann": float(ann_from_monthly(pre["ret"])), "post_ann": float(ann_from_monthly(post["ret"]))}
res["bench"] = {"main_ann": float(ann_from_monthly(bmain)), "pre_ann": float(ann_from_monthly(bpre)),
                "post_ann": float(ann_from_monthly(bpost)),
                "main_cum": float((1 + bmain).prod() - 1)}
print("V1:", json.dumps(res, ensure_ascii=False))

# ---------- 8. V2 敏感性(无黑名单) ----------
navdf2, retdf2, trades2, skips2 = run_backtest(use_blacklist=False)
main2 = retdf2[(retdf2["ym"] >= "2018-02") & (retdf2["ym"] <= "2026-07")]
mnav2 = navdf2[(navdf2["ym"] >= "2018-02") & (navdf2["ym"] <= "2026-07")]
res["V2"] = {"ann": float(ann_from_monthly(main2["ret"])),
             "excess_pp": float((ann_from_monthly(main2["ret"]) - ann_from_monthly(bmain)) * 100),
             "mdd": float(mdd_from_nav(mnav2["nav"])),
             "turnover": float(navdf2[(navdf2["ym"] >= "2018-02") & (navdf2["ym"] <= "2026-06")]["turnover"].mean()),
             "cum_ret": float((1 + main2["ret"]).prod() - 1)}
print("V2:", json.dumps(res["V2"], ensure_ascii=False))

# ---------- 9. IC 衰减监控 (信用过滤后 universe, E1 口径 gap=1) ----------
me_ic = filter_universe(me, use_blacklist=True).sort_values(["code", "ym"]).copy()
mi = (me_ic["ym"].dt.year * 12 + me_ic["ym"].dt.month).astype(float)
same_next = me_ic["code"] == me_ic["code"].shift(-1)
me_ic["fwd_close"] = me_ic["close"].shift(-1).where(same_next)
me_ic["fwd_ret"] = me_ic["fwd_close"] / me_ic["close"] - 1
me_ic["mi_next"] = mi.shift(-1).where(same_next)
me_ic = me_ic[(me_ic["mi_next"] - mi) == 1]
me_ic["f_dual_low"] = -(me_ic["close"] + me_ic["prem"])
me_ic["f_price"] = -me_ic["close"]

def ic_series(df, col):
    out = []
    for ym, g in df.dropna(subset=[col, "fwd_ret"]).groupby("ym"):
        if len(g) < 30:
            continue
        r = g[col].rank().corr(g["fwd_ret"].rank())
        out.append((str(ym), len(g), r))
    return pd.DataFrame(out, columns=["ym", "n", "ic"]).set_index("ym")

ic_dual = ic_series(me_ic, "f_dual_low")
ic_price = ic_series(me_ic, "f_price")
ic_out = ic_dual[['ic']].rename(columns={"ic": "ic_dual_low"}).join(ic_price[['ic']].rename(columns={"ic": "ic_price"}))
ic_out.to_csv(f"{OUT}/e2_ic_filtered_universe.csv")

def roll6_check(s):
    s = s[s.index <= "2026-07"]
    if len(s) < 6:
        return {"triggered": False, "note": "insufficient_data"}
    last6 = s.iloc[-6:]
    return {"triggered": bool((last6 < 0).all()),
            "last6_ic": [round(float(x), 4) for x in last6],
            "last6_months": [str(x) for x in last6.index]}

res["ic_monitor"] = {
    "dual_low": roll6_check(ic_dual["ic"]),
    "price_only": roll6_check(ic_price["ic"]),
    "dual_low_full_mean": float(ic_dual["ic"].mean()) if len(ic_dual) else None,
    "price_full_mean": float(ic_price["ic"].mean()) if len(ic_price) else None,
    "n_months": int(len(ic_dual)),
}
print("IC:", json.dumps(res["ic_monitor"], ensure_ascii=False))

with open(f"{OUT}/e2_gates_result.json", "w") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("DONE")
