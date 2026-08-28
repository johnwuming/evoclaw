# task-0550 PhaseA 跟踪条件处置 — 过程笔记

开始时间: 2026-08-29 02:27 GMT+8
任务: ①roe/roa 补验(只读核验) ②卖出跌停闸方案起草 ③DIV_EVENTS 接线方案起草
约束: HP 只读; ②③只出方案不改代码; 在役零改动

## R-345 关键事实（§二/§五/§七/§九）
- A1 残留补验项: fundamentals_monthly.parquet (roe_ttm/roa_ttm/div_yield_ttm 过滤通道) 构建器 = scripts/fetch_valuation_data.py（+ prep_dividend_roa.py）; grep lag/shift/avail/as_of 命中0; panel 无 avail_date 列; a13 因子含 roe 0.3 权重。若发现报告期直落 → a13 roe 通道历史结论需重新定性（绝对阻塞复评）。
- A4 缺口: paper_engine.py 卖出侧无跌停禁卖闸（grep limit_down=0）; L949 is_limit_up (pct>=阈-1e-4, ST 分阈) + L1251 买入前硬闸; 历史 0 笔卖出未行使。
- A6 缺口: paper_engine.py L61 定义 DIV_EVENTS, 全文件仅 1 处引用（加载未接线）; dividend_events.parquet 48081 行; 持有窗口 0 命中（4 个代码级疑似全在窗口外, 601600 恰除息日当天买入不享有）。
- 附加条件②: 两缺口修复立修复项, 不自动修。

## 编号与产物
- R-351 未占用（R-350 为最新）。
- 报告: R-351-PhaseA跟踪条件处置.md; notes: work/task-0550-tracking-notes.md

## R-343 方法论要点
- 核验方式: 逐行代码核验, 证据=文件绝对路径+关键行号+对齐机制引文
- 判定标准: ①信号=f(t 月末及以前信息); 收益归属月=t+1 (shift(1)); ②财务数据必须按披露日 avail_date as-of join, 报告期直 join=前视
- 天然免疫结构: 「月末因子值 × 次月收益」
- 反例症状: 同月对齐 → 信号"躲过下跌首月", 熊市 MDD≈0
- G0 双层校验: Part A (E2 复现 E1) + Part B (E1 实现 vs 声明口径独立复算)

## 检查点 1: HP 勘察开始 (02:35)

## 检查点 2: ①roe/roa 构建器核验 (prep_dividend_roa.py, 396行)
- 真正构建器 = prep_dividend_roa.py（fetch_valuation_data.py 只读该面板用于行业PE, L41/L380）→ 解释 R-345 grep 未命中（查错文件+实现不用 shift/asof 关键词）
- L195-206 disclosure_available(): 报告期→法定披露截止日映射 (Q1→4/30, 中报→8/31, Q3→10/31, 年报→次年4/30) — 保守(截止日), PIT 安全方向
- L252: fin["avail_date"]=report_date.map(disclosure_available)
- L275-343 面板构建: date=MonthEnd(收盘取当月最后交易日); div_yield_ttm=searchsorted ex_date∈(mend-365d, mend] 累计/c月末 — 无前视
- L344-380 PIT join: bisect_right(av_dates, d)-1 → 只取 avail_date ≤ 月末d 的最后一条 roe/roa — 真 as-of backward, 无报告期直 join
- 边界: d==avail_date 当日即用（法定截止日收盘前必须披露, 安全）; drop_duplicates keep=last
- 初步结论: 构建器无前视。待查下游消费对齐。

