import pandas as pd, numpy as np, json
out="/home/noname/quant-evolve/results/r272/"
res={}
# ---------- in-library raw ----------
sig=pd.read_parquet("/home/noname/quant-evolve/results/timing_v2/signal_series.parquet")[["M_micro_ew"]]
sig.index=pd.to_datetime(sig.index)
r=np.log(sig["M_micro_ew"]).diff()
sig["rv20"]=r.rolling(20).std()*np.sqrt(252)
sig["d"]=sig.index
sig["ym"]=sig.index.to_period("M")
# month-end rows + next-month stats
g=sig.groupby("ym")
me=g.tail(1).set_index("ym")            # month-end rv20 etc
nxt=pd.DataFrame(index=me.index)
nxt["mkt_next"]=g["M_micro_ew"].last().pct_change().shift(-1)   # ret of month t+1
nxt["pos_end"]=g["M_micro_ew"].last().pct_change()  # not used
# month-internal MDD of next month
sig["cum"]=sig["M_micro_ew"]
def mdd_month(gr):
    v=gr["M_micro_ew"].values; peak=np.maximum.accumulate(v); return ((v/peak)-1).min()
mdm=sig.groupby("ym").apply(mdd_month)
nxt["mdd_next"]=mdm.shift(-1)
# a13 monthly
a13=pd.read_csv("/home/noname/quant-evolve/results/a13_rsraw_e1f10dz_full_nav.csv")
a13["d"]=pd.to_datetime(a13["date"]); a13["ym"]=a13["d"].dt.to_period("M")
nxt["a13_next"]=a13.groupby("ym")["nav"].last().pct_change().shift(-1)
# cross-check RV vs r250
rv250=pd.read_csv("/home/noname/quant-evolve/results/r250/rv_monthly_v2.csv",index_col=0)
rv250.index=pd.to_datetime(rv250.index).to_period("M")
j=pd.concat([me["rv20"],rv250["rv20"]],axis=1,keys=["mine","r250"]).dropna()
res["rv_crosscheck_corr"]=round(j["mine"].corr(j["r250"]),4)
# ---------- sentiment signals ----------
# QVIX daily
q=pd.read_csv(out+"qvix50.csv"); q["d"]=pd.to_datetime(q["date"]); q["close"]=pd.to_numeric(q["close"],errors="coerce")
q=q.set_index("d")["close"].sort_index()
def rollpct(s,w=756,mp=252):
    return s.rolling(w,min_periods=mp).apply(lambda x:(x.iloc[-1]>=x).mean(),raw=False)
qme=q.groupby(q.index.to_period("M")).last()
# iv-rv daily
ivrv=(q - sig["rv20"]).dropna()
ivrv_pct=rollpct(ivrv); ivrv_me=ivrv.groupby(ivrv.index.to_period("M")).last()
ivrvpct_me=ivrv_pct.groupby(ivrv_pct.index.to_period("M")).last()
q_pct=rollpct(q); qpct_me=q_pct.groupby(q_pct.index.to_period("M")).last()
# qvix300 backfill check
q3=pd.read_csv(out+"qvix300.csv"); q3["d"]=pd.to_datetime(q3["date"])
qq=pd.DataFrame({"d":q3["d"],"c300":pd.to_numeric(q3["close"],errors="coerce")}).merge(
    pd.DataFrame({"d":q.index,"c50":q.values}),on="d")
pre=qq[qq["d"]<"2019-12-23"].dropna()
res["qvix300_eq50_pre2019"]=round((pre["c300"]==pre["c50"]).mean(),4); res["qvix300_pre_n"]=len(pre)
# PCR monthly
p=pd.read_csv(out+"pcr_monthend.csv")
for c in ["认购成交量","认沽成交量","未平仓认购合约数","未平仓认沽合约数","总成交量"]:
    p[c]=pd.to_numeric(p[c],errors="coerce")
pg=p.groupby("ym").agg(call=("认购成交量","sum"),put=("认沽成交量","sum"),
                       oic=("未平仓认购合约数","sum"),oip=("未平仓认沽合约数","sum"))
