# task-0317 种子B重置执行笔记
- 开始时间: 2026-08-16 19:22 GMT+8
- 序列: 备份→清空→注册种子→种子B基线


## 步骤0 预检（19:25）
- HP results/ 37M（603 项）、model/ 188K（10 项）
- 备份保留清单（步骤2 用）：
  1. R-188-quant-evolve-Phase1-小市值基准策略回测.md
  2. factor-expansion-report.md
  3. factor_catalog_v3.json
- model/ 含 decision-log.jsonl、factor_pool.json、history.jsonl、main.json、pending.json、rejected_last.json、sota.json、switch_log.jsonl、candidates/、registry/
- experiment-ledger.jsonl 位于 ~/quant-evolve/results/experiment-ledger.jsonl

## 步骤1 tar 备份（19:26 完成）
- HP 打包: /tmp/quant-results-model-20260816.tar.gz, 9.9M, 729 条目（603 results 项 + model/ 子项，目录条目也计入，合理）
- md5: b2e1d572ee6477acadb7a24f5b5687db
- 大小 9.9M << 500MB，可 scp 回 VPS
- scp 回 VPS: /root/backups/quant-results-model-20260816.tar.gz (9.9M), md5 一致 ✓
- HP 同步留档: ~/quant-backups/quant-results-model-20260816.tar.gz, md5 一致 ✓
- 三处副本（VPS /root/backups、HP ~/quant-backups、HP /tmp）校验完成，备份验证通过，可执行破坏性操作

## 步骤2 清空 HP results/（19:28 完成）
- 保留 3 文件确认存在后删除其余 600 项（清单存 HP /tmp/results-to-delete-20260816.txt）
- 结果: results/ 仅剩 R-188 种子文档、factor-expansion-report.md、factor_catalog_v3.json ✓
