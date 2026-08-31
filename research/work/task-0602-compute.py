#!/usr/bin/env python3
"""task-0602: runtime 实仓组合真实回撤审计 + 四基线对齐（R-387）
只读本地数据；复用 task-0591 引擎语义（锚点先复现再算 runtime 变体）。
runtime 组合 = 微盘腿(a13_rsraw_e1f10dz) ~60% + 现金 ~40%（现金日收益按 0，如实披露）。
产物: /tmp/task-0602-results.json + work/task-0602-results.json
"""
import pandas as pd, numpy as np, json

CSV = '/root/.openclaw/workspace/tools/quant-bff/live/data/nav_curves.csv'
A13 = '/root/.openclaw/workspace/shared/results/04-投资研究/a13_rsraw_e1f10dz_full_nav.csv'
PAPER = '/root/.openclaw/workspace/shared/results/04-投资研究/baseline-paper-nav.csv'
DRYRUN_WA, DRYRUN_WG = 0.5802970, 0.4197030
COST = 0.0013
out = {}

# ---------- 月频：锚点复现 + runtime 变体 ----------
df = pd.read_csv(CSV, parse_dates=['month']).set_index('month')
rA = df['A'].pct_change().fillna(df['A'] - 1.0)
rG = df['gold'].pct_change().fillna(df['gold'] - 1.0)
n = len(df); rAv = rA.values; rGv = rG.values; months = list(df.index)
rCash = np.zeros(n)  # 现金腿日/月收益按 0

def m_metrics(rp, periods_per_year=12):
    nav = (1 + rp).cumprod()
    yrs = len(rp) / periods_per_year
    ann = nav.iloc[-1] ** (1 / yrs) - 1
    vol = rp.std(ddof=1) * np.sqrt(periods_per_year)
    s = pd.concat([pd.Series([1.0]), nav.reset_index(drop=True)])
    dd = s / s.cummax() - 1
    ti = int(dd.idxmin()); pi = int(s.iloc[:ti + 1].idxmax())
    ri = next((i for i in range(ti, len(s)) if s.iloc[i] >= s.iloc[pi]), None)
    dt = lambda i: 'BASE' if i == 0 else str(months[i - 1].date())
    return dict(ann=round(float(ann), 6), vol=round(float(vol), 6),
                sharpe=round(float(ann / vol), 4), mdd=round(float(dd.min()), 6),
                final=round(float(nav.iloc[-1]), 6),
                dd_peak=dt(pi), dd_trough=dt(ti),
                dd_recovery=dt(ri) if ri is not None else '未修复')

def run_static(wA, r_leg, cost_on_leg=True, rebal=True):
    """静态 wA/1-wA；cost 只按 |ΔwA| 计（现金腿无交易成本）；rebal=False 即买入持有漂移"""
    w = np.nan; rp = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(w):
            w = wA; cost = COST * abs(wA) if cost_on_leg else 0.0
        elif rebal:
            cost = COST * abs(wA - w) if cost_on_leg else 0.0; w = wA
        else:
            cost = 0.0
        rp[i] = w * r_leg[i] + (1 - w) * 0 - cost
        m = 1 + w * r_leg[i]
        w = w * (1 + r_leg[i]) / m
    return pd.Series(rp, index=df.index)

# 锚点①：展示口径 静态58/42 月度再平衡（双腿含成本，逐行同 task-0591）
def run_engine_two_leg(target, rebal_mask):
    wA = wG = np.nan; rp = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(wA):
            wA, wG = target(i); cost = COST * (abs(wA) + abs(wG))
        elif rebal_mask[i]:
            tA, tG = target(i); cost = COST * (abs(tA - wA) + abs(tG - wG)); wA, wG = tA, tG
        else:
            cost = 0.0
        rp[i] = wA * rAv[i] + wG * rGv[i] - cost
        m = 1 + wA * rAv[i] + wG * rGv[i]
        wA, wG = wA * (1 + rAv[i]) / m, wG * (1 + rGv[i]) / m
    return pd.Series(rp, index=df.index)

m_disp = m_metrics(run_engine_two_leg(lambda i: (DRYRUN_WA, DRYRUN_WG), np.ones(n, dtype=bool)))
assert abs(m_disp['ann'] - .1444) <= .002 and abs(m_disp['mdd'] + .0969) <= .002, '锚点①失败'
out['baseline1_display_5842'] = m_disp

