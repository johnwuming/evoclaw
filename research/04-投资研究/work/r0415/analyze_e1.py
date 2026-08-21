import pandas as pd, numpy as np, hashlib, json
W="/home/noname/quant-evolve/results/work/r0415/"
px = pd.read_csv(W+"sw_industry_monthly.csv", index_col=0, parse_dates=True).sort_index()
px = px[px.index <= "2026-07-31"]
ret = px.pct_change(limit=3)
md5csv = hashlib.md5(open(W+"sw_industry_monthly.csv","rb").read()).hexdigest()

nav = pd.read_csv("/home/noname/quant-evolve/results/a13_rsraw_e1f10dz_full_nav.csv", index_col=0, parse_dates=True)["nav"]
a13_m = nav.resample("ME").last().pct_change().dropna()
a13_m.index = a13_m.index.to_period("M").to_timestamp("M")

START="2006-01-01"; END="2026-07-31"
months = px.loc[START:END].index
n_m = len(months)
res = {"coverage":{"start":str(months[0].date()),"end":str(months[-1].date()),"n_months":int(n_m),
 "n_industries":int(px.shape[1]),"md5":md5csv,
 "universe_evolution":{"1999-12~2013":16,"2014-01~2020-12":28,"2021-01~":31}}}

def tstat(x):
    x=pd.Series(x).dropna()
    return float(x.mean()/(x.std(ddof=1)/np.sqrt(len(x)))) if len(x)>3 and x.std(ddof=1)>0 else float("nan")

def blocks(s):  # 5y blocks direction stability
    out={}
    for a,b in [(2006,2010),(2011,2015),(2016,2020),(2021,2026)]:
        ss=s[(s.index>=f"{a}-01-01")&(s.index<=f"{b}-12-31")]
        if len(ss)>5: out[f"{a}-{b}"]={"mean_pct":round(float(ss.mean())*100,3),"win":round(float((ss>0).mean())*100,1),"n":int(len(ss))}
    return out

# ---- A/B: momentum & IC, adaptive universe ----
mom={}; ic={}
for k in [1,3,6,12]:
    past = px/px.shift(k)-1
    nxt = ret.shift(-1)
    sp5=[]; sp3=[]; t5r=[]; idxs=[]; cors=[]; n_eligs=[]
    for i in px.index:
        if not (pd.Timestamp(START)<=i<=pd.Timestamp(END)): continue
        a=past.loc[i]; f=nxt.loc[i]
        elig=a.notna()&f.notna()
        ne=int(elig.sum())
        if ne<10: continue
        ar=a[elig]; fr=f[elig]
        order=ar.rank(ascending=False)
        n3=max(1,int(round(ne/3)))
        t5=fr[order<=5].mean(); b5=fr[order>=ne-4].mean()
        t3=fr[order<=n3].mean(); b3=fr[order>=ne-n3+1].mean()
        sp5.append(t5-b5); sp3.append(t3-b3); t5r.append(t5); idxs.append(i); n_eligs.append(ne)
        cors.append(ar.corr(fr))
    s5=pd.Series(sp5,index=idxs); s3=pd.Series(sp3,index=idxs); t5s=pd.Series(t5r,index=idxs)
    cs=pd.Series(cors,index=idxs).dropna()
    mom[k]={"n_triggers":int(len(s5)),
      "top5bot5_mean_m_pct":round(float(s5.mean())*100,3),"top5bot5_t":round(tstat(s5),2),"top5bot5_win":round(float((s5>0).mean())*100,1),
      "top3bot3_mean_m_pct":round(float(s3.mean())*100,3),"top3bot3_t":round(tstat(s3),2),"top3bot3_win":round(float((s3>0).mean())*100,1),
      "top5_mean_m_pct":round(float(t5s.mean())*100,3),
      "blocks":blocks(s5)}
    ic[k]={"mean_ic":round(float(cs.mean()),4),"t":round(tstat(cs),2),"n":int(len(cs)),
      "blocks":blocks(cs)}
    t5s.to_csv(W+f"top5_mom{k}_arith.csv")
res["momentum"]=mom; res["ic_reversal"]=ic

# ---- C: dispersion ----
disp=[]; didx=[]
for i in months:
    r=ret.loc[i].dropna()
    if len(r)>=10: disp.append(r.std(ddof=1)); didx.append(i)
ds=pd.Series(disp,index=didx)
d5={}
for a,b in [(2006,2010),(2011,2015),(2016,2020),(2021,2026)]:
    ss=ds[(ds.index>=f"{a}-01-01")&(ds.index<=f"{b}-12-31")]
    d5[f"{a}-{b}"]=round(float(ss.mean())*100,2)
res["dispersion"]={"full_mean_m_pct":round(float(ds.mean())*100,2),"ann_mean_pct":round(float(np.sqrt((ds.pow(2)*12).mean()))*100,1),
 "by_5y":d5,"recent5y_vs_full":round(float(ds[ds.index>="2021-08-01"].mean()/ds.mean()),3)}

# ---- D: correlations with a13 ----
ewm=ret.loc[START:END].mean(axis=1)
ewm.index=ewm.index.to_period("M").to_timestamp("M")
a13w=a13_m.loc[START:END]
common=ewm.index.intersection(a13w.index)
corrEW=float(ewm[common].corr(a13w[common]))
c5={}
for k in [1,3,6,12]:
    t5s=pd.read_csv(W+f"top5_mom{k}_arith.csv",index_col=0,parse_dates=True).iloc[:,0]
    t5s.index=t5s.index.to_period("M").to_timestamp("M")
    c=t5s.index.intersection(a13w.index)
    c5[k]={"pearson":round(float(t5s[c].corr(a13w[c])),3),
      "ann_ret_pct":round(float(t5s[c].mean()*12)*100,1),"ann_vol_pct":round(float(t5s[c].std()*np.sqrt(12))*100,1)}
res["corr_a13"]={"ew_vs_a13":round(corrEW,3),"n_common":int(len(common)),
 "a13_ann_ret_pct":round(float(a13w[common].mean()*12)*100,1),"a13_ann_vol_pct":round(float(a13w[common].std()*np.sqrt(12))*100,1),
 "ew_ann_ret_pct":round(float(ewm[common].mean()*12)*100,1),"ew_ann_vol_pct":round(float(ewm[common].std()*np.sqrt(12))*100,1),
 "top5_by_k":{str(k):v for k,v in c5.items()}}
res["ew_stats"]={"win_rate":round(float((ewm[common]>0).mean())*100,1)}
with open(W+"e1_results.json","w") as f: json.dump(res,f,ensure_ascii=False,indent=1)
print(json.dumps(res,ensure_ascii=False,indent=1))
