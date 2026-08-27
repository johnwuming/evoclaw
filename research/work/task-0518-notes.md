# task-0518 R-336 v1.1 修订笔记 (2026-08-28)

## 任务
按用户验收意见修订 R-336：P0×2（裁决三段式、风控层级下沉）、P1×3（backfill定义、状态机反向箭头、相关性监控并入4.4）、小修×3（paper_entered_at、G-L1周期定义、paper/canary串行三段式）。原地升级 v1.1，零代码。

## 定位结果（行号基于 v1.0，469 行）
- L52 总图⑦裁决优先级旧口径；L87 §1.2⑤ schema（risk_control 含 sleeve_ddc、paper_since）
- L93/L96 §1.2⑥ paper/canary/live 三档表述；L99-100 §1.2⑦ 职责（组合级>策略级）
- L137-140 §3.2 事件枚举（promotion.* 无降级事件）
- L196 §4.3 标题 canary/live 二选一读法；L200 G-L1 调仓周期无机器定义
- L209-212 §4.4 表（sleeve ddc 挂在组合层、两层关系旧口径、无相关性监控行）
- L288 §7.2 canary/live 表述
- L308-317 §7.5.3 裁决表第3/4行矛盾；L319-323 §7.5.4 相关性监控（需并入 §4.4 交叉引用）
- L439-467 附录 A GLOSSARY（canary/ddc 行需更新，需补 paper_entered_at/per_sleeve_risk_cap/backfill_rule 行）
- 无 G-B 类门禁命名 → 在 §1.2⑤ backfill_rule 定义处显式设立归属（正确性/无前视组）
- "组合级 > 策略级"旧口径仅 4 处：L52/L99/L212/L317，全部在修改计划内

## 修改方案
P0-1 → §7.5.3 整体重写为三段式（熔断硬上限>组合级>单腿级），同步 §1.1/§1.2⑦/§4.4
P0-2 → §1.2⑤ risk_control 只留组合级，sleeve_ddc 下沉 sleeve 版本对象，可选 per_sleeve_risk_cap；§4.4 行更新；GLOSSARY 补行
P1-1 → §1.2⑤ backfill_rule 显式定义+门禁归属
P1-2 → §1.2⑤ 状态机补 live→shadow / live→gated + §3.2 补 promotion.downgraded 事件
P1-3 → §4.4 加运行时相关性行（引用 §7.5.4 为定义出处），§7.5.4 加交叉引用
小修1 → paper_since→paper_entered_at + paper_duration（§1.2⑤ + GLOSSARY）
小修2 → G-L1 调仓周期机器定义（月频=1自然月，自进入状态首个调仓日起算）
小修3 → §4.3 标题/§1.2⑥/§7.2/GLOSSARY 全部改串行三段式表述
文档头 → 一句话版本后加修订记录表
