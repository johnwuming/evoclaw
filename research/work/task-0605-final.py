#!/usr/bin/env python3
# task-0605 终版：157 月双口径复算 + 同窗 G3 稳健性核验
import csv, json, math

def perf(rets):
    nav=1.0; peak=1.0; mdd=0.0
    for _,r in rets:
        nav*=(1+r); peak=max(peak,nav); mdd=min(mdd,nav/peak-1)
    n=len(rets); ann=nav**(12/n)-1
    vol=(sum(r*r for _,r in rets)/n)**0.5*math.sqrt(12)
    return {"n":n,"ann":round(ann*100,4),"vol":round(vol*100,4),"mdd":round(mdd*100,4),
            "sharpe":round(ann/vol,3),"calmar":round(ann/abs(mdd),3)}

arets=[]; prev=1.0
with open("04-投资研究/f6_curves/a_alone_nav.csv") as f:
    for r in csv.DictReader(f):
        v=float(r["nav"]); arets.append((r["date"], v/prev-1.0)); prev=v
# 补 2026-08（R-331 口径：a13 引擎 08-14/07-31）
r_aug = 64.30956281284777/62.73930028086797 - 1
arets.append(("2026-08-31", r_aug))

gret={}; gnav={}; prev=1.0
with open("04-投资研究/engines/gold/shadow_nav.csv") as f:
    for r in csv.DictReader(f):
        gret[r["month"]]=float(r["gold_ret"])
        v=float(r["nav"]); gnav[r["month"]]=v/prev-1.0; prev=v

def comb(a_rets, gmap, wA):
    return [(d, wA*ra+(1-wA)*gmap[d]) for d,ra in a_rets]

out={}
out["r372_replica_5842_goldret_n157"] = perf(comb(arets,gret,0.58))
out["r372_replica_5803_n157"] = perf(comb(arets,gret,0.5803))
out["display_replica_A_goldeng_n157"] = perf(comb(arets,gnav,0.5803))
out["display_replica_A_goldeng_n157_w58"] = perf(comb(arets,gnav,0.58))
# 同窗 2016-08..2026-08（R-372 表内 n=121 口径）：gold_ret 版 vs gold引擎版
w1616=[(d,r) for d,r in arets if d>="2016-08-31"]
out["same121_goldret"] = perf(comb(w1616,gret,0.58))
out["same121_goldeng"] = perf(comb(w1616,gnav,0.58))
# 2026-08 单月两口径
out["aug2026"] = {"A": round(r_aug*100,4), "gold_ret": round(gret["2026-08-31"]*100,4), "gold_eng": round(gnav["2026-08-31"]*100,4)}
json.dump(out, open("work/task-0605-results-final.json","w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
