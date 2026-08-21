import akshare as ak, os
def probe(name, fn, path):
    try:
        df = fn(); df.to_csv(path, index=False)
        print(f"[OK] {name}: shape={df.shape}, cols={list(df.columns)[:8]}")
        print(f"     first={df.iloc[0].to_dict()}"); print(f"     last={df.iloc[-1].to_dict()}")
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e)[:120]}")

print("has index_value_hist:", hasattr(ak, "index_value_hist"))
probe("fxdb_pe_932000", lambda: ak.index_value_hist(symbol="932000.CSI", indicator="市盈率PE1"), "/tmp/r268/fxdb_pe_932000.csv")
probe("fxdb_pe_000922", lambda: ak.index_value_hist(symbol="000922.CSI", indicator="市盈率PE1"), "/tmp/r268/fxdb_pe_000922.csv")
probe("sina_px_sh000922", lambda: ak.stock_zh_index_daily(symbol="sh000922"), "/tmp/r268/px_sh000922_sina.csv")
probe("em_px_932000_retry", lambda: ak.index_zh_a_hist(symbol="932000", period="daily", start_date="20140101", end_date="20260821"), "/tmp/r268/px_932000_em.csv")
