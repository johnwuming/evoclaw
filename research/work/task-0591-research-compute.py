#!/usr/bin/env python3
"""task-0591 research线: R-380 双口径缺口归因拆分（收益差线一 + 回撤差线二）
只读 tools/quant-bff/live/data/nav_curves.csv；引擎语义与 task-0585 完全一致（锚点先复现）。
产物: /tmp/task-0591-research-results.json + work/task-0591-research-results.json
"""
import pandas as pd, numpy as np, json

CSV = '/root/.openclaw/workspace/tools/quant-bff/live/data/nav_curves.csv'
DRYRUN_WA, DRYRUN_WG = 0.5802970, 0.4197030
COST, BAND, WIN, MIN_OBS = 0.0013, 0.02, 6, 4

df = pd.read_csv(CSV, parse_dates=['month']).set_index('month')
rA = df['A'].pct_change().fillna(df['A'] - 1.0)
rG = df['gold'].pct_change().fillna(df['gold'] - 1.0)
n = len(df); rAv, rGv = rA.values, rG.values
months = list(df.index)

def run_engine(target_fn, rebal_mask=None):
    wA = wG = np.nan; rp = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(wA):
            wA, wG = target_fn(i); cost = COST * (abs(wA) + abs(wG))
        elif rebal_mask is None or rebal_mask[i]:
            tA, tG = target_fn(i)
            cost = COST * (abs(tA - wA) + abs(tG - wG)); wA, wG = tA, tG
        else:
            cost = 0.0
        rp[i] = wA * rAv[i] + wG * rGv[i] - cost
        m = 1 + wA * rAv[i] + wG * rGv[i]
        wA, wG = wA * (1 + rAv[i]) / m, wG * (1 + rGv[i]) / m
    return pd.Series(rp, index=df.index)

def run_band_engine(target_fn):
    wA = wG = np.nan; rp = np.full(n, np.nan); wlog = []
    for i in range(n):
        tA, tG = target_fn(i)
        if np.isnan(wA):
            wA, wG = tA, tG; cost = COST * (abs(wA) + abs(wG))
        elif abs(tA - wA) > BAND or abs(tG - wG) > BAND:
            cost = COST * (abs(tA - wA) + abs(tG - wG)); wA, wG = tA, tG
        else:
            cost = 0.0
        rp[i] = wA * rAv[i] + wG * rGv[i] - cost
        wlog.append(wA)
        m = 1 + wA * rAv[i] + wG * rGv[i]
        wA, wG = wA * (1 + rAv[i]) / m, wG * (1 + rGv[i]) / m
    return pd.Series(rp, index=df.index), pd.Series(wlog, index=df.index)

def eqvol_target_factory(win):
    def f(i):
        if i < 4:
            return (0.5, 0.5)
        a = rAv[max(0, i - win):i]; g = rGv[max(0, i - win):i]
        sA = a.std(ddof=1) * np.sqrt(12); sG = g.std(ddof=1) * np.sqrt(12)
        if not (np.isfinite(sA) and np.isfinite(sG)) or sA <= 0 or sG <= 0:
            return (0.5, 0.5)
        wA = (1 / sA) / (1 / sA + 1 / sG)
        return (float(wA), float(1 - wA))
    return f

def metrics(rp):
    nav = (1 + rp).cumprod()
    r = rp
    yrs = len(r) / 12.0
    ann = nav.iloc[-1] ** (1 / yrs) - 1
    vol = r.std(ddof=1) * np.sqrt(12)
    s = pd.concat([pd.Series([1.0]), nav.reset_index(drop=True)])
    dd = s / s.cummax() - 1
    trough_i = int(dd.idxmin())
    peak_i = int(s.iloc[:trough_i + 1].idxmax())
    rec = dd.iloc[trough_i:]
    rec_i = next((i for i in range(trough_i, len(s)) if s.iloc[i] >= s.iloc[peak_i]), None)
    def dt(i):
        return 'BASE(2013-07)' if i == 0 else str(months[i - 1].date())
    return dict(ann=round(float(ann), 6), vol=round(float(vol), 6),
                sharpe=round(float(ann / vol), 4), mdd=round(float(dd.min()), 6),
                final=round(float(nav.iloc[-1]), 6),
                dd_peak=dt(peak_i), dd_trough=dt(trough_i),
                dd_recovery=dt(rec_i) if rec_i is not None else '未修复')

