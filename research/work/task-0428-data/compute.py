import pandas as pd, numpy as np, json

# ---------- load ----------
pe1 = pd.read_csv('/tmp/r268/pe_lg_中证1000.csv', parse_dates=['日期'])
pe3 = pd.read_csv('/tmp/r268/pe_lg_沪深300.csv', parse_dates=['日期'])
pxd = pd.read_csv('/tmp/r268/px_sh000922_em.csv', parse_dates=['date'])
crow = pd.read_csv('/root/.openclaw/workspace/shared/results/04-投资研究/crowding_history.csv', parse_dates=['date'])
nav = pd.read_csv('/root/.openclaw/workspace/shared/results/04-投资研究/a13_rsraw_e1f10dz_full_nav.csv', parse_dates=['date'])

m1 = pe1[['日期','指数','滚动市盈率']].rename(columns={'日期':'date','指数':'px1000','滚动市盈率':'pe1000'}).set_index('date')
m3 = pe3[['日期','指数','滚动市盈率']].rename(columns={'日期':'date','指数':'px300','滚动市盈率':'pe300'}).set_index('date')
df = m1.join(m3, how='inner').sort_index()
df['spread'] = np.log(df.pe1000 / df.pe300)

def trail_pct(s, w=756):
    return s.rolling(w, min_periods=w).apply(lambda x: float((x[-1] >= x).mean()), raw=True)

df['s1_pct'] = trail_pct(df.spread)
df['m'] = df.index.to_period('M')
me = df.groupby('m').tail(1).copy()          # month-end rows
me.index = me['m']                           # PeriodIndex(M)
me['ret1000'] = me.px1000.pct_change()
me['ret300'] = me.px300.pct_change()
me['fwd_ret1000'] = me.ret1000.shift(-1)
me['fwd_ret300'] = me.ret300.shift(-1)
me['diff_bm'] = me.fwd_ret300 - me.fwd_ret1000
me['s1'] = me.s1_pct >= 0.70

# crowding roll3y pct
crow = crow.set_index('date').sort_index()
crow['c_pct'] = trail_pct(crow.micro_turnover_share_roll20)
cm = crow.groupby(crow.index.to_period('M')).tail(1)
me['c_pct'] = cm.set_index(cm.index.to_period('M')).c_pct.reindex(me.index)
me['s2'] = me.c_pct >= 0.60
me['scomb'] = me.s1 & me.s2

# dividend leg
pxd = pxd.set_index('date').sort_index()
dm = pxd.groupby(pxd.index.to_period('M')).tail(1)
me['retdiv'] = dm.set_index(dm.index.to_period('M')).close.reindex(me.index).pct_change()
me['fwd_retdiv'] = me.retdiv.shift(-1)
me['diff_div'] = me.fwd_retdiv - me.fwd_ret1000

# a13 monthly
nv = nav.set_index('date').nav.resample('ME').last()
a13m = nv.pct_change()
a13m.index = a13m.index.to_period('M')
me['a13'] = a13m.reindex(me.index)

# quarterly fwd (3m overlapping)
me['fwd3_ret1000'] = me.px1000.shift(-3) / me.px1000 - 1
me['fwd3_ret300'] = me.px300.shift(-3) / me.px300 - 1
me['diff_bm_3m'] = me.fwd3_ret300 - me.fwd3_ret1000

# switch stream (S1-based)
me['switch_ret'] = np.where(me.s1, me.fwd_ret300, me.fwd_ret1000)

sample = me.dropna(subset=['diff_bm','s1_pct']).copy()
def stats(x):
    x = x.dropna()
    if len(x) == 0: return dict(n=0)
    return dict(n=int(len(x)), mean=float(x.mean()), win=float((x > 0).mean()),
                t=float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 1 else None)