# 锚点②：滚动等波动 6m band0.02（双腿含成本）
BAND, WIN = 0.02, 6
def eqvol(i):
    if i < 4: return (.5, .5)
    a = rAv[max(0, i - WIN):i]; g = rGv[max(0, i - WIN):i]
    sA = a.std(ddof=1) * np.sqrt(12); sG = g.std(ddof=1) * np.sqrt(12)
    if not (np.isfinite(sA) and np.isfinite(sG)) or sA <= 0 or sG <= 0: return (.5, .5)
    wA = (1 / sA) / (1 / sA + 1 / sG); return (float(wA), float(1 - wA))
wA_ = wG_ = np.nan; rp = np.full(n, np.nan)
for i in range(n):
    tA, tG = eqvol(i)
    if np.isnan(wA_): wA_, wG_ = tA, tG; cost = COST * (abs(tA) + abs(tG))
    elif abs(tA - wA_) > BAND or abs(tG - wG_) > BAND:
        cost = COST * (abs(tA - wA_) + abs(tG - wG_)); wA_, wG_ = tA, tG
    else: cost = 0.0
    rp[i] = wA_ * rAv[i] + wG_ * rGv[i] - cost
    m = 1 + wA_ * rAv[i] + wG_ * rGv[i]
    wA_, wG_ = wA_ * (1 + rAv[i]) / m, wG_ * (1 + rGv[i]) / m
m_roll = m_metrics(pd.Series(rp, index=df.index))
assert abs(m_roll['ann'] - .1012) <= .002 and abs(m_roll['mdd'] + .0571) <= .002, '锚点②失败'
out['baseline2_roll6m'] = m_roll

# ④ runtime 变体（月频，同窗 2013-08..2026-07，现金=0）
out['runtime_w60_rebal'] = m_metrics(run_static(0.60, rAv, cost_on_leg=True, rebal=True))
out['runtime_w60_rebal_nocost'] = m_metrics(run_static(0.60, rAv, cost_on_leg=False, rebal=True))
out['runtime_w5961_rebal'] = m_metrics(run_static(0.59607, rAv, cost_on_leg=True, rebal=True))
out['runtime_w60_bh'] = m_metrics(run_static(0.60, rAv, cost_on_leg=True, rebal=False))
out['runtime_w606_rebal'] = m_metrics(run_static(0.606, rAv, cost_on_leg=True, rebal=True))
# 敏感性：窗口尾部外推一行（用 A 腿 2026-08 = 08-14/07-31 的 R-372 口径）不inker——保持同窗可比，不做

# A 腿单独（买入持有口径）
s = pd.concat([pd.Series([1.0]), df['A'].reset_index(drop=True)])
ddA = s / s.cummax() - 1
out['legA_monthly'] = dict(ann=round(float(df['A'].iloc[-1] ** (1 / (n / 12)) - 1), 6),
                           vol=round(float(df['A'].pct_change().iloc[1:].std(ddof=1) * np.sqrt(12)), 6),
                           mdd=round(float(ddA.min()), 6))

# 一致性核验：nav_curves A 列 vs a13 日频引擎月末值（应为恒定比例）
a13 = pd.read_csv(A13, parse_dates=['date']).set_index('date')['nav']
a13_me = a13.resample('M').last()
ratios = []
for d in ['2013-08-31', '2015-08-31', '2020-08-31', '2026-07-31']:
    ts = pd.Timestamp(d)
    if len(a13_me[:ts]) and len(df[:ts]):
        ratios.append(round(float(df.loc[:ts, 'A'].iloc[-1] / a13_me[:ts].iloc[-1]), 6))
out['A_vs_a13_ratio_check'] = ratios  # 恒定 => 同一条腿

# ---------- 日频 runtime 直算（微盘腿 0.60 + 现金 0.40，月末再平衡，权益腿换手计成本） ----------
nav_d = a13[a13.index >= '2013-08-30']
rd = nav_d.pct_change().fillna(nav_d.iloc[0] / 1.0 - 1.0)  # 首日以 1 为基
# 对齐 R-380 展示窗：2013-08-30..2026-07-31；以及 R-372 全窗：..2026-08-14
def daily_runtime(nav_series, wA=0.60, end=None):
    s = nav_series if end is None else nav_series[:end]
    r = s.pct_change().fillna(s.iloc[0] / 1.0 - 1.0)
    w = wA; rp = []
    rebal_dates = set(pd.Series(s.index).dt.to_period('M').drop_duplicates().index)
    prev_month = None
    for dt_, rr in r.items():
        cur_m = dt_.to_period('M')
        if prev_month is not None and cur_m != prev_month:
            cost = COST * abs(wA - w); w = wA
        else:
            cost = COST * abs(wA) if prev_month is None else 0.0
        rp.append(w * rr - cost)
        w = w * (1 + rr) / (1 + w * rr)
        prev_month = cur_m
    rp = pd.Series(rp, index=r.index)
    navp = (1 + rp).cumprod()
    yrs = len(rp) / 244.0  # A股年交易日约244
    ann = navp.iloc[-1] ** (1 / yrs) - 1
    vol = rp.std(ddof=1) * np.sqrt(244)
    dd = navp / navp.cummax() - 1
    ti = dd.idxmin(); pi = navp[:ti].idxmax() if navp[:ti].size else navp.index[0]
    if dd.loc[pi] < 0 or navp[ti] >= navp[pi]: pass
    after = dd.loc[ti:]
    ri = next((d_ for d_ in after.index if navp[d_] >= navp[pi]), None)
    return dict(ann=round(float(ann), 6), vol=round(float(vol), 6),
                sharpe=round(float(ann / vol), 4), mdd=round(float(dd.min()), 6),
                final=round(float(navp.iloc[-1]), 6),
                dd_peak=str(pi.date()), dd_trough=str(ti.date()),
                dd_recovery=str(ri.date()) if ri is not None else '未修复',
                n_days=len(rp), first=str(r.index[0].date()), last=str(r.index[-1].date()))

