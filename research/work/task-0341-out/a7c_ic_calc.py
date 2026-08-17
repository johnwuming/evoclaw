#!/usr/bin/env python
# task-0341 A7c: dynamic IC validity for P0 candidate factors
# Uses local W1 monthly IC panel (247 months) + catalog v3 direction.
# Effective IC = raw_ic * (1 if dir=='pos' else -1)
import pandas as pd, numpy as np, json, os

BASE = '/root/.openclaw/workspace/shared/results/04-投资研究'
OUT = '/root/.openclaw/workspace/shared/results/work/task-0341-out'
os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(f'{BASE}/factor_ic_monthly.csv')
df['ym'] = pd.to_datetime(df['ym'].astype(str) + '-01')
df = df.sort_values('ym').reset_index(drop=True)
print('IC panel:', df['ym'].iloc[0].date(), '->', df['ym'].iloc[-1].date(), 'n=', len(df))

cat = json.load(open(f'{BASE}/factor_catalog_v3.json'))['factors']

# Mapping: survey factor -> catalog columns (with direction from catalog)
MAPPING = {
    'P0-1 低成交额/低换手族': ['avg_amount_20d','turnover_rate','turnover_rate_60d','log_amount_60d'],
    'P0-2 Amihud': ['amihud_illiquidity','amihud_60d'],
    'P0-6 换手CV': ['amount_cv','amount_cv_60d','turnover_std_20d'],
    'P1 F7 低波': ['volatility_20d','volatility_60d','idiosyncratic_vol','downside_vol_20d'],
    'P1 F13 股息': ['div_yield_ttm'],
    'P2 F14 壳价值': ['shell_value_proxy','mktcap_rank_pct','microcap_liq_interact'],
}

def ic_stats(s, label=''):
    s = s.dropna()
    if len(s) == 0:
        return None
    m = s.mean(); sd = s.std(ddof=1)
    icir = m/sd if sd > 0 else np.nan
    t = m/(sd/np.sqrt(len(s))) if sd > 0 else np.nan
    pos = (s > 0).mean()
    return dict(n=len(s), mean=m, std=sd, icir=icir, t=t, pos=pos)

def half_life_ar1(s):
    # method 2 (R-200): IC_t = a + b*IC_{t-1}; T1/2 = -ln2/ln(beta)
    s = s.dropna()
    if len(s) < 30:
        return None
    x = s.iloc[:-1].values; y = s.iloc[1:].values
    b = np.cov(x, y)[0,1] / np.var(x)
    if b <= 0 or b >= 1:
        return None
    return -np.log(2)/np.log(b)

def eff(s, d):
    sgn = -1 if d == 'neg' else 1
    return s * sgn

results = []
for fac, cols in MAPPING.items():
    for c in cols:
        if c not in df.columns:
            continue
        d = cat.get(c, {}).get('direction', 'pos')
        s = eff(df[c], d)
        full = ic_stats(s)
        if full is None or full['n'] < 60:
            continue
        seg1 = ic_stats(s[(df['ym'] >= '2018-01') & (df['ym'] <= '2021-12')])  # 2018-2021
        seg2 = ic_stats(s[df['ym'] >= '2022-01'])  # 2022-2026
        r24 = ic_stats(s[df['ym'] >= df['ym'].max() - pd.DateOffset(months=23)])
        r36 = ic_stats(s[df['ym'] >= df['ym'].max() - pd.DateOffset(months=35)])
        hl = half_life_ar1(s)
        hl_cat = cat.get(c,{}).get('half_life_months')
        results.append(dict(survey=fac, col=c, cat=cat.get(c,{}).get('category',''),
            dirn=d, label=cat.get(c,{}).get('label',c),
            full=full, seg181_211=seg1, seg221=seg2, r24=r24, r36=r36, hl=hl, hl_cat=hl_cat))

# classification
def classify(r):
    full, r24, seg2 = r['full'], r['r24'], r['seg221']
    if r24 is None:
        return '数据不足'
    f_m, r_m = full['mean'], r24['mean']
    f_t, r_icir = full['t'], r24['icir']
    # thresholds
    strong_full = abs(f_t) >= 2.0
    strong_24 = abs(r_icir) >= 0.4 and abs(r_m) >= 0.02
    weak_24 = abs(r_icir) < 0.25 or abs(r_m) < 0.01
    same_sign = (f_m > 0) == (r_m > 0)
    if strong_full and strong_24 and same_sign:
        return '稳定有效'
    if strong_full and (not strong_24) and same_sign:
        return '衰减中'
    if strong_full and r_m != 0 and not same_sign:
        return '已失效/反转'
    if (not strong_full) and strong_24:
        return '近期涌现'
    if strong_full and weak_24:
        return '衰减中'
    if (not strong_full) and (not strong_24):
        return '全期弱'
    return '弱信号'

for r in results:
    r['profile'] = classify(r)

# Build table
rows = []
for r in results:
    def g(x, k):
        return round(x[k],3) if x and x.get(k) is not None else 'NA'
    rows.append({
        'survey': r['survey'], 'col': r['col'], 'label': r['label'], 'dir': r['dirn'],
        'full_n': r['full']['n'], 'full_IC': g(r['full'],'mean'), 'full_ICIR': g(r['full'],'icir'),
        'full_t': g(r['full'],'t'), 'r36_IC': g(r['r36'],'mean'), 'r36_ICIR': g(r['r36'],'icir'),
        'r24_IC': g(r['r24'],'mean'), 'r24_ICIR': g(r['r24'],'icir'),
        'seg181_IC': g(r['seg181_211'],'mean'), 'seg181_ICIR': g(r['seg181_211'],'icir'),
        'seg221_IC': g(r['seg221'],'mean'), 'seg221_ICIR': g(r['seg221'],'icir'),
        'half_life_m': r['hl_cat'] if r.get('hl_cat') else (round(r['hl'],1) if r['hl'] else 'NA'),
        'profile': r['profile'],
    })

tbl = pd.DataFrame(rows)
tbl.to_csv(f'{OUT}/a7c-dynamic-ic-table.csv', index=False)
tbl.to_json(f'{OUT}/a7c-dynamic-ic-table.json', orient='records', force_ascii=False, indent=1)
pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 50)
print(tbl.to_string(index=False))
