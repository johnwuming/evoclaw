# R-244：ZeroTier 推链路丢 SYN 排查 + qfq 行情日更采集方案

- 任务号：task-0380（承接 task-0377 遗留项）
- 日期：2026-08-19
- 类型：研究型（只读排查 + 方案输出，生产文件 0 改动）
- 排查人：OpenClaw subagent（task-0380）

## 1. 背景与目标

task-0377（paper 逐股现价）验收后遗留两件事：

1. **ZeroTier 跨机推送偶发丢 SYN**：HP → VPS 的推送链路不稳定，怀疑 ZeroTier 隧道丢包；
2. **qfq 行情更新频率偏低**：目前实质上是"周更 + 手动补"，评估改为日更的采集方案。

目标：给出丢 SYN 根因（带日志证据链）+ qfq 日更方案（只出方案不实施）。

## 2. 方法与数据来源

- VPS：`zerotier-cli peers/listnetworks`、`ip addr/neigh`、`dmesg`、`/etc/ufw/user.rules`、`ss -tlnp`、`sshd_config`、systemctl 时间戳、ping 连通性测试
- NAS（只读）：docker 容器 `zerotier-zerotier-synology` 内 `zerotier-cli info/peers/listnetworks`
- HP：`crontab -l`、`~/quant-evolve/scripts/` 源码（refresh_data.py / collect_qfq_baostock.py / paper_engine.py / cron_paper_*.sh）、数据目录 `data/all_stocks_qfq/` 统计、`logs/refresh_data.log`
- 原始证据堆：`shared/results/work/task-0380-notes.md`

## 3. 核心发现（结论先行）

### 3.1 ZeroTier 隧道无责：丢 SYN 的真凶是 VPS 的 UFW 静默丢弃 + 三方配置错位

**一句话结论：SYN 没有丢在 ZeroTier 链路上，而是完好到达 VPS 后被 UFW 防火墙静默 DROP（无 RST 回包），HP 侧观测为"SYN 丢失"反复重传直至超时。**

证据链（每条可溯源）：

1. **隧道健康**：VPS `zerotier-cli peers` 全部 DIRECT（PLANET 156-232ms，LEAF 25-26ms），无 RELAY；`journalctl -u zerotier-one -72h` 无 warn/error；ping NAS .241 三包零丢（rtt 24-34ms）、ping HP .174 零丢（29-37ms）。NAS 侧（容器 Up 8 weeks）对 VPS 节点 DIRECT 26ms——双向直连健康。
2. **铁证（dmesg）**：环形缓冲（覆盖 8/18 19:26–8/19 19:44，约 24h）有 35 条
   `[UFW BLOCK] IN=ztfl6eg7ba SRC=10.12.192.174 DST=10.12.192.98 ... DPT=22 ... SYN`
   全部是 HP→VPS:22 的 SSH SYN；时间呈典型 TCP 指数退避重传（1,1,1,2,2,4,8s，每突发 9 包 = `tcp_syn_retries=6`），8/18 22:22、22:26、22:28 与 8/19 00:29 共约 6 次独立连接尝试全部被丢。证据落盘 `/tmp/ufw_zt.log`。
3. **UFW 规则**（`/etc/ufw/user.rules`）：全表无任何 `dport 22` 放行（eth0 也没有）；ZT 侧仅放行 `zt+→22222/tcp` 与 `ztfl6eg7ba→12145/tcp`；另有 8051/8052/8060/80/443/6080/12145 全接口放行。
4. **sshd 配置漂移**：`/etc/ssh/sshd_config` 为 `Port 22222`（2026-07-07 12:55 修改），但 sshd 服务 active since 2026-07-07 10:44（早于改配置 2 小时、从未 reload）→ 实际监听 `0.0.0.0:22`（`ss -tlnp`，pid 27194），**22222 端口无人监听**。UFW 为 22222 放的行成了空转。
5. **IP 文档陈旧**：TOOLS.md/任务书记载 VPS ZT IP=10.12.192.225，实际接口仅 **10.12.192.98/24**；.225 在网段内无人应答（ping 3/3 丢、`ip neigh` FAILED）。HP 三个脚本（`cron_paper_daily.sh`、`cron_paper_rebalance.sh`、`sync_to_vps.sh`）仍在 rsync 到 `root@10.12.192.225` → 这些路径 100% 失败，且与"偶发"观感叠加。
6. **推链路四路径画像**（HP scripts grep）：rsync→.225:22（死 IP，恒败）；rsync→.98:22（paper_engine.py，UFW 恒丢——即 dmesg 铁证）；HTTP→公网 82.156.124.186:8055（每分钟 metrics，正常）；openclaw node→.98:12145（heartbeat_selfheal，正常）。**"偶发"实为按路径分流：走 8055/12145 的活，走 SSH 的死。**

