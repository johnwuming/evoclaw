#!/usr/bin/env python3
"""
gen_versions_manifest.py — 生成 versions-manifest.json（task-0329 看板去硬编码）

扫描 HP ~/quant-evolve：
  1. model/registry/*.json（版本注册表，含 backtest_refs 直接指向 results 回测文件）
  2. results/*_{full,locked}_metrics.json（回测指标文件）
  3. model/main.json（active 指针）

产出 results/versions-manifest.json：
  {
    "generated_at": "...",
    "active": "v2b_trr",
    "versions": [
      {
        "version_id": "v2b_trr",
        "strategy_prefix": "a2c_v2b_trr",     # 回测文件名前缀（不含 _{window}_）
        "status": "active|retired|pending|backtest-only",
        "strategy": "dividend_quality_smallcap_seedB",
        "registered_at": "...",
        "windows": {
          "full":   {"annual_return":..,"max_drawdown":..,"sharpe":..,"calmar":..,
                     "cumulative_return":..,"monthly_win_rate":..,"period_start":..,"period_end":..,"years":..},
          "locked": {...}
        },
        "files_note": "results/a2c_v2b_trr_{full,locked}_metrics.json"
      }, ...
    ]
  }

VPS 看板（server.js baseline/models API）消费此文件实现版本零硬编码。
用法：
  python3 gen_versions_manifest.py [--base ~/quant-evolve] [--out <path>]
仅标准库，无第三方依赖。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

METRICS_RE = re.compile(r"^(?P<prefix>.+)_(?P<window>full|locked)_metrics\.json$")
# 从文件前缀里切出版本号：a2c_v2b_trr → v2b_trr；a2b_v1i_q3z → v1i_q3z；a2_equivcheck → None（无 vX 段）
VERSION_RE = re.compile(r"^(?P<tool>[a-z][a-z0-9]*)_(?P<version>v\d.*)$")

# 保留进 windows 的指标字段（缺啥给 null，前端容错）
WINDOW_FIELDS = [
    "annual_return", "max_drawdown", "sharpe", "calmar",
    "cumulative_return", "monthly_win_rate",
    "period_start", "period_end", "years", "num_rebalance",
]

# 文件名里的裸版本 → registry 版本 id 别名（seedB_v0 对应 v0_seed）
VERSION_ALIAS = {"v0": "v0_seed"}


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [manifest] {msg}", file=sys.stderr)


def load_json(p: Path):
    try:
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        log(f"读取 {p.name} 失败（跳过）: {e}")
    return None


def read_metrics(results_dir: Path, prefix: str, window: str):
    p = results_dir / f"{prefix}_{window}_metrics.json"
    d = load_json(p)
    if not isinstance(d, dict):
        return None
    return {k: d.get(k) for k in WINDOW_FIELDS}


def prefix_from_backtest_refs(refs) -> str | None:
    """registry.backtest_refs.metrics_full = 'results/a2c_v2b_trr_locked_metrics.json' → 'a2c_v2b_trr'"""
    if not isinstance(refs, dict):
        return None
    for key in ("metrics_full", "endtoend", "baseline"):
        v = refs.get(key)
        if isinstance(v, str) and v:
            base = os.path.basename(v)
            m = METRICS_RE.match(base) or re.match(r"^(?P<prefix>.+)_(?:full|locked)_nav\.csv$", base)
            if m:
                return m.group("prefix")
    return None


def main():
    ap = argparse.ArgumentParser(description="生成 versions-manifest.json")
    ap.add_argument("--base", default=os.path.expanduser("~/quant-evolve"), help="项目根目录")
    ap.add_argument("--out", default=None, help="输出路径（默认 <base>/results/versions-manifest.json）")
    args = ap.parse_args()

    base = Path(args.base).expanduser().resolve()
    results_dir = base / "results"
    registry_dir = base / "model" / "registry"
    out_path = Path(args.out).expanduser() if args.out else results_dir / "versions-manifest.json"

    # active 指针（model/main.json）
    main_json = load_json(base / "model" / "main.json") or {}
    active = main_json.get("version") or main_json.get("model_version") or None

    versions: list[dict] = []
    seen_ids: set[str] = set()
    covered_prefixes: set[str] = set()

    # ① registry 为主源：零启发式取 prefix（backtest_refs 直接指路）
    if registry_dir.is_dir():
        for f in sorted(registry_dir.glob("*.json")):
            if ".snapshot" in f.name or f.name.endswith(".bak"):
                continue
            reg = load_json(f)
            if not isinstance(reg, dict):
                continue
            vid = reg.get("version_id") or f.stem
            status = reg.get("status") or "registered"
            sel = reg.get("selection") or {}
            prefix = prefix_from_backtest_refs(reg.get("backtest_refs"))
            if not prefix:
                # 兜底：文件名约定 <tool>_<version>_ 不存在时用 stem 探测 results/
                cand = [p for p in results_dir.glob(f"*_{vid}_full_metrics.json")]
                prefix = cand[0].name[: -len("_full_metrics.json")] if cand else None
            windows = {}
            if prefix:
                for w in ("full", "locked"):
                    m = read_metrics(results_dir, prefix, w)
                    if m is not None:
                        windows[w] = m
                covered_prefixes.add(prefix)
            files_note = (
                f"results/{prefix}_{{full,locked}}_metrics.json"
                if prefix and windows
                else ("registry only（无回测文件）" if not prefix else "回测 metrics 文件缺失")
            )
            versions.append({
                "version_id": vid,
                "strategy_prefix": prefix,
                "status": status,
                "strategy": sel.get("strategy") or reg.get("strategy") or None,
                "registered_at": reg.get("created_at") or reg.get("registered_at") or reg.get("activated_at") or None,
                "windows": windows,
                "files_note": files_note,
            })
            seen_ids.add(vid)

    # ② 兜底扫描：registry 未覆盖的回测文件（equivcheck / repro 等实验产物）
    if results_dir.is_dir():
        for f in sorted(results_dir.glob("*_metrics.json")):
            m = METRICS_RE.match(f.name)
            if not m:
                continue
            prefix, window = m.group("prefix"), m.group("window")
            if prefix in covered_prefixes:
                continue
            covered_prefixes.add(prefix)
            vm = VERSION_RE.match(prefix)
            raw_vid = vm.group("version") if vm else prefix
            vid = VERSION_ALIAS.get(raw_vid, raw_vid)
            windows = {window: read_metrics(results_dir, prefix, window)} if window else {}
            other = "locked" if window == "full" else "full"
            om = read_metrics(results_dir, prefix, other)
            if om is not None:
                windows[other] = om
            versions.append({
                "version_id": vid,
                "strategy_prefix": prefix,
                "status": "backtest-only",
                "strategy": None,
                "registered_at": None,
                "windows": windows,
                "files_note": f"results/{prefix}_{{full,locked}}_metrics.json（未注册 registry）",
            })
            seen_ids.add(vid)

    # 排序：active 最前，其余按 version_id 字典序
    versions.sort(key=lambda v: (0 if v["version_id"] == active else 1, v["version_id"]))

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "active": active,
        "versions": versions,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    n_active = sum(1 for v in versions if v["version_id"] == active)
    log(f"OK manifest → {out_path}（{len(versions)} 版本，active={active}"
        f"{'✓' if n_active else ' ⚠未见 active 版本'}）")
    print(json.dumps({"ok": True, "out": str(out_path), "versions": len(versions), "active": active}))


if __name__ == "__main__":
    main()
