# task-0587 过程笔记（R-344 PRD 43 模块表刷新 + 两条裁定落款）

## 一、今日实况核验（2026-08-30 15:4x 实测）

1. policy-lint：`node scripts/policy-lint.mjs` → **PASS metrics-display-policy@v1，四项全过**（引擎层禁令/口径标注/ablation 禁令/硬编码禁令）。
2. `GET /api/v1/overview`：`active_pv=vC-0 status=paper`；sleeves 权重 equity_sleeve=0.5803 / hedge_sleeve_gold=0.4197；`reconciliation_ok=true`；nav=null 但接口不再断供（0586 修复生效，null 容错返回完整结构）。→ B3 已修 ✓
3. `GET /api/v1/portfolios/vC-0/holdings`：items 带 `sleeve` 字段（000848 → equity_sleeve 等）。→ B2 已修 ✓
4. `grep -c "risk_control\|gate_report\|组合构建" Version.jsx` → **12 命中**。→ B1/B2/B3 批后风控配置/门禁成绩单/组合构建区块在场 ✓

## 二、文件定位

- 目标文件 33387 bytes（>30KB，禁全读）。
- 模块对照附录：L308 起标题 `## 附：模块对照表（v1.3 收编 R-359 §2）`，快照 2026-08-29。
- 修订记录：L363 附近，最新条目 v1.3（2026-08-30，task-0570）。

## 三、逐行改动清单（边查边写）

（待模块表逐行核对后填写）

## 四、修订记录与 README

（待完成）
