#!/usr/bin/env python3
# task-0609 阶段一: B 配置(a13+真金腿 静态58/42 日频) DDC/vol_target 历史触发校准
# 数据全部本地复用: task-0607/gold_sh518880_daily.csv + 04-投资研究/a13_rsraw_e1f10dz_full_nav.csv
# DDC 权威语义(R-390/R-336§4.4/R-318 F6): ddc_th20_rd50_rc5, 日频 T 收盘判定 T+1 生效
import json
import numpy as np
import pandas as pd

W = '/root/.openclaw/workspace/shared/results/work'
A13 = '/root/.openclaw/workspace/shared/results/04-投资研究/a13_rsraw_e1f10dz_full_nav.csv'
OUT_JSON = f'{W}/task-0609-results.json'

a13 = pd.read_csv(A13, parse_dates=['date']).set_index('date')['nav']
a13.index = pd.to_datetime(a13.index)
a13 = a13[a13.index >= '2013-07-25']
g = pd.read_csv(f'{W}/task-0607/gold_sh518880_daily.csv', parse_dates=['date']).set_index('date')['close']
common = g.index.intersection(a13.index)
a13, g = a13.reindex(common).ffill(), g.reindex(common).ffill()
rA = a13.pct_change().fillna(0.0)
rG = g.pct_change().fillna(0.0)

def mdd(nav):
    dd = nav / nav.cummax() - 1.0
    tr = dd.idxmin()
    return float(dd.min()), nav.loc[:tr].idxmax(), tr

def stats(nav):
    yrs = (nav.index[-1] - nav.index[0]).days / 365.25
    r = nav.pct_change().dropna()
    m, pk, tr = mdd(nav)
    return dict(final=round(float(nav.iloc[-1]), 3), ann=round(float(nav.iloc[-1]) ** (1/yrs) - 1, 4),
                vol=round(float(r.std() * np.sqrt(252)), 4),
                mdd=round(m, 5), dd_win=f'{pk.date()}->{tr.date()}')

def ddc_sim(nav, th=-0.20, rec=-0.05, half=0.5):
    """sleeve DDC: T 收盘判定(对 running_max 回撤 <=th 减半, >=rec 回补), T+1 生效。
    返回 (adj_nav, episodes, states)"""
    dd = nav / nav.cummax() - 1.0
    states, episodes = [], []
    state = 1.0
    cur = None
    for d in nav.index:
        x = dd.loc[d]
        if x <= th:
            if state == 1.0:  # 新触发
                cur = {'trigger_judge': d.date().isoformat(), 'trigger_eff': None,
                       'depth_at_trigger': round(float(x), 4)}
                episodes.append(cur)
            state = half
        elif x >= rec:
            if state == half and cur is not None:
                cur['recover_judge'] = d.date().isoformat()
            state = 1.0
        if state == half and cur is not None and cur.get('trigger_eff') is None and d != cur and True:
            pass
        states.append(state)
    st = pd.Series(states, index=nav.index)
    # T+1 生效: T 日判定的仓位作用于 T+1 收益
    r_adj = nav.pct_change().fillna(0.0) * st.shift(1).fillna(1.0)
    adj = (1 + r_adj).cumprod()
    # 补充每段 episode 的生效日/谷底/回补生效日/减半天数
    halved = st == half
    for i, ep in enumerate(episodes):
        tj = pd.Timestamp(ep['trigger_judge'])
        pos = nav.index.get_loc(tj)
        eff = nav.index[min(pos + 1, len(nav.index) - 1)]
        ep['trigger_eff'] = eff.date().isoformat()
        seg = nav.loc[eff:]
        end = pd.Timestamp(ep['recover_judge']) if ep.get('recover_judge') else nav.index[-1]
        seg = seg.loc[:end]
        dd_seg = seg / seg.cummax() - 1.0
        ep['trough'] = dd_seg.idxmin().date().isoformat()
        ep['trough_dd'] = round(float(dd_seg.min()), 4)
        if ep.get('recover_judge'):
            rj = pd.Timestamp(ep['recover_judge'])
            ep['recover_eff'] = nav.index[min(nav.index.get_loc(rj) + 1, len(nav.index) - 1)].date().isoformat()
        else:
            ep['recover_judge'] = None
            ep['note'] = '样本末仍处减半状态'
        ep['halved_days'] = int(halved.loc[eff:end].sum())
    return adj, episodes, st

res = {'window': dict(first=str(common[0].date()), last=str(common[-1].date()), n=int(len(common)))}

# ---------- ① 单腿 DDC ----------
for tag, nav in [('a13', a13), ('gold', g)]:
    adj, eps, _ = ddc_sim(nav)
    base, adj_s = stats(nav / nav.iloc[0]), stats(adj / adj.iloc[0])
    res[f'ddc_{tag}_leg'] = dict(baseline=base, with_ddc=adj_s, n_episodes=len(eps), episodes=eps)

# ---------- ② 组合(58/42 月初再平衡, 腿级 DDC 已应用) ----------
def portfolio(rA_, rG_, wA0=0.58):
    navP, navs = 1.0, []
    wA, wG = wA0, 1 - wA0
    prev_month = None
    for t in common:
        if prev_month is not None and t.month != prev_month:
            wA, wG = wA0, 1 - wA0
        gA, gG = (1 + rA_.loc[t]) * wA, (1 + rG_.loc[t]) * wG
        navP *= (gA + gG)
        navs.append(navP)
        prev_month = t.month
    return pd.Series(navs, index=common)

