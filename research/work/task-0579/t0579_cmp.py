import pandas as pd, numpy as np, sys
sys.path.insert(0,"/home/noname/quant-evolve/scripts")
R="/home/noname/quant-evolve/results"
nav=pd.read_csv(f"{R}/a13_rsraw_e1f10dz_full_nav.csv",parse_dates=["date"]).set_index("date")["nav"].astype(float)
cal=nav.index
st=pd.read_csv(f"{R}/p2gate_task0576_states.csv",parse_dates=["date"]).set_index("date")
print("states cols:",[c for c in st.columns][:8],"rows",len(st))
col=[c for c in st.columns if "MA20_c0_full" in c][0]
a=st[col]
zz=pd.read_parquet("/home/noname/quant-evolve/data/zz500_daily_20060101_20260808.parquet")
ccol=[c for c in zz.columns if "close" in str(c).lower()][0]
if not isinstance(zz.index,pd.DatetimeIndex):
    for c in zz.columns:
        if "date" in str(c).lower(): zz=zz.set_index(c);break
zz=zz[ccol].astype(float).reindex(cal).ffill()
ma20=zz.rolling(20).mean()
S=pd.Series(np.where(ma20.notna(),(zz>=ma20).astype(float),1.0),index=cal)
mine=S.shift(1).fillna(1.0)
b=a.reindex(cal)
d=(mine-b).abs()
dd=d[d>1e-9]
print("diff days:",len(dd))
if len(dd):
    first=dd.index[0]; i=cal.get_loc(first)
    print("first diff:",first.date(),"mine",mine.loc[first],"A",b.loc[first])
    print(zz.iloc[i-25:i+3].tail(28).to_string())
    print("ma20@first",ma20.loc[first],"zz@first",zz.loc[first])
