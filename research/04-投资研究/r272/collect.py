import akshare as ak, pandas as pd, time, glob, warnings
warnings.filterwarnings("ignore")
out="/home/noname/quant-evolve/results/r272/"
# 1) margin paging
frames=[]
for s,e in [("20100301","20140101"),("20140101","20180601"),("20180601","20260822")]:
    try:
        df=ak.stock_margin_sse(start_date=s,end_date=e); frames.append(df); print("margin",s,e,df.shape,flush=True)
    except Exception as ex: print("margin FAIL",s,str(ex)[:60],flush=True)
    time.sleep(1)
if frames:
    m=pd.concat(frames).drop_duplicates(subset=0) if False else pd.concat(frames)
    # dedupe by date col
    datecol=m.columns[0]
    m=m.drop_duplicates(subset=[datecol]).sort_values(datecol)
    m.to_csv(out+"margin_sse_full.csv",index=False)
    print("margin full:",m.shape,str(m[datecol].min()),str(m[datecol].max()),flush=True)
    print("margin cols:",list(m.columns),flush=True)
# 2) month-end PCR from QVIX calendar
q=pd.read_csv("/tmp/r272_qvix50.csv"); q["d"]=pd.to_datetime(q["date"])
q["ym"]=q["d"].dt.to_period("M")
month_ends=q.groupby("ym").tail(1)["d"].dt.strftime("%Y%m%d").tolist()
print("month_ends:",len(month_ends),month_ends[0],month_ends[-1],flush=True)
rows=[]
for dt in month_ends:
    try:
        d=ak.option_daily_stats_sse(date=dt)
        d["ym"]=dt[:6]; rows.append(d)
        print("pcr",dt,"ok",len(d),flush=True)
    except Exception as ex:
        print("pcr",dt,"FAIL",str(ex)[:60],flush=True)
    time.sleep(0.25)
if rows:
    p=pd.concat(rows); p.to_csv(out+"pcr_monthend.csv",index=False)
    print("pcr saved:",p.shape,flush=True)
# 3) copy qvix
import shutil
shutil.copy("/tmp/r272_qvix50.csv",out+"qvix50.csv"); shutil.copy("/tmp/r272_qvix300.csv",out+"qvix300.csv")
print("ALL_DONE",flush=True)
