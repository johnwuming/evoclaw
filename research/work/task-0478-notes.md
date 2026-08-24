# task-0478 notes — csad 独立引擎 E2 回测 + 与在役 a13 结合收益分析
时间戳: 2026-08-24 13:28 GMT+8 (start)

## 0. 任务书要点
- 目标: csad 独立引擎真实 NAV 回测 + 与在役 a13 组合收益实测 (R-297)
- 数据: HP ~/quant-evolve/, python=/home/noname/miniconda3/envs/quant/bin/python
- 关键: 预注册先写后算(机器锁 JSON+sha256 落盘时间<首跑), 判门数字全部来自 e2_results.json
- 零引擎/registry/paper_engine/HP crontab 改动

## 1. 执行日志 (append)
