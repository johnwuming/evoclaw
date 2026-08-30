#!/usr/bin/env python3
"""task-0585: vC-0 权威口径组合曲线供给（滚动等波动率 + 58/42 静态对照）
方法: 复用 task-0492 backtest_f1_drift_engine.py 引擎语义（月频、双腿、成本 0.13%×(|Δw_A|+|Δw_gold|)）
solver_equal_vol_v1 参数月频适配: 60d 滚动窗→6 个月度收益观测窗; 年化 252→×sqrt(12);
min_obs 40→40×(6/60)=4 个观测（不足→等权 fallback）; rebalance_band 0.02 原样保留。
PIT: t 月权重只用 t-1 及更早收益。锚定: dryrun 2026-08-28 解 0.5802970/0.4197030（静态对照变体 + 末端窗对比）。
只读 live/data/nav_curves.csv; 产物写 live/data/nav_curves.authoritative.csv（新文件，旧文件零改动）。
"""
import pandas as pd, numpy as np, hashlib, json, sys

CSV = '/root/.openclaw/workspace/tools/quant-bff/live/data/nav_curves.csv'
OUT = '/root/.openclaw/workspace/tools/quant-bff/live/data/nav_curves.authoritative.csv'
DRYRUN_WA, DRYRUN_WG = 0.5802970, 0.4197030
COST, BAND, WIN, MIN_OBS = 0.0013, 0.02, 6, 4

df = pd.read_csv(CSV, parse_dates=['month']).set_index('month')
rA = df['A'].pct_change().fillna(df['A'] - 1.0)   # 首行相对基期 1.0 的收益
rG = df['gold'].pct_change().fillna(df['gold'] - 1.0)
n = len(df); rAv, rGv = rA.values, rG.values

def metrics(nav_series, incl_base_mdd=True):
    r = nav_series.pct_change().fillna(nav_series.iloc[0] - 1.0)
    yrs = len(r) / 12.0
    ann = nav_series.iloc[-1] ** (1 / yrs) - 1
    vol = r.std(ddof=1) * np.sqrt(12)
    nav_mdd = nav_series if incl_base_mdd else nav_series
    s = pd.concat([pd.Series([1.0]), nav_mdd.reset_index(drop=True)]) if incl_base_mdd else nav_mdd
    mdd = float((s / s.cummax() - 1).min())
    return dict(ann_return=round(float(ann), 6), ann_vol=round(float(vol), 6),
                sharpe=round(float(ann / vol), 4) if vol > 0 else None,
                max_drawdown=round(mdd, 6), final_nav=round(float(nav_series.iloc[-1]), 6), n_months=len(r))

# ---------- ① 方法论复现：F1_quarterly（50/50 静态、季初月再平衡）max|diff| 必须=0 ----------
def run_engine(target_fn, rebal_mask=None, band=None):
    wA = wG = np.nan; rp = np.full(n, np.nan); wlog = np.full((n, 2), np.nan)
    for i in range(n):
        if np.isnan(wA):
            wA, wG = target_fn(i)
            cost = COST * (abs(wA) + abs(wG))
        elif rebal_mask is None or rebal_mask[i]:
            tA, tG = target_fn(i)
            if not (np.isnan(tA) or np.isnan(tG)):
                cost = COST * (abs(tA - wA) + abs(tG - wG)); wA, wG = tA, tG
            else:
                cost = 0.0
        else:
            cost = 0.0
        rp[i] = wA * rAv[i] + wG * rGv[i] - cost
        wlog[i] = (wA, wG)
        m = 1 + wA * rAv[i] + wG * rGv[i]
        wA, wG = wA * (1 + rAv[i]) / m, wG * (1 + rGv[i]) / m
    return pd.Series(rp, index=df.index), wlog

f1q_mask = np.array([d.month % 3 == 1 for d in df.index])
rp_f1q, _ = run_engine(lambda i: (0.5, 0.5), f1q_mask)
nav_f1q = (1 + rp_f1q).cumprod()
maxdiff = float(np.max(np.abs(nav_f1q.values - df['F1_quarterly'].values)))
print(f'[repro] F1_quarterly max|diff| = {maxdiff:.3e}')
# R-377 用月收益文件直乘得精确 0.0；本脚本从 NAV 列 pct_change 反解收益，引入 <1e-14 机器噪声，判定等价
assert maxdiff < 1e-12, '方法论复现失败'

# ---------- ② 滚动等波动率目标权重（PIT: t 月只用 t-6..t-1） ----------
def eqvol_target(i):
    if i < MIN_OBS:
        return (0.5, 0.5)  # min_obs 前等权 fallback（solver fallback=equal_weight）
    a = rAv[max(0, i - WIN):i]; g = rGv[max(0, i - WIN):i]
    sA = a.std(ddof=1) * np.sqrt(12); sG = g.std(ddof=1) * np.sqrt(12)
    if not (np.isfinite(sA) and np.isfinite(sG)) or sA <= 0 or sG <= 0:
        return (0.5, 0.5)
    invA, invG = 1 / sA, 1 / sG
    wA = invA / (invA + invG)
    return (float(wA), float(1 - wA))

def run_band_engine(target_fn):
    """band 0.02: 月初看目标，与当前漂移权重各腿偏差 ≤band → 不调仓(零成本); 超出→重置+成本"""
    wA = wG = np.nan; rp = np.full(n, np.nan); wlog = []
    rebals = 0
    for i in range(n):
        tA, tG = target_fn(i)
        if np.isnan(wA):
            wA, wG = tA, tG; cost = COST * (abs(wA) + abs(wG)); rebals += 1
        elif abs(tA - wA) > BAND or abs(tG - wG) > BAND:
            cost = COST * (abs(tA - wA) + abs(tG - wG)); wA, wG = tA, tG; rebals += 1
        else:
            cost = 0.0
        rp[i] = wA * rAv[i] + wG * rGv[i] - cost
        wlog.append((wA, wG))
        m = 1 + wA * rAv[i] + wG * rGv[i]
        wA, wG = wA * (1 + rAv[i]) / m, wG * (1 + rGv[i]) / m
    return pd.Series(rp, index=df.index), pd.DataFrame(wlog, index=df.index, columns=['w_A', 'w_gold']), rebals

