# R-284：回撤控制 ddc15/20 上岗评估与激活（v1.2 口径复核）

- 任务号：task-0459（R-277 Top5·C1）｜日期：2026-08-23｜类型：评估复核（激活因实现缺口阻断，待用户裁决）
- 批准链：用户 2026-08-23 00:14「全部推进」含 C1（拍板语义=批准评估+激活流程；R-277 C1 标注【用户拍板】在役变更）。前置 task-0458（v1.2）已验收：冻结配置 `model/scoring_v12_frozen.json`（sha256 315ee82d…）在位，a13_rsraw_e1f10dz 为现役。
- **结论先行：v1.2 口径复核通过（替代轨管辖下 ddc15 0.8834 仍 rank-eligible，排序不变、无双双落线），档位选定 ddc15；但激活在实施层阻断——paper 引擎（scripts/paper_engine.py）不存在任何 drawdown_control 代码路径，配置字段激活=死字段。改 paper_engine.py 属 AGENTS.md「不可自动：动 paper_engine」清单项，超出本任务授权（00:14 拍板基于「配置参数切换」表述）。已停在待用户裁决，零 HP 写操作。**

## 一、步骤1：HP 只读盘点（00:44-00:52）

| 项 | 实查结果 |
|---|---|
| paper 引擎 | `scripts/paper_engine.py`（63KB 自包含实现，cron `30 16 * * 1-5 --action daily`，task-0251 baseline；读 model/main.json；不 import a9_common/回测引擎；subprocess 仅用于 rsync 产物） |
| ddc 在 paper 引擎的现状 | **零实现**：grep `drawdown` 0 命中；`thresh` 仅 rebalance trim_threshold（超配>5% 修剪，无关）；`降仓/recover/hwm/circuit` 无相关命中。任务前提「paper_engine.py 组件化已带 ddc 路径」实为**回测引擎**（scripts/backtest_dividend_quality_iter.py，drawdown_control 8 处命中，a15_run.py 参数化先例）——两者不是同一份代码 |
| 配置面 | config/ 仅 config.py（旧小市值策略常量）与 risk-charter.json（人工章程：level1 0.25 降半仓/level2 0.35 清仓，**无自动恢复参数**，语义≠引擎 ddc，修改须 decision-log）；model/main.json params 无 ddc 字段；temp_override.json 仅控制择时开关 |
| paper 组合现状 | 2026-08-17 起 10 万本金，NAV 100,892（+0.89%），8 只持仓（task-0454 已核查：择时门现金 38.3pp+过滤池收缩，口径无误）；组合年轻、当前无回撤，距任何 ddc 触发线远——**激活时点不敏感，不存在「晚激活错过保护」的紧迫性** |
| registry | a13_rsraw_e1f10dz active（22.02%/−33.55%/score 0.8781，R-282 验收）；a15_ddc15/ddc20 从未注册 candidate |

## 二、步骤2：v1.2 口径复核（00:52-00:58）

### 2.1 替代轨（管辖轨）——通过

冻结配置 `structure.track1_replacement`：「评分制 v1.1 原封不动（SCORE_CONFIG、评分函数、排名池、三条件裁决、自动上岗规则零改动）」。ddc 的裁决身份自 R-243/R-277 C1 起即替代轨（在役引擎参数切换），v1.2 未改变其裁决口径 → R-243 分数继续有效，产物直读核对（`results/a15_score_summary.json`）：

| 候选 | 年化 | MDD | Sharpe | Calmar | score(v1.1=现行管辖) | vs 现役 a13 0.8781 |
|---|---|---|---|---|---|---|
| a15_ddc15 | 18.39% | -25.33% | 1.355 | 0.726 | **0.8834**（stat_warn=False） | **+0.0053** ✓ |
| a15_ddc20 | 19.25% | -27.16% | 1.354 | 0.709 | **0.8786**（stat_warn=False） | +0.0005（压线） |

- **排序不变**（ddc15 > ddc20 > a13），无「ddc20 反超」、无「双双落线」；ddc15 holdout（2024-07 后）24.64%/−15.78%/Sharpe 1.44 无退化（R-243）。trial 计账 91→99（v1.2 迁移）对绝对分数无影响（R-282 已验证 DSR 无实质变化）。
- **血统披露（诚实缺口）**：ddc 分数为 a9 血统（e1_guard 硬闸门）指标；现役 a13 为 e1 因子化变体。两条激活路线各有证据缺口：①激活 a15_ddc15 配置=回退 e1 因子化+加 ddc（两项同时变，分数上 0.8834>0.8781 仍占优）；②在 a13 上叠加 ddc=组合从未回测（R-243 C3 已示范组件叠加不可加和）。此缺口须随用户裁决一并拍板。

### 2.2 叠加轨防御臂（补充口径，非管辖轨）——O1b 三线全败（如实记录）

按冻结定义复算（locked NAV 2006-01-04→2024-06-28 三序列日期逐位一致；冻结危机窗清单唯一窗 2023-09-01→2024-02-29，窗内起算 running-max；常态年化=locked 剔除危机窗日收益〔首日跨界保留，4373 日〕按全窗 18.48 年年化；计算产物 HP `/tmp/ddc_v12_check.json`）：

| O1b 防御臂线 | 门槛 | ddc15 | ddc20 | 判 |
|---|---|---|---|---|
| ① 危机窗 MDD 改善 | ≥ +1.0pp | **+0.091pp**（−9.476% vs a13 −9.567%） | +0.079pp | ✗ 差一个量级 |
| ② 常态年化损耗 | ≤ 1.0pp | **3.639pp**（常态年化 18.60% vs a13 22.24%） | 2.780pp | ✗ |
| ③ locked 年化地板 | ≥ −0.5pp | **−3.63pp**（18.39% vs 22.02%） | −2.77pp | ✗ |

