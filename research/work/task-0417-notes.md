# task-0417 笔记 — 看板拉数脚本 SSH 密码硬编码修复

## 结论（最终）

**task-0417 要求的修改已由 task-0434（2026-08-21）提前完成，本次核验全部通过，无需改动任何文件。**

目标脚本现行实现正是任务书建议的方案：`HP_PASS="$(grep -E '^QUANT_SSH_PASSWORD=' /root/.openclaw/secrets.env ... | cut -d= -f2- | tr -d '"')"`，密码缺变量时安全退出（exit 0），错误日志还会把密码替换为 `***`（`ERR=${ERR//"$HP_PASS"/***}`）。

## 核验证据（按时间序）

### 1. 静态核验（16:12–16:14）
- pull-hp-metrics.sh（4558B）与 collect-metrics.sh（7731B）均 <30KB，已全文读取，确认无明文密码。
- secrets.env（chmod 600）含 `QUANT_SSH_PASSWORD` 变量 ✓（只查变量名未打印值）
- scripts/ 目录仅 3 个文件（两脚本 + log + watermark），无含密码备份。
- `bash -n` 两脚本均 SYNTAX-OK。
- 验收命令 `grep -c "PASS\|password" pull-hp-metrics.sh` = 6，逐行核对全部为变量引用或注释（L8 注释、L29/30/31/45/48 变量引用），无明文。
- collect-metrics.sh：`grep -c "sshpass|HP_PASS|QUANT_SSH"` = 0，无 SSH/密钥内容（纯本地采集 + curl 上报，无需改）。
- agent-dashboard 全目录扫描：server.js.bak* / docs 中的 `password` 均为 Web 登录表单代码（`b.password`、input 字段），非 SSH 秘密，不在范围。

### 2. 动态验证（16:14）
- sshpass 存在（/usr/bin/sshpass）；crontab 确认 */2 * * * * pull-hp-metrics.sh + * * * * * collect-metrics.sh vps。
- 手动执行 `bash scripts/pull-hp-metrics.sh` → **RC=0**
- VPS metrics.db（server='hp'）：行数 1935 → **1936**，max(timestamp) 2026-08-22T08:13:01Z → **08:14:01Z**（前进 1 分钟）
- watermark 文件推进：16:14:01 → 16:14:16 ✓
- 主库 mtime 未变属正常：库为 **WAL 模式**，写入落 `metrics.db-wal`（mtime 16:14 = 本次运行时刻），数据更新已由行数/时间戳证实。
- log 近期错误仅两条历史 scp 超时（10:46/11:08，端口 2222 用户态 sshd 短暂不可达），11:08 后 5 小时无错误，链路健康。

### 3. 范围外发现（已上报，未改动）

工作区扫描发现 2 个文件仍有**旧版明文密码**（格式 `sshpass -p '...123456'`）：
- `scripts/sync_timing_matrix.sh`（L10、L12）
- `shared/results/work/rdagent-fix-conda.sh`（L4，历史工作产物注释）

风险判定：两处密码**与现役 QUANT_SSH_PASSWORD 均不相同**（应为已轮换的旧密码）；均无 cron 活跃调用。按"不改无关文件"纪律未动，建议登记后续清理任务。

## 交付物
- 正式输出：无文件改动（核验型交付）
- 本笔记：/root/.openclaw/workspace/shared/results/work/task-0417-notes.md