# ---------- 锚点复现 ----------
rp_stat = run_engine(lambda i: (DRYRUN_WA, DRYRUN_WG), np.ones(n, dtype=bool))
m_stat = metrics(rp_stat)
rp_roll, w_roll = run_band_engine(eqvol_target_factory(6))
m_roll = metrics(rp_roll)
print('[anchor] static5842:', json.dumps(m_stat))
print('[anchor] roll6m    :', json.dumps(m_roll))
assert abs(m_stat['ann'] - .1444) <= .002 and abs(m_stat['mdd'] + .0969) <= .002, '静态锚失败'
assert abs(m_roll['ann'] - .1012) <= .002 and abs(m_roll['mdd'] + .0571) <= .002, '滚动锚失败'

# 单腿（买入持有口径：腿 NAV 直接算，无成本）
def leg_metrics(navcol):
    s = pd.concat([pd.Series([1.0]), df[navcol].reset_index(drop=True)])
    dd = s / s.cummax() - 1
    r = s.pct_change().fillna(s.iloc[0] - 1)
    yrs = len(df) / 12.0
    return dict(ann=round(float(s.iloc[-1] ** (1 / yrs) - 1), 6),
                vol=round(float(r.std(ddof=1) * np.sqrt(12)), 6),
                mdd=round(float(dd.min()), 6),
                dd_peak=(None if int(dd.idxmin()) == 0 else str(months[int(dd.idxmin()) - 1].date())),
                dd_trough=(None if int(dd.idxmin()) == 0 else str(months[int(s.iloc[:int(dd.idxmin()) + 1].idxmax()) - 1].date())))
mA, mG = leg_metrics('A'), leg_metrics('gold')
print('[legs] A:', json.dumps(mA), ' gold:', json.dumps(mG))

# ---------- 线一a: 全期最优静态权重（反波动率解 + 网格 ann/Sharpe 最优） ----------
sAv = float(rA.std(ddof=1) * np.sqrt(12)); sGv = float(rG.std(ddof=1) * np.sqrt(12))
w_invvol = (1 / sAv) / (1 / sAv + 1 / sGv)
grid = {}
best = dict(ann=(-9, None), sharpe=(-9, None))
for w in np.arange(0.0, 1.0001, 0.005):
    rp = run_engine(lambda i, ww=w: (ww, 1 - ww), np.ones(n, dtype=bool))
    m = metrics(rp)
    grid[round(float(w), 3)] = (m['ann'], m['sharpe'], m['mdd'])
    if m['ann'] > best['ann'][0]: best['ann'] = (m['ann'], round(float(w), 3), m)
    if m['sharpe'] > best['sharpe'][0]: best['sharpe'] = (m['sharpe'], round(float(w), 3), m)
m_invvol = metrics(run_engine(lambda i: (w_invvol, 1 - w_invvol), np.ones(n, dtype=bool)))
print(f'[line1a] 腿年化波动 A={sAv:.4f} gold={sGv:.4f}; 全期反波动率静态权重 wA*={w_invvol:.4f}')
print(f'[line1a] 反波动率解指标: {json.dumps(m_invvol)}')
print(f"[line1a] 网格 ann 最优: wA={best['ann'][1]} ann={best['ann'][2]['ann']:.4f} sharpe={best['ann'][2]['sharpe']}")
print(f"[line1a] 网格 sharpe 最优: wA={best['sharpe'][1]} ann={best['sharpe'][2]['ann']:.4f} sharpe={best['sharpe'][2]['sharpe']} mdd={best['sharpe'][2]['mdd']:.4f}")
print(f"[line1a] 58/42 vs ann最优缺口: {(best['ann'][2]['ann']-m_stat['ann'])*100:.2f}pp; vs sharpe最优缺口: {best['sharpe'][1]-0.5802970:.3f}(wA差)")

