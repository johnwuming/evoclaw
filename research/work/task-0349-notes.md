# task-0349 过程笔记（边查边写）

任务：看板v6 模型/回测页版本选择器：数据支持评估 + 条件实现
开始：2026-08-17 21:52 GMT+8

## 1. 数据盘点（2026-08-17 22:00 前后）

### 1.1 manifest 总览
- versions-manifest.json（71,138B）：{generated_at, active:"v5h_xsub", versions:[69]}
- 69 条 entries，version_id 去重后 68（v4b_mve1 出现两次：a5_v4b_mve1_formal[pending,文件全] + a7b_v4b_mve1[backtest-only,仅locked]）
- 每条字段：version_id/strategy_prefix/status/strategy/registered_at/windows{full,locked}/files_note

### 1.2 文件存在性（shared/results/04-投资研究/ 与 workspace-quant/results/ 双份一致，后者是 dashboard 实际读取源 QUANT_REPORTS_DIR）
- 69 entries × {full,locked} × {metrics.json, nav.csv} 存在性：
  - a9_timing_MA200_on_f30：metrics+nav 双窗口有；yearly 无（回测-only 版本，yearly 不在 dashboard 消费范围）
  - v4b_mve1@a7b 前缀：full 三件缺（同 version_id 的 a5 前缀文件全）
  - v6a_def：prefix=null，registry only，全缺
  - 其余 66 entries：metrics/nav/yearly 全有
- yearly.csv 仅历史页用（现 v5 页面不消费 yearly，模型/回测页不需要）→ 不构成缺口

### 1.3 nav 序列质量（逐版本 head/tail 实测）
- 全部有文件的版本：full 窗口 2006-01-04 → 2026-08-14（5009 行，a4dx/v3x 系 5011 行），locked 窗口 → 2024-06-28（4492 行）
- 序列完整、口径统一，趋势图数据 100% 支持

### 1.4 metrics.json 字段（模型页参数解释的数据源）
- 每份 metrics json 含完整选股参数：sort/cost_model/limit_board/capital_base/div_min/roe_min/roa_min/score_weights/n_hold/price_cap/min_amt/drawdown_control/dd_thresh/dd_reduce + 绩效指标
- 模板引擎 quantTplSelection/quantTplTiming/quantTplTrading 消费 metrics json（mj）+ registry（selParams/timing）

### 1.5 registry 覆盖（VPS /root/.openclaw/workspace-quant/model/registry/，48 个 json）
- 覆盖 44/68 unique 版本（全部 v0_seed..v6a_def 主线版本）
- 缺 registry 的 24 个：a2/a2b/a2cx/a4dx/a5x/a7x/a8x/a9x/mfx 各 equiv/ref + a8_bucket_* + a9_*（equiv 复验与 backtest-only 实验版）→ 这些版本解释模板自动回退 metrics json（选股闸门/排序/持仓可渲染，择时层显示"未知/未启用"，缺 e1护栏/次新剔除等 registry 独有参数）
- registry-only 额外条目 v1.1~v1.4（老版本线，不在 manifest）

### 1.6 基准序列
- 沪深300：e2e_curves/index_hs300.csv，2006-01-04 → 2026-08-07（注意比策略 nav 短 5 个交易日，前端 v5AlignSeries 前向填充 + 窗口首日归一已处理）
- 微盘指数（回测页"微盘等权指数"实际数据源）：a2cx_ew_trend_signal.csv 的 ew_idx 列（月频 2005-01 → 2026-08，261 行，全池等权含退市）——不是 e2e_curves 下的文件，是从 HP 同步的池内等权指数
- 择时仓位：timing_signals_iter4.csv（58,828B）+ a2cx_ew_trend_signal.csv trend_f 列，VPS 端合成

### 1.7 现有 API/前端架构（task-0343 v5）
- 后端：/api/quant/active（profile=windows指标+模板解释）、/api/quant/active/pos、/api/quant/active/curves（策略nav双窗口+hs300+ewmicro）、/api/quant/history（分页列表）、**/api/quant/history/:versionId（单版本详情：windows+explanation+selection_params+timing+decisions，已存在！）**
- quantActiveProfile() 只服务 active 指针版本；curves 端点内嵌 active profile
- 前端：renderV5Model（头卡+指标卡+解释+仓位图）、renderV5Btlc（指标卡+nav对比图+范围chips）、renderV5HistList/Detail（已能点开任意版本看报告式详情）
- 结论：模型页切换所需后端 90% 已存在（history/:versionId）；回测页切换需给 curves 加 version 参数

