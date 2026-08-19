# task-0380 过程笔记（原始证据堆）

任务：① ZeroTier 推链路丢 SYN 根因排查 ② qfq 行情日更采集方案评估
日期：2026-08-19 | 类型：研究型（只读排查+方案，0 生产改动）

## T0 环境事实

- VPS 本机：VM-0-11-ubuntu，ZeroTier 服务 `zerotier-one.service` active running，cli 在 `/usr/sbin/zerotier-cli`（不在 PATH）
- 网络：a581878f7dc4f35d，VPS=10.12.192.225，NAS=10.12.192.241，HP=10.12.192.174

## 排查日志

（边查边记，以下按时间顺序追加）

## A. ZeroTier 排查结论（VPS 侧，2026-08-19 19:35-19:50）

### A1. 链路本身健康（排除 ZeroTier 丢包）
- `zerotier-cli peers`：4 PLANET 全 DIRECT（lat 156-232ms），2 LEAF DIRECT（58.212.197.84，即 HP/NAS 所在出口），controller 节点 DIRECT。无 RELAY。
- `ping 10.12.192.241`(NAS) 3/3 收包 0% loss，rtt 24-34ms；`ping 10.12.192.174`(HP) 2/2 收包，rtt 29-37ms
- `journalctl -u zerotier-one -72h` 非 notice/info 级别：0 条（无错误）
- 结论：ZeroTier 隧道无丢包证据。

### A2. 「丢 SYN」真凶 = VPS UFW 静默丢弃 ZT 入站 SYN（铁证）
- dmesg 环形缓冲（覆盖 8/18 19:26 → 8/19 19:44，约24h）：`[UFW BLOCK] IN=ztfl6eg7ba SRC=10.12.192.174 DST=10.12.192.98 DPT=22 ... SYN` 共 35 条
- 全部是 HP→VPS:22 的 SSH SYN；呈 TCP 指数退避重传（1,1,1,2,2,4,8s），每突发 9 个 SYN = tcp_syn_retries=6 典型特征
- 突发时间：8/18 22:22:11-31(SPT=43022)、22:26:22-33(SPT=35682)、22:28:15-22:29:34(多端口多次)、8/19 00:29:40-00:30:00(SPT=51628)，共约 6 次独立连接尝试全部失败
- 证据文件落盘：/tmp/ufw_zt.log（35 行）

### A3. 配置三方错位（根因）
1. `/etc/ssh/sshd_config`: `Port 22222`（2026-07-07 12:55 修改）
2. 但 sshd 服务 active since 2026-07-07 10:44（早于配置修改 2 小时，未 reload）→ 实际监听 0.0.0.0:22（ss -tlnp 证实 pid=27194），**22222 无进程监听**
3. UFW user.rules：放行 `-i zt+ --dport 22222`（为 ZT 的 SSH 放行）与 `-i ztfl6eg7ba --dport 12145`；**全表无任何 dport 22 放行规则**（eth0 也没有）
4. 结果：HP 以 .98:22 推送 → sshd 在监听但 UFW 先丢包 → 静默 drop 无 RST → HP 侧表现为「SYN 丢失/超时」

### A4. 文档 IP 陈旧问题
- TOOLS.md 记 VPS ZT IP=10.12.192.225；实际 `listnetworks`/`ip addr` 只有 **10.12.192.98/24**
- ping 10.12.192.255 网段内 .225：3/3 丢包，`ip neigh` 显示 .225 FAILED（无 ARP 应答，死地址）
- 若有脚本按文档用 .225 目标推送，则 100% 失败（比 UFW 丢包更彻底）
- VPS 网段内还有 .245/.199/.1 均 FAILED（无人认领），.46 STALE

### A5. 「偶发」的解释
- VPS 主动外连（VPS→HP/NAS）受 ESTABLISHED 回包放行 → 正常
- HP→VPS 新建入站 SSH（ZT, :22）→ 必失败；经公网 443 网关类推送 → 正常
- 推送走不同路径/不同端口时成败混合，观感即「偶发丢 SYN」

## B. NAS 侧只读排查（2026-08-19 19:55）
- 容器：`zerotier-zerotier-synology` Up 8 weeks（docker ps）
- `listnetworks`：a581878f7dc4f35d 状态 OK，NAS=10.12.192.241/24（另有第二网络 noname_nas 60ee7c034a482681 / 192.168.191.241）
- `peers`：全部 DIRECT；对 VPS 节点 c8012321a2 为 DIRECT 26ms（路径 82.156.124.186:9993）；对 HP（1cfed9bba2）DIRECT 4ms（LAN 192.168.3.138）→ NAS 与 HP 同局域网，NAS↔VPS 直连健康
- 结论：NAS 侧 ZeroTier 无异常，佐证「丢 SYN 不在隧道，在 VPS 主机防火墙」

