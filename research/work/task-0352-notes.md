# task-0352 工作笔记（边查边写恢复点）

目标: paper_engine 补 e1/xsub/limup 规则层 + v5h 等价校验 + 看板标注 + 产物链修绿

## 2026-08-17 23:40 前置勘察（HP）

- `scripts/paper_engine.py` 45897B；`grep -cE "e1_guard|xsub|limup"` = **0**（未实现，坐实 D-20260817-A7-02）
- `model/main.json` version=**v5h_xsub**，params 已声明: `sort=ext, ext_factor=low_amount, ext_weights=[1.0,0.0], e1_guard=true, mom_cols=[ret120], xsub_days=365.0` —— paper_engine.select_target_codes 只读 n_hold/div_min/roe_min/roa_min/price_cap/sort，**忽略其余参数**
- 回测引擎语义源: `scripts/a9_common.py` patch_engine（a5_runner.py 已清理，a9_common 为等价复刻，a9_sel.py S2 stage 已验证 a9 引擎 ≡ a7_v5h_xsub_formal）
  - e1_guard: 买入日 s=as-of closes; len(s)<121 保留；r120=close[-1]/close[-121]-1 < -0.30 剔除
  - xsub_days: (d - first_last[code][0]).days < 365 剔除（first=K线首日）
  - lim_filter（v5g 语义, cfg 守卫默认关）: 近21根K线内涨停计数>3 剔除；涨停判定 pct>=th-1e-4, th=ST 5%/主板 9.8%
  - v5h CFG: `ext_mode=zscore, ext_specs=[("amt20",0,-1),("circ_mv",1,-1)], ext_filter_all=1, e1_guard=1, xsub_days=365`
  - amt20 定义: 近20日 amount 均值, 需 ≥10 个非NaN 且 mean>0, 否则 NaN；ext_filter_all=1 → 权重0因子NaN也剔除
  - 单因子 zscore(circ_mv,-1) 降序 ≡ circ_mv 升序；backtest 中 NaN circ_mv 被剔除（filter_all）
- kline parquet 列: date/open/high/low/close/volume/amount/... 数据至 2026-08-14
- main.json 四闸门参数未声明 → DEFAULT_PARAMS: div_min=0.02/roe_min=0.15/roa_min=0.10/price_cap=10/n_hold=20（与 v5h 回测 cfg 一致, metrics.json 证实）
- LIMIT_UP_PCT=0.098 / ST_LIMIT_UP_PCT=0.05 已在 paper_engine 定义；is_limit_up()/is_st_on() 已存在

## 修改方案（paper_engine.select_target_codes）

规则层插在 target 构建后、排序前：
1. e1_guard: kd>=121 → r120<-0.30 剔除（不足121条保留，对齐 a9）
2. xsub_days>0: (rd-first).days < xsub_days 剔除
3. limup_max（默认 None=off）: 近21根涨停计数>limup_max 剔除（引擎支持位，v5h 不开）
4. ext 模式（sort=="ext"）补 amt20 过滤（≥10/20日, mean>0）+ circ_mv 非NaN 剔除（对齐 ext_filter_all=1）

## 23:50-00:05 完成点

1. **paper_engine 规则层**: 已打补丁（备份 scripts/paper_engine.py.bak_task0352, 45897B）；py_compile 过；grep -cE "e1_guard|xsub|limup" = 18 ≥3 ✅
   - e1_guard（不足121条K线保留）、xsub_days、limup_max（默认off）、ext模式amt20过滤+circ_mv非NaN
2. **等价校验 EQUIV_DIFF0**: 3/3 对齐日（2026-06-01 / 07-01 / 08-03）持仓清单 diff=0 ✅
   - 产物: HP results/paper_v5h_equiv_check.json（verdict=EQUIV_DIFF0, model=v5h_xsub）
   - 坑1: holdings.csv target 列是 `|` 分隔（首跑误用 `,` 造成假 MISMATCH）
   - 坑2: HP 内存仅剩 ~2G（openclaw 主进程 99.9% CPU 跑 task-0353），pyarrow 并发读偶发 "Corrupt snappy"；用 pq.read_table(use_threads=False, memory_map=False)+retry6x 解决
