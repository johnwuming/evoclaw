#!/usr/bin/env python3
# task-0442 R-274: A股真宇宙覆盖率审计 + Sloan应计IC画像 (零回测, E1)
import os, json
from collections import Counter, defaultdict
import numpy as np, pandas as pd
from scipy.stats import spearmanr

HP = os.path.expanduser("~/quant-evolve")
FD = os.path.join(HP, "data", "fin_deep")

# ---- 1. A股参照宇宙: r0414 panel (W1可交易口径 ever) ----
z = np.load(os.path.join(HP, "results/work/r0414/panel.npz"), allow_pickle=True)
codes_ref = z["codes"].tolist(); codes_set = set(codes_ref)
pref = Counter(c[:3] if c[:2] in ("60","68") else c[:2] for c in codes_ref)
print("A股参照宇宙 r0414 panel:", len(codes_ref), "prefix:", dict(pref.most_common(10)))

# ---- 2. 四表 ----
yj = pd.read_parquet(os.path.join(FD,"yjbb.parquet"), columns=["code","report_period","net_profit","pubDate"])
xj = pd.read_parquet(os.path.join(FD,"xjll.parquet"), columns=["code","report_period","ocf","pubDate"])
zc = pd.read_parquet(os.path.join(FD,"zcfz.parquet"), columns=["code","report_period","total_asset","pubDate"])
for df in (yj,xj,zc): df["code"]=df["code"].astype(str).str.zfill(6)
yj_a=yj[yj.code.isin(codes_set)]; xj_a=xj[xj.code.isin(codes_set)]; zc_a=zc[zc.code.isin(codes_set)]
print("A股口径行数: yjbb", len(yj_a), "xjll", len(xj_a), "zcfz", len(zc_a))

np_ok=set(map(tuple,yj_a.dropna(subset=["net_profit"])[["code","report_period"]].values))
ocf_ok=set(map(tuple,xj_a.dropna(subset=["ocf"])[["code","report_period"]].values))
ta_ok=set(map(tuple,zc_a.dropna(subset=["total_asset"])[["code","report_period"]].values))
per_all=sorted(set(yj_a.report_period)|set(xj_a.report_period)|set(zc_a.report_period))
rows=[]
for p in per_all:
    np_s={c for c,q in np_ok if q==p}; ocf_s={c for c,q in ocf_ok if q==p}; ta_s={c for c,q in ta_ok if q==p}
    tri=np_s&ocf_s&ta_s; denom=max(len(np_s|ocf_s|ta_s),1)
    rows.append(dict(p=p,np=len(np_s),ocf=len(ocf_s),ta=len(ta_s),triple=len(tri),cov=round(100*len(tri)/denom,1)))
cov=pd.DataFrame(rows); cov["yr"]=cov.p.str[:4]
byy=cov.groupby("yr").apply(lambda d:{"期数":len(d),"triple":int(d.triple.sum()),"分母":int(d[["np","ocf","ta"]].max(axis=1).sum()),"cov%":round(100*d.triple.sum()/max(d[["np","ocf","ta"]].max(axis=1).sum(),1),1)})
print("=== 逐期A股三要素覆盖(按年) ===")
for y,v in byy.items(): print(y, v)
print("20260630单期:", cov[cov.p=="20260630"].to_dict("records"))

xj_all=set(map(tuple,xj[["code","report_period"]].values))
yj_only=[(c,p) for (c,p) in np_ok if (c,p) not in xj_all]
print("yjbb有净利但xjll无该行(A股,全86期):",len(yj_only),"例; 按年:",dict(Counter(p[:4] for c,p in yj_only).most_common(10)))
json.dump({"cov_by_year":{k:v for k,v in byy.items()},"yj_only_n":len(yj_only),"yj_only_by_yr":dict(Counter(p[:4] for c,p in yj_only))}, open(os.path.join(HP,"results/work/r274/breadth.json"),"w"), ensure_ascii=False, indent=1, default=str)
np.save(os.path.join(HP,"results/work/r274/yj_only.npy"), np.array(yj_only, dtype="U10"))

# ---- 3. Sloan 应计 (TTM, 分母=上一期总资产) + PIT ----
pit_path=os.path.join(HP,"data/pit_disclosure_map.parquet")
pit=pd.read_parquet(pit_path) if os.path.exists(pit_path) else None
LEGAL={1:lambda y:pd.Timestamp(y,4,30),2:lambda y:pd.Timestamp(y,8,31),3:lambda y:pd.Timestamp(y,10,31),4:lambda y:pd.Timestamp(y+1,4,30)}
w=yj_a[["code","report_period","net_profit","pubDate"]].rename(columns={"net_profit":"np"}).merge(
  xj_a[["code","report_period","ocf","pubDate"]],on=["code","report_period"],how="outer",suffixes=("","_xj")).merge(
  zc_a[["code","report_period","total_asset","pubDate"]],on=["code","report_period"],how="outer",suffixes=("","_zc"))
pubcols=[c for c in w.columns if c.startswith("pubDate")]
w["pubMax"]=pd.to_datetime(w[pubcols].apply(lambda r: pd.to_datetime(r, errors="coerce").max(), axis=1), errors="coerce")
w["statDate"]=pd.to_datetime(w["report_period"])
if pit is not None:
    p2=pit.copy(); p2["code"]=p2["code"].astype(str).str.zfill(6)
    p2=p2.rename(columns={"report_period":"statDate"})[["code","statDate","usable_from"]]
    p2["statDate"]=pd.to_datetime(p2["statDate"]); p2["usable_from"]=pd.to_datetime(p2["usable_from"])
    w=w.merge(p2,on=["code","statDate"],how="left")
