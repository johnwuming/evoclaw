#!/usr/bin/env python3
# r275_diag.py — 诊断: 为何大部分月份 len(a)<200 (PIT usable 门)
import glob, time, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
W = "/root/.openclaw/workspace/shared/results/work/r275"

A_PREFIX = ("000","001","002","003","300","301","302","600","601","603","605","688","689")
def is_a(c): return len(c)==6 and c[:3] in A_PREFIX

def load(tname, cols):
    frames=[]
    for f in sorted(glob.glob(f"{W}/chunks/{tname}_*.parquet")):
        p=f.split("_")[-1].split(".")[0]
        d=pd.read_parquet(f)
        if len(d)==0: continue
        d["statDate"]=p; frames.append(d)
    df=pd.concat(frames, ignore_index=True)
    df=df[df["code"].map(is_a)].copy()
    for c in cols:
        if c not in ("code","pubDate","statDate"):
            df[c]=pd.to_numeric(df[c], errors="coerce")
    df["pubDate"]=pd.to_datetime(df["pubDate"], errors="coerce")
    return df.drop_duplicates(["code","statDate"])

yj=load("yjbb",["net_profit","roe","gp_margin","revenue_yoy","net_profit_yoy"])
zc=load("zcfz",["total_asset"])
xj=load("xjll",["ocf"])
q=yj[["code","statDate","net_profit","pubDate"]].copy()
q=q.merge(xj[["code","statDate","ocf"]],on=["code","statDate"],how="inner")
q=q.merge(zc[["code","statDate","total_asset"]],on=["code","statDate"],how="inner")
q=q.dropna(subset=["net_profit","ocf","total_asset"])
q["dt"]=pd.to_datetime(q["statDate"],format="%Y%m%d")
q=q.sort_values(["code","dt"]).reset_index(drop=True)
print("pubDate null rate:", round(q["pubDate"].isna().mean(),3))
print("pubDate year dist:", q["pubDate"].dt.year.value_counts().sort_index().head(6).to_dict())
grp=q.groupby("code",sort=False)
q["np4"]=grp["net_profit"].rolling(4).sum().reset_index(0,drop=True)
q["ocf4"]=grp["ocf"].rolling(4).sum().reset_index(0,drop=True)
q["d0"]=grp["dt"].shift(3)
q["span_ok"]=(q["dt"]-q["d0"]).dt.days.between(270,278)
q["nrows"]=grp.cumcount()+1
acc=q[(q["span_ok"])&(q["nrows"]>=5)&(q["total_asset"]>0)].copy()
acc["accrual"]=(acc["np4"]-acc["ocf4"])/acc["total_asset"]
acc=acc.dropna(subset=["accrual"])
def deadline(sd):
    y,md=int(sd[:4]),sd[4:]
    if md=="0331": return pd.Timestamp(y,4,30)
    if md=="0630": return pd.Timestamp(y,8,31)
    if md=="0930": return pd.Timestamp(y,10,31)
    return pd.Timestamp(y+1,4,30)
acc["dl"]=acc["statDate"].map(deadline)
acc["pub"]=acc["pubDate"].fillna(acc["dl"])
acc["usable"]=acc[["dl","pub"]].max(axis=1)+pd.Timedelta(days=1)
print("acc rows:",len(acc),"usable year dist:",acc["usable"].dt.year.value_counts().sort_index().head(5).to_dict())
# 逐月 gate 计数
for m in ["2015-01-31","2015-04-30","2015-05-31","2015-07-31","2015-10-31","2020-07-31","2025-11-30"]:
    m=pd.Timestamp(m)
    a=acc[acc["usable"]<=m]
    n1=len(a); n_codes=a["code"].nunique()
    b=a.sort_values("usable").groupby("code").tail(1)
    b=b[(m-b["dt"]).dt.days<=400]
    print(f"{m.date()}: usable_ok={n1} (codes {n_codes}) -> tail1 {len(b)} -> staleness {len(b)}")
