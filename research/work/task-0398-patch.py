#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0398: g3 corr 口径修正补丁（D-20260819-G3CORR）
三处修改 evolution_pipeline.py：
  P1 GATE_CONFIG 后新增 GUARD_CORR_CONFIG
  P2 load_ic_monthly 左连接并入补充月度IC列
  P3 gate_max_corr 护栏替身豁免 + 月度IC Pearson 兜底
锚点均为唯一字符串，替换前校验存在且唯一；改完 py_compile。
"""
import py_compile

P = "/home/noname/quant-evolve/scripts/evolution_pipeline.py"
src = open(P, encoding="utf-8").read()

def rep(old, new, tag):
    global src
    n = src.count(old)
    assert n == 1, f"[{tag}] anchor count={n} (expect 1)"
    src = src.replace(old, new)
    print(f"Patched: {tag} (+{len(new)-len(old)} bytes)")

# ---------------- P1: GUARD_CORR_CONFIG ----------------
anchor1 = '''    "g6_enabled": False,         # D-20260819-G6DEL（task-0391 用户拍板）：门禁6硬判定禁用；mdd 数值保留入评分 dd 项
}
'''
insert1 = '''    "g6_enabled": False,         # D-20260819-G6DEL（task-0391 用户拍板）：门禁6硬判定禁用；mdd 数值保留入评分 dd 项
}

# D-20260819-G3CORR（task-0398，用户 2026-08-19 15:04 批准 A 方案）：g3 corr 口径——在役因子集
# 区分「排序因子」与「护栏登记项」。依据 R-242（task-0395）双重计价复核：在役 E1 硬护栏列
# （ret120<-30% 硬排除）登记在 selection.factors 但不参与排序打分；护栏对组合行为的影响已完整
# 进入在役 locked 指标并由 oos/dd 分量计价一次。g3 再把护栏信号当「在役排序因子」与候选的
# 「因子化替身」（mom_pen / mom_pen_dz = λ·|clip(ret120,-1,0)|[死区变体]）比 IC 相关（实测 0.7555，
# 而与在役真排序因子最高仅 0.2066）属双重计价。
# 口径：在役 params.e1_guard 为真、且护栏列不在排序 specs（ext_specs/ext_factor/sort/ext_weights）
# 中时，该护栏列对其因子化替身豁免 g3 比较；oos/dd 分量不豁免（行为差异照常计价）。
# 向后兼容：在役无 e1_guard、护栏列参与排序、或候选无替身因子时，比较集与旧版完全一致
# （老版本评分不漂移）。替身名单显式登记在 guard_avatars，防止豁免范围无界扩大。
GUARD_CORR_CONFIG = {
    "enabled": True,
    "guard_col_default": ["ret120"],            # e1_guard 未显式给 mom_cols 时的护栏列
    "guard_avatars": {"ret120": ["mom_pen", "mom_pen_dz"]},   # 护栏列 → 其因子化替身因子名
    "supp_ic_files": ["a13_supp_ic_monthly.csv"],  # 补充月度IC列（左连接并入 base，供 g1/g2/g3）
}
'''
rep(anchor1, insert1, "P1 GUARD_CORR_CONFIG")

# ---------------- P2: load_ic_monthly ----------------
old2 = '''def load_ic_monthly():
    import pandas as pd
    p = os.path.join(RESULTS, "factor_ic_monthly.csv")
    if not os.path.exists(p):
        return None
    return pd.read_csv(p, dtype={"ym": str})
'''
new2 = '''def load_ic_monthly():
    import pandas as pd
    p = os.path.join(RESULTS, "factor_ic_monthly.csv")
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p, dtype={"ym": str})
    # D-20260819-G3CORR（task-0398）：左连接并入补充月度IC列（base 为主表，仅新增因子列，
    # 不覆盖 base 既有列 → 老版本复合 IC/g3 相关逐位不变）。n_* 辅助列（如 n_pb_inv）跳过。
    for supp in GUARD_CORR_CONFIG.get("supp_ic_files", []):
        sp = os.path.join(RESULTS, supp)
        if not os.path.exists(sp):
            continue
        try:
            s = pd.read_csv(sp, dtype={"ym": str})
        except Exception:
            continue
        new_cols = [c for c in s.columns
                    if c != "ym" and not c.startswith("n_") and c not in df.columns]
        if new_cols:
            df = df.merge(s[["ym"] + new_cols], on="ym", how="left")
    return df
'''
rep(old2, new2, "P2 load_ic_monthly")

# ---------------- P3: gate_max_corr ----------------
old3 = '''def gate_max_corr(reg):
    """门禁3：候选新增因子 vs 在役(active)因子 最高|ρ|<0.7。
    数据源：results/factor_ic_corr.csv（因子IC相关矩阵，W1 catalog附属）优先；
    矩阵未覆盖组合→ catalog corr_alerts 成员关系判 ≥阈值下限；两者均缺→N/A。"""
    import pandas as pd
    cat_p = os.path.join(RESULTS, "factor_catalog_v2.json")
    corr_p = os.path.join(RESULTS, "factor_ic_corr.csv")
    act = find_active()
    active_factors = set((act.get("selection") or {}).get("factors", [])) if act else set()
    cand_factors = reg["selection"].get("factors", [])
    new_factors = [f for f in cand_factors if f not in active_factors]
    if not new_factors:
        # E3修复(task-0292): 无新增因子时相关性无信息量 → N/A（不折减总判定，也不计PASS）
        return {"status": "N/A", "max_abs_corr": None, "worst_pair": None,
                "note": "无新增因子（因子集与active一致），相关性门禁无信息量 → N/A"}
    corr, cat = None, None
    if os.path.exists(corr_p):
        try:
            corr = pd.read_csv(corr_p, index_col=0)
        except Exception:
            corr = None
    if os.path.exists(cat_p):
        try:
            cat = load_json(cat_p).get("factors", {})
        except Exception:
            cat = None
    if corr is None and cat is None:
        return {"status": "N/A", "note": "factor_catalog_v2/factor_ic_corr 均缺失（W1交付），该项跳过"}
    mx, worst, unresolved = 0.0, None, []
    for f in new_factors:
        for g in active_factors:
            v = None
            if corr is not None and f in corr.index and g in corr.columns:
                try:
                    v = abs(float(corr.loc[f, g]))
                except Exception:
                    v = None
            if v is None and cat is not None:
                alerts = set((cat.get(g) or {}).get("corr_alerts") or [])
                if f in alerts:
                    v = 0.6  # catalog corr_alerts 成员 ⇒ |ρ|≥阈值下限（W1阈值0.6）
            if v is None:
                unresolved.append((f, g))
                continue
            if v > mx:
                mx, worst = v, (f, g)
    st = "PASS" if mx < GATE_CONFIG["max_corr_max"] else "FAIL"
    out = {"status": st, "max_abs_corr": round(mx, 4), "worst_pair": worst,
           "n_new_factors": len(new_factors), "new_factors": new_factors,
           "threshold": GATE_CONFIG["max_corr_max"]}
    if unresolved:
        out["unresolved_pairs"] = len(unresolved)
        out["note"] = f"{len(unresolved)}个组合无相关性数据（按未超限处理，待W1全量矩阵）"
    return out
'''
new3 = '''def _guard_exempt_pairs(new_factors, active_reg):
    """D-20260819-G3CORR（task-0398）：返回应豁免 g3 比较的 (new_factor, guard_col) 对集合。
    豁免条件（R-242 建议#1，全部满足才豁免）：
      1) 在役 params.e1_guard 为真（E1 硬护栏在位）；
      2) 护栏列 = params.mom_cols 或默认 [ret120]，登记在在役 selection.factors 中；
      3) 该护栏列不出现在排序 specs（ext_specs / ext_factor / sort / ext_weights）里
         ——即「护栏登记项」而非「排序因子」（真排序因子不豁免）；
      4) 候选新增因子是该护栏列的因子化替身（GUARD_CORR_CONFIG.guard_avatars 显式名单）。
    在役 registry 无 e1_guard / 候选无替身因子 → 空集，行为与旧版完全一致。"""
    if not GUARD_CORR_CONFIG.get("enabled", True):
        return set()
    sel = (active_reg or {}).get("selection") or {}
    params = sel.get("params") or {}
    if not params.get("e1_guard"):
        return set()
    guard_cols = params.get("mom_cols") or GUARD_CORR_CONFIG["guard_col_default"]
    reg_factors = set(sel.get("factors") or [])
    sort_blob = json.dumps([params.get("ext_specs"), params.get("ext_factor"),
                            params.get("sort"), params.get("ext_weights")],
                           ensure_ascii=False, default=str)
    avatars = GUARD_CORR_CONFIG.get("guard_avatars") or {}
    ex = set()
    for gc in guard_cols:
        if gc not in reg_factors or gc in sort_blob:
            continue  # 未登记在 factors，或本身参与排序 → 不豁免
        for f in new_factors:
            if f in avatars.get(gc, []):
                ex.add((f, gc))
    return ex


def gate_max_corr(reg, active=None):
    """门禁3：候选新增因子 vs 在役(active)因子 最高|ρ|<0.7。
    数据源（优先级）：results/factor_ic_corr.csv（因子IC相关矩阵，W1 catalog附属）→
    catalog corr_alerts 成员关系判 ≥阈值下限 → 月度IC序列 Pearson（≥24 月重叠，
    D-20260819-G3CORR 兜底，与矩阵同源方法）；三者皆缺→N/A。
    D-20260819-G3CORR（task-0398）：在役「护栏登记项」（e1_guard 护栏列、不在排序 specs）
    对候选中该护栏的因子化替身（guard_avatars 名单）豁免比较——护栏行为已由 oos/dd 分量
    计价，g3 只度量「排序信息冗余」；豁免对会记录在 guard_exempt_pairs。oos/dd 不豁免。"""
    import pandas as pd
    cat_p = os.path.join(RESULTS, "factor_catalog_v2.json")
    corr_p = os.path.join(RESULTS, "factor_ic_corr.csv")
    act = active if active is not None else find_active()
    active_factors = set((act.get("selection") or {}).get("factors", [])) if act else set()
    cand_factors = reg["selection"].get("factors", [])
    new_factors = [f for f in cand_factors if f not in active_factors]
    if not new_factors:
        # E3修复(task-0292): 无新增因子时相关性无信息量 → N/A（不折减总判定，也不计PASS）
        return {"status": "N/A", "max_abs_corr": None, "worst_pair": None,
                "note": "无新增因子（因子集与active一致），相关性门禁无信息量 → N/A"}
    exempt = _guard_exempt_pairs(new_factors, act)  # D-20260819-G3CORR
    corr, cat = None, None
    if os.path.exists(corr_p):
        try:
            corr = pd.read_csv(corr_p, index_col=0)
        except Exception:
            corr = None
    if os.path.exists(cat_p):
        try:
            cat = load_json(cat_p).get("factors", {})
        except Exception:
            cat = None
    ic_df = load_ic_monthly()  # 含补充列（G3CORR），兜底数据源；缺失返回 None
    if corr is None and cat is None and ic_df is None:
        return {"status": "N/A", "note": "factor_ic_corr/factor_catalog_v2/月度IC 均缺失，该项跳过"}
    import numpy as np
    mx, worst, unresolved = 0.0, None, []
    src_cnt = {"matrix": 0, "catalog": 0, "ic_monthly": 0}
    for f in new_factors:
        for g in active_factors:
            if (f, g) in exempt:
                continue  # 护栏登记项 × 因子化替身 → 豁免（D-20260819-G3CORR）
            v = None
            if corr is not None and f in corr.index and g in corr.columns:
                try:
                    v = abs(float(corr.loc[f, g]))
                except Exception:
                    v = None
                if v is not None:
                    src_cnt["matrix"] += 1
            if v is None and cat is not None:
                alerts = set((cat.get(g) or {}).get("corr_alerts") or [])
                if f in alerts:
                    v = 0.6  # catalog corr_alerts 成员 ⇒ |ρ|≥阈值下限（W1阈值0.6）
                    src_cnt["catalog"] += 1
            if v is None and ic_df is not None and f in ic_df.columns and g in ic_df.columns:
                j = ic_df[[f, g]].dropna()
                if len(j) >= 24:
                    try:
                        v = abs(float(np.corrcoef(j[f].astype(float), j[g].astype(float))[0, 1]))
                        src_cnt["ic_monthly"] += 1
                    except Exception:
                        v = None
            if v is None:
                unresolved.append((f, g))
                continue
            if v > mx:
                mx, worst = v, (f, g)
    st = "PASS" if mx < GATE_CONFIG["max_corr_max"] else "FAIL"
    out = {"status": st, "max_abs_corr": round(mx, 4), "worst_pair": worst,
           "n_new_factors": len(new_factors), "new_factors": new_factors,
           "threshold": GATE_CONFIG["max_corr_max"],
           "corr_sources": src_cnt}
    if exempt:
        out["guard_exempt_pairs"] = sorted([list(p) for p in exempt])
        out["corr_policy"] = "D-20260819-G3CORR 护栏替身豁免（oos/dd 不豁免）"
    if unresolved:
        out["unresolved_pairs"] = len(unresolved)
        out["note"] = f"{len(unresolved)}个组合无相关性数据（按未超限处理，待W1全量矩阵）"
    return out
'''
rep(old3, new3, "P3 gate_max_corr")

with open(P, "w", encoding="utf-8") as f:
    f.write(src)
py_compile.compile(P, doraise=True)
print("py_compile OK, new size:", len(src))