else: w["usable_from"]=pd.NaT
pt=w.statDate.dt.month.map({3:1,6:2,9:3,12:4}); yr=w.statDate.dt.year
w["usable_from"]=pd.to_datetime(w["usable_from"]).fillna(pd.Series([LEGAL[pv](yv)+pd.Timedelta(days=1) for pv,yv in zip(pt,yr)],index=w.index))
w["usable_from"]=pd.concat([w["usable_from"],w["pubMax"]+pd.Timedelta(days=1)],axis=1).max(axis=1)
w=w.sort_values(["code","statDate"])
def ttm_calc(df):
    df=df.set_index("statDate")
    idx=df.index
    col_np=df["np"]; col_ocf=df["ocf"]; col_ta=df["total_asset"]
    ttm_np=[]; ttm_ocf=[]
    for t in idx:
        y=t.year-1; same=pd.Timestamp(y,t.month,t.day); ann=pd.Timestamp(y,12,31)
        a=col_np.get(t,np.nan); b=col_np.get(ann,np.nan); c=col_np.get(same,np.nan)
        ttm_np.append(a+b-c if pd.notna(a) and pd.notna(b) and pd.notna(c) else np.nan)
        a=col_ocf.get(t,np.nan); b=col_ocf.get(ann,np.nan); c=col_ocf.get(same,np.nan)
        ttm_ocf.append(a+b-c if pd.notna(a) and pd.notna(b) and pd.notna(c) else np.nan)
    ta_lag=col_ta.shift(1)
    acc=(pd.Series(ttm_np,index=idx)-pd.Series(ttm_ocf,index=idx))/ta_lag
    out=pd.DataFrame({"usable_from":df["usable_from"].values,"acc":acc.values},index=idx).dropna(subset=["usable_from"])
    return out
parts=[]
for _cd,g in w.groupby("code"):
    if len(g)>=5:
        t=ttm_calc(g); t["code"]=_cd; parts.append(t)
q=pd.concat(parts).reset_index()
print("Sloan应计(TTM/滞后TA)季度观测:",len(q))

# ---- 4. 月度 as-of + IC (W1: spearman(F[m],R[m+1]), min_obs=20, MASK池) ----
months=z["months"]; codes=z["codes"]; R=z["R"]; MASK=z["MASK"]
month_end=pd.to_datetime(months.astype(str)+"-28")
qmap={c:g[["usable_from","acc"]].sort_values("usable_from") for c,g in q.groupby("code")}
n_c,n_m=len(codes),len(months)
F=np.full((n_c,n_m),np.nan,dtype=np.float64)
for i,code in enumerate(codes):
    sub=qmap.get(code)
    if sub is None: continue
    uf=sub["usable_from"].values; ac=sub["acc"].values
    pos=np.searchsorted(uf,month_end.values,side="right")-1
    ok=pos>=0; pc=np.clip(pos,0,len(ac)-1)
    F[i]=np.where(ok,ac[pc],np.nan)
qual=-F  # 质量口径: 低应计=高质量
ics=[];covs=[];qs=[[] for _ in range(5)]
for m in range(n_m-1):
    mk=MASK[:,m]&~np.isnan(qual[:,m])&~np.isnan(R[:,m+1])
    covs.append(float(np.mean(MASK[:,m]&~np.isnan(qual[:,m]))) if MASK[:,m].any() else 0.0)
    if mk.sum()>=20:
        ic=spearmanr(qual[mk,m],R[mk,m+1]).statistic
        ics.append((str(months[m]),float(ic)))
        o=np.argsort(np.argsort(qual[mk,m])); k=o.astype(float)
        for qi in range(5):
            sel=(k>=qi*len(k)/5)&(k<(qi+1)*len(k)/5)
            qs[qi].append(float(np.mean(R[mk,m+1][sel])))
ic_s=pd.Series({m:v for m,v in ics})
seg=np.array_split(ic_s.index.astype(str),5)
print("=== Sloan应计IC画像 (qual=-accrual, 正IC=低应计跑赢) ===")
print("月数:",len(ic_s)," meanIC:",round(ic_s.mean(),4)," ICIR:",round(ic_s.mean()/ic_s.std(),3)," 平均覆盖率(月均):",round(float(np.mean(covs)),3))
print("五分段ICIR:",[round(ic_s.loc[s].mean()/ic_s.loc[s].std(),2) for s in seg])
ic_s.index=pd.to_datetime(ic_s.index+"-28")
print("分年IC:",{str(y):round(v,4) for y,v in ic_s.groupby(ic_s.index.year).mean().items()})
print("五分位月均次月收益 Q1..Q5:",[round(float(np.mean(x)),5) for x in qs])
out={"n_months":len(ic_s),"mean_ic":float(ic_s.mean()),"icir":float(ic_s.mean()/ic_s.std()),"mean_cov":float(np.mean(covs)),
     "seg_icir":[float(ic_s.loc[s].mean()/ic_s.loc[s].std()) for s in seg],
     "by_year":{str(y):float(v) for y,v in ic_s.groupby(ic_s.index.year).mean().items()},
     "quintile_next_ret":[float(np.mean(x)) for x in qs],
     "ic_positive_share":float((ic_s>0).mean()),"n_quarter_obs":len(q)}
json.dump(out,open(os.path.join(HP,"results/work/r274/sloan_ic.json"),"w"),indent=1)
ic_s.to_csv(os.path.join(HP,"results/work/r274/sloan_ic_monthly.csv"))
print("DONE")
