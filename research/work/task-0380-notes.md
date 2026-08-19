# task-0380 过程笔记（原始证据堆）

任务：① ZeroTier 推链路丢 SYN 根因排查 ② qfq 行情日更采集方案评估
日期：2026-08-19 | 类型：研究型（只读排查+方案，0 生产改动）

## T0 环境事实

- VPS 本机：VM-0-11-ubuntu，ZeroTier 服务 `zerotier-one.service` active running，cli 在 `/usr/sbin/zerotier-cli`（不在 PATH）
- 网络：a581878f7dc4f35d，VPS=10.12.192.225，NAS=10.12.192.241，HP=10.12.192.174

## 排查日志

（边查边记，以下按时间顺序追加）
