import akshare as ak, pandas as pd, time, hashlib, os, sys
out = "/home/noname/quant-evolve/results/work/r0415/sw_industry_monthly.csv"
info = ak.sw_index_first_info()
codes = list(zip(info["行业代码"], info["行业名称"]))
print("n_industries:", len(codes), flush=True)
frames = []
fails = []
for i,(code,name) in enumerate(codes):
    sym = code.split(".")[0]
    try:
        df = ak.index_hist_sw(symbol=sym, period="month")[["日期","收盘"]].copy()
        df.columns = ["date", name]
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        frames.append(df.set_index("date"))
        print(f"[{i+1}/{len(codes)}] {name} rows={len(df)} first={df[date].iloc[0]} last={df[date].iloc[-1]}", flush=True)
    except Exception as e:
        fails.append((name,str(e)[:80])); print("FAIL", name, str(e)[:80], flush=True)
    time.sleep(0.4)
wide = frames[0]
for f in frames[1:]:
    wide = wide.join(f, how="outer")
wide = wide.sort_index()
wide.index.name = "date"
wide.to_csv(out)
h = hashlib.md5(open(out,"rb").read()).hexdigest()
print("SAVED", out, "shape", wide.shape, "md5", h, flush=True)
print("FAILS", fails, flush=True)
