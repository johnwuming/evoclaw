#!/usr/bin/env python3
# task-0442 R-274: 分层抽样源核验 v2 — sina 个股现金流量表 (stock_financial_report_sina)
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
print("分层(每年3例)样本:",len(sample),"年份:",sorted(by_yr),flush=True)

_cache={}
def sina_cf(code):
    if code in _cache: return _cache[code]
    sym=("sh" if code[0]=="6" else "sz")+code
    try:
        df=ak.stock_financial_report_sina(stock=sym, symbol="现金流量表")
        if df is None or len(df)==0:
            r=pd.DataFrame()
        else:
            datecol=[c for c in df.columns if "日期" in c][0]
            ocfcol=[c for c in df.columns if "经营活动产生的现金流量净额"==c]
            r=df[[datecol]+ocfcol].copy()
            r.columns=["rdate","ocf"] if ocfcol else ["rdate"]
            if ocfcol:
                r["ocf"]=pd.to_numeric(r["ocf"],errors="coerce")
            r["rdate"]=r["rdate"].astype(str).str.replace("-","")
        _cache[code]=r
        return r
    except Exception as e:
        _cache[code]=repr(e)[:80]
        return _cache[code]

def classify(code,period):
    r=sina_cf(code)
    if isinstance(r,str): return "接口ERR:"+r[:50]
    tgt=period
    hit=r[r.rdate==tgt]
    if len(hit)==0: return "源无该期行(共%d期)"%len(r)
    if "ocf" not in hit.columns or pd.isna(hit.iloc[0]["ocf"]): return "源有行但OCF空"
    return "源有OCF=%.0f"%hit.iloc[0]["ocf"]

res=[]
for i,(code,period) in enumerate(sample):
    s=classify(code,period)
    res.append(dict(code=code,period=period,sina=s))
    if i%8==0: print(i,code,period,s,flush=True)
    time.sleep(1.0)
json.dump(res,open(HP+"/results/work/r274/sample_missing.json","w"),ensure_ascii=False,indent=1)
from collections import Counter
print("缺失样本分类:",dict(Counter(("无行" if "无该期行" in x["sina"] else "有行" if "有OCF" in x["sina"] else "空值/ERR") for x in res)),flush=True)

# 对照组: xjll 有值 5 对, 数值一致性 (单位均元)
xj=pd.read_parquet(HP+"/data/fin_deep/xjll.parquet",columns=["code","report_period","ocf"])
ctl=[]
for p in ["20070331","20120630","20170930","20220331","20250630"]:
    d=xj[(xj.report_period==p)&xj.ocf.notna()]
    if not len(d): continue
    row=d.sample(1,random_state=274).iloc[0]
    s=classify(row.code,p)
    m=""
    if "有OCF=" in s:
        sv=float(s.split("=")[1]); bv=float(row.ocf)
        m="一致" if abs(sv-bv)<=max(1,abs(bv)*0.001) else "不一致(源=%.0f 批=%.0f)"%(sv,bv)
    ctl.append(dict(code=row.code,period=p,batch_ocf=float(row.ocf),sina=s,check=m))
    print("CTL",row.code,p,round(float(row.ocf),1),s,m,flush=True)
    time.sleep(1.0)
json.dump(ctl,open(HP+"/results/work/r274/sample_control.json","w"),ensure_ascii=False,indent=1)
print("DONE-SAMPLE2")
