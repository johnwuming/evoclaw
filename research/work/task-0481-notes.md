# task-0481 红利低波 E2 预注册+执行 边查边写笔记

时间轴（硬上限 1h，设计 ≤40min）：21:56 启动。

## 已读入上下文
- R-300（14.9KB 全文）：hl120 IC +0.0746/ICIR 0.364，2022-08 后 +0.114；Top-20 corr(a13)=0.3821 过线，宽组 Q5 0.547 超线 → E2 必须锁 Top-N；毛年化 12.64%/MDD −27.05% 破线；TR 口径毛超额 ≈+3.0pp。
- 判门先例 R-288（可转债 E2 二次预注册）：G0 锚校验/G1 超额/G2 MDD/G3 分段/G4 换手/G5 容量 + IC 衰减监控；机器可读锁 + sha256 + 时间戳取证。
- r480 数据资产：month_end_panel.parquet（21834 行, cols=[code,ym,date,craw,cqfq,dv,vol60,vol120,fwd]）、ic_series.csv、ic_summary.json、port_monthly.csv + md5 全在。
- a13 NAV: shared/results/04-投资研究/a13_rsraw_e1f10dz_locked_nav.csv（尚未读，报告阶段读）。

## 步骤1：PIT 成分史可得性实测（21:58 开始）
待测：akshare index_stock_hist（新浪历史成分）、index_detail_hist_cni（国证历史成分）、中证官网 closeweight 文件。
