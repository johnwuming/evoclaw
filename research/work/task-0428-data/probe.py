import akshare as ak, pandas as pd, traceback, os
os.makedirs('/tmp/r268', exist_ok=True)

def probe(name, fn, path):
    try:
        df = fn()
        df.to_csv(path, index=False)
        print(f"[OK] {name}: shape={df.shape}, cols={list(df.columns)[:8]}")
        print(f"     first={df.iloc[0].to_dict()}")
        print(f"     last={df.iloc[-1].to_dict()}")
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e)[:150]}")

# 1) legulegu PE
for sym in ["中证1000", "中证2000", "沪深300", "中证红利"]:
    probe(f"pe_lg_{sym}", lambda s=sym: ak.stock_index_pe_lg(symbol=s), f"/tmp/r268/pe_lg_{sym}.csv")

# 2) fxdb PE (中证2000)
def f932():
    return ak.index_value_hist_fxdb(symbol="932000.CSI", indicator="市盈率PE1")
probe("fxdb_pe_932000", f932, "/tmp/r268/fxdb_pe_932000.csv")

# 3) price history
for code in ["932000", "000852", "000300", "000922", "H00922"]:
    def g(c=code):
        return ak.index_zh_a_hist(symbol=c, period="daily", start_date="20140101", end_date="20260821")
    probe(f"px_{code}", g, f"/tmp/r268/px_{code}.csv")
