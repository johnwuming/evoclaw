#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_0537.py — task-0537 Phase A 回测正确性六项审计（只读审计，产物只写新目录）
输出: ~/quant-evolve/results/phase_a_audit_0537/audit_findings.json + audit_log.txt
禁止修改任何既有文件。
"""
import os, sys, json, traceback, glob
import pandas as pd, numpy as np

os.chdir(os.path.expanduser("~/quant-evolve"))
OUT = os.path.expanduser("~/quant-evolve/results/phase_a_audit_0537")
os.makedirs(OUT, exist_ok=True)
F = {"findings": {}}

def sec(name):
    print("\n" + "=" * 20, name, "=" * 20, flush=True)

def put(key, val):
    F["findings"][key] = val
    print(key, "=>", json.dumps(val, ensure_ascii=False, default=str)[:400], flush=True)

# ---------- A1: PIT ----------
sec("A1-PIT")
try:
    ths = pd.read_parquet("data/derived/ths_ttm_panel.parquet")
    ths["avail_date"] = pd.to_datetime(ths["avail_date"])
    ths["rp"] = pd.to_datetime(ths["report_date"].astype(str))
    lag = (ths["avail_date"] - ths["rp"]).dt.days
    put("A1_ths_panel", {"rows": int(len(ths)), "lag_median": int(lag.median()),
                         "lag_min": int(lag.min()), "neg_count": int((lag < 0).sum())})
except Exception as e:
    put("A1_ths_panel", {"error": str(e)})

# load_fullpool_market 基本面 join 源码
try:
    sys.path.insert(0, "scripts")
    import a9_common
    src_engine_loader = inspect_src = None
    import inspect
    src = inspect.getsource(a9_common.load_engine)
    put("A1_load_engine_head", src[:800])
except Exception as e:
    put("A1_load_engine_head", {"error": str(e)})

# 择时 shift(1) 证据
try:
    for f, pats in [("scripts/timing_layer_prod.py", ["shift(1)", "上一个月末"]),
                    ("scripts/paper_engine_gold.py", ["prev_me", "PIT"]),
                    ("scripts/paper_engine.py", ["prev_me", "signal_date", "prev_month"])]:
        hits = {}
        txt = open(f, encoding="utf-8", errors="ignore").read()
        for p in pats:
            hits[p] = txt.count(p)
        put("A1_shift_" + os.path.basename(f), hits)
except Exception as e:
    put("A1_shift", {"error": str(e)})

# ---------- A2: 复权 ----------
sec("A2-QFQ")
try:
    # 513100 拆分反例：qfq 后不应有 <-30% 单日
    cands = glob.glob("data/all_stocks_qfq/513100*.parquet")
    put("A2_513100_files", [os.path.basename(c) for c in cands])
    for c in cands:
        d = pd.read_parquet(c)
        dc = [x for x in d.columns if x.lower() in ("close", "closeqfq", "adj_close", "close_qfq")]
        if not dc:
            put("A2_513100_cols", list(d.columns)[:12]); continue
        s = pd.to_numeric(d[dc[0]], errors="coerce").dropna()
        r = s.pct_change().dropna()
        put("A2_513100_" + os.path.basename(c), {"min_daily_ret": float(r.min()),
            "max_daily_ret": float(r.max()), "n": int(len(r)),
            "date_min": str(d["date"].min())[:10], "date_max": str(d["date"].max())[:10]})
except Exception as e:
    put("A2_513100", {"error": str(e)})

# qfq vs raw 抽样：除息日外收益应一致
try:
    raw_dir, qfq_dir = "data/all_stocks_merged.parquet", "data/all_stocks_qfq"
    raw = pd.read_parquet(raw_dir, columns=None) if os.path.isdir(raw_dir) is False and os.path.exists(raw_dir) else None
    if raw is not None:
        raw["date"] = pd.to_datetime(raw["date"])
        diffs, exdays = [], 0
        for code in ["000001", "600519", "000858", "601318"]:
            k = raw[raw["code"] == code].sort_values("date").set_index("date")["close"]
            qf = pd.read_parquet(f"{qfq_dir}/{code}.parquet")
            qf["date"] = pd.to_datetime(qf["date"])
            q = qf.sort_values("date").set_index("date")["close"]
            idx = k.index.intersection(q.index)
            rr, qr = k.loc[idx].pct_change(), q.loc[idx].pct_change()
            d = (rr - qr).abs().dropna()
            diffs.append({"code": code, "max_diff": float(d.max()), "n_gt_1pct": int((d > 0.01).sum())})
        put("A2_qfq_vs_raw", diffs)
    else:
        put("A2_qfq_vs_raw", "merged parquet not file — skip")
except Exception as e:
    put("A2_qfq_vs_raw", {"error": str(e)})

# ---------- A3: 退市 ----------
sec("A3-DELIST")
try:
    dp = pd.read_parquet("data/delisted_pool.parquet") if os.path.exists("data/delisted_pool.parquet") else pd.read_csv("data/delisted_pool.csv")
    codes = set(dp["code"].astype(str))
    put("A3_delisted_pool", {"n": len(codes), "cols": list(dp.columns)[:8]})
    qfq_codes = set(os.path.basename(p).split(".")[0] for p in glob.glob("data/all_stocks_qfq/*.parquet"))
    qfq_codes = set(c for c in qfq_codes if not c.endswith("_daily_qfq"))
    cov = codes & qfq_codes
    put("A3_coverage", {"delisted_in_qfq_dir": len(cov), "ratio": round(len(cov) / max(1, len(codes)), 3)})
except Exception as e:
    put("A3_delisted", {"error": str(e)})

# ---------- A4: 涨跌停 ----------
sec("A4-LIMIT")
try:
    tr = pd.read_csv("results/baseline-paper-trades.csv")
    tr.columns = [c.strip().lower() for c in tr.columns]
    put("A4_trades", {"rows": int(len(tr)), "cols": list(tr.columns)})
    buys = tr[tr["action"].astype(str).str.lower().str.contains("buy")]
    lim_hits = []
    for _, r in buys.iterrows():
        code, d = str(r["code"]), str(r["date"])[:10]
        kf = f"data/all_stocks_qfq/{code}.parquet"
        if not os.path.exists(kf): continue
        k = pd.read_parquet(kf); k["date"] = pd.to_datetime(k["date"])
        kd = k[k["date"] <= d].sort_values("date")
        if len(kd) < 2: continue
        pct = kd["close"].iloc[-1] / kd["close"].iloc[-2] - 1
        if pct >= 0.098 - 1e-4:
            lim_hits.append({"code": code, "date": d, "pct": float(pct)})
    put("A4_buy_on_limitup", {"n_buys": int(len(buys)), "violations": lim_hits[:5], "n_viol": len(lim_hits)})
except Exception as e:
    put("A4_paper_check", {"error": str(e)})

# backtest 层 limit_board 实现定位
try:
    hits = []
    for f in glob.glob("scripts/*.py"):
        t = open(f, encoding="utf-8", errors="ignore").read()
        if "limit_board" in t and "def " in t:
            hits.append(os.path.basename(f))
    put("A4_limit_board_impl_files", hits[:8])
except Exception as e:
    put("A4_limit_board", {"error": str(e)})

# ---------- A5: 成本 ----------
sec("A5-COST")
try:
    tr = pd.read_csv("results/baseline-paper-trades.csv")
    tr.columns = [c.strip().lower() for c in tr.columns]
    sells = tr[tr["action"].astype(str).str.lower().str.contains("sell")]
    put("A5_trades_fee", {"buy_rows": int(len(tr) - len(sells)), "sell_rows": int(len(sells)),
                          "cost_na": int(tr["cost"].isna().sum()) if "cost" in tr else "n/a"})
    # 抽 3 笔验证费用口径
    samp = tr.tail(3).to_dict("records")
    put("A5_fee_sample", [{k: str(v) for k, v in s.items()} for s in samp])
except Exception as e:
    put("A5_fee", {"error": str(e)})

# ---------- A6: 分红 ----------
sec("A6-DIV")
try:
    dv = pd.read_parquet("data/derived/dividend_events.parquet")
    put("A6_div_events", {"rows": int(len(dv)), "cols": list(dv.columns)[:10]})
    dcol = [c for c in dv.columns if "date" in c.lower()][0]
    dv[dcol] = pd.to_datetime(dv[dcol])
    recent = dv[dv[dcol] >= "2026-05-01"]
    put("A6_div_recent", {"n_since_202605": int(len(recent))})
    tr = pd.read_csv("results/baseline-paper-trades.csv")
    tr.columns = [c.strip().lower() for c in tr.columns]
    held = set(tr["code"].astype(str))
    hit = recent[recent[[c for c in dv.columns if "code" in c.lower()][0]].astype(str).isin(held)]
    put("A6_div_x_paper_holdings", {"n": int(len(hit)),
        "sample": hit.head(5).astype(str).to_dict("records")})
except Exception as e:
    put("A6_div", {"error": str(e)})

# paper NAV 复算（三个月锚点）——从 trades+qfq close 重算月末 NAV vs paper-nav.csv
sec("RECON-NAV")
try:
    st = json.load(open("results/paper-state.json"))
    cash = float(st.get("cash", 0))
    pos = st.get("positions", {})
    nav_now = cash + sum(float(p.get("shares", 0)) * float(p.get("price", p.get("cost", 0))) for p in pos.values())
    put("RECON_state", {"cash": cash, "n_pos": len(pos), "nav_from_state": round(nav_now, 2)})
    nav = pd.read_csv("results/paper-nav.csv")
    put("RECON_navfile", {"rows": int(len(nav)), "cols": list(nav.columns), "tail": nav.tail(2).astype(str).to_dict("records")})
except Exception as e:
    put("RECON", {"error": str(e)})

with open(os.path.join(OUT, "audit_findings.json"), "w") as f:
    json.dump(F, f, ensure_ascii=False, indent=1, default=str)
print("\nDONE ->", os.path.join(OUT, "audit_findings.json"), flush=True)
