import sys, os, time
sys.path.insert(0, "/home/noname/quant-evolve/scripts")
import factor_expansion_v3ak as fe
NEW = "/home/noname/quant-evolve/data/derived/fin_deep_monthly_panel_ak.ashare.parquet"
assert not os.path.exists(NEW), NEW
fe.FIN_PANEL_CACHE = NEW
t0 = time.time()
p = fe.build_fin_deep_monthly_panel()
print("[rebuild] DONE shape=%s codes=%d secs=%.0f" % (p.shape, p.code.nunique(), time.time()-t0), flush=True)
cf = ["accrual_quality", "cf_or_ratio", "cf_np_ratio", "ocf_stability"]
yr = p["ym"].str[:4].astype(int)
last_y = int(p["ym"].max()[:4])
r12 = p[yr >= last_y - 0]  # 近12个月近似: 最新年
r36 = p[yr >= last_y - 2]
print("[after] rows=%d codes=%d ym %s->%s" % (len(p), p.code.nunique(), p.ym.min(), p.ym.max()), flush=True)
for c in cf:
    print("  %s nonnull all=%.4f recent3y=%.4f" % (c, p[c].notna().mean(), r36[c].notna().mean()), flush=True)
print("[after] recent12m(ym>=%d-09) accrual_quality nonnull=" % (last_y - 1), flush=True)
rec = p[p.ym >= "%d-09" % (last_y - 1)]
print("  accrual_quality=%.4f cf_or_ratio=%.4f ocf_stability=%.4f (rows=%d)" % (rec.accrual_quality.notna().mean(), rec.cf_or_ratio.notna().mean(), rec.ocf_stability.notna().mean(), len(rec)), flush=True)
print("[ALL-DONE]", flush=True)
