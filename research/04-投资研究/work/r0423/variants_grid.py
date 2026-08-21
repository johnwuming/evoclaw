#!/usr/bin/env python3
# task-0423 / R-261: 行业轮动降换手变体网格（E1 层算术画像，零回测纪律）
# 口径（与 R-258 复算对拍锁定）：月末去重(keep last，弃2017-01-20伪行) + pct_change(fill_method=None)
#   n=247 持有月（R-258 记 248 系双行伪月计数，锚点数字全部对上）
# V0 k=1 Top5 对照 | V1 3月均值信号 | V2 缓冲带8 | V3 季度调仓 | V4 V1+V2
# 成本: cost(t)=2c*turnover, turnover=1-|H(t-1)&H(t)|/5 成员口径, 首月单腿c
import json, os, hashlib
import numpy as np
import pandas as pd

CSV = '/home/noname/quant-evolve/results/work/r0415/sw_industry_monthly.csv'
OUT = '/home/noname/quant-evolve/results/work/r0423'
os.makedirs(OUT, exist_ok=True)

df_raw = pd.read_csv(CSV, parse_dates=['date']).set_index('date').sort_index()
cols_all = list(df_raw.columns)
assert len(cols_all) == 31
# 月末去重：每月保留最后一行（2017-01 双行 -> 保留 2017-01-26）
key = pd.Series([(d.year, d.month) for d in df_raw.index], index=df_raw.index)
dup = key[key.duplicated(keep='last')]
df = df_raw.loc[~df_raw.index.isin(dup.index)]
rets = df.pct_change(fill_method=None)
ym = [(d.year, d.month) for d in df.index]
hold_idx = [i for i, (y, m) in enumerate(ym) if (2006, 1) <= (y, m) <= (2026, 7)]
N = len(hold_idx)  # 247

def build_holdings(variant, col_subset):
    cs = list(col_subset)
    k = 3 if variant in ('V1', 'V4') else 1
    sc = rets[cs].rolling(k).mean()
    H, holdings = None, []
    for j, hi in enumerate(hold_idx):
        si = hi - 1
        valid = rets[cs].iloc[hi].notna() & sc.iloc[si].notna()
        elig = [c for c in cs if valid[c]]
        ranks = sorted(elig, key=lambda c: (-sc.iloc[si][c], cs.index(c)))
        rank_of = {c: r + 1 for r, c in enumerate(ranks)}
        top5 = ranks[:5]
        if variant in ('V0', 'V1'):
            H = top5
        elif variant in ('V2', 'V4'):
            if H is None:
                H = top5
            else:
                keep = [c for c in H if rank_of.get(c, 10**9) <= 8]
                H = list(keep)
                for c in ranks:
                    if len(H) >= 5: break
                    if c not in H and rank_of[c] <= 5: H.append(c)
                for c in ranks:
                    if len(H) >= 5: break
                    if c not in H: H.append(c)
                H = H[:5]
        elif variant == 'V3':
            if H is None or j % 3 == 0: H = top5
        holdings.append(list(H))
    return holdings

def ew_series(col_subset):
    cs = list(col_subset)
    out = []
    for hi in hold_idx:
        valid = rets[cs].iloc[hi].notna() & rets[cs].iloc[hi - 1].notna()
        out.append(rets[cs].iloc[hi][valid].mean())
    return np.array(out)

def geo_ann(r):
    r = np.asarray(r, dtype=float)
    return float(np.prod(1 + r) ** (12 / len(r)) - 1)

def evaluate(holdings, ew, label):
    gross = np.array([rets.iloc[hi][h].mean() for hi, h in zip(hold_idx, holdings)])
    n = len(gross)
    to = np.zeros(n)
    for t in range(1, n):
        to[t] = 1 - len(set(holdings[t - 1]) & set(holdings[t])) / 5
    tau = float(to[1:].mean())
    res = {'label': label, 'n_months': n, 'tau': round(tau, 4),
           'gross_ann': round(geo_ann(gross) * 100, 2), 'ew_ann': round(geo_ann(ew) * 100, 2),
           'gross_excess_pp': round((geo_ann(gross) - geo_ann(ew)) * 100, 2),
           'excess_mean_mo_pct': round(float((gross - ew).mean() * 100), 3),
           'excess_t': round(float((gross - ew).mean() / ((gross - ew).std(ddof=1) / np.sqrt(n))), 2)}
    for c in (0.001, 0.002):
        net = gross.copy(); net[0] -= c; net[1:] -= 2 * c * to[1:]
        res[f'net_excess_pp_c{int(c*10000)}'] = round((geo_ann(net) - geo_ann(ew)) * 100, 2)
        res[f'net_ann_c{int(c*10000)}'] = round(geo_ann(net) * 100, 2)
    exc = gross - ew
    n_lock = n - 26
    segs = np.array_split(np.arange(n_lock), 5)
    seg_means = [round(float(exc[s].mean() * 100), 3) for s in segs]
    res['five_seg_pct_mo'] = seg_means
    res['five_seg_pos'] = int(sum(1 for v in seg_means if v > 0))
    res['seg_bounds'] = [f"{df.index[hold_idx[s[0]]].date()}~{df.index[hold_idx[s[-1]]].date()}" for s in segs]
    res['locked_months'] = int(n_lock)
    ho = exc[-26:]
    res['holdout_mean_mo_pct'] = round(float(ho.mean() * 100), 3)
    res['holdout_net20_mean_mo_pct'] = round(float((gross[-26:] - 0.002 * 2 * to[-26:]).mean() * 100 - ew[-26:].mean() * 100), 3)
    res['holdout_bounds'] = f"{df.index[hold_idx[-26]].date()}~{df.index[hold_idx[-1]].date()}"
    return res, gross, to