### 1.8 支持矩阵结论（版本×能力，三档：✅可用 / 🟡部分 / ❌缺）
- 指标卡（metrics 四件套+）：68/68 有文件的版本全支持（v6a_def ❌）
- 趋势图（nav 全序列）：同上 68/68 支持（v6a_def ❌；v4b_mve1 用 a5 前缀 ✅）
- 参数解释（模板零 LLM）：44 版本全量支持（registry+metrics）；24 个 equiv/backtest-only 版本 🟡 部分（metrics 回退，择时层与 registry 独有护栏参数缺）；v6a_def ❌
- 总支持率：指标卡 98.6%(68/69 entries)，趋势图 98.6%，参数解释 63.8% 全量 + 34.8% 部分（合计 98.6% 可渲染）
- 主流版本（active v5h_xsub + sota v2b_trr + 近三轮实验 a9_*/a8_*）：指标+趋势图 100%；a9_*/a8_* 参数解释为部分（无 registry）但不阻塞切换展示

**评估结论：主流版本数据齐备 → 过闸，进入第二阶段实现。**

## 2. 实现与验证（2026-08-17 22:05-22:10）

### 2.1 后端 /api/quant/version-options（插在 curves 之后）
- 实现：manifest 69 entries → 同 version_id 去重（v4b_mve1 保 a5 前缀那条，评分 metrics×2+nav×1）→ 68 条
- caps 判定：metrics/nav=QUANT_REPORTS_DIR 下 prefix_locked/full 文件任一存在；explain_full=registry 存在 AND metrics 有（notes §1.8 口径）
- 排序：active 最前（v5h_xsub），其余 registered_at 倒序（次条 v6a_def 2026-08-17 12:12:45）
- node --check 通过；重启 agent-dashboard 后 active

### 2.2 验证输出（实际运行）
- 任务中心正常：GET /api/tasks 返回 JSON（task-0350 在列）✓
- version-options：{"ok":true,"available":true,"total":68,"active_version":"v5h_xsub"}；caps 计数 metrics=67/nav=67/explain_full=43（=44 registry 版 − v6a_def 无文件）；nodata 仅 v6a_def（caps 全 false，windows null）✓
- 去重验证：v4b_mve1 仅 1 条，strategy_prefix=a5_v4b_mve1_formal ✓
- active?version=v2b_trr：available，prefix=a2c_v2b_trr，windows.locked annual 15.15% ✓
- curves?version=v2b_trr：strategy locked 899 点 / full 1003 点（周频降采样）+ hs300 + ewmicro ✓
- bad version（nonexist99）：available:false + note '版本不存在或等待同步…' ✓（响应落盘 /tmp/t0349-opts.json、/tmp/t0349-curves.json）

### 2.3 前端（模型/回测 Tab 版本选择器）
- _v5State 增 version/versionOptions；v5VersionSelHtml() 共用选择器（默认=active，选项文本 `version_id (status)`，无数据版本 disabled+"（无数据）"后缀，选中历史版显示"历史版本"徽标）
- loadV5ModelQuant/loadV5BtlcQuant：quant/active 与 curves 追加 ?version=（v5QuantVersionQ()），并拉 version-options（btlc 仅在 available 时覆盖缓存）；sig 增 version+versionOptions
- renderV5Model：头部插选择器；isHist 时徽标换"历史版本"、说明行提示当前 active；renderV5Btlc：标题"历史版本回测"
- 切换→v5SetVersion→switchQuantTab(force)→两 Tab 联动，tab 间共享不重置

### 2.4 无头浏览器验证（google-chrome headless + CDP，Node22 内置 WebSocket 零依赖，脚本 /tmp/t0349-shots.js）
- 4 张截图存 shared/results/work/task-0349-shots/：t0349-v5model-v2btrr-{390x844,1440x900}.png、t0349-v5btlc-v2btrr-{390x844,1440x900}.png（110-202KB，内容实渲染非空白）
- 模型页选中 v2b_trr：select.value=v2b_trr ✓、徽标"历史版本"✓、scrollW=390=cw（390 宽口）/ 1425=cw（1440 宽口）→ 无横向滚动 ✓
- 回测页共享选择：标题"历史版本回测（v2b_trr）"✓、scrollW 同样无溢出 ✓
- 验证方式：showPage('quant')→switchQuantTab('v5model',true)→v5SetVersion('v2b_trr')，与真实用户操作路径一致
