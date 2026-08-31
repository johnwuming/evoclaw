# task-0596 过程笔记（R-383 文章重做：在役模型逻辑与模型层迭代机制）

日期：2026-08-31
目标：3000-5000字中文文章，聚焦模型层（不写系统层/看板/工程），对照 B站/小红书量化迭代方法论。
交付：shared/results/01-AI行业研究/R-383-文章重做-在役模型逻辑与模型层迭代机制-b站-小红书量化迭代方法论对照.md

## 文件检查
- R-383 未被占用（目录仅 R-382）。使用 R-383。
- R-382 = 20732B（<30KB，可全读，重点取外部素材与来源清单）
- R-322 = 36089B（>30KB，只读结构+关键段落）
- baseline-paper-summary.json = 2520B（全读）
- engines.json = 3833B（全读）

## 核验记录
（边查边写）

## 内部素材核验结论（2026-08-31）

### 1. 两径汇流（R-322 §3，已核）
- 微盘版本线：registry 版本对象驱动，全自动 candidate→backtest→EQUIV→evaluate/SCORED→rank==1 自动 activate→shadow_watch 出影。
- 引擎线：engines.json 引擎对象驱动，半自动：E1 画像→E2 预注册→判门(G0-G6)→影子登记→用户批准激活→active_paper。唯一人工门=激活确认。
- 18 节点 N0-N18：N1-N11 外环研究链、N12-N14 内环运行巡检、N15-N17 横切、N18 退出回退。
- 版本线门禁 g1-g6（R-322 N8）：样本内 ICIR 阈值 / 样本外 ICIR 显著性(p>0.05) / 与现有策略相关性 |ρ|≤0.7 / DSR≥0.95 / g5 必填 / g6 只入评分。五门禁一票否决→综合评分（权重：p .175/dsr .175/oos_calmar .125/oos_sharpe .125/is_calmar .075/is_sharpe .075/dd .10/corr .10/logic .05），rank==1 才有上岗资格，门禁 PASS 自动 activate（R220#8 移除人工确认）。
- EQUIV 等价校验：patch 全关复跑 parent，diffs={} 逐位一致才挂新分支。
- 回测双窗：full+locked（OOS 切分 2021-01）。
- 影子：版本级 shadow_watch（stat_warn 进影清零；clean_evals 满 watch_periods 出影）；引擎级 cross_engine 月度评估。
- 回退：rollback --to 字节级还原（时间线一键回退兜底）。
- 注意：任务书"五门禁 IC/ICIR/turnover/容量/相关性"与 R-322 原文 g1-g6 不完全一致，以文件为准（ICIR_IS/ICIR_OOS/相关性/DSR/必填）。

### 2. 在役模型（engines.json + baseline-paper-summary.json + memory 08-25/08-30，已核）
- 微盘 A：a13_rsraw_e1f10dz，status=active，逻辑=微盘市值倾斜选股 + q3z×EW-MA200 择时内化；version_line a13_rsraw_*。paper 模拟盘运行（8 持仓、部分现金，model_version 与 timing_layer 两个字段）。单引擎绩效不上文章（11:10 原则：单引擎只讲逻辑/进展/状态）。
- 黄金 gold_trend_sma200：SMA200 趋势，active_paper；R-307 用户批准激活（影子期豁免+paper 层），「激活≠真金」；R-378 核验=虚腿 by design（paper_engine_gold.py 无下单接口，产出仅模拟账本，引擎模拟权重 w=0）。对外口径：分阶段门控，先纸面验证机制，真买留独立决策。
- A2 影子臂：a14_crowdf2（T4 拥挤度防御）w=0.5 叠加于 A，status=shadow；影子期 3-6 个月，clean_evals 剔除低拥挤零区分月份（p<40 时 A2≈A 属预期）；R-273 判据；promotion=真金权重分配=用户人工门，永不自动化。

