# task-0346 过程笔记
开始时间：2026-08-17 14:36

## 阶段0 对比定位
（待填）
## 阶段0 对比定位完成（14:45）
- SSH 2222 被拒 → 用 HTTP API http://10.12.192.174:8060/run + X-API-Key（hp_api_server.py, 字段 command）
- diff -u 当前(cur, 53096B) vs 备份(bak, 55157B) → 10 hunks:
  1. 文件头(3-17): 四操作→五操作(override)；R220 note 行（当前特有）；activate 注释(#8保留)；override usage 行
  2. 常量(42): OVERRIDE_FILE 需恢复
  3. bootstrap(487): hash unknown→unknown-legacy, code_ref legacy() 前缀 —— #13 恢复
  4. bootstrap(504): verdict PASS→legacy-grandfathered, note —— #13 恢复
  5. evaluate(774): 当前=auto-activate(#8保留)；备份=pending 人工
  6. evaluate(789): expected_impact —— #8 保留当前
  7. activate(847): 当前=白名单仅PASS(#13删)；备份=("PASS","legacy-grandfathered") —— #13 恢复
  8. override cmd 块(953): 整段 cmd_override/_parse_ttl —— #13 恢复
  9. Step7(1090): 当前=自动activate(#8保留)
  10. argparse(1137): override 子命令 —— #13 恢复
## 阶段1 恢复执行（15:20）
- SSH 2222 被拒 → HTTP API /run + env:"raw" 跳过 conda 前缀（quant python 绝对路径可跑）
- 恢复脚本 /tmp/hp_restore13.py 执行成功：
  - 备份已建：evolution_pipeline.py.bak-r220fix-20260817-065116
  - 注入结果：cmd_override=1, _parse_ttl=1, OVERRIDE_FILE=5, legacy-grandfathered=2, unknown-legacy=1, pending_assign=0(#8保留), auto_activate_log=1(#8保留)
  - ⚠️ py_compile 失败：line 956 游离 `-`（R6 提取 block 时 bak[si-2:ei] 多取一个字符）
  - 当前 grep：957:# cmd: override / 959:def _parse_ttl / 971:def cmd_override / 1003:# cmd: status / 1005:def cmd_status —— 结构正确，仅游离符需修
- 修复游离 `-`：line 956 单独 `-` 行（R6 提取 si-2 误取），删除即可
## 阶段1 修复完成（15:30）
- 游离 `-` 已删除，py_compile OK（55603B）
- 白名单: L852 `if verdict not in ("PASS","legacy-grandfathered") and not force:` ✓
- bootstrap: L492 unknown-legacy / L495 code_ref legacy() / L509 verdict legacy-grandfathered ✓
- argparse: L1186 add_parser("override") ✓
- cmd_status 仅 1 处（无重复注入）✓
- 验收: A1=11(≥3) ✓ A2=pending仅1(STATUS_ENUM常量,无pending→人工) ✓ A3=备份存在 ✓ A4=PYCOMPILE_OK ✓
- A5 #12: 25%/-20%/1.2 在 pipeline 无命中（仅版本号v1.2、n_hold=25参数、数据文件名）→ 确认无需代码改动 ✓

## 阶段2 等价校验
（待填）
## 阶段2 等价校验完成（15:35）
- CLI status 干跑：registry 正常输出（v0_seed gate_verdict=legacy-grandfathered）✓
- 单测：_parse_ttl 24h/30m/7d 均 True（初测 "30m:0.5h" 系测试脚本期望值笔误，非代码问题）✓
- 白名单谓词：legacy-grandfathered/PASS 放行、REJECT 拒绝、force 放行 ✓
- OVERRIDE_FILE 常量存在、cmd_override/cmd_status 可调用 ✓
- 无意外写 MODEL_DIR 文件 ✓
- 无正在运行的 activate/cycle 进程 ✓
## 阶段3 收尾
（待填：decision-log / 完成回报）
## 阶段3 收尾完成（15:40）
- decision-log 已追加：D-20260817-006 type=r220_restore_13（~quant-evolve/model/decision-log.jsonl）
- 最终验收：
  - F1=11(≥3) ✓ #13 恢复
  - F2=PYCOMPILE_OK ✓
  - F3=无 reg["status"]="pending" ✓ #8 保留（evaluate 无人工确认制）
  - F4=L780 门禁 PASS→自动 activate ✓ #8 保留
  - F5=r220_restore_13=1 ✓ decision-log 已追加
- 文件最终状态：55603B；备份 evolution_pipeline.py.bak-r220fix-20260817-065116（53096B 恢复前状态）+ 原始 .bak-r220-20260817-1414
## 结论
task-0346 完成：#13（legacy 豁免 + override TTL）已从备份恢复，#8（自动 activate）保留未回退，#12 确认无需代码改动。等价校验（parse_ttl/白名单/status 干跑/无意外写入）通过。
