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
