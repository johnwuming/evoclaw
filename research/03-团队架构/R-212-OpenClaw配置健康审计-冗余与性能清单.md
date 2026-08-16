# R-212 OpenClaw 配置健康审计：冗余与性能清理清单

> 任务：task-0290 | 审计时间：2026-08-16 10:45–11:20 | 数据源：/tmp/openclaw-audit/ 预采集 + 现场补充实测（全部只读）
> 编号说明：任务预留编号 R-203 已被 `05-量化投资/R-203-量化系统流程梳理与自动化改造设计.md` 占用（R-210/R-211 亦已占用），顺延为 **R-212**。

---

## 一、执行摘要（按风险等级排序）

**发现总计 19 项：高危 3 / 中危 7 / 低危 9。** 其中「确认冗余可安全清理」11 项，「疑似冗余需用户确认」8 项。

### 🔴 高危（3 项）

| # | 一句话概括 | 影响 |
|---|-----------|------|
| H1 | **task-monitor.sh 超时兜底自部署起 100% 失败**：root crontab 每 10 分钟执行，cron 环境 PATH 不含 nvm 的 node，`node: command not found` 累计 **5690 次**、日志 527KB 持续增长。AGENTS.md 声称"task-monitor.sh（超时兜底）保留"，实际该兜底**从未工作过**（5690 次 ÷ 6 次/时 ÷ 24 ≈ 39.5 天 = uptime 全程） | 功能失效 + 磁盘/日志垃圾 |
| H2 | **跨家目录依赖结构陷阱**：root 生产环境的 5 个关键组件实体都在 `/home/ubuntu/` 下——agent-dashboard 实体（521M，root 侧仅软链）、bill-editor 运行副本（146M + nginx 静态资源 alias 指向它）、metrics.db/tasks.db、evolving-claw-sync 的 evolving-claw-repo、dashboard 服务用的 ubuntu nvm node。**误删 ubuntu 家目录任意一块即断服务**；同时导致 3.9GB 旧安装数据无法回收 | 结构性风险 + 3.9GB 空间锁死 |
| H3 | **systemd journal 2.1GB 无上限**（`/var/log/journal`），磁盘已用 40G/59G（70%）。40 天积累 2.1G，年化 ~19GB，不加限制将吃满磁盘 | 磁盘耗尽风险 |

### 🟡 中危（7 项）

| # | 一句话概括 | 影响 |
|---|-----------|------|
| M1 | **HEARTBEAT.md 79KB/557 行**，每次心跳全量注入上下文：204 处 task- 引用、157 条 `- [x]` 已完成任务、"进行中任务跟踪"标题重复出现 5 次（多会话追加失控），含 RD-Agent v2–v6 全程排障史等已闭环内容 | 心跳决策变慢、上下文污染，估算每次心跳多注入 2–3 万 tokens |
| M2 | **metrics.db 272MB，其中 61% 是空闲碎片**：freelist 40551/66431 页（≈158MB），collect-metrics.sh 每分钟 DELETE 24h 前数据但从未 VACUUM，文件只增不减 | 磁盘浪费，且随时间继续膨胀 |
| M3 | **会话目录 846 个文件 557MB 无归档策略**：7/19–7/27 旧会话约 67 个文件仍在，trajectory.jsonl 单文件普遍 10MB（11 个 ≥10MB），另有 7.9MB `.usage-cost-cache.json` | 磁盘 + 会话列表查询变慢 |
| M4 | **/root/.openclaw/ 下 openclaw.json 备份文件 20 个堆积**（bak / bak.1–4 / bak-20260811 / bak-20260815 / bak-before-* 等，8/1–8/16 十天内产生） | 管理成本；自动备份机制（gateway 每次重启滚动）+ 手工备份无清理规则 |
| M5 | **ubuntu 侧旧 agent 会话 1.5GB 死数据**：`/home/ubuntu/.openclaw/agents/`（main 1.3G + research-lead 148M + research-searcher 30M + research-reviewer/citation 等），最后活动 8/1，此后全部流量在 root 侧 | 1.5GB 可回收（压缩归档后约省 70–80%） |
| M6 | **/root/.cache 可清缓存 530MB**：pip 399M + node-gyp 130M（另有 playwright 625M 是 chrome 依赖需保留） | 磁盘 |
| M7 | **telegram botToken 残留**：channel 已 `enabled:false` 但 botToken 明文仍在 openclaw.json；连同 4 个 provider apiKey、lightclawbot/qqbot 密钥集中存于单一 JSON（已有 chmod 600，但备份文件×20 同样含密钥） | 安全/管理成本 |

