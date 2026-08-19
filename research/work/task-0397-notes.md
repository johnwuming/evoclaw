# task-0397 笔记：HP pipeline 修复 find_active glob 漏检 + status KeyError

目标文件：HP `~/quant-evolve/scripts/evolution_pipeline.py`（72300 bytes）
参考：VPS task-0392（dashboard 侧同类修复，正则 `^[a-z][a-z0-9._]*\.json$`）

## 复现记录（改前）

### Bug 1: registry_files 只 glob v*.json
- L181-183：`def registry_files(): return sorted(glob.glob(os.path.join(REGISTRY_DIR, "v*.json")))`
- registry 目录 61 个文件；非 v 的正式条目：`a12_s2_reb.json`(status=candidate)、`a9_ranksum_raw.json`(status=active)
- 复现命令：`python -c "import evolution_pipeline as ep; print(ep.find_active())"` 
  → `find_active (buggy) -> None | scanned 46 files`（a9_ranksum_raw 是唯一 active 却被漏检）
- 目录内另有备份文件 `a12_s2_reb.json.bak-task0384-20260819`、`a9_ranksum_raw.main.json.snapshot`，修复时不得误入扫描

### Bug 2: cmd_status 台账 e['type'] KeyError
- L1295：`log(f"📒 台账: ... (backtest {sum(1 for e in led if e['type']=='backtest')}) ...")`
- `results/experiment-ledger.jsonl` 95 行中有 2 行无 `type` 字段（用 `event` 字段：`ledger_reset`、`baseline_v0_seed`，task-0317 写入）
- 复现命令：`python scripts/evolution_pipeline.py status`
  → `KeyError: 'type'`（L1295），status 无法完成输出
- 同类风险：L1297 decision-log 行的 `e['decision_id']`、`e['type']` 也是直接下标（当前 69 行都有字段，防御性一并改 .get）

## 修复方案
1. registry_files：glob `v*.json` → listdir + 正则 `^[a-z][a-z0-9._]*\.json$`（镜像 task-0392；自动排除 .bak-*/.snapshot）
2. cmd_status：`e['type']` → `e.get('type')`；decision-log 行 `e['decision_id']`→`e.get('decision_id','?')`、`e['type']`→`e.get('type','?')`
3. 备份原文件 `evolution_pipeline.py.bak-task0397-*` 后再改

## 验证（改后）
（待填）
