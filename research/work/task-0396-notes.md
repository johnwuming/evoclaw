# task-0396 paper_engine ranksum 适配笔记

开始时间: 2026-08-19 15:07 (GMT+8) | 完成时间: 2026-08-19 ~10:15 (HP)
目标: paper_engine 识别 ext_mode=ranksum/raw_universe，与 a9_ranksum_raw 回测口径对齐并做等价校验

## 一、探索结论（已核验，来自 HP 实查）
### 1. 文件位置
- paper_engine.py: `~/quant-evolve/scripts/paper_engine.py`（改前 51789B → 改后 63167B, 1298→1584 行）
- 回测补丁: `scripts/a9_common.py`（patch_engine: PA raw_universe / PB ext 排序 / PC e1_guard+xsub / PD pb 列 / PE2 e1_lambda）
- 候选批: `scripts/a13_run.py`；registry: `model/registry/a9_ranksum_raw.json`
- main.json 曾被并发改为 a13_rsraw_e1f10dz（e1_guard=0, e1_lambda=1.0）→ 校验一律从 registry 读参数，不依赖 main.json 激活态

### 2. a9_ranksum_raw 参数（registry, 等价基准）
```
sort=ext, ext_mode=ranksum
ext_specs=[("log_mv",1.0,-1), ("amt20",1.0,-1), ("pb_inv",0.7,1.0), ("roe",0.3,1.0)]
ext_filter_all=1, raw_universe=1, e1_guard=1, xsub_days=365.0, n_hold=20, min_amt=0
```
- 择时(q3z×EW-MA200)只影响仓位系数, 不影响选股 target 集合

### 3. 回测语义（a9_common.patch_engine, 对齐目标）
- raw_universe: 四闸门(div/roe/roa/price_cap)整体可关, 仅要求有效价格>0
- ext 分支: ranksum → col.rank(pct=True); zscore → (x-mean)/std; score=Σ w*sgn*tr; ranked 按 -score 降序取前 n_hold
- ext_filter_all=1 → 所有 spec 因子非缺失(含权重0因子)
- e1_guard: len>=121 时 r120<-0.30 剔除; xsub_days: (d-first_date).days<N 剔除
- amt20: _a.loc[:d].tail(20).dropna() 需≥10样本且mean>0（**最近20日**, 非全历史）
- pb: ths_ttm_panel equity avail_date(披露日) merge_asof backward 行级对齐, pb=circ_mv/equity(>0)

### 4. 关键口径差异（老路径 vs 回测, 新分支已修复）
| 项 | 回测 | 老路径 | 新分支 |
|---|---|---|---|
| 宇宙 | 主+退市面板 concat | 仅主面板 | ✅ 主+退市 |
| 价格日 | 必须恰有 d 当日行 | last<=d 允许陈旧 | ✅ 恰有 d |
| 停牌 | vol<=0\|NaN 剔除 | 无 | ✅ 有 |
| ST 源 | st_history_ranges(并集) | stock_info 快照 | ✅ st_history_ranges |
| amt20 | tail(20).dropna() | 全历史 | ✅ tail(20) |
| 最小K线 | len<20 整只剔除 | 无 | ✅ len<20 剔除 |
| pb | PIT merge | 无 | ✅ PIT merge |

## 二、实现（scripts/paper_engine.py, diff=268 行纯新增, 0 行修改）
- 新增常量: PANEL_DEL / HFQ_DIR / DELISTED_IDX / ST_RANGES_CSV / THS_TTM_PANEL
- 新增函数: `load_st_bt()`(ST并集) / `load_kline_bt(code)`(qfq→hfq 回退) / `load_mkt_bt()`(主+退市面板+pb PIT merge, 模块缓存) / `_ext_factor_value()`(引擎 _fval 同款因子) / `select_target_codes_ext(rebalance_date, p)`(完整 PA/PC/PB/PD 语义)
- select_target_codes 顶部 dispatch: 仅当 sort==ext 且 (ext_mode in ranksum,zscore 或 raw_universe=1) → 新分支; 否则老路径原样
- 备份: `scripts/paper_engine.py.bak_task0396_20260819`

## 三、等价校验（paper vs a9_ranksum_raw_full_holdings.csv target 逐位）
```
date        n_ref  n_paper  SET_MATCH  ORDER_MATCH  missing  extra   elapsed
2026-06-01   20     20       True       True          0        0       60.2s
2026-07-01   20     20       True       True          0        0       60.1s
2026-08-03   20     20       True       True          0        0       60.1s
```
- 集合+顺序均逐位一致（rank 含 tie 顺序一致）。universe=5331(主+退市)
- 中间发现: 首版 amt20 用全历史均值 → 三日期各缺/多 10-13 只; 修复为 tail(20) 后全部一致

## 四、回归检查（老路径不受影响）
```
A circ_mv_asc 老路径      n=11 (2026-08-03, 闸门+ST 过滤后, 正常)
B v5h 老布尔 ext 路径     n=10 (无 ext_mode → 老路径, 正常)
Bz v5h zscore 新分支      n=10 集合与 B 完全一致 (交叉验证新分支语义)
diff 备份 vs 新版: 268 行新增(>), 0 行修改(<) → 只增不改确认
```

## 五、结论
- ✅ paper_engine 在 ext_mode=ranksum+raw_universe 下选股与 a9_ranksum_raw 回测 target 逐位一致(3 调仓日验证)
- ✅ circ_mv 老路径回归不受影响（代码 0 修改, 功能实测正常）
- ✅ py_compile 通过; 新分支读 registry 参数, 不依赖 main.json 激活态
- 交付物: paper_engine.py(修改) + paper_engine.py.bak_task0396_20260819(备份) + scripts/t0396_equiv.py(校验脚本) + scripts/t0396_regress.py(回归脚本)
- 未恢复 rebalance cron（保持 PAUSED, 恢复另定）
- 备注: main.json 激活态为 a13_rsraw_e1f10dz（非任务范围, 记录供参考; 恢复 a9_ranksum_raw 属 task-0394 域）
