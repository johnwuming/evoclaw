import pandas as pd, numpy as np, json, sys
R="/root/.openclaw/workspace/shared/results/work/r323"
RES="/root/.openclaw/workspace/shared/results"
ym=lambda d:d.dt.year*100+d.dt.month

def monthly_close(csv):
    d=pd.read_csv(f"{R}/raw/{csv}",parse_dates=["date"])[["date","close"]].sort_values("date")
    d["k"]=ym(d["date"])
    me=d.groupby("k").last().reset_index()
    return me.set_index("k")["close"], me.set_index("k")["date"]

def daily_feats(code):
    d=pd.read_csv(f"{R}/raw/{code}_tx_qfq.csv",parse_dates=["date"]).sort_values("date")
    c=d["close"]; r=c.pct_change()
    f=pd.DataFrame({"sma200":c>c.rolling(200).mean(),"sma240":c>c.rolling(240).mean(),
        "ma50_200":c.rolling(50).mean()>c.rolling(200).mean(),
        "voltgt10":(0.10/(r.rolling(60).std()*np.sqrt(244))).clip(0,1)})
    f["k"]=ym(d["date"]); return f.groupby("k").last()

def ann_mdd(nav):
    n=len(nav); a=(nav.iloc[-1]/nav.iloc[0])**(12/(n-1))-1
    dd=(nav/nav.cummax()-1); return a,dd.min()

def stats(ret):
    nav=(1+ret.fillna(0)).cumprod(); a,mdd=ann_mdd(nav)
    pos=ret.dropna(); win=float((pos>0).mean()) if len(pos) else np.nan
    return {"ann":round(a,4),"mdd":round(mdd,4),"calmar":round(a/abs(mdd),3),"win_m":round(win,3),"n":int(len(pos))}

# ---- data ----
codes={"sh513100":"513100纳指100","sh513500":"513500标普500"}
M={c:monthly_close(f"{c}_tx_qfq.csv") for c in codes}
F={c:daily_feats(c) for c in codes}
mc,mdate=M["sh513100"][0], M["sh513100"][1]
rets={c:M[c][0].pct_change() for c in codes}
hs,hd=monthly_close("sh000300_sina.csv"); hsret=hs.pct_change()
mm=pd.read_csv(f"{R}/raw/mmf_000198.csv",parse_dates=["净值日期"]).rename(columns={"净值日期":"date","每万份收益":"inc"}).sort_values("date")
mm["k"]=ym(mm["date"]); mmf_m=(1+mm["inc"]/10000).groupby(mm["k"]).prod()-1

rows=[]
ks=[k for k in mc.index if k in F["sh513100"].index and k in F["sh513500"].index]
for i in range(13,len(ks)):
    k,pk=ks[i],ks[i-1]
    sig={}
    for c in codes:
        f=F[c].loc[k]; mc_=M[c][0]
        idx=mc_.index.get_loc(k)
        s11,f11,dic=int(f["sma200"]),float(f["voltgt10"]),{}
        dic["trend"]=1.0 if s11 else 0.0
        dic["vt"]=f11
        if idx>=13:
            prev=mc_.iloc[idx-1]; yoy=mc_.iloc[idx-13]
            dic["mom"]=1.0 if prev/yoy-1>0 else 0.0
        else: dic["mom"]=np.nan
        sig[c]=dic
    row={"k":k}
    for c in codes:
        r1=rets[c].get(k,np.nan)
        row[f"{c}_ret"]=r1; 
        for s in ["trend","mom"]:
            w=sig[c][s]; row[f"{c}_{s}_gross"]=w*r1
            row[f"{c}_{s}_cash"]=w*r1+(1-w)*float(mmf_m.get(pk,np.nan))
        # trend x voltgt 组合
        w=sig[c]["trend"]*sig[c]["vt"]
        row[f"{c}_mix_gross"]=w*r1; row[f"{c}_mix_cash"]=w*r1+(1-w)*float(mmf_m.get(pk,np.nan))
        for tag in ["sma200","sma240","ma50_200"]:
            wv=1.0 if bool(F[c].loc[k][tag]) else 0.0
            row[f"{c}_{tag}_gross"]=wv*r1; row[f"{c}_{tag}_cash"]=wv*r1+(1-w)*float(mmf_m.get(pk,np.nan))
        row[f"{c}_buyhold_cash"]=np.nan
    row["hs300_ret"]=hsret.get(k,np.nan)
    rows.append(row)
