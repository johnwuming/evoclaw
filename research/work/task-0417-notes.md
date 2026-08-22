# task-0417 笔记 — 看板拉数脚本 SSH 密码硬编码修复

## 初步发现（16:12）

- 目标文件 pull-hp-metrics.sh（4558B）已全文读取。
- **当前版本无明文密码**。头部注释：2026-08-21 task-0434 重构时已改
  `HP_PASS="$(grep -E '^QUANT_SSH_PASSWORD=' /root/.openclaw/secrets.env ...)"`。
  task-0417 编号 < task-0434，登记在先；task-0434 顺带完成了本任务要求的改法（grep 抽取法，与任务书建议一致）。
- collect-metrics.sh（7731B）已全文读取：**无任何 SSH/密码/密钥内容**（仅本地采集 + curl POST 上报，无认证字段）。无需改动。

## 待核验清单

- [ ] secrets.env 存在 QUANT_SSH_PASSWORD（只查变量名，不打印值）
- [ ] agent-dashboard 目录内无其他明文密码残留（含 .bak）
- [ ] bash -n 两脚本
- [ ] grep 验收命令
- [ ] 手动执行 pull-hp-metrics.sh：rc=0、VPS metrics.db mtime/行数更新