## 检查点 3: ①下游消费链核验 (闭合)
- a13_run.py L22-31: load_engine() → backtest_dividend_quality_iter.py + patch_engine(a9_common)
- backtest_dividend_quality_iter.py L187-190: panel 排序; L389-390: fund = panel[panel.date <= d].groupby("code").tail(1).set_index("code") — 调仓日 d 向后 as-of 取快照, 无前视
- L250: rebalance_dates = 每月首个交易日 (groupby(M).min()) → 信号(≤上月末信息) → 次月首日执行, 标准 shift 结构
- a9_common.py L49-73 (PA 闸门): fund.loc[code,roe_ttm/roa_ttm/div_yield_ttm] 过滤; L155-156 roe 因子取 tdf(目标持仓,来自同一 fund 快照); pb_inv 经 merge_pb_into_panel (R-345 已验 L237-249 as-of)
- q4b_build_delisted_panel.py L15: 退市镜像 statYear 数据 (year+1)-05 生效, 面板date=生效月末日 — 更保守, PIT 安全
- ①总结论: **roe/roa 过滤通道构建器+消费链全链路无前视**。构建器=prep_dividend_roa.py(R-345 误指 fetch_valuation_data.py, 该文件只读不写); 披露日用法定截止日映射(保守方向); as-of 用 bisect/searchsorted(故 R-345 grep lag/shift/avail/as_of 未命中)。精确性瑕疵均为"滞后"方向(截止日晚于实际披露/月末归一), 无一"领先"方向 → a13 roe 通道历史结论**无需重新定性**, Phase B 影子层消费放行。

## 检查点 4: ②卖出路径证据 (paper_engine.py, 1759行)
- L1433-1441 sell_list 构建: 不在目标/ST/get_price=None
- L1442-1455 清仓卖出: price=get_price(d) or cost; fee=comm+印花; del holdings — 无跌停检查
- L1460-1492 timing 减仓: 同样无跌停检查
- L1499-1502 买入闸: is_limit_up 硬闸(对照)
- L949-963 is_limit_up: pct=cur/prev-1, th=ST?0.05:0.098, 容差-1e-4, qfq close
- L965-975 get_price: qfq kline 最近收盘 ≤d
- L286 load_kline: KLINE_DIR/{code}_daily_qfq.parquet
- L97-98: LIMIT_UP_PCT=0.098 / ST_LIMIT_UP_PCT=0.05
- L905-925: 选股侧 limup_max 近21日涨停计数过滤(另一处掩码)
- grep -c limit_down = 0 (确认 R-345)
- 持仓结构: {"shares":int,"cost":float,"buy_date":str}

## 检查点 5: ③DIV_EVENTS 证据
- L61 定义, grep 全文件仅此 1 处 (确认 R-345 L100)
- dividend_events.parquet: 559KB, mtime 2026-08-13 03:30 (与面板同次构建); crontab 无自动刷新
- data_validator.py L33-34 引用 FUND_PANEL+DIV_EVENTS (调仓前校验已触碰该文件)
- action_daily L1312+: 每日 NAV, 缺口回填循环逐日 holdings_value_at+append_nav → 分红挂点
- action_rebalance: 卖出块在 L1442 起 → 分红需在卖出前处理(除息日当日卖出仍享有, T-1 收盘持仓即享有)
- state 无 last_div 字段; 现有 state: holdings/cash/created_at/last_rebalance/model_version/timing_ratio

## 检查点 6: 敞口现状
- paper-state.json: n_holdings=8, cash=40393, last_rb=2026-08-14, created_at=2026-08-17 (task-0486 重建)
- → 两缺口均为活敞口(非 R-345 审计时点的空仓态): 9-1 调仓可能遇跌停卖出; 8 持仓随时可能跨除息日(2026-05 以来 3470 条分红事件)
- spot-check R-345/R-343 数字: L72 limit_up_pct=0.098 ✓; L97 48,081 ✓; L100 DIV_EVENTS L61 ✓; R-343 L25 10.04%/0.3878 ✓

## 方案要点草稿
② is_limit_down: 板块感知阈值 — 300/301/688/689 → 0.198(创业板/科创板±20%, ST 仍 20%); 主板 ST → 0.05; 其余 0.098; pct <= -th+1e-4。接线两处(清仓 L1442 块 skip+保留持仓; 减仓 L1464 块 continue 下一个)。env 开关 PAPER_LIMIT_DOWN_GATE。回退: .bak + 开关。
③ watermark state["last_div_date"] + 双挂点(action_daily 回填循环逐日 credit; action_rebalance 卖出块前) + entitlement buy_date<ex_date + ledger 文件 paper-div-ledger.csv(不动 trades.csv schema) + 税务 v1 毛额入账(v1.1 可选 10% 预扣) + 依赖: dividend_events 需定期刷新(无 cron, 手动 prep_dividend_roa --only div)。
实施顺序: ①已完成(只读) → ②批准后实施(下次调仓前) → ③批准后实施(分红季紧迫)。两缺口现均活敞口。
