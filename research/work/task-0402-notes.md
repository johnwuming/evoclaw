# task-0402 过程笔记：qfq 日更采集实施 + ZeroTier UFW 放行

- 日期：2026-08-20 00:12–00:35（用户 00:06 批准推进）
- 方案来源：R-244 §4.1 方案 A（UFW 放行）+ §4.2（qfq 日更）
- 快照目录：`shared/results/work/task-0402-snapshots/`（ufw-before/after、hp-crontab-before/after）

## 1. UFW 放行（VPS 本机）✅

变更前：18 条规则，active，无任何 22 端口放行（与 R-244 证据一致）。

**新增（最小面：仅 ZT 接口 + ZT 网段 → 22）**：
```
/usr/sbin/ufw allow in on ztfl6eg7ba from 10.12.192.0/24 to any port 22 proto tcp
```
变更后：`[10] 22/tcp on ztfl6eg7ba  ALLOW IN  10.12.192.0/24`。公网 22 无新放行（公网暴露面不变）。

**连通实测**：HP → `ssh root@10.12.192.98` 返回 `HP_TO_VPS_SSH_OK / VM-0-11-ubuntu`（此前该路径 SYN 被 UFW 100% DROP，R-244 dmesg 35 条铁证）。

**回滚**：
```
/usr/sbin/ufw status numbered        # 找到 22/tcp on ztfl6eg7ba 的行号 N（当前为 10）
/usr/sbin/ufw delete N
```

## 2. qfq 日更实施（HP）✅

### 2.1 现状基线
- `collect_qfq_baostock.py` 已被 task-0373（8/19）升级：`--mode update` 真增量 + 重叠日除权跳变检测（|close比-1|>0.5% → 该股全量重拉）+ `--mode idx` 指数日更 + `--mode init` 断点续传全量。**增量内核无需重写**。
- 缺的是编排层 → 新增 `scripts/cron_qfq_daily.py`（5.8KB，未动既有脚本）：
  1. `--mode idx` 指数日更（hs300/zz500）
  2. 阶段1：持仓(paper-state.json holdings, 8只) + HS300(hs300_constituents.csv, 300只) 去重 ≈294 股，先保 paper 链
  3. 阶段2：全市场 5206 股 `--mode update`
  4. 每阶段失败清单（解析 `code: err:` 行）自动重试一轮
  5. 错误率>10%（含 baostock login 失败的典型表现）→ POST 公网 8055 任务中心建告警任务（通道实测可用；sourceSession=hp-quant-cron，进通知队列由主会话转述）
  6. 质量门：抽 600519+4 随机股尾部日期 vs 指数最新交易日，<80% 达标 → 告警
  - `--only-stage1` 参数供深夜/首跑验证

### 2.2 HP crontab 安装（25 行 → 31 行，+2 注释 +2 任务）
```
0 18 * * 1-5 ... python3 scripts/cron_qfq_daily.py >> logs/cron_qfq_daily.log 2>&1
0 18 * * 0 ... python3 scripts/collect_qfq_baostock.py --mode init >> logs/cron_qfq_sunday.log 2>&1; python3 scripts/rebuild_merged.py >> logs/cron_qfq_sunday.log 2>&1
```
- 日更 18:00 与 16:30 paper、17:10 a12、20:00 周任务错峰（R-244：baostock 17:30+ 就绪）
- 周日 init 为"断点续传校验"：文件尾部>=end 即跳过，只补滞后股（滞后则从 2005 全量根治），后接 rebuild_merged 重建 304MB 快照
- 既有 cron 行（16:30 paper ×3、20:00 refresh/validate、*/30 heartbeat 等）零改动；evolution_pipeline/paper_engine/registry 未动

**回滚**：`crontab ~/.../hp-crontab-before.txt`（快照在 VPS snapshots 目录 + HP /tmp/task0402-crontab-before.txt）；删除脚本：`rm ~/quant-evolve/scripts/cron_qfq_daily.py`（旧采集脚本有 .bak.20260819，未改）

### 2.3 首跑验证（--only-stage1，00:20）
```
IDX rc=0 zz500_daily_: already latest 2026-08-19
stage1 pool=294 (holdings+hs300)
STAGE1 rc=0 DONE codes=294 updated=0 latest=294 no_new=0 err=0 dur=2s
GATE ref=2026-08-19 fresh=5/5
exit code 0
```
- 294 股全 latest：task-0373 已于 8/19 拉齐数据（符合预期，upd/write 路径该任务已验证）
- 数据完好性：600519 尾部=2026-08-19；qfq 消费者格式文件 5206 个（数量不变）；all_stocks_merged.parquet mtime 仍 2026-08-11 01:46（未受任何影响）
- 告警通道实测：POST 8055 成功创建任务（task-0405 自检后已 reject 关闭）

## 3. 验收命令复现
```
# ① HP→VPS SSH 通
ssh noname@10.12.192.174 'ssh -o ConnectTimeout=8 root@10.12.192.98 hostname'   # → VM-0-11-ubuntu
# ② cron 行
ssh noname@10.12.192.174 'crontab -l | grep task-0402 -A1'                      # → 两行 0 18
# ③ UFW 规则
ufw status numbered | grep "22/tcp on ztfl6eg7ba"                               # → ALLOW IN 10.12.192.0/24
# ④ 手动首跑
ssh noname@10.12.192.174 '~/miniconda3/envs/quant/bin/python ~/quant-evolve/scripts/cron_qfq_daily.py --only-stage1'
```

## 4. 遗留/建议（不在本任务范围）
- HP 三脚本仍 rsync 到死 IP 10.12.192.225（R-244 §4.1 #3 IP 收敛，需另立任务）
- TOOLS.md 的 VPS ZT IP .225 → .98 文档同步（R-244 #4）
- refresh_data.py 周日 20:00 行（akshare 失效源）仍在跑，R-244 建议禁用——属既有 cron 行，本任务禁改未动
