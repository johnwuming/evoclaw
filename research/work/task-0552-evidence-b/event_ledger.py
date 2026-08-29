# -*- coding: utf-8 -*-
"""event_ledger.py — Iteration Ledger 事件账本 v1（R-342 §3.2 / R-336 §3.3 / 附录重放幂等伪代码）

规格要点（冻结条款）：
- append-only JSONL，一事件一行：{"seq","ts","actor","event_type","target","payload"}
- 写前 flock 互斥（LOCK_EX|LOCK_NB，获锁失败短重试+告警），每行写完 fsync
- 按月滚动文件：iteration-ledger-YYYY-MM.jsonl（按事件 ts 归月）
- seq 全局递增，幂等键：同 seq 重复追加 → 跳过；重放 seq 去重
- sha256 校验：各滚动文件摘要登记于 .ledger-sha256.json，verify() 比对
- actor ∈ {evolution_pipeline, user, risk_layer}

在役零改动：本模块只读写 portfolio/events/ 目录。
"""
from __future__ import annotations

import bisect
import datetime as dt
import fcntl
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

LEDGER_PREFIX = "iteration-ledger-"
LOCK_NAME = ".ledger.lock"
SHA_NAME = ".ledger-sha256.json"

ACTORS = {"evolution_pipeline", "user", "risk_layer"}


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class LedgerError(RuntimeError):
    pass


class EventLedger:
    def __init__(self, base_dir: str, retries: int = 3, retry_delay: float = 0.2):
        self.base_dir = base_dir
        self.lock_path = os.path.join(base_dir, LOCK_NAME)
        self.sha_path = os.path.join(base_dir, SHA_NAME)
        self.retries = retries
        self.retry_delay = retry_delay
        os.makedirs(base_dir, exist_ok=True)

    # ---------- 内部工具 ----------

    def _month_path(self, ts: dt.datetime) -> str:
        return os.path.join(self.base_dir, f"{LEDGER_PREFIX}{ts.strftime('%Y-%m')}.jsonl")

    def all_files(self) -> List[str]:
        if not os.path.isdir(self.base_dir):
            return []
        return sorted(
            os.path.join(self.base_dir, f)
            for f in os.listdir(self.base_dir)
            if f.startswith(LEDGER_PREFIX) and f.endswith(".jsonl")
        )

    def _acquire_exclusive(self):
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        for attempt in range(self.retries):
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fd
            except OSError:
                if attempt == self.retries - 1:
                    os.close(fd)
                    print(f"[ledger][warn] lock busy after {self.retries} retries: {self.lock_path}", file=sys.stderr)
                    raise LedgerError("ledger lock busy, append aborted")
                time.sleep(self.retry_delay)
        raise LedgerError("unreachable")

    @staticmethod
    def _release(fd: int):
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def _read_lines(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []
        out = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def _max_seq(self) -> int:
        mx = 0
        for p in self.all_files():
            for ev in self._read_lines(p):
                mx = max(mx, int(ev.get("seq", 0)))
        return mx

    def _existing_seqs(self) -> set:
        s = set()
        for p in self.all_files():
            for ev in self._read_lines(p):
                if "seq" in ev:
                    s.add(int(ev["seq"]))
        return s

    def _update_sha_registry(self, fd: int):
        reg: Dict[str, Any] = {}
        if os.path.exists(self.sha_path):
            with open(self.sha_path, "r", encoding="utf-8") as f:
                reg = json.load(f)
        for p in self.all_files():
            reg[os.path.basename(p)] = {"sha256": sha256_file(p), "size": os.path.getsize(p)}
        tmp = self.sha_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.sha_path)
        dfd = os.open(self.base_dir, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)

    # ---------- 追加（幂等） ----------

    def append(self, event_type: str, target: str, payload: Dict[str, Any],
               actor: str = "evolution_pipeline", ts: Optional[dt.datetime] = None,
               seq: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """追加一条事件。seq 已存在则跳过（幂等），返回 None；成功返回事件 dict。"""
        if actor not in ACTORS:
            raise LedgerError(f"actor must be one of {sorted(ACTORS)}, got {actor!r}")
        ts = ts or dt.datetime.now().astimezone()
        if isinstance(ts, dt.datetime) and ts.tzinfo is None:
            raise LedgerError("ts must be timezone-aware")

        fd = self._acquire_exclusive()
        try:
            existing = self._existing_seqs()
            if seq is None:
                seq = self._max_seq() + 1
            if seq in existing:
                return None  # 幂等：重复 seq 跳过
            ev = {
                "seq": int(seq),
                "ts": ts.isoformat(timespec="seconds"),
                "actor": actor,
                "event_type": event_type,
                "target": target,
                "payload": payload,
            }
            path = self._month_path(ts)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(ev, ensure_ascii=False, sort_keys=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            self._update_sha_registry(fd)
            return ev
        finally:
            self._release(fd)

    # ---------- 读取 / 校验 / 重放 ----------

    def read_all(self) -> List[Dict[str, Any]]:
        out = []
        for p in self.all_files():
            out.extend(self._read_lines(p))
        return out

    def verify(self) -> Dict[str, Any]:
        """对照 .ledger-sha256.json 校验各滚动文件完整性。"""
        if not os.path.exists(self.sha_path):
            return {"ok": True, "note": "no sha registry yet", "violations": []}
        with open(self.sha_path, "r", encoding="utf-8") as f:
            reg = json.load(f)
        violations = []
        for name, meta in reg.items():
            p = os.path.join(self.base_dir, name)
            if not os.path.exists(p):
                violations.append({"file": name, "reason": "missing"})
                continue
            cur = sha256_file(p)
            if cur != meta.get("sha256"):
                violations.append({"file": name, "reason": "sha256_mismatch",
                                   "expected": meta.get("sha256"), "actual": cur})
        for p in self.all_files():  # 未登记的新文件提示
            name = os.path.basename(p)
            if name not in reg:
                violations.append({"file": name, "reason": "not_in_registry"})
        return {"ok": len(violations) == 0, "violations": violations}

    def replay(self) -> Dict[str, Any]:
        """附录伪代码最小实现：seq 幂等去重后按序返回事件流与去重统计。"""
        seen = set()
        events = []
        skipped = 0
        for p in self.all_files():
            for i, ev in enumerate(self._read_lines(p)):
                key = ev.get("seq", f"{os.path.basename(p)}:{i}")
                if key in seen:
                    skipped += 1
                    continue
                seen.add(key)
                events.append(ev)
        events.sort(key=lambda e: (e.get("ts", ""), int(e.get("seq", 0)) if isinstance(e.get("seq"), int) else 0))
        return {"events": events, "skipped_duplicates": skipped, "count": len(events)}
