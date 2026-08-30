import pandas as pd, numpy as np, os, sys, bisect
sys.path.insert(0,"/home/noname/quant-evolve/scripts")
from cost_model_v2 import estimate_cost
R="/home/noname/quant-evolve/results"; KLINE="/home/noname/quant-evolve/data/all_stocks_qfq"; CAP=1e7
hold=pd.read_csv(f"{R}/a13_rsraw_e1f10dz_full_holdings.csv",parse_dates=["date"])
hold=hold[hold["num_target"].fillna(0)>0]
reb=sorted(hold["date"].tolist()); hm={r["date"]:[c for c in str(r["target"]).split("|") if c] for _,r in hold.iterrows()}
def load(c):
    p=os.path.join(KLINE,c+"_daily_qfq.parquet")
    if not os.path.exists(p): p=os.path.join(KLINE,c+".parquet")
    if not os.path.exists(p): return None
    df=pd.read_parquet(p); df.columns=[str(x).lower() for x in df.columns]
    return df.set_index(pd.to_datetime(df["date"]))["amount"].astype(float).sort_index()
d=pd.Timestamp("2006-02-20")  # 首个闸切换执行日
ri=bisect.bisect_right(reb,d)-1; codes=hm[reb[ri]]
for tag,dpv,pv in [("FULL",1.0,1.0*CAP),("HALF",0.5,1.0*CAP)]:
    tot=0; n=0
    for c in codes:
        s=load(c)
        adv=s[s.index<=d].iloc[-20:].mean() if s is not None else np.nan
        est=estimate_cost(dpv/len(codes)*pv, adv, side="sell")
        if est: tot+=est["total_bps"]/1e4/len(codes); n+=1
        if c==codes[0]: print(tag,c,"adv=%.3e"%adv,"order=%.3e"%(dpv/len(codes)*pv),"bps=%.1f"%(est["total_bps"] if est else -1))
    print(tag,"cost_frac=%.5f (%.1f bp) valid n=%d"%(tot,tot*1e4,n))