## C. HP 推链路画像（grep scripts，2026-08-19 20:05）
HP→VPS 四条推送路径：
1. `cron_paper_daily.sh` / `cron_paper_rebalance.sh` / `sync_to_vps.sh`：`rsync → root@10.12.192.225` —— **陈旧 IP**（.225 死地址）→ 100% 失败
2. `paper_engine.py`：`VPS_RSYNC_TARGET=root@10.12.192.98:...`（rsync over SSH 22）→ **UFW 无 22 放行** → 静默丢 SYN（dmesg 35 条铁证）
3. `collect-metrics.sh`（每分钟）：HTTP → 公网 82.156.124.186:8055 → UFW 放行 8055 → 正常
4. `heartbeat_selfheal.sh`：openclaw node → 10.12.192.98:12145 → UFW 放行 zt 12145 → 正常
→ 「偶发不稳定」= 四条路径混用两种目标 IP 与四个端口，成功率取决于路径；ZeroTier 隧道本身无责。

## D. qfq 数据现状（HP，2026-08-19 20:00）
- 数据目录 `~/quant-evolve/data/all_stocks_qfq/`：5206 个 `{code}_daily_qfq.parquet`（消费者格式，共 1.1G）+ 242 个裸编号 parquet（akshare refresh_data.py 残留）
- 数据新鲜度：600519 最新日期 **2026-08-14**（文件 mtime 8/15 17:04），今天 8/19 → 滞后 3 个交易日
- 更新链路两条：
  a) `refresh_data.py`（akshare/EastMoney）cron `0 20 * * 0` 周日 20:00：8/9-8/10 运行 6h+，5539 只中 **4714 错误（85%）** RemoteDisconnected —— 源已实质失效；且写裸编号文件名，与消费者格式不一致
  b) `collect_qfq_baostock.py`（2026-08-15 新增，baostock 源）：写 `_daily_qfq.parquet` 原子替换、adjustflag=2 前复权、字段含 outstanding_share 反推；**无 cron，纯手动**，8/15 跑过一次
- 消费者：base_strategy.py(优先 `*_daily_qfq` glob)、paper_trade.py、rebalance*.py —— paper 信号链每天 16:30 依赖此数据；另有 all_stocks_merged.parquet（304MB，8/11 01:46）被 evolution_pipeline/backtest 消费，更陈旧
- `collect_qfq_baostock.py` 隐患：save() 为整文件替换且 fetch 起点取 --start（默认 2005-01-01）；若用短窗口 --start 调用会**截断历史**（无 merge 逻辑）；docstring 宣称的增量+跳变检测实际未实现
- baostock 计时参考：单股查询 ~0.2-0.4s + sleep 0.4s；5206 股全量(2005→今) ≈ 60-80 分钟
- HP cron 每分钟 metrics 推公网 8055 正常 → 日更任务日志/告警可复用该通道（不新增 ZT 依赖）

## E. 方案要点（报告取材）
### E1. ZeroTier 推链路修复（建议，不实施）
- 立即止血（二选一，需用户批准后另立任务执行）：
  A. `ufw allow in on ztfl6eg7ba from 10.12.192.0/24 to any port 22 proto tcp`（零重启，改一行规则即恢复 HP→VPS rsync）
  B. 让 sshd 真正切到 22222：`systemctl restart ssh`（需控制台兜底，防止失联）→ HP 侧 rsync 加 `-p 22222`（UFW 已放行 zt+→22222）
- 收敛 IP：HP 三个脚本 `root@10.12.192.225` → `10.12.192.98`；VPS/TOOLS.md 文档同步改
- 长期：推送统一走已验证通道（公网 8055 / ZT 12145），SSH-rsync 仅做批量同步，且目标端口与 UFW/sshd 三方对齐（加配置自检脚本：比对 sshd 监听端口 vs UFW 规则 vs 脚本目标）
### E2. qfq 日更方案（建议，不实施）
- 载体：扩展 collect_qfq_baostock.py 新增 `--mode inc`（真增量）：读旧文件 last date → 拉 [last+1, today] → concat 去重排序 → 原子写回整文件（修复截断隐患）；跳变检测：新尾部 close 与旧尾部衔接处比率 |Δ|>8% 且非涨跌停 → 该股全量重拉（除权导致 qfx 因子变化）
- 频率与时刻：每交易日 18:10（baostock 日线约 17:30-18:00 就绪；避开 16:30 paper cron 与 20:00 其他任务）
- 规模/耗时/预算：5206 股 × 1 次 query（窗口≤10日）+ sleep 0.3 → 约 45-60 分钟单线程；外呼 ≈ 5210 次/日（baostock 免费）；login 1 次
- 两阶段加速（可选）：先持仓+HS300（~320 股，5 分钟内）→ 再全市场
- 兜底：失败清单重试一轮；错误率>10% 或 login 失败 → 走 metrics 通道告警；每周日保留一次 init 全量校验 + rebuild_merged 重建 merged 快照；实施时需改 HP crontab 加一行（本任务不实施，另立任务）
