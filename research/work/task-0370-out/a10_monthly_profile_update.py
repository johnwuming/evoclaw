#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A10-4 (task-0370): A7c 动态画像月度自动更新（增量 + 幂等）.

数据源（与 A7c/task-0341 同源，W1 月频全市场 IC 口径）:
  - results/factor_ic_monthly.csv   月频 IC 面板（ym + 107 因子列）
  - results/factor_catalog_v3.json  因子元数据（direction/mean_ic/icir/half_life_months）

产物（独立目录，不覆盖 a7c 原始产物）:
  - results/a10-monthly-profile/dynamic-ic-table.{csv,json}  含 as_of_ym
  - results/a10-monthly-profile/rolling-ic-series.json
  - results/a10-monthly-profile/state.json                   输入 md5 + 运行历史
  - results/a10-monthly-profile/history/dynamic-ic-table-asof-YYYYMM.csv  月度快照(追加)

增量: 输入 md5 未变且产物完好 -> 跳过重算（幂等，exit 0 up-to-date）；
      md5 变化 -> 全量重算（确定性），原子写 + 快照。
用法: python scripts/a10_monthly_profile_update.py [--force]
"""
import pandas as pd, numpy as np, json, os, sys, hashlib, datetime

HOME = os.path.expanduser('~')
BASE = f'{HOME}/quant-evolve'
PANEL = f'{BASE}/results/factor_ic_monthly.csv'
CAT = f'{BASE}/results/factor_catalog_v3.json'
OUT = f'{BASE}/results/a10-monthly-profile'
HIST = f'{OUT}/history'
STATE = f'{OUT}/state.json'
FORCE = '--force' in sys.argv

os.makedirs(HIST, exist_ok=True)

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def atomic_write(path, content):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp, path)

# ---- 幂等检查 ----
pmd5, cmd5 = md5(PANEL), md5(CAT)
state = {}
if os.path.exists(STATE):
    try:
        state = json.load(open(STATE))
    except Exception:
        state = {}
outs_ok = all(os.path.exists(f'{OUT}/{n}') for n in
              ('dynamic-ic-table.csv', 'dynamic-ic-table.json', 'rolling-ic-series.json'))
if outs_ok and not FORCE and state.get('panel_md5') == pmd5 and state.get('cat_md5') == cmd5:
    print(f"[up-to-date] inputs unchanged (panel_md5={pmd5[:8]}...), outputs intact, as_of={state.get('as_of_ym')}, skip recompute")
    sys.exit(0)

# ---- 数据加载 ----
df = pd.read_csv(PANEL)
df['ym'] = pd.to_datetime(df['ym'].astype(str) + '-01')
df = df.sort_values('ym').reset_index(drop=True)
as_of = df['ym'].iloc[-1].strftime('%Y-%m')
cat = json.load(open(CAT))['factors']
print(f"[run] panel {df['ym'].iloc[0].date()} -> {df['ym'].iloc[-1].date()} n={len(df)} as_of={as_of}")

# 15 普查因子 -> 面板可算列（与 A7c 相同映射）
MAPPING = {
    'P0-1 低成交额/低换手族': ['avg_amount_20d', 'turnover_rate', 'turnover_rate_60d', 'log_amount_60d'],
    'P0-2 Amihud': ['amihud_illiquidity', 'amihud_60d'],
    'P0-6 换手CV': ['amount_cv', 'amount_cv_60d', 'turnover_std_20d'],
    'P1 F7 低波': ['volatility_20d', 'volatility_60d', 'idiosyncratic_vol', 'downside_vol_20d'],
    'P1 F13 股息': ['div_yield_ttm'],
    'P2 F14 壳价值': ['shell_value_proxy', 'mktcap_rank_pct', 'microcap_liq_interact'],
}

def ic_stats(s):
    s = s.dropna()
    if len(s) == 0:
        return None
    m, sd = s.mean(), s.std(ddof=1)
    return dict(n=int(len(s)), mean=m, icir=(m / sd if sd > 0 else np.nan),
                t=(m / (sd / np.sqrt(len(s))) if sd > 0 else np.nan))

def eff(s, d):
    return s * (-1 if d == 'neg' else 1)

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
        seg1 = ic_stats(s[(df['ym'] >= '2018-01') & (df['ym'] <= '2021-12')])
        seg2 = ic_stats(s[df['ym'] >= '2022-01'])
        r24 = ic_stats(s[df['ym'] >= df['ym'].max() - pd.DateOffset(months=23)])
        r36 = ic_stats(s[df['ym'] >= df['ym'].max() - pd.DateOffset(months=35)])
        results.append(dict(survey=fac, col=c, label=cat.get(c, {}).get('label', c), dirn=d,
                            full=full, seg181_211=seg1, seg221=seg2, r24=r24, r36=r36,
                            hl_cat=cat.get(c, {}).get('half_life_months')))

def classify(r):
    full, r24 = r['full'], r['r24']
    if r24 is None or r24['n'] < 6:
        return '数据不足'
    f_m, r_m = full['mean'], r24['mean']
    f_t, r_icir = full['t'], r24['icir']
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

def g(x, k, nd=3):
    return round(x[k], nd) if x and x.get(k) is not None and not (isinstance(x.get(k), float) and np.isnan(x[k])) else 'NA'

rows = []
for r in results:
    r['profile'] = classify(r)
    rows.append({'as_of_ym': as_of, 'survey': r['survey'], 'col': r['col'], 'label': r['label'], 'dir': r['dirn'],
                 'full_n': r['full']['n'], 'full_IC': g(r['full'], 'mean'), 'full_ICIR': g(r['full'], 'icir'),
                 'full_t': g(r['full'], 't'),
                 'r36_IC': g(r['r36'], 'mean'), 'r36_ICIR': g(r['r36'], 'icir'),
                 'r24_IC': g(r['r24'], 'mean'), 'r24_ICIR': g(r['r24'], 'icir'),
                 'seg181_IC': g(r['seg181_211'], 'mean'), 'seg181_ICIR': g(r['seg181_211'], 'icir'),
                 'seg221_IC': g(r['seg221'], 'mean'), 'seg221_ICIR': g(r['seg221'], 'icir'),
                 'half_life_m': r['hl_cat'] if r.get('hl_cat') else 'NA', 'profile': r['profile']})

tbl = pd.DataFrame(rows)
atomic_write(f'{OUT}/dynamic-ic-table.csv', tbl.to_csv(index=False))
atomic_write(f'{OUT}/dynamic-ic-table.json', json.dumps(rows, ensure_ascii=False, indent=1))

# ---- 滚动 IC 时序（24m/36m，12m 步进，与 A7c 相同）----
P0KEY = {'P0-1_low_amt': ['avg_amount_20d', 'log_amount_60d'],
         'P0-2_amihud': ['amihud_illiquidity'],
         'P0-6_amount_cv': ['amount_cv']}
roll = []
for fac, cols in P0KEY.items():
    for c in cols:
        if c not in df.columns:
            continue
        d = cat.get(c, {}).get('direction', 'pos')
        s = eff(df[c], d)
        for win in (24, 36):
            steps = []
            for i in range(len(df) - 1, win - 2, -12):
                w = s.iloc[i - win + 1:i + 1].dropna()
                if len(w) >= 18:
                    sd = w.std(ddof=1)
                    steps.append([df['ym'].iloc[i].strftime('%Y-%m'), round(w.mean(), 3),
                                  round(w.mean() / sd, 2) if sd > 0 else None])
            roll.append({'factor': fac, 'col': c, 'window': f'{win}m', 'as_of_ym': as_of, 'series': steps[::-1]})
atomic_write(f'{OUT}/rolling-ic-series.json', json.dumps(roll, ensure_ascii=False, indent=1))

# ---- 月度快照（同 as_of 只存一次）----
snap = f'{HIST}/dynamic-ic-table-asof-{as_of.replace("-", "")}.csv'
if not os.path.exists(snap):
    tbl.to_csv(snap, index=False)

# ---- 与上次快照的画像变化（月度增量价值）----
changes = []
prev_state_asof = state.get('as_of_ym')
if prev_state_asof and prev_state_asof != as_of:
    prev_snap = f'{HIST}/dynamic-ic-table-asof-{prev_state_asof.replace("-", "")}.csv'
    if os.path.exists(prev_snap):
        prev = pd.read_csv(prev_snap)[['col', 'profile']].set_index('col')['profile'].to_dict()
        for r in rows:
            p = prev.get(r['col'])
            if p and p != r['profile']:
                changes.append(f"{r['col']}: {p} -> {r['profile']}")

# ---- state 更新 ----
runs = state.get('runs', [])
runs.append({'ts': datetime.datetime.now().isoformat(timespec='seconds'), 'as_of_ym': as_of,
             'n_rows': int(len(df)), 'panel_md5': pmd5, 'cat_md5': cmd5, 'forced': FORCE})
atomic_write(STATE, json.dumps({'panel_md5': pmd5, 'cat_md5': cmd5, 'as_of_ym': as_of,
                                'n_rows': int(len(df)), 'runs': runs[-24:]}, ensure_ascii=False, indent=1))

cnt = tbl['profile'].value_counts().to_dict()
print(f"[done] factors={len(tbl)} as_of={as_of} profiles={cnt}")
print(f"[done] outputs -> {OUT}/dynamic-ic-table.csv|.json, rolling-ic-series.json, snapshot={snap}")
if changes:
    print('[changes vs last snapshot]')
    for c in changes:
        print('  ', c)
pd.set_option('display.width', 250)
print(tbl[['col', 'full_IC', 'full_ICIR', 'r24_IC', 'r24_ICIR', 'profile']].to_string(index=False))
sys.exit(0)