pg["pcr_vol"]=pg["put"]/pg["call"]; pg["pcr_oi"]=pg["oip"]/pg["oic"]
pg.index=pd.to_datetime(pg.index.astype(str),format="%Y%m").to_period("M")
pcr_pct=pg["pcr_vol"].rolling(36,min_periods=24).apply(lambda x:(x.iloc[-1]>=x).mean(),raw=False)
oi_pct=pg["pcr_oi"].rolling(36,min_periods=24).apply(lambda x:(x.iloc[-1]>=x).mean(),raw=False)
# margin monthly change
mrg=pd.read_csv(out+"margin_sse_full.csv")
mrg["ym"]=pd.to_datetime(mrg["信用交易日期"],format="%Y%m%d").dt.to_period("M")
mrg["_rz"]=pd.to_numeric(mrg["融资余额"],errors="coerce")
mb=mrg.groupby("ym")["_rz"].last()
mdelta=mb.pct_change()
md_pct=mdelta.rolling(36,min_periods=24).apply(lambda x:(x.iloc[-1]>=x).mean(),raw=False)
# ---------- panel ----------
P=pd.DataFrame(index=nxt.index)
P["mkt_next"]=nxt["mkt_next"]; P["mdd_next"]=nxt["mdd_next"]; P["a13_next"]=nxt["a13_next"]
P["qvix"]=qme; P["qvix_pct"]=qpct_me
P["ivrv"]=ivrv_me; P["ivrv_pct"]=ivrvpct_me
P["pcr"]=pg["pcr_vol"]; P["pcr_pct"]=pcr_pct; P["pcroi_pct"]=oi_pct
P["mdelta"]=mdelta; P["md_pct"]=md_pct
P["rv20"]=me["rv20"]; P["rv_pct"]=rv250["rv_pct"]; P["rv_state"]=rv250["rv_state"]
P.to_csv(out+"monthly_panel.csv")
# ---------- conditional profile ----------
def cell(df,mask,col="mkt_next"):
    s=df[mask][col].dropna()
    if len(s)==0: return dict(n=0)
    return dict(n=int(len(s)),mean=round(100*s.mean(),2),win=round(100*(s>0).mean(),3),
                mdd=round(100*df[mask]["mdd_next"].dropna().mean(),2),
                a13=round(100*df[mask]["a13_next"].dropna().mean(),2))
def prof(P,pc,name,split,bound):
    d={"signal":name}
    valid=P[pc].notna()&P["mkt_next"].notna()
    df=P[valid]
    d["sample"]=[str(df.index[0]),str(df.index[-1]),len(df)]
    d["uncond"]=cell(df,pd.Series(True,index=df.index))
    lo=None; hi=None
    d["low"]=cell(df,df[pc]<=0.30); d["high"]=cell(df,df[pc]>=0.70)
    # hypo cell + split-half
    for tag,cond in [("low",df[pc]<=0.30),("high",df[pc]>=0.70)]:
        a=cond&(df.index.to_timestamp()<bound); b=cond&(df.index.to_timestamp()>=bound)
        d[f"{tag}_pre"]=cell(df,a); d[f"{tag}_post"]=cell(df,b)
    # dedup vs rv
    hh=(P[pc]>=0.70)&(P["rv_state"]=="high"); ll=(P[pc]<=0.30)&(P["rv_state"]=="low")
    both=((P[pc]>=0.70)|(P[pc]<=0.30))&P[pc].notna()
    jhi=((P[pc]>=0.70)&(P["rv_state"]=="high")).sum()/max(((P[pc]>=0.70)|(P["rv_state"]=="high")).sum(),1)
    d["jaccard_hi_vs_rvhi"]=round(jhi,3)
    d["corr_sig_rv"]=round(P[[pc.replace("_pct",""),"rv20"]].corr().iloc[0,1],3) if pc.replace("_pct","") in P else None
    return d
b_qp=pd.Timestamp("2020-12-31"); b_m=pd.Timestamp("2018-08-31")
res["profiles"]={
 "qvix":prof(P,"qvix_pct","QVIX50",None,b_qp),
 "ivrv":prof(P,"ivrv_pct","IV-RV",None,b_qp),
 "pcr":prof(P,"pcr_pct","PCR_vol",None,b_qp),
 "pcroi":prof(P,"pcroi_pct","PCR_oi",None,b_qp),
 "mdelta":prof(P,"md_pct","MarginDelta",None,b_m),
}
# flagship months states
fm=["2015-05","2015-06","2018-01","2024-01","2024-02","2024-09","2026-05","2026-06"]
flag=P.loc[[x for x in fm if pd.Period(x,"M") in P.index],[pc for pc in ["qvix","qvix_pct","ivrv","ivrv_pct","pcr","pcr_pct","mdelta","md_pct","rv20","rv_state"]]]
res["flagship"]=flag.round(3).to_string()
json.dump(res,open(out+"profile.json","w"),ensure_ascii=False,indent=1,default=str)
print(json.dumps(res,ensure_ascii=False,indent=1,default=str))