adjA, epsA, _ = ddc_sim(a13)
adjG, epsG, _ = ddc_sim(g)
rA_adj = a13.pct_change().fillna(0.0) * (_ if False else 1.0)  # placeholder
# 重新导出各腿已调整日收益(ddc_sim 内部逻辑): states shift(1)
def adj_returns(nav):
    dd = nav / nav.cummax() - 1.0
    state, states = 1.0, []
    for d in nav.index:
        x = dd.loc[d]
        state = 0.5 if x <= -0.20 else (1.0 if x >= -0.05 else state)
        states.append(state)
    st = pd.Series(states, index=nav.index)
    return nav.pct_change().fillna(0.0) * st.shift(1).fillna(1.0)

rA_adj, rG_adj = adj_returns(a13), adj_returns(g)
p_base = portfolio(rA, rG)
p_ddc = portfolio(rA_adj, rG_adj)
res['portfolio_5842'] = dict(baseline=stats(p_base), with_sleeve_ddc=stats(p_ddc),
                             n_ddc_episodes_a13=len(epsA), n_ddc_episodes_gold=len(epsG))

# ---------- ③ 组合级回撤四带天数分布(呈现带, R-336§4.4) ----------
dd_p = p_base / p_base.cummax() - 1.0
bands = {'normal_<5pct': int((dd_p > -0.05).sum()), 'esc_5-10': int(((dd_p <= -0.05) & (dd_p > -0.10)).sum()),
         'cut_10-15': int(((dd_p <= -0.10) & (dd_p > -0.15)).sum()), 'cb_>15': int((dd_p <= -0.15).sum())}
res['portfolio_dd_bands_days'] = bands

# ---------- ④ 组合级 vol_target 校准(8%±2pp, 20d/60d 滚动实现波动率) ----------
rP = p_base.pct_change().fillna(0.0)
def vol_calib(win):
    rv = rP.rolling(win).std() * np.sqrt(252)
    rv = rv.dropna()
    above, below, inside = rv > 0.10, rv < 0.06, (rv >= 0.06) & (rv <= 0.10)
    def eps_count(mask):
        m = mask.astype(int).diff().fillna(0)
        return int((m == 1).sum())
    # vol targeting: exposure = clip(0.08/rv, 0, 1), T 收盘计算 T+1 生效
    expo = (0.08 / rv).clip(0, 1)
    r_adj = rP.reindex(rv.index) * expo.shift(1).fillna(1.0)
    nav_adj = (1 + r_adj).cumprod()
    st = stats(nav_adj)
    return dict(rv_last=round(float(rv.iloc[-1]), 4),
                days_above10=int(above.sum()), days_below6=int(below.sum()), days_in_band=int(inside.sum()),
                share_in_band=round(float(inside.mean()), 3),
                breach_episodes_above=eps_count(above), breach_episodes_below=eps_count(below),
                longest_above_days=int(above.astype(int).groupby((above != above.shift()).cumsum()).sum().max()) if above.any() else 0,
                targeted=st)
res['vol_target'] = {'win20': vol_calib(20), 'win60': vol_calib(60),
                     'note': '带宽6-10%无文档出处(R-388发现), 8%目标同待确认; targeting expo=clip(8%/rv,0,1) T+1生效'}

# ---------- ⑤ DDC+vol_target 组合效果(20d, 供阈值校准输入) ----------
rv20 = rP.rolling(20).std() * np.sqrt(252)
expo_v = (0.08 / rv20).clip(0, 1).reindex(p_base.index)
r_ddc_v = rP * expo_v.shift(1).fillna(1.0)
# 注意: 此处 vol targeting 作用于已含腿级DDC的组合收益
rP_ddc = p_ddc.pct_change().fillna(0.0)
rv20b = rP_ddc.rolling(20).std() * np.sqrt(252)
expo_vb = (0.08 / rv20b).clip(0, 1)
r_both = rP_ddc * expo_vb.shift(1).fillna(1.0)
res['combined'] = dict(ddc_then_vol20=stats((1 + r_both).cumprod()),
                       vol20_on_raw=stats((1 + r_ddc_v).cumprod()))

json.dump(res, open(OUT_JSON, 'w'), ensure_ascii=False, indent=1, default=str)
print('saved', OUT_JSON, 'size', __import__('os').path.getsize(OUT_JSON))
for k in ['window', 'ddc_a13_leg', 'ddc_gold_leg', 'portfolio_5842', 'portfolio_dd_bands_days', 'vol_target', 'combined']:
    v = res[k]
    if k.startswith('ddc_'):
        print(k, 'eps=', v['n_episodes'], 'base_mdd=', v['baseline']['mdd'], 'ddc_mdd=', v['with_ddc']['mdd'],
              'base_final=', v['baseline']['final'], 'ddc_final=', v['with_ddc']['final'])
    elif k == 'portfolio_5842':
        print(k, 'base=', {x: v['baseline'][x] for x in ['mdd', 'final', 'vol']},
              'ddc=', {x: v['with_sleeve_ddc'][x] for x in ['mdd', 'final', 'vol']})
    elif k == 'vol_target':
        for w2 in ['win20', 'win60']:
            print(w2, {x: v[w2][x] for x in ['days_above10', 'days_below6', 'days_in_band', 'breach_episodes_above']})
    else:
        print(k, v)
