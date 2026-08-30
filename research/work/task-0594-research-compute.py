#!/usr/bin/env python3
"""task-0594 research线: R-381 滚动/静态区间对齐敏感性 + 判定标准复核
只读 tools/quant-bff/live/data/{nav_curves.csv,nav_curves.authoritative.csv}；引擎语义与 task-0591/task-0585 一致。
产物: /tmp/task-0594-results.json + work/task-0594-results.json
"""
import pandas as pd, numpy as np, json

CSV = '/root/.openclaw/workspace/tools/quant-bff/live/data/nav_curves.csv'
AUTH = '/root/.openclaw/workspace/tools/quant-bff/live/data/nav_curves.authoritative.csv'
DRYRUN_WA, DRYRUN_WG = 0.5802970, 0.4197030
COST, BAND, WIN, MIN_OBS = 0.0013, 0.02, 6, 4

df = pd.read_csv(CSV, parse_dates=['month']).set_index('month')
rA = df['A'].pct_change().fillna(df['A'] - 1.0)
rG = df['gold'].pct_change().fillna(df['gold'] - 1.0)
n = len(df); rAv, rGv = rA.values, rGv = rG.values
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
        if i < MIN_OBS:
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
    yrs = len(rp) / 12.0
    ann = nav.iloc[-1] ** (1 / yrs) - 1
    vol = rp.std(ddof=1) * np.sqrt(12)
    s = pd.concat([pd.Series([1.0]), nav.reset_index(drop=True)])
    dd = s / s.cummax() - 1
    trough_i = int(dd.idxmin())
    peak_i = int(s.iloc[:trough_i + 1].idxmax())
    def dt(i):
        return 'BASE(2013-07)' if i == 0 else str(months[i - 1].date())
    return dict(ann=round(float(ann), 6), vol=round(float(vol), 6),
                sharpe=round(float(ann / vol), 4), mdd=round(float(dd.min()), 6),
                calmar=round(float(ann / abs(dd.min())), 4), final=round(float(nav.iloc[-1]), 6),
                dd_peak=dt(peak_i), dd_trough=dt(trough_i))

# ---------- 锚点复现 ----------
rp_stat = run_engine(lambda i: (DRYRUN_WA, DRYRUN_WG), np.ones(n, dtype=bool))
rp_roll, w_roll = run_band_engine(eqvol_target_factory(WIN))
m_stat, m_roll = metrics(rp_stat), metrics(rp_roll)
print('[anchor] static5842:', json.dumps(m_stat))
print('[anchor] roll6m    :', json.dumps(m_roll))
assert abs(m_stat['ann'] - .1444) <= .002 and abs(m_stat['mdd'] + .0969) <= .002, '静态锚失败'
assert abs(m_roll['ann'] - .1012) <= .002 and abs(m_roll['mdd'] + .0571) <= .002, '滚动锚失败'

# ---------- warmup 语义：引擎 wlog vs authoritative.csv W_ROLL 列 双证 ----------
auth = pd.read_csv(AUTH, parse_dates=['month']).set_index('month')
common = auth.index.intersection(df.index)
w_diff = float(np.abs(w_roll.loc[common].values - auth.loc[common, 'W_ROLL_A'].values).max())
warmup_rows = auth.loc[auth.index[0]:months[MIN_OBS - 1], ['W_ROLL_A', 'W_ROLL_GOLD']].round(6)
print(f"[warmup] n={n} first={months[0].date()} last={months[-1].date()}")
print(f"[warmup] 引擎wlog vs CSV W_ROLL_A max|diff| = {w_diff:.3e} （0=逐位一致）")
print('[warmup] W_ROLL 前6行（CSV 原值）:'); print(warmup_rows.to_string())
first_real = months[MIN_OBS]  # i=MIN_OBS 即 2013-12
i_first_real = list(months).index(first_real)
print(f"[warmup] 首个非 fallback 月 = {first_real.date()}（i={i_first_real}）；warmup 月数 = {i_first_real}（{months[0].date()}~{months[MIN_OBS-1].date()}）")
print(f"[warmup] warmup 期滚动通道实际持有 = 等权 0.5/0.5 fallback（非 NaN、非缺月）；两通道区间同起 BASE(2013-07)，无 6 个月错位")

# ---------- 敏感性一：静态 58/42 截断到首个非 warmup 月（2013-12）起 ----------
cut = months[i_first_real]  # 2013-12-31
seg_stat = rp_stat.loc[cut:]
seg_roll = rp_roll.loc[cut:]
ms_t, mr_t = metrics(seg_stat), metrics(seg_roll)
print(f"[sens1] 静态全长 vs 截断({cut.date()}~): ann {m_stat['ann']:.4f} vs {ms_t['ann']:.4f} | vol {m_stat['vol']:.4f} vs {ms_t['vol']:.4f} | sharpe {m_stat['sharpe']} vs {ms_t['sharpe']} | mdd {m_stat['mdd']:.4f} vs {ms_t['mdd']:.4f} | final {m_stat['final']} vs {ms_t['final']}")
print(f"[sens1] 截断引起的静态指标漂移: Δann {(ms_t['ann']-m_stat['ann'])*100:+.2f}pp Δmdd {(ms_t['mdd']-m_stat['mdd'])*100:+.2f}pp Δsharpe {ms_t['sharpe']-m_stat['sharpe']:+.3f}")

