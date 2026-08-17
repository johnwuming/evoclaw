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
