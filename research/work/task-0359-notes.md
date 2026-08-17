# task-0359 笔记：单一事实源 + API 一致性自检（VPS dashboard）

## 现状勘察（2026-08-18 02:1x）

### 数据源地形（真源 = HP auto-sync 镜像到 VPS）
- active 指针：`workspace-quant/model/main.json` → **v5h_xsub**（quantActiveVersion()：main.json 优先，回退 manifest.active）
- manifest：`results/versions-manifest.json` generated_at 2026-08-17T18:00:02, active=v5h_xsub, **69 条（unique 68，v4b_mve1 重复×2）**
- registry 目录：`workspace-quant/model/registry/*.json` **48 个**（排除 .snapshot/.bak）；含旧周期 v1.1–v1.4 + v0_seed
- decision-log：`model/decision-log.jsonl` **59 行**（/api/quant/decisions 与 quantDecisionRecords 用）
  - ⚠️ 分叉：`results/model/decision-log.jsonl` 仅 **1 行**（seed_reset）——/api/quant/lifecycle 的主源！
- ledger：`results/experiment-ledger.jsonl` 36 行（34 行 IT/trial：有 type/run_id 键；2 行事件 ledger_reset/baseline_v0_seed）
- 旧 registry：`results/model/`（v0_seed.json version=v0_seed）→ gates/lifecycle 读它

### 现有 API 视角差异（已实证的不一致）
| API | active 来源 | 当前值 |
|---|---|---|
| /models /active /history /version-options | quantActiveVersion()（main.json） | v5h_xsub ✅ |
| /freshness | manifest.active | v5h_xsub ✅ |
| /gates | results/model/v0_seed.json | **v0_seed ❌** |
| /lifecycle registry.active | results/model/ 目录扫描 | **v0_seed ❌**（注释称旧周期仅计数参考） |
| /decisions | model/decision-log.jsonl | 59 行 ✅ |
| /lifecycle decisions | results/model/（1 行）→ 回退 model/ | 1 行 ❌ 分叉 |
| manifest 内部 | versions[] | **v4b_mve1 重复 ❌** |

### 关键代码坐标（server.js 694331B, 12994 行）
- 路由：gates@2831 models@2872 active@3090 version-options@3178 history@3235 history/:id@3282 freshness@3317 lifecycle@2526 decisions@2423 ledger@2495 baseline/summary@2676
- quantActiveVersion@~2641, quantBaselineResolve@~2648（v0_seed 硬编码兜底）, quantActiveProfile@~3055（metrics_source 已有：metrics-file/registry-backtest-refs/versions-manifest）
- 前端：getDashboardHTML@5896；量化 Tab 骨架@6619-6634（quantSeg + quantFreshness@6626）；_V5_TABS@8598（data/factor/v5model/v5btlc/v5hist）
- renderV5Model@8805（头卡）、v5VersionSelHtml@8734、renderV5HistList@9074、v5StatusBadge@9032、_v5State@8694
- loadQuantFreshness@8575、visibilitychange@8588、loadQuant@8724 区

### 实施计划（每步 ≤40 行，一改一验）
1. P1 后端：新增 /api/quant/consistency（freshness 路由后插入）——truth vs 各 API 视角 checks[]，severity: error/warn/info；consistent=无 error 级失败；status red/yellow/green；try/catch 降级
2. P2 前端：量化 Tab 顶部一致性状态点（点击展开明细）+ 30min 轮询 + visibilitychange 刷新
3. P3 后端：history/version-options/models 加 legacy 字段（/^v0_|^v1\./ 或 registered_at<2026-08）
4. P4 前端：history 列表 legacy 徽标 + 「隐藏 legacy」筛选 chip（服务端 ?hide_legacy=1 + 前端 toggle）；版本选择器 legacy 标注
5. P5 后端：quantBaselineResolve 显式版本未知时不再静默回退 v0_seed → available:false 数据缺失；baseline/summary 带 fallback 标记
6. P6 前端：模型页数据源角标（metrics_source）+ 指标缺失红色态
7. 验收：node --check、三态 curl、真数据一致性输出、截图 390/1440

## 执行日志
- 02:10 勘察完成，上述坐标与不一致清单已落盘

