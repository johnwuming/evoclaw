# task-0481 红利低波 E2 预注册+执行 边查边写笔记

时间轴（硬上限 1h，设计 ≤40min）：21:56 启动。

## 已读入上下文
- R-300（14.9KB 全文）：hl120 IC +0.0746/ICIR 0.364，2022-08 后 +0.114；Top-20 corr(a13)=0.3821 过线，宽组 Q5 0.547 超线 → E2 必须锁 Top-N；毛年化 12.64%/MDD −27.05% 破线；TR 口径毛超额 ≈+3.0pp。
- 判门先例 R-288（可转债 E2 二次预注册）：G0 锚校验/G1 超额/G2 MDD/G3 分段/G4 换手/G5 容量 + IC 衰减监控；机器可读锁 + sha256 + 时间戳取证。
- r480 数据资产：month_end_panel.parquet（21834 行, cols=[code,ym,date,craw,cqfq,dv,vol60,vol120,fwd]）、ic_series.csv、ic_summary.json、port_monthly.csv + md5 全在。
- a13 NAV: shared/results/04-投资研究/a13_rsraw_e1f10dz_locked_nav.csv（尚未读，报告阶段读）。

## 步骤1：PIT 成分史可得性实测（21:58 开始）
待测：akshare index_stock_hist（新浪历史成分）、index_detail_hist_cni（国证历史成分）、中证官网 closeweight 文件。

## 步骤1结论：PIT 不可得（22:00-22:04 实测）
- akshare 1.18.94 无 index_stock_hist；cons_csindex 仅当前快照；index_detail_hist_cni 实测仅最新单期截面（399324 → 40 行全 2026-07-31）且国证族无对应指数；官网历史成分=逐期公告 PDF 超预算；全市场 fallback 外推 >1.5h 超硬上限。
- 处置：折中口径=176 快照池+月度 PIT 规则，预注册冻结+硬披露，G6 终止开关不放宽。

## 步骤2：预注册落盘（22:07）
- work/r481/e2_prereg.json（4122B）+ R-301 报告（3244B）已写；sha256+时间戳见上命令输出（转录至下）：
  - e2_prereg.json sha256 已记（见 md5 段）
- 冻结要点：Top-20 等权月频；风险层=H30269<200DMA→次月半仓；成本单边 0.10%；基准=价格+池中位股息/12 自建 TR；G1 净超额≥+2.5pp（理由：E1 毛超额+3.0、死亡线+2、成本-0.4）；G2 MDD≤20%；G3 两段均正；G4 换手≤40%；G5 容量≥2000万（全持仓 10%×ADV20）；G6 corr(a13)<0.5 终止开关。
- 后台进行中：fetch_adv.py（135 只 ever-held 成交额，/tmp/r481/fetch_adv.log）
11097197a4b881d30ef4a5c3b8a1595bd5d60229c0a4f956153afbde19f2b750  work/r481/e2_prereg.json

## 步骤3：执行+判门（22:13 首跑，22:15 完成）
- G0 PASS 0.999829（n=152，管线复现 E1）；IC 双锚：hl120 均值 0.0746/ICIR 0.364 与 E1 逐位一致。
- 判门：G1 +1.859pp<2.5 FAIL；G2 −23.53%>20 FAIL；G3 −0.03/+5.71 FAIL；G4 19.35% PASS；G5 7.23亿 PASS；**G6 0.5126≥0.5 FAIL → 终止开关**。
- v2sens N=30：+1.49pp/−25.3% 更差。
- 归因：风险层 −2.78pp/年、MDD 仅 −27→−23.5；自建 TR 7.53%（时变池中位股息均值 3.26%，E1 的 9.5% 高估）；**G6 死因=窗口敏感**：E1 0.3821 复现无误，2014 单年 corr −0.4068 是去相关主要来源，剔 2014 后毛组合本身 0.5206（非风险层所致）。2022-09 后 0.069 仅近期现象。
- IC 监控：滚动6月均值连负 10 个月（2020-02..2020-11）触发复看标记（非门）。
- 判定：②负结果归档+死因，B 槽红利低波线关闭；建议下一 E1=黄金/贵金属趋势（R-300 排序第二）。
- 单位核验：sina amount 601288 近20日中位 32.1亿 → 元。fetch_adv 135/135 零失败。

## 产物
- R-301 预注册（3.2KB）+ e2_prereg.json 锁（sha256 11097197…，22:07<22:13 首跑）
- R-302 执行报告（4.1KB，数字全部取自 e2_gates_result.json）
- work/r481/{e2_backtest.py, e2_nav_monthly.csv, e2_capacity_monthly.csv, e2_ic_series.csv, e2_gates_result.json, fetch_adv.py, md5.txt}
