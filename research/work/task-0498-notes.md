# task-0498 / R-320 过程笔记（量化系统与 Dashboard 抽象合并精简方案）

> 边查边写：每完成一个取证点立即追加。恢复点文件。

## 时间线
- 2026-08-27 01:10 任务启动

## 0. 基础事实
- server.js: 825KB / 14942 行（任务书给定，待复核）
- 目标：纯方案设计，零代码改动
- 交付：R-320 报告 + 本笔记 + README 更新日志

## 取证计划
1. server.js API 端点全量提取（grep app.get/app.post）
2. 前端调用对照（grep fetch/axios 调用模式）
3. deprecated/legacy 标记定位
4. paper 双端点验证
5. 前端量化Tab 模块结构
6. HP 主机脚本与 crontab 清单（SSH 只读）
