#!/usr/bin/env python3
"""task-0598: 全库 R 报告编号唯一性校验脚本（可复跑）

扫描 /root/.openclaw/workspace/shared/results/ 下各 NN-* 分类目录的一级 .md 文件，
从文件名提取 R- 编号（含 R-NNNR-MMM 复合模式），输出碰撞列表。
退出码：0 = 零碰撞；1 = 存在碰撞。
"""
import os
import re
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # shared/results
if os.path.basename(BASE) != "results":
    BASE = "/root/.openclaw/workspace/shared/results"

# 文件名中的 R- 编号模式：
#   R-213-xxx        -> 213
#   R-342R-344-xxx   -> 342, 344（复合占用，视为违例）
PAT_COMPOSITE = re.compile(r"R-(\d{2,4})R-(\d{2,4})(?=[-_.]|$)")
PAT_SINGLE = re.compile(r"R-(\d{2,4})(?=[-_.]|\b)")


def extract_ids(filename: str):
    """返回 (ids, composite_hits)。ids 为文件名声称占用的编号列表。"""
    stem = os.path.splitext(filename)[0]
    ids = []
    composite = []
    m = PAT_COMPOSITE.search(stem)
    if m:
        composite = [m.group(1), m.group(2)]
        ids.extend(composite)
        # 复合模式之后可能还有独立号
        rest = stem[m.end():]
        ids.extend(PAT_SINGLE.findall(rest))
        return ids, composite
    ids.extend(PAT_SINGLE.findall(stem))
    return ids, []


def main():
    owners = defaultdict(list)   # rid -> [(category, filename)]
    composites = []              # (category, filename, ids)
    for d in sorted(os.listdir(BASE)):
        dpath = os.path.join(BASE, d)
        if not os.path.isdir(dpath) or not re.match(r"^\d{2}-", d):
            continue
        for f in sorted(os.listdir(dpath)):
            if not f.endswith(".md"):
                continue
            ids, comp = extract_ids(f)
            if comp:
                composites.append((d, f, ids))
            for rid in ids:
                owners[rid].append((d, f))

    collisions = {rid: v for rid, v in owners.items() if len(v) > 1}

    print("=" * 60)
    print(f"[check_rid_dup] 扫描目录: {BASE}")
    total = sum(len(v) for v in owners.values())
    print(f"扫描文件编号占用总数: {total}, 唯一编号数: {len(owners)}")
    print("-" * 60)
    if composites:
        print("复合命名变体（占用多号）:")
        for d, f, ids in composites:
            print(f"  {d}/{f}  -> 占用 {ids}")
        print("-" * 60)
    if collisions:
        print("发现碰撞:")
        for rid in sorted(collisions):
            print(f"  R-{rid}:")
            for d, f in collisions[rid]:
                print(f"    - {d}/{f}")
        print("-" * 60)
        print(f"RESULT: FAIL — {len(collisions)} 个编号存在碰撞")
        sys.exit(1)
    else:
        print("RESULT: PASS — 零碰撞")
        sys.exit(0)


if __name__ == "__main__":
    main()