### 🟢 低危（9 项）

| # | 一句话概括 | 影响 |
|---|-----------|------|
| L1 | device-pair 插件配置残留（openclaw 官方 Config warnings 已提示：disabled but config present） | 启动警告噪音 |
| L2 | volcengine-agent-plan 内含 glm-5.2 / deepseek-v4-flash / deepseek-v4-pro，与 glmcode、deepseek provider 模型重复（疑为多通道容灾，属故意的可能性大）→ 需确认 | 配置冗余感 |
| L3 | `agents.defaults.models` 别名键大小写不一致：`glmcode/GLM-5.2`（大写）vs 实际模型 id `glm-5.2`（小写），6 个 GLM-5.x 别名可能匹配失效 → 需确认 | 潜在隐藏 bug |
| L4 | tasks.db 231 任务 229 done（2026-06-23 起累计），无归档机制；当前仅 1.4MB 不紧急 | 长期查询变慢 |
| L5 | agents-disabled-backup/quant-compute（2026-08-15 刚删）建议定保留期（如 30 天）后清理 | 管理成本 |
| L6 | backup_config.sh 每日备份正常工作（最新 8/16 03:00，大小与当前配置一致），但**备份文件名日期恒为 20260701**（格式化 bug），且脚本物理位置在 /home/ubuntu/.lighthouse/ | 管理成本 |
| L7 | 散落备份目录/文件：`tools/agent-dashboard.bak-20260801-194935`（2.8M）、`agents/main/agent/models.json.bak-add-glm53`；collect-metrics 每分钟采集频率对 24h 趋势图而言可用 */2 降一半写入 | 磁盘/管理 |
| L8 | HEARTBEAT.md Step 2 仍写"任务中心自动完成调度（dispatch.js + server.js）"，与 AGENTS.md v4（2026-08-15 dispatch 已停用）矛盾 | 文档误导后续会话 |
| L9 | tools/bill-editor 存在 root(143M) 与 ubuntu(146M) 双实体副本，服务与 nginx 均用 ubuntu 副本，root 副本 8/2 后未再更新 → 疑似冗余需确认 | 143MB + 混乱 |

### ✅ 审计确认正常项（不构成问题，防止误报）

- **openclaw 内部 cron：无 job，无残留**（`No cron jobs`，仅 device-pair 警告即 L1）
- crontab 3 条 /home/ubuntu 路径**均真实存在**（非死路径）：task-monitor.sh 失败根因是 node 而非路径缺失；backup_config.sh 的 `$HOME` 在 root cron 下解析为 /root，**实际备份的是新配置且成功**；collect-metrics.sh 经软链与 /root 副本为同一文件
- skills.entries 34 个 `enabled:false` 是内置技能的禁用清单，属正常管理方式，**不建议清理**
- pull-hp-metrics（*/2）、auto_sync_notify（*/30 + 每日全量）频率与其用途（Dashboard 趋势/量化同步通知）匹配，保留
- 系统资源：内存 2.0G/3.7G + swap 722M（偏紧但可控，主因 gateway 917MB + dsh 300MB + dashboard 200MB + chrome ~200MB）；load 0.73 正常；systemd timers 无异常（certbot 无证书空跑属 Ubuntu 默认，可卸载但非必须）

---

## 二、分类明细清单

### 2.1 主配置 /root/.openclaw/openclaw.json