# ---- main grid (31 industries) ----
ew31 = ew_series(cols_all)
variants = ['V0', 'V1', 'V2', 'V3', 'V4']
results, holds, grosses, tos = {}, {}, {}, {}
for v in variants:
    h = build_holdings(v, cols_all)
    holds[v] = h
    r, g, to = evaluate(h, ew31, v)
    results[v] = r; grosses[v] = g; tos[v] = to
    if v == 'V3':
        r['tau_per_rebalance'] = round(float(np.mean([to[t] for t in range(3, len(to), 3)])), 4)
        r['rebalance_count'] = len([t for t in range(0, len(to), 3)])

v0h = [set(x) for x in holds['V0']]
for v in variants[1:]:
    results[v]['overlap_with_V0'] = round(float(np.mean([len(set(x) & y) / 5 for x, y in zip(holds[v], v0h)])), 3)

opt = sorted(['V1', 'V2', 'V3', 'V4'], key=lambda v: (-results[v]['net_excess_pp_c20'], results[v]['tau']))[0]

# ---- 28-industry sensitivity (drop 2021-12 new columns) ----
first_valid = {c: str(df[c].first_valid_index().date()) for c in cols_all}
new2021 = [c for c in cols_all if first_valid[c] >= '2021-01-01']
cols28 = [c for c in cols_all if c not in new2021]
ew28 = ew_series(cols28)
h28 = build_holdings(opt, cols28)
r28, _, _ = evaluate(h28, ew28, f'{opt}_28ind')

out = {
    'meta': {
        'csv_md5': hashlib.md5(open(CSV, 'rb').read()).hexdigest(),
        'convention': 'month-end dedup keep-last (drop 2017-01-20 spurious row) + pct_change fill_method=None; n=247 hold months 2006-01~2026-07; R-258 anchors reproduced (tau .704/gross 2.84pp/net20 -0.90pp)',
        'signal_pit': 't月持有用t-1月末及以前数据',
        'cost_model': 'cost(t)=2c*turnover, turnover=1-|H(t-1)&H(t)|/5, first month single-leg c',
        'benchmark': 'EW-all eligible (valid ret t-1 & t), cost-free reference',
        'data_anomalies': {'dup_month_rows': [str(d.date()) for d in dup.index], 'coal_gap_months': int(df['煤炭'][df['煤炭'].first_valid_index():df['煤炭'].last_valid_index()].isna().sum())},
        'new2021_industries': new2021, 'n_cols_28': len(cols28),
    },
    'variants': results, 'optimal_variant': opt, 'sens28': r28,
}
with open(f'{OUT}/variant_metrics.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

rows = []
for v in variants:
    for j, hi in enumerate(hold_idx):
        rows.append({'variant': v, 'month': str(df.index[hi].date()), 'gross_ret': round(float(grosses[v][j]), 6),
                     'ew_ret': round(float(ew31[j]), 6), 'turnover': round(float(tos[v][j]), 4),
                     'holdings': '|'.join(holds[v][j])})
pd.DataFrame(rows).to_csv(f'{OUT}/monthly_detail.csv', index=False)

print('ANCHOR V0: tau=%.4f gross=%.2fpp net10=%.2f net20=%.2f meanExc=%.3f' % (
    results['V0']['tau'], results['V0']['gross_excess_pp'], results['V0']['net_excess_pp_c10'],
    results['V0']['net_excess_pp_c20'], results['V0']['excess_mean_mo_pct']))
for v in variants:
    r = results[v]
    print('%s tau=%.4f gross=%+.2f net10=%+.2f net20=%+.2f seg=%d/5 ov=%.3f %s' % (
        v, r['tau'], r['gross_excess_pp'], r['net_excess_pp_c10'], r['net_excess_pp_c20'],
        r['five_seg_pos'], r.get('overlap_with_V0', 1.0), r['five_seg_pct_mo']))
print('optimal:', opt, '| sens28:', json.dumps({k: r28[k] for k in ['tau', 'gross_excess_pp', 'net_excess_pp_c10', 'net_excess_pp_c20', 'five_seg_pct_mo', 'five_seg_pos', 'holdout_mean_mo_pct']}, ensure_ascii=False))
