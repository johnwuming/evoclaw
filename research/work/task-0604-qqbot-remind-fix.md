# task-0604 修复笔记（边查边写）

## 事实
- 目标文件：/root/.openclaw/extensions/qqbot/dist/tools-CeUI9pG-.js（18270 字节，可整读）
- bug：qqbot_remind add 动作向 Gateway 发 cron.add 时把参数包在 `job: {...}` 里；Gateway openclaw 2026.7.1-2 期望字段平铺在顶层

## 待查
- [ ] 定位 add 动作构造请求的代码段
- [ ] Gateway cron.add schema 字段对照
- [ ] 最小 diff 修复
- [ ] node --check 验证
