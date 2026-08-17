# task-0339 A7b 过程笔记（边查边写）
> 生成 2026-08-17 ~10:00 | 任务：v4b骨架现金曲线 + P0候选稳健性核验

## 访问路径（09:52-10:00 确立）
- HP SSH 10.12.192.174:22 **Connection refused**（多次重试均拒；task-0337/0338 同期同样被拒，疑 fail2ban/MaxStartups）
- 替代路径（沿用 task-0338）：**HP HTTP API http://10.12.192.174:8060 + X-API-Key**（key 在 VPS /root/.openclaw/workspace-quant/scripts/.hp-api-key，32字符）
  - /health OK：quant env 存在，merged 304MB，qfq 5448，disk free 31.7GB
  - /run 可执行（cwd=/home/noname/quant-evolve，env=quant，timeout 上限1800s）
- A7 产物现状：results/a7_ic_monthly.csv + a7_ic_summary.json（IC预检已完成，回测批进行中/未出）
- results/ 总数 552 文件

## 阶段0 基线
（待完成：复跑 v4b_mve1 locked 核对 12.42%/-28.99%/0.840；确认 A7 进程在但不动）
