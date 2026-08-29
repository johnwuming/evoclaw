# task-0564 工作笔记：8-29 qfq 收盘源入库后补跑 equity daily + mirror + recon + BFF 验证

- 开工时间：2026-08-29 20:44 (GMT+8)
- 背景：task-0556 发现 8-29 在役日更 cron 触发但当日 NAV 行未生成（qfq 收盘源未及时入库）。触发窗口今晚 20:30 后手动补跑。
- 纪律：HP 在役进程勿杀；禁改 crontab/registry/paper_engine/引擎文件/权威文件历史行；curl 截断；SSH 输出 ≤30 行；边查边写。

## 步骤 0：先例文档定位
