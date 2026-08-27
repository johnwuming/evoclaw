import akshare as ak, pandas as pd, hashlib, time, json, os
OUT="/root/.openclaw/workspace/shared/results/work/r323/raw"
res={}
def retry(fn,n=2,wait=0.5):
    for i in range(n+1):
        try: return fn()
        except Exception as e:
            if i==n: raise
            time.sleep(wait)
# 1) sina 全史日线
for code in ["sh513100","sh513500","sz159941","sh513300","sh000300"]:
    try:
        df=retry(lambda c=code: ak.fund_etf_hist_sina(symbol=c)); df.to_csv(f"{OUT}/{code}_sina.csv",index=False)
        res[code+"_sina"]=f"rows={len(df)} {df['date'].min()}..{df['date'].max()} cols={list(df.columns)}"
    except Exception as e: res[code+"_sina"]=f"FAIL {str(e)[:80]}"
    time.sleep(0.5)
# 2) 东财带成交额（容量）
for code in ["513100","513500"]:
    try:
        df=retry(lambda c=code: ak.fund_etf_hist_em(symbol=c,period="daily",adjust="")); df.to_csv(f"{OUT}/{code}_em.csv",index=False)
        res[code+"_em"]=f"rows={len(df)} {df.iloc[0,0]}..{df.iloc[-1,0]}"
    except Exception as e: res[code+"_em"]=f"FAIL {str(e)[:80]}"
    time.sleep(0.5)
# 3) 货币基金 000198
try:
    df=retry(lambda: ak.fund_money_fund_info_em(fund="000198")); df.to_csv(f"{OUT}/mmf_000198.csv",index=False)
    res["mmf_000198"]=f"rows={len(df)} {str(df.iloc[0,0])}..{str(df.iloc[-1,0])}"
except Exception as e: res["mmf_000198"]=f"FAIL {str(e)[:80]}"
md5={f:hashlib.md5(open(f"{OUT}/{f}",'rb').read()).hexdigest()[:12] for f in sorted(os.listdir(OUT)) if f.endswith('.csv')}
json.dump(md5,open(f"{OUT}/md5.txt","w"),indent=1)
json.dump(res,open(f"{OUT}/fetch_summary.json","w"),ensure_ascii=False,indent=1)
for k,v in res.items(): print(k,"=>",v)
