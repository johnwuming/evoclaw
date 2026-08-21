#!/usr/bin/env python3
# task-0414 阶段A: LightGBM walk-forward 月频IC画像 (预登记: 窗60月/月推进/两组超参/种子42)
import os, json, time, hashlib
import numpy as np, pandas as pd
import lightgbm as lgb
from scipy.stats import spearmanr

HP = "/home/noname/quant-evolve"; OUT = f"{HP}/results/work/r0414"
SEED=42; TRAIN_WIN=60; VAL_WIN=12; MIN_OBS=20
d = np.load(f"{OUT}/panel.npz", allow_pickle=True)
F, R, MASK = d["F"], d["R"], d["MASK"]
months = [str(x) for x in d["months"]]; feats = [str(x) for x in d["feats"]]
n_codes, n_month, _ = F.shape
log = open(f"{OUT}/lgbm_run.log","w")
def P(*a): print(*a, file=log, flush=True)
P(f"panel loaded {F.shape} feats={feats}")

# 截面预处理: 1%/99% winsorize + zscore (逐月, R-251 隔离测试: 不改秩IC)
def cs_norm(X):
    Xo = X.copy()
    for m in range(X.shape[1]):
        x = Xo[:,m,:]
        for k in range(x.shape[1]):
            v = x[:,k]; ok = np.isfinite(v)
            if ok.sum()>50:
                lo,hi = np.nanpercentile(v[ok],1), np.nanpercentile(v[ok],99)
                v[ok] = np.clip(v[ok],lo,hi)
                s = v[ok].std()
                if s>0: v[ok]=(v[ok]-v[ok].mean())/s
    return Xo
Fn = cs_norm(F)
P("cs_norm done")

def train_eval(params, m, tag):
    """训练窗 j∈[m-60,m-1] 样本(F[j],R[j+1]); 预测月 m 打分, IC=spearman(score,R[m+1])"""
    jidx = list(range(m-TRAIN_WIN, m))
    Xs, ys = [], []
    for j in jidx:
        ok = MASK[:,j] & np.isfinite(R[:,j+1])
        if ok.sum()<50: continue
        Xs.append(Fn[ok,j,:]); ys.append(R[ok,j+1])
    X = np.vstack(Xs); y = np.concatenate(ys)
    p = dict(params); p.update({"random_state":SEED,"verbosity":-1,"n_jobs":8})
    vtr = int(len(X)*(1-VAL_WIN/TRAIN_WIN))  # 训练窗末12月作验证
    m_lgb = lgb.LGBMRegressor(**p)
    if p.get("n_estimators",300)>=100:
        m_lgb.fit(X[:vtr],y[:vtr],eval_set=[(X[vtr:],y[vtr:])],
                  callbacks=[lgb.early_stopping(30,verbose=False)])
        best = m_lgb.best_iteration_ or p["n_estimators"]
    else:
        m_lgb.fit(X,y); best=p["n_estimators"]
    okm = MASK[:,m] & np.isfinite(R[:,m+1])
    score = m_lgb.predict(Fn[okm,m,:])
    np.save(f"{OUT}/lgbm_scores_{tag}_{months[m]}.npy", score.astype(np.float32))
    rho,_ = spearmanr(score, R[okm,m+1])
    return float(rho), int(okm.sum()), int(best), m_lgb

CFG_D = {"num_leaves":31,"learning_rate":0.05,"n_estimators":300,"min_child_samples":200,
         "feature_fraction":0.9,"bagging_fraction":0.8,"bagging_freq":1}
# --- O 组: 预登记随机搜索 ≤20 trial (optuna 未装, 用固定种子随机搜索替代, 计账同口径) ---
SPACE = {"num_leaves":[15,31,63],"learning_rate":[0.03,0.05,0.10],
         "min_child_samples":[100,200,400],"feature_fraction":[0.7,0.9,1.0]}
