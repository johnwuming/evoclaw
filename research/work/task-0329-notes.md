# task-0329 过程笔记

## 目标
1. versions-manifest 去硬编码（HP 生成 → VPS 消费）
2. models API 合并 manifest + registry 扫描
3. auto_sync_notify.py 加 --push-now
4. freshness API + 前端新鲜度提示 + 版本下拉动态渲染
5. HP 部署验证

## 勘察记录

(待填)

### 勘察结论（2026-08-16 23:45）
1. server.js 644KB。版本映射实为 `QUANT_BASELINE_VERSIONS`（L2812 附近，v0_seed→seedB_v0），resolve 函数 `quantBaselineResolve`。
   - baseline summary/nav/yearly/meta 都走 `${prefix}_${window}_*.json|csv` 于 QUANT_BASELINE_DIR=/root/.openclaw/workspace-quant/results
   - meta 读 QUANT_BASELINE_REGISTRY_DIR=results/model/{version}.json（仅 v0_seed 存在）
2. models API（L3008）：扫 MODEL_REGISTRY_DIR=workspace-quant/results/model（仅 v0_seed.json + archive-cache.json），activeId 硬编码 'v0_seed'。**新 registry 实际在 /root/.openclaw/workspace-quant/model/registry/（VPS 29 文件含 .snapshot/.bak）**
3. HP 侧：results/ 44 个 *_metrics.json，模式 {tool}_{version}_{full,locked}_metrics.json（tool=a2/a2b/a2c/seedB，version=v1i_q3z/v2b_trr/…）+ 配套 nav/yearly csv
   - HP model/registry/ 21 文件；**registry JSON 含 backtest_refs 字段直接指向 results 文件（如 results/a2c_v2b_trr_locked_metrics.json）→ 生成脚本可零启发式取 prefix**
   - registry 结构：{version_id, status, created_at, main_alias, selection{strategy,params,...}, timing, backtest_refs{metrics_full, baseline, endtoend, metrics{...}, eval_window}, gate, activated_at}
   - HP model/main.json: version=v2b_trr（现役）
   - a2c_v2b_trr_locked_metrics.json: ann=0.1515 mdd=-0.2986 sharpe=0.9356 calmar=0.5074（验收锚点✓）
4. auto_sync_notify.py 20KB 555 行：main() 顺序 = 可达检查 → Step1.5 通知转发 → Step1.5 model/ rsync（→workspace-quant/model/）→ Step2 列文件 → Step4 rsync 主同步 → Step4.5 mirror_quant_results（MIRROR_INCLUDES 仅 seedB_*/q4b*）→ Step5 状态 → Step6 通知。已有 ssh_exec()/do_rsync() 可复用。
5. VPS workspace-quant/results/ 现只有 seedB_v0_* + q4b/ + model/。a2c_* 未镜像 → mirror includes 需扩展 *_metrics.json/*_nav.csv/*_yearly.csv/versions-manifest.json。

### 设计决定
- gen_versions_manifest.py（HP）：以 model/registry/*.json 为主源（backtest_refs 取 prefix，读 metrics 文件嵌 windows），再扫 results/ 未覆盖的 {tool}_{version}_{full,locked}_metrics.json 作 status=backtest-only；active=model/main.json.version
- VPS baseline：manifest 优先（version→prefix 映射 + windows 内嵌指标兜底），VERSION_MAP 降级兜底；summary 缺文件时用 manifest.windows
- models：active=workspace-quant/model/main.json 指针；versions 合并 新registry/*.json + manifest + 旧 results/model/v0_seed + archive-cache
- mirror includes 扩展：--include=*_[fu]ll_metrics.json 等三类 + versions-manifest.json
- freshness：generated_at + last_sync + 关键文件 mtime
- --push-now：ssh 重生成 manifest → rsync manifest+model/ 四类小文件 → 不动状态/通知

### server.js 改动清单（23:55 完成初版，node --check 通过）
1. resolve/manifest：新增 QUANT_MANIFEST_PATH/QUANT_MODEL_REGISTRY_DIR/QUANT_MODEL_MAIN + loadQuantManifest()/quantActiveVersion()；quantBaselineResolve manifest 优先（带 manifest_windows），VERSION_MAP 兜底保留
2. baseline/summary：镜像文件缺 annual_return 时用 manifest.windows[win] 兜底（meta.source 标注）
3. baseline/meta：双 registry 路径（旧 results/model 优先 → 新 model/registry），caliber 从 selection.params 补 cost_model/limit_board
4. /api/quant/models 重写：active=main.json 指针（回退 manifest.active→v0_seed）；versions 合并 model/registry/*.json（新）⊕ manifest ⊕ 旧 v0_seed ⊕ archive-cache，去重，active 置顶
5. 新增 /api/quant/freshness：generated_at/last_sync/versions_count/files mtime
6. 前端：基线卡加版本下拉（_baselineVersion/_baselineVersionList，models API 动态渲染）；quantSeg 下加 quantFreshness 小字条（HH:MM，HP UTC→补 Z 转换）；visibilitychange → 仅 screen-quant 可见时刷新当前子Tab（sig 守卫）+ freshness + 失效版本清单缓存；loadQuant() 启动调 loadQuantFreshness()
7. 备份：server.js.bak-task0329-20260816-234526

### 验证结果（00:05 全部通过）
1. node --check server.js ✓ | systemctl is-active agent-dashboard = active ✓ | ast.parse(auto_sync) ✓
2. HP results/versions-manifest.json：active=v2b_trr，n=22，generated_at=2026-08-16T16:00:02（cron Step0.9 自动重生成）✓
3. baseline/summary?version=v2b_trr&window=locked → ann=0.1515 mdd=-0.2986 sharpe=0.9356 calmar=0.5074（已读镜像文件 a2c_v2b_trr_locked_metrics.json，非 manifest 兜底）✓
4. models → v2b_trr & v1i_q3z in versions，len=26（19 model/registry + 7 manifest-only；archive-cache v1.1-1.4 被新 registry 去重）✓
5. freshness → ok:true，generated_at + last_sync 都在 ✓
6. CDP /tmp/task0329-quant.png（232KB）：DOM 确认基线卡下拉 26 项含 v2b_trr★在役/v1i_q3z，顶部新鲜度「🔄 数据更新于 23:51（registry/结果） · 同步 23:30 · 22 版本」，locked 指标 年化15.15%/回撤-29.86%/夏普0.936/Calmar0.507/累计1256%/月胜率59.7%，口径 v2+一字板+审计锁 ✓
- 空态：?version=unknown_xyz → HTTP 200，回退 v0_seed（0.2626/-0.6949）不 500 ✓；lifecycle HTTP 200 未改 ✓
- diff 30 hunks 全在预期区域（baseline/models/freshness/前端/HTML/JS），gates/dsr/q4b-contrast/lifecycle 未触碰 ✓
- auto_sync 常规 cron（00:00）正常：Step0.9 manifest 重生成 → 128 文件扩展镜像（含 a2c_* metrics/nav）→ 状态/通知正常 ✓；--push-now 独立入口测试通过（不动 .sync-state）✓
- 改动文件：server.js（原地，备份 server.js.bak-task0329-20260816-234526）、auto_sync_notify.py（原地，备份 .bak-task0329）、HP ~/quant-evolve/scripts/gen_versions_manifest.py（本地副本 shared/results/work/gen_versions_manifest.py）