| 编号 | 位置 | 现状证据（实测） | 影响 | 建议动作 | 风险 | 档位 |
|------|------|----------------|------|---------|------|------|
| L1 | `plugins.entries.device-pair` | openclaw 启动警告：`plugin disabled (not in allowlist) but config is present`（allow 列表无 device-pair，entries 残留 publicUrl 配置） | 启动警告噪音、管理成本 | 删除 `plugins.entries.device-pair` 整块（确认不配对 iOS/Android 节点后） | 低 | ✅ 确认可清理（需确认无配对设备在用） |
| L2 | `models.providers.volcengine-agent-plan.models` | 含 glm-5.2 / deepseek-v4-flash / deepseek-v4-pro，与 glmcode、deepseek provider 同名模型重复；volcengine-coding-plan 仅 1 个 deepseek-v4-flash 也与 deepseek provider 重复 | 若是多通道容灾（火山通道计费/限流独立）则合理；若闲置则徒增配置面 | 保留 fallback 链在用的 volcengine-coding-plan；询问用户 volcengine-agent-plan 7 个模型是否仍在切换使用，不用则删模型项 | 低 | ⚠️ 疑似冗余需确认 |
| L3 | `agents.defaults.models` | 17 个别名中 `glmcode/GLM-5.2`、`glmcode/GLM-5.1`、`glmcode/GLM-5-Turbo`、`glmcode/glm-4.x` 等用大写/旧命名，而 provider 实际 id 为小写 `glm-5.2`；仅 `glmcode/glm-5.3` 与 provider id 一致 | 大小写不一致的别名可能无法被 `/model` 引用命中（未实测 OpenClaw 匹配规则） | 用 `openclaw gateway config.schema` 或实测验证；无效别名统一改为小写 id | 低 | ⚠️ 疑似失效需确认 |
| M7 | `channels.telegram.botToken` | `enabled:false` 但 botToken `8794820238:AAG…` 明文残留；该 token 若 telegram 账号已弃用应吊销 | 安全（泄露面） | 确认弃用后删除整段 telegram 配置并去 @BotFather 吊销 token | 中 | ⚠️ 需确认 |
| — | `agents.list` | 仅 main 一个 agent，无 quant-compute/dev 团队残留 ✅；bindings 仅 weixin→main ✅；main.subagents.allowAgents=['claude'] 已清引用 ✅ | — | 无需动作（8/15 清理已到位） | — | ✅ 正常 |
| — | `skills.entries`（34 个 disabled） | 全部为官方内置技能的显式禁用记录 | 无 | 保留（这是防止内置技能自动加载的正确做法） | — | ✅ 正常 |

### 2.2 系统 crontab（root）

| 编号 | 位置 | 现状证据（实测） | 影响 | 建议动作 | 风险 | 档位 |
|------|------|----------------|------|---------|------|------|
| H1 | `*/10 … task-monitor.sh`（ubuntu 路径） | `/var/log/task-monitor.log` 527KB，`grep -c "command not found"` = **5690**；日志首行显示曾用 /root 路径同样失败。根因：cron PATH 无 `/root/.nvm/versions/node/v22.23.2/bin`（node 由 nvm 安装）。两份脚本内容 `diff` 完全相同 | **超时兜底完全失效**（任务卡死无人标记）+ 日志无限增长 | cron 行改为：`*/10 * * * * PATH=/root/.nvm/versions/node/v22.23.2/bin:$PATH /root/.openclaw/workspace/scripts/task-monitor.sh >> …`，并 `truncate -s 0 /var/log/task-monitor.log`；修复后验证一次成功运行 | 高 | ✅ 确认需修复 |
| — | `00 3 … backup_config.sh` | 脚本 SOURCE=`$HOME/.openclaw/openclaw.json`，root cron 下解析为 /root → 最新备份 8/16 03:00、14865B 与当前配置一致 ✅（非死路径，此前的担忧不成立） | 正常 | 保留；可顺手把脚本迁到 /root/.lighthouse/ 统一归属 | — | ✅ 正常 |
| L6 | 同上（backup_config.sh） | 备份文件名恒为 `*-20260701-auto.json`（8/16 产物仍叫 20260701），日期取值 bug | 排查回滚时易误判文件新旧 | 修复脚本内日期变量；bak 目录仅 256K 无需清理 | 低 | ✅ 确认 bug |
| — | `* * * * * collect-metrics.sh vps`（ubuntu 路径） | 路径存在（经软链与 /root 副本同文件）；写入正常（metrics 最新到当前分钟） | 正常 | 路径统一改 /root 软链路径即可（可选）；频率见 L7 | — | ✅ 正常 |
| — | `*/2 pull-hp-metrics.sh`、`*/30 + 0 3 auto_sync_notify.py` | 路径存在于 /root；HP 拉取与量化同步按设计运行（HEARTBEAT 8/16 记录 02:00 同步 31 文件正常） | 正常 | 保留 | — | ✅ 正常 |
| — | `*/5 stargate`（腾讯云） | 云厂商自带 | 无 | 保留 | — | ✅ 正常 |

### 2.3 会话堆积（/root/.openclaw/agents/main/sessions）

