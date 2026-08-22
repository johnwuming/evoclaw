#!/usr/bin/env python3
# task-0456 E1: excess_decay 全历史重算（复刻 tmp/task-0373/collect_crowding.py 口径）
# 输出: excess_decay_daily.csv（日频 slope/tstat/flag + 微盘等权/hs300 归一）
import os, sys, numpy as np, pandas as pd

KLINE_DIR = "/root/.openclaw/workspace-quant/data/all_stocks_qfq"
HS300_FILE = "/root/.openclaw/workspace-quant/data/hs300_daily_20060101_20260808.parquet"
OUT = "/root/.openclaw/workspace/shared/results/work/task-0456-data/excess_decay_daily.csv"
START = "2015-01-01"
ROLL, MICRO_PCT = 60, 0.20

files = sorted(f for f in os.listdir(KLINE_DIR) if f.endswith("_daily_qfq.parquet"))
cutoff = int(pd.Timestamp(START).timestamp() // 86400)
date_arrs, code_arrs, mcap_arrs, close_arrs = [], [], [], []
n_read = 0
for i, fn in enumerate(files):
    try:
        df = pd.read_parquet(os.path.join(KLINE_DIR, fn), columns=["date", "close", "outstanding_share"])
    except Exception:
        continue
    if df is None or df.empty:
        continue
    d = pd.to_datetime(df["date"].values)
    days = (d.to_numpy().astype("datetime64[D]") - np.datetime64("1970-01-01", "D")).astype(np.int64)
    keep = days >= cutoff
    if not keep.any():
        continue
    days = days[keep]
    close = df["close"].values[keep].astype(np.float32)
    oshare = df["outstanding_share"].values[keep].astype(np.float64)
    mcap = (close * oshare).astype(np.float32)
    valid = (close > 0) & (mcap > 0) & np.isfinite(mcap)
    if not valid.any():
        continue
    date_arrs.append(days[valid]); code_arrs.append(np.full(int(valid.sum()), n_read, dtype=np.int32))
    mcap_arrs.append(mcap[valid]); close_arrs.append(close[valid])
    n_read += 1
    if (i + 1) % 1000 == 0:
        print(f"read {i+1}/{len(files)} stocks={n_read}", flush=True)
days = np.concatenate(date_arrs); codes = np.concatenate(code_arrs)
mcaps = np.concatenate(mcap_arrs); closes = np.concatenate(close_arrs)
del date_arrs, code_arrs, mcap_arrs, close_arrs
print(f"panel stocks={n_read} rows={len(days):,}", flush=True)

# 分组: 按 (day, mcap) 排序 → 每日市值后 20% 标记
order = np.lexsort((mcaps, days))
days, codes, mcaps, closes = days[order], codes[order], mcaps[order], closes[order]
day_codes, day_start, day_count = np.unique(days, return_index=True, return_counts=True)
grp_idx = np.searchsorted(day_start, np.arange(len(days)), side="right") - 1
rank = np.arange(len(days)) - day_start[grp_idx]
micro = rank < (day_count[grp_idx] * MICRO_PCT).astype(np.int64)
del mcaps, rank, order
print("micro flag done", flush=True)

# 等权日收益: 按 (code, day) 排序取前日收益
order2 = np.lexsort((days, codes))
_d2, _c2, _cl2, _mi2 = days[order2], codes[order2], closes[order2], micro[order2]
prev = np.roll(_cl2, 1); prev[0] = np.nan
same = np.r_[False, _c2[1:] == _c2[:-1]]
ret2 = np.where(same & (prev > 0), _cl2 / prev - 1.0, np.nan)
ret2 = np.nan_to_num(ret2, nan=0.0)
micro_cnt = np.bincount(grp_idx, weights=micro, minlength=len(day_codes))
micro_ret_sum = np.bincount(grp_idx, weights=(ret2 * _mi2)[np.argsort(order2)], minlength=len(day_codes))
micro_ret_mean = micro_ret_sum / np.where(micro_cnt > 0, micro_cnt, np.nan)
for name in ("days", "codes", "closes", "micro", "order2", "_d2", "_c2", "_cl2", "_mi2", "ret2", "prev", "same", "grp_idx", "day_start", "day_count"):
    try:
        del globals()[name]
    except KeyError:
        pass
dates = pd.to_datetime(day_codes.astype("datetime64[D]"))
print(f"trading days={len(dates)} {dates[0].date()}->{dates[-1].date()}", flush=True)

# excess vs hs300 → 60d OLS slope/tstat（复刻 collect_crowding 行184-207）
hs = pd.read_parquet(HS300_FILE); hs["date"] = pd.to_datetime(hs["date"])
hs_s = hs.set_index("date")["close"].sort_index()
hs_ret = hs_s.reindex(dates).pct_change()
excess = micro_ret_mean - hs_ret.values
excess = np.nan_to_num(excess, nan=0.0)
log_cum = np.log(np.cumprod(1 + excess))
slope_series = np.full(len(dates), np.nan); tstat_series = np.full(len(dates), np.nan)
x = np.arange(ROLL, dtype=float); xm = x.mean(); denom = ((x - xm) ** 2).sum()
for i in range(ROLL - 1, len(dates)):
    y = log_cum[i - ROLL + 1:i + 1]
    if not np.all(np.isfinite(y)):
        continue
    slope = ((x - xm) * (y - y.mean())).sum() / denom
    resid = y - (y.mean() + slope * (x - xm))
    sse = (resid ** 2).sum()
    if sse <= 0:
        continue
    se = np.sqrt(sse / (ROLL - 2) / denom)
    slope_series[i] = slope
    tstat_series[i] = slope / se if se > 0 else np.nan

flag = np.where((slope_series < 0) & (tstat_series < -2), "red",
        np.where(slope_series < 0, "yellow", "green"))
flag = np.where(np.isnan(slope_series), "na", flag)
eqw = (1 + pd.Series(micro_ret_mean, index=dates).replace(np.nan, 0.0)).cumprod() * 1000.0
hs_norm = hs_s.reindex(dates).ffill()
out = pd.DataFrame({
    "date": dates.strftime("%Y-%m-%d"),
    "micro_eqw": eqw.round(4).values,
    "hs300": hs_norm.round(2).values,
    "slope_60d": np.round(slope_series, 6),
    "tstat_60d": np.round(tstat_series, 3),
    "flag": flag,
})
out.to_csv(OUT, index=False)
red = (flag == "red").sum()
print(f"saved {OUT} rows={len(out)} red_days={red}", flush=True)
