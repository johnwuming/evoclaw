#!/usr/bin/env python3
# task-0606: HP 只读复算 —— 引擎月末语义 vs asof 语义信号对照
# 在 HP 上执行: ssh hp 'python3 - ' < this file; stdout -> task-0606-hp-signals.csv, stderr -> task-0606-hp-summary.txt
import sys, importlib.util
import numpy as np, pandas as pd

spec = importlib.util.spec_from_file_location('peg', '/home/noname/quant-evolve/scripts/paper_engine_gold.py')
peg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(peg)  # 只用其 fetch_gold_daily 与常量，__main__ 不会执行

s = peg.fetch_gold_daily()          # 与引擎每日 cron 同源同参
SMA_N, VOL_N, VOL_TARGET = peg.SMA_N, peg.VOL_N, peg.VOL_TARGET

m = s.resample("ME").last().dropna()
sma = s.rolling(SMA_N).mean()
vol = s.pct_change().dropna().rolling(VOL_N).std() * np.sqrt(252)

sma_eng = sma.reindex(m.index)                        # 引擎语义（日历月末精确匹配 → 逢非交易日 = NaN）
vol_eng = vol.reindex(m.index)
sma_asof = sma.reindex(m.index, method='ffill')       # asof 语义（取月末前最后交易日）
vol_asof = vol.reindex(m.index, method='ffill')

asof_date = pd.Series([s.index[s.index <= me][-1] for me in m.index], index=m.index)

vt_eng = (VOL_TARGET / vol_eng).clip(0, 1)
vt_asof = (VOL_TARGET / vol_asof).clip(0, 1)
dir_eng = pd.Series((m.values > sma_eng.values).astype(float), index=m.index)
w_eng = (dir_eng * vt_eng).fillna(0.0)
dir_asof = pd.Series(np.where(m.values > sma_asof.values, 1.0, 0.0), index=m.index)
w_asof = (dir_asof * vt_asof)
w_asof = w_asof.where(sma_asof.notna(), 0.0).fillna(0.0)   # 热身期 asof 也无值 → 真实 w=0

out = pd.DataFrame({
    'asof_date': asof_date, 'px': m,
    'sma_eng': sma_eng, 'sma_asof': sma_asof,
    'vol_eng': vol_eng, 'vol_asof': vol_asof,
    'w_eng': w_eng.round(6), 'w_asof': w_asof.round(6),
})
out['is_cal_nan'] = sma_eng.isna() & sma_asof.notna()   # 纯日历月末非交易日造成的 NaN
out['is_warmup_nan'] = sma_eng.isna() & sma_asof.isna() # 上市热身期，asof 也无值
out['w_disagree'] = (w_eng - w_asof).abs() > 1e-9
out.to_csv(sys.stdout, float_format='%.6f')

nan_cal = out.index[out['is_cal_nan']]
dis = out.index[out['w_disagree']]
print(f"rows={len(out)} cal_nan={len(nan_cal)} warmup_nan={int(out['is_warmup_nan'].sum())} w_disagree={len(dis)}", file=sys.stderr)
print("CAL_NAN_MONTHS=" + ",".join(d.strftime('%Y-%m-%d') for d in nan_cal), file=sys.stderr)
print("W_DISAGREE_MONTHS=" + ",".join(d.strftime('%Y-%m-%d') for d in dis), file=sys.stderr)
print(f"last_me={m.index[-1].date()} last_px={m.iloc[-1]:.4f} sma_eng={sma_eng.iloc[-1]} sma_asof={sma_asof.iloc[-1]:.4f} w_eng={w_eng.iloc[-1]:.4f} w_asof={w_asof.iloc[-1]:.4f}", file=sys.stderr)
print(f"daily_rows={len(s)} first={s.index[0].date()} last_trade={s.index[-1].date()}", file=sys.stderr)