3. **看板标注**: server.js 已备份 server.js.bak_task0352 并加 rules_align 字段（/api/quant/paper/summary 返回 status: aligned/diff/unknown + note）；paper 页 quant-desc 上方徽标 + 模型页主模型行 chip；agent-dashboard 已 restart，API 已验证返回 rules_align ✅
4. **run-status 7红灯根因**: dashboard 读 workspace-quant/results（QUANT_REPORTS_DIR），auto_sync_notify.py 的量化镜像 include 只放行 seedB_*/q4b*/回测小文件 → baseline-paper-*/risk-status/crowding/timing_layer_prod 从不镜像 → 7 项 exists:false 全红（registry 绿）
   - 已修: auto_sync_notify.py MIRROR_INCLUDES 补 baseline-paper-*/risk-status.json/crowding-indicators.json/timing_layer_prod.json/paper_v5h_equiv_check.json（备份 .bak-task0352-20260817, py_compile 过）；手动跑镜像: baseline-paper-validation.json 已落 workspace-quant/results
   - 上游缺口: HP results/ 本身缺 risk-status/crowding-indicators/timing_layer_prod/baseline-paper-nav|trades|summary（何时被删待查，producer 脚本都在: risk_patrol.py/collect_crowding.py/timing_layer_prod.py，paper_engine 产物需 init）
   - paper_engine cron 被 PAUSED-20260816-seedB（用户决策，不碰 crontab）→ 我做一次性再生 + 建议用户恢复 cron

## 待办
- [ ] HP 一次性再生: timing_layer_prod refresh / collect_crowding / risk_patrol / paper_engine init+daily
- [ ] 镜像后再核对 run-status 全绿
- [ ] decision-log D-20260817-P02 + completions

## 00:20 收尾（全绿）

### 验收逐项
1. ✅ 规则层: grep -cE "e1_guard|xsub|limup" paper_engine.py = 18（≥3）；py_compile 过；备份 scripts/paper_engine.py.bak_task0352（45897B 原始版）
2. ✅ 等价校验 EQUIV_DIFF0: 2026-06-01 / 07-01 / 08-03 三对齐日持仓 diff=0（HP results/paper_v5h_equiv_check.json）
3. ✅ 看板标注: /api/quant/paper/summary → rules_align.status=aligned(3月)；paper 页徽标+模型页 chip（server.js.bak_task0352 备份；agent-dashboard restart 完成）
4. ✅ run-status 8/8 绿（paper_nav/trades/summary 0.1h、validation 20.3h、risk/crowding 0h、timing_prod 0.3h、registry 50.5h）
5. ✅ decision-log 尾行 D-20260817-P02；completions task-0352

### 关键修复链
- 红灯根因: auto_sync_notify.py 量化镜像 include 未覆盖 paper 产物 → 已补 5 类 include（备份 .bak-task0352-20260817）
- HP results/ 曾缺 risk-status/crowding/timing_layer_prod/i3_abs_s1_nav/baseline-paper-*（producer 均在）：timing_layer_prod --refresh、collect_crowding(attempt2)、risk_patrol(需从 shared 回填 i3_abs_s1_nav.csv track record)、paper_engine init+daily 一次性再生成
- HP 高内存压力(可用~2G, 同机 task-0353 openclaw 99.9%CPU)下 pyarrow 并发读偶发 Corrupt snappy / segfault / pyc marshal 损坏：paper_engine load_kline+面板读取永久加固(单线程+重试)；重试循环通过；__pycache__ 清理
- crowding 手动首跑 segfault→attempt2 成功，无需回填

### 残留与提示（需用户决策/后续）
- paper_engine cron 仍 PAUSED-20260816-seedB（用户决策未动）：36h 后 baseline-paper-nav/trades/summary 将转黄→红（red line 禁改 crontab）。建议: 恢复 cron 或将 run-status 三项指向 paper_trade 活跃产物
- risk_patrol cron 16:45 UTC 依赖 results/i3_abs_s1_nav.csv（已回填）；HP results/ 曾被清理的原因未深挖（不在本任务范围）
- collect_crowding 周日 cron 在内存压力下可能 segfault，建议错峰或限内存（后续任务）
- 看板旧实例: 8053/8056 端口两个 node server.js 僵尸进程（8月11/15 起），未动（非本任务范围）
