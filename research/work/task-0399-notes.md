# task-0399 过程笔记（A15 风控组件对照批）

## 目标
在在役 a9_ranksum_raw 血统上验证：C1(n_hold=30) / C2(dd_control) / C3(叠加) / C4(dd阈值敏感性)，评分 v1.1 incumbent=a9_ranksum_raw；另产监控画像 monitor_signals/。

## 时间线
- 14:21 启动。报告编号确认：R-242 为现有最大 → 本批 R-243。

## 待核验点
- [ ] registry a9_ranksum_raw.json 内容（参数 schema）
- [ ] evolution_pipeline.py 的 score_composite 接口与调用方式
- [ ] breadth.parquet 字段
- [ ] 中证2000/沪深300/成交额在库情况
- [ ] 回测脚本调用方式（参考 a13 / task-0394 的跑法）