rp_roll, wlog, n_reb = run_band_engine(eqvol_target)
nav_roll = (1 + rp_roll).cumprod()

# 权重合理性断言
assert np.allclose(wlog.sum(axis=1), 1.0, atol=1e-12), '权重和≠1'
# PIT 断言: 对抽样 i，扰动 ≥i 的收益不得改变 i 月目标（窗口右开 [i-WIN, i) 结构性无前视）
def target_at(i, A=None, G=None):
    A = rAv if A is None else A; G = rGv if G is None else G
    if i < MIN_OBS: return (0.5, 0.5)
    a = A[max(0, i - WIN):i]; g = G[max(0, i - WIN):i]
    sA = a.std(ddof=1) * np.sqrt(12); sG = g.std(ddof=1) * np.sqrt(12)
    wA = (1/sA) / (1/sA + 1/sG); return (float(wA), float(1 - wA))
pit_ok = True
for i in (MIN_OBS, 50, 100, 155, n - 1):
    A2, G2 = rAv.copy(), rGv.copy(); A2[i:] = 0.01; G2[i:] = -0.02
    pit_ok &= abs(target_at(i)[0] - target_at(i, A2, G2)[0]) == 0
print(f'[sanity] 权重和=1 ✓; PIT(扰动 t 及以后不影响 t 月目标) = {pit_ok}; 调仓次数={n_reb}/{n}')
assert pit_ok

# ---------- ③ 静态 58.03/41.97 月度再平衡对照（锚=dryrun 解） ----------
rp_static, wlog_s, _ = run_engine(lambda i: (DRYRUN_WA, DRYRUN_WG), np.ones(n, dtype=bool))
nav_static = (1 + rp_static).cumprod()

m_roll = metrics(nav_roll); m_static = metrics(nav_static); m_f1q = metrics(df['F1_quarterly'])
print('[metrics] rolling :', json.dumps(m_roll))
print('[metrics] static58:', json.dumps(m_static))
print('[metrics] F1q(old):', json.dumps(m_f1q))
# R-377 重算A 锚（静态 58.03/41.97 月度再平衡）: ann .1444 vol .1032 sharpe 1.399 mdd -.0969 final 5.774
ref = dict(ann=.1444, vol=.1032, sharpe=1.399, mdd=-.0969, final=5.774)
chk = dict(ann=round(m_static['ann_return'],4), vol=round(m_static['ann_vol'],4),
           sharpe=round(m_static['sharpe'],3), mdd=round(m_static['max_drawdown'],4), final=m_static['final_nav'])
print('[anchor] static vs R-377 重算A:', json.dumps(chk), '| expect', ref)
assert abs(chk['ann']-ref['ann']) <= .002 and abs(chk['vol']-ref['vol']) <= .002 and abs(chk['final']-ref['final']) <= .02

# ---------- ④ 锚定校验：滚动序列末端窗 vs dryrun 解 ----------
last_w = wlog.iloc[-1]; tgt_last = eqvol_target(n - 1)
print(f"[anchor] 滚动末端执行权重 {last_w['w_A']:.4f}/{last_w['w_gold']:.4f}; 末端目标 {tgt_last[0]:.4f}/{tgt_last[1]:.4f}; dryrun {DRYRUN_WA:.4f}/{DRYRUN_WG:.4f}")
w_first = wlog.iloc[MIN_OBS]; tgt_first = eqvol_target(MIN_OBS)
print(f"[anchor] 首个非 fallback 期 {wlog.index[MIN_OBS].date()} 目标 {tgt_first[0]:.4f}/{tgt_first[1]:.4f}")

# ---------- ⑤ 落盘 ----------
out = pd.DataFrame({
    'month': df.index.strftime('%Y-%m-%d'),
    'A': df['A'].values, 'gold': df['gold'].values,          # 腿净值原样保留（对照/溯源）
    'F1_quarterly': df['F1_quarterly'].values,               # 旧近似口径列保留（历史对照）
    'VC0_ROLLING_EQVOL': nav_roll.values.round(10),
    'VC0_5842_STATIC': nav_static.values.round(10),
    'w_roll_A': wlog['w_A'].values.round(10), 'w_roll_gold': wlog['w_gold'].values.round(10),
})
out.to_csv(OUT, index=False)
md5 = hashlib.md5(open(OUT, 'rb').read()).hexdigest()
print(f'[out] {OUT} md5={md5} rows={len(out)}')
res = dict(repro_maxdiff=maxdiff, metrics_rolling=m_roll, metrics_static58=m_static, metrics_f1q_old=m_f1q,
           static_vs_R377=chk, last_target=[round(tgt_last[0], 6), round(tgt_last[1], 6)],
           last_exec=[round(float(last_w['w_A']), 6), round(float(last_w['w_gold']), 6)],
           first_nonfallback=dict(month=str(wlog.index[MIN_OBS].date()), target=[round(tgt_first[0], 6), round(tgt_first[1], 6)]),
           rebalances=n_reb, n_months=n, md5=md5, pit_ok=bool(pit_ok))
json.dump(res, open('/tmp/task-0585-results.json', 'w'), indent=1)
print('DONE')