| 编号 | 位置 | 现状证据（实测） | 影响 | 建议动作 | 风险 | 档位 |
|------|------|----------------|------|---------|------|------|
| M3 | sessions 目录 | 846 文件 557MB；时间分布：7/19–7/27 约 67 文件（最旧），8/10–8/11 高峰 393 文件，8/16 仍有 47；`ls -laS` 前 11 名 trajectory.jsonl 均 ≈10.4MB；`.usage-cost-cache.json` 7.9MB | 磁盘增长（日均 ~14MB）+ 会话枚举变慢 | 分层归档：① 7 月份旧会话 trajectory.jsonl 打 gzip（预计省 60–70%）；② 30 天以上整会话移 `sessions-archive/`；③ 大 trajectory 上限问题如 OpenClaw 无配置项，可在归档脚本中处理。**清理前先 sessions_list 确认无活跃引用** | 中 | ⚠️ 归档策略需用户确认保留期 |

### 2.4 上下文注入体积（workspace 根）

| 编号 | 位置 | 现状证据（实测） | 影响 | 建议动作 | 风险 | 档位 |
|------|------|----------------|------|---------|------|------|
| M1 | HEARTBEAT.md | 79,299 字节 / 557 行；`grep -c "task-"`=204，`- [x]` 已完成=157，`## 🔄 进行中任务跟踪` 标题重复 5 次；尾部仍保留 8/12–8/16 的 RD-Agent v2–v6 排障全记录、task-0285/0286/0287/0288 已闭环详情 | 每 30 分钟心跳全量注入 ≈2–3 万 tokens（AGENTS.md 本要求"Keep it small to limit token burn"）；新旧指令混杂（如 stop-at-pending vs 直接 activate 两条"铁律"并存）易误导决策 | **瘦身四步**：① 保留 Step 0–2b 流程 + 活跃任务（≤5 条）+ 最近 3 天审核索引行；② 其余全部移 `memory/heartbeat-archive-20260816.md`；③ 修订 Step 2 文档（见 L8）；④ 加维护规则"归档区只留 5 条，心跳审核通过后即搬走"。目标 <10KB（-87%） | 中 | ✅ 确认可瘦身（归档不删除，零信息损失） |
| — | AGENTS.md 14.7K / TOOLS.md 4.9K / MEMORY.md 3.7K / SOUL.md 2.1K / USER.md 0.9K | 均在合理量级 | 无 | 不动 | — | ✅ 正常 |

### 2.5 任务中心（tasks.db）

| 编号 | 位置 | 现状证据（实测） | 影响 | 建议动作 | 风险 | 档位 |
|------|------|----------------|------|---------|------|------|
| L4 | tools/agent-dashboard/tasks.db | 231 任务（done 229 / pending 1 / running 1），2026-06-23 起按日累计；db 仅 1.4MB | 当前无性能问题；长期将拖慢列表查询与 Dashboard 渲染 | 加轻量归档：`INSERT INTO tasks_archive SELECT * FROM tasks WHERE status='done' AND updated_at < now-30d`（月度 cron），Dashboard 查询加状态过滤即可 | 低 | ✅ 建议采纳（非紧急） |

### 2.6 系统资源

| 编号 | 位置 | 现状证据（实测） | 影响 | 建议动作 | 风险 | 档位 |
|------|------|----------------|------|---------|------|------|
| H3 | /var/log/journal | `journalctl --disk-usage` = 2.0G；`du -sh /var/log` = 2.2G；磁盘 40G/59G（70%），余 18G | 40 天 2.1G → 年化 ~19G，将挤占 swap/数据空间 | `journalctl --vacuum-size=300M` 立即回收 ~1.8G；`/etc/systemd/journald.conf` 设 `SystemMaxUse=300M` + `SystemMaxFileSize=50M` 后 `systemctl restart systemd-journald` | 高 | ✅ 确认可执行 |
| M2 | tools/agent-dashboard/metrics.db | 272,101,376B；`system_metrics` 现存 641,373 行（时间窗 8/15 00:00–8/16 10:46，24h 滚动删除生效）；PRAGMA：freelist_count=40551 / page_count=66431 → **61% 空闲页（≈158MB）**从未归还 OS | 文件虚胖且随采集继续；du 把它算进 ubuntu 家目录，加剧 H2 回收难度 | 低峰期 `sqlite3 metrics.db 'VACUUM;'`（注意 VACUUM 需 2× 空间峰值，先确认磁盘余量）；长期：collect-metrics.sh 每日 1 次 `PRAGMA auto_vacuum` 或定期 VACUUM 任务 | 中 | ✅ 确认可执行 |
| M6 | /root/.cache | pip 399M + node-gyp 130M（playwright 625M 是 lighthouse-chromium 运行依赖，**不能删**；pnpm 154M 是包管理缓存，删了会重新下载） | 磁盘 | `pip cache purge`（+399M）；node-gyp 130M 可删（编译时自动重建） | 中 | ✅ 确认可执行 |
| — | 内存/负载 | 2.0G/3.7G used + swap 722M；load 0.73；大头：openclaw gateway 917MB(RSS 24%)、dsh-web 300MB、agent-dashboard 200MB、chrome(CDP) ~200MB、bill-editor/joke-workshop/jokehub 合计 ~370MB | 偏紧但稳定，swap 充足（10G） | 无需立即动作；若未来吃紧可评估 joke-workshop(71M node_modules)/jokehub 是否常驻必要 | — | ✅ 正常（观察） |