out['runtime_daily_w60_display_win'] = daily_runtime(nav_d, 0.60, '2026-07-31')
out['runtime_daily_w60_full_win'] = daily_runtime(nav_d, 0.60, None)  # 2013-08-30..2026-08-14
# 引擎裸腿日频（对照）
def daily_leg(nav_series, end=None):
    s = nav_series if end is None else nav_series[:end]
    navl = s / s.iloc[0]
    r = navl.pct_change().fillna(navl.iloc[0] - 1.0)
    yrs = len(r) / 244.0
    dd = navl / navl.cummax() - 1
    return dict(ann=round(float(navl.iloc[-1] ** (1 / yrs) - 1), 6),
                vol=round(float(r.std(ddof=1) * np.sqrt(244)), 6),
                mdd=round(float(dd.min()), 6),
                dd_trough=str(dd.idxmin().date()), n_days=len(r))
out['legA_daily_display_win'] = daily_leg(nav_d, '2026-07-31')
out['legA_daily_full_win'] = daily_leg(nav_d, None)

# ---------- ④a 实际运行窗口（baseline-paper-nav.csv，真实 runtime 镜像账户，12 个交易日） ----------
pp = pd.read_csv(PAPER, parse_dates=['date']).set_index('date')['nav']
rp_p = pp.pct_change().dropna()
navp = pp / pp.iloc[0]
dd = navp / navp.cummax() - 1
yrs_p = len(rp_p) / 244.0
out['runtime_actual_paper'] = dict(
    first=str(pp.index[0].date()), last=str(pp.index[-1].date()), n_days=len(pp),
    total_return=round(float(navp.iloc[-1] - 1), 6),
    ann=round(float(navp.iloc[-1] ** (1 / yrs_p) - 1), 6),  # 仅2周，年化无统计意义，如实披露
    vol=round(float(rp_p.std(ddof=1) * np.sqrt(244)), 6),
    mdd=round(float(dd.min()), 6),
    dd_peak=str(dd.idxmax().date() if False else navp[:dd.idxmin()].idxmax().date()),
    dd_trough=str(dd.idxmin().date()))
# 现金腿核查：paper 引擎现金是否计息——账面现金 40393 从 08-14 创建至 08-28 未变（state 文件 updated_at 对照）
st = json.load(open('/root/.openclaw/workspace/shared/results/04-投资研究/paper-state.json'))
out['paper_state'] = dict(cash=st['cash'], initial=st['initial_capital'],
                          created_at=st.get('created_at'), updated_at=st.get('updated_at'),
                          model_version=st.get('model_version'),
                          n_holdings=len(st['holdings']),
                          equity_cost=sum(v['shares'] * v['cost'] for v in st['holdings'].values()))
ec = out['paper_state']['equity_cost']
out['paper_state']['equity_w_costbasis'] = round(ec / (ec + st['cash']), 6)

# ---------- 汇总：展示 vs runtime 差距 ----------
rt = out['runtime_w60_rebal']
out['gap_display_vs_runtime_pp'] = dict(
    mdd=round((rt['mdd'] - m_disp['mdd']) * 100, 3),
    ann=round((rt['ann'] - m_disp['ann']) * 100, 3),
    vol=round((rt['vol'] - m_disp['vol']) * 100, 3),
    sharpe=round(rt['sharpe'] - m_disp['sharpe'], 3))

for p in ('/tmp/task-0602-results.json', '/root/.openclaw/workspace/shared/results/work/task-0602-results.json'):
    json.dump(out, open(p, 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