## 执行日志（续）
- 02:18 P1a+P1b 完成：/api/quant/consistency 上线，真数据实测 **status=yellow**：
  - warn×3：① /gates 内部读值 v0_seed ≠ main.json v5h_xsub（旧周期滞后）② manifest v4b_mve1 重复 ③ decision-log 分叉 model/59行 vs results/model/1行（lifecycle 主源）
  - error 级全过（active 指针/models/registry 档案/台账自洽/镜像新鲜度 19min）
  - truth 输出：active=v5h_xsub, registry=48, manifest=69, decisions=59, ledger IT=34/36
- 02:22 P2 完成：量化 Tab 顶部一致性状态点（quantConsistDot + quantConsistDetail 明细表 + toggleQuantConsist），30min setInterval + loadQuant/visibilitychange 双钩子；服务已重启，HTML 含 8 处新元素/函数引用

## 执行日志（续2）
- 02:24 P3 完成：quantIsLegacyVersion()（/^v0_|^v1[._a-z]/ 前缀或 created_at<2026-08）；history items/version-options/models pushVersion/history 详情 4 处加 legacy 字段；history 支持 ?hide_legacy=1（默认关，保 active 不隐藏）+ hidden_legacy 计数回显。实测：69 版中 12 个 legacy（v0_seed + v1a~v1k）；hide=1 → 68 版
- 02:25 P4 完成：前端 v5LegacyBadge()（灰虚线徽标）+ v5ToggleLegacy() 开关 chip + 「已隐藏 N 个旧周期版本」提示 + 列表/详情徽标 + 版本选择器选项 ' · legacy' 后缀；_v5State.hideLegacy 默认 true
- 02:26 P5 完成：quantBaselineResolve 显式未知版本 → {missing:true} 不再静默回退 v0_seed；baseline summary/nav/yearly 三路由均降级 available:false+note（source:'missing'）。实测 v99_ghost→数据缺失 / 无参→v0_seed 合法默认 / v5h_xsub→正常
- 02:27 P6 完成：模型页头卡「数据源:」角标（镜像 metrics 文件=绿 / registry 内嵌=黄 / manifest 内嵌=黄 / 指标全缺=红「数据缺失」），title 注明回退链
- 02:27 三态测试（沙箱副本 8099 端口，路径重定向 /tmp，不碰真数据）：
  - 正常态（8055 真数据）：status=yellow（warn×3 如实列出，error 级全过）
  - 缺文件态：status=red（active 版本无 registry 档案=error；manifest 缺失→freshness warn）
  - 空目录+陈旧指针态：status=red，active=vX_test_missing，4 项失败逐条列出
- 02:29-02:30 截图（google-chrome headless + CDP，task-0349 同法）7 张存 shared/results/work/task-0359-shots/：
  - v5model 390/1440（状态点「● 镜像延迟」+「数据源: 镜像 metrics 文件」角标）
  - consist-detail 1440（9 项检查表展开）
  - v5hist-p4-legacy 390/1440（第 4 页 7 行 legacy 徽标）+ v5hist-legacy 390/1440（默认隐藏态）
  - 横向滚动检查：390 宽 sw=cw=390、1440 宽 sw=cw=1425，均无横向滚动 ✅
- 02:31 回归：16 个 quant API 端点全 200（含旧 gates/lifecycle/registry 不动）；node --check 通过；备份 server.js.bak-a103-20260818 存在
- 沙箱/Chrome 进程已清理，8099 端口释放

## 交付清单
- 改动：server.js 单文件（694331B → ~707KB），6 个小补丁，每补丁 node --check+curl 验证
- 新 API：/api/quant/consistency（consistent/status/truth/checks[]，含 severity 分级）
- 前端：一致性状态点+明细、legacy 徽标+筛选、数据源角标
- 已知遗留（如实报告，不在本任务范围）：/gates 与 /lifecycle 仍读旧 results/model（旧端点保留防断链，consistency API 已将其滞后显式化为 warn 项）；manifest v4b_mve1 重复（HP 侧生成问题，自检已捕获）；decision-log 双路径分叉（model/ 59 行 vs results/model/ 1 行，自检已捕获）