### 2.7 agents 目录与备份

| 编号 | 位置 | 现状证据（实测） | 影响 | 建议动作 | 风险 | 档位 |
|------|------|----------------|------|---------|------|------|
| H2-a | /home/ubuntu/.openclaw 全域 | **3.9GB**：npm 1.5G + agents 1.5G + workspace 702M + memory-tdai 98M + browser-session 36M + …；其中 **agent-dashboard 实体 521M（含 metrics.db 272M）被 root 侧软链依赖**、bill-editor 运行副本 146M（systemd WorkingDirectory + nginx alias 双指向）、evolving-claw-repo 11M（inotify 同步守护进程脚本源）、dashboard/bill 服务用 ubuntu 的 node v22.23.1 | ubuntu 家目录成了生产单点；3.9G 无法回收；两套 nvm/node 版本并存（root v22.23.2 / ubuntu v22.23.1）增加维护面 | **分两步**：① 近期：只回收确定死数据（M5 的 agents 1.5G + npm 1.5G，先 tar 归档到 /root/backups/ 再删）；② 中期规划：把 agent-dashboard、bill-editor 实体迁入 /root（迁移=copy→改 systemd WorkingDirectory/ExecStart + nginx alias→验证→删旧），软链反向过渡，彻底消除跨家目录依赖。**迁移期间勿动 ubuntu 家目录** | 高 | ⚠️ 结构迁移需用户排期确认；死数据回收可先做 |
| M5 | /home/ubuntu/.openclaw/agents | main 1.3G（sessions 最后活动 8/1）+ research-lead 148M（7/7）+ research-searcher 30M + reviewer/citation/opencode/gemini/codex 零头 | 1.5GB 死数据（root 侧已接管全部流量 15 天） | `tar czf /root/backups/ubuntu-agents-archive-20260816.tar.gz` 后删除原目录（约省 1.4G+，tar 后预计 <400M） | 中 | ✅ 确认可归档（research 系 agent 8/15 决策"未动"，归档可逆，恢复=tar 解开） |
| M4 | /root/.openclaw/openclaw.json.bak* | 20 个备份（bak、bak.1–.4 自动滚动、9 个手工命名），全部含明文密钥（600 权限） | 管理成本 + 密钥副本×20 | 保留最近 3 个（bak / bak.1 / bak-20260815），其余 tar 归档到 /root/backups/ 后删除 | 中 | ✅ 确认可归档 |
| L5 | /root/.openclaw/agents-disabled-backup/quant-compute | 2026-08-15 迁入（v4 架构决策产物） | 暂无 | 保留至 2026-09-15（30 天观察期）后随归档批次处理 | 低 | ✅ 按期处理 |
| L7 | 散落备份 | `tools/agent-dashboard.bak-20260801-194935`（2.8M，8/1 备份，dashboard 已稳定 15 天）、`agents/main/agent/models.json.bak-add-glm53`（3.2K，8/14） | 零散 | 均可移入 /root/backups/ 统一管理 | 低 | ✅ 确认可归档 |
| L9 | tools/bill-editor（root 副本） | root 实体 143M（mtime 8/2 13:31）vs ubuntu 运行副本 146M（systemd + nginx 均指向 ubuntu）；root 副本 14 天未更新 | 143MB 疑似废弃 + 版本混淆风险（改错副本不生效） | 与用户确认 root 副本是否有未部署改动（diff 两目录）；无 → 删 root 副本或改软链；有 → 明确哪个是 source of truth 再统一 | 低 | ⚠️ 需确认 |

### 2.8 openclaw 内部 cron

| 编号 | 位置 | 现状证据 | 影响 | 建议动作 | 风险 | 档位 |
|------|------|---------|------|---------|------|------|
| — | openclaw cron jobs | `No cron jobs`（仅 device-pair 警告，即 L1） | 无 | 无需动作 ✅ | — | ✅ 确认无残留 |

