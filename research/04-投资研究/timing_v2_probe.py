#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
task-0361 [T1-E1] 择时v2信号画像第一批：SPREAD / 回流广度REB / FLOW / 超跌包
纯分析画像：参数冻结（华福原参 + R-230 固定参数），无遍历、无策略回测。
只读生产数据；全部产物落 results/timing_v2/；n_trials=3（SPREAD w∈{5,10,20}）。

口径：
- SPREAD_w = MA_w(全市场上涨家数占比)，底表=results/breadth.parquet（任务书指定）
- M_t 全池等权指数 = data/all_stocks_merged.parquet（q4b/A9 池，5,447只）流式复算，
  与 a9_common.build_timing 的 ew_idx 同构（mean(全池ret)→cumprod）
- 微盘池 = 每日按总市值(close×outstanding_share)排序后20%（collect_crowding.py 口径，qfq 池）
- REB = 池内 (vol/vol_MA5>1.2 & vol>0 & ret>0) / 池内有效成员(ret非缺 & vol_MA5有效 & vol>0)
- FLOW = (Σ上涨amt − Σ下跌amt)/Σamt，池内 amt>0
- 超跌包(载体M)：dd60/dev15/RSI14(Wilder)/B1复合/dd250危机通道
"""
import os, sys, json, time
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HP = "/home/noname/quant-evolve"
OUT = os.path.join(HP, "results", "timing_v2")
os.makedirs(OUT, exist_ok=True)
LOG = lambda msg: print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
EPOCH = np.datetime64("1970-01-01", "D")

# ---------------- Part A: M_t 全池等权指数（流式读 merged） ----------------
LOG("Part A: 流式读 all_stocks_merged.parquet ...")
t0 = time.time()
pf = pq.ParquetFile(os.path.join(HP, "data", "all_stocks_merged.parquet"))
day_list, ret_list, up_list = [], [], []
prev_code, prev_close = None, np.nan
for rg in range(pf.num_row_groups):
    tb = pf.read_row_group(rg, columns=["date", "code", "close"]).to_pandas()
    d64 = pd.to_datetime(tb["date"]).values.astype("datetime64[D]")
    days = (d64 - EPOCH).astype(np.int32)
    code = tb["code"].values
    close = tb["close"].values.astype(np.float64)
    same = np.empty(len(tb), dtype=bool)
    same[0] = (code[0] == prev_code) if rg > 0 else False
    same[1:] = code[1:] == code[:-1]
    prev = np.empty(len(tb), dtype=np.float64)
    prev[0] = prev_close if same[0] else np.nan
    prev[1:] = np.where(same[1:], close[:-1], np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        ret = np.where(same & (prev > 0) & (close > 0), close / prev - 1.0, np.nan)
    valid = np.isfinite(ret)
    day_list.append(days[valid]); ret_list.append(ret[valid].astype(np.float32))
    up_list.append((ret[valid] > 0).astype(np.int8))
    prev_code, prev_close = code[-1], close[-1]
    del tb, d64, days, code, close, same, prev, ret

daysA = np.concatenate(day_list); retsA = np.concatenate(ret_list); upsA = np.concatenate(up_list)
del day_list, ret_list, up_list
day_codesA = np.unique(daysA)
n_dayA = len(day_codesA)
invA = np.searchsorted(day_codesA, daysA)
sum_ret = np.bincount(invA, weights=retsA, minlength=n_dayA)
cnt_ret = np.bincount(invA, minlength=n_dayA).astype(np.float64)
up_shareA = np.bincount(invA, weights=upsA, minlength=n_dayA) / cnt_ret
ew_ret = np.where(cnt_ret > 0, sum_ret / np.maximum(cnt_ret, 1), 0.0)
M = np.cumprod(1.0 + ew_ret)
datesA = pd.DatetimeIndex(pd.to_datetime(day_codesA.astype(np.int64), unit="D"))
sM = pd.Series(M, index=datesA, name="M")
s_upshare = pd.Series(up_shareA, index=datesA, name="up_share_merged")
LOG(f"Part A done: {n_dayA} 天 {time.time()-t0:.0f}s | M {datesA[0].date()}~{datesA[-1].date()} 共{len(datesA)}日, 总收益 {M[-1]/M[0]-1:+.1%}")

# ---------------- Part B: 微盘池 + REB + FLOW（单遍逐文件流式） ----------------
LOG("Part B: 逐文件读 qfq 池（单遍, 含 vma_valid 标志）...")
t0 = time.time()
QFQ = os.path.join(HP, "data", "all_stocks_qfq")
files = sorted(f for f in os.listdir(QFQ) if f.endswith("_daily_qfq.parquet"))
day_list, ret_list, amt_list, mcap_list = [], [], [], []
up_list, dn_list, vr_list, vma_list, rvalid_list = [], [], [], [], []
n_read = n_skip = n_rows = 0
for fn in files:
    try:
        df = pd.read_parquet(os.path.join(QFQ, fn),
                             columns=["date", "close", "volume", "amount", "outstanding_share"])
    except Exception:
        n_skip += 1; continue
    if df is None or len(df) < 5:
        n_skip += 1; continue
    df = df.sort_values("date").drop_duplicates("date")
    close = df["close"].astype(float)
    vol = df["volume"].astype(float)
    mcap = close * df["outstanding_share"].astype(float)
    ret = close.pct_change()
    vol_ma5 = vol.rolling(5).mean()
    v = np.isfinite(close.values) & (close.values > 0) & np.isfinite(mcap.values) & (mcap.values > 0) \
        & np.isfinite(df["amount"].values) & (df["amount"].values >= 0)
    if not v.any():
        n_skip += 1; continue
    d64 = pd.to_datetime(df["date"]).values.astype("datetime64[D]")
    daysX = (d64 - EPOCH).astype(np.int32)[v]
    r = ret.values[v]
    rv = np.isfinite(r)
    rz = np.where(rv, r, 0.0)
    volv = vol.values[v]
    vma = vol_ma5.values[v]
    vma_ok = (np.isfinite(vma) & (vma > 0) & (volv > 0) & np.isfinite(volv))
    day_list.append(daysX)
    ret_list.append(rz.astype(np.float32))
    rvalid_list.append(rv.astype(np.int8))
    up_list.append(((rz > 0) & (volv > 0)).astype(np.int8))
    dn_list.append(((rz < 0)).astype(np.int8))
    vr_list.append((vma_ok & (volv > 1.2 * np.where(np.isfinite(vma), vma, np.nan))).astype(np.int8))
    vma_list.append(vma_ok.astype(np.int8))
    amt_list.append(df["amount"].values[v].astype(np.float32))
    mcap_list.append(mcap.values[v].astype(np.float32))
    n_read += 1; n_rows += int(v.sum())
    if n_read % 1000 == 0:
        LOG(f"  已读 {n_read}/{len(files)} 文件, 行数 {n_rows:,}")

daysB = np.concatenate(day_list); retsB = np.concatenate(ret_list)
upsB = np.concatenate(up_list); dnsB = np.concatenate(dn_list)
vrsB = np.concatenate(vr_list); vmasB = np.concatenate(vma_list)
rvsB = np.concatenate(rvalid_list)
amtsB = np.concatenate(amt_list); mcapsB = np.concatenate(mcap_list)
del day_list, ret_list, up_list, dn_list, vr_list, vma_list, rvalid_list, amt_list, mcap_list
LOG(f"  文件完成: {n_read} 有效/{n_skip} 跳过, 行数 {n_rows:,}, {time.time()-t0:.0f}s")

LOG("  微盘池 lexsort(mcap, day) ...")
order = np.lexsort((mcapsB, daysB))
daysB, retsB, upsB, dnsB, vrsB, vmasB, rvsB, amtsB, mcapsB = (
    daysB[order], retsB[order], upsB[order], dnsB[order], vrsB[order],
    vmasB[order], rvsB[order], amtsB[order], mcapsB[order])
del order
day_codesB, day_start, day_count = np.unique(daysB, return_index=True, return_counts=True)
grp_idx = np.searchsorted(day_start, np.arange(len(daysB)), side="right") - 1
rank = np.arange(len(daysB)) - day_start[grp_idx]
n_today = day_count[grp_idx]
micro = (rank < (n_today * 0.20).astype(np.int64)).astype(np.int8)
del rank, n_today, grp_idx
n_dayB = len(day_codesB)
datesB = pd.DatetimeIndex(pd.to_datetime(day_codesB.astype(np.int64), unit="D"))
LOG(f"  微盘池: {n_dayB} 天, 池内行数 {int(micro.sum()):,}")

invB = np.searchsorted(day_codesB, daysB)
microf = micro.astype(np.float64)
amt_pos = np.where(amtsB > 0, amtsB, 0.0).astype(np.float64)
num = lambda w: np.bincount(invB, weights=w, minlength=n_dayB)

micro_cnt   = num(microf)
micro_rsum  = num(retsB.astype(np.float64) * microf)
micro_rcnt  = num((microf * rvsB))
reb_num     = num(microf * vrsB * upsB)          # 放量上涨
reb_den     = num(microf * vmasB * rvsB)           # 有效成员 = vma_ok & ret_valid
flow_up     = num(microf * upsB * amt_pos)
flow_dn     = num(microf * dnsB * amt_pos)
flow_tot    = num(microf * amt_pos)
del microf, amt_pos, daysB, retsB, upsB, dnsB, vrsB, vmasB, rvsB, amtsB, mcapsB, micro, invB

REB = pd.Series(np.where(reb_den >= 5, reb_num / np.maximum(reb_den, 1), np.nan), index=datesB, name="REB")
FLOW = pd.Series(np.where(flow_tot > 0, (flow_up - flow_dn) / flow_tot, np.nan), index=datesB, name="FLOW")
micro_ew_ret = np.where(micro_rcnt > 0, micro_rsum / np.maximum(micro_rcnt, 1), 0.0)
Mmicro = pd.Series(np.cumprod(1.0 + micro_ew_ret), index=datesB, name="M_micro_ew")
LOG(f"Part B done: REB 有效 {REB.notna().sum()} 天, FLOW 有效 {FLOW.notna().sum()} 天, {time.time()-t0:.0f}s")

# ---------------- Part C: 信号、episode、统计 ----------------
LOG("Part C: 信号构建与画像 ...")
br = pd.read_parquet(os.path.join(HP, "results", "breadth.parquet"))["breadth"]
br.index = pd.to_datetime(br.index)
xc = pd.concat([br.rename("breadth"), s_upshare], axis=1).dropna()
LOG(f"  交叉验证 up_share(merged复算) vs breadth.parquet: n={len(xc)}, mean|diff|={(xc.breadth-xc.up_share_merged).abs().mean():.6f}, corr={xc.corr().iloc[0,1]:.4f}")

master = datesA
df = pd.DataFrame(index=master)
df["M"] = sM
df["M_micro_ew"] = Mmicro.reindex(master)
df["breadth"] = br.reindex(master)

sig_defs = {}
for w in (5, 10, 20):
    sp = br.rolling(w).mean()
    c1 = sp.rolling(20).max() >= 0.85
    c2 = (sp.shift(1).rolling(5).max() - sp) >= 0.05
    sig_defs[f"SPREAD{w}_top"] = (c1 & c2)
    df[f"SPREAD{w}"] = sp.reindex(master)
    df[f"flag_SPREAD{w}_top"] = (c1 & c2).reindex(master).fillna(False).astype(bool)

reb5 = REB - REB.shift(5)
sig_reb = (REB >= 0.55) & (reb5 >= 0.05)
df["REB"] = REB.reindex(master)
df["flag_REB_bottom"] = sig_reb.reindex(master).fillna(False).astype(bool)

fma3 = FLOW.rolling(3).mean()
sig_flow = (fma3 > 0) & (fma3.shift(1) <= 0) & fma3.shift(1).notna() & fma3.notna()
df["FLOW"] = FLOW.reindex(master)
df["FLOW_MA3"] = fma3.reindex(master)
df["flag_FLOW_pos_cross"] = sig_flow.reindex(master).fillna(False).astype(bool)

ret1 = sM.pct_change()
dd_run = sM / sM.cummax() - 1.0
dd60 = sM / sM.rolling(60).max() - 1.0
dd250 = sM / sM.rolling(250).max() - 1.0
dev15 = sM / sM.rolling(15).mean() - 1.0
diff = sM.diff()
gain = diff.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
loss = (-diff.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
rsi14 = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
df["dd60"] = dd60.reindex(master); df["dd250"] = dd250.reindex(master)
df["dev15"] = dev15.reindex(master); df["rsi14"] = rsi14.reindex(master)
df["ret1"] = ret1.reindex(master)

f_dd60 = dd60 < -0.10
f_dev = dev15 < -0.03
f_rsi = rsi14 <= 45
f_B1 = f_dd60 & f_dev & f_rsi
f_C = (dd250 < -0.35) & (ret1 > 0.05)
for nm, f in [("flag_dd60", f_dd60), ("flag_dev15", f_dev), ("flag_rsi14", f_rsi), ("flag_B1_oversold", f_B1), ("flag_C_crisis", f_C)]:
    df[nm] = f.reindex(master).fillna(False).astype(bool)

SIGNALS = ["SPREAD5_top", "SPREAD10_top", "SPREAD20_top", "REB_bottom", "FLOW_pos_cross",
           "dd60", "dev15", "rsi14", "B1_oversold", "C_crisis"]
DIRECTION = {s: ("top" if s.startswith("SPREAD") else "bottom") for s in SIGNALS}

fwd15 = (sM.shift(-15) / sM - 1.0).reindex(master)

def episodes(flag):
    v = flag.fillna(False).values
    idx = np.where(v)[0]
    if len(idx) == 0:
        return []
    brk = np.where(np.diff(idx) > 1)[0]
    starts = np.r_[idx[0], idx[brk + 1]]
    ends = np.r_[idx[brk], idx[-1]]
    return [(master[s], master[e], e - s + 1) for s, e in zip(starts, ends)]

rows, summary = [], {}
for s in SIGNALS:
    flag = df["flag_" + s]
    eps = episodes(flag)
    evs = []
    for st, en, nd in eps:
        f = fwd15.loc[st] if st in fwd15.index else np.nan
        hit = bool(f < 0) if (DIRECTION[s] == "top" and np.isfinite(f)) else (bool(f > 0) if np.isfinite(f) else False)
        evs.append((st, en, nd, f, hit))
        rows.append({"signal": s, "start": st.date().isoformat(), "end": en.date().isoformat(),
                     "n_days": nd, "fwd15": None if not np.isfinite(f) else round(float(f), 4), "hit": hit})
    fs = [f for _, _, _, f, _ in evs if np.isfinite(f)]
    summary[s] = {
        "direction": DIRECTION[s],
        "trigger_days": int(flag.sum()),
        "n_episodes": len(eps),
        "n_events_with_fwd15": len(fs),
        "win_rate": None if not fs else round(float(np.mean([h for _, _, _, f, h in evs if np.isfinite(f)])), 4),
        "fwd15_mean": None if not fs else round(float(np.mean(fs)), 4),
        "fwd15_median": None if not fs else round(float(np.median(fs)), 4),
        "fwd15_min": None if not fs else round(float(np.min(fs)), 4),
        "fwd15_max": None if not fs else round(float(np.max(fs)), 4),
        "first_episode": None if not eps else eps[0][0].date().isoformat(),
        "last_episode": None if not eps else eps[-1][1].date().isoformat(),
    }
    LOG(f"  {s}: {summary[s]['trigger_days']} 触发日 / {len(eps)} episodes / 胜率 {summary[s]['win_rate']} / fwd15均值 {summary[s]['fwd15_mean']}")

# 重合度矩阵（日级 Jaccard）
flags = {s: df["flag_" + s] for s in SIGNALS}
ov = pd.DataFrame(index=SIGNALS, columns=SIGNALS, dtype=float)
for a in SIGNALS:
    for b in SIGNALS:
        A, B = flags[a].values, flags[b].values
        inter = int((A & B).sum()); union = int((A | B).sum())
        ov.loc[a, b] = inter / union if union else 0.0

# 大回撤段覆盖检查（数据驱动）
dd_series = dd_run.reindex(master)
deep = (dd_series < -0.15).fillna(False).values
idx = np.where(deep)[0]
spans = []
if len(idx):
    brk = np.where(np.diff(idx) > 1)[0]
    st = np.r_[idx[0], idx[brk + 1]]; en = np.r_[idx[brk], idx[-1]]
    for s0, e0 in zip(st, en):
        seg = dd_series.iloc[s0:e0 + 1]
        tr_i = seg.idxmin()
        depth = float(seg.min())
        pk_i = master[s0 - 1] if s0 > 0 else master[0]
        spans.append({"peak": pk_i.date().isoformat(), "trough": tr_i.date().isoformat(),
                      "end": master[e0].date().isoformat(), "depth": round(depth, 4)})
spans = sorted(spans, key=lambda x: x["depth"])[:8]
pos = {d: i for i, d in enumerate(master)}
bottom_sigs = ["REB_bottom", "FLOW_pos_cross", "dd60", "dev15", "rsi14", "B1_oversold", "C_crisis"]
top_sigs = ["SPREAD5_top", "SPREAD10_top", "SPREAD20_top"]
cov = []
for sp_ in spans:
    tp = pos.get(pd.Timestamp(sp_["trough"]), None); pp = pos.get(pd.Timestamp(sp_["peak"]), None)
    row = {"drawdown": sp_, "bottom_hits": {}, "top_hits": {}}
    for s in bottom_sigs:
        eps = episodes(flags[s])
        ds = [tp - pos[e[0]] for e in eps if tp is not None and e[0] in pos and abs(tp - pos[e[0]]) <= 10]
        row["bottom_hits"][s] = len(ds)
    for s in top_sigs:
        eps = episodes(flags[s])
        ds = [pp - pos[e[0]] for e in eps if pp is not None and e[0] in pos and -15 <= pp - pos[e[0]] <= 5]
        row["top_hits"][s] = len(ds)
    cov.append(row)

# M 基础统计
yrs = (master[-1] - master[0]).days / 365.25
m_stats = {
    "n_days": len(master), "start": str(master[0].date()), "end": str(master[-1].date()),
    "total_return": round(float(M[-1] / M[0] - 1), 4),
    "ann_return": round(float((M[-1] / M[0]) ** (1 / yrs) - 1), 4),
    "MDD": round(float(dd_series.min()), 4),
}
summary_out = {
    "task": "task-0361 [T1-E1]", "date": "2026-08-18", "n_trials": 3,
    "params_frozen": "华福原参+R-230 固定参数; SPREAD w∈{5,10,20}; 顶部=rollmax20≥0.85 & 5日回落≥0.05; REB≥55% & Δ5≥5pp; B1=dd60<-10%&dev15<-3pp&RSI14≤45; C=dd250<-35%&ret>+5%",
    "M_stats": m_stats,
    "breadth_crosscheck": {"n": int(len(xc)), "mean_abs_diff": round(float((xc.breadth - xc.up_share_merged).abs().mean()), 6),
                            "corr": round(float(xc.corr().iloc[0, 1]), 4)},
    "signals": summary,
    "major_drawdowns": cov,
}

df.to_parquet(os.path.join(OUT, "signal_series.parquet"))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "episodes_all.csv"), index=False)
ov.to_csv(os.path.join(OUT, "overlap_matrix.csv"))
with open(os.path.join(OUT, "summary.json"), "w") as f:
    json.dump(summary_out, f, ensure_ascii=False, indent=1, default=str)
LOG("DONE: 产物已写 results/timing_v2/{signal_series.parquet, episodes_all.csv, overlap_matrix.csv, summary.json}")