# ---------- 线一b: 期限结构（3/6/12/24 月窗滚动等波动率） ----------
term = {}
for win in (3, 6, 12, 24):
    rp_w, w_w = run_band_engine(eqvol_target_factory(win))
    mm = metrics(rp_w)
    term[win] = dict(m=mm, w_last=round(float(w_w.iloc[-1]), 4), w_mean=round(float(w_w.mean()), 4),
                     w_p5=round(float(w_w.quantile(.05)), 4), w_p95=round(float(w_w.quantile(.95)), 4))
    print(f"[line1b] win={win}m: ann={mm['ann']:.4f} mdd={mm['mdd']:.4f} 末端wA={term[win]['w_last']} 均值wA={term[win]['w_mean']} [{term[win]['w_p5']},{term[win]['w_p95']}]")

# ---------- 线一: 收益差分解（水平 vs 动态） ----------
w_avg = round(float(w_roll.mean()), 4)
rp_lvl = run_engine(lambda i: (w_avg, 1 - w_avg), np.ones(n, dtype=bool))
m_lvl = metrics(rp_lvl)
gap_total = m_stat['ann'] - m_roll['ann']
gap_dyn = m_lvl['ann'] - m_roll['ann']
gap_lvl = m_stat['ann'] - m_lvl['ann']
print(f'[line1] 滚动权重时均 wA={w_avg}; 静态化(时均权重) ann={m_lvl["ann"]:.4f}')
print(f'[line1] 收益差分解: 总差={gap_total*100:.2f}pp = 权重水平 {gap_lvl*100:.2f}pp + 动态/带控噪声 {gap_dyn*100:.2f}pp')
# 水平差再拆: wA 0.58 vs wA_avg 的腿收益差近似 (Δw)*(annA-annG) + 再平衡增益差
approx = (DRYRUN_WA - w_avg) * (mA['ann'] - mG['ann'])
print(f'[line1] 水平差一阶近似 Δw*(annA-annG) = {approx*100:.2f}pp（vs 实际水平差 {gap_lvl*100:.2f}pp，余项≈再平衡波动收割差异）')

# ---------- 线二a: 回撤差分解（同权重下 再平衡 vs 买入持有；权重水平对照） ----------
rp_bh = run_engine(lambda i: (DRYRUN_WA, DRYRUN_WG), rebal_mask=np.zeros(n, dtype=bool))
m_bh = metrics(rp_bh)
print(f'[line2a] 58/42 月度再平衡: mdd={m_stat["mdd"]:.4f} ({m_stat["dd_peak"]}→{m_stat["dd_trough"]}, 修复 {m_stat["dd_recovery"]})')
print(f'[line2a] 58/42 买入持有漂移: ann={m_bh["ann"]:.4f} mdd={m_bh["mdd"]:.4f} ({m_bh["dd_peak"]}→{m_bh["dd_trough"]}, 修复 {m_bh["dd_recovery"]})')
print(f'[line2a] 时均权重静态({w_avg}) 月度再平衡: mdd={m_lvl["mdd"]:.4f} ({m_lvl["dd_peak"]}→{m_lvl["dd_trough"]})')
print(f'[line2a] 滚动等波动: mdd={m_roll["mdd"]:.4f} ({m_roll["dd_peak"]}→{m_roll["dd_trough"]}, 修复 {m_roll["dd_recovery"]})')

# ---------- 线二b: 最深回撤段 两腿贡献拆解 ----------
def dd_contrib(legs_nav, wA_func, peak_d, trough_d):
    """段内两腿贡献: w_avg_leg * (leg_t/leg_peak - 1) 求和近似"""
    lp = legs_nav.loc[:peak_d].iloc[-1]; lg = legs_nav.loc[:peak_d].iloc[-1]
    legA = df['A'].loc[peak_d:trough_d]; legG = df['gold'].loc[peak_d:trough_d]
    contribA = float((legA / legA.iloc[0] - 1).iloc[-1]); contribG = float((legG / legG.iloc[0] - 1).iloc[-1])
    return contribA, contribG

