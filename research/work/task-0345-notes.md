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

## 已读代码段（14:06）
- evaluate 函数 L778-790：PASS→pending；L790 expected_impact="PASS→pending 待人工确认后 activate"
- _do_activate L847-943：L848-849 verdict in ("PASS","legacy-grandfathered") and not force → 拒绝；后续为激活主体逻辑（快照冻结/main重建/registry流转/decision_log），需保留
- cmd_override L967-999：L969-974 --clear 分支；L978-994 写 TTL 覆盖；L985 timing_off；decision_log L990-993
- _parse_ttl L955-963

## 补读（14:08 重试恢复）
- L584-590：backtest --override key=val 是"临时参数覆盖"（写入 sel_params），非择时安全阀——与 #13 的 override --ttl 是两回事
- L584-589 是 backtest 的参数覆盖循环
- 待查：调用方是否引用 --confirm/--override/--ttl/legacy/grandfather（a5/a7 runner、cron、paper_engine）

## 侦察完成（14:10 重试恢复）
- pending 全引用（evolution_pipeline.py）：仅 L64(enum)/L778-779(设置pending)/L790(注释文本)
- activate 子命令无 runner/cron 调用方（grep 空）→ 纯手动命令，可安全改造为自动
- cmd_status 显示 gate_verdict，无 pending 特判 → 不受影响
- temp_override.json 不存在（无残留覆盖文件）；paper_engine 读它，但本任务不碰 paper_engine（写侧 cmd_override 移除后文件不再产生，读侧自然失效，无需改）
- notify_hub.py 有 scan_pending（通知侧，非 evolution_pipeline 机制实现）→ 不改（超范围，仅记录）
- a2_registry_bootstrap.py L58 也有 legacy-grandfathered（一次性历史 bootstrap 脚本，已跑过）→ 不改（超范围，仅记录）

## 改动方案（对齐 R-220 #8/#13）
1. evaluate（L778-790）：PASS 且 prev==candidate → 直接 _do_activate（自动 activate），不再置 pending；L790 expected_impact 改"PASS→自动 activate"
2. _do_activate（L848-849）：verdict 白名单去掉 "legacy-grandfathered" → 仅 "PASS"（保留 force 供 rollback/演练）
3. 删除 cmd_override + _parse_ttl（L953-999 整段）+ OVERRIDE_FILE 常量（L45）+ override 子命令 argparse（L1183-1188）+ 文件头 usage 注释
4. bootstrap（L491/494/508）：去掉 legacy 标签（hash "unknown-legacy"→"unknown"；code_ref 去 legacy() 前缀；verdict "legacy-grandfathered"→改中性 + note 更新）
5. Step7 日志（L1136）：改"evaluate PASS 即自动 activate（R220 #8 移除人工确认）"
6. STATUS_ENUM：保留 "pending"（历史 pending 条目 9 个是存量数据，不迁移、不删枚举避免破坏展示）
7. backtest --override（L584/589/1162）：保留——是"参数覆盖"非 #13 择时安全阀，且 task-0340/0342 A8/A9 网格实验会用到；报告里明确说明
8. 不删 activate 子命令（rollback 也走 _do_activate；admin 保留）

## 编辑完成（14:14 重试恢复）— 全部改动已应用 + py_compile OK
改动清单：
1. 文件头：五操作→四操作；删 override usage 行；加 R220 注释
2. activate help：注明正常路径由 evaluate PASS 自动触发
3. 删 OVERRIDE_FILE 常量
4. evaluate：PASS→直接 _do_activate（自动 activate），不再置 pending；expected_impact 更新
5. _do_activate：verdict 白名单仅 "PASS"（force 保留 rollback/演练）
6. 删 cmd_override + _parse_ttl 整段
7. 删 override 子命令 argparse
8. bootstrap：hash unknown-legacy→unknown；code_ref 去 legacy() 前缀；verdict legacy-grandfathered→PASS（note 说明 R220 移除豁免）
9. Step7 日志：改"门禁 PASS 即自动 activate"

残留 grep 命中分类：
- 注释/文档：L8, L131, L508, L850 → 允许
- backtest --override（L583/585/588/1119）：参数覆盖（非 #13 择时安全阀），保留，报告中说明
- confirmed_by（L896/940）：switch_log 审计字段（非 #8 人工确认机制），保留

## HP 部署验证（14:17 重试恢复）
- evolution_pipeline.py 已推送 HP（53096 bytes），HP quant python py_compile OK
- 模块加载：_do_activate 保留(True)，cmd_override/OVERRIDE_FILE/_parse_ttl 均不存在(False)，STATUS_ENUM 保留 pending（历史数据兼容）
- 无 evolution/paper 进程在跑（pgrep 仅命中自身）
- 残留 grep 命中=仅注释 + backtest--override(参数覆盖) + confirmed_by(审计字段)，无 #8/#13 机制实现

## 沙箱等价校验通过（14:21）
- 用临时沙箱路径跑 _do_activate（模拟 evaluate PASS 自动 activate）：
  - rc=0；v_new status→active；activated_at 写入
  - 新快照 + 旧快照均冻结（.main.json.snapshot 生成）
  - decision-log 追加 type=activate
  - 旧 active→sota 流转正确
  - SANDBOX_OK
- 生产未动（沙箱 /tmp/evolve_sandbox_*，已 rmtree）

## 完成（14:23 重试恢复）
- decision-log 已追加并验证：D-20260817-R220-1 r220_remove task-0345 (R220 #8/#13 实施)
- 全部验收项：
  1. 残留 grep：仅注释 + backtest--override(参数覆盖,保留) + confirmed_by(审计字段) ✓
  2. 等价校验：沙箱 _do_activate 通过（自动 activate/快照冻结/decision-log/旧active→sota）✓
  3. py_compile OK（HP quant python）+ 备份存在（evolution_pipeline.py.bak-r220-20260817-1414）✓
  4. decision-log D-20260817-R220-1 追加 ✓
- #7 verdict 合成（g1-g6）未动：diff 中无 verdict 合成逻辑变更 ✓
- 备份路径：HP ~/quant-evolve/scripts/evolution_pipeline.py.bak-r220-20260817-1414 (55157B)
