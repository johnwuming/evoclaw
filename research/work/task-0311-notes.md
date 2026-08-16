# task-0311 任务中心瘦身笔记

## 基线（2026-08-16 15:47）
- server.js: 11531 行 / 595778 字节
- 主 agent 确认：零 running 任务，死代码健在

## P0 孤儿文件
- [x] 15:48 dispatch.js → /root/backups/dispatch.js.task0311 (19238B, mv 成功)
- [x] 15:49 rm dispatch.log (17875509B=17.8MB) + dispatch.log.* + *.tmp
  - 未删 dispatch.js.bak-task0265-20260814（不在任务书范围，保留）
