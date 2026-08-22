#!/usr/bin/env python3
# r275_collect_one.py <table> — 单表采集（并行用）
import os, sys, time, json, traceback
import pandas as pd
import akshare as ak
import urllib3
urllib3.disable_warnings()

TNAME = sys.argv[1]
OUT = "/root/.openclaw/workspace/shared/results/work/r275/chunks"
os.makedirs(OUT, exist_ok=True)
LOG = open(f"/root/.openclaw/workspace/shared/results/work/r275/collect_{TNAME}.log", "a", buffering=1)

TABLES = {"yjbb": ak.stock_yjbb_em, "zcfz": ak.stock_zcfz_em, "xjll": ak.stock_xjll_em}
KEEP = {
    "yjbb": ["股票代码", "净利润-净利润", "净资产收益率", "销售毛利率", "营业总收入-同比增长", "净利润-同比增长", "最新公告日期"],
    "zcfz": ["股票代码", "资产-总资产", "公告日期"],
    "xjll": ["股票代码", "经营性现金流-现金流量净额", "公告日期"],
}
RENAME = {
    "股票代码": "code", "净利润-净利润": "net_profit", "净资产收益率": "roe",
    "销售毛利率": "gp_margin", "营业总收入-同比增长": "revenue_yoy", "净利润-同比增长": "net_profit_yoy",
    "最新公告日期": "pubDate", "资产-总资产": "total_asset",
    "经营性现金流-现金流量净额": "ocf", "公告日期": "pubDate",
}
PERIODS = [f"{y}{md}" for y in range(2005, 2027) for md in ("0331", "0630", "0930", "1231")]
PERIODS = [p for p in PERIODS if p <= "20260630"]

fn = TABLES[TNAME]
t0 = time.time()
for p in PERIODS:
    path = f"{OUT}/{TNAME}_{p}.parquet"
    if os.path.exists(path):
        continue
    ok = False
    for attempt in range(3):
        try:
            df = fn(date=p)
            if df is None or len(df) == 0:
                LOG.write(f"[{p}] EMPTY attempt{attempt}\n"); time.sleep(2); continue
            cols = [c for c in KEEP[TNAME] if c in df.columns]
            d = df[cols].rename(columns={k: v for k, v in RENAME.items() if k in cols}).copy()
            d["code"] = d["code"].astype(str).str.zfill(6)
            d.to_parquet(path, index=False)
            LOG.write(f"[{p}] rows={len(d)} t={time.time()-t0:.0f}s\n")
            ok = True; break
        except Exception as e:
            LOG.write(f"[{p}] ERR attempt{attempt}: {repr(e)[:120]}\n"); time.sleep(2 * (attempt + 1))
    if not ok:
        LOG.write(f"[{p}] FAIL-PERMANENT\n")
    time.sleep(1.2)
LOG.write(f"TABLE-{TNAME}-DONE t={time.time()-t0:.0f}s\n")
