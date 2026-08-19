# task-0403 notes：A10 月度画像/IC 衰减监控接入 cron

- 开始时间：2026-08-20 00:12
- 目标：HP crontab 新增 a10 月度行 + 通知接入 + 手动触发验证

## 步骤进度
1. [ ] 读 a10 两个脚本，确认数据依赖与定时依据
2. [ ] 设计 cron 行
3. [ ] 通知 wrapper（参考 a12 notify 用法）
4. [ ] crontab 快照 + 追加安装 + 验证
5. [ ] 手动触发 a10_ic_decay_monitor.py 全链路验证
6. [ ] VPS 侧通知队列验证

