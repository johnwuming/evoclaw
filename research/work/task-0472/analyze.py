#!/usr/bin/env python3
# task-0472 层2 参数离线训练计算脚本（零真金，只读 NAV csv，纯离线）
import pandas as pd, numpy as np, json, os

BASE = "/root/.openclaw/workspace/shared/results"
OUT = "/root/.openclaw/workspace/shared/results/work/task-0472"
os.makedirs(OUT, exist_ok=True)

def load_daily_nav(path):
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').set_index('date')
    # month-end
    m = df['nav'].resample('ME').last()
    return m

def monthly_ret(nav):
    r = nav.pct_change().dropna()
    return r

# ---- A 全史（日频→月频） ----
a_nav_m = load_daily_nav(f"{BASE}/04-投资研究/a13_rsraw_e1f10_full_nav.csv")
# ---- A2 影子 NAV（日频→月频） ----
a2_nav_m = load_daily_nav(f"{BASE}/04-投资研究/engines/a2/shadow_nav.csv")
# ---- E2 可转债（已是月频） ----
e2 = pd.read_csv(f"{BASE}/work/r281/e2_nav_monthly.csv")
e2['ym'] = pd.to_datetime(e2['ym'], format='%Y-%m')
e2 = e2.set_index('ym')['nav']

a_r = monthly_ret(a_nav_m)
a2_r = monthly_ret(a2_nav_m)
e2_r = monthly_ret(e2)

print("=== 月频对齐概况 ===")
print(f"A: {a_nav_m.index.min().date()}..{a_nav_m.index.max().date()}  {len(a_nav_m)}月")
print(f"A2: {a2_nav_m.index.min().date()}..{a2_nav_m.index.max().date()}  {len(a2_nav_m)}月")
print(f"E2: {e2.index.min().date()}..{e2.index.max().date()}  {len(e2)}月")

# ---- 全窗口月收益表 ----
all_months = sorted(set(a_r.index) | set(a2_r.index) | set(e2_r.index))
df = pd.DataFrame(index=all_months)
df['A'] = a_r.reindex(all_months)
df['A2'] = a2_r.reindex(all_months)
df['E2'] = e2_r.reindex(all_months)

# 月度统计（各腿可用期）
stats = {}
for c in ['A','A2','E2']:
    s = df[c].dropna()
    stats[c] = dict(n=len(s), ann=((1+s.mean())**12-1), vol=round(s.std()*np.sqrt(12)*100,2), mean_m=round(s.mean()*100,3))
print("=== 各腿月度统计(全可用期) ===")
for c,v in stats.items(): print(c, v)

# 月度化年化波动/收益（用于带宽候选）
print("=== 近24月滚动波动（年化%）用于带宽 ===")
for c in ['A','A2','E2']:
    s = df[c].dropna().tail(24)
    print(f"{c}: vol24={round(s.std()*np.sqrt(12)*100,2)}%  mean24_m={round(s.mean()*100,3)}%")

# ---- 相关性矩阵（A+A2 重叠 2006-2024；A+E2 重叠 2018-2026；全三腿 2018-2024） ----
def corr_df(cols):
    sub = df[cols].dropna()
    return sub.corr(), len(sub)

print("=== 相关性（月度） ===")
c_aa2, n_aa2 = corr_df(['A','A2'])
print(f"A-A2 corr={c_aa2.loc['A','A2']:.6f} (n={n_aa2})")
c_ae2, n_ae2 = corr_df(['A','E2'])
print(f"A-E2 corr={c_ae2.loc['A','E2']:.6f} (n={n_ae2})")
c_a2e2, n_a2e2 = corr_df(['A2','E2'])
print(f"A2-E2 corr={c_a2e2.loc['A2','E2']:.6f} (n={n_a2e2})")
c3, n3 = corr_df(['A','A2','E2'])
print(f"三腿 corr:\n{c3}\nn={n3}")