hi = sample[sample.s1]; lo = sample[~sample.s1]
res = {
 'pe_range': [str(df.index.min().date()), str(df.index.max().date())],
 'sample_months': [str(sample.index.min()), str(sample.index.max())],
 'uncond': stats(sample.diff_bm),
 's1_high': stats(hi.diff_bm), 's1_low': stats(lo.diff_bm),
 's1_high_div': stats(hi.diff_div), 's1_low_div': stats(lo.diff_div),
 's1_high_3m': stats(hi.diff_bm_3m), 's1_low_3m': stats(lo.diff_bm_3m),
 'hi_mean_ret300': stats(hi.fwd_ret300), 'hi_mean_ret1000': stats(hi.fwd_ret1000),
 'lo_mean_ret300': stats(lo.fwd_ret300), 'lo_mean_ret1000': stats(lo.fwd_ret1000),
 'pre': stats(sample[(sample.index <= '2022-12')].query('s1').diff_bm),
 'pre_n_all': int((sample.index <= '2022-12').sum()),
 'post': stats(sample[(sample.index > '2022-12')].query('s1').diff_bm),
 'post_n_all': int((sample.index > '2022-12').sum()),
 'pre_low': stats(sample[(sample.index <= '2022-12')].query('not s1').diff_bm),
 'post_low': stats(sample[(sample.index > '2022-12')].query('not s1').diff_bm),
 'comb': stats(sample[sample.scomb].diff_bm),
 'comb_low': stats(sample[~sample.scomb].diff_bm),
 'comb_hi_ret300': stats(sample[sample.scomb].fwd_ret300),
 'comb_hi_ret1000': stats(sample[sample.scomb].fwd_ret1000),
 'n_s2hi': int(sample.s2.sum()),
 's2_only_hi': stats(sample[sample.s2].diff_bm), 's2_only_lo': stats(sample[~sample.s2].diff_bm),
}
# correlations vs a13
sub = sample.dropna(subset=['a13'])
res['corr_switch_a13'] = float(sub.switch_ret.corr(sub.a13))
res['corr_micro_a13'] = float(sub.fwd_ret1000.corr(sub.a13))
res['corr_300_a13'] = float(sub.fwd_ret300.corr(sub.a13))
res['corr_diff_a13'] = float(sub.diff_bm.corr(sub.a13))
res['corr_n'] = int(len(sub))
res['corr_switch_a13_all'] = float(sample.dropna(subset=['a13']).switch_ret.corr(sample.dropna(subset=['a13']).a13))

# robustness: median / ex-2024 (post-hoc sensitivity, labeled)
hid = hi.diff_bm.dropna()
res['s1_high_median'] = float(hid.median())
res['s1_high_ex2024'] = stats(hi[hi.index.year != 2024].diff_bm)
res['s1_high_ex2024_low'] = stats(lo[lo.index.year != 2024].diff_bm)
res['s1_high_top3'] = sorted([(str(i), round(v,4)) for i,v in hid.items()], key=lambda x:-x[1])[:3]
res['s1_high_bot3'] = sorted([(str(i), round(v,4)) for i,v in hid.items()], key=lambda x:x[1])[:3]

# current state
last = df.dropna(subset=['s1_pct']).iloc[-1]
res['now'] = dict(date=str(last.name.date()), pe1000=float(last.pe1000), pe300=float(last.pe300),
                  spread=float(last.spread), s1_pct=float(last.s1_pct),
                  c_pct=float(me.c_pct.dropna().iloc[-1]))

# high months listing
hm = hi[['s1_pct','c_pct','fwd_ret300','fwd_ret1000','diff_bm']].copy()
res['high_months'] = [(str(i), round(r.s1_pct,2), None if pd.isna(r.c_pct) else round(r.c_pct,2),
                       round(r.fwd_ret300,4), round(r.fwd_ret1000,4), round(r.diff_bm,4)) for i,r in hm.iterrows()]

json.dump(res, open('/tmp/r268/summary.json','w'), ensure_ascii=False, indent=1, default=str)
me.to_csv('/tmp/r268/monthly_panel.csv')
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
