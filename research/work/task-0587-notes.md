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

## 三、逐行改动清单（PRD，已全部落地）

| 行 | 改动 | 依据 |
|---|---|---|
| 附录导语 | 快照日期更新为 2026-08-30；标注增补 2 行共 45 行；未复测行沿用 08-29 原状 | task-0587 实测 |
| 净值曲线（总览） | ❌ 保留但注明 0586 断供已修、根因改 R-377 口径判定待 B8 | overview 实测 nav=null+active_pv 在场；R-377 判定 |
| 当前回撤（总览） | 注明 0830 复测仍 null | overview drawdown_pct=null |
| 在役版本卡（总览） | 权重更新 58.03/41.97+0580 契约 v2.1 核验注记 | overview sleeves 实测 |
| 引擎卡（总览） | 🟡→✅ 按 11:10 禁令收敛：IC/ICIR 裁定不上单引擎；行名同步去掉 IC/ICIR | policy-lint ①PASS+task-0583 |
| 门禁成绩单（版本） | 🟡→✅ 0578 补区块渲染；vC-0 未评级保留 | Version.jsx grep 命中 gate_report |
| 详情·风险控制配置（版本） | ❌→✅ 0578 补渲染 | Version.jsx grep 命中 risk_control |
| 新增行：候选库视图（子页面） | ✅ 0572/0573/0582；ablation 降级 policy-lint ③PASS | App.jsx #/candidates 不占 Tab |
| 新增行：双腿持仓卡（版本） | ✅ 0575；holdings sleeve 字段 0580 | /holdings 实测+Version.jsx |
| 未动的行 | 沿用 08-29 快照原状（风控 Tab 数据源缺口/迁移投影等均非本批范围） | 导语已注明 |

## 四、裁定落款位置

- 三层定义：§3 区块③末尾新增 bullet（组合构建层/组合层/风控层+不得窄化「双腿持仓」）。
- 单引擎指标禁令：§3 区块②「关键信息」后新增修订 bullet（裁撤 IC/ICIR 接入+policy 编译化 task-0583）。
- 两条均在修订记录 v1.4 完整落款；README 顶部更新日志同批加一行。

## 五、验证（已跑）

- wc -c：37375（原 33387，+3988B <8KB 增幅合理）✓
- grep -c "2026-08-30"=5（≥4）✓；grep -c "单引擎指标禁令\|三层"=3（≥2）✓
- 修订记录 v1.4 在场 ✓；README 顶行已加 ✓
- policy-lint 实跑 PASS 四项 ✓（本批零代码改动，仅文档）
