import pandas as pd, numpy as np, json
R="/root/.openclaw/workspace/shared/results/work/r341"
RES="/root/.openclaw/workspace/shared/results"
ym=lambda d: d.dt.year*100+d.dt.month

def monthly_close(path):
    d=pd.read_csv(path,parse_dates=["date"]).sort_values("date")
    d["k"]=ym(d["date"])
    me=d.groupby("k").last().reset_index()
    return me.set_index("k")["close"], me.set_index("k")["date"]

def daily_feats(path):
    d=pd.read_csv(path,parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    c=d["close"]; r=c.pct_change()
    ma200=c.rolling(200).mean()
    f=pd.DataFrame({"sma200":(c>ma200)&ma200.notna(),
        "vt":(0.10/(r.rolling(60).std()*np.sqrt(244))).clip(0,1)})
    f["k"]=ym(d["date"]); d["k"]=f["k"]
    g=f.groupby("k").last()
    g["nobs"]=d.groupby("k").size().cumsum()
    g["sma200"]=g["sma200"]&(g["nobs"]>=200)
    g["vt"]=g["vt"].where(g["nobs"]>=60)
    return g

def ann_mdd(nav):
    n=len(nav); a=(nav.iloc[-1]/nav.iloc[0])**(12/(n-1))-1
    dd=nav/nav.cummax()-1
    return a,dd.min()

def stats(ret):
    nav=(1+ret.fillna(0)).cumprod(); a,mdd=ann_mdd(nav)
    return {"ann":round(float(a),4),"mdd":round(float(mdd),4),"calmar":round(float(a/abs(mdd)),3),"n":int(len(ret.dropna()))}

# ---------- data ----------
codes=["sh513100","sh513500"]
M={c:monthly_close(f"{R}/raw/{c}_tx_qfq.csv") for c in codes}
F={c:daily_feats(f"{R}/raw/{c}_tx_qfq.csv") for c in codes}
rets={c:M[c][0].pct_change() for c in codes}
mc=M["sh513100"][0]
mm=pd.read_csv(f"{R}/raw/mmf_000198.csv",parse_dates=["净值日期"]).rename(columns={"净值日期":"date","每万份收益":"inc"}).sort_values("date")
mm["k"]=ym(mm["date"]); mmf_m=(1+mm["inc"]/10000).groupby(mm["k"]).prod()-1
a13=pd.read_csv(f"{RES}/04-投资研究/a13_rsraw_e1f10_locked_nav.csv",parse_dates=["date"])
a13["k"]=ym(a13["date"]); a13m=a13.groupby("k")["nav"].last().pct_change()
gold=pd.read_csv(f"{RES}/04-投资研究/f6_curves/gold_alone_nav.csv",parse_dates=["date"])
gold["k"]=ym(gold["date"]); goldm=gold.set_index("k")["nav"].pct_change()

ks=[k for k in mc.index if k in F["sh513100"].index and k in F["sh513500"].index]

def sig_w(c,k,key):
    """E1 signal: trend=px>SMA200(月末), vt=clip(10%/vol60_ann), mix=trend*vt; key in mix|trend"""
    f=F[c].loc[k]; t=1.0 if bool(f["sma200"]) else 0.0
    if key=="trend": return t
    v=float(f["vt"]) if pd.notna(f["vt"]) else np.nan
    return t*v

# ---------- Part A: E1-exact replication (same-month alignment, cash at pk) ----------
rowsA=[]
for i in range(13,len(ks)):
    k,pk=ks[i],ks[i-1]
    row={"k":k}
    for c in codes:
        r1=rets[c].get(k,np.nan)
        w=sig_w(c,k,"mix"); wt=sig_w(c,k,"trend")
        row[f"{c}_mix_w"]=w; row[f"{c}_mix_gross"]=w*r1
        row[f"{c}_mix_cash"]=w*r1+(1-w)*float(mmf_m.get(pk,np.nan))
        row[f"{c}_trend_gross"]=wt*r1
        row[f"{c}_trend_cash"]=wt*r1+(1-wt)*float(mmf_m.get(pk,np.nan))
        row[f"{c}_ret"]=r1
    rowsA.append(row)
A=pd.DataFrame(rowsA).set_index("k")
rep={}
for c,cod in zip(codes,["513100","513500"]):
    rep[f"{cod}_mix_avgpos"]=round(float(A[f"{c}_mix_w"].mean()),3)
    rep[f"{cod}_mix_cash"]=stats(A[f"{c}_mix_cash"])
    rep[f"{cod}_mix_gross"]=stats(A[f"{c}_mix_gross"])
    g=A[f"{c}_mix_gross"]; m=pd.concat([g,a13m],axis=1,join="inner").dropna()
    x,y=m.iloc[:,0],m.iloc[:,1]
    post=m.index>=202001
    rep[f"{cod}_mix_a13_full"]=round(float(np.corrcoef(x,y)[0,1]),4)
    rep[f"{cod}_mix_a13_post"]=round(float(np.corrcoef(x[post],y[post])[0,1]),4)
    rep[f"{cod}_mix_a13_n"]=int(len(m))
    gt=A[f"{c}_trend_gross"]; mt=pd.concat([gt,a13m],axis=1,join="inner").dropna()
    rep[f"{cod}_trend_a13_full"]=round(float(np.corrcoef(mt.iloc[:,0],mt.iloc[:,1])[0,1]),4)
    postt=mt.index>=202001
    rep[f"{cod}_trend_a13_post"]=round(float(np.corrcoef(mt.iloc[:,0][postt],mt.iloc[:,1][postt])[0,1]),4)
    mg=pd.concat([g,goldm],axis=1,join="inner").dropna()
    rep[f"{cod}_mix_gold"]=round(float(np.corrcoef(mg.iloc[:,0],mg.iloc[:,1])[0,1]),4)

ANCH={"513100_mix_avgpos":0.481,"513500_mix_avgpos":0.526,
 "513100_mix_cash":{"ann":0.1638},"513500_mix_cash":{"ann":0.1581},
 "513100_mix_a13_full":0.125,"513100_mix_a13_post":0.346,
 "513100_trend_a13_full":0.1623,"513100_trend_a13_post":0.357,
 "513100_mix_gold":-0.0574}
dev={}
for k_,v_ in ANCH.items():
    if isinstance(v_,dict):
        got=rep[k_]["ann"]; dev[k_]=round(got-v_["ann"],4)
    else:
        got=rep.get(k_); dev[k_]=round(got-v_,4)
json.dump({"replication":rep,"anchor_deviation":dev},open(f"{R}/out/e2_replication.json","w"),indent=1)

# ---------- Part B: official E2 run, frozen shift(1): signal k end -> held month k+1 ----------
months=ks[13:]                      # n=139: 2015-02..2026-08 (frozen sample)
ki={k:i for i,k in enumerate(ks)}
def wser(c,key):
    return {k:sig_w(c,k,key) for k in ks}
W1=wser("sh513100","mix"); W2=wser("sh513500","mix"); W3=wser("sh513100","trend")

def run_shift(W,code,rate):
    """official: w(k) applied to month k+1 returns, both legs; cost=|dw|*rate on QDII leg"""
    out={}
    prev_w=0.0
    for j,k in enumerate(months):
        pk=ks[ki[k]-1]                # signal month = k-1
        w=W.get(pk,np.nan)
        dw=abs(w-prev_w)
        ra=rets[code].get(k,np.nan); rm=float(mmf_m.get(k,np.nan))
        gross=w*ra
        cashg=w*ra+(1-w)*rm
        net=cashg-dw*rate
        out[k]={"w_sig":round(float(w),6) if pd.notna(w) else np.nan,"ra":ra,"rm":rm,
                "gross":gross,"cash_gross":cashg,"net":net,"cost":dw*rate,"dw":dw}
        prev_w=w
    return pd.DataFrame(out).T

V1n=run_shift(W1,"sh513100",0.002)   # cost v2 = 0.1%+0.1%
V2n=run_shift(W2,"sh513500",0.002)
V3n=run_shift(W3,"sh513100",0.002)
V1g15=run_shift(W1,"sh513100",0.0015)
V1g30=run_shift(W1,"sh513100",0.0030)

# B&H same window (n=139) + full history (n=159)
bh_same=rets["sh513100"].reindex(months)
bh_full=rets["sh513100"].dropna()

met={"V1_net":stats(V1n["net"]),"V1_cash_gross":stats(V1n["cash_gross"]),"V1_gross":stats(V1n["gross"]),
     "V2_net":stats(V2n["net"]),"V3_net":stats(V3n["net"]),
     "V1_net_g15":stats(V1g15["net"]),"V1_net_g30":stats(V1g30["net"]),
     "BH_same":stats(bh_same),"BH_full":stats(bh_full),
     "V1_avgpos":round(float(V1n["w_sig"].mean()),3),"V2_avgpos":round(float(V2n["w_sig"].mean()),3),
     "V3_avgpos":round(float(V3n["w_sig"].mean()),3),
     "turnover_ann":round(float(V1n["dw"].sum()/(len(V1n)/12)),3),
     "cost_drag_ann":round(float(V1n["cost"].mean()*12),5)}

# ---------- Part C: correlations & gates ----------
V1net=V1n["net"].astype(float)
pair_a13=pd.concat([V1net,a13m],axis=1,join="inner").dropna()
pair_gold=pd.concat([V1net,goldm],axis=1,join="inner").dropna()
def corr_static(m,sub=None):
    x,y=m.iloc[:,0],m.iloc[:,1]
    if sub is not None: x,y=x[sub],y[sub]
    return round(float(np.corrcoef(x,y)[0,1]),4), int(len(x))
c_a13_full,n_a13=corr_static(pair_a13)
c_a13_post,_=corr_static(pair_a13,pair_a13.index>=202001)
c_gold,n_gold=corr_static(pair_gold)
# rolling 6-month windows over a13 overlap
wc=[]
vals=pair_a13.values
for i in range(len(pair_a13)-5):
    x=vals[i:i+6,0]; y=vals[i:i+6,1]
    if np.std(x)>0 and np.std(y)>0:
        wc.append((str(pair_a13.index[i]),float(np.corrcoef(x,y)[0,1])))
wseries=pd.DataFrame(wc,columns=["win_start","corr"]).set_index("win_start")
wseries.to_csv(f"{R}/out/e2_g3_rolling_corr.csv")
med=float(wseries["corr"].median()); mx=float(wseries["corr"].max())
nwin=len(wseries); n_gt35=int((wseries["corr"]>0.35).sum()); n_gt45=int((wseries["corr"]>0.45).sum())

# G4 subwindow: excl 2024-2026 -> ..2023-12
sub=V1n[V1n.index<=202312]
sub_bh=bh_same[bh_same.index<=202312]
g4_ex=float(stats(sub["net"])["ann"])-float(stats(sub_bh)["ann"])
g4_mdd=float(stats(sub["net"])["mdd"])

# G0 official (shift(1)) vs published anchors
g0={"pos_V1":{"got":met["V1_avgpos"],"ref":0.481,"dev_pp":round(met["V1_avgpos"]-0.481,3)},
    "pos_V2":{"got":met["V2_avgpos"],"ref":0.526,"dev_pp":round(met["V2_avgpos"]-0.526,3)},
    "cashann_V1":{"got":met["V1_cash_gross"]["ann"],"ref":0.1638,"dev_rel":round(met["V1_cash_gross"]["ann"]/0.1638-1,4)},
    "cashann_V2":{"got":stats(V2n["cash_gross"])["ann"],"ref":0.1581,"dev_rel":round(stats(V2n["cash_gross"])["ann"]/0.1581-1,4)},
    "corr_mix_a13_full":{"got":c_a13_full,"ref":0.125,"dev":round(c_a13_full-0.125,4)},
    "corr_mix_a13_post":{"got":c_a13_post,"ref":0.346,"dev":round(c_a13_post-0.346,4)},
    "corr_mix_gold":{"got":c_gold,"ref":-0.0574,"dev":round(c_gold-(-0.0574),4)},
    "replication_dev":dev}

# gates
bh_ann=float(stats(bh_same)["ann"]); bh_cal=float(stats(bh_same)["calmar"])
v1_ann=float(met["V1_net"]["ann"]); v1_cal=float(met["V1_net"]["calmar"]); v1_mdd=float(met["V1_net"]["mdd"])
gates={
 "G1":{"excess_ann":round(v1_ann-bh_ann,4),"thr":0.02,"calmar_ratio":round(v1_cal/bh_cal,3),"thr_cal":1.5,
       "PASS":bool((v1_ann-bh_ann)>=0.02 and v1_cal>=1.5*bh_cal)},
 "G2":{"net_mdd":v1_mdd,"thr":-0.15,"PASS":bool(v1_mdd>=-0.15)},
 "G3_vs_a13":{"static_full":c_a13_full,"static_post2020":c_a13_post,"n_overlap":n_a13,
       "rolling_median":round(med,4),"rolling_max":round(mx,4),"n_windows":nwin,
       "n_win_gt_obs035":n_gt35,"n_win_gt_term045":n_gt45,
       "PASS":bool(med<=0.45 and n_gt45==0),
       "obs_tag":bool(med>0.35)},
 "G3_vs_gold":{"corr":c_gold,"n_overlap":n_gold,"thr":0.15,"PASS":bool(c_gold<=0.15)},
 "G4":{"excess_ann_sub":round(g4_ex,4),"mdd_sub":round(g4_mdd,4),
       "PASS":bool(g4_ex>0 and g4_mdd>=-0.15),"sub_span":f"{sub.index.min()}..{sub.index.max()}"},
 "G5":{"calmar_0.15":met["V1_net_g15"]["calmar"],"calmar_0.30":met["V1_net_g30"]["calmar"],
       "PASS_friction":bool(met["V1_net_g15"]["calmar"]>1 and met["V1_net_g30"]["calmar"]>1),
       "PASS":None,"premium":"see_partD"},
}

# ---------- Part D: premium friction (F2 closure) ----------
prem_summary={}
for code,cod in [("sh513100","513100"),("sh513500","513500")]:
    nav=pd.read_csv(f"{R}/raw/{cod}_official_nav.csv",parse_dates=["date"])
    nav["k"]=ym(nav["date"]); navm=nav.set_index("k")["nav"]  # monthly avg nav not needed; daily used below
    px=pd.read_csv(f"{R}/raw/{code}_sina_raw.csv",parse_dates=["date"]).sort_values("date")
    px["k"]=ym(px["date"])
    m=px.merge(nav[["date","nav"]],on="date",how="inner")
    m["prem"]=m["close"]/m["nav"]-1
    # rebalance events: months where official V1 dw != 0 -> trade at first trading day of that month
    trade_ks=set(V1n[V1n["dw"]>1e-9].index) if cod=="513100" else set(V2n[V2n["dw"]>1e-9].index)
    m=m.sort_values("date")
    first_day=m.groupby("k").first().reset_index()
    ev=first_day[first_day["k"].isin(trade_ks)]
    abs_full=float(m["prem"].abs().mean()); abs_ev=float(ev["prem"].abs().mean())
    prem_summary[cod]={"n_days":int(len(m)),
      "prem_mean":round(float(m["prem"].mean()),5),"prem_median":round(float(m["prem"].median()),5),
      "prem_p05":round(float(m["prem"].quantile(0.05)),5),"prem_p95":round(float(m["prem"].quantile(0.95)),5),
      "abs_prem_mean_full":round(abs_full,5),
      "rebalance_events":int(len(ev)),"abs_prem_mean_at_rebalance":round(abs_ev,5),
      "abs_prem_p95_at_rebalance":round(float(ev["prem"].abs().quantile(0.95)),5)}
    if cod=="513100":
        gates["G5"]["premium_abs_at_rebalance"]=round(abs_ev,5)
        gates["G5"]["PASS_premium_T2"]=bool(abs_ev<=0.005)
        gates["G5"]["PASS"]=bool(gates["G5"]["PASS_friction"] and abs_ev<=0.005)
    m[["date","close","nav","prem"]].to_csv(f"{R}/out/e2_premium_{cod}.csv",index=False)

allpass=all([gates["G1"]["PASS"],gates["G2"]["PASS"],gates["G3_vs_a13"]["PASS"],
             gates["G3_vs_gold"]["PASS"],gates["G4"]["PASS"],gates["G5"]["PASS"]])
gates["ALL_PASS"]=bool(allpass)

# ---------- outputs ----------
panel=pd.DataFrame({"k":V1n.index,
  "w1_sig":[V1n.loc[k,"w_sig"] for k in V1n.index],"w2_sig":[V2n.loc[k,"w_sig"] for k in V1n.index],
  "ra_513100":[V1n.loc[k,"ra"] for k in V1n.index],"rm_mmf":[V1n.loc[k,"rm"] for k in V1n.index],
  "v1_gross":[V1n.loc[k,"gross"] for k in V1n.index],"v1_cash_gross":[V1n.loc[k,"cash_gross"] for k in V1n.index],
  "v1_net":[V1n.loc[k,"net"] for k in V1n.index],"v1_cost":[V1n.loc[k,"cost"] for k in V1n.index],
  "v2_net":[V2n.loc[k,"net"] for k in V1n.index],"v3_net":[V3n.loc[k,"net"] for k in V1n.index],
  "bh_513100":[bh_same.get(k,np.nan) for k in V1n.index],
  "a13_ret":[a13m.get(k,np.nan) for k in V1n.index],"gold_ret":[goldm.get(k,np.nan) for k in V1n.index]})
panel.to_csv(f"{R}/out/e2_monthly_panel.csv",index=False)
for name,ser in [("V1_net",V1n["net"]),("V1_cash_gross",V1n["cash_gross"]),("V2_net",V2n["net"]),("V3_net",V3n["net"])]:
    pass
navs=pd.DataFrame({nm:(1+s.fillna(0)).cumprod() for nm,s in
    [("V1_net",V1n["net"]),("V1_cash_gross",V1n["cash_gross"]),("V1_net_g15",V1g15["net"]),
     ("V1_net_g30",V1g30["net"]),("V2_net",V2n["net"]),("V3_net",V3n["net"]),
     ("BH_same",bh_same)]})
navs.to_csv(f"{R}/out/e2_nav_series.csv")
met["corr"]={"v1net_a13_full":c_a13_full,"v1net_a13_post2020":c_a13_post,"v1net_gold":c_gold}
json.dump({"metrics":met,"gates":gates,"g0_shift_vs_published":g0,"prem_summary":prem_summary},
          open(f"{R}/out/e2_gate_results.json","w"),indent=1,ensure_ascii=False)
print(json.dumps({"gates":gates},ensure_ascii=False)[:1500])
print("METRICS:",json.dumps(met,ensure_ascii=False)[:800])
