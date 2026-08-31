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

# 声称占用口径（task-0598 定性）：
#   1) 文件名首个 R-号；
#   2) 无分隔复合模式 R-NNNR-MMM（紧邻，中间无破折号）也算声称占用；
#   3) 其后破折号分隔的 R-号（如 R-290-…-按-R-256-R-259-…）为描述性引用，不占号。
PAT_COMPOSITE = re.compile(r"R-(\d{2,4})R-(\d{2,4})(?=[-_.]|$)")
PAT_SINGLE = re.compile(r"R-(\d{2,4})(?=[-_.]|\b)")


def extract_ids(filename: str):
    """返回 (claimed_ids, composite_hits)。claimed_ids 为该文件声称占用的编号。"""
    stem = os.path.splitext(filename)[0]
    m = PAT_COMPOSITE.search(stem)
    if m:
        # 复合模式：占用其中两号；若首个 R-号在复合段之前且不同，也占用
        ids = [m.group(1), m.group(2)]
        head = stem[: m.start()]
        heads = PAT_SINGLE.findall(head)
        if heads and heads[0] not in ids:
            ids.insert(0, heads[0])
        return ids, [m.group(1), m.group(2)]
    all_ids = PAT_SINGLE.findall(stem)
    # 只取第一个作为声称占用
    return ([all_ids[0]] if all_ids else []), []


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
