import requests, pandas as pd, json, time, hashlib, os
R="/root/.openclaw/workspace/shared/results/work/r341"
res={}
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def tx_fq(code,end="2026-08-28"):
    rows={}
    for it in range(25):
        u=f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,2013-01-01,{end},640,qfq"
        j=requests.get(u,timeout=15,headers=UA).json()["data"][code]
        k=j.get("qfqday") or j.get("day") or []
        if not k: break
        for d in k: rows[d[0]]=[d[0],float(d[1]),float(d[4]),float(d[5])]
        first=k[0][0]; nd=str(pd.Timestamp(first)-pd.Timedelta(days=1))[:10]
        if nd==end or len(k)<600: break
        end=nd; time.sleep(0.5)
    return pd.DataFrame([rows[k] for k in sorted(rows)],columns=["date","open","close","vol"])

# 1) 腾讯 qfq 全史重抓（R-340 步骤1：唯一正式口径）
for code in ["sh513100","sh513500"]:
    try:
        df=tx_fq(code); df.to_csv(f"{R}/raw/{code}_tx_qfq.csv",index=False)
        res[code+"_qfq"]=f"rows={len(df)} {df['date'].min()}..{df['date'].max()}"
    except Exception as e: res[code+"_qfq"]=f"FAIL {str(e)[:80]}"
    time.sleep(0.6)

# 2) sina 未复权日线（仅用于 F2 溢价比对，禁止进任何收益统计）
import akshare as ak
for code in ["sh513100","sh513500"]:
    try:
        df=ak.fund_etf_hist_sina(symbol=code)
        df.to_csv(f"{R}/raw/{code}_sina_raw.csv",index=False)
        res[code+"_sina"]=f"rows={len(df)} {df['date'].min()}..{df['date'].max()}"
    except Exception as e: res[code+"_sina"]=f"FAIL {str(e)[:80]}"
    time.sleep(0.5)

# 3) 现金腿 000198（在役管线同源：akshare fund_money_fund_info_em）
try:
    df=ak.fund_money_fund_info_em(fund="000198")
    df.to_csv(f"{R}/raw/mmf_000198.csv",index=False)
    res["mmf_000198"]=f"rows={len(df)} {df.iloc[0,0]}..{df.iloc[-1,0]}"
except Exception as e: res["mmf_000198"]=f"FAIL {str(e)[:80]}"

# 4) 官方单位净值（F2 溢价比对基准；pingzhongdata 全史日净值）
def nav_pingzhong(code):
    u=f"http://fund.eastmoney.com/pingzhongdata/{code}.js"
    t=requests.get(u,timeout=20,headers=UA).text
    i=t.find("Data_netWorthTrend ="); j=t.find("];",i)
    seg=t[i:j+1]; seg=seg[seg.find("["):]
    arr=json.loads(seg)
    df=pd.DataFrame([(pd.Timestamp(x["x"],unit="ms").normalize(),x["y"]) for x in arr],columns=["date","nav"])
    return df
for code in ["513100","513500"]:
    try:
        df=nav_pingzhong(code); df.to_csv(f"{R}/raw/{code}_official_nav.csv",index=False)
        res[code+"_nav"]=f"rows={len(df)} {df['date'].min()}..{df['date'].max()}"
    except Exception as e: res[code+"_nav"]=f"FAIL {str(e)[:80]}"
    time.sleep(1)

# 5) 跳零哨兵：qfq |日收益|>15% 计数（兼 F4 拆分哨兵）；sina 未复权对照
sent={}
for code in ["sh513100","sh513500"]:
    q=pd.read_csv(f"{R}/raw/{code}_tx_qfq.csv",parse_dates=["date"]).sort_values("date")
    r=q["close"].pct_change().abs()
    sent[code+"_qfq_gt15pct"]=int((r>0.15).sum()); sent[code+"_qfq_maxdaily"]=round(float(r.max()),4)
    s=pd.read_csv(f"{R}/raw/{code}_sina_raw.csv",parse_dates=["date"]).sort_values("date")
    rs=s["close"].pct_change().abs()
    sent[code+"_sina_gt15pct"]=int((rs>0.15).sum())  # 未复权应检出2022拆分
md5={f:hashlib.md5(open(f"{R}/raw/{f}",'rb').read()).hexdigest()[:12] for f in sorted(os.listdir(f"{R}/raw")) if f.endswith(".csv")}
json.dump(md5,open(f"{R}/raw/md5.txt","w"),indent=1)
json.dump({"fetch":res,"sentinel":sent},open(f"{R}/raw/fetch_summary.json","w"),ensure_ascii=False,indent=1)
print(json.dumps({"fetch":res,"sentinel":sent},ensure_ascii=False))
