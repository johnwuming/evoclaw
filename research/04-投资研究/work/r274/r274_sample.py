#!/usr/bin/env python3
# task-0442 R-274: 分层抽样源核验 — 缺失对(A股) vs akshare 个股现金流量表源
import json, time, random
from collections import defaultdict
import numpy as np, pandas as pd
import akshare as ak

HP="/home/noname/quant-evolve"
random.seed(274)
yj_only=[(str(c),str(p)) for c,p in np.load(HP+"/results/work/r274/yj_only.npy")]
by_yr=defaultdict(list)
for c,p in yj_only: by_yr[p[:4]].append((c,p))
sample=[]
for yr in sorted(by_yr):
    sample+=random.sample(by_yr[yr], min(3,len(by_yr[yr])))
print("分层(每年3例)样本:",len(sample),"覆盖年份:",sorted(by_yr))

def query_src(code,period):
    try:
        df=ak.stock_cash_flow_sheet_em(symbol=code, period=period)
        if df is None or len(df)==0: return "源无该期行"
        col=[c for c in df.columns if c.upper()=="NETCASH_OPERATE"]
        if not col: return "源有行但无OCF列:"+",".join(df.columns[:5])
        v=df.iloc[0][col[0]]
        return ("源有OCF" if pd.notna(v) else "源有行OCF空")+f"={v}"
    except Exception as e:
        return "ERR:"+repr(e)[:70]

res=[]
for i,(code,period) in enumerate(sample):
    s=query_src(code,period)
    res.append(dict(code=code,period=period,akshare=s))
    if i%6==0: print(i,code,period,s,flush=True)
    time.sleep(1.2)
json.dump(res,open(HP+"/results/work/r274/sample_missing.json","w"),ensure_ascii=False,indent=1)

# 对照组: xjll 有值的 6 对, 数值一致性
xj=pd.read_parquet(HP+"/data/fin_deep/xjll.parquet",columns=["code","report_period","ocf"])
ctl_pool=[]
for p in ["20070331","20120630","20170930","20220331","20250630"]:
    d=xj[(xj.report_period==p)&xj.ocf.notna()]
    if len(d): ctl_pool.append((d.sample(1,random_state=274).code.iloc[0], p, d.ocf.iloc[0]))
ctl=[]
for code,period,v_batch in ctl_pool:
    s=query_src(code,period)
    ctl.append(dict(code=code,period=period,batch_ocf=float(v_batch),akshare=s))
    print("CTL",code,period,round(float(v_batch),1),s,flush=True)
    time.sleep(1.2)
json.dump(ctl,open(HP+"/results/work/r274/sample_control.json","w"),ensure_ascii=False,indent=1)
print("DONE-SAMPLE")
