#!/usr/bin/env python3
# task-0456 E1 触发普查 + 前瞻胜率 + PIT 月度 + q3z 重合
import pandas as pd, numpy as np, json

D = '/root/.openclaw/workspace/shared/results/work/task-0456-data'
df = pd.read_csv(f'{D}/excess_decay_daily.csv', parse_dates=['date']).set_index('date')
df['micro_ret'] = df.micro_eqw.pct_change()
df['hs_ret'] = df.hs300.pct_change()
df['excess'] = (df.micro_ret - df.hs_ret).fillna(0.0)
H = [21, 42, 63]
for h in H:
    df[f'fwd{h}'] = (1 + df.excess).shift(-1).rolling(h).apply(lambda x: np.prod(1+x), raw=True).shift(-(h-1)) - 1
    # 上式等价 prod(1+excess[t+1..t+h])-1

def census(sub, label):
    red = (sub.flag == 'red').values
    # episode: 连续 red 段
    eps = []
    i = 0
    n = len(sub)
    while i < n:
        if red[i]:
            j = i
            while j + 1 < n and red[j + 1]:
                j += 1
            eps.append((sub.index[i], sub.index[j], j - i + 1))
            i = j + 1
        else:
            i += 1
    rows = []
    for s, e, nd in eps:
        r = {'ep_start': s.strftime('%Y-%m-%d'), 'ep_end': e.strftime('%Y-%m-%d'), 'days': nd,
             'tstat_first': float(sub.tstat_60d.loc[s])}
        for h in H:
            r[f'fwd{h}'] = None if np.isnan(sub[f'fwd{h}'].loc[e]) else round(float(sub[f'fwd{h}'].loc[e]), 4)
            # 用 episode 末日（PIT 更保守：整个 episode 结束才确认）取前瞻
        rows.append(r)
    ep = pd.DataFrame(rows)
    ep.to_csv(f'{D}/red_episodes_{label}.csv', index=False)
    # 胜率：两种口径——episode 首日触发、episode 末日确认
    res = {'label': label, 'n_red_days': int(red.sum()), 'n_days': n, 'n_episodes': len(eps)}
    for anchor, name in [(0, 'first'), (1, 'last')]:
        vals = {h: [] for h in H}
        for s, e, nd in eps:
            t = s if anchor == 0 else e
            for h in H:
                v = sub[f'fwd{h}'].loc[t]
                if not np.isnan(v):
                    vals[h].append(v)
        res[name] = {h: {'n': len(vals[h]),
                         'mean': round(float(np.mean(vals[h])), 4) if vals[h] else None,
                         'win': round(float(np.mean([v > 0 for v in vals[h]])), 3) if vals[h] else None} for h in H}
    # 无条件基准（全样本日）
    base = {h: {'n': int(sub[f'fwd{h}'].notna().sum()),
                'mean': round(float(sub[f'fwd{h}'].mean()), 4),
                'win': round(float((sub[f'fwd{h}'].dropna() > 0).mean()), 3)} for h in H}
    res['baseline_alldays'] = base
    return res, ep

r19, ep19 = census(df[df.index >= '2019-01-01'], '2019plus')
r15, ep15 = census(df, '2015plus')
print(json.dumps(r19, ensure_ascii=False, indent=1))
print(json.dumps(r15, ensure_ascii=False, indent=1))

# PIT 月度：月末定值，次月超额
m = df.resample('ME').last().copy()
m['next_m_excess'] = (1 + df.excess).resample('ME').apply(lambda x: np.prod(1 + x) - 1).shift(-1)
m['red_me'] = m.flag == 'red'
m19 = m[m.index >= '2019-01-01']
pit = {'n_months': int(len(m19)), 'n_red_me': int(m19.red_me.sum()),
       'red_next_mean': round(float(m19.loc[m19.red_me, 'next_m_excess'].mean()), 4),
       'red_next_win': round(float((m19.loc[m19.red_me, 'next_m_excess'] > 0).mean()), 3),
       'all_next_mean': round(float(m19.next_m_excess.mean()), 4),
       'all_next_win': round(float((m19.next_m_excess.dropna() > 0).mean()), 3),
       'green_next_mean': round(float(m19.loc[~m19.red_me, 'next_m_excess'].mean()), 4),
       'green_next_win': round(float((m19.loc[~m19.red_me, 'next_m_excess'] > 0).mean()), 3)}
red_months = m19[m19.red_me]
# 连续 red 月段（episode 化）
grp = (m19.red_me != m19.red_me.shift()).cumsum()
runs = m19[m19.red_me].groupby(grp[m19.red_me])
pit['red_month_runs'] = [{'start': g.index[0].strftime('%Y-%m'), 'end': g.index[-1].strftime('%Y-%m'), 'n': len(g)} for _, g in runs]
print(json.dumps(pit, ensure_ascii=False))
json.dump({'daily_2019': r19, 'daily_2015': r15, 'pit_monthly_2019': pit}, open(f'{D}/census_summary.json', 'w'), ensure_ascii=False, indent=1)

# q3z 重合（tail 24 个月）
q = pd.read_csv(f'{D}/q3z_pos_ratio_tail24.csv', parse_dates=['month_end'])
q['red_me'] = q.month_end.map(lambda d: bool(m.loc[m.index == d, 'red_me'].iloc[0]) if d in m.index else None)
q['next_m_excess'] = q.month_end.map(lambda d: float(m.loc[m.index == d, 'next_m_excess'].iloc[0]) if d in m.index else None)
q.to_csv(f'{D}/q3z_overlap_tail24.csv', index=False)
sub = q.dropna(subset=['red_me'])
ov = {'n_overlap_months': int(len(sub)), 'red_months': int(sub.red_me.sum()),
      'corr_red_vs_posratio': round(float(np.corrcoef(sub.red_me.astype(float), sub.pos_ratio)[0, 1]), 3),
      'red_and_lowpos': int(((sub.red_me) & (sub.pos_ratio < 0.6)).sum()),
      'red_and_highpos': int(((sub.red_me) & (sub.pos_ratio >= 0.6)).sum()),
      'mean_next_excess_red_lowpos': round(float(sub.loc[sub.red_me & (sub.pos_ratio < 0.6), 'next_m_excess'].mean()), 4) if (sub.red_me & (sub.pos_ratio < 0.6)).any() else None,
      'mean_next_excess_red_highpos': round(float(sub.loc[sub.red_me & (sub.pos_ratio >= 0.6), 'next_m_excess'].mean()), 4) if (sub.red_me & (sub.pos_ratio >= 0.6)).any() else None}
print(json.dumps(ov, ensure_ascii=False))
json.dump(ov, open(f'{D}/q3z_overlap_summary.json', 'w'), ensure_ascii=False, indent=1)
