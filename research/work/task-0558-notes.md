# task-0558 工作笔记：模型说明卡版本化绑定

## 环境事实（已核验）
- Version.jsx 18271B（<30KB 可全读）；ModelCard 在 L118 附近，四行文案静态内联
- 报告编号：shared/results/05-量化投资/ 最大 R-356 → 本任务用 **R-357**
- 测试基线：quant-bff `npm test` = node --test test/*.test.js，33/33（30 基线+3 W7）
- quant-dashboard package.json 无 test 脚本、无测试依赖（零新依赖约束 → 用 node:assert 最小脚本）
- 部署：nginx `/quantv6/` alias → `tools/quant-dashboard/dist/`（build 即上线）
- 上一版产物 hash：index-CoQGba57.js（R-356）

## 方案
1. 新增 `src/engineCopy.js`（纯 JS，无 JSX）：ENGINE_COPY map（按 engine_id 键）+ engineCopy() 解析器（未命中→`<id>（说明待补）`，空 id→'—'）+ buildModelRows(detail) 纯函数
2. Version.jsx ModelCard 改为渲染 buildModelRows 输出，删内联文案
3. `scripts/engine-copy.test.mjs`：node:assert 断言（命中 4 条/降级 test_engine_x/空 id/真实 vC-0 形状/换引擎后旧文案不出现）；package.json 加 `"test"` 脚本
4. 验证：quant-bff npm test 33/33 不回归 + dashboard 新断言 + VITE_API_BASE=/quantv6 build + grep /quantv6 + 线上 index 新 hash + 无头 390x844 bodyScrollW=390

## 映射（任务书指定）
- a13_rsraw_e1f10dz → A股因子选股（月频调仓）
- gold_trend_sma200 → 黄金ETF 200日均线趋势择时
- ddc → DDC 回撤控制（≤-20% 降仓×0.5，回补 -5%，T+1 生效）
- solver_equal_vol_v1 → 等波动率求解器（两腿风险贡献相等）

## 执行记录
- [2026-08-29 14:0x] 环境核验完成，方案定稿，开始写代码
