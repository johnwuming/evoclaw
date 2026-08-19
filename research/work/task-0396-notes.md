# task-0396 paper_engine ranksum 适配笔记

开始时间: 2026-08-19 15:07 (GMT+8) | 重试时间: 15:40 (上次尝试超时中断, 探索结论已恢复)
目标: paper_engine 识别 ext_mode=ranksum/raw_universe，与 a9_ranksum_raw 回测口径对齐并做等价校验

## 一、探索结论（已核验，来自 HP 实查）

### 1. 文件位置
- paper_engine.py: `~/quant-evolve/scripts/paper_engine.py`（51789B, 有 .bak_task0352 / .bak.20260818n）
- 回测补丁: `~/quant-evolve/scripts/a9_common.py`（17914B）— patch_engine()
- 候选批: `scripts/a13_run.py`（5677B）
- registry: `model/registry/a9_ranksum_raw.json`；main.json 已激活为 a9_ranksum_raw（params 已含 ext_mode=ranksum）

### 2. registry/main.json 参数（a9_ranksum_raw，已确认）
```
sort=ext, ext_mode=ranksum
ext_specs=[("log_mv",1.0,-1), ("amt20",1.0,-1), ("pb_inv",0.7,1.0), ("roe",0.3,1.0)]
ext_filter_all=1, raw_universe=1, e1_guard=1, xsub_days=365.0, n_hold=20
div_min=0.02, roe_min=0.15, roa_min=0.10, price_cap=10.0, min_amt=0.0
```
- 择时: q3z×EW-MA200（影响仓位系数，不影响选股 target 集合）——选股等价只比 target 集合

### 3. a9_common.patch_engine 语义（回测侧，等价目标）
- **PA raw_universe**: 四闸门(div/roe/roa/price_cap)整体可关，仅要求有效价格(>0, 非NaN)
- **PB ext 分支**: ext_mode in (zscore, ranksum)；ext_specs=[(factor,weight,sign),...]
  - _fval 因子取值: circ_mv/log_mv(ln circ_mv>0)/pb_inv(1/pb, pb>0)/roe(roe_ttm)/amt20(amt.loc[:d].tail(20).dropna(), 需≥10样本且mean>0)/amihud20
  - ext_filter_all=1 → 所有 spec 因子都必须非缺失(含权重0因子)
  - ranksum: tr = col.rank(pct=True)；zscore: (x-mean)/std(std>0)
  - score = Σ weight*sign*tr；e1_lambda>0 时 score -= lam*|clip(ret120,-1,0)|(e1_deadzone死区变体)
  - **ranked = sorted(_score.items(), key=lambda kv: -kv[1])** → 降序, 取前 n_hold
- **PC e1_guard**: closes.loc[:d] len>=121 时 r120=close[-1]/close[-121]-1 < -0.30 → 剔除（不足121条保留）
- **PC xsub_days**: (d - first_last[code][0]).days < N → 剔除（first=K线首日）
- **PD pb 列**: panel 需 merge pb（PIT）
- 引擎选择循环顺序: fund(panel date<=d tail1) → code in closes → 四闸门(PA) → ST/susp → first_last → min_amt → e1_guard/xsub → ext 排序

### 4. 数据/口径关键差异（paper 老路径 vs 回测，必须在新分支修复）
| 项 | 回测引擎 | paper 老路径 | 影响 |
|---|---|---|---|
| 宇宙 | q4b: 主面板+**退市面板**(fundamentals_delisted_monthly) concat；退市股K线用 HFQ_DIR hfq+raw缩放 | 仅 FUND_PANEL 主面板, K线仅 all_stocks_qfq | 退市股缺失→宇宙偏窄 |
| 价格日 | 必须**恰好有 d 当日K线行** `d in closes[code].index` | 取 last row <= d（允许陈旧价） | 停牌股口径差 |
| 停牌 | susp = (vol<=0)\|NaN 在 d 剔除 | 无 susp 检查 | 停牌股会误入 |
| ST 源 | st_history_ranges.csv(多区间取并集) | stock_info.csv 快照(单区间) | ST 口径差 |
| amt20 | amount.replace(0,NaN) 后 tail(20).dropna() | 原始 amount 不去0 | 零成交行口径差 |
| 最小K线 | len(df)<20 的 code 整只剔除(不入 closes) | 不检查 | 边缘股口径差 |
| pb | ths_ttm_panel equity, avail_date(披露日) as-of merge_asof backward, pb=circ_mv/equity, 逐面板行 | 无 | 必须补 pb PIT merge |

### 5. 等价参照物
- `results/a9_ranksum_raw_full_holdings.csv`（249 行, 列: date,num_target,num_held,target,held,...）target 为 pipe 分隔选股代码串
- 最近含 target 的调仓日: **2026-06-01, 2026-07-01, 2026-08-03**
- a7_v5h_xsub_formal_full_holdings.csv 存在（可做老路径回归参照）
- 数据时点: 回测 2026-08-17 跑, store@2026-08-17, kline_as_of 2026-08-10；面板 mtime 未变；qfq 复权重算不影响 ranksum 因子(逐股常数缩放对 r120/amt 不敏感, log_mv/pb/roe 来自面板)

### 6. paper_engine 结构
- select_target_codes(rebalance_date, model) @L402: 老路径(闸门+ST+price_cap → v5h rules 层 e1/xsub/limup/amt20 → circ_mv 排序)
- load_main_model() @L176 读 model/main.json（params 已含 ext_mode=ranksum）
- select_target_codes 调用点: L820(action_init), L959(action_rebalance), L1135/L1139(shadow), L1217(action_timing)
- HP 内存: 15G total, ~10G free（kline 缓存可行但按纪律单日期单进程更稳）

## 二、实施计划
1. 备份 paper_engine.py → scripts/paper_engine.py.bak_task0396_YYYYMMDD
2. 新增函数(置于 select_target_codes 前): `_load_st_bt()`(st_history_ranges 并集), `_load_panel_bt()`(主+退市面板+pb PIT merge, 模块缓存), `_load_kline_bt(code)`(qfq→hfq 回退), `_select_ext_rank(rebalance_date, p)`(完整 ranksum/zscore+raw_universe 语义)
3. select_target_codes 顶部 dispatch: 仅当 sort==ext 且 (ext_mode==ranksum 或 raw_universe=1) → 新分支；否则老路径原样(零回归)
4. py_compile + 等价校验脚本(逐日期跑, 对比 a9_ranksum_raw_full_holdings.csv target) + 老路径回归(比 a7_v5h_xsub_formal)
5. 写 .task-completions.jsonl
