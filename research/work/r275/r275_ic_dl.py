#!/usr/bin/env python3
# r275_ic.py — Sloan 应计因子 IC 验证 + A股口径现金流广度复算 [task-0442/R-275 阶段B]
# 零回测: 因子构建 + IC 画像 + 代理相关性。口径对齐 W1: 月频全市场 spearman, MAD3去极值+zscore
import os, glob, json, time, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

W = "/root/.openclaw/workspace/shared/results/work/r275"
LOG = open(f"{W}/ic.log", "a", buffering=1)
def log(m): LOG.write(f"[{time.strftime('%H:%M:%S')}] {m}\n")
t0 = time.time()

A_PREFIX = ("000", "001", "002", "003", "300", "301", "302", "600", "601", "603", "605", "688", "689")
def is_a(c): return len(c) == 6 and c[:3] in A_PREFIX
log("=== r275_ic deadline-PIT start ===")

# ---- Phase A: 装载财务 chunks ----
def load(tname, cols):
    frames = []
    for f in sorted(glob.glob(f"{W}/chunks/{tname}_*.parquet")):
        p = f.split("_")[-1].split(".")[0]
        d = pd.read_parquet(f)
        if len(d) == 0: continue
        d["statDate"] = p
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df = df[df["code"].map(is_a)].copy()   # A 股过滤 (数据债修正口径)
    for c in cols:
        if c not in ("code", "pubDate", "statDate"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["pubDate"] = pd.to_datetime(df["pubDate"], errors="coerce")
    return df.drop_duplicates(["code", "statDate"])

yj = load("yjbb", ["net_profit", "roe", "gp_margin", "revenue_yoy", "net_profit_yoy"])
zc = load("zcfz", ["total_asset"])
xj = load("xjll", ["ocf"])
log(f"[A] yjbb={len(yj)} zcfz={len(zc)} xjll={len(xj)} (A股口径) t={time.time()-t0:.0f}s")

# ---- Phase B: A股真宇宙三要素齐全率 (修正44.5%数据债结论) ----
per = yj[["code", "statDate", "net_profit"]].merge(zc[["code", "statDate", "total_asset"]], on=["code", "statDate"], how="left")
per = per.merge(xj[["code", "statDate", "ocf"]], on=["code", "statDate"], how="left")
per["ok3"] = per["net_profit"].notna() & per["total_asset"].notna() & per["ocf"].notna()
per["year"] = per["statDate"].str[:4]
g = per.groupby("year").agg(n=("code", "size"), ok=("ok3", "sum"))
g["rate"] = g["ok"] / g["n"]
g.to_csv(f"{W}/breadth_a_share.csv")
# 全史 & 近3年
all_rate = per["ok3"].mean()
recent = per[per["year"].astype(int) >= 2023]["ok3"].mean()
xjll_only_recent = per[per["year"].astype(int) >= 2023]["ocf"].notna().mean()
log(f"[B] A股三要素齐全率 全史={all_rate:.3f} 近3年={recent:.3f}; xjll覆盖(近3年)={xjll_only_recent:.3f}")

# ---- Phase C: Sloan 应计 TTM (向量化) ----
q = yj[["code", "statDate", "net_profit", "pubDate"]].copy()
q = q.merge(xj[["code", "statDate", "ocf"]], on=["code", "statDate"], how="inner")
q = q.merge(zc[["code", "statDate", "total_asset"]], on=["code", "statDate"], how="inner")
q = q.dropna(subset=["net_profit", "ocf", "total_asset"])
q["dt"] = pd.to_datetime(q["statDate"], format="%Y%m%d")
q = q.sort_values(["code", "dt"]).reset_index(drop=True)
# TTM: 4 个连续季度 (t-3→t 跨度 273~275 天, 宽容至 270~278)
grp = q.groupby("code", sort=False)
q["np4"] = grp["net_profit"].rolling(4).sum().reset_index(0, drop=True)
q["ocf4"] = grp["ocf"].rolling(4).sum().reset_index(0, drop=True)
q["ta0"] = grp["total_asset"].shift(0)
q["d0"] = grp["dt"].shift(3)
q["span_ok"] = (q["dt"] - q["d0"]).dt.days.between(270, 278)
q["nrows"] = grp.cumcount() + 1
acc = q[(q["span_ok"]) & (q["nrows"] >= 5) & (q["ta0"] > 0)].copy()
acc["accrual"] = (acc["np4"] - acc["ocf4"]) / acc["ta0"]
acc = acc.dropna(subset=["accrual"])
# PIT: usable_from = max(法披期限, pubDate) + 1
def deadline(sd):
    y, md = int(sd[:4]), sd[4:]
    if md == "0331": return pd.Timestamp(y, 4, 30)
    if md == "0630": return pd.Timestamp(y, 8, 31)
    if md == "0930": return pd.Timestamp(y, 10, 31)
    return pd.Timestamp(y + 1, 4, 30)
acc["dl"] = acc["statDate"].map(deadline)
acc["pub"] = acc["pubDate"].fillna(acc["dl"])
acc["usable"] = acc["dl"] + pd.Timedelta(days=1)  # deadline-PIT: 免 EM 回填污染
log(f"[C] Sloan TTM 观测 {len(acc)} 条, {acc['dt'].min().date()}~{acc['dt'].max().date()} t={time.time()-t0:.0f}s")
first_usable = acc.groupby(acc["usable"].dt.year).size()
log(f"[C] usable_from 首年分布: {first_usable.head(3).to_dict()}")

# ---- Phase D: 价格矩阵 + month_end ----
QFQ = "/root/sr365/qfq"
files = sorted(f for f in os.listdir(QFQ) if f.endswith("_daily_qfq.parquet"))
ccls, codes = [], []
for fn in files:
    c = fn.replace("_daily_qfq.parquet", "")
    if not is_a(c): continue
    d = pd.read_parquet(os.path.join(QFQ, fn), columns=["date", "close"])
    d = d.dropna().sort_values("date").drop_duplicates("date").set_index("date")
    ccls.append(d["close"].rename(c)); codes.append(c)
close = pd.concat(ccls, axis=1).sort_index()
del ccls
cal = close.index
me = pd.Series(cal, index=cal).groupby(cal.to_period("M")).max()
me_dates = pd.DatetimeIndex(me.values)
log(f"[D] close {close.shape[0]}d x {close.shape[1]}codes, {cal[0].date()}~{cal[-1].date()}; months={len(me_dates)} t={time.time()-t0:.0f}s")

nlist = (~close.isna()).cumsum()          # 上市累计交易日
# 月收益 = close[m+1]/close[m]-1
cl_me = close.reindex(me_dates)
ret_fwd = cl_me.shift(-1) / cl_me - 1
listed_me = nlist.reindex(me_dates)

# ---- Phase E: 因子月度化 (asof) + IC ----
acc_codes = acc["code"].unique()
len(acc_codes)
ic_rows, corr_rows = [], []
proxies = {}
for pcol in ["roe", "gp_margin", "revenue_yoy", "net_profit_yoy"]:
    pq = yj[["code", "statDate", pcol, "pubDate"]].dropna(subset=[pcol]).copy()
    pq["dt"] = pd.to_datetime(pq["statDate"], format="%Y%m%d")
    pq["dl"] = pq["statDate"].map(deadline)
    pq["pub"] = pq["pubDate"].fillna(pq["dl"])
    pq["usable"] = pq["dl"] + pd.Timedelta(days=1)  # deadline-PIT
    pq = pq.sort_values("usable")
    proxies[pcol] = pq

me_ns = me_dates
for k, m_end in enumerate(me_dates):
    if m_end <= pd.Timestamp("2006-06-30"): continue
    if k + 1 >= len(me_dates): break
    # accrual 因子: PIT 可用行中取报告期最新 (statDate 优先, 防 EM 回填老期 pubDate 挤出新报告)
    a = acc[acc["usable"] <= m_end]
    a = a.sort_values(["statDate", "usable"]).groupby("code").tail(1)
    a = a[(m_end - a["dt"]).dt.days <= 400]
    a = a.set_index("code")["accrual"]
    # 去极值 MAD3 + zscore
    a = a[(a - a.median()).abs() <= 3 * (a - a.median()).abs().median()] if len(a) > 50 else a
    if len(a) < 200: continue
    az = (a - a.mean()) / a.std()
    r1 = ret_fwd.loc[m_end]; lst = listed_me.loc[m_end]
    common = az.index.intersection(r1.dropna().index)
    common = [c for c in common if lst.get(c, 0) >= 120]
    if len(common) < 200: continue
    f = az[common]; rr = r1[common]
    # spearman = pearson on ranks (scipy 不可用, 用 pandas rank 等价实现)
    ic = pd.Series(f).rank().corr(pd.Series(rr).rank())
    # 分组 (quintile of -accrual = 质量)
    quints = pd.qcut(-f, 5, labels=False, duplicates="drop")
    gret = pd.Series(rr.values).groupby(quints.values).mean()
    # 代理相关性 (同月 spearman)
    crow = {"ym": str(m_end)[:7]}
    for pcol, pq in proxies.items():
        p = pq[pq["usable"] <= m_end]
        p = p.sort_values(["dt", "usable"]).groupby("code").tail(1)
        p = p[(m_end - p["dt"]).dt.days <= 400].set_index("code")[pcol]
        pc = p.index.intersection(f.index)
        if len(pc) >= 200:
            crow[pcol] = round(pd.Series(f[pc]).rank().corr(pd.Series(p[pc]).rank()), 4)
    ic_rows.append({"ym": str(m_end)[:7], "ic_accrual": round(ic, 4), "n": len(common),
                    **{f"q{i+1}": round(gret.get(i, np.nan), 5) for i in range(5)}})
    corr_rows.append(crow)
ic_df = pd.DataFrame(ic_rows)
ic_df.to_csv(f"{W}/ic_monthly.csv", index=False)
cr_df = pd.DataFrame(corr_rows)
cr_df.to_csv(f"{W}/corr_proxies.csv", index=False)

# ---- Phase F: 汇总 ----
ic = ic_df["ic_accrual"]
pos = -ic  # 质量方向 (-accrual)
summary = {
    "n_months": int(len(ic_df)),
    "period": [ic_df["ym"].iloc[0], ic_df["ym"].iloc[-1]],
    "ic_mean": round(ic.mean(), 4), "ic_std": round(ic.std(), 4),
    "icir": round(ic.mean() / ic.std(), 4),
    "t_stat": round(ic.mean() / ic.std() * np.sqrt(len(ic)), 3),
    "ic_pos_rate": round((ic > 0).mean(), 4),
    "quality_ic_mean": round(pos.mean(), 4), "quality_icir": round(-ic.mean() / ic.std(), 4),
    "avg_n": int(ic_df["n"].mean()),
    "q_monotonic": bool(np.all(np.diff([ic_df[f"q{i}"].mean() for i in range(1, 6)]) > 0) or
                        np.all(np.diff([ic_df[f"q{i}"].mean() for i in range(1, 6)]) < 0)),
    "q_means": [round(ic_df[f"q{i}"].mean(), 5) for i in range(1, 6)],
    "corr_proxies_avg": {c: round(cr_df[c].abs().mean(), 4) for c in ["roe", "gp_margin", "revenue_yoy", "net_profit_yoy"] if c in cr_df},
    "breadth_a_all": round(float(all_rate), 4), "breadth_a_recent3y": round(float(recent), 4),
    "accrual_obs": int(len(acc)), "first_usable_year": int(acc["usable"].min().year),
}
# 分年 IC
ic_df["yr"] = ic_df["ym"].str[:4]
yr_ic = ic_df.groupby("yr")["ic_accrual"].agg(["mean", "count"]).round(4)
yr_ic.to_csv(f"{W}/ic_by_year.csv")
json.dump(summary, open(f"{W}/summary.json", "w"), ensure_ascii=False, indent=1)
log(f"[F] summary={json.dumps(summary, ensure_ascii=False)}")
log(f"=== done t={time.time()-t0:.0f}s ===")
print(json.dumps(summary, ensure_ascii=False))
