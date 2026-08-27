import pandas as pd, numpy as np, json
R="/root/.openclaw/workspace/shared/results/work/r323"
mms=lambda d:(d.dt.year*100+d.dt.month)
def month_end_close(df):
    df=df.copy(); df["ym"]=mms(df["date"])
    me=df.groupby("ym").last().reset_index(); me["date"]=pd.to_datetime(me["date"])
    return me.set_index("date")
# --- MMF 日收益 -> 月收益 ---
mm=pd.read_csv(f"{R}/raw/mmf_000198.csv",parse_dates=["净值日期"]).rename(columns={"净值日期":"date","每万份收益":"inc"})
mm=mm.sort_values("date"); mm["ret"]=mm["inc"]/10000.0
mm["ym"]=mms(mm["date"]); mm["gr"]=(1+mm["ret"])
mmf_m=mm.groupby("ym")["gr"].prod()-1.0   # 月无风险(简单加总按日复利)
def mmf_for_month(ym):
    return float(mmf_m.get(ym-1 if ym%100>1 else ym-89, 0.002)) # t+1月的MMF需t月已实现? 用t月已知值保守: 取前一个月
# 注意: 现金增强用 t+1 月实现的 MMF 收益(实盘口径), 而非预测。此处理解为事后结算。
# --- 标的月末序列与信号 ---
signals={"sma200":None,"sma240":None,"ma50_200":None,"mom12_1":None,"voltgt10":None}
out={}
def build(code):
    d=pd.read_csv(f"{R}/raw/{code}_sina.csv",parse_dates=["date"])[["date","close","amount"]].sort_values("date")
    me=month_end_close(d[["date","close"]]); ret=me["close"].pct_change()
    c=d["close"].values; dt=d["date"].values
    res=[]
    for i,row in me.iterrows():
        idx=np.searchsorted(dt,np.datetime64(i))
        if idx<240: res.append(np.nan); continue
        seg=c[:idx+1]; px=seg[-1]
        s={"sma200":px>seg[-200:].mean(),"sma240":px>seg[-240:].mean(),
           "ma50_200":seg[-50:].mean()>seg[-200:].mean()}
        if len(me)>=14:
            m=me["close"]; j=(m.index.get_loc(i)); 
            s["mom12_1"]= j>=12 and m.iloc[j]/m.iloc[j-12]-1>0
        r=d["date"]<=i; recent=d[r].tail(60); vol=recent["close"].pct_change().std()*np.sqrt(244)
        s["voltgt10"]=float(min(max(0.10/vol,0),1.0))
        res.append(s)
    S=pd.DataFrame(res,index=me.index).astype(float) if False else pd.DataFrame([x if isinstance(x,dict) else {"sma200":np.nan} for x in res],index=me.index)
    T=pd.DataFrame(index=me.index); T["ret"]=ret; T["signal"]=S.shift(0)
    for k in ["sma200","sma240","ma50_200","mom12_1"]:
        T[k]=((S[k]>0)|(S[k]==1.0)).astype(float)
    for k in ["sma200","sma240","ma50_200","mom12_1"]:
        w=T[k].shift(1); T[f"g_{k}"]=w*T["ret"]
        T[f"c_{k}"]=w*T["ret"]+(1-w)*0.0  # cash 部分后面统一填
    return T,S
frames={}
for code in ["sh513100","sh513500"]:
    frames[code]=build(code)[0]
print(list(frames.keys()))
json.dump({"built":True},open(f"{R}/out/_probe.json","w"))
