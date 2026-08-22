# task-0441 notes — R-273 PEAD负惊喜软惩罚 E1验证
开始: 2026-08-22 15:44 GMT+8
目标: 复用R-251 ths_ttm_panel PIT面板，验证 SUE<0 且披露≤2月 子集的次月负向集中度，做软惩罚项净增量IC验证，三卡判定。
## 步骤
- [ ] 读R-251（面板位置/口径）、R-269（双门教训）
- [ ] HP确认面板文件与字段
- [ ] 负惊喜子集 IC/ICIR/Q5-Q1
- [ ] 对在役四因子净增量IC
- [ ] 三卡判定
- [ ] 报告落盘+README更新

## §1 前置报告要点（15:48 完成）
R-251（05-量化投资/R-251-SUE财报事件因子IC画像.md, 7647B）：
- 面板：HP ~/quant-evolve/data/derived/ths_ttm_panel.parquet（235,170行×8，含 avail_date 披露日）
- R-251 脚本/产物：HP scripts/r251_sue_profile.py；results/r251/{sue_summary.json,sue_ic_monthly.csv,sue_events.parquet}
- IC口径：IC[m]=spearman(F_m,R_{m→m+1})，月频全市场 min_obs=20，去极值1%/99%+zscore；池=在市+上市满120交易日+当月有交易；K线 data/all_stocks_qfq/*.parquet
- sue_std=Foster型 (E_q−E_{q−4})/std(ΔE_{q−7..q},min5) clip±15；全样本 ICIR 0.115；0-2月新鲜窗 IC 0.0266/ICIR 0.261；与roe_ttm截面ρ=0.599、IC序列相关0.886
- PIT：ym_avail=avail_date所在月 as-of 映射+同月取最新+按月ffill；严禁report_date直接join（中位滞后62天）
R-269（05-量化投资/R-269，约8KB）：
- 教训：EP_stab形式过ICIR门(0.297)但Q5−Q1=−0.02pp(t=−0.07) → 达线判定必须同时含ICIR门+spread门(Q5−Q1 t≥2方向一致)
- 在役四因子自查IC：log_mv −0.054/−0.314、amt20 −0.104/−0.675、pb_inv −0.061/−0.565、roe_ttm −0.011/−0.085（口径量级参考）
- 在役=a13 ranksum4：log_mv/amt20/pb_inv/roe（R-251记法）
三卡判定预登记（计算前写定，禁事后调线）：
- C1: 负惊喜子集因子（PEN=1{SUE<0 且 披露≤2月}，期望负向）|ICIR|≥0.25 且方向=负
- C2: 净增量IC>0（对在役四因子截面残差化后 mean IC，按惩罚方向取号）
- C3: Q5−Q1 价差同向（惩罚组−非惩罚组 <0，t≥2参照R-269 spread门）
任一卡不满足 → 如实关闭。目标量级：ICIR 0.3+ 且净正。

## §2 HP 部署与计算启动（16:02）
- registry 只读确认：active 引擎 a12_s2_reb + a13_rsraw_e1f10dz；a13 = ranksum4（log_mv/amt20/pb_inv/roe），与 R-251/R-269 记载一致 → 在役四因子=log_mv/amt20/pb_inv/roe
- 数据源列核验：all_stocks_merged(date,code,close,volume,amount)；fundamentals_monthly(code,date,circ_mv,div_yield...)；ths_ttm_panel 8列含 avail_date
- 脚本已传 HP:~/quant-evolve/scripts/r273_pead_penalty.py（12,283B，本地留底 /tmp/r273_pead_penalty.py），语法过
- nohup 后台运行中，日志 results/r273/build.log；产物 results/r273/{summary.json, ic_*.csv, spread_monthly.csv}
- 脚本设计（计算前登记）：
  - PEN=1{sue_std<0 且 STALE≤2}（主）；敏感性：PEN_SIG=sue_std 负部、pen_pct2（sue_pct口径）、pen_std1（≤1月）
  - 自洽校验：复现 R-251 sue_std 全样本 ICIR 0.115 与 0-2月新鲜窗 0.261
  - C2 净增量：G=−PEN 对四因子 zscore 截面 OLS 残差化 → 残差 IC 均值>0 为净正；另组合诊断 comp4+w·G 的 ΔIC（w=0.1/0.2，按各因子自身IC有利方向合成，标注为诊断口径非在役复刻）
  - C3：Q5−Q1 = PEN=1组 − PEN=0组 月均价差（pp），t 检验

## §3 运行纪要（16:20）
- 第一跑：monthly_asof("net_profit_ttm") 占位行 KeyError → 删除
- 第二跑：all_stocks_merged.code 为 categorical，sort_values 报 categories 不唯一 → astype(str) 修复
- 第三跑（16:14 起）正常推进：[1] events=235,170/5,174 codes；[2] 池 5,020 只，月均 2,845（与 R-251 一致）；[3] PEN 月均覆盖 674 只（负惊喜新鲜票规模充足）
- BUG 修复两次，均未影响既有进程；脚本产物只写 results/r273/ 新目录

## §4 阶段B（22:55 起，VPS 本地收口）
### 4.1 断点接管与数据盘点（23:05 完成）
- HP 第三跑产物未同步 VPS（本地仅空 build.log）；HP results/r273/ 不可访问（本阶段禁 SSH HP）→ 按「参数重建」路线收口
- R-251 断点产物 VPS 侧：evolving-claw-repo/research/04-投资研究/r251/{sue_summary.json, sue_ic_monthly.csv}（校准目标：sue_std 全样本 ICIR 0.115 / 0-2月窗 IC 0.0266 ICIR 0.261）
- VPS 数据盘点：
  - K线 data/all_stocks_qfq/*.parquet 5,205 只（000001 验证 2006-01-04~2026-08-07，含 amount/outstanding_share/close）→ 与 R-251 K线库同源，池/收益完全可复刻
  - all_stocks_merged 仅 2020-2025（不可用）；financial-ths CSV 无披露日列；fin_deep(baostock) 仅 20 股完成（不可用）→ ths_ttm_panel 无法原样重建
- **替代面板路线**：akshare 1.18.94 在 VPS 可用；ak.stock_yjbb_em(报告期) 逐期返回全市场 净利润(累计)+最新公告日期 → 自建 PIT 事件面板（code/report_date/avail_date/np_cum → TTM 换算）。与 R-251 ths_ttm_panel 口径差异：起点 2006（ths 1997 起）→ SUE 事件窗前段缩短，IC 窗约 2008+ 起；其余口径（TTM 同构、Foster 型 SUE、clip、PIT as-of、W1 IC）逐一复刻
- 产物目录：/root/.openclaw/workspace/shared/results/work/r274/（新目录）；原始采集 /tmp/r274_vps/
- 四因子代理（a13 ranksum4 复刻口径）：log_mv=log(close×outstanding_share)、amt20=20日均额、pb_inv=bps/close（yjbb 每股净资产 PIT）、roe=yjbb 净资产收益率 PIT；对 R-269 自查 IC 量级校准
### 4.2 采集与计算（23:15 启动）
- ak.stock_yjbb_em 逐报告期采集 2005Q4-2026Q2（86期），列：股票代码/净利润-净利润(累计)/最新公告日期/每股净资产/净资产收益率；Q4期含预告+实报混合行（如20161231 9540行），dedup 规则=同code同report_date取avail_date最新（实报覆盖预告）
- 采集脚本 /tmp/r274_vps/collect_yjbb.py（重试3次+断点续采），主计算 /tmp/r274_vps/r274_compute.py（语法已过）；VPS 仅 3GB 内存 → K线流式按股聚合月度，不 concat 全量
- 主计算口径：TTM=Q4年报直取/Q1-Q3=上年年报+当期累计-上年同期；sue_std Foster 型 clip±15、dE 仅取季距=1 的相邻季差；PIT=ym_avail as-of+同月最新+按月ffill；PEN=1{sue_std<0 且 stale≤2月(60.9天)}；G=−PEN；IC=W1口径 spearman min_obs=20 去极值+zscore；池=td_cum≥120+当月有收盘
- 产物将落 shared/results/work/r274/{events_sue.parquet, kline_monthly.parquet, summary.json, spread_monthly.csv, ic_*.csv, pen_coverage.csv}
### 4.3 v1 面板缺陷与修复（23:25-23:35）
- v1 自洽校验失败：sue_std 全样本 IC −0.0105/ICIR −0.147（R-251 为 +0.0117/+0.115，符号翻转）→ 触发排查
- **根因**：akshare stock_yjbb_em 的「最新公告日期」不是原始披露日，而是东财回填的「含该期比较数据的最新公告日」（000001 2024Q4 行=2026-03-21 即 2025 年报公告日；全表滞后 p50：2024Q4=479 天、2025Q1=393 天 ≈ 次年同期报告公告日）→ 整面板晚 12 个月，PEN「披露≤2月」完全错位，v1 全部 C1-C3 作废
- **修复 v2**：avail_date 改用法定披露期限上界代理（Q1→4/30、H1→8/31、Q3→10/31、年报→次年4/30）。性质：只可能晚于真实披露（绝不前视）；对效应方向的偏置=因子更陈旧→对 C1-C3 不利（保守门）；预登记门槛不变
- v2 复用缓存 events_sue.parquet + kline_monthly.parquet，不再重采；bps/roe 经 report_date join 重取（期限代理同口径）
- v1 残留结果备份在 summary.json（如需对照），v2 落 summary_v2.json
### 4.4 v2 结果与判定（23:45 完成）
- 自洽校验通过：sue_std 全样本 0.0108/0.112/1.70 (n=232) vs R-251 0.0117/0.115/1.78；年度模式一致（2013+0.042/2017+0.081/2021−0.048）；log_mv −0.054/−0.319、amt20 −0.103/−0.659 与 R-269 近全等 → 面板质量合格
- C1 ✗：PEN IC −0.0073/ICIR −0.099/t −1.07（门槛 0.25，仅 40%）；方向正确
- C2 ✓数值：残差化 G IC +0.0152/ICIR 0.326/t 3.49 (n=114)
- C3 ✗：价差 −0.118pp/t −0.79/负月 52.6%（门槛 t≤−2）
- 敏感性全弱：pen_std1 方向反、pen_sig 无信号、pen_pct 同主口径
- **判定：不显著但机制清晰→维持关闭**。C2 残差净增量为唯一存活线索（重启触发条件：真实披露日面板复验，预期低收益）；R-251 登记口子正式关闭
- 报告落盘：shared/results/05-量化投资/R-274-PEAD负惊喜软惩罚净增量验证.md（4.8KB）；README 更新日志待更新
- 期限代理稀释说明：PEN=1 月均 1,492 vs R-251 真实 674（披露同步化）；新鲜窗 IC 0.015 vs 真实 0.027
