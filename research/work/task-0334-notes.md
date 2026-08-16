# task-0334 神奇公式 A6 — 过程笔记（VPS 收口副本）
## 时间线
- 01:36 连通HP, load 1.05, 无A5回测进程
- 阶段0: mf_panel.parquet 构建完成 (HP results/mfpanel.parquet 68MB, 707245 rows, 5032 codes)
  - EBIT_u=NP_ttm/0.85; EV=circ_mv+(total_liab-ap-adv)-cash; ROC=EBIT_u/(total_asset-cash); roc_g=EBIT_u/(ar+inv-ap-adv)
  - 覆盖率: 全市场 86% (EBIT>0 限制), 质量宇宙 99.9%
- 阶段1: IC 预检完成 (HP results/mfic_monthly*.csv)
  - 全市场: roc -0.0022/ICIR-0.06, ev_ebit -0.0325/ICIR-0.88, mf_score -0.0186/ICIR-0.48
  - 质量宇宙: roc -0.0053, roc_g +0.0070, ev_ebit -0.0569/ICIR-1.25, mf_score -0.0468/ICIR-1.24
  - 诊断: spearman(ev_ebit,pe_ttm)=0.881, (ev_ebit,pb)=0.821, (roc,roe_ttm)=0.302
- 02:00 起 HP sshd 握手卡死(沙箱→HP), TCP/ICMP 正常, NAS→HP 正常 → 判定为沙箱IP的 sshd 未认证连接槽耗尽
## 候选设计 (5个, g5 逻辑预埋)
- v4a_mf0_trr: 原教旨(无质量过滤, mf纯排序, price_cap保留) + q3z_tr
- v4b_mfu_trr: 质量宇宙 + mf纯排序 + q3z_tr
- v4c_mfu_e1_trr: v4b + E1护栏(ret120>-30%)
- v4d_mfu_raw: v4b 无择时(归因对照)
- v4e_rocblend_trr: 质量宇宙 + 0.5mv+0.5roc blend + q3z_tr (预检显示ev_ebit维度弱, 只保留roc质量腿)
## 完成回报
- 见 .task-completions.jsonl