# ---- ERC 计算（含等波动封顶对照） ----
def erc_w(r, W, cov, max_iter=1000, tol=1e-10):
    """风险贡献 ERC 迭代；返回权重"""
    n = len(r)
    w = (1.0/np.sqrt(np.diag(cov))); w = w/w.sum()
    for it in range(max_iter):
        sig_p = np.sqrt(w @ cov @ w)
        mrc = cov @ w / sig_p
        rc = w * mrc
        # 目标: 全部 RC 相等 -> w_new = w * (mean_rc/rc)^0.5? 用标准 ERC 迭代
        target = rc.mean()
        w_new = w * np.sqrt(target / np.maximum(rc, 1e-12))
        w_new = w_new / w_new.sum()
        if np.max(np.abs(w_new-w)) < tol:
            return w_new
        w = w_new
    return w

def scan_erc(cols, Ws=[24,36,48], name=""):
    print(f"=== ERC 扫描 {name} ===")
    out = {}
    r = df[cols].dropna()
    for W in Ws:
        if len(r) < W+1:
            print(f"  W={W}: 数据不足({len(r)})"); continue
        rw = r.tail(W)
        cov = rw.cov()
        w = erc_w(rw, W, cov)
        # 等波动封顶对照
        inv_vol = 1/np.sqrt(np.diag(cov)); w_eqv = inv_vol/inv_vol.sum()
        out[W] = dict(w={c: round(float(x),4) for c,x in zip(cols,w)},
                      w_eqvol={c: round(float(x),4) for c,x in zip(cols,w_eqv)},
                      corr=round(float(rw.corr().stack().mean()),4))
        print(f"  W={W}: ERC={out[W]['w']} 等波动封顶={out[W]['w_eqvol']} 平均|corr|={out[W]['corr']}")
    return out

erc_aa2 = scan_erc(['A','A2'], name="A+A2（双腿）")
erc_ae2 = scan_erc(['A','E2'], name="A+E2（双腿，候选B）")
erc_3   = scan_erc(['A','A2','E2'], name="A+A2+E2（三腿）")

# ---- 带宽：漂移模拟（A+A2 或 A+E2 月度自然漂移） ----
def drift_sim(cols, w0, label):
    """无现金流自然漂移：w_i(t)=w_i(t-1)*(1+r_i(t))/sum(...)；统计 |Δw| 与相对漂移"""
    r = df[cols].dropna()
    w = np.array([w0[c] for c in cols])
    rows=[]
    for t in r.index:
        rt = r.loc[t].values
        w_new = w*(1+rt)
        w_new = w_new/w_new.sum()
        rows.append(dict(t=t, **{c: w_new[i] for i,c in enumerate(cols)}))
        w = w_new
    dr = pd.DataFrame(rows).set_index('t')
    # 相对漂移 |w_act-w_tgt|/w_tgt, 绝对漂移 |w_act-w_tgt|
    out={}
    for c in cols:
        rel=(dr[c]-w0[c]).abs()/w0[c]
        absd=(dr[c]-w0[c]).abs()
        out[c]=dict(rel_max=round(rel.max(),4), rel_p95=round(rel.quantile(0.95),4),
                    abs_max=round(absd.max(),4), abs_p95=round(absd.quantile(0.95),4),
                    mean_abs_m=round(absd.mean(),4))
    return dr, out

# A+E2（有实质意义的双腿）漂移
w_ae2_36 = erc_ae2[36]['w']
dr, drift_stat = drift_sim(['A','E2'], w_ae2_36, "A+E2 W36")
print("=== A+E2 W36 自然漂移统计（band 候选依据） ===")
print(json.dumps(drift_stat, ensure_ascii=False, indent=1))

# A+A2 漂移（极端高相关）
w_aa2_36 = erc_aa2[36]['w']
dr2, drift_stat2 = drift_sim(['A','A2'], w_aa2_36, "A+A2 W36")
print("=== A+A2 W36 自然漂移统计 ===")
print(json.dumps(drift_stat2, ensure_ascii=False, indent=1))

# ---- 组合回撤门压力测试（危机段） ----
def dd_series(nav_m):
    return nav_m/nav_m.cummax()-1

