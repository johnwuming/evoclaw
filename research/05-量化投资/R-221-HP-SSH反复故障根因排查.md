# R-221 HP SSH 反复故障根因排查报告

- 日期：2026-08-17 15:32
- 触发：用户「ssh 之前也没有问题，彻底排查下原因和问题」
- 结论先行：**HP 存在系统性内存/硬件不稳定（多进程随机 SIGSEGV），SSH 会话进程崩溃级联拖垮 sshd 本体，叠加 systemd 半死导致无法自动拉起——不是 SSH 配置或网络问题**

## 一、故障时间线（2026-08-17）

| 时间 | 事件 |
|---|---|
| 01:09-01:12 | 系统 sshd（22）会话进程 SIGSEGV（signal 11），级联 `recv_rexec_state: ssh_msg_recv failed`，主 sshd 死亡；systemd 未拉起 |
| 01:11 | 最后一次成功登录（10.12.192.98） |
| 09:00-12:00 | 22 端口死透，cron-auto-sync 连续失败 7 次 |
| 12:25 | 用户指令修复 → 我经 HTTP API 启动用户态 sshd（2222，nohup） |
| 12:30-14:30 | 2222 正常使用（多次验收通过） |
| ~14:35 | 用户态 sshd 同样死于 `recv_rexec_state: ssh_msg_recv failed`（uhd.log 唯一一行） |
| 14:42+ | 2222 拒绝连接（本报告排查起点） |
| 15:32 | 经 HTTP API 重启用户态 sshd，2222 恢复（SSH_ALIVE 确认） |

## 二、关键证据链

1. **两个 sshd 死于同一错误**：系统 sshd 与用户态 sshd 的日志最后一行都是 `recv_rexec_state: ssh_msg_recv failed`——这是 sshd 父进程与 fork 出的会话进程通信失败，会话进程先 SIGSEGV。
2. **内核日志 segfault 风暴**（`journalctl -k`）：近几日逐日攀升——
   - 8/9: 2 次 | 8/10: 2 | 8/11: 5 | 8/12: 15 | 8/16: 48 | **8/17: 99**
   - 崩溃进程：python3.14、conda、dash、sh 等多个**不同二进制**，分布在 CPU 1/2/3
   - 纯 C 的 dash/sh 也崩 → 排除"某个 python 库坏"的单点解释
3. **systemd 半死**：`systemctl is-system-running` 超时（RC=124）；journald 反复报 `Failed to send WATCHDOG=1 notification: Transport endpoint is not connected`——systemd/dbus 自身不稳定，所以 sshd 死后无人拉起。
4. **排除项**：无 MCE/机器检查记录、无 EDAC 计数（Haswell 主板未暴露）、无 OOM（内存 15G 仅用 ~1.2G）、无磁盘 I/O 错误、swap 正常、磁盘 69% 用量。

## 三、根因判断

**HP 主机存在系统性硬件级不稳定**（最可能为内存故障/CPU 不稳），表现为多进程随机 SIGSEGV：
- 崩溃对象跨 python/dash/sh 多种二进制 → 不是单一软件损坏
- 崩溃计数逐日攀升（2→99）→ 渐进式退化，与纯软件 bug 不符
- 触发 sshd 死亡的是**会话子进程崩溃**，级联拖垮 sshd 主进程，而 systemd 半死无法自动重启 → 表现为"SSH 反复挂、重启后能撑一会儿又挂"

OpenSSH 10.2 的 PerSourcePenalties 把 10.12.192.98 标记 penalty 是**结果不是原因**——该源只是恰好在崩溃时段被连接。

## 四、建议处置

1. **短期**：SSH 通道已恢复（2222 用户态 sshd）。它可能再挂，挂了重跑 nohup 命令即可（命令在 TOOLS.md）。
2. **根本**：HP 在方便时**重启 + 内存自检**（memtest86+，i5-4590T 是 Haswell 非 ECC，若内存有坏块需换条）。重启会顺带清掉 systemd 半死状态。
3. **缓解**：考虑给 HP 加一个用户态 sshd 的心跳自愈（检测 2222 不在就重启）——需你同意后实施。
4. 已记录：A7 批 scipy ABI 间歇损坏、conda activate 损坏、多次瞬时段错误，均与本次同源（内存不稳定）。

## 五、来源
- HP journalctl（-k 内核日志、-u ssh、-p err）
- ~/.ssh/uhd.log（用户态 sshd 日志）
- journald WATCHDOG 报错、/proc/cpuinfo、free、df、ip neigh
