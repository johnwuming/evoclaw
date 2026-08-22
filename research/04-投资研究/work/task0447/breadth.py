import pandas as pd
BASE = "/home/noname/quant-evolve"
A = ("00", "30", "60", "68")
def load(t):
    df = pd.read_parquet("%s/data/fin_deep/%s.parquet" % (BASE, t))
    df["code"] = df["code"].astype(str).str.zfill(6)
    df = df[df["code"].str[:2].isin(A)]
    df["statDate"] = pd.to_datetime(df["report_period"])
    return df.sort_values(["code","statDate"]).drop_duplicates(["code","statDate"], keep="last")
yj = load("yjbb"); zc = load("zcfz"); xj = load("xjll"); lr = load("lrb")
print("universe codes: yjbb=%d zcfz=%d xjll=%d lrb=%d" % (yj.code.nunique(), zc.code.nunique(), xj.code.nunique(), lr.code.nunique()))
m = yj[["code","statDate","net_profit"]].merge(xj[["code","statDate","ocf"]], on=["code","statDate"], how="left").merge(zc[["code","statDate","total_asset"]], on=["code","statDate"], how="left")
m["ok"] = m.net_profit.notna() & m.ocf.notna() & m.total_asset.notna()
m["year"] = m.statDate.dt.year
g = m.groupby("year")["ok"].agg(["mean","size"]).round(4)
print("three-element (NP&ocf&TA) per year: pct n")
for y, row in g.iterrows():
    print("  %d %.4f %d" % (y, row["mean"], row["size"]))
print("OVERALL all-history pooled = %.4f" % m.ok.mean())
for y0 in (2023, 2024):
    sub = m[m.year >= y0]
    print("recent ym>=%d pooled = %.4f (n=%d)" % (y0, sub.ok.mean(), len(sub)))
