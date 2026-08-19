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
