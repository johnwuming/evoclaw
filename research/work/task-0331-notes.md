# task-0331 持仓级输赢归因 过程笔记
## 阶段0 数据装载与口径定义 [2026-08-16]
- 数据源确认:
  - trades: results/a2c_v2b_trr_{full,locked}_trades.csv (full: 1273 BUY / 1258 SELL_REBAL / 11 SELL_FORCED_DELIST / 19 BUY_SKIP_LIMIT_UP; locked: 1195/1171/0/18)
  - full nav 末 2026-08-14 num_held=0（全部平仓）; locked nav 末 2024-06-28 num_held=20（有 OPEN 仓位，期末价用最后交易日 close）
  - trades 只有 date,code,action,price，无数量 → episode 配对用"首笔 BUY → 对应 SELL"，需验证无重叠 BUY
  - fundamentals_monthly.parquet 707,245行(listed) + fundamentals_delisted_monthly 44,005行(361只): code,date,div_yield_ttm,circ_mv,roe_ttm,roa_ttm 月度 PIT
  - 行情: data/all_stocks_qfq/<code>_daily_qfq.parquet (5448只, 含 turnover/outstanding_share/amount); 退市股不在 qfq 目录 → 用 data/stocks_hfq/<code>_daily_hfq.parquet (5569只, 含退市) 算收益率类特征(日收益 hfq≈qfq)
  - st_history.parquet 是 2026-08-15 快照(206只) → 只做描述性标注，不进 PIT 归因(避免前视)
- 口径:
  - 持有期收益 = SELL价/BUY价 - 1 (同源 qfq 序列内部一致, 分红经复权近似)
  - 特征取 买入日前一交易日 asof 值 (严格 PIT)
  - 基本面特征月度横截面分位: listed+delisted 合并面板
  - 量价特征月度横截面分位: 该策略实际交易过的 code 全集(universe≈traded codes)——文档中标注
  - 跌得深组 = ret≤-30% 或 全部 closed episodes 收益最差5% (回撤贡献 proxy, 无权重数据, 报告中注明)
  - 涨得好组 = ret≥+100% 或 持有≥365天且年化>50%
## 阶段1 输赢分布全景 [2026-08-16 16:10]
- 口径核验: overlap_buy=2 (极小, 首笔BUY约定可接受), orphan_sell=0, px_missing=0
- full: 1269 closed / 2 open; locked: 1171 closed / 22 open
- full 收益分布: P5=-25.98% P25=-7.40% P50=+4.68% P75=+18.41% P95=+63.83% mean=+9.76% win_rate=59.8%
- 亏损尾部集中: 最差5%(63笔)贡献33.5%总亏损; 最好5%(63笔)贡献37.1%总盈利 (双尾都集中)
- 分组: full 跌深组64 / 涨好组33 / normal 1172 (无重叠); locked 跌深59 / 涨好32
- locked 与 full 高度一致 (mean 9.78% q05 -26.4% q95 +63.8%), 结论稳健

## 阶段2 特征归因 (full, 买入时点PIT) [2026-08-16 16:15]
- 跌深组(64) vs 非跌深组 显著项 (Welch t):
  - dy_pct 中位0.941 vs 0.909 diff+0.049 p<0.001 → 跌深组股息率分位更高 (高股息陷阱/价值陷阱信号!)
  - ret120_pct 中位0.324 vs 0.462 diff-0.098 p=0.014 → 买入时动量分位更低 (接刀)
  - dist250h 中位-0.31 vs -0.22 diff-0.077 p=0.0047 → 更远离年高点, 买在深度回撤区
  - roe 均0.2545 vs 0.2294 diff+0.025 p=0.042 (跌深组roe反而高, 注意是PIT快照, 说明不是"基本面烂"型)
  - mv_pct/vol20/turnover/amount 不显著
- 涨好组(33) vs 非涨好组 显著项:
  - mv_pct 中位0.042 vs 0.098 diff-0.092 p<0.001 → 赢家市值更小 (小盘高弹性)
  - roa 均0.1485 vs 0.1704 diff-0.022 p=0.006 → 赢家ROA更低 (同为小盘高弹性特征)
  - ret120 中位0.132 vs -0.011 (不显著但方向对), dy/roe_pct/vol 不显著
- 核心不对称: 小市值同时驱动赢家与输家 (输家组mv_pct也低但不显著) → 杠杆不在市值本身, 而在市值×质量/动量
- 退市/强平检查: 11笔SELL_FORCED_DELIST 全部 is_delisted_code=0 (不在361退市索引内!) → 这些是引擎级强制卖出(ST/停牌强平), 非真退市; 全样本真退市索引命中仅1笔(ret -0.018)
  - 强平笔特征: 002027(大市值roe0.309)亏-38%; 300824(小市值流动性0.037枯竭)亏-12%; 603551(流动性0.022)小亏; 多数小赚小亏 → 强平机制本身在002027上贡献-38%损失, 属"高roe大盘股突停"型, 常规退市预警筛不掉
- 持仓时长: 输家中位166天 vs 赢家中位304天 vs 全体63天 → 赢家拿得住, 输家平均持有更久(僵持)

## 阶段3 规则证据 (full) [2026-08-16 16:20]
- R1 微盘尾mv_pct<10%: 51%笔数 avg+10.7% (反而高), 捕61%输家但误杀64%赢家 → 不可用
- R3c ret120<-30%: 9.5%笔数 avg+4.1% vs 保留+10.4%, 捕18.8%输家/20.8%亏损, 误杀12.1%赢家 → 最佳单规则
- R3b ret120<-30% & amount20_pct<20%: 2.9%笔数 avg+3.1%, 捕9.4%输家/11.7%亏损, 误杀6.1% → 精确
- VT dy_pct>0.90 & ret120_pct<0.35: 20.6%笔数 avg+6.9%, 捕34.4%输家/34.9%亏损, 误杀30.3% → 最大亏损砍手, 但误杀高 → 建议降权非硬排除
- deepdecay ret120_pct<0.30 & dist250h<-0.30: 11%笔数 avg+2.2%, 捕12.5%输家/12.0%亏损, 误杀6.1% → 精确
- R4 amount20_pct<10%: 12.1%笔数 avg+5.6%, 捕7.8%输家, 误杀12.1% → 弱但方向对
- R5 roe<0: 仅2笔 (universe已基本剔除, 保留作硬过滤)
- R7 dist250h<-60%: avg+25.4% (反而好) → 不可用于排除
- 加强带: nearHigh(dist250h>-10%)&ret120>0: avg+21.2% win78.4% ann_med+119%; 温和正动量ret120>0: avg+16.1% win68%; 动量40-90分位: avg+12.1% vs 末40分位+6.7%; 流动性前50%: +12.3% vs 末20%+7.2%; 高股息: +9.9% vs 低+3.5%