T=pd.DataFrame(rows).set_index("k")

def series(code,key,col): return T[f"{code}_{key}_{col}"]
corr_a13=lambda s:(pd.concat([s,a13m],axis=1,join="inner").dropna())
a13=pd.read_csv(f"{RES}/04-投资研究/a13_rsraw_e1f10_locked_nav.csv",parse_dates=["date"])
a13["k"]=ym(a13["date"]); a13m=a13.groupby("k")["nav"].last().pct_change()
gold=pd.read_csv(f"{RES}/04-投资研究/f6_curves/gold_alone_nav.csv",parse_dates=["date"])
gold["k"]=ym(gold["date"]); goldm=gold.set_index("k")["nav"].pct_change()

out={}
def spearman(x,y):
    rx=x.rank(); ry=y.rank(); return float(np.corrcoef(rx,ry)[0,1])
for code in codes:
    for key in ["trend","sma200","sma240","ma50_200","mom","mix"]:
        g=series(code,key,"gross"); ca=series(code,key,"cash")
        out[f"{code}_{key}"]={"gross":stats(g),"cash":stats(ca),
            "occ":round(float((g.notna()).mean()),3)}
a13vals={}
for code in codes:
    for key in ["trend","mix","mom"]:
        g=series(code,key,"gross"); m=corr_a13(g)
        if len(m)>30 and m.std().std()!=0:
            pv=m[m.columns[0]].values if False else None
            x=m.iloc[:,0]; y=m.iloc[:,1]
            sp=spearman(x,y)
            mk=m.index
            pre=x[mk<202001]; post=x[mk>=202001]
            ypre=y[mk<202001]; ypost=y[mk>=202001]
            a13vals[f"{code}_{key}"]={
              "full":{"corr":round(float(np.corrcoef(x,y)[0,1]),4),"rho":round(float(sp),3),"n":len(m),
                      "span":f"{m.index.min()}..{m.index.max()}"},
              "pre2020":round(float(np.corrcoef(pre,ypre)[0,1]),3) if len(pre)>20 else None,
              "post2020":round(float(np.corrcoef(post,ypost)[0,1]),3) if len(post)>20 else None}
corrg={}
for code in codes:
    for key in ["trend","mix","mom"]:
        g=series(code,key,"gross"); m=pd.concat([g,goldm],axis=1,join="inner").dropna()
        if len(m)>20:
            corrg[f"{code}_{key}"]={"corr":round(float(np.corrcoef(m.iloc[:,0],m.iloc[:,1])[0,1]),4),"n":len(m),
              "span":f"{m.index.min()}..{m.index.max()}"}
corr_hs={}
for code in codes:
    for key in ["trend","mix"]:
        g=series(code,key,"gross"); m=pd.concat([g,T["hs300_ret"]],axis=1,join="inner").dropna()
        corr_hs[f"{code}_{key}"]=round(float(np.corrcoef(m.iloc[:,0],m.iloc[:,1])[0,1]),4)
json.dump({"signals":out,"vs_a13":a13vals,"vs_gold":corrg,"vs_hs300":corr_hs,
           "mmf_ann":None},open(f"{R}/out/metrics_qfq.json","w"),ensure_ascii=False,indent=1,default=str)
T.to_csv(f"{R}/out/monthly_panel_qfq.csv")
print(json.dumps(out,ensure_ascii=False)[:400])
print(json.dumps(a13vals,ensure_ascii=False)[:600])
print(json.dumps(corrg,ensure_ascii=False)[:400])
print("HS300:",corr_hs)
