# task-0350 过程笔记（R-223 量化迭代流程与规则总纲）

## 1. HP registry 现读验收（2026-08-17 22:0x）
- registry 共 48 个文件（含 .main.json.snapshot 4 个，实际版本 ~44 个）
- status 分布：**active = v5h_xsub** ✓、**sota = v2b_trr** ✓、**candidate 含 v6a_def** ✓
- 其余大量 candidate / pending / retired（v0_seed、v1i_q3z retired）
- 版本时间线：v0_seed → v1a-v1k（第一代单因子）→ v2a-v2f → v3a-v3f → v4a-v4e → v5a-v5i → v6a_def
- 验收标准1：通过

## 2. VPS 已有报告清单（05-量化投资/）
- R-195 RD-Agent 评估、R-196 执行总纲、R-198 因子清单调研、R-200 平衡问题
- R-201/202 部署与框架调研、R-203 流程梳理与自动化改造、R-204 行业标杆
- R-205/206/207 Tab重构三连、R-213 质疑评审
- R-216 因子普查、R-217 换赛道、R-218 华福调研、R-219 约束审计、R-220 处置建议、R-221 SSH排查、R-222 A9实验
- work/ 下 notes：task-0331~0349

（后续持续追加）

## 3. 现役/关键版本配置（registry 现读）
### v5h_xsub（active，activated 2026-08-17 04:58:48）
- selection: strategy=dividend_quality_smallcap_seedB, sort=ext(ext_factor=low_amount, ext_weights=[1.0,0.0]), e1_guard=true, mom_cols=[ret120], xsub_days=365（次新剔除：上市不满1年剔除，first_last字段实现含退市）
- factors: div_yield_ttm / roe_ttm / roa_ttm / circ_mv / ret120
- timing: q3z_x_ew_trend_overlay；q_key=q3z(win36,zscore,hi1.0,cut0.40,w_min0.3)；trend=池内等权指数(含退市)月末收盘 vs MA200 破位×0.6；月度乘法合成，无重裁剪(自然下限0.18)
- gate: DSR=0.9923, n_trial=85, verdict=PASS；logic=次新剔除(P0-5)降尾部风险
- provenance: task-0338 A7 P0 增强因子批次收口, parent=v4b_mve1, report=results/a7-iteration-report.md

### v6a_def（candidate，created 2026-08-17 12:12:45）
- selection 与 v5h 完全一致（四闸门+ext low_amount+E1+xsub365）
- timing: q3z(w_min=0.0) × MA15 快趋势，自然下限 0.0；[A9 E2 网格 MA15_on_f0]
- gate verdict=candidate；注册线: MDD 改善 5.13pp(≥3) 且年化损失 1.11pp(≤2)；用户 2026-08-17 20:10 拍板注册防守档；Calmar 0.593 > v5h 0.528
- provenance: batch=A9, task-0342, experiment=E2 timing grid MA15_on_f0

### v2b_trr（sota，evaluated 2026-08-16 15:24:02）
- selection: sort=mv, div_min=0.02, roe_min=0.15, roa_min=0.10, n_hold=20, price_cap=10.0, cost_model=v2, limit_board=on, capital_base=1000万
- timing: 同结构 q3z(w_min0.3)×EW-MA200
- gate: ICIR_IS=0.5994, ICIR_OOS=-0.0525, DSR=0.9873, n_trial=51, MDD改善 -4.88pp（即恶化4.88? 待对符号：mdd_deterioration_pp=-4.88 为改善4.88pp）, oos_split=2021-01
- provenance: task-0327 A3 fork 回撤攻坚, parent=v1i_q3z

