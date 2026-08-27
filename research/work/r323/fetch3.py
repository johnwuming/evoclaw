import requests, pandas as pd, json, time
R="/root/.openclaw/workspace/shared/results/work/r323"
def tx_fq(code):
    rows={}; end="2026-08-27"
    for it in range(25):
        u=f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,2013-01-01,{end},640,qfq"
        j=requests.get(u,timeout=15).json()["data"][code]
        k=j.get("qfqday") or j.get("day") or []
        if not k: break
        for d in k: rows[d[0]]=[d[0],float(d[1]),float(d[4]),float(d[5])]
        first=k[0][0]; nd=str(pd.Timestamp(first)-pd.Timedelta(days=1))[:10]
        if nd==end or len(k)<600: break
        end=nd; time.sleep(0.5)
    df=pd.DataFrame([rows[k] for k in sorted(rows)],columns=["date","open","close","vol"])
    return df
res={}
for code in ["sh513100","sh513500"]:
    try:
        df=tx_fq(code); df.to_csv(f"{R}/raw/{code}_tx_qfq.csv",index=False)
        res[code]=f"rows={len(df)} {df['date'].min()}..{df['date'].max()}"
    except Exception as e: res[code]=f"FAIL {str(e)[:80]}"
    time.sleep(0.6)
print(json.dumps(res))
