#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A10-4 (task-0370): IC 衰减监控（只读监控，不动 registry/管线）.

规则（与 A7c/W1 口径一致，有效IC = raw × 方向）:
  - 每因子衰减阈值 th = max(0.01, 0.5 × |全周期均值IC|)   # 跌破历史强度一半
  - 近3期 |IC| < th 连续 >=3 期  -> ALERT_DECAY（建议降权）
  - 近3期与全周期反号且 |IC|>=0.01 连续 >=3 期 -> ALERT_FLIP（建议暂停，待复核）
  - 连续 2 期 -> WARN（观察）
  - 建议降权系数: ALERT_FLIP -> 0.0; ALERT_DECAY -> clamp(|近12m ICIR|/|全周期ICIR|, 0.2, 0.8)
                 （近12m 与全周期反号 -> 0.0）; 其余 -> 1.0

产物: results/a10-ic-decay-alerts.{json,csv,md}（原子写，幂等）
退出码: 0=正常跑完（含有告警的情形）；2=数据错误
本脚本只做「监控+标记+建议权重」；真正改 registry 的执行方案写在 md 的待批段，需用户批准后另任务执行。
"""
import pandas as pd, numpy as np, json, os, sys, datetime

HOME = os.path.expanduser('~')
BASE = f'{HOME}/quant-evolve'
PANEL = os.environ.get('A10_PANEL', f'{BASE}/results/factor_ic_monthly.csv')  # A10_PANEL 仅测试注入用
CAT = os.environ.get('A10_CATALOG', f'{BASE}/results/factor_catalog_v3.json')
OUTJ = os.environ.get('A10_OUT_PREFIX', f'{BASE}/results/a10-ic-decay-alerts') + '.json'
OUTC = os.environ.get('A10_OUT_PREFIX', f'{BASE}/results/a10-ic-decay-alerts') + '.csv'
OUTM = os.environ.get('A10_OUT_PREFIX', f'{BASE}/results/a10-ic-decay-alerts') + '.md'
N_CONSEC = 3  # 连续期数阈值

MAPPING = {
    'P0-1 低成交额/低换手族': ['avg_amount_20d', 'turnover_rate', 'turnover_rate_60d', 'log_amount_60d'],
    'P0-2 Amihud': ['amihud_illiquidity', 'amihud_60d'],
    'P0-6 换手CV': ['amount_cv', 'amount_cv_60d', 'turnover_std_20d'],
    'P1 F7 低波': ['volatility_20d', 'volatility_60d', 'idiosyncratic_vol', 'downside_vol_20d'],
    'P1 F13 股息': ['div_yield_ttm'],
    'P2 F14 壳价值': ['shell_value_proxy', 'mktcap_rank_pct', 'microcap_liq_interact'],
}

def atomic_write(path, content):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp, path)

try:
    df = pd.read_csv(PANEL)
except Exception as e:
    print(f'[error] cannot read panel: {e}')
    sys.exit(2)
df['ym'] = pd.to_datetime(df['ym'].astype(str) + '-01')
df = df.sort_values('ym').reset_index(drop=True)
cat = json.load(open(CAT))['factors']
as_of = df['ym'].iloc[-1].strftime('%Y-%m')
run_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

rows, alerts = [], []
for fac, cols in MAPPING.items():
    for c in cols:
        if c not in df.columns:
            continue
        d = cat.get(c, {}).get('direction', 'pos')
        s = (df[c] * (-1 if d == 'neg' else 1)).dropna()
        if len(s) < 60:
            continue
        idx = s.index  # 对齐 df['ym']
        full_m, full_sd = s.mean(), s.std(ddof=1)
        full_icir = full_m / full_sd if full_sd > 0 else np.nan
        th = max(0.01, round(0.5 * abs(full_m), 4))
        tail = s.iloc[-N_CONSEC:]
        tail_ym = [df['ym'].loc[i].strftime('%Y-%m') for i in tail.index]
        tail_v = [round(v, 4) for v in tail.values]
        n_avail = len(tail.dropna())
        below = [abs(v) < th for v in tail.values]
        flip = [(v * full_m < 0) and abs(v) >= 0.01 for v in tail.values]
        # 连续尾部计数
        cb = 0
        for b in reversed(below):
            if b:
                cb += 1
            else:
                break
        cf = 0
        for b in reversed(flip):
            if b:
                cf += 1
            else:
                break
        r12 = s.iloc[-12:]
        r12_m, r12_sd = r12.mean(), r12.std(ddof=1)
        r12_icir = r12_m / r12_sd if r12_sd > 0 else np.nan
        if n_avail < 2:
            status = 'DATA_SHORT'
        elif cf >= N_CONSEC:
            status = 'ALERT_FLIP'
        elif cb >= N_CONSEC:
            status = 'ALERT_DECAY'
        elif cb == 2 or cf == 2:
            status = 'WARN'
        else:
            status = 'OK'
        # 建议系数
        if status == 'ALERT_FLIP':
            k = 0.0
        elif status == 'ALERT_DECAY':
            k = 0.0 if (r12_m * full_m < 0) else round(clamp(abs(r12_icir) / abs(full_icir), 0.2, 0.8), 2) \
                if np.isfinite(r12_icir) and np.isfinite(full_icir) and abs(full_icir) > 0 else 0.2
        else:
            k = 1.0
        sug = {'ALERT_FLIP': '暂停使用（反号），待微盘内复核',
               'ALERT_DECAY': f'降权 ×{k}',
               'WARN': '观察（连续2期异常）', 'OK': '维持现权重', 'DATA_SHORT': '数据不足，暂缓判定'}[status]
        row = {'as_of_ym': as_of, 'survey': fac, 'col': c, 'label': cat.get(c, {}).get('label', c),
               'dir': d, 'full_IC': round(full_m, 4), 'full_ICIR': round(full_icir, 3) if np.isfinite(full_icir) else 'NA',
               'decay_th': th, 'last3_ym': ','.join(tail_ym), 'last3_IC': ','.join(f'{v:+.4f}' for v in tail_v),
               'consec_below': cb, 'consec_flip': cf, 'r12_IC': round(r12_m, 4),
               'r12_ICIR': round(r12_icir, 3) if np.isfinite(r12_icir) else 'NA',
               'status': status, 'suggested_weight_k': k, 'suggestion': sug}
        rows.append(row)
        if status.startswith('ALERT'):
            alerts.append(row)

rows.sort(key=lambda r: (r['status'] != 'ALERT_FLIP', r['status'] != 'ALERT_DECAY', r['status'] != 'WARN', r['col']))
tbl = pd.DataFrame(rows)
atomic_write(OUTC, tbl.to_csv(index=False))
atomic_write(OUTJ, json.dumps({'as_of_ym': as_of, 'run_ts': run_ts, 'n_consec': N_CONSEC,
                               'n_factors': len(rows), 'n_alerts': len(alerts), 'rows': rows},
                              ensure_ascii=False, indent=1))

# ---- md 报告 ----
L = [f'# A10-4 IC 衰减监控（as_of {as_of}，run {run_ts}）', '',
     f'- 判定规则：th = max(0.01, 0.5×|全周期均值IC|)；连续 {N_CONSEC} 期 |IC|<th → ALERT_DECAY；连续 {N_CONSEC} 期反号(|IC|≥0.01) → ALERT_FLIP；连续 2 期 → WARN',
     f'- 建议系数：FLIP→0.0（暂停）；DECAY→clamp(|近12m ICIR|/|全周期ICIR|, 0.2, 0.8)，反号→0.0；其余→1.0',
     f'- **告警 {len(alerts)} 个 / 共 {len(rows)} 因子**（有效IC=raw×方向，W1 月频全市场口径）', '',
     '| 因子 | 近3期IC | 阈值 | 连续低于/反号 | 近12m IC/ICIR | 状态 | 建议系数 |', '|---|---|---|---|---|---|---|']
for r in rows:
    L.append(f"| {r['col']} | {r['last3_IC']} | {r['decay_th']} | {r['consec_below']}/{r['consec_flip']} | "
             f"{r['r12_IC']}/{r['r12_ICIR']} | {r['status']} | ×{r['suggested_weight_k']} |")
L += ['', '## 告警清单', '']
if alerts:
    for r in alerts:
        L.append(f"- **{r['col']}（{r['survey']}）**：近3期 {r['last3_IC']}（{r['last3_ym']}）连续 {r['consec_below']} 期低于 th={r['decay_th']}"
                 f"（反号 {r['consec_flip']} 期）→ {r['status']}，建议权重 ×{r['suggested_weight_k']}（{r['suggestion']}）")
else:
    L.append('- 无连续 3 期低于阈值的因子。')
L += ['', '## 待批执行方案（未执行，需用户批准）', '',
      '1. **降权执行**（本次只到「建议」，不动 registry/paper_engine）：',
      '   - 批准后由新任务将 ALERT 因子在策略权重表中权重 ×k（k 见上表），先在 A7/A10 回测框架跑 locked 对照验证净增量不恶化，再人工修改对应配置。',
      '   - ALERT_FLIP 因子建议先冻结（k=0），并在微盘宇宙内独立复核方向（A7c 警示：全市场 IC 反号不必然等于微盘内失效）。',
      '2. **月度自动化 crontab（建议条目，未安装）**：',
      '   ```',
      '   5 8 3 * * cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python scripts/a10_monthly_profile_update.py >> logs/a10-monthly-profile-update.log 2>&1 && /home/noname/miniconda3/envs/quant/bin/python scripts/a10_ic_decay_monitor.py >> logs/a10-ic-decay-monitor.log 2>&1',
      '   ```',
      '   （每月 3 日 08:05，避开月初数据刷新；安装需用户批准）',
      '', f'- 产物：`{OUTJ}` / `{OUTC}` / 本 md；幂等可重跑（原子写）']
atomic_write(OUTM, '\n'.join(L))

# ---- stdout 摘要（含每因子近3期IC与阈值判定）----
print(f'[ic-decay-monitor] as_of={as_of} factors={len(rows)} alerts={len(alerts)} (rule: consec {N_CONSEC} below th=max(0.01,0.5*|fullIC|))')
for r in rows:
    print(f"{r['col']:<22} last3={r['last3_IC']:<22} th={r['decay_th']:<7} below/flip={r['consec_below']}/{r['consec_flip']} "
          f"r12={r['r12_IC']}/{r['r12_ICIR']:<6} {r['status']:<11} k={r['suggested_weight_k']}")
print(f'[done] outputs -> {OUTJ} , {OUTC} , {OUTM}')
sys.exit(0)
