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

## 步骤3 model/ 注册表重置（19:31 完成）
- 历史 10 项全部归档至 model/archive-20260816/
- 注册 model/v0_seed.json：种子B参数 div≥2%/roe≥15%/roa≥10%/mv升序Top20/price_cap=10，上下文含全量池+cost v2+一字板+审计锁+五门禁
- decision-log.jsonl 重开，首行 D-20260816-SEEDB-RESET
- R-188 种子文档格式已参照（简洁 JSON 格式注册）

## 步骤4 VPS 镜像同步（19:33 完成）
- q4b 收口 11 文件 → /root/backups/q4b-closeout-20260816/（保留不删）
- 其余 174 项历史产物 → /root/backups/vps-results-archive-20260816/（移走归档，不删）
- 隐藏点文件（.check/.dircheck/.p3-3-status/.placeholder）为同步机制状态文件，保留
- VPS workspace-quant/results/ 现与 HP 清空后状态一致（HP 3 保留文件已在此镜像存在；HP 侧已删除的隐藏文件 VPS 侧保留无碍）
- 修正：VPS 镜像最初缺 3 个保留文件，已从 HP scp 补齐（R-188/factor-expansion-report.md/factor_catalog_v3.json），现与 HP 一致 ✓