segA, segG = dd_contrib(df, None, m_stat['dd_peak'], m_stat['dd_trough'])
print(f"[line2b] 静态5842 最深段({m_stat['dd_peak']}→{m_stat['dd_trough']}): A腿 {segA*100:.2f}% × 0.58 = {segA*0.58*100:.2f}pp; gold腿 {segG*100:.2f}% × 0.42 = {segG*0.42*100:.2f}pp; 合计 {(segA*0.58+segG*0.42)*100:.2f}%")
segA2, segG2 = dd_contrib(df, None, m_roll['dd_peak'], m_roll['dd_trough'])
print(f"[line2b] 滚动 最深段({m_roll['dd_peak']}→{m_roll['dd_trough']}): A腿 {segA2*100:.2f}%; gold腿 {segG2*100:.2f}%（段内滚动 wA 均值另计）")
# 段内滚动权重路径
if m_roll['dd_peak'] != 'BASE(2013-07)':
    seg_w = w_roll.loc[m_roll['dd_peak']:m_roll['dd_trough']]
    print(f"[line2b] 滚动段内 wA: mean={seg_w.mean():.3f} min={seg_w.min():.3f} max={seg_w.max():.3f}")
# 静态段内两腿月收益与滚动段对照
seg_stat = rp_stat.loc[m_stat['dd_peak']:m_stat['dd_trough']]
seg_roll_same = rp_roll.loc[m_stat['dd_peak']:m_stat['dd_trough']]
print(f"[line2b] 同段(静态最深段)两通道累计: 静态 {(1+seg_stat).prod()-1:+.4f} vs 滚动 {(1+seg_roll_same).prod()-1:+.4f}")

# ---------- 分年收益对照（收益差时间分布） ----------
yr_stat = (1 + rp_stat).groupby(rp_stat.index.year).prod() - 1
yr_roll = (1 + rp_roll).groupby(rp_roll.index.year).prod() - 1
yr = pd.DataFrame({'static': yr_stat, 'roll': yr_roll})
yr['diff_pp'] = (yr['static'] - yr['roll']) * 100
print('[years] static vs roll diff_pp:'); print(yr['diff_pp'].round(2).to_string())

# ---------- 落盘 ----------
res = dict(anchor_static=m_stat, anchor_roll=m_roll, legs=dict(A=mA, gold=mG),
           leg_vol=dict(A=round(sAv, 6), gold=round(sGv, 6)),
           line1a=dict(w_invvol=round(w_invvol, 6), m_invvol=m_invvol,
                       grid_best_ann=dict(wA=best['ann'][1], m=best['ann'][2]),
                       grid_best_sharpe=dict(wA=best['sharpe'][1], m=best['sharpe'][2]),
                       hindsight_gap_ann_pp=round((best['ann'][2]['ann'] - m_stat['ann']) * 100, 3)),
           line1b={str(k): dict(m=v['m'], w_last=v['w_last'], w_mean=v['w_mean'], w_p5=v['w_p5'], w_p95=v['w_p95']) for k, v in term.items()},
           line1=dict(w_avg=w_avg, m_level=m_lvl, gap_total_pp=round(gap_total * 100, 3),
                      gap_level_pp=round(gap_lvl * 100, 3), gap_dyn_pp=round(gap_dyn * 100, 3),
                      first_order_pp=round(approx * 100, 3)),
           line2=dict(m_bh=m_bh, seg_static=dict(A=round(segA, 4), gold=round(segG, 4)),
                      seg_roll=dict(A=round(segA2, 4), gold=round(segG2, 4)),
                      same_seg_cum=dict(static=round(float((1 + seg_stat).prod() - 1), 4),
                                        roll=round(float((1 + seg_roll_same).prod() - 1), 4))),
           yearly_diff_pp={str(k): round(float(v), 2) for k, v in yr['diff_pp'].items()},
           n_months=n, first=str(months[0].date()), last=str(months[-1].date()))
for p in ('/tmp/task-0591-research-results.json', '/root/.openclaw/workspace/shared/results/work/task-0591-research-results.json'):
    json.dump(res, open(p, 'w'), indent=1, ensure_ascii=False)
print('DONE')
