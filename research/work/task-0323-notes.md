# task-0323 开发笔记（QTV4-P3 生命周期层）

## 任务
server.js 新增 `/api/quant/lifecycle` API + ⑥生命周期层 UI（决策时间线/实验台账/迭代轨迹散点/A2管线视图），挂在 btlc 页 P2 验证层之后、e2e 趋势图之前。

## 已确认事实
- server.js = 617998B（禁止全读，只能 grep/局部读）
- 备份已做：server.js.bak-task0323-20260816-220941
- 设计文档已读（R-214）：§1.5 ID 前缀体系（D-/IT-/V-/T-/F-）；§2 ⑥层四组件；§4 数据映射
- decision-log.jsonl 当前 1 条：D-20260816-SEEDB-RESET（注意：任务书写的是 D-20260816-Q4B-BC，实际文件里是 SEEDB-RESET；验收 curl 只要求含 "D-20260816" 相关字段——需确认验收命令 "含 D-20260816-Q4B-BC" 实际按文件当前内容渲染即可，API 是动态读文件，渲染实际存在的行）
  - 实际行字段：ts/decision_id/type/version/trigger/action/backup/params/...
- experiment-ledger.jsonl 当前 2 行：
  - 行1 ledger_reset（不编号）task=task-0317
  - 行2 baseline_v0_seed = IT-001，含 full{years:20.61,ann:0.2635,mdd:-0.6949,sharpe:0.9027,n_rebalance:248} / locked{...ann:0.2626...} / pool:fullpool+costv2+limitboard+auditlock / strategy:dividend_quality_smallcap_seedB
- ⚠️ 验收命令2写的是「含 D-20260816-Q4B-BC 与 IT-001」。decision-log 实际当前只有 D-20260816-SEEDB-BC... 不对，是 D-20260816-SEEDB-RESET。A2 可能中途追加。API 必须动态：curl 输出会包含文件里实际存在的 decision_id。IT-001 会有。D-20260816-Q4B-BC 不在文件里 → curl 无法包含它。解决：验收时以实际文件内容为准；如文件中途被 A2 追加了 Q4B-BC 则自然满足。若不满足，在完成回报中说明实际 decision_id 集合。

## 待探查（server.js）
- [ ] quant API 注册模式（P1/P2 的 /api/quant/* handler）
- [ ] fmtID / quantConceptBadge 函数位置与签名
- [ ] btlc 页 P2 验证层结束、e2e 趋势图开始的锚点
- [ ] Chart.js 本地化方式与已有图表初始化模式
- [ ] 口径切换器实现（full/locked）
- [ ] registry active 读取方式

## 进度日志
- 22:09 备份完成；设计文档/数据文件已读
