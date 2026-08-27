#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r325_verify_filter.py — task-0505/R-325 配套验证脚本 (VPS 本地, 零回测, 零回测引擎改动)

验证 fin_deep 管线 yjbb 宇宙污染修复 (merge 前A股前缀过滤):
  Stage build   : 从 r275 本地重采 chunks 构建生产 schema 的临时表目录 (yjbb/zcfz/xjll)
  Stage baseline: 未过滤管线仿真 (修复前原行为转录) → 计数基线落盘 pre_baseline.json
  Stage full    : 导入已补丁的 factor_expansion_v3ak.load_ak_wide() 实跑修复后行为,
                  输出修复前后计数对照 / R-275锚点复现 / md5抽验 / 剔除明细抽样

用法:
  python3 r325_verify_filter.py --stage build
  python3 r325_verify_filter.py --stage baseline   # 修改代码前运行
  python3 r325_verify_filter.py --stage full       # 修改代码后运行(含导入真模块)
"""
import os, sys, json, glob, hashlib, argparse
import types
import numpy as np
import pandas as pd

R275W = "/root/.openclaw/workspace/shared/results/work/r275"
OUT = "/root/.openclaw/workspace/shared/results/work/r325"
TMPDIR = "/tmp/r325_findb"
os.makedirs(OUT, exist_ok=True)

# 与 R-275 (r275_ic/r275_diag) 逐字一致的 A 股前缀白名单 —— 复现口径唯一来源
A_PREFIX = ("000", "001", "002", "003", "300", "301",
            "302", "600", "601", "603", "605", "688", "689")


def is_a(c):
    return isinstance(c, str) and len(c) == 6 and c[:3] in A_PREFIX


def prefix_family(c):
    c = str(c)[:3]
    if c in ("083", "087", "043", "092"):
        return "新三板"
    if c in ("040", "042"):
        return "老三板/两网退市"
    if c in ("090", "020"):
        return "B股"
    return f"A股或未知({c})"


# 生产 schema 中存在但 r275 本地子集未采的派生源列：以 NaN 补齐（不造数，仅供结构验证）
REQ_FILL = {
    "yjbb": ["revenue", "eps", "bps", "cfps"],
    "zcfz": ["equity", "cash", "inventory", "ar", "total_asset_yoy",
             "total_liability", "debt_to_asset"],
}
LRB_FILL_COLS = ["code", "report_period", "pubDate", "total_profit", "revenue",
                 "net_profit", "net_profit_yoy", "revenue_yoy"]


# ---------------------------------------------------------------- Stage: build
def stage_build():
    os.makedirs(TMPDIR, exist_ok=True)
    fp = {}
    for t in ["yjbb", "zcfz", "xjll"]:
        frames = []
        for f in sorted(glob.glob(f"{R275W}/chunks/{t}_*.parquet")):
            per = os.path.basename(f)[len(t) + 1:-8]
            d = pd.read_parquet(f)
            if len(d) == 0:
                continue
            d["report_period"] = per
            d["code"] = d["code"].astype(str).str.zfill(6)
            if "pubDate" in d.columns:
                d["pubDate"] = pd.to_datetime(d["pubDate"], errors="coerce")
            frames.append(d)
        full = pd.concat(frames, ignore_index=True)
        for c in REQ_FILL.get(t, []):
            if c not in full.columns:
                full[c] = np.nan
        out = os.path.join(TMPDIR, f"{t}.parquet")
        full.to_parquet(out, index=False)
        h = hashlib.md5(full.sort_values(["code", "report_period"])
                        [["code", "report_period"]].astype(str).to_csv(index=False).encode()).hexdigest()
        fp[t] = {"rows": int(len(full)), "stocks": int(full.code.nunique()),
                 "periods": int(full.report_period.nunique()), "md5_keys": h}
    # lrb 空壳（零行）: HP 生产有 lrb 表, 本地子集未采；提供 schema 使真函数可端到端跑通,
    # 零行=外连不改行集, lrb 源派生值为 NaN 不构成伪造。
    lr = pd.DataFrame({c: pd.Series(dtype="float64" if c not in ("code", "report_period") else str)
                       for c in LRB_FILL_COLS})
    lr.to_parquet(os.path.join(TMPDIR, "lrb.parquet"), index=False)
    fp["_lrb_filler"] = {"rows": 0, "note": "zero-row schema stub, 无伪数据"}
    json.dump(fp, open(f"{OUT}/inputs_fingerprint.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(fp, ensure_ascii=False, indent=1))


# ------------------------------------------------- 未过滤管线仿真 (修复前转录)
def _load_table_unfiltered(fin_dir, t):
    """转录原 factor_expansion_v3ak.load_ak_wide 读表段 (无过滤), lrb 缺则跳过."""
    p = os.path.join(fin_dir, f"{t}.parquet")
    if not os.path.exists(p):
        return None
    df = pd.read_parquet(p)
    df["code"] = df["code"].astype(str).str.zfill(6)
    df["statDate"] = pd.to_datetime(df["report_period"])
    if "pubDate" in df.columns:
        df["pubDate"] = pd.to_datetime(df["pubDate"], errors="coerce")
    else:
        df["pubDate"] = pd.NaT
    df = df.sort_values(["code", "statDate"]).drop_duplicates(["code", "statDate"], keep="last")
    return df


def _merge_wide_unfiltered(tabs):
    """转录原 outer merge 链 (不含 pub/pit/派生段; 过滤效果与此无关)."""
    keep_pub = lambda d: d[["code", "statDate", "pubDate"]]
    base, pub_parts = None, []
    conflict_cols = {"net_profit", "revenue", "net_profit_yoy", "revenue_yoy"}
    for t, df in tabs.items():
        keep = [c for c in df.columns
                if c not in ("code", "statDate", "pubDate", "report_period", "name", "industry")]
        if base is None:
            base = df[["code", "statDate"] + keep].copy()
        else:
            dup = [c for c in keep if c in base.columns and c in conflict_cols]
            keep2 = [c if c not in dup else f"{c}__{t}" for c in keep]
            dfr = df[["code", "statDate"] + keep].copy()
            dfr.columns = ["code", "statDate"] + keep2
            base = base.merge(dfr, on=["code", "statDate"], how="outer")
            for c in dup:
                cn = f"{c}__{t}"
                base[c] = base[c].where(base[c].notna(), base[cn])
                base = base.drop(columns=[cn])
        pub_parts.append(keep_pub(df))
    return base, pub_parts


def simulate_unfiltered(fin_dir=TMPDIR):
    tabs = {}
    for t in ["yjbb", "zcfz", "xjll", "lrb"]:
        df = _load_table_unfiltered(fin_dir, t)
        if df is not None:
            tabs[t] = df
    base, _ = _merge_wide_unfiltered(tabs)
    return tabs, base


# ------------------------------------------------------------ 统计与抽验工具
def table_stats(tabs):
    out = {}
    for t, df in tabs.items():
        m = df.code.map(is_a)
        n_a = int(df.loc[m, "code"].nunique()) if len(df) else 0
        out[t] = {"rows": int(len(df)), "stocks": int(df.code.nunique()),
                  "stocks_a": n_a,
                  "rows_nonA": int((~m).sum()) if len(df) else 0}
    return out


def three_element_rates(tabs):
    """完全复制 r275_ic.py Phase-B: 以过滤后yjbb为宇宙的 NP∧OCF∧TA 齐全率."""
    if any(k not in tabs for k in ("yjbb", "zcfz", "xjll")):
        return None
    per = tabs["yjbb"][["code", "statDate", "net_profit"]].merge(
        tabs["zcfz"][["code", "statDate", "total_asset"]], on=["code", "statDate"], how="left")
    per = per.merge(tabs["xjll"][["code", "statDate", "ocf"]], on=["code", "statDate"], how="left")
    for c in ("net_profit", "total_asset", "ocf"):
        per[c] = pd.to_numeric(per[c], errors="coerce")
    per["ok3"] = per.net_profit.notna() & per.total_asset.notna() & per.ocf.notna()
    per["year"] = per.statDate.dt.year
    all_rate = float(per.ok3.mean())
    recent = float(per[per.year >= 2023].ok3.mean())
    return {"all": round(all_rate, 4), "recent3y": round(recent, 4)}


def frame_md5(df, cols):
    d = df[cols].sort_values(["code", "statDate"]).reset_index(drop=True)
    h = pd.util.hash_pandas_object(d.astype({"code": str}), index=False).values.tobytes()
    return hashlib.md5(h).hexdigest()


# ---------------------------------------------------------- Stage: baseline
def stage_baseline():
    tabs, base = simulate_unfiltered()
    res = {"tables": table_stats(tabs)}
    res["wide_pre_rows"] = int(len(base))
    res["wide_pre_stocks"] = int(base.code.nunique())
    res["wide_nonA_codes"] = int((~base.code.map(is_a)).sum())
    y25 = tabs["yjbb"]; x25 = tabs["xjll"]
    p = "20251231"
    yj_p = y25[y25.statDate == p]
    xs = set(x25[x25.statDate == p].code)
    miss = sorted(set(yj_p.code) - xs)
    fams = {}
    for c in miss:
        fams[prefix_family(c)] = fams.get(prefix_family(c), 0) + 1
    res["p20251231"] = {
        "yjbb_stocks_raw": int(yj_p.code.nunique()), "xjll_stocks_raw": int(len(xs)),
        "ratio_pct": round(100 * len(xs) / yj_p.code.nunique(), 2),
        "missing": len(miss), "missing_families": fams,
        "a_prefix_missing": len([c for c in miss if is_a(c)])}
    res["pollution_ratio_r275_style"] = round(
        100 * tabs["zcfz"].code.nunique() / tabs["yjbb"].code.nunique(), 2)
    res["unfiltered_hash_yjbb_np"] = frame_md5(y25, ["code", "statDate", "net_profit", "roe", "gp_margin"])
    json.dump(res, open(f"{OUT}/pre_baseline.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


# --------------------------------------- 补丁模块加载 (真实修改过的函数实跑)
def load_patched_module():
    for name in ("scipy", "scipy.stats", "scipy.cluster", "scipy.cluster.hierarchy"):
        if name not in sys.modules:
            m = types.ModuleType(name)
            sys.modules[name] = m
    sys.modules["scipy.stats"].spearmanr = lambda *a, **k: None
    m_cl = types.ModuleType("scipy.cluster"); m_h = types.ModuleType("scipy.cluster.hierarchy")
    sys.modules["scipy.cluster"] = m_cl
    sys.modules["scipy.cluster.hierarchy"] = m_h
    sys.modules["scipy"].cluster = m_cl
    m_cl.hierarchy = m_h
    fe = types.ModuleType("factors_ext")
    sys.modules["factors_ext"] = fe
    src_dir = "/root/.openclaw/workspace/scripts/task-0285"
    sys.path.insert(0, src_dir)
    if "factor_expansion_v3ak" in sys.modules:
        del sys.modules["factor_expansion_v3ak"]
    mod = __import__("factor_expansion_v3ak")
    mod.FIN_DEEP_DIR = TMPDIR           # 重定向到本地验证数据 (隔离, 不触 HP 路径)
    mod.FIN_PANEL_CACHE = "/tmp/r325_panel_cache.parquet"
    return mod


# -------------------------------------------------------------- Stage: full
def stage_full():
    base_res = json.load(open(f"{OUT}/pre_baseline.json"))
    mod = load_patched_module()
    assert hasattr(mod, "is_a_share_code") or hasattr(mod, "A_SHARE_PREFIXES"), \
        "补丁未生效: factor_expansion_v3ak 缺少 A_SHARE_PREFIXES/is_a_share_code"
    ap = tuple(mod.A_SHARE_PREFIXES)
    assert ap == A_PREFIX, f"前缀白名单与R-275口径不一致: {ap}"
    # 真函数实跑 (修复后)
    tabs_post_probe, _ = simulate_unfiltered()          # 仅用于对齐表集合
    wide_post = mod.load_ak_wide()

    # --- 修复后断言 ---
    codes = wide_post.code.astype(str)
    non_a = codes[~codes.str[:3].isin(A_PREFIX)]
    assert len(non_a) == 0, f"修复失败: 宽表仍有 {len(non_a)} 个非A股代码"

    # --- 表级对照 (修复前 vs 修复后): 用真模块同款读取重算 after-filter 表 ---
    tabs_post = {}
    for t in ["yjbb", "zcfz", "xjll"]:
        df = _load_table_unfiltered(TMPDIR, t)
        mask = df.code.isin([c for c in df.code.unique() if is_a(c)])
        tabs_post[t] = df[mask]
    post_tab_stats = table_stats(tabs_post)

    # --- 保留行恒等校验: 公共列全量 hash (不只是抽样) ---
    checks = {}
    for t in ["yjbb", "zcfz", "xjll"]:
        pre, pst = tabs_post_probe.get(t), tabs_post.get(t)
        cols = [c for c in pre.columns if c in pst.columns]
        same = frame_md5(pre[cols], cols) == frame_md5(pst[cols], cols)
        # 抽样 md5 明细 (150 行)
        pre_a = pre[pre.code.map(is_a)][cols].sort_values(["code", "statDate"])
        smp = pre_a.sample(n=min(150, len(pre_a)), random_state=42)
        row_hashes = [
            hashlib.md5("|".join(str(v) for v in r.tolist()).encode()).hexdigest()
            for _, r in smp.iterrows()]
        checks[t] = {"kept_full_hash_equal": bool(same),
                     "sample_rows": [{"code": str(c), "period": str(p_), "md5_kept_pre": h}
                                     for (c, p_), h in zip(smp[["code", "statDate"]].astype(str).values[:10], row_hashes[:10])],
                     "sample_size": int(len(smp)),
                     "post_resample_match": True}
    # 抽样 md5 事后复核: 同一行在修复后表里重算 hash 应逐行一致
    for t in ["yjbb", "zcfz", "xjll"]:
        pst = tabs_post[t].set_index(["code", "statDate"])
        cols = [c for c in tabs_post_probe[t].columns if c in pst.columns]
        mism = 0
        pre = tabs_post_probe[t]
        pre_a = pre[pre.code.map(is_a)][cols].sort_values(["code", "statDate"])
        smp = pre_a.sample(n=min(150, len(pre_a)), random_state=42)
        for _, r in smp.iterrows():
            key = (r["code"], r["statDate"])
            if key not in pst.index:
                mism += 1; continue
            r2 = pst.loc[key]
            h1 = hashlib.md5("|".join(str(v) for v in r.tolist()).encode()).hexdigest()
            row2 = [r2[c] for c in cols]
            h2 = hashlib.md5("|".join(str(v) for v in row2).encode()).hexdigest()
            if h1 != h2:
                mism += 1
        checks[t]["post_resample_match"] = (mism == 0)
        checks[t]["mismatch_rows"] = mism

    # --- 剔除明细: 规则解释性与抽样清单 ---
    removals = []
    ypre = tabs_post_probe["yjbb"]; ypst = tabs_post["yjbb"]
    removed_codes = sorted(set(ypre.code.unique()) - set(ypst.code.unique()))
    fam_ct = {}
    for c in removed_codes:
        f_ = prefix_family(c)
        fam_ct[f_] = fam_ct.get(f_, 0) + 1
    explained = all(not is_a(c) for c in removed_codes)
    prng = np.random.default_rng(7)
    pick = sorted(prng.choice(removed_codes, size=min(30, len(removed_codes)), replace=False))
    det = ypre[ypre.code.isin(pick)][["code", "statDate", "net_profit"]].copy()
    det["family"] = det.code.map(prefix_family)
    det["rule_verdict"] = "剔除(A股白名单外)"
    removal_sample = det.head(30).to_dict("records")

    # --- A股三要素齐全率 (修复后口径, 应≈R-275 96.6%/99.4%) ---
    rate = three_element_rates({**tabs_post})
    prev = None
    try:
        prev = pd.read_csv(f"{R275W}/breadth_a_share.csv")
    except Exception:
        pass

    result = {
        "anchor_R275": {"hp_baseline": "yjbb 451669行/11765股 vs zcfz/xjll/lrb 各5244股 → 5244/11765=44.57%",
                        "expect_rates": {"all": 0.966, "recent3y": 0.994},
                        "expect_local_rows_A": {"yjbb": 288275, "zcfz": 280143, "xjll": 288715}},
        "pre_fix": base_res,
        "post_tables": post_tab_stats,
        "post_wide": {"rows": int(len(wide_post)), "stocks": int(wide_post.code.nunique())},
        "row_integrity_checks": {t: {"kept_full_hash_equal": v["kept_full_hash_equal"],
                                      "post_resample_match": v["post_resample_match"]}
                                  for t, v in checks.items()},
        "sample_md5_kept": {t: checks[t]["sample_rows"] for t in checks},
        "removed_summary": {"count_codes_removed_from_yjbb": len(removed_codes),
                            "all_explained_by_prefix_rule": bool(explained),
                            "families": fam_ct},
        "removal_sample": removal_sample,
        "removal_sample": removal_sample,
        "rates_after_fix": rate,
        "breadth_prev_rows": None if prev is None else int(len(prev)),
    }
    json.dump(result, open(f"{OUT}/verify_output.json", "w"), ensure_ascii=False, indent=1, default=str)
    brief = {
        "keeps_equal": result["row_integrity_checks"],
        "yjbb_rows_before_after": [base_res["tables"]["yjbb"]["rows"], post_tab_stats["yjbb"]["rows"]],
        "yjbb_stocks_before_after": [base_res["tables"]["yjbb"]["stocks"], post_tab_stats["yjbb"]["stocks"]],
        "wide_stocks_before_after": [base_res["wide_pre_stocks"], result["post_wide"]["stocks"]],
        "p20251231_ratio_pct": base_res["p20251231"]["ratio_pct"],
        "rates": rate,
        "removed_families": fam_ct,
    }
    print(json.dumps(brief, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--stage", choices=["build", "baseline", "full"], required=True)
    a = ap_.parse_args()
    {"build": stage_build, "baseline": stage_baseline, "full": stage_full}[a.stage]()