## 4. decision-log 全貌（53 条）
- 结构字段：ts/decision_id/type/version/trigger/action/backup/params/rollback_condition/expected_impact/code_ref/data_snapshot
- 类型序列：seed_reset → bootstrap → evaluate_pass/reject → activate → a2b/a2c_batch_activate → a4d/a5/a6_batch_closeout → A7 closeout+addendum → R220 处置 → A9 closeout+register_candidate → paper_timing_align → A8 closeout
- 关键决策详情：
  - D-20260816-SEEDB-RESET: task-0316 Q4b 收口后种子B重置；params={div_min0.02,roe_min0.15,roa_min0.10,sort:mv,n_hold20,price_cap10.0}；备份 tar 729条目 md5 b2e1d572
  - D-20260817-A7-01: A7 收口 9 版本（v5a_amt37/v5b_amt55/v5c_amt73/v5d_amh55/v5e_cv73/v5f_cal/v5g_lim/v5h_xsub/v5i_comb）；v5h activate；回退条件=激活后回撤超阈值或paper显著劣于endtoend→rollback v2b_trr
  - D-20260817-A9-1 (19:50): A9 收口结论 6 条：
    (1) 四闸门=真实安全换收益交易(+6.0pp年化/+7.0pp MDD)
    (2) PB 价值 alpha 主要藏于原始宇宙（质量宇宙近12月IC≈0.004失效, raw仍0.0324, 微盘段近端归零）
    (3) 闸门外价值暴露(E3 raw)较纯去闸门(E1 raw)省3.23pp回撤且年化持平
    (4) MA15_on_f0 过防御线(MDD改善5.13pp, 年化损1.11pp)→防守备选操作点（后经用户20:10拍板注册为 v6a_def candidate）
    (5) q3z off 纯趋势空仓全部 MDD -38%~-52%，外部"MA15空仓压回撤"证伪
    (6) 当前可达前沿 v5h(15.7/-29.8)~raw(21.8/-36.8)，防守端点 MA15_on_f0(14.6/-24.7)，25%/-20% 双目标仍不可达
  - D-20260817-A9-2 (12:12): v6a_def 注册 candidate（不切换现役，上线需 evaluate/评分流程）
  - D-20260817-R220N37 (12:28): paper 调仓时点对齐回测口径（R-219 #37 发现，task-0347）；下次调仓 2026-09-01
  - D-20260817-A8-1 (20:58): A8 收尾；bucket raw 年化+2.55pp 过线但 MDD 恶化4.21pp>2pp → 不注册；合成方式归因闭环：ranksum 排序层最优(抗极值+全序分辨率)；bucket 顶部分辨率不足且并列推高换手0.536全场最高；zscore quality宇宙最优但raw被极值扭曲；前沿 v5h(15.7/-29.8)~raw ranksum(21.8/-33.6)

## 5. 五门禁定义（evolution_pipeline.py 现读，L57-65 GATE_CONFIG）
- STATUS_ENUM = [candidate, pending, active, sota, retired]
- g1 icir_is_min=0.5：IS 全样本复合 ICIR 年化下限
- g2 oos_p_min=0.05：OOS 相对 IS 劣化单侧 t 检验 p>0.05（不显著劣于）；oos_split_ym=2021-01
- g3 max_corr_max=0.7：候选新增因子 vs 在役因子最高|ρ|<0.7；数据源 factor_ic_corr.csv 优先/catalog corr_alerts；无新增因子→N/A（E3修复 task-0292）
- g4 dsr_min=0.95：Deflated Sharpe（Bailey & López de Prado 2014），n_trials 累计计数
- g5 logic 非空：候选改动须有逻辑说明
- g6 mdd_vs_parent_max_pp=2.0：endtoend MDD 较父版本(active)恶化 ≤2pp，**一票否决**（E3修复 task-0292；数据缺失→N/A 不折减）
- verdict 规则：decisive(有 PASS/FAIL 的门禁) 全 PASS → PASS；L778: PASS 且 prev=candidate → 自动 activate（待确认具体行文）

## 6. R-220 执行现状与基建脚本（HP 现读）
- **#8 已实施**（evolution_pipeline.py L776-781）：evaluate verdict=PASS 且 prev=candidate → 自动 _do_activate，日志注明"R220 #8 移除人工确认制"；decision-log expected_impact 同步注明
- **audit_lock.py**（task-0292/E6）：AUDIT_LOCK_END=2024-06-30（locked 审计段，OOS/评估窗口不得穿透）；clamp_date/clamp_ym 统一截断；v1.4 前历史穿透不回改
- **rebalance_gate.py**（task-0347/R220-#37）：判断今日是否当月首个交易日，对齐回测 groupby(M).min() 口径；日历源 T1 官方缓存→T2 本地K线→T3 兜底周一~五；退出码 0=PASS/3=SKIP/2=ERROR；修复 paper_engine --check-month-start 因周度刷新月首无K线而永久 skip 的缺陷

## 7. cost_model_v2.py（task-0293/Q3 可交易性基建）
- estimate_cost(): 佣金 2.5bp（最低5元）+ 印花税卖出 5bp + 滑点/冲击 ADV 平方根模型 impact=k*sqrt(order_amt/ADV20)，k=10 保守
- is_untradeable(): 一字板判定 O==H==L==C(容差1e-6) 且涨跌幅≥板块阈值-0.1%容差
- 涨跌停分段：主板10%；科创板688 20%(2019-07-22起)；创业板300/301 10%→20%(2020-08-24注册制)；ST 5%/20%；北交所30%(2021-11-15起)
- qfq 前复权近似性论证在文件头

