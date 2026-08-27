# task-0512 笔记：R-334 简化重构方案（吸收外部对标建议的收敛版）

## 基本事实
- 当前最大报告号 = **R-333**（ls 排序核对），本任务产出 = **R-334**。
- 源文章 8,336B 全文已读。作者自述对 R-322 的描述全部是「推测」，未读过真实报告。
- 四大批评：①人机协同深度不足（人工主导因子挖掘）②迭代效率低（串行、周期数周~月）③策略多元化不足④软硬件协同缺失。
- 文章声称指标：「效率提升40%」「因子数量减少70%」「延迟3μs」「回撤收窄2.65pp」——均不可直接照抄，需折算为可验证断言。

## 真伪核查预判（待与真实证据比对）
1. 「人工串行因子挖掘」→ **不成立**：我们已有 evolution_pipeline 自动进化 + 五门禁 G0-G6 自动判门 + n_trials 台账（R-225/R-249）。待补文件行号。
2. 「回测与实盘割裂」→ 部分不成立：已有 paper 影子观察链路（R-306/R-307/R-308）+ E2 引擎级对照（R-253 等）。
3. 「策略同质化」→ 部分属实但已缓解：多引擎注册制（R-256/R-259）+ 中央风控 corr 判门 G6 独立性 0.15/0.20（R-330 L16 附近）；但引擎数量仍少（微盘+黄金+…）。
4. 「多套自研实现并存复杂度过高」→ **属实**（R-320 D1-D11 / R-321 / R-322 已实锤）。
5. FPGA/GPU/量子/Spark Streaming → 与体量无关，列拒绝项。

## R-201 关键可行性证据（qlib bin）
- 待读 R-201 提取 HP qlib bin 521MB 实测记录。

## 已完成核验（2026-08-27，全部本地证据）

### R 编号与输入状态
- 最大号 R-333 → 本报告 **R-334**。
- R-322 §4-§7 已细读：GM1-GM15 唯一落点表、P0-P3 分期骨架、待确认 7 条（influence/D6/D3/D4/影子特例/factor_catalog/engines.json）。
- R-320 全文已读：60 端点 29 死、死 UI 树 ~1500 行（L11377-12836）、D1-D11 重复矩阵、5 条同步通道仅 1.5 有效、107/182 孤儿、hp_api_server 死服务、分期 P0(删)/P1(通道)/P2(抽象)。
- R-321 关键数字（经 R-322/R-320 转引）：36 可见模块、B1 徽标与 M3/B5 同值最高优去重、≥9 指标渲染点同源 6 处、6 组端点重复拉取、跨 Tab 缓存 TTL30s 方案。
- R-204 执行摘要已读：**总评=治理超配（半月度进化 ★★★★个人玩家超配）/内核欠配（因子台账·微盘风控·风险预算·实验留痕·PIT 均 ★~★★）**；80% 优先级应放因子台账/DSR·多重检验/PIT 数据/微盘风控/实验跟踪五件事，不是继续加治理。
- R-201 可行性证据（L185/L177/L169-180）：HP conda env `rdagent4qlib`（qlib/lightgbm/rdagent CLI **已装**，实测记录）+ `daily_pv.h5` 全市场 1413 万行/5000+ 股票就绪；⚠️ **任务书所称「qlib bin 521MB 已装」未检索到**——R-201 原文当时判断 cn_data bin 层「很可能缺」（L177），故 qrun 迁移第一步必须先校验 `~/.qlib/qlib_data/cn_data` 是否就绪，缺则 get_data.py 补齐。诚实写进报告。
- R-202 结论：QuantaAlpha 与 daily_pv.h5 直接兼容；推荐 B 档起步=**Qlib qrun 原生 workflow（Alpha158/360+LGBM+Ensemble）绕开 RD-Agent 全部坑**；RD-Agent 十轮长流程在 15G 内存机器有 OOM(#678 单因子 df 615-665MB concat)/静默退出稳定性坑 → 不部署独立框架的证据。
- 择时模块定位（task-0501-notes L43/L68/L80-81/L120）：M5=v5model Tab「择时仓位趋势图」；生产端=paper_engine v3 内 `timing_layer_prod` 复算 q3z×trendvol + HP `macro_timing_layer.py`（v1 乘法门 f_breadth）；六 action 含 timing 诊断；timing_matrix 报告页已埋葬（R-321§3.1）。

### 四大批评判定（终版）
1. 人工串行挖掘 → **不成立**（evidence: evolution_pipeline 七步全自动周六 cron、g1-g6 门禁+SCORED、R-220 已移除 #7/#8 人工）
2. 回测实盘割裂 → **部分不成立**（evidence: paper 六action 双引擎、影子两粒度、E2 引擎级对照 R-253/R-264/R-329）；残留=撮合假设分叉风险（R-204 维度一）→ 走 GM9 quant_common
3. 策略同质化 → **部分属实、已有机制**（evidence: engines.json A/A2/gold 多引擎注册制、G6 独立性判门 0.15/0.20（R-330 重冻结晶种）、扩赛道线实跑 R-307/R-330/R-331）；缺口=在役引擎少+非结构化零覆盖
4. 多套自研并存 → **属实**（R-320 D1-D11/R-321/R-322 Top6 三重自查已覆盖，比文章更彻底）
- FPGA 3μs 批评 → 与月频 T+1 十万级体系无关，拒绝项

### 分期表草稿（P0'-P3'）
- P0'=R-320 P0 死码清理照做 + 因子表达式化设计稿（零代码）+ 辩论代理 SOP（本文档）
- P1'=R-321 P1 + M5 状态色带预留（纯渲染分支）
- P2'=GM6 门禁 schema 统一/GM7 影子合一/GM9 quant_common/engines.json 单落点/metrics 二选一/factor_catalog v3 + **新增：qrun 第二裁判底座（cn_data 校验→dump_bin→e2e 双窗对照设计）** + macro_timing_layer f_icir_weight+HMM gate 评审稿
- P3'=p3_3 停 cron（批准）/同步通道取舍/timing 生产端上线/qrun 接管裁决/辩论代理首跑
- 验收命令：crontab -l | grep -c p3_3=0；sha256sum engines.json 前后一致；curl 冒烟 head -c200；影子窗口 diff

- backtest_dividend_quality*.py 自研回测 → Qlib qrun 统一基座评估
- 进化双轨 D6（p3_3 vs evolution_pipeline 双 cron）→ 单轨化
- 五门禁两代字段 G0-G6 vs g1-g6 → 统一 schema
- 影子观察三实现 → 合一
- FactorMAD 辩论 → sessions_spawn 双子代理最小版
- 滚动 ICIR 加权 / HMM → 落进 M5 择时模块改动点
