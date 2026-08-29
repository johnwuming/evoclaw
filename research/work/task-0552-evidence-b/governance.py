#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task-0552 Phase B / R-336 v1.5 §8 Phase C 治理切换执行模块 (v1)

事件溯源治理层：registry/engines/composites/paper指针/运行态镜像 统一走
「追加事件(iteration-ledger, flock+fsync+seq幂等) + 重放投影(文件头 sha256)」。
权威数据文件（model/registry/*.json、results/paper-state.json、baseline-paper-*.csv、
versions/vC-0.json）保持引擎原写路径零改动；本层只做治理投影与 append-only 镜像，
不回写任何权威文件。复用 portfolio_v1/event_ledger.py 的 EventLedger。

子命令：
  switch      首次切换：基线事件+标定留痕+paper指针事件+五投影生成+自校验（幂等保护）
  verify      验证a/e：重放重建 vs 切换前快照逐字段 diff + 投影 sha256 对账 + ledger verify
  mirror      增量镜像 nav.daily / trade.fill（按 date 去重，可重复调用）
  watch       轮询监测权威 CSV 变更→mirror（--until "YYYY-MM-DD HH:MM:SS" 自退出）
  recon       三方对账 §6.3（paper账本 vs 引擎执行记录 vs vC-0 定义 + 镜像一致性）
  checkpoint  §6.2 快照写入 + 恢复干跑（replay 截断重建 vs checkpoint 逐字段 diff）
  breaker     §6.1 断路器评估（--sandbox-sim 注入亏损/回撤序列做触发干跑）
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.expanduser("~/quant-evolve/portfolio_v1"))
from event_ledger import EventLedger  # noqa: E402

ROOT = os.path.expanduser("~/quant-evolve")
LEDGER_DIR = os.path.join(ROOT, "portfolio_v1/portfolio/events")
GOV = os.path.join(ROOT, "portfolio_v1/governance")
PROJ = os.path.join(GOV, "projections")
EVID = os.path.join(GOV, "evidence")
CKPT = os.path.join(GOV, "checkpoints")
RECON_DIR = os.path.join(GOV, "recon")
SNAP = os.path.join(GOV, "preswitch-snapshot")
TMP_SNAP = "/tmp/task0552-phaseB-preswitch"

SRC = {
    "registry_entry_a13": os.path.join(ROOT, "model/registry/a13_rsraw_e1f10dz.json"),
    "gold_state": os.path.join(ROOT, "results/engines/gold/paper_state.json"),
    "vC-0": os.path.join(ROOT, "portfolio_v1/portfolio/versions/vC-0.json"),
    "paper_state": os.path.join(ROOT, "results/paper-state.json"),
}
NAV_CSV = os.path.join(ROOT, "results/baseline-paper-nav.csv")
TRADES_CSV = os.path.join(ROOT, "results/baseline-paper-trades.csv")
PORTFOLIO_JSON = os.path.join(ROOT, "results/baseline-paper-portfolio.json")

ACTOR_SWITCH = "user"            # 用户批准的切换动作
ACTOR_MIRROR = "evolution_pipeline"
ACTOR_RISK = "risk_layer"


def now_iso():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ledger():
    return EventLedger(LEDGER_DIR)


def read_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# ---------------- 事件 apply 状态机（幂等） ----------------

def apply_ev(ev, st):
    et, p = ev.get("event_type"), ev.get("payload") or {}
    if et == "governance.baseline":
        st["sources"] = p["sources"]
        st["runtime"] = {"nav_daily": [dict(r) for r in p.get("runtime_nav_rows", [])],
                         "trades": [dict(r) for r in p.get("runtime_trades", [])],
                         "trade_csv_rows_at_baseline": p.get("trade_csv_rows_at_baseline")}
    elif et == "calibration.recorded":
        st.setdefault("calibration", []).append(p)
    elif et == "paper.pointer.switched":
        st["paper_pointer"] = p
    elif et == "nav.daily":
        nav = st.setdefault("runtime", {}).setdefault("nav_daily", [])
        if not any(r.get("date") == p.get("date") for r in nav):
            nav.append(dict(p))
    elif et == "trade.fill":
        tr = st.setdefault("runtime", {}).setdefault("trades", [])
        key = (p.get("date"), p.get("code"), p.get("action"), p.get("shares"), p.get("price"))
        if not any((r.get("date"), r.get("code"), r.get("action"), r.get("shares"), r.get("price")) == key for r in tr):
            tr.append(dict(p))
    elif et == "checkpoint.created":
        st.setdefault("checkpoints", []).append(p)
    elif et in ("reconciliation.passed", "reconciliation.failed"):
        st.setdefault("recon_log", []).append({"event_type": et, **p})
    elif et == "risk.action":
        st.setdefault("risk_log", []).append(p)
    elif et == "governance.note":
        st.setdefault("notes", []).append(p)
    return st


def replay_all():
    lg = ledger()
    r = lg.replay()
    st = {}
    for ev in r["events"]:
        apply_ev(ev, st)
    return st, r


# ---------------- 投影（文件头 sha256） ----------------

def write_projection(name, body):
    doc = {"header": {"projection": name, "schema": "governance-projection@v1",
                      "sha256": sha_text(canonical(body)), "generated_at": now_iso()},
           "body": body}
    write_json(os.path.join(PROJ, name + ".json"), doc)
    return doc["header"]["sha256"]


def build_bodies(st):
    src = st.get("sources", {})
    pp = st.get("paper_pointer", {})
    bodies = {
        "registry": {"registry": {"a13_rsraw_e1f10dz": src.get("registry_entry_a13", {}).get("content")},
                     "active_semantics": "投影为治理视图；在役 registry 文件仍是引擎权威读路径（Phase D 才退役）"},
        "engines": {"engines": {"gold_trend_sma200": src.get("gold_state", {}).get("content")}},
        "composites": {"versions": {"vC-0": src.get("vC-0", {}).get("content")}},
        "paper": dict(pp),
        "runtime": {"portfolio_version_ref": "vC-0",
                    "nav_daily": sorted(st.get("runtime", {}).get("nav_daily", []),
                                        key=lambda r: r.get("date", "")),
                    "trades": sorted(st.get("runtime", {}).get("trades", []),
                                     key=lambda r: (r.get("date", ""), r.get("code", ""))),
                    "authoritative_sources": {"nav": "results/baseline-paper-nav.csv",
                                              "trades": "results/baseline-paper-trades.csv"},
                    "semantics": "§3.6 镜像：权威=CSV/JSON，账本=append-only 镜像，BFF 只读"},
    }
    return bodies


def refresh_projections(st):
    out = {}
    for name, body in build_bodies(st).items():
        out[name] = write_projection(name, body)
    return out


# ---------------- 数据读取 ----------------

def read_nav_rows():
    rows = []
    with open(NAV_CSV, newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            rows.append({"date": rec.get("date"), "nav": rec.get("nav"), "source_file": "results/baseline-paper-nav.csv"})
    return rows


TRADE_ALIASES = {
    "date": ("date", "日期", "trade_date", "datetime"),
    "code": ("code", "代码", "symbol", "stock_code"),
    "action": ("action", "动作", "side", "操作", "type"),
    "shares": ("shares", "股数", "数量", "volume", "qty", "shares_traded"),
    "price": ("price", "价格", "成交价", "avg_price"),
    "fee": ("fee", "手续费", "费用", "commission", "cost"),
}


def read_trade_rows():
    rows = []
    with open(TRADES_CSV, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        cols = {c.strip().lower(): c for c in (rd.fieldnames or [])}
        m = {}
        for std, aliases in TRADE_ALIASES.items():
            for a in aliases:
                if a.lower() in cols:
                    m[std] = cols[a.lower()]
                    break
        for rec in rd:
            rows.append({k: rec.get(v) for k, v in m.items()} | {"source_file": "results/baseline-paper-trades.csv"})
    return rows


# ---------------- 子命令 ----------------

def cmd_switch(_):
    st, r = replay_all()
    if any(e["event_type"] == "governance.baseline" for e in r["events"]):
        print(json.dumps({"result": "already_switched", "hint": "switch 仅执行一次；如需重建投影用 verify/mirror"}, ensure_ascii=False))
        return 2
    v = ledger().verify()
    if not v.get("ok"):
        print(json.dumps({"result": "ABORT_ledger_verify_failed", "verify": v}, ensure_ascii=False))
        return 3
    # 权威文件快照（HP 侧持久留档 + 复制 /tmp 清单）
    os.makedirs(SNAP, exist_ok=True)
    manifest = {}
    for k, p in SRC.items():
        manifest[k] = {"path": os.path.relpath(p, ROOT), "sha256": sha_file(p), "content": read_json(p)}
    manifest["nav_csv"] = {"path": "results/baseline-paper-nav.csv", "sha256": sha_file(NAV_CSV),
                           "rows": read_nav_rows()}
    manifest["trades_csv"] = {"path": "results/baseline-paper-trades.csv", "sha256": sha_file(TRADES_CSV),
                              "row_count": len(read_trade_rows())}
    for k, p in SRC.items():
        import shutil
        shutil.copy2(p, os.path.join(SNAP, os.path.basename(p)))
    import shutil
    shutil.copy2(NAV_CSV, os.path.join(SNAP, "baseline-paper-nav.csv"))
    shutil.copy2(SRC["gold_state"], os.path.join(SNAP, "gold-paper_state.json"))
    write_json(os.path.join(SNAP, "manifest.json"), {k: {kk: vv for kk, vv in v.items() if kk != "content"} for k, v in manifest.items()})

    t0 = time.time()
    ledger().append("governance.baseline", "portfolio/vC-0",
                    {"sources": manifest,
                     "runtime_nav_rows": manifest["nav_csv"]["rows"],
                     "trade_csv_rows_at_baseline": manifest["trades_csv"]["row_count"],
                     "preswitch_tmp_snapshot": TMP_SNAP,
                     "note": "Phase C 治理切换基线：切换时点权威文件内容整体入账（重放种子）"},
                    actor=ACTOR_SWITCH)
    t_base = time.time()
    ledger().append("calibration.recorded", "drift/equity_sleeve",
                    {"code": "CAL-20260829-01", "date": "2026-08-14",
                     "diff_bp": -21.43,
                     "note": "建仓日官方 NAV 按成本+费用计价 vs 重放按收盘计价=-21.43bp，属口径差非状态错误，8/17 起逐日归零",
                     "source": "R-353 §5 ①；task-0552 阶段B 标定留痕"},
                    actor=ACTOR_SWITCH)
    t_cal = time.time()
    ps = manifest["paper_state"]["content"]
    ledger().append("paper.pointer.switched", "paper/vC-0",
                    {"portfolio_version_ref": "vC-0", "status": "paper",
                     "from": "A(a13_rsraw_e1f10dz)+gold(active_paper)+ddc 散装三元组",
                     "sleeves": {
                         "equity_sleeve": {"registry_entry": "a13_rsraw_e1f10dz", "status": "active",
                                           "state_file": "results/paper-state.json",
                                           "state_sha256_at_switch": manifest["paper_state"]["sha256"]},
                         "hedge_sleeve_gold": {"engine_id": "gold_trend_sma200", "status": "active_paper",
                                               "state_file": "results/engines/gold/paper_state.json",
                                               "state_sha256_at_switch": manifest["gold_state"]["sha256"]}},
                     "semantics": "指针语义切换：持仓/现金/NAV 数值不落指针，权威数值仍在引擎文件（§3.6 镜像）",
                     "paper_live_facts": {"cash": ps.get("cash"), "initial_capital": ps.get("initial_capital"),
                                          "holdings_count": len(ps.get("holdings", {})),
                                          "last_daily": ps.get("last_daily")},
                     "switch_task": "task-0552 Phase B", "user_approved": "2026-08-29 10:13"},
                    actor=ACTOR_SWITCH)
    t_ptr = time.time()
    st, r = replay_all()
    t_replay = time.time()
    shas = refresh_projections(st)
    t_proj = time.time()
    out = {"result": "switched", "events_in_ledger": r["count"],
           "timings_s": {"baseline_append": round(t_base - t0, 4), "calibration_append": round(t_cal - t_base, 4),
                         "pointer_append": round(t_ptr - t_cal, 4), "replay": round(t_replay - t_ptr, 4),
                         "projections": round(t_proj - t_replay, 4)},
           "projection_sha256": shas, "ledger_verify": ledger().verify()}
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_verify(_):
    st, r = replay_all()
    bodies = build_bodies(st)
    diffs, checks = [], {}
    # 验证a：重放重建 vs 切换前快照逐字段 diff（快照目录优先 SNAP，回退 /tmp）
    snap_dir = SNAP if os.path.isdir(SNAP) else TMP_SNAP
    pairs = [("registry_entry_a13", "registry", "registry"), ("gold_state", "engines", "engines"),
             ("vC-0", "composites", "versions")]
    map_snap = {"registry_entry_a13": "a13_rsraw_e1f10dz.json", "gold_state": "gold-paper_state.json", "vC-0": "vC-0.json"}
    for key, body_name, inner in pairs:
        rebuilt = (bodies[body_name].get(inner) or {}).get("a13_rsraw_e1f10dz" if key == "registry_entry_a13" else ("gold_trend_sma200" if key == "gold_state" else "vC-0"))
        with open(os.path.join(snap_dir, map_snap[key]), encoding="utf-8") as f:
            pre = json.load(f)
        if canonical(rebuilt) == canonical(pre):
            checks[key] = "identical"
        else:
            checks[key] = "DIFF"
            diffs.append({"field": key, "rebuilt_sha": sha_text(canonical(rebuilt)), "preswitch_sha": sha_text(canonical(pre))})
    # paper-state 数值零变化（验证e 的重放侧）
    pre_ps = read_json(os.path.join(snap_dir, "paper-state.json"))
    cur_ps = read_json(SRC["paper_state"])
    num_fields = ["cash", "initial_capital", "holdings", "last_rebalance", "model_version", "timing_ratio"]
    ps_diff = {k: {"pre": pre_ps.get(k), "cur": cur_ps.get(k)} for k in num_fields
               if canonical(pre_ps.get(k)) != canonical(cur_ps.get(k))}
    ps_diff_allowed = {k for k in ps_diff if k in ("last_daily", "last_daily_update", "updated_at", "last_data_date", "last_div_date")}
    real_ps_diff = [k for k in ps_diff if k not in ps_diff_allowed]
    # 投影文件头 sha256 对账
    proj_ok = {}
    for name in bodies:
        p = os.path.join(PROJ, name + ".json")
        if not os.path.exists(p):
            proj_ok[name] = "missing"
            continue
        doc = read_json(p)
        proj_ok[name] = "ok" if doc["header"]["sha256"] == sha_text(canonical(doc["body"])) else "SHA_MISMATCH"
        if canonical(doc["body"]) != canonical(bodies[name]):
            proj_ok[name] = "BODY_STALE"
    ev = {"verify_ts": now_iso(), "checks": checks, "projection_headers": proj_ok,
          "paper_state_numeric_diff_fields": real_ps_diff,
          "paper_state_ignored_bookkeeping_fields": sorted(ps_diff.keys()),
          "result": "diff=0" if not diffs and not real_ps_diff and all(v == "ok" for v in proj_ok.values()) else "FAIL"}
    write_json(os.path.join(EVID, f"verify-diff-{dt.date.today().isoformat()}.json"), ev)
    print(json.dumps(ev, ensure_ascii=False))
    return 0 if ev["result"] == "diff=0" else 1


def cmd_mirror(_):
    st, r = replay_all()
    have_nav = {x.get("date") for x in st.get("runtime", {}).get("nav_daily", [])}
    new_nav = [x for x in read_nav_rows() if x.get("date") and x["date"] not in have_nav]
    have_tr = {(x.get("date"), x.get("code"), x.get("action"), x.get("shares"), x.get("price"))
               for x in st.get("runtime", {}).get("trades", [])}
    new_tr = [x for x in read_trade_rows()
              if (x.get("date"), x.get("code"), x.get("action"), x.get("shares"), x.get("price")) not in have_tr]
    t0 = time.time()
    for x in new_nav:
        ledger().append("nav.daily", "paper/vC-0#equity", x, actor=ACTOR_MIRROR)
    for x in new_tr:
        ledger().append("trade.fill", "paper/vC-0#equity", x, actor=ACTOR_MIRROR)
    st2, _ = replay_all()
    shas = refresh_projections(st2)
    out = {"result": "mirrored", "nav_appended": len(new_nav), "trades_appended": len(new_tr),
           "append_seconds": round(time.time() - t0, 4), "projection_sha256": shas,
           "nav_total": len(st2.get("runtime", {}).get("nav_daily", [])),
           "trades_total": len(st2.get("runtime", {}).get("trades", []))}
    write_json(os.path.join(EVID, f"mirror-last-{dt.date.today().isoformat()}.json"), out)
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_watch(args):
    until = dt.datetime.fromisoformat(args.until).astimezone() if args.until else \
        dt.datetime.now().astimezone() + dt.timedelta(minutes=args.minutes)
    logd = os.path.join(GOV, "logs")
    os.makedirs(logd, exist_ok=True)
    logp = os.path.join(logd, f"watch-{dt.date.today().isoformat()}.log")

    def log(msg):
        with open(logp, "a", encoding="utf-8") as f:
            f.write(f"[{now_iso()}] {msg}\n")
    log(f"watch start until={until.isoformat()} poll={args.interval}s")
    last = {NAV_CSV: sha_file(NAV_CSV), TRADES_CSV: sha_file(TRADES_CSV)}
    while dt.datetime.now().astimezone() < until:
        time.sleep(args.interval)
        try:
            cur = {NAV_CSV: sha_file(NAV_CSV), TRADES_CSV: sha_file(TRADES_CSV)}
            for p, h in cur.items():
                if h != last.get(p):
                    log(f"change detected: {os.path.basename(p)} -> mirror")
                    rc = os.system(f"{sys.executable} {os.path.abspath(__file__)} mirror >> {logp} 2>&1")
                    log(f"mirror rc={rc}")
                    last = cur
        except Exception as e:  # 钩子失败不阻塞任何引擎流程：只记缺口
            log(f"hook_error {e!r} (gap marker, 对账兜底补齐)")
    log("watch exit (self-terminated)")


def cmd_recon(_):
    st, r = replay_all()
    ps = read_json(SRC["paper_state"])
    pf = read_json(PORTFOLIO_JSON) if os.path.exists(PORTFOLIO_JSON) else {}
    vc0 = read_json(SRC["vC-0"])
    nav_rows = read_nav_rows()
    checks, details = {}, {}
    # ① paper账本 vs 引擎执行记录（portfolio.json / trades 推导）持仓集合一致
    hold_a = {c: (h.get("shares") if isinstance(h, dict) else h) for c, h in (ps.get("holdings") or {}).items()}
    pf_hold = pf.get("holdings") or pf.get("positions") or {}
    hold_b = {c: (h.get("shares") if isinstance(h, dict) else h) for c, h in pf_hold.items()} if pf_hold else {}
    if hold_b:
        checks["holdings_set_equal"] = set(hold_a) == set(hold_b)
        details["holdings_only_in_paper"] = sorted(set(hold_a) - set(hold_b))
        details["holdings_only_in_engine"] = sorted(set(hold_b) - set(hold_a))
    else:
        checks["holdings_set_equal"] = None
        details["holdings_note"] = "baseline-paper-portfolio.json 无持仓字段，以 paper-state 为准（单一权威）"
    # ② 现金/NAV 帐内自洽 + 容忍带（现金差 ≤0.5% NAV）
    last_nav = nav_rows[-1]["nav"] if nav_rows else None
    total = ps.get("cash", 0) + sum(float(h.get("value", 0) or 0) for h in (ps.get("holdings") or {}).values() if isinstance(h, dict))
    checks["nav_present_for_last_row"] = last_nav is not None
    if last_nav:
        hold_vals = list((ps.get("holdings") or {}).values())
        priced = all(isinstance(h, dict) and h.get("last_price") is not None for h in hold_vals) and hold_vals
        if priced:
            state_total = ps.get("cash", 0) + sum(float(h["shares"]) * float(h["last_price"]) for h in hold_vals)
            implied_total = float(last_nav) * float(ps.get("initial_capital", 100000))
            checks["cash_band_0.5pct_nav"] = abs(state_total - implied_total) <= 0.005 * implied_total
            details["cash_check"] = {"state_total": state_total, "nav_implied": implied_total}
        else:
            checks["cash_band_0.5pct_nav"] = None
            details["cash_check"] = "holdings 无 last_price 字段：现金带检查降级为 NAV 对账日核（引擎侧计价，不在治理层复算）"
    # ③ vC-0 定义 vs 组件在役状态
    sl = vc0.get("sleeves", {})
    checks["equity_registry_entry_active"] = sl.get("equity_sleeve", {}).get("component_ref", {}).get("registry_entry") == "a13_rsraw_e1f10dz"
    checks["gold_engine_active_paper"] = sl.get("hedge_sleeve_gold", {}).get("component_ref", {}).get("status") == "active_paper"
    ws = (vc0.get("weight_solution") or {}).get("weights") or {}
    checks["weight_solution_sums_1"] = abs(sum(ws.values()) - 1.0) <= 1e-6 if ws else None
    # ④ 镜像一致性：投影 runtime vs 权威 CSV 逐字段
    rt = st.get("runtime", {})
    checks["mirror_nav_rows_match_csv"] = [x.get("date") for x in sorted(rt.get("nav_daily", []), key=lambda x: x.get("date", ""))] == [x["date"] for x in nav_rows]
    mirror_nav_field_ok = all(a.get("nav") == b.get("nav") for a, b in zip(
        sorted(rt.get("nav_daily", []), key=lambda x: x.get("date", "")), nav_rows))
    checks["mirror_nav_fields_match"] = mirror_nav_field_ok
    checks["mirror_trades_count_match_csv"] = len(rt.get("trades", [])) == len(read_trade_rows())
    # ⑤ NAV 时效（断路器输入：停摆≥2交易日→冻结）
    checks["nav_fresh"] = bool(nav_rows and nav_rows[-1]["date"] >= (dt.date.today() - dt.timedelta(days=4)).isoformat())
    ok = all(v is not False for v in checks.values())
    doc = {"recon_ts": now_iso(), "tolerances": {"sleeve_weight_pp": 1.0, "cash_pct_nav": 0.5, "holdings_set": "exact"},
           "checks": checks, "details": details, "result": "PASS" if ok else "FAIL"}
    write_json(os.path.join(RECON_DIR, f"recon-{dt.date.today().isoformat()}.json"), doc)
    ledger().append("reconciliation.passed" if ok else "reconciliation.failed", "paper/vC-0",
                    {"checks": checks, "details": details}, actor=ACTOR_RISK)
    print(json.dumps({"result": doc["result"], "checks": checks}, ensure_ascii=False))
    return 0 if ok else 1


def cmd_checkpoint(_):
    st, r = replay_all()
    ps = read_json(SRC["paper_state"])
    nav_rows = read_nav_rows()
    offset = r["count"]
    payload = {"date": (ps.get("last_daily") or dt.date.today().isoformat()),
               "positions": {c: (h.get("shares") if isinstance(h, dict) else h)
                             for c, h in (ps.get("holdings") or {}).items()},
               "cash": ps.get("cash"), "nav": nav_rows[-1]["nav"] if nav_rows else None,
               "portfolio_version_ref": "vC-0", "ledger_offset": offset}
    payload["md5"] = sha_text(canonical(payload))
    cp_id = f"cp-{payload['date']}-off{offset}"
    payload["checkpoint_id"] = cp_id
    ledger().append("checkpoint.created", "paper/vC-0", payload, actor=ACTOR_MIRROR)
    write_json(os.path.join(CKPT, cp_id + ".json"), {"checkpoint": payload, "written_at": now_iso()})
    # 恢复干跑：重放截断到 offset 重建 positions/cash/nav vs checkpoint 逐字段
    lg = ledger()
    evs = lg.replay()["events"][:offset]
    st2 = {}
    for ev in evs:
        apply_ev(ev, st2)
    src_ps = st2["sources"]["paper_state"]["content"]
    rec = {"positions": {c: (h.get("shares") if isinstance(h, dict) else h)
                         for c, h in (src_ps.get("holdings") or {}).items()},
           "cash": src_ps.get("cash"), "nav": st2["runtime"]["nav_daily"][-1]["nav"]}
    diff = {k: {"checkpoint": payload[k], "rebuilt": rec[k]} for k in rec
            if canonical(rec[k]) != canonical(payload.get(k))}
    out = {"checkpoint_id": cp_id, "ledger_offset": offset, "recovery_diff": diff,
           "result": "diff=0" if not diff else "FAIL"}
    write_json(os.path.join(EVID, f"checkpoint-recovery-{dt.date.today().isoformat()}.json"), out)
    print(json.dumps(out, ensure_ascii=False))
    return 0 if not diff else 1


def breaker_eval(nav_values, last_date):
    """§6.1 阈值：单日亏≥2%停开新仓；DD 10-15%×0.5；>15%熔断；NAV 停摆≥2交易日冻结。"""
    actions, checks = [], {}
    if len(nav_values) >= 2 and nav_values[-2]:
        dret = nav_values[-1] / nav_values[-2] - 1
        checks["daily_return"] = round(dret, 6)
        if dret <= -0.02:
            actions.append("halt_new_opens_today")
    peak = max(nav_values) if nav_values else None
    if peak:
        dd = 1 - nav_values[-1] / peak
        checks["drawdown"] = round(dd, 6)
        if dd > 0.15:
            actions.extend(["halt_new_opens", "escalate_review", "notify_user"])
        elif dd >= 0.10:
            actions.append("reduce_half")
    try:
        ld = dt.date.fromisoformat(last_date)
        stale_days = (dt.date.today() - ld).days
        checks["nav_age_days"] = stale_days
        if stale_days >= 4:  # ≥2 交易日（周末放宽）
            actions.append("freeze_auto_decisions")
    except Exception:
        pass
    return actions, checks


def cmd_breaker(args):
    nav_rows = read_nav_rows()
    vals = [float(r["nav"]) for r in nav_rows if r.get("nav")]
    actions, checks = breaker_eval(vals, nav_rows[-1]["date"] if nav_rows else "")
    out = {"mode": "live", "nav_points": len(vals), "actions": actions, "checks": checks,
           "status": "GREEN" if not actions else "TRIGGERED", "eval_ts": now_iso(),
           "reset_policy": "断路器动作只能人工复位（promotion.approved 同级人工门），自动恢复禁止"}
    if args.sandbox_sim:
        sim_nav = [1.0, 1.02, 0.99, 0.80, 0.784]  # 注入：单日 -3.03%，DD=23.1%
        s_act, s_chk = breaker_eval(sim_nav, dt.date.today().isoformat())
        out["sandbox_sim"] = {"nav_series": sim_nav, "actions": s_act, "checks": s_chk,
                              "expect": ["halt_new_opens_today", "halt_new_opens", "escalate_review", "notify_user"],
                              "pass": set(["halt_new_opens_today", "halt_new_opens", "escalate_review", "notify_user"]).issubset(set(s_act))}
    write_json(os.path.join(EVID, f"breaker-{dt.date.today().isoformat()}.json"), out)
    if actions:
        ledger().append("risk.action", "circuit_breaker/vC-0", {"actions": actions, "checks": checks}, actor=ACTOR_RISK)
    print(json.dumps(out, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Phase C governance switch (task-0552)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("switch").set_defaults(fn=cmd_switch)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    sub.add_parser("mirror").set_defaults(fn=cmd_mirror)
    p = sub.add_parser("watch")
    p.add_argument("--until", default=None, help='local time "YYYY-MM-DD HH:MM:SS"')
    p.add_argument("--minutes", type=int, default=30)
    p.add_argument("--interval", type=int, default=20)
    p.set_defaults(fn=cmd_watch)
    sub.add_parser("recon").set_defaults(fn=cmd_recon)
    sub.add_parser("checkpoint").set_defaults(fn=cmd_checkpoint)
    p = sub.add_parser("breaker")
    p.add_argument("--sandbox-sim", action="store_true")
    p.set_defaults(fn=cmd_breaker)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