### 3.2 qfq 现状：名义周更、实质半停；数据已滞后 3 个交易日；补采脚本有截断隐患

1. **规模**：`~/quant-evolve/data/all_stocks_qfq/` 共 5448 个 parquet / 1.1G；其中 5206 个为消费者格式 `{code}_daily_qfq.parquet`（前复权日线，含 date/OHLC/volume/amount/outstanding_share/turnover），242 个为裸编号（akshare refresh_data.py 写入的残留，消费者不用）。
2. **更新链路两条并行且一死一残**：
   - `refresh_data.py`（akshare/东财源，cron 周日 20:00）：8/9–8/10 实际运行 6 小时+，5539 只中 **4714 只失败（85%，RemoteDisconnected）**（logs/cron_refresh.log 与 refresh_data.log）——外呼源实质失效；且它写裸编号文件名，与消费者 glob（`*_daily_qfq.parquet`）不匹配。
   - `collect_qfq_baostock.py`（2026-08-15 新增，baostock 源，前复权 adjustflag=2，原子替换写入消费者格式）：**无 cron，纯手动**，8/15 跑过一次。
3. **新鲜度**：抽样 600519（茅台）`_daily_qfq.parquet` 最新日期 **2026-08-14**（文件 mtime 8/15 17:04）；今天 8/19 → **滞后 3 个交易日**。信号链（paper_trade/rebalance/base_strategy，每日 16:30 cron）与 `all_stocks_merged.parquet`（304MB，8/11 重建，被 evolution_pipeline/backtest 消费）均在吃陈旧数据。
4. **补采脚本隐患**：`collect_qfq_baostock.py` 的 save() 是**整文件替换**、fetch 起点取 `--start`（默认 2005-01-01）；若以短窗口 `--start` 调用会**截断历史**——docstring 宣称的"增量尾部 + 因子跳变检测自动全量重拉"在代码里并未实现。改日更前必须先补 merge 逻辑，否则有数据事故风险。

## 4. 结论与建议（均不实施，待用户批准后另立任务）

### 4.1 推链路修复（优先级高，改动小）

| # | 动作 | 说明 |
|---|---|---|
| 1 | UFW 补一行放行（方案 A，零重启止血） | `ufw allow in on ztfl6eg7ba from 10.12.192.0/24 to any port 22 proto tcp`——立即恢复 HP→VPS rsync/SSH |
| 2 | 或让 sshd 真正切 22222（方案 B） | `systemctl restart ssh` 前需确认控制台兜底；切完后 HP 侧 rsync 加 `-p 22222`（UFW 已放行） |
| 3 | HP 三脚本 IP 收敛 | `.225` → `10.12.192.98`（cron_paper_daily.sh / cron_paper_rebalance.sh / sync_to_vps.sh） |
| 4 | 文档同步 | VPS/TOOLS.md 的 ZT IP .225 → .98 |
| 5 | 长期 | 推送统一走已验证通道（公网 8055 / ZT 12145）；加配置自检：sshd 实际监听端口 vs UFW 规则 vs 脚本目标三方对齐 |

注意：方案 B 单独执行会先断现有 :22 连接路径（UFW 未放 22 前重启 sshd 会把唯一的 SSH 入口挪到 22222，反而配合 UFW 现状"修复"了对齐性，但需防自身失联，务必保留控制台/网关兜底）。

### 4.2 qfq 日更方案（载体：扩展 collect_qfq_baostock.py）

