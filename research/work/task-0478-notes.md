# task-0478 notes — csad 独立引擎 E2 回测 + 与在役 a13 结合收益分析
时间戳: 2026-08-24 13:28 GMT+8 (start)

## 0. 任务书要点
- 目标: csad 独立引擎真实 NAV 回测 + 与在役 a13 组合收益实测 (R-297)
- 数据: HP ~/quant-evolve/, python=/home/noname/miniconda3/envs/quant/bin/python
- 关键: 预注册先写后算(机器锁 JSON+sha256 落盘时间<首跑), 判门数字全部来自 e2_results.json
- 零引擎/registry/paper_engine/HP crontab 改动

## 1. 执行日志 (append)

## 2. 探测记录 (2026-08-24 13:30)
- HP 连接 OK (10.12.192.174, QUANT_SSH_PASSWORD)
- a13_rsraw_e1f10dz_full_nav.csv: date,nav,num_held, 5009 行 (2006-01-04 起, 日频)
- csad_resid_monthly.csv: ym,code,resid_z, 596523 行, md5 416019cf5368bde27c289949069f6193 ✓ (与任务书一致)
- r263 脚本目录 scripts_r263 未在 results/work/r263/ 下找到, 需确认位置 (VPS 镜像 work/r263/scripts_r263/)
