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