## 8. Registry 五操作 + rollback 机制
- evolution_pipeline.py: 版本 Registry + 五操作 backtest/evaluate/activate/rollback/override
- activate 时冻结 main.json 字节快照 → rollback 字节级还原依据（registry/*.main.json.snapshot）
- decision_log() 每操作写 decision-log.jsonl（trigger/metrics_summary/expected_impact/rollback_condition/phash/data_snapshot）
- ledger_append() 写 experiment-ledger.jsonl（entry_type/version/metrics/data_snapshot/phash）
- temp_override 可 TTL 关闭（timing.disable_switch 字段）

## 9. R-220 处置细节（报告现读，task-0344 续，用户 13:58/14:09 确认）
- 总原则（用户 13:10）：门禁机制改权重机制，不设强制通过门禁
- 三档处置：
  - 第一档立即权重化：#7 一票否决→综合评分制（核心改造）；g2/g4→最高权重评分项+统计警示线（g2 p<0.01 或 DSR<0.90→人工复核标签）；g1/g3/g5 低权重；#18 E1→惩罚分；#21 日历降仓系数网格{0,0.3,0.5,0.7}；#29 排序权重与 A8 合流；#11 OOS split 可调
  - 第二档 A9 实验裁决（用户 13:58 授权验证后自动推进）：#14-17 四闸门→质量分进排序（ROE降权0.3-0.5）；#19 次新剔除保留硬剔除（+3.32pp 实测最强增益）；#20 涨停剔除（+2.32pp 未上岗）A9 顺带测；#23/24 MA{15,20,50,100,200}×floor{0,10,18,30}%×q3z{开,关}；#39 ST 对照
  - 第三档保留：#9 rollback 快照、#10 locked≤2024-06-30（可信评估职责）、#13 legacy 豁免+override TTL（14:09 澄清保留）、#22/25 q3z 参数、C类物理现实、D类防作弊
- 特殊处置：#12 战役目标 25%/-20%/1.2 从迭代评判摘除（是 openclaw goal 非评判标准）；#37 paper 月末 vs 回测月首口径 bug 级独立修复（已完成 task-0347）；#8 activate 人工确认删除（task-0345 执行）
- 综合评分公式草案：0.35×S_stat + 0.25×S_oos + 0.15×S_is + 0.10×S_dd + 0.10×S_corr + 0.05×S_logic
- **#7 评分制改造现状：R-220 已定但未实施**（pipeline 现读仍是一票否决 verdict 逻辑）；路线图第一项"[立即] #7 verdict 改造"尚未落地

## 10. 各批次迭代报告要点（HP results/*-iteration-report.md 现读）
### A2/task-0324（107因子进管线第一批，5 候选全 REJECT）
- 基线 v0_seed：full 26.35%/-69.49%/0.903；locked 26.26%/-69.49%/0.885（裸选股无择时）
- 候选：v1a_score 质量复合分 / v1b_mvq 小盘主导复合 / v1c_liq min_amt500万 / v1d_cv 成交额CV / v1e_vol 低波；全 REJECT
- 首创 ext runner：对 engine.run_backtest 源码字符串级插入 ext 分支、exec 副本，引擎文件零改动；等价校验逐位一致 diffs={}
- 基建口径从此确立：全量池+成本v2+一字板+审计锁（AUDIT_LOCK_END=2024-06-30）

### A2B/task-0325（DSR 友好化，6 候选 2 PASS，v1i_q3z activate）
- 先算 DSR 通过线再设计：N=45 时 σ_d≈0.0125（择时档）需 Sharpe≥0.84 → 降σ仓位类改动是过 g4 唯一现实路径
- v1i_q3z（+q3z 估值择时 PE36月z>1降仓）五门禁全 PASS → activate；v1k_q5z PASS 留备选
- 四路新 patch：inv_vol 加权 / rank_buffer / vt_target + 原有 ext，等价校验逐位一致

### A2C/task-0327（回撤攻坚，6 候选 5 PASS，v2b_trr activate）
- 父 v1i_q3z locked 15.80%/-34.74%/0.905；诊断四个≥30%回撤段：2008(-34.74%)/2011-12慢熊(-31.4%)/2016-18慢熊(-30.5%)/2015一字跌停(-29.9%仅8日)
- 低估值慢熊 q3z 天然失明 → 趋势信号补位：v2b_trr = q3z×池内EW指数MA200趋势（月末破位×0.6）五门禁全 PASS → activate，成为长期现役（后被 v5h 替代转 sota）
- 战役三目标 15%/10%/1.0 同时不可达（本批口径）→ 交付可达前沿 + 现役升级；Calmar 不变式首次提出（纯择时/风控到不了 25%+20%，需选股层真 alpha）
- 5 PASS 4 留 pending，1 REJECT

### A4D/task-0328（价值大师选股，6 候选 2 PASS 0 activate）
- 大师指标 IC 预检全负：pb ICIR -1.626、peg_np -1.337、neff -0.796；buf_quality 唯一近零(+0.0035/+0.091)；lynch_bucket 无IC砍掉
- 结论：质量小盘宇宙内价值指标 IC 全负，价值不能当排序主键；alpha 由小市值+成长主导
- 0 activate，现役仍 v2b_trr

### A5/task-0333（成长×质量+E1护栏，5 候选 2 PASS 0 activate）
- 证据链三报告：a4d（价值IC负）+ holdings-postmortem task-0331（E1 砍20.8%尾部亏损/误杀12.1%赢家；G1 avg+21.2%/胜率78.4%）+ a2c（Calmar不变式）
- v4b_mve1（仅加E1护栏）与 v4d_gqg1 六门全 PASS 留 pending；最优 v4b_mve1 12.42%/-28.99%/0.840 不优于 v2b_trr 15.15%/-29.86%/0.936
- 核心结论：成长×质量复合在质量小盘宇宙无 alpha（IC -0.0265/-0.62 + 回测双证）；E1 单加压 MDD 但年化/Sharpe 双降；25%/-20%/1.2 前沿无交点需换赛道
- v4b_mve1 成为 A7 骨架 parent
- 新基建：ST 区间表加入（a5 起口径=全量池+成本v2+一字板+审计锁+ST区间表）

### A7/task-0338（微盘宇宙 P0 增强因子，9 候选 4 PASS，v5h_xsub activate）★现役上岗批
- 骨架 v4b_mve1；裁决：v5h_xsub（次新剔除 xsub_days=365）六门禁全 PASS 且 locked 三项全优于 v2b_trr → activate（D-20260817-001/-002），v2b_trr→sota
- v5h locked 15.74%/-29.80%/0.998/Calmar 0.528
- IC 预检：amt20 -0.107 / amt_cv20 -0.189（低成交额/低换手CV 收益更高）；amihud 近零 +0.0039
- 前置证据 A7b（task-0339）：常驻现金曲线 每10%现金≈-1.31pp年化/+2.55pp MDD，Sharpe 单调缓降无拐点 → 现金只压回撤不补收益
- 前置证据 A7c（task-0341）：动态画像 低成交额族近端仍有效（推进）、换手CV 近端走强（补测）、Amihud 全市场强但微盘增量弱
- 次新剔除 +3.32pp 实测最强增益（R-220 引用）；涨停剔除 +2.32pp 未上岗

### A8/task-0348（合成方式归因，ranksum/zscore/bucket 三方式对照）
- 同因子集（log_mv1.0+amt20 1.0+pb_inv0.7+roe0.3）× 三方式：
  quality 宇宙：zscore 15.94%/-29.52% 最优 > ranksum 15.33%/-28.78% > bucket 15.27%/-28.80%
  raw 宇宙：ranksum 21.76%/-33.55%/1.344/0.649 最优 > zscore 19.85%/-34.59% > bucket 18.29%/-34.01%
- bucket raw 年化+2.55pp 过线但 MDD 恶化4.21pp>2pp → 不注册
- bucket 语义：月度截面 rank(pct)→符号翻转→floor(r×5) 得桶号0-4→Σ权重×桶号；月换手0.536 全场最高（并列推高换手）
- 归因闭环：ranksum 排序层最优（抗极值+全序分辨率）；zscore quality 宇宙最优但 raw 被极值扭曲；bucket 顶部分辨率不足

### A9/task-0342（原始宇宙对照+PB IC+排序合成+择时网格 40 组）→ 详见 R-222
- raw locked 21.76%/-36.78%/1.215/0.592；四闸门=+6.02pp年化/+6.98pp MDD 真实安全换收益交易
- PB IC：原始全宇宙 0.0576/0.521 vs 质量闸门内 0.0313/0.196（差2.7倍）；质量宇宙近12月 0.0042 失效；微盘底20%近12月 0.0007 归零
- E3 raw 21.76%/-33.55%：闸门外价值暴露比纯去闸门省 3.23pp 回撤
- E2 网格：MA15_on_f0 14.63%/-24.67%/0.593 最优（MDD改善5.13pp/年化损1.11pp）→ 用户 20:10 拍板注册 v6a_def candidate
- 证伪1：q3z off 纯趋势全部 MDD -38%~-52%（外部 MA15 空仓说法不成立）；证伪2：A7b"MA缩短恶化"仅在重地板成立
- 前沿：防守 MA15_on_f0(14.6/-24.7) — v5h(15.7/-29.8) — 进攻 E3 raw ranksum(21.8/-33.6)；25%/-20% 双目标无交点

## 11. 补充批次与 HP 自动化
### A6/task-0334（神奇公式批次，D-20260816-032）
- 无 activate；结论=估值腿负 alpha（ev_ebit ICIR -1.25，与 pe 相关 0.88）；质量腿零 alpha（roc IC≈0）
- 候选 v4a_mf0_trr/v4b_mfu_trr/v4c_mfu_e1_trr/v4d_mfu_raw/v4e_rocblend_trr

### A7b/task-0339（常驻现金曲线+稳健性）
- 现金网格 {0..40%}：每10%现金≈-1.31pp年化/+2.55pp MDD改善；Sharpe 单调缓降 0.8401→0.7996 无拐点（贴主"夏普略升"不迁移）
- MDD≤20% 需 cash≥40%（-18.77%）但年化只剩 7.20%（距25%目标 -17.8pp）→ 现金只压回撤压不回收益
- 参数扰动+分段稳健性：2018-2021/2022-2026 分段方向一致才算数
- 结论：参数无隐藏空间/现金杠杆不推动前沿

### A7c/task-0341（动态有效性画像）
- 低成交额族近端仍有效（推进）；换手CV 近端走强（补测）；Amihud 全市场强但微盘增量弱；低波族近端衰减

### Calmar 不变式五次验证时间线
1. a2c(08-16)：首次实证，7 数据点 Calmar 0.32-0.51，MDD 每压5pp年化掉约3pp
2. a4d(08-16)：再证，v3e MDD 压到 -22.8% 时年化只剩 10.05%
3. a5(08-17)：第三次，v4e 裸选股 19.09%/-71.69% vs v4d 择时 11.59%/-29.67%；30+候选无 25%/-20% 交点
4. a7b(08-17)：第四次，40%现金档 MDD 达标但年化 7.20%
5. A9(08-17 R-222)：第五次，年化25%所有路径附≥3.5pp MDD恶化；MDD -20%端最高年化仅14.6%

### HP crontab 自动化（现读）
- paper_trade.py --action daily：工作日 16:30
- cron_paper_rebalance.sh：工作日 16:30，gate 自检月首才调仓（task-0347/R220-#37，旧"每月25日"cron 已停）
- refresh_data.py：周日 20:00；fetch_valuation_data.py：周日 06:30
- p3_3_evolution_standalone.py --rounds 5：每月 1/15 日 02:00（半月度因子进化）
- paper_engine baseline（task-0251）：daily/rebalance 已 PAUSED-20260816-seedB，validate 周日 20:00 保留
- collect-metrics.sh：每分钟推 VPS 8055（量化指标采集循环）

## 12. 架构与同步（VPS+HP 现读）
- R-203 五层架构：L1 因子层（72因子字典+IC/ICIR+观察池）/ L2 选股层（股息+ROE+ROA 小盘 + 三重gate+WF）/ L3 择时层 / L4 模拟盘（paper_engine 3条cron 全自动）/ L5 进化闭环（evolution_engine）
- R-203 断点评估（08-15）：L4 已全自动，唯一断点=L5 定时+统一编排；改造=纯增量（决策日志/想法池/统一runner/页面控制面）
- HP→VPS：collect-metrics.sh 每分钟推 VPS:8055（agent-dashboard，量化Tab）；sync_to_vps.sh 经 ZeroTier（HP 10.12.192.174→VPS 10.12.192.225）同步 results/
- HP 其余 cron：evolution_pipeline.py cycle 周六09:00；notify_hub.py 每小时:10（W8 task-0279）；w6_collect_delisted 每月1日06:00；reboot_autostart @reboot；heartbeat_selfheal */5min（含 2222 用户态 sshd 自愈，R-221 缓解项）
- VPS 端：shared/results/04-投资研究/ 与 05-量化投资/ 承接同步成果；README.md 变更记录