# A 全史回撤 + 危机段
a_dd = dd_series(a_nav_m)
crises = {
  "2008(金融危机)": ("2008-01-01","2008-12-31"),
  "2015(股灾)": ("2015-06-01","2016-01-31"),
  "2024(微盘踩踏)": ("2023-09-01","2024-02-29"),
}
print("=== A 组合回撤压力测试（月频） ===")
for name,(s,e) in crises.items():
    seg = a_dd.loc[s:e]
    mdd = seg.min()
    print(f"  {name}: minDD={mdd*100:.2f}%")
print(f"  A 全史最大回撤: {a_dd.min()*100:.2f}% @ {a_dd.idxmin().date()}")

# 全史回撤持续时间（从峰值到回撤最低点）
peak = a_nav_m.cummax()
draw = a_nav_m/peak-1
print(f"  A 全史最大回撤时长(峰值→谷底): {a_nav_m.loc[:a_dd.idxmin()].idxmax().date()} → {a_dd.idxmin().date()}")

# E2 回撤
e2_dd = dd_series(e2)
print(f"  E2 全史最大回撤: {e2_dd.min()*100:.2f}%")

# 等波动双腿组合（A+E2 或 A+A2）回撤（月频，w 固定目标，无再平衡近似=买持有）
def combo_dd(cols, w, label):
    r = df[cols].dropna()
    # 组合月收益 = Σ w_i * r_i（固定权重，近似；实际层2 有带宽再平衡）
    cr = (r[cols] * np.array([w[c] for c in cols])).sum(axis=1)
    cn = (1+cr).cumprod()
    dd = cn/cn.cummax()-1
    return dd, cr

for cols, w, label in [(['A','E2'], w_ae2_36, "A+E2 W36等"),
                       (['A','A2'], w_aa2_36, "A+A2 W36等")]:
    dd, cr = combo_dd(cols, w, label)
    print(f"  {label} 组合 MDD: {dd.min()*100:.2f}%")

# 危机段三腿组合（2018-2024 重叠可用）回撤
sub3 = df[['A','A2','E2']].dropna()
print(f"  三腿重叠窗口: {sub3.index.min().date()}..{sub3.index.max().date()} ({len(sub3)}月)")
w3 = erc_3[36]['w']
cr3 = (sub3[['A','A2','E2']] * np.array([w3[c] for c in ['A','A2','E2']])).sum(axis=1)
cn3 = (1+cr3).cumprod()
dd3 = cn3/cn3.cummax()-1
print(f"  三腿组合(W36 ERC) MDD: {dd3.min()*100:.2f}% @ {dd3.idxmin().date()}")

# 漂移模拟输出
dr.to_csv(f"{OUT}/drift_A_E2.csv")
dr2.to_csv(f"{OUT}/drift_A_A2.csv")
dd.to_csv(f"{OUT}/combo_dd_A_E2.csv")

summary = dict(
  stats=stats,
  corr_aa2=float(c_aa2.loc['A','A2']), n_aa2=n_aa2,
  corr_ae2=float(c_ae2.loc['A','E2']), n_ae2=n_ae2,
  corr_a2e2=float(c_a2e2.loc['A2','E2']), n_a2e2=n_a2e2,
  erc_aa2=erc_aa2, erc_ae2=erc_ae2, erc_3=erc_3,
  drift_A_E2=drift_stat, drift_A_A2=drift_stat2,
  A_mdd=float(a_dd.min()), A_mdd_date=str(a_dd.idxmin().date()),
  A_mdd_dur=f"{a_nav_m.loc[:a_dd.idxmin()].idxmax().date()}→{a_dd.idxmin().date()}",
  crises={k: float(a_dd.loc[s:e].min()) for k,(s,e) in crises.items()},
  e2_mdd=float(e2_dd.min()),
  combo_ae2_mdd=float(combo_dd(['A','E2'], w_ae2_36, "x")[0].min()),
  combo_3_mdd=float(dd3.min()),
)
with open(f"{OUT}/summary.json","w") as f: json.dump(summary, f, ensure_ascii=False, indent=1, default=str)
print("=== summary.json 已落盘 ===")
print(json.dumps({k:v for k,v in summary.items() if k in ('A_mdd','A_mdd_dur','e2_mdd','combo_ae2_mdd','combo_3_mdd')}, ensure_ascii=False, default=str))
