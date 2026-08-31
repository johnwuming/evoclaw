#!/usr/bin/env python3
# 验证：展示口径金腿 = nav_curves gold 列（引擎净值） vs R-372 金腿 = shadow gold_ret
import csv, json, math

def perf(rets):
    nav=1.0; peak=1.0; mdd=0.0
    for _,r in rets:
        nav*=(1+r); peak=max(peak,nav); mdd=min(mdd,nav/peak-1)
    n=len(rets); ann=nav**(12/n)-1
    vol=(sum(r*r for _,r in rets)/n)**0.5*math.sqrt(12)
    return {"n":n,"ann":round(ann*100,4),"vol":round(vol*100,4),"mdd":round(mdd*100,4),
            "sharpe":round(ann/vol,3),"calmar":round(ann/abs(mdd),3),"final":round(nav,4)}

a=[]; gnav=[]; gret={}
with open("04-投资研究/f6_curves/a_alone_nav.csv") as f:
    for r in csv.DictReader(f): a.append((r["date"],float(r["nav"])))
with open("tools_link_tmp" if False else "/root/.openclaw/workspace/tools/quant-bff/live/data/nav_curves.csv") as f:
    for r in csv.DictReader(f): gnav.append((r["month"],float(r["gold"])))
with open("04-投资研究/engines/gold/shadow_nav.csv") as f:
    for r in csv.DictReader(f): gret[r["month"]]=float(r["gold_ret"])

# gold 引擎净值 -> 月收益（首月 nav/1-1）
gnav_rets=[]; prev=1.0
for d,v in gnav:
    gnav_rets.append((d, v/prev-1.0)); prev=v

# gold_ret 单腿 vs gold 引擎净值单腿
print("gold_ret alone      :", perf([(d,gret[d]) for d,_ in a]))
print("gold_engineNAV alone:", perf(gnav_rets))

def two_leg(a_rets, g_map, wA):
    out=[]
    for d,ra in a_rets:
        rg=g_map[d]; out.append((d, wA*ra+(1-wA)*rg))
    return out

amap=dict(a); arets=[]
prev=1.0
for d,v in a: arets.append((d, v/prev-1.0)); prev=v

# 组合：A + gold引擎净值（展示口径近似，月度再平衡 0.5803/0.4197）
gmap_nav=dict(gnav_rets)
comb = two_leg(arets, gmap_nav, 0.5803)
print("58/42 A+goldENGINE n156:", perf(comb))
# 组合：A + gold_ret（R-372 口径）
comb2 = two_leg(arets, gret, 0.58)
print("58/42 A+goldRET   n156:", perf(comb2))

# 2026-06 当月对照
for m in ["2026-05-31","2026-06-30","2026-07-31"]:
    ra=dict(arets)[m]; print(m, "A=%.2f%%"%(ra*100), "gold_ret=%.2f%%"%(gret[m]*100), "goldENG=%.2f%%"%(gmap_nav[m]*100))
# gold 引擎 vs gold_ret 逐月收益差异统计
diffs=[(d, gret[d]-gmap_nav[d]) for d,_ in arets if d in gmap_nav]
big=[(d,round(x*100,2)) for d,x in diffs if abs(x)>0.02]
print("月收益差>2pp 的月份数:", len(big), "示例:", big[:10])
