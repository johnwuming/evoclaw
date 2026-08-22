# task-0446 过程笔记：状态协议三处最小修复（R-276 落地）

## 0. 环境确认
- server.js：761,293B（禁全读）；spawn-task.md 6,306B；R-276 报告 11,434B（已全读 §四/§五）
- 服务：systemd `agent-dashboard.service`，active running，监听 127.0.0.1:8055（pid 3616939）
- 修复依据（报告 §五）：高-1=模板补 PUT 回写；高-2=PUT 白名单；中-1=session-key 翻转 spawn_owner+注释

## 1. 计划
1. 备份 server.js → /tmp/server.js.bak-task0446
2. 改前基线：全库 status 分布（只读）
3. 修复A：spawn-task.md 完成回报段补 PUT pending_review 协议行
4. 修复B：server.js :1051-1058 session-key SQL 加 spawn_owner='main'；:275-278 注释修正
5. 修复C：server.js :921-960 PUT handler 加状态白名单
6. node --check → 重启 → 验收（400/200/session-key 翻转/无扰动）

## 2. 定位与改动（边查边记）

（进行中）
