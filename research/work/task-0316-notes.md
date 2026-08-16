# task-0316 Q4b 第四棒 过程笔记（边查边写）

## 18:58 接手
- 前序：A组双区间已落盘（A_full 25.73%/-70%/0.913；A_locked 26.11%/-70%/0.907）；第三棒就绪件 build_delisted_panel.py + q4b_run_BC.py 已冒烟过
- 日志确认：`/tmp/q4b_collect_v2_full.log` 显示 293/293 采完，末行 `COLLECT_V2_DONE`，`logout success`，无致命错。data/fin_delisted 共 309 个文件（含索引）
- 采集健康：✅ 退市财务采集完成（步骤1过）

## 待办
1. ✅ 采集完成确认
2. ⏳ 重建全量退市 panel
3. ⏳ B/C 全区间回测
4. ⏳ 收口报告
5. ⏳ decision-log 入档
6. ⏳ VPS 镜像同步
