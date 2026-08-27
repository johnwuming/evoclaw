import akshare as ak, pandas as pd, hashlib, time, json, os
OUT="/root/.openclaw/workspace/shared/results/work/r323/raw"
res={}
def retry(fn,n=2,wait=1.5):
    for i in range(n+1):
        try: return fn()
        except Exception as e:
            if i==n: raise
            time.sleep(wait)
try:
    df=retry(lambda: ak.fund_money_fund_info_em(symbol="000198")); df.to_csv(f"{OUT}/mmf_000198.csv",index=False)
    res["mmf_000198"]=f"rows={len(df)} {str(df.iloc[0,0])}..{str(df.iloc[-1,0])} cols={list(df.columns)}"
except Exception as e: res["mmf_000198"]=f"FAIL {str(e)[:100]}"
time.sleep(1)
md5={f:hashlib.md5(open(f"{OUT}/{f}",'rb').read()).hexdigest()[:12] for f in sorted(os.listdir(OUT)) if f.endswith('.csv')}
json.dump(md5,open(f"{OUT}/md5.txt","w"),indent=1)
json.dump(res,open(f"{OUT}/fetch2_summary.json","w"),ensure_ascii=False)
print(json.dumps(res,ensure_ascii=False))