# ---------- 敏感性二：对齐区间（2013-12~2026-07）两通道缺口重算 ----------
print(f"[sens2] 对齐区间两通道: 静态 ann {ms_t['ann']:.4f} vol {ms_t['vol']:.4f} sharpe {ms_t['sharpe']} mdd {ms_t['mdd']:.4f} calmar {ms_t['calmar']}")
print(f"[sens2]                  滚动 ann {mr_t['ann']:.4f} vol {mr_t['vol']:.4f} sharpe {mr_t['sharpe']} mdd {mr_t['mdd']:.4f} calmar {mr_t['calmar']}")
gap_full = dict(ann_pp=round((m_stat['ann'] - m_roll['ann']) * 100, 2),
                mdd_pp=round((m_stat['mdd'] - m_roll['mdd']) * 100, 2),
                sharpe=round(m_stat['sharpe'] - m_roll['sharpe'], 3),
                calmar=round(m_stat['calmar'] - m_roll['calmar'], 3))
gap_align = dict(ann_pp=round((ms_t['ann'] - mr_t['ann']) * 100, 2),
                 mdd_pp=round((ms_t['mdd'] - mr_t['mdd']) * 100, 2),
                 sharpe=round(ms_t['sharpe'] - mr_t['sharpe'], 3),
                 calmar=round(ms_t['calmar'] - mr_t['calmar'], 3))
print(f"[sens2] 缺口(静−滚) 全区间: {json.dumps(gap_full)}")
print(f"[sens2] 缺口(静−滚) 对齐后: {json.dumps(gap_align)}")

# 对齐区间水平/动态分解复算（验 R-380 归因在对齐后是否成立）
w_avg_al = round(float(w_roll.loc[cut:].mean()), 4)
rp_lvl = run_engine(lambda i: (w_avg_al, 1 - w_avg_al), np.ones(n, dtype=bool)).loc[cut:]
ml_t = metrics(rp_lvl)
gap_total_a = ms_t['ann'] - mr_t['ann']
gap_dyn_a = ml_t['ann'] - mr_t['ann']
gap_lvl_a = ms_t['ann'] - ml_t['ann']
print(f"[sens2] 对齐后收益差分解: 总差 {gap_total_a*100:.2f}pp = 权重水平 {gap_lvl_a*100:.2f}pp + 动态/带控 {gap_dyn_a*100:.2f}pp（对齐时均 wA={w_avg_al}）")

# ---------- 判定标准：vol 带合规 + 风险调整口径 ----------
VT, VT_BAND = 0.08, 0.02  # 用户 2026-08-30 洞察④提出 8%±2pp（文档无出处，如实标注）
def band_check(vol, label):
    lo, hi = VT - VT_BAND, VT + VT_BAND
    ok = lo <= vol <= hi
    print(f"[judge] {label} vol={vol*100:.2f}% 带[{lo*100:.0f},{hi*100:.0f}]% → {'带内' if ok else f'带外(超上沿{(vol-hi)*100:.2f}pp)' if vol>hi else '带外(低于下沿)'}")
    return ok
band_full = dict(rolling=band_check(m_roll['vol'], '滚动·全长'), static=band_check(m_stat['vol'], '静态·全长'))
band_align = dict(rolling=band_check(mr_t['vol'], '滚动·对齐'), static=band_check(ms_t['vol'], '静态·对齐'))
# 定义日快照解隐含组合波动（solver diagnostics: 风险贡献各 0.0644884844）
snap_vol = 0.0644884844 * 2
print(f"[judge] 定义日(2026-08-28)快照解隐含组合波动 ≈ {snap_vol*100:.2f}%（solver 等风险贡献闭式解，非目标波动约束）")

res = dict(anchor=dict(static=m_stat, rolling=m_roll), n=n,
           warmup=dict(first_non_fallback=str(first_real.date()), n_warmup_months=i_first_real,
                       w_roll_head=[[str(ix.date()), float(r.W_ROLL_A), float(r.W_ROLL_GOLD)] for ix, r in warmup_rows.iterrows()],
                       engine_vs_csv_maxdiff=w_diff),
           sens1=dict(cut=str(cut.date()), static_trunc=ms_t, drift=dict(ann_pp=round((ms_t['ann']-m_stat['ann'])*100,2),
                      mdd_pp=round((ms_t['mdd']-m_stat['mdd'])*100,2), sharpe=round(ms_t['sharpe']-m_stat['sharpe'],3))),
           sens2=dict(rolling_trunc=mr_t, gap_full=gap_full, gap_aligned=gap_align,
                      level_decomp_aligned=dict(w_avg=w_avg_al, total_pp=round(gap_total_a*100,2),
                                                level_pp=round(gap_lvl_a*100,2), dyn_pp=round(gap_dyn_a*100,2)),
                      m_level_aligned=ml_t),
           judge=dict(band_full=band_full, band_aligned=band_align, vt=VT, vt_band=VT_BAND,
                      defdate_snapshot_vol=snap_vol))
for p in ('/tmp/task-0594-results.json', '/root/.openclaw/workspace/shared/results/work/task-0594-results.json'):
    json.dump(res, open(p, 'w'), indent=1, ensure_ascii=False)
print('DONE')