- **改哪个脚本**：`collect_qfq_baostock.py` 新增 `--mode inc`（真增量 merge）：
  1. 读旧 parquet last date → 拉 `[last+1, today]` 尾窗 → concat+按日期去重排序 → 原子写回**合并后**整文件（根治截断隐患）；
  2. 衔接处跳变检测：新旧尾部 close 衔接比率异常（|Δ|>8% 且非当日涨跌停区间）→ 判定除权 → 该股自动全量重拉（2005→今）；
  3. 保留 `--mode init`（已有断点续传）做冷启动/周校验。
- **增量还是全量**：日常增量（尾窗 ≤10 个自然日）；全市场全量仅在冷启动、除权重拉、周日完整性校验时触发。
- **时刻与耗时**：建议每交易日 18:10（baostock 日线约 17:30–18:00 就绪；避开 16:30 paper cron 与 20:00 现有任务）。单股查询 ~0.2–0.4s + sleep 0.3 → **5206 股约 45–60 分钟**单线程、CPU/内存占用可忽略；可选两阶段：先持仓+HS300（~320 股，5 分钟内完成，先保 paper 链）再跑全市场。
- **外呼预算**：≈5210 次 query/日（baostock 免费、login 1 次/运行），无 token 成本；较现行 akshare 周更（单次 5539 次、85% 失败重试）总外呼量更低且成功率高。
- **失败兜底**：① 失败清单落盘，跑完后自动重试一轮；② 错误率 >10% 或 login 失败 → 经现有 metrics 通道（公网 8055）告警；③ 每周日保留一次 `init` 全量校验 + `rebuild_merged.py` 重建 merged 快照（evolution 消费者对齐）；④ 数据质量门：更新后抽查 N 股最新日期=交易日历最新交易日，不达标不上报"完成"。
- **实施边界**：需改 HP crontab 加一行（本任务约束不实施）；不改 evolution_pipeline.py / registry / paper_engine（日更只喂 data/all_stocks_qfq 原始层，不动消费代码）。
- **清理建议**：242 个裸编号残留 parquet 移入归档目录（避免 `*.parquet` 兜底 glob 误读双份）；禁用/移除 refresh_data.py 周日 cron 行（akshare 源已实质失效，留着只会产错误日志）。

## 5. 来源清单

| 证据 | 出处 |
|---|---|
| 35 条 UFW BLOCK SYN（HP→.98:22） | VPS `dmesg -T`（8/18 19:26–8/19 19:44 环形缓冲），落盘 `/tmp/ufw_zt.log` |
| UFW 无 22 放行 / zt+→22222 / zt→12145 | VPS `/etc/ufw/user.rules`（grep `^-A ufw-user-input`） |
| sshd 配置漂移（config=22222，实听 22） | VPS `/etc/ssh/sshd_config`（mtime 2026-07-07 12:55）vs `ss -tlnp`（:22, pid 27194）vs `systemctl show ssh -p ActiveEnterTimestamp`（2026-07-07 10:44） |
| VPS ZT 实际 IP .98 / .225 死地址 | VPS `zerotier-cli listnetworks`、`ip addr show ztfl6eg7ba`、`ip neigh`（.225 FAILED） |
| ZeroTier 双向健康 | VPS `zerotier-cli peers`、ping 丢包率 0%；NAS 容器 `zerotier-zerotier-synology` `peers`（对 VPS DIRECT 26ms） |
| HP 推送路径四条 | HP `grep -rE "10.12.192|82.156.124.186" ~/quant-evolve/scripts/`（cron_paper_*.sh、paper_engine.py、collect-metrics.sh、heartbeat_selfheal.sh） |
| akshare 周更 85% 失败 | HP `logs/cron_refresh.log` / `refresh_data.log`（2026-08-10 02:05:58 完成：5539 总/825 成功/4714 错误） |
| qfq 规模/新鲜度 | HP `ls | wc -l`（5448）、`du -sh`（1.1G）、600519 parquet 尾部日期 2026-08-14、mtime 8/15 17:04 |
| 消费者清单 | HP `grep -rl all_stocks_qfq scripts/`（base_strategy/paper_trade/rebalance*）；base_strategy L31 优先 `*_daily_qfq.parquet` |
| 补采脚本截断隐患 | HP `collect_qfq_baostock.py` 源码（save() 整文件替换，fetch 起点=--start 默认 2005-01-01，无 merge） |
