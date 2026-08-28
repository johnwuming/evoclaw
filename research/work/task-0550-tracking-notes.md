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
