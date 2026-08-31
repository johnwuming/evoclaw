#!/usr/bin/env python3
# task-0607: 静态58/42两腿(a13+金) 月末采样 vs 日频 MDD 低估系数 + 金腿单独口径
# 金腿数据源: 腾讯公开接口 sh518880 qfq 日线(静态权重+原始价格收益重建, 非在役信号路径)
import json, urllib.request, time
import pandas as pd

OUT = '/root/.openclaw/workspace/shared/results/work/task-0607'
A13 = '/root/.openclaw/workspace/shared/results/04-投资研究/a13_rsraw_e1f10dz_full_nav.csv'

# ---------- ① 金腿日频重建(分页) ----------
def fetch_gold():
    rows, end = [], '2026-08-31'
    start = '2013-07-01'
    for _ in range(30):
        url = (f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?'
               f'param=sh518880,day,{start},{end},640,qfq')
        with urllib.request.urlopen(url, timeout=20) as r:
            d = json.loads(r.read().decode())
        data = d['data']['sh518880']
        chunk = data.get('qfqday') or data.get('day')
        rows = chunk + rows
        first = chunk[0][0]
        if chunk[0][0] <= start or len(chunk) < 640:
            break
        end = first  # 游标回退
        time.sleep(0.4)
    df = pd.DataFrame([(r[0], float(r[2])) for r in rows], columns=['date', 'close'])
    df = df.drop_duplicates('date').sort_values('date').reset_index(drop=True)
    df.to_csv(f'{OUT}/gold_sh518880_daily.csv', index=False)
    return df

gold = fetch_gold()
print('gold rows', len(gold), gold['date'].iloc[0], '->', gold['date'].iloc[-1])

# ---------- ② 对齐 a13 日频 ----------
a13 = pd.read_csv(A13, parse_dates=['date']).set_index('date')['nav']
g = gold.set_index(pd.to_datetime(gold['date']))['close']
a13.index = pd.to_datetime(a13.index)
# 有效段: a13 策略起点 2013-07-31(0602 口径), 截至两序列共同末日
a13 = a13[a13.index >= '2013-07-25']
common_idx = g.index.intersection(a13.index)
a13, g = a13.reindex(common_idx).ffill(), g.reindex(common_idx).ffill()
print('common', common_idx[0].date(), '->', common_idx[-1].date(), 'n=', len(common_idx))

rA = a13.pct_change().fillna(0.0)   # a13 腿日收益(在役策略净值, 已含信号)
rG = g.pct_change().fillna(0.0)     # 金腿日收益(原始价格, 非信号)

def mdd_from(nav):
    peak = nav.cummax()
    dd = nav / peak - 1.0
    trough = dd.idxmin()
    peak_d = nav.loc[:trough].idxmax()
    return dd.min(), peak_d, trough

def portfolio(wA0=0.58, end=None):
    """月末再平衡 + 日频逐日估值; 返回日频 nav 与月末采样 nav"""
    idx = common_idx if end is None else common_idx[common_idx <= pd.Timestamp(end)]
    rA_, rG_ = rA.reindex(idx).fillna(0.0), rG.reindex(idx).fillna(0.0)
    navA, navG, navPs = [], [], []
    navP = 1.0
    wA, wG = wA0, 1 - wA0
    prev_month = None
    for t in idx:
        if prev_month is not None and t.month != prev_month:  # 新月初=上月末收盘后再平衡
            wA, wG = wA0, 1 - wA0
        # 当日各腿增长
        gA, gG = (1 + rA_.loc[t]) * wA, (1 + rG_.loc[t]) * wG
        navP = navP * (gA + gG)
        navPs.append(navP)
        navA.append(gA / (gA + gG))  # 期末漂移权重
        navG.append(gG / (gA + gG))
        prev_month = t.month
    daily = pd.Series(navPs, index=idx)
    me = daily.groupby(idx.to_period('M')).last()
    return daily, me

res = {}
for tag, end in [('display', '2026-07-31'), ('full', None)]:
    daily, me = portfolio(end=end)
    md_d, pk_d, tr_d = mdd_from(daily)
    md_m, pk_m, tr_m = mdd_from(me)
    n_years = (idx_last := daily.index[-1]) and (daily.index[-1] - daily.index[0]).days / 365.25
    ann_d = daily.iloc[-1] ** (1 / n_years) - 1
    vol_d = daily.pct_change().std() * (252 ** 0.5)
    vol_m = me.pct_change().std() * (12 ** 0.5)
    ann_m = me.iloc[-1] ** (1 / n_years) - 1
    res[f'p5842_{tag}'] = dict(
        first=str(daily.index[0].date()), last=str(daily.index[-1].date()), n_days=len(daily),
        daily_mdd=round(md_d, 5), daily_dd=f'{pk_d.date()}->{tr_d.date()}',
        monthend_mdd=round(md_m, 5), monthend_dd=f'{str(pk_m)[-6:]}->{str(tr_m)[-6:]}',
        coef=round(abs(md_d / md_m), 3),
        daily_ann=round(ann_d, 4), daily_vol=round(vol_d, 4),
        monthend_ann=round(ann_m, 4), monthend_vol=round(vol_m, 4), final=round(daily.iloc[-1], 3))

# 金腿单独: 月末采样 vs 日频
gm = g.groupby(g.index.to_period('M')).last()
md_gd, pk, tr = mdd_from(g / g.iloc[0])
md_gm, pk2, tr2 = mdd_from(gm / gm.iloc[0])
res['gold_leg'] = dict(daily_mdd=round(md_gd, 5), monthend_mdd=round(md_gm, 5),
                       coef=round(abs(md_gd / md_gm), 3),
                       daily_dd=f'{pk.date()}->{tr.date()}', monthend_dd=f'{str(pk2)[-6:]}->{str(tr2)[-6:]}',
                       first=str(g.index[0].date()), last=str(g.index[-1].date()))

# a13 腿单独(共同窗口内复核 0602)
am = a13.groupby(a13.index.to_period('M')).last()
md_ad, _, _ = mdd_from(a13 / a13.iloc[0])
md_am, _, _ = mdd_from(am / am.iloc[0])
res['a13_leg_common_win'] = dict(daily_mdd=round(md_ad, 5), monthend_mdd=round(md_am, 5),
                                 coef=round(abs(md_ad / md_am), 3))

json.dump(res, open(f'{OUT}/compute_results.json', 'w'), ensure_ascii=False, indent=1)
daily_full, _ = portfolio(end=None)
daily_full.to_csv(f'{OUT}/p5842_daily_nav.csv')
for k, v in res.items():
    print(k, v)
