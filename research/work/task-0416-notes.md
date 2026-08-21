# task-0416 过程笔记：多引擎+中央风控架构与量化看板模块映射（R-256）

## 时间线
- 13:10 task-0416 置 running ✓（任务中心返回 ok）
- R-255 确认为 05-量化投资 目录当前最大编号 ✓ → 新报告用 R-256
- 13:2x 实查完成，报告落盘

## 证据 1：设计文档源头
- R-206 v4（模块清单版，26.5KB 全读）：设计五Tab 33模块 + registry版本对象体系
- R-205（审查版）：Tab1-4 旧四Tab审查，发现三硬伤（因子全不过/9信号只用3/K线FAIL无人管）
- R-207（产品说明书）：五Tab总览+数据资产+API设计+cron全景
- README 变更记录确认后续演进：R-214（15-产品方案，v4重构设计+ID前缀体系）、R-224（版本选择器）、R-248（a12月度evaluate/影子机制）

## 证据 2：看板代码实查（tools/agent-dashboard/server.js，745KB/13707行，8-19最后修改）
### 前端子Tab（server.js:8909 `_V5_TABS = ['data','factor','v5model','v5btlc','paper','v5hist']`）
1. **data 数据页**(9621)：api=quant/data-health + quant/data-assets。data-health=6经典卡(baseline-paper-validation.json)+4灰卡(graycards_cache.json: PIT/幸存者/估值/财务) = R-206设计10卡已落地
2. **factor 因子页**(9768)：api=quant/factor-catalog(v3) + factor-ic-series；在役四因子硬编码(8810 IN_SERVICE_FACTORS)
3. **v5model 模型页**(9081)：api=quant/active + active/pos + version-options；版本选择器+指标卡回退链(metrics→registry→manifest)+择时仓位趋势图
4. **v5btlc 回测页**(9179)：api=quant/active + active/curves + version-options；净值=策略vs基准
5. **paper 模拟实盘页**(12163)：api=paper/summary+nav+trades+portfolio + baseline/summary?version + run-status + crowding + risk-status + registry + timing；M4.7拥挤度/M4.8退出纪律以卡片存在(paper页消费)
6. **v5hist 迭代历史页**(9428)：api=quant/history(分页,hide_legacy) + history/:id；详情页内嵌模型层(quant/models + baseline/summary?window + baseline/meta) + 验证层(gates + dsr + q4b-contrast)
7. 头部横条：quant/freshness(8821) + quant/consistency(8844,30min自检,task-0359)

### 隐藏页（僵尸判定核心证据）
8. **quant-page-models**(div 6854)：loadModelsQuant(10397) 渲染 M2.2/M2.3/M2.4/M2.5决策时间线/M2.6 Pending/M2.7想法池/M2.9台账/action-queue徽标+择时贡献矩阵(quant/timing-matrix)。**不在 _V5_TABS**，switchQuantTab 永不激活(8910 `if indexOf<0 tab='data'`)；唯一残余调用=action入队后自刷(10714) → 隐藏但代码完整
9. **quant-page-btlc**(div 6855)：loadBtlcQuant(10907) 渲染 M3.0四层归因链+危机段+历代最优+e2e-curves多版本叠加。同因不在 _V5_TABS 不可达；btlcOnVersionChange(10968) 仅由本页自渲染元素触发 → 死链

### 后端僵尸路由（代码级实锤）
server.js:1833-1836, 2663-2664, 3508 显式 `quantDeprecated(res)`：summary/nav/factors/evolution/microcap status/microcap phases/evolution summary 共7条（1798注释「旧周期留档 2026-08-16 起新周期 registry 驱动」）

### 影子观察现状
- lifecycle API(2553) 含 shadow_watch 清单(2614-2649, task-0383)：扫 registry gate.shadow_watch.active
- pending API(2450) 透传 shadow_watch 进度(since/last_eval/clean_evals/required)
- 消费方=隐藏 btlc 页 → 影子观察UI当前不可达（后端机制在）

## 证据 3：数据侧（workspace-quant = HP 镜像，auto-sync 30min）
- registry 实况：~60版本；**a13_rsraw_e1f10dz=active（引擎A在役）**；a12_s2_reb=candidate（影子观察对象,R-248）；a14_crowdf2=candidate（R-254负结果归档）；v1.4=active（择时层命名空间）；a9/v1.1=sota
- paper 引擎产物：baseline-paper-nav/trades/summary/portfolio/validation.json（results/）
- risk-status.json（charter_version/rules/overall_status）+ crowding-indicators.json（microcap_eqw_index/overall_flag/capacity）→ M4.7/M4.8 数据在产
- run-status 8文件心跳(3685)：paper nav/trades/summary 36h + validation/risk/crowding 8d + timing_prod 40h + registry 90d
- paper_v5h_equiv_check.json：paper vs active 回测规则层一致性校验（task-0352）
- versions-manifest.json 107KB（8-21 13:00 仍在更新）= 单一事实源

## 证据 4：引擎B与影子事实（README变更记录）
- R-255：k=1行业动量Top5月频，E1达线（t=1.59胜率55.5%四分段全正），Top5与a13相关仅0.09-0.15 → 建议进E2预注册；E2尚未开始
- R-248：a12影子机制=月度evaluate+晋升守卫(clean_evals≥2转人工)+shadow_watch registry 字段
- R-253/R-254：a14拥挤度T4差一条不过线，负结果归档不激活 → 评分制v1.1自动激活三条件先例

## 文档vs代码不一致清单
1. R-206「五Tab 33模块」→ 实际六Tab（v5hist 独立，task-0343 定序 data/factor/v5model/v5btlc/paper/v5hist）
2. M1.4相关性热力图、M1.5月度体检报告：**代码未见**（因子页仅 catalog+IC序列）
3. M2.5/M2.6/M2.7/M2.9 控制面UI：代码存在但页面隐藏（R-207§4仍描述为Tab3模型页内容）
4. M3.0-M3.7 归因链/危机段/历代最优：代码存在但页面隐藏（v5btlc 只有 active+curves 简化版）
5. M3.8 DSR曲线：以 gates/dsr API+v5hist验证层形式落地（形态≠设计）
6. microcap status/phases API：设计有、代码已deprecated（被 crowding-indicators.json 替代）——设计与实现分叉的实锤
7. 微盘拥挤度/退出纪律：设计在Tab5卡片 → 实际在 paper 页（无独立卡组件，随paper页渲染）