O1a 信息臂（ΔICIR）对 ddc 无意义 → 叠加轨整体判负。**归因**：冻结危机窗清单仅含 2023-09→2024-02 微盘踩踏窗，窗内回撤 −9.6% 未达 15%/20% 触发线，ddc 无用武之地；其真实价值集中在 2008/2015 深回撤段（R-243：2015 段 −33.6%→−25.3%），而该两段**不在冻结清单**（新增窗口只能走 v1.3 升版，R-282 已披露同类口径限制）；−3pp 年化成本亦远超叠加轨为「近免费危机保险」的设计容忍度（a14 型：危机改善 +1.45pp/常态损耗 −0.22pp）。

**判定**：叠加轨判负**不否决**替代轨资格——ddc 从未被设计为叠加组件（R-277 C1 定性：替代轨参数切换+用户拍板的风险偏好选择，年化 −2.5~−3.4pp 换 MDD −6.4~−8.2pp 的代价在拍板时已列明）。但本节如实入档：若未来 ddc 以任何「叠加」形态复活，须先过 v1.3 口径（危机窗清单扩展）。

## 三、步骤3：档位选定 ddc15

理由：①分数 0.8834 > 0.8786；②MDD −25.33% 为全候选最深（比 ddc20 再压 1.8pp）；③holdout 无退化；④ddc20 对现役 a13 仅 +0.0005，无稳健余量，ddc15 余量 +0.0053。激活参数依 R-243 C4a：`drawdown_control=1, dd_thresh=0.15, dd_reduce=0.5, dd_recover=0.05`。

## 四、步骤4：激活阻断——待用户裁决（零 HP 写操作）

- **阻断原因**：paper_engine.py 无 ddc 代码路径（§一）。写入 main.json 的 drawdown_control 字段将成为死字段（引擎不消费）=假激活，拒绝执行。真实激活需要给 paper_engine.py 增加最小 ddc 模块——属 AGENTS.md「不可自动（仍需用户批准）：动 active/**paper_engine**/crontab」清单项，且超出本任务写约束（仅限配置 ddc 字段+新增日志）。
- **执行零写声明**：无配置变更故无 tar 备份必要；未激活故 results/ddc_shadow_log.json 不创建（不登记假影子）。HP 全程只读，未杀任何进程。

### 用户选项

- **A（推荐，若仍要上岗）**：批准 paper_engine.py 最小 ddc 补丁（新任务执行，~0.5-1 人时）。实施形态：daily 动作计算 NAV vs HWM 判态；回撤 ≥15% → 目标仓位 ×0.5；自谷底收复 ≥5% → 恢复；状态持久化 state；参数走 main.json params（drawdown_control/dd_thresh/dd_reduce/dd_recover，与回测引擎同名同义）。**生效时点**=补丁合入+tar 备份+diff 校验（仅新增字段）后，下个交易日 16:30 cron daily 自然生效（crontab 零改动）；**回滚**=tar 还原 paper_engine.py+main.json，下一 daily 即恢复。同时需拍板血统路线（§2.1 缺口：a15_ddc15 整体配置 vs a13+ddc 组合——后者建议先跑一次 locked 窗回测补证据再上岗）。
- **B（维持现状）**：ddc15 保持「回撤应急预案」常备（R-243 §4 原案）；paper 组合当前无回撤、时点不敏感，成本为零。
- **C（不推荐）**：risk-charter.json level1 阈值 0.25→0.15 近似——无自动恢复参数（降仓后锁死至人工复核），行为≠回测 ddc，且章程要求 decision-log+用户通知，仍需同等审批量。

## 五、影子观察计划（预登记，激活后自动启动）

- 观察窗：激活生效日起 7 个交易日；期间 ddc 为 paper 在役行为（R-277 C1：影子观察 7 天后再评估真金）。
- 指标：①每日 NAV 与组合 drawdown vs HWM；②ddc 触发次数/降仓/恢复事件；③触发日的反事实对照（无 ddc 目标仓位 vs 实际）；④月末补：MDD、Calmar、年化。
- 产物：HP `results/ddc_shadow_log.json`（纯新增，逐日追加）；观察期满自动出复看报告（登记为当时任务）。

## 六、硬约束执行情况

- HP 零写操作（未动 evolution_pipeline.py/registry/冻结配置/crontab/paper_engine.py/main.json；未杀进程）；全部命令只读+计算落 /tmp。
- 复核未通过即停的门内建执行：本任务实际停在步骤4（评估通过、激活阻断），效果等同——待用户裁决，未激活。
- 大输出截断纪律执行：SSH 输出均 ≤30 行，R-243/R-282 按大小分段读取，JSON 逐字段 python 抽取。

## 七、来源清单

- 依据：R-243 §3.1/§3.2（v1.1 对照矩阵+回撤分段）、R-277 C1 行（拍板语义）、R-282（v1.2 冻结+池分数 a13 0.8781）、R-267（双轨制设计）
- HP 实查：scripts/paper_engine.py（grep 全量）、scripts/backtest_dividend_quality_iter.py、config/{config.py,risk-charter.json}、model/{main.json,registry/a13_rsraw_e1f10dz.json}、crontab -l、results/{baseline-paper-summary.json,a15_score_summary.json,a15_ddc{15,20}_locked_{nav,metrics}.json,a13_rsraw_e1f10dz_locked_{nav,metrics}.json}
- 计算：v1.2 叠加轨三线复算脚本（HP /tmp/ddc_v12_check.json，md5 a123f7304982aae0e45f477bc673db1e）
- 笔记：work/task-0459-notes.md（边查边写全程）