rng = np.random.default_rng(SEED)
trials = [dict(num_leaves=int(rng.choice(SPACE["num_leaves"])),
               learning_rate=float(rng.choice(SPACE["learning_rate"])),
               min_child_samples=int(rng.choice(SPACE["min_child_samples"])),
               feature_fraction=float(rng.choice(SPACE["feature_fraction"])),
               n_estimators=300, bagging_fraction=0.8, bagging_freq=1) for _ in range(20)]
m0 = TRAIN_WIN  # 首个预测月
P(f"O组搜索: {len(trials)} trial @ m0={months[m0]} (前48月训练/末12月验证)")
best_ic, cfg_O = -9, None
t0=time.time()
for ti,tp in enumerate(trials):
    # 评估协议: j∈[m0-60,m0-13] 训练, [m0-12,m0-1] 验证IC
    Xs,ys=[],[]
    for j in range(m0-TRAIN_WIN, m0-VAL_WIN):
        ok = MASK[:,j] & np.isfinite(R[:,j+1])
        if ok.sum()<50: continue
        Xs.append(Fn[ok,j,:]); ys.append(R[ok,j+1])
    Xv,yv=[],[]
    for j in range(m0-VAL_WIN, m0):
        ok = MASK[:,j] & np.isfinite(R[:,j+1])
        if ok.sum()<50: continue
        Xv.append(Fn[ok,j,:]); yv.append(R[ok,j+1])
    X=np.vstack(Xs); y=np.concatenate(ys)
    p=dict(tp); p.update({"random_state":SEED,"verbosity":-1,"n_jobs":8})
    mdl=lgb.LGBMRegressor(**p)
    mdl.fit(X,y)  # 搜索阶段不早停(省时), 用固定300轮
    ics=[spearmanr(mdl.predict(Xv[t]),yv[t])[0] for t in range(len(Xv))]
    vic=float(np.nanmean(ics))
    P(f"  trial{ti+1}/{len(trials)} val_ic={vic:.4f} {tp} ({time.time()-t0:.0f}s)")
    if vic>best_ic: best_ic, cfg_O = vic, tp
P(f"O组选定: {cfg_O} val_ic={best_ic:.4f}")

# --- walk-forward 两配置 ---
results = {}
for tag,cfg in [("D",CFG_D),("O",cfg_O)]:
    import csv as _csv
    fh = open(f"{OUT}/lgbm_ic_monthly_{tag}.csv","w",newline="")
    w = _csv.writer(fh); w.writerow(["ym","ic","n","best_iter"])
    for m in range(TRAIN_WIN, n_month-1):
        ic,n,best,mdl = train_eval(cfg, m, tag)
        w.writerow([months[m],round(ic,6),n,best]); fh.flush()
        if (m-TRAIN_WIN)%12==0: P(f"[{tag}] {months[m]} ic={rc:.4f} n={n}" if False else f"[{tag}] {months[m]} ic={ic:.4f} n={n} ({time.time()-t0:.0f}s)")
    fh.close()
    df=pd.read_csv(f"{OUT}/lgbm_ic_monthly_{tag}.csv"); rows=df.to_dict("records")
    df=pd.DataFrame(rows); df.to_csv(f"{OUT}/lgbm_ic_monthly_{tag}.csv",index=False)
    ic=df["ic"].values
    results[tag]={"n_months":len(ic),"mean_ic":float(np.nanmean(ic)),
                  "icir":float(np.nanmean(ic)/np.nanstd(ic,ddof=1)),
                  "ic_positive":float(np.mean(ic>0))}
    P(f"[{tag}] DONE icir={results[tag][chr(39)+chr(39)] if False else results[tag][chr(105)+chr(99)+chr(105)+chr(114)]:.4f}")
json.dump({"cfg_D":CFG_D,"cfg_O":cfg_O,"trials_O":len(trials),"optuna_note":"optuna未安装,预登记随机搜索替代,seed42",
           "results":results},open(f"{OUT}/lgbm_summary.json","w"),ensure_ascii=False,indent=1,default=str)
P("ALL_DONE")
