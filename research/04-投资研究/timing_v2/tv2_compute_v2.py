#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
task-0361 [T1-E1] 择时v2信号画像第一批：SPREAD / 回流广度REB / FLOW / 超跌包
纯分析画像：参数冻结（华福原参 + R-230 固定参数），无遍历、无策略回测。n_trials=3（SPREAD w∈{5,10,20}）。

执行说明（重要偏离，已记 notes）：
- HP 内存耗尽（MemAvailable 57MB, swap 满, 106 个 idle openclaw-node 进程占 14.7GB，
  按纪律一律勿杀）→ 计算移至 VPS：数据 rsync 自 HP 只读副本（qfq 池 1.1G + merged 290M + breadth），
  产物回写 HP results/timing_v2/。口径不变：
  - merged = q4b/A9 池（5,447 只含退市 241）→ M_t 全池等权（build_timing ew_idx 同构）
  - qfq 池 = collect_crowding 微盘定义底表（close×outstanding_share 每日后 20%）
- 内存安全：Part A 按 row group 流式 + 日桶增量聚合；Part B 按日期分块（5 块，块前扩 20 天
  保证 rolling5/pct_change 上下文），块内 numpy lexsort，峰值 ~350MB。

口径：
- SPREAD_w = MA_w(breadth.parquet 上涨家数占比)（任务书指定底表）
- REB = 池内(vol/vol_MA5>1.2 & vol>0 & ret>0) / 池内有效成员(ret非缺 & vol_MA5有效 & vol>0)
- FLOW = (Σ上涨amt−Σ下跌amt)/Σamt（池内 amt>0）
- 超跌包(载体M)：dd60 / dev15 / RSI14(Wilder) / B1=三者同时 / C=dd250<−35%&日收益>+5%
- 顶部 SPREAD_top_w = rollmax20(SPREAD_w)≥0.85 且 (max(SPREAD_w,t−5..t−1)−SPREAD_w)≥0.05
- REB_bottom = REB≥0.55 且 REB−REB.shift(5)≥0.05；FLOW_pos_cross = FLOW_MA3 上穿 0
- episode=连续触发日段，事件日=段首；fwd15=M.shift(−15)/M−1；底向 hit=fwd15>0，顶向 hit=fwd15<0
"""
import os, sys, json, time
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

DATA = sys.argv[1] if len(sys.argv) > 1 else "/root/tv2data"
OUT = os.path.join(DATA, "out")
os.makedirs(OUT, exist_ok=True)
LOG = lambda msg: print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
EPOCH = np.datetime64("1970-01-01", "D")

# ---------------- Part A: M_t 全池等权指数（merged 流式 + 日桶增量） ----------------
LOG("Part A: 流式读 all_stocks_merged.parquet ...")
t0 = time.time()
pf = pq.ParquetFile(os.path.join(DATA, "all_stocks_merged.parquet"))
bin_days, bin_sum, bin_cnt, bin_up = [], [], [], []
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
    dv, rv, uv = days[valid], ret[valid].astype(np.float32), (ret[valid] > 0).astype(np.int8)
    udays, inv = np.unique(dv, return_inverse=True)
    bin_days.append(udays)
    bin_sum.append(np.bincount(inv, weights=rv, minlength=len(udays)))
    bin_cnt.append(np.bincount(inv, minlength=len(udays)).astype(np.float64))
    bin_up.append(np.bincount(inv, weights=uv, minlength=len(udays)))
    prev_code, prev_close = code[-1], close[-1]
    del tb, d64, days, code, close, same, prev, ret, valid, dv, rv, uv
    LOG(f"  row_group {rg+1}/{pf.num_row_groups} done, {time.time()-t0:.0f}s")

bd = np.concatenate(bin_days)
agg = pd.DataFrame({
    "day": bd,
    "sum": np.concatenate(bin_sum),
    "cnt": np.concatenate(bin_cnt),
    "up": np.concatenate(bin_up),
}).groupby("day").sum().sort_index()
del bin_days, bin_sum, bin_cnt, bin_up, bd
datesA = pd.DatetimeIndex(pd.to_datetime(agg.index.values.astype(np.int64), unit="D"))
ew_ret = (agg["sum"] / agg["cnt"]).values
M = np.cumprod(1.0 + ew_ret)
sM = pd.Series(M, index=datesA, name="M")
s_upshare = pd.Series((agg["up"] / agg["cnt"]).values, index=datesA, name="up_share_merged")
n_dayA = len(datesA)
LOG(f"Part A done: {n_dayA} 天 {time.time()-t0:.0f}s | M {datesA[0].date()}~{datesA[-1].date()} 总收益 {M[-1]/M[0]-1:+.1%}")

# ---------------- Part B: 微盘池 + REB + FLOW（按日期分块） ----------------
LOG("Part B: qfq 池分块扫描 ...")
t0 = time.time()
QFQ = os.path.join(DATA, "all_stocks_qfq")
files = sorted(f for f in os.listdir(QFQ) if f.endswith("_daily_qfq.parquet"))
chunks = [("2005-12-01", "2009-12-31"), ("2010-01-01", "2013-12-31"),
          ("2014-01-01", "2017-12-31"), ("2018-01-01", "2021-12-31"),
          ("2022-01-01", "2026-12-31")]
res_rows = []  # day-level dicts
for ci, (lo, hi) in enumerate(chunks):
    lo_ts, hi_ts = pd.Timestamp(lo), pd.Timestamp(hi)
    ctx_lo = lo_ts - pd.Timedelta(days=30)  # 上下文窗口: rolling5/pct_change
    day_l, ret_l, up_l, dn_l, vr_l, vma_l, rv_l, amt_l, mcap_l = [], [], [], [], [], [], [], [], []
    n_read = n_rows = 0
    for fn in files:
        try:
            tbl = pq.read_table(os.path.join(QFQ, fn), columns=["date", "close", "volume", "amount", "outstanding_share"],
                                filters=[("date", ">=", ctx_lo), ("date", "<=", hi_ts)])
            df = tbl.to_pandas()
        except Exception:
            continue
        if df is None or len(df) < 2:
            continue
        df = df.sort_values("date").drop_duplicates("date")
        close = df["close"].astype(float)
        vol = df["volume"].astype(float)
        mcap = close * df["outstanding_share"].astype(float)
        ret = close.pct_change()
        vol_ma5 = vol.rolling(5).mean()
        v = np.isfinite(close.values) & (close.values > 0) & np.isfinite(mcap.values) & (mcap.values > 0) \
            & np.isfinite(df["amount"].values) & (df["amount"].values >= 0)
        dv = pd.to_datetime(df["date"]).values.astype("datetime64[D]")
        keep = v & (dv >= np.datetime64(lo, "D")) & (dv <= np.datetime64(hi, "D"))
        if not keep.any():
            continue
        d64 = dv[keep]
        daysX = (d64 - EPOCH).astype(np.int32)
        r = ret.values[keep]
        rv = np.isfinite(r)
        rz = np.where(rv, r, 0.0)
        volv = vol.values[keep]
        vma = vol_ma5.values[keep]
        vma_ok = (np.isfinite(vma) & (vma > 0) & (volv > 0) & np.isfinite(volv))
        with np.errstate(invalid="ignore"):
            vr = vma_ok & (volv > 1.2 * np.where(np.isfinite(vma), vma, np.nan))
        day_l.append(daysX)
        ret_l.append(rz.astype(np.float32))
        rv_l.append(rv.astype(np.int8))
        up_l.append(((rz > 0) & (volv > 0)).astype(np.int8))
        dn_l.append((rz < 0).astype(np.int8))
        vr_l.append(vr.astype(np.int8))
        vma_l.append(vma_ok.astype(np.int8))
        amt_l.append(df["amount"].values[keep].astype(np.float32))
        mcap_l.append(mcap.values[keep].astype(np.float32))
        n_read += 1; n_rows += int(keep.sum())
    daysC = np.concatenate(day_l); retsC = np.concatenate(ret_l)
    upsC = np.concatenate(up_l); dnsC = np.concatenate(dn_l)
    vrsC = np.concatenate(vr_l); vmasC = np.concatenate(vma_l); rvsC = np.concatenate(rv_l)
    amtsC = np.concatenate(amt_l); mcapsC = np.concatenate(mcap_l)
    del day_l, ret_l, up_l, dn_l, vr_l, vma_l, rv_l, amt_l, mcap_l
    order = np.lexsort((mcapsC, daysC))
    daysC, retsC, upsC, dnsC, vrsC, vmasC, rvsC, amtsC, mcapsC = (
        daysC[order], retsC[order], upsC[order], dnsC[order], vrsC[order],
        vmasC[order], rvsC[order], amtsC[order], mcapsC[order])
    del order
    day_codesC, day_start, day_count = np.unique(daysC, return_index=True, return_counts=True)
    grp_idx = np.searchsorted(day_start, np.arange(len(daysC)), side="right") - 1
    rank = np.arange(len(daysC)) - day_start[grp_idx]
    n_today = day_count[grp_idx]
    micro = (rank < (n_today * 0.20).astype(np.int64)).astype(np.int8)
    del rank, n_today, grp_idx
    invC = np.searchsorted(day_codesC, daysC)
    nd = len(day_codesC)
    microf = micro.astype(np.float64)
    amt_pos = np.where(amtsC > 0, amtsC, 0.0).astype(np.float64)
    num = lambda w: np.bincount(invC, weights=w, minlength=nd)
    res_rows.append(pd.DataFrame({
        "day": day_codesC.astype(np.int64),
        "micro_cnt": num(microf),
        "micro_rsum": num(retsC.astype(np.float64) * microf),
        "micro_rcnt": num(microf * rvsC),
        "reb_num": num(microf * vrsC * upsC),
        "reb_den": num(microf * vmasC * rvsC),
        "flow_up": num(microf * upsC * amt_pos),
        "flow_dn": num(microf * dnsC * amt_pos),
        "flow_tot": num(microf * amt_pos),
    }))
    LOG(f"  chunk {ci+1}/5 [{lo}~{hi}]: 文件 {n_read}, 行 {n_rows:,}, 池内行 {int(micro.sum()):,}, {time.time()-t0:.0f}s")
    del daysC, retsC, upsC, dnsC, vrsC, vmasC, rvsC, amtsC, mcapsC, micro, invC, microf, amt_pos

bagg = pd.concat(res_rows).groupby("day").sum().sort_index()
del res_rows
datesB = pd.DatetimeIndex(pd.to_datetime(bagg.index.values, unit="D"))
REB = pd.Series(np.where(bagg["reb_den"].values >= 5, bagg["reb_num"].values / np.maximum(bagg["reb_den"].values, 1), np.nan), index=datesB, name="REB")
FLOW = pd.Series(np.where(bagg["flow_tot"].values > 0, (bagg["flow_up"].values - bagg["flow_dn"].values) / bagg["flow_tot"].values, np.nan), index=datesB, name="FLOW")
micro_ew_ret = np.where(bagg["micro_rcnt"].values > 0, bagg["micro_rsum"].values / np.maximum(bagg["micro_rcnt"].values, 1), 0.0)
Mmicro = pd.Series(np.cumprod(1.0 + micro_ew_ret), index=datesB, name="M_micro_ew")
LOG(f"Part B done: REB 有效 {REB.notna().sum()} 天 / FLOW 有效 {FLOW.notna().sum()} 天, {time.time()-t0:.0f}s")

# ---------------- Part C: 信号、episode、统计 ----------------
LOG("Part C: 信号构建与画像 ...")
br = pd.read_parquet(os.path.join(DATA, "breadth.parquet"))["breadth"]
br.index = pd.to_datetime(br.index)
xc = pd.concat([br.rename("breadth"), s_upshare], axis=1).dropna()
LOG(f"  交叉验证 up_share(merged复算) vs breadth.parquet: n={len(xc)}, mean|diff|={(xc.breadth-xc.up_share_merged).abs().mean():.6f}, corr={xc.corr().iloc[0,1]:.4f}")

master = datesA
df = pd.DataFrame(index=master)
df["M"] = sM
df["M_micro_ew"] = Mmicro.reindex(master)
df["breadth"] = br.reindex(master)

for w in (5, 10, 20):
    sp = br.rolling(w).mean()
    c1 = sp.rolling(20).max() >= 0.85
    c2 = (sp.shift(1).rolling(5).max() - sp) >= 0.05
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
gain = diff.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
loss = (-diff.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
rsi14 = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
df["dd60"] = dd60.reindex(master); df["dd250"] = dd250.reindex(master)
df["dev15"] = dev15.reindex(master); df["rsi14"] = rsi14.reindex(master)
df["ret1"] = ret1.reindex(master)

f_dd60 = dd60 < -0.10
f_dev = dev15 < -0.03
f_rsi = rsi14 <= 45
f_B1 = f_dd60 & f_dev & f_rsi
f_C = (dd250 < -0.35) & (ret1 > 0.05)
for nm, f in [("flag_dd60", f_dd60), ("flag_dev15", f_dev), ("flag_rsi14", f_rsi),
              ("flag_B1_oversold", f_B1), ("flag_C_crisis", f_C)]:
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
        hit = (bool(f < 0) if DIRECTION[s] == "top" else bool(f > 0)) if np.isfinite(f) else False
        evs.append((st, f, hit))
        rows.append({"signal": s, "start": st.date().isoformat(), "end": en.date().isoformat(),
                     "n_days": nd, "fwd15": None if not np.isfinite(f) else round(float(f), 4), "hit": hit})
    fs = [f for _, f, _ in evs if np.isfinite(f)]
    hits = [h for _, f, h in evs if np.isfinite(f)]
    summary[s] = {
        "direction": DIRECTION[s],
        "trigger_days": int(flag.sum()),
        "n_episodes": len(eps),
        "n_events_with_fwd15": len(fs),
        "win_rate": None if not hits else round(float(np.mean(hits)), 4),
        "fwd15_mean": None if not fs else round(float(np.mean(fs)), 4),
        "fwd15_median": None if not fs else round(float(np.median(fs)), 4),
        "fwd15_min": None if not fs else round(float(np.min(fs)), 4),
        "fwd15_max": None if not fs else round(float(np.max(fs)), 4),
        "first_episode": None if not eps else eps[0][0].date().isoformat(),
        "last_episode": None if not eps else eps[-1][1].date().isoformat(),
    }
    LOG(f"  {s}: 触发日 {summary[s]['trigger_days']} / episodes {len(eps)} / 胜率 {summary[s]['win_rate']} / fwd15均值 {summary[s]['fwd15_mean']}")

flags = {s: df["flag_" + s] for s in SIGNALS}
ov = pd.DataFrame(index=SIGNALS, columns=SIGNALS, dtype=float)
for a in SIGNALS:
    for b in SIGNALS:
        A, B = flags[a].values, flags[b].values
        inter = int((A & B).sum()); union = int((A | B).sum())
        ov.loc[a, b] = inter / union if union else 0.0

dd_series = dd_run.reindex(master)
deep = (dd_series < -0.15).fillna(False).values
idx = np.where(deep)[0]
spans = []
if len(idx):
    brk = np.where(np.diff(idx) > 1)[0]
    st_arr = np.r_[idx[0], idx[brk + 1]]; en_arr = np.r_[idx[brk], idx[-1]]
    for s0, e0 in zip(st_arr, en_arr):
        seg = dd_series.iloc[s0:e0 + 1]
        tr_i = seg.idxmin()
        spans.append({"peak": (master[s0 - 1] if s0 > 0 else master[0]).date().isoformat(),
                      "trough": tr_i.date().isoformat(), "end": master[e0].date().isoformat(),
                      "depth": round(float(seg.min()), 4)})
spans = sorted(spans, key=lambda x: x["depth"])[:8]
pos = {d: i for i, d in enumerate(master)}
bottom_sigs = ["REB_bottom", "FLOW_pos_cross", "dd60", "dev15", "rsi14", "B1_oversold", "C_crisis"]
top_sigs = ["SPREAD5_top", "SPREAD10_top", "SPREAD20_top"]
cov = []
for sp_ in spans:
    tp = pos.get(pd.Timestamp(sp_["trough"])); pp = pos.get(pd.Timestamp(sp_["peak"]))
    row = {"drawdown": sp_, "bottom_hits": {}, "top_hits": {}}
    for s in bottom_sigs:
        eps = episodes(flags[s])
        row["bottom_hits"][s] = sum(1 for e in eps if tp is not None and e[0] in pos and abs(tp - pos[e[0]]) <= 10)
    for s in top_sigs:
        eps = episodes(flags[s])
        row["top_hits"][s] = sum(1 for e in eps if pp is not None and e[0] in pos and -15 <= pp - pos[e[0]] <= 5)
    cov.append(row)

yrs = (master[-1] - master[0]).days / 365.25
m_stats = {"n_days": len(master), "start": str(master[0].date()), "end": str(master[-1].date()),
           "total_return": round(float(M[-1] / M[0] - 1), 4),
           "ann_return": round(float((M[-1] / M[0]) ** (1 / yrs) - 1), 4),
           "MDD": round(float(dd_series.min()), 4)}
summary_out = {
    "task": "task-0361 [T1-E1]", "date": "2026-08-18", "n_trials": 3,
    "compute_env": "VPS(vm-0-11) 数据副本 rsync 自 HP；HP MemAvailable 57MB 无法本地计算；产物已回写 HP results/timing_v2/",
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
LOG(f"DONE: 产物已写 {OUT}/ 共 {len(df)} 行序列, episodes {len(rows)} 条")
