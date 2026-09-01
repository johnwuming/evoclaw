#!/usr/bin/env python3
# task-0611: 金腿 DDC 2026-03-23 触发真伪独立复算（只读本地数据，零 HP 写入）
# 数据: task-0607/gold_sh518880_daily.csv (sh518880 qfq 日线, R-390/R-392 同源)
#       04-投资研究/a13_rsraw_e1f10dz_full_nav.csv (a13 日频 NAV)
#       04-投资研究/engines/gold/shadow_nav.csv + work/task-0606-nav-true.csv (gold 引擎月频账本/反事实)
# DDC 语义(R-390§三/R-392): ddc_th20_rd50_rc5, 腿NAV对running_max, <=-20%减半, >=-5%回补, T判定T+1生效
import json
import numpy as np
import pandas as pd

R = '/root/.openclaw/workspace/shared/results'
W = f'{R}/work'
out = {}

g = pd.read_csv(f'{W}/task-0607/gold_sh518880_daily.csv', parse_dates=['date']).set_index('date')['close'].sort_index()
a13 = pd.read_csv(f'{R}/04-投资研究/a13_rsraw_e1f10dz_full_nav.csv', parse_dates=['date']).set_index('date')['nav'].sort_index()
sn = pd.read_csv(f'{R}/04-投资研究/engines/gold/shadow_nav.csv')
nt = pd.read_csv(f'{W}/task-0606-nav-true.csv', index_col=0)

def dds(s):
    return s / s.cummax() - 1.0

def full_mdd(s):
    dd = dds(s)
    tr = dd.idxmin()
    pk = s.loc[:tr].idxmax()
    return dict(depth=round(float(dd.min()), 5), peak=str(pk.date()), peak_px=round(float(s.loc[pk]), 4),
                trough=str(tr.date()), trough_px=round(float(s.loc[tr]), 4))

def episodes(s, th=-0.20, rec=-0.05):
    dd = dds(s)
    eps, state, cur = [], 1.0, None
    for d, x in dd.items():
        if x <= th:
            if state == 1.0:
                pk = s.loc[:d].idxmax()
                cur = dict(trigger_judge=str(d.date()), dd_at_trigger=round(float(x), 5),
                           peak_date=str(pk.date()), peak_px=round(float(s.loc[pk]), 4),
                           close_at_trigger=round(float(s.loc[d]), 4))
                eps.append(cur)
            state = 0.5
        elif x >= rec:
            if state == 0.5 and cur is not None and 'recover_judge' not in cur:
                cur['recover_judge'] = str(d.date())
            state = 1.0
    for c in eps:
        tj = pd.Timestamp(c['trigger_judge'])
        i = s.index.get_loc(tj)
        c['effective_T1'] = str(s.index[min(i + 1, len(s.index) - 1)].date())
        end = pd.Timestamp(c['recover_judge']) if c.get('recover_judge') else s.index[-1]
        seg = dds(s.loc[s.index[min(i + 1, len(s.index) - 1)]:end])
        ti = seg.idxmin()
        c.update(trough_date=str(ti.date()), trough_px=round(float(s.loc[ti]), 4), trough_dd=round(float(seg.min()), 5))
        if not c.get('recover_judge'):
            c['status'] = 'still_halved_at_sample_end'
    return eps

# ① 真金裸价 全期 MDD + DDC episodes
out['gold_window'] = dict(first=str(g.index[0].date()), last=str(g.index[-1].date()), n=int(len(g)))
out['gold_bare_full_mdd'] = full_mdd(g)
out['gold_ddc_episodes'] = episodes(g)

# ② 2026-03-23 专项
d = pd.Timestamp('2026-03-23')
ddg = dds(g)
assert d in g.index, '2026-03-23 非交易日'
pk = ddg.loc[:d].idxmax()
out['gold_20260323'] = dict(close=round(float(g.loc[d]), 4), dd_vs_running_max=round(float(ddg.loc[d]), 5),
                            peak_date=str(pk.date()), peak_px=round(float(g.loc[pk]), 4),
                            breach_le_20pct=bool(ddg.loc[d] <= -0.20))
# 月末采样对照（同一裸价序列）
gm = g.resample('ME').last().dropna()
out['gold_monthend_mdd'] = full_mdd(gm)
gmdd = dds(gm)
m03 = pd.Timestamp('2026-03-31')
out['gold_monthend_2026_dd'] = {str(t.date()): round(float(gmdd.loc[t]), 5)
                                for t in [pd.Timestamp(x) for x in ['2026-01-31', '2026-02-28', '2026-03-31', '2026-04-30', '2026-05-31', '2026-06-30']] if t in gmdd.index}

# ③ a13 腿复核
dda = dds(a13)
t = pd.Timestamp('2015-06-29')
out['a13_window'] = dict(first=str(a13.index[0].date()), last=str(a13.index[-1].date()), n=int(len(a13)))
out['a13_20150629'] = dict(nav=round(float(a13.loc[t]), 4), dd_vs_running_max=round(float(dda.loc[t]), 5),
                           breach_le_20pct=bool(dda.loc[t] <= -0.20))
out['a13_full_mdd'] = full_mdd(a13)
out['a13_ddc_episodes'] = episodes(a13)

# ④ 引擎月频账本 vs 反事实 MDD（5.90/8.09 复算）
def m_mdd(nav):
    nav = nav.sort_index()
    dd = nav / nav.cummax() - 1.0
    tr = dd.idxmin()
    return dict(depth=round(float(dd.min()), 5), trough=str(pd.Timestamp(tr).date()))
out['engine_ledger_mdd'] = m_mdd(sn['nav'])
out['engine_true_mdd'] = m_mdd(nt['nav_true'])
out['engine_2026'] = sn[sn['month'] >= '2026-01'][['month', 'w_applied', 'gold_ret', 'net', 'nav']].round(6).to_dict('records')
nt26 = nt[nt.index >= '2026-01']
out['engine_true_2026_nav'] = {str(pd.Timestamp(k).date()): round(float(v), 4) for k, v in nt26['nav_true'].items()}

# ⑤ 8 月 px 时点核验（task-0608 附注用事实）
px0731 = float(g.loc['2026-07-31'])
px0828 = float(g.loc['2026-08-28'])
px0831 = float(g.loc['2026-08-31']) if pd.Timestamp('2026-08-31') in g.index else None
sma28 = round(float(g.loc[:'2026-08-28'].rolling(200).mean().iloc[-1]), 4)
sma31 = round(float(g.loc[:'2026-08-31'].rolling(200).mean().iloc[-1]), 4) if px0831 else None
out['aug_px_check'] = dict(px_0731=round(px0731, 4), px_0828=round(px0828, 4), px_0831=px0831,
                           ret_0831_vs_0731=round(px0831 / px0731 - 1, 6) if px0831 else None,
                           ret_0828_vs_0731=round(px0828 / px0731 - 1, 6),
                           ledger_aug_gold_ret=float(sn.loc[sn['month'] == '2026-08-31', 'gold_ret'].iloc[0]),
                           sma200_asof_0828=sma28, sma200_asof_0831=sma31,
                           dow_0831=pd.Timestamp('2026-08-31').day_name())

with open(f'{W}/task-0611-results.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, indent=1, default=str)[:3500])
