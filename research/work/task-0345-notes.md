# task-0345 notes — 移除 #8 activate 人工确认 + #13 legacy/override TTL

## 阶段0 定位（进行中）
- 2026-08-17 14:04 任务启动

## 阶段0 grep 定位结果（2026-08-17 14:04）
- 文件：HP ~/quant-evolve/scripts/evolution_pipeline.py，55157 bytes（严禁全读）
- #8 activate 人工确认相关行：
  - L64 STATUS_ENUM = ["candidate","pending","active","sota","retired"]（pending 状态本身保留？——pending 仅在 L778 使用，可考虑一并移除，但保守起见先看代码）
  - L778-779 reg["status"]="pending"; log "🚦 门禁 PASS → candidate → pending"
  - L790 expected_impact="PASS→pending 待人工确认后 activate"
  - L1122 注释：候选无回测产物，人工 backtest（这是回测，不是 activate 确认，保留）
  - L1136 log "— Step7 activate 为人工确认操作（本骨架不自动激活）"
- #13 legacy/override/TTL 相关行：
  - L6/12/16 文件头 usage 注释
  - L45 OVERRIDE_FILE
  - L491 "hash":"unknown-legacy"; L494 code_ref "legacy(...) bootstrap by task-0275"（bootstrap 描述，无害）
  - L508 verdict="legacy-grandfathered"（豁免类别判定）
  - L584-589 backtest --override key=val（参数覆盖，注意：这是 backtest 的临时参数覆盖，不是择时 override，需区分！）
  - L848-849 _do_activate 检查 verdict in ("PASS","legacy-grandfathered") and not force
  - L953-994 cmd_override 整段（TTL 临时覆盖择时开关）
  - L955-962 _parse_ttl
  - L1162 backtest --override 参数
  - L1183-1188 override 子命令 argparse
- 待确认：backtest 的 --override（L584/1162）是参数覆盖机制还是择时安全阀？R-220 #13 指"override --ttl 临时关闭择时安全阀"，即 cmd_override 子命令。backtest --override key=val 是别的功能（参数覆盖），任务书要求 grep 无 override 命中业务代码——但删 backtest --override 可能超出范围。需要看 R-220 原文确认。

## R-220 确认（14:05 已读 VPS 副本 8585B）
- #8 删除：activate 人工确认制→自动上岗，评分第一即自动 activate（不再人工拍板）
- #13 删除：legacy 豁免 + override TTL（非迭代评判标准）
- 保留：#9 rollback 快照、#10 locked、快照冻结、等价校验
- 本任务不动 #7 verdict 合成（task-0346）