---

## 三、建议执行顺序（供主 agent 排期）

**第一批 · 立即可做（无需确认，收益 ~2.5GB + 修复 1 个失效功能）**
1. H1：修 task-monitor cron PATH + 清日志（10 分钟，恢复超时兜底）
2. H3：journal vacuum-size=300M + journald.conf 限制（+1.8G）
3. M6：pip cache purge + node-gyp 清理（+530M）
4. M2：metrics.db VACUUM（-158M，低峰执行）
5. L1：删 device-pair 配置块（需 gateway restart 生效）
6. M4：openclaw.json 备份归档至 /root/backups/

**第二批 · 归档类（信息零损失，+1.9GB 左右）**
7. M5：ubuntu 旧 agents tar 归档后删除（+1.4G）
8. M1：HEARTBEAT.md 瘦身 79KB→<10KB（历史移 memory/heartbeat-archive-20260816.md，顺带修 L8 文档）
9. M3：7 月旧会话 trajectory gzip / 归档（+~200M）
10. L7：散落备份统一进 /root/backups/

**第三批 · 需用户确认后执行**
11. L2/L3：volcengine 模型清单 + models 别名大小写核实
12. M7：telegram botToken 删除与吊销
13. L9：bill-editor root 副本去向
14. H2-b：agent-dashboard / bill-editor 实体迁 /root 的结构迁移（建议单独开任务，涉及 systemd+nginx+软链三处联动）
15. L4：tasks.db 月度归档机制
16. L5/L6：quant-compute 备份保留期、backup 日期 bug

**预期总收益**：磁盘回收约 **4.4GB**（40G/70% → ~36G/61%）；心跳上下文注入 -87%；恢复 1 个失效兜底功能；消除 5 处跨家目录生产依赖中的 3 处（剩余列入迁移规划）。

---

## 附录：关键实测命令与输出摘录（可复现）

```bash
# H1 证据
$ ls -la /var/log/task-monitor.log        # 527383 bytes
$ grep -c "command not found" /var/log/task-monitor.log   # 5690
$ head -1 /var/log/task-monitor.log       # task-monitor.sh: line 18: node: command not found
$ which node                              # /root/.nvm/versions/node/v22.23.2/bin/node（cron PATH 不含）

# H2/M5 证据
$ du -sh /home/ubuntu/.openclaw           # 3.9G
$ du -sh /home/ubuntu/.openclaw/agents/*  # main 1.3G / research-lead 148M / research-searcher 30M …
$ ls -la /root/.openclaw/workspace/tools/ | grep dashboard   # agent-dashboard -> /home/ubuntu/...（软链）
$ grep ExecStart /etc/systemd/system/agent-dashboard.service # /home/ubuntu/.nvm/.../node .../agent-dashboard/server.js
$ grep -n alias /etc/nginx/sites-enabled/bill-editor         # 静态资源 alias 指向 ubuntu 副本

# H3 证据
$ journalctl --disk-usage                 # 2.0G
$ df -h /                                 # 40G/59G 70%

# M2 证据（python3 sqlite3）
# system_metrics 行数 641,373，窗口 2026-08-15T00:00Z~2026-08-16T02:46Z（24h 滚动删除生效）
# freelist_count=40551, page_count=66431, page_size=4096 → 61% 空闲页 ≈158MB

# M1 证据
$ wc -c /root/.openclaw/workspace/HEARTBEAT.md   # 79299
$ grep -c "task-" HEARTBEAT.md                   # 204
$ grep -c "^- \[x\]" HEARTBEAT.md                # 157
$ grep -c "^## 🔄 进行中任务跟踪" HEARTBEAT.md    # 5（标题重复）

# M3 证据
$ ls /root/.openclaw/agents/main/sessions | wc -l 相关采集：846 文件 557M
$ ls -laS sessions | head -12                    # 11 个 trajectory.jsonl ≈10.4MB

# M4 证据
$ ls /root/.openclaw/openclaw.json.bak* | wc -l  # 20

# 正常项证据
$ ls /home/ubuntu/.openclaw/workspace/scripts/task-monitor.sh  # 存在（非死路径）
$ ls -lt /etc/lighthouse/openclaw/bak/auto/ | head -2          # 8/16 03:00 最新，14865B=当前配置大小
$ diff /home/ubuntu/.../task-monitor.sh /root/.../task-monitor.sh  # SAME
```

> 本报告全程只读审计，未修改任何配置/服务/数据文件。
