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

## 阶段0 基线核对（~10:10）
- a5_v4b_mve1_formal_locked_metrics.json（740B）确认：
  sort=gq, n_hold=20, cost_model=v2, limit_board=on, capital=1e7, dd_control=0
  period 2006-01-04~2024-06-28（18.48y, 222次调仓）
  **annual_return=0.1242 / max_drawdown=-0.2899 / sharpe=0.8401 / calmar=0.4285**
  → 与任务书 locked 口径 12.42%/-28.99%/0.840 完全一致 ✓
- A7 进程检查：ps 未见 a7/runner 进程（A7 批可能已结束或未起）；勿动其产物
- 复跑机制：/tmp/a5_runner.py（18KB）patch q4b_run_BC.py 的 run_backtest（ext 排序/权重/inv_vol/vt_target/dd_trigger/value-mom/gq 分支），base_cfg 注入 SEEDP
- 下一步：读 a5_runner main 流程 + base_cfg 复现 v4b_mve1 配置；设计现金注入方式