### 3. 负结果归档实例（memory 08-23/08-30 + R-341/R-329，已核）
- PCR（R-277 线）：层级外推负结果第三例——PCR 残差信息真实但作用于组合总暴露层，选股层截面差实测≈0（残差的 2%），不可变现 → 归档。excess_decay 同期关闭。防御侧两线均负。
- PEAD（R-329，task-0508）：因子层三关 G0/G1/T2 全 PASS（残差化净增量真实，IC +0.0266/t 4.35）；但组合层四门 G2 ΔIC/G3 分段/G4 turnover/G5 容量全部 FAIL → 三试验变体判负归档，不翻案不扩网格不换窗。
- QDII（R-341）：E2 判负——G1 净超额 −9.68pp（线 ≥+2pp）、G4 剔近期子窗仍负、G5 成本后 Calmar<1、T2 溢价摩擦 2.60%/边（线 0.5%）触发终止条款；且发现 E1 有同月对齐前视缺陷，按元规则另立预注册。教训：上游锚缺陷如实披露。
- 微盘 P2 闸（R-374/0576）：仅 MA20 日频形态有条件进 E2；月频/MA60（与 RV 门重叠 86.8% 疑似同构）/动量独立闸判负。后续合并裁决 NO-GO（R-382 引 R-377）。
- 可转债线 E1→E2 亦负结果归档（memory 08-23：防御侧两条+新赛道三条线全部负结果归档）。
- a15_csad_resid 评分制 v1.2 判负归档（O1a 严格线不过，毫厘级）。

### 4. 表述纪律（memory 08-30，已核）
- 单引擎只讲逻辑/进展/状态，绩效指标只有组合层有。
- 组合层背景一句：vC-0 静态 58/42 月度再平衡为主通道（B8 权威口径管道），模型插在组合构建层上。
- 微盘 a13 回撤归因（R-373）：maxDD −33.55%=2015 股灾段；2024Q1 篮子 −35.3% vs 策略 −9.9%（这条是归因报告数字，可选择性用于说明"模型也要定期体检"？——属单引擎绩效数字，谨慎：回撤归因属研究结论非绩效展示，可用"2015 年股灾段是历史最大回撤来源"一句，不展开）。→ 决定：不引具体数字，避免口径风险。

### 5. R-382 可复用外部素材
来源清单 17 条全部可复用（B 站三流派、R&D-Agent(Q)、国联民生实测、21 经济网量化平权、Kimi 实践、知乎、smzdm、避坑指南、因子生命周期管理、小红书登录墙说明+R-371 样本）。

## 外部检索补充（2026-08-31，web_search 不可用改用 web-search-prime）
- B站｜科大金工｜《量化金融gplearn遗传规划自动因子挖掘框架》（播放 9514）：https://www.bilibili.com/video/BV1X24y1a7Ai/
- B站｜《AI量化进化遇瓶颈？全新的多因子挖掘框架》（自进化 40+ 版本、需人工介入）：https://www.bilibili.com/video/BV1pV5S6mEWQ/
- B站｜《因子挖掘最佳实践》：https://www.bilibili.com/video/BV1NY411F75J/
- QuantaAlpha（上财团队，LLM+进化策略自进化因子挖掘）：https://github.com/QuantaAlpha/QuantaAlpha
- BigQuant Wiki｜《遗传规划挖掘因子》：https://bigquant.com/wiki/doc/FYXdVMRHRu
- 知乎专栏｜《为什么你的策略回测完美，实盘腰斩？》（样本内 70-80%/样本外 20-30%、滚动窗口）：https://zhuanlan.zhihu.com/p/1977130656162129679
- quant67｜《量化交易系统架构：研究、回测、模拟、实盘四套环境》：https://quant67.com/post/quant/27-trading-system-arch/27-trading-system-arch.html
- 21经济网｜《26岁离开10亿私募，一个交易天才与他的AI Trading创业》（2026-08-23；含对小红书 AI 交易内容生态的公开评价「高赞笔记仍是骗子、割韭菜的新话术」）：https://m.21jingji.com/article/20260823/herald/dd637d64ce2f1885b84194c126041cff.html
- 中国基金报｜《量化的"AlphaGo时刻"：AI重写全球资本市场的游戏规则》：https://www.chnfund.com/article/AR5debe521-fb5e-bcee-3e06-3a22707e4df5
- 知乎专栏｜《AI 量化交易的过去现在和未来》（演进路径：金融知识化→Workflow→Agent→策略代码化→闭环优化）：https://zhuanlan.zhihu.com/p/2070518802069055178
- GitHub｜UFund-Me/Qbot（回测+模拟交易+实盘三段式开源框架）：https://github.com/UFund-Me/Qbot
- 小红书：站内仍登录墙，无法核验原文；用 21经济网公开转述 + R-371 内部提取样本，如实标注。

## 写作裁决
- PEAD 按文件口径写（因子层 PASS/组合层四门 FAIL），不采用任务书「三试验全败 G1」简写。
- 版本线门禁按 R-322 g1-g6 写；「五门禁一票否决→评分 rank1 自动 activate」保留。
- 单引擎零绩效数字；黄金只讲「分阶段门控、纸面验证、真买留独立决策」。
