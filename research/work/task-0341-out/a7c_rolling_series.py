#!/usr/bin/env python
# task-0341 A7c: rolling 24m/36m IC series (12m step) for P0 factors
import pandas as pd, numpy as np, json, os

BASE = '/root/.openclaw/workspace/shared/results/04-投资研究'
OUT = '/root/.openclaw/workspace/shared/results/work/task-0341-out'

df = pd.read_csv(f'{BASE}/factor_ic_monthly.csv')
df['ym'] = pd.to_datetime(df['ym'].astype(str) + '-01')
df = df.sort_values('ym').reset_index(drop=True)
cat = json.load(open(f'{BASE}/factor_catalog_v3.json'))['factors']

P0 = {
    'P0-1_low_amt': ['avg_amount_20d','log_amount_60d'],
    'P0-2_amihud': ['amihud_illiquidity'],
    'P0-6_amount_cv': ['amount_cv'],
}
def eff(s, d):
    return s * (-1 if d=='neg' else 1)

rows = []
for fac, cols in P0.items():
    for c in cols:
        d = cat.get(c, {}).get('direction','pos')
        s = eff(df[c], d)
        # rolling 24m / 36m trailing mean IC + ICIR, 12m step
        for win in (24, 36):
            steps = []
            for i in range(len(df)-1, win-2, -12):
                lo = i - win + 1
                w = s.iloc[lo:i+1].dropna()
                if len(w) >= 18:
                    steps.append((df['ym'].iloc[i].strftime('%Y-%m'),
                                  round(w.mean(),3), round(w.mean()/w.std(ddof=1),2) if w.std(ddof=1)>0 else np.nan))
            rows.append({'factor':fac,'col':c,'window':f'{win}m','series':steps[::-1]})

json.dump(rows, open(f'{OUT}/a7c-rolling-ic-series.json','w'), ensure_ascii=False, indent=1)
# print compact
for r in rows:
    ser = ' | '.join(f"{m}:{ic}/{icir}" for m,ic,icir in r['series'])
    print(f"{r['factor']} {r['col']} [{r['window']}]")
    print('  ', ser[:400])
