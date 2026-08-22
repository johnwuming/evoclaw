import pandas as pd, numpy as np, json
out="/home/noname/quant-evolve/results/r272/"
P=pd.read_csv(out+"monthly_panel.csv",index_col=0); P.index=pd.to_datetime(P.index).to_period("M")
sig=pd.read_parquet("/home/noname/quant-evolve/results/timing_v2/signal_series.parquet")[["M_micro_ew"]]
sig.index=pd.to_datetime(sig.index); sig["ym"]=sig.index.to_period("M")
mret=sig.groupby("ym")["M_micro_ew"].last().pct_change()   # same-month return
P["mkt_t"]=mret
r={}
# pcr_oi corr with rv: need pcr_oi values
p=pd.read_csv(out+"pcr_monthend.csv")
for c in ["未平仓认购合约数","未平仓认沽合约数"]: p[c]=pd.to_numeric(p[c],errors="coerce")
pg=p.groupby("ym").agg(oic=("未平仓认购合约数","sum"),oip=("未平仓认沽合约数","sum"))
pg["pcr_oi"]=pg["oip"]/pg["oic"]; pg.index=pd.to_datetime(pg.index.astype(str),format="%Y%m").to_period("M")
j=pd.concat([pg["pcr_oi"],P["rv20"]],axis=1).dropna()
r["pcroi_rv_corr"]=round(j["pcr_oi"].corr(j["rv20"]),3)
# robustness for PCR low cells
for name,pc in [("pcr","pcr_pct"),("pcroi","pcroi_pct")]:
    d=P[P[pc].notna()&P["mkt_next"].notna()]
    lo=d[d[pc]<=0.30]["mkt_next"]
    r[name]={"n":len(lo),"median":round(100*lo.median(),2),
             "min":round(100*lo.min(),2),"max":round(100*lo.max(),2),
             "drop_worst_mean":round(100*lo.sort_values().iloc[1:].mean(),2),
             "drop_best_mean":round(100*lo.sort_values().iloc[:-1].mean(),2),
             "t":round(lo.mean()/(lo.std()/np.sqrt(len(lo))),2)}
    lm=d[d[pc]<=0.30]
    r[name]["months"]=[f"{str(i)}:{round(100*v,1)}" for i,v in lm["mkt_next"].items()]
    r[name]["past_mkt_t_mean"]=round(100*lm["mkt_t"].mean(),2)
    r[name]["win"]=round(100*(lo>0).mean(),1)
# reversal-proxy check: past-month top/bottom cells
d=P[P["mkt_t"].notna()&P["mkt_next"].notna()]
hi=d[d["mkt_t"]>=d["mkt_t"].quantile(0.7)]["mkt_next"]; lo2=d[d["mkt_t"]<=d["mkt_t"].quantile(0.3)]["mkt_next"]
r["reversal_proxy"]={"past_hi_next":round(100*hi.mean(),2),"n_hi":len(hi),"past_lo_next":round(100*lo2.mean(),2),"n_lo":len(lo2),"uncond":round(100*d["mkt_next"].mean(),2)}
r["corr_pcr_pct_mkt_t"]=round(P["pcr_pct"].corr(P["mkt_t"]),3)
# a13 robustness pcr low
d=P[P["pcr_pct"].notna()&P["a13_next"].notna()]
r["pcr_low_a13"]={"mean":round(100*d[d["pcr_pct"]<=0.30]["a13_next"].mean(),2),"n":int((d["pcr_pct"]<=0.30).sum()),"uncond":round(100*d["a13_next"].mean(),2)}
# qvix/ivrv pre/post for L3 note
print(json.dumps(r,ensure_ascii=False,indent=1,default=str))
