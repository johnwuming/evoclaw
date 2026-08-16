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
## 连通性故障记录与恢复点 (02:00-02:4x)
- 症状: 沙箱→HP ssh 握手卡死(TCP/ping正常, NAS→HP正常); scp 推送间歇可用; 长时间ssh会话随turn超时被SIGKILL
- 判定: HP sshd 未认证连接槽耗尽(我的快速重连) 或 A5 重负载; setsid nohup 全detach 的远端进程不受影响
- 已完成(确认在HP): 阶段0 mfpanel.parquet / 阶段1 mfic_monthly.csv+mfic_monthly_univ.csv / 8个脚本在 /tmp/
- 已尝试: mf_supervise.sh(一次 RC=0, 可能已启动runner), mf_ensure.sh(推送成功 scp_exit=0, 运行超时但远端可能已启动)
- 恢复点: 若runner已在HP跑, 结果自动落 results/mf_*; 若未跑, 需重连后 bash /tmp/mf_ensure.sh (幂等: 确保runner+finish流水线)
- finish流水线: runner完成后自动 ic_ext -> evaluate -> post_bt -> report -> touch /tmp/mf_FINISHED
## 03:00+ 状态更新
- 8个脚本全部确认推送到HP /tmp/ (mf_runner/mf_supervise/mf_ic_ext/mf_evaluate/mf_post_bt/mf_finish/mf_report/mf_ensure)
- mf_supervise.sh 曾以 RC=0 执行过(会setsid nohup 启动 runner); mf_ensure.sh 也被调用过(幂等确保 runner+finish)
- 结论: HP 上 detached 流水线大概率已自主运行: runner(等价校验+10回测) -> finish等runner -> ic_ext->evaluate->post_bt->report -> touch /tmp/mf_FINISHED
- 沙箱->HP ssh 持续超时(rc=124), 但 TCP/ping/NAS->HP 正常 → 判定沙箱IP sshd槽位问题/间歇性, 非HP宕机
- NAS 端口转发被 sshd 禁止(administratively prohibited), NAS 无法做中继 → 只能直接ssh重试
- 待办: HP通后 ①验证 results/mf_*(50) + report>4KB + registry/ledger/decision-log ②scp拉 mfsummary.json+gate table ③同步notes ④写 .task-completions.jsonl
## 03:15 突破: runner 已完成!
- 03:12:01 重试循环成功连接: mf_run.log 显示 MF_RUNNER_DONE 1077.7s (全候选回测完成)
- v4e_rocblend_trr full: ann=12.48% mdd=-29.97% sharpe=0.846 calmar=0.416 (log尾部可见)
- 注意: 早期探测 summary=0 是相对路径误报(ssh默认cwd=home, 应为 ~/quant-evolve/results/)
- finish 日志为空 → mf_finish.sh 可能未启动(ensure 曾超时); 需重跑 ensure(幂等) 确保 finish 流水线
- pgrep -f 计数含探测命令自匹配(误报), 以日志为准
## 03:38 finish 流水线已启动!
- 关键修复: 之前 scp "exit=0" 是管道 tail 退出码误报, 实际脚本从未推送成功(mf_ensure.sh 不存在)
- 改用 base64 内联经单次 ssh 推送(mf_ic_ext/mf_evaluate/mf_post_bt/mf_report/mf_close/mf_finish.sh), 修正 mf_finish.sh 顺序: ic_ext -> post_bt(registry先注册) -> evaluate(门禁) -> close(decision-log) -> report
- runner 早已完成: mfcount=50 + mfsummary.json (03:12 窗口确认)
- finish 启动日志: finish_start=19:38:24 runner_done_at=19:38:24 iter=1 (HP时区19:38 = VPS 03:38)
- 待办: 轮询 /tmp/mf_FINISHED + gate/report 产物, 验证后收口
## 03:40 finish 完成但 post_bt 崩溃 (rc=139 SIGSEGV)
- marker=1 ✓ / ic_ext=1 ✓ (mf_ic_monthly_ext.csv 247x113) / report=1 ✓ (8400B) / close=1 ✓ (D-20260816-032)
- 问题: postbt_rc=139 (段错误, 无任何输出→崩溃在 print 之前, 疑 compute_data_snapshot 或 load_json); eval_rc=1 (registry 无 v4a_mf0_trr)
- 连锁: gate=0 (mf_gate_table.json 缺失), ledger 未加行, registry 未注册
- 修复计划: 诊断 post_bt (前台跑拿 stderr) → 修 → 重跑 post_bt → evaluate → 重生成 report (带门禁表)
- 注意: HP 时区=UTC (VPS-8h), decision-log 日期为 20260816 (house style 同 a4d)
## 03:47 五门禁完成! (清理pandas pycache修复段错误)
- n_trials=67; 全部 REJECT (0 activate)
- v4a_mf0_trr: g1 FAIL 0.338 g2 FAIL g3 PASS g4 PASS 0.9936 g5 PASS g6 PASS | 16.53%/-29.86%/1.011
- v4b_mfu_trr: g1 FAIL 0.338 g2 FAIL g4 PASS 0.9678 | 12.42%/-28.95%/0.832
- v4c_mfu_e1_trr: g1 FAIL 0.338 g2 FAIL g4 PASS 0.962 | 11.99%/-28.95%/0.812
- v4d_mfu_raw: g1 FAIL g2 FAIL g4 FAIL 0.5483 g6 FAIL | 20.59%/-69.27%/0.777
- v4e_rocblend_trr: g1 PASS 0.5753(!) g2 FAIL 0.0153 g4 PASS 0.967 | 12.35%/-29.97%/0.829
- 核心印证: 去掉ev_ebit负IC腿后 g1 0.338→0.575 过线; 但OOS劣化(g2)仍FAIL — 质量腿零alpha被证实
- max_corr=0.0752 (与active因子低相关); ledger实际文件=results/experiment-ledger.jsonl (非model/history.jsonl!)
- decision-log: D-20260816-032(close) ~037(evaluate_reject×5)
- 待办: 重跑report(含门禁表) → 最终验证 → 收口notes+completions
## 03:48 收口验证完成 (全部产物确认)
- report: 8606B (>4KB✓), 含门禁表+IC预检表+A4对照段
- ledger: results/experiment-ledger.jsonl (5行backtest带features + 5行evaluate)
- decision-log: D-20260816-032(a6_batch_close) + D-20260816-033~037(evaluate_reject×5)
- registry: v4a_mf0_trr/v4b_mfu_trr/v4c_mfu_e1_trr/v4d_mfu_raw/v4e_rocblend_trr 5个候选
- mf_* 产物 53个 (50件正式套件 + mfsummary/mf_gate_table/mf_ic_ext)
- 验收标准全部满足: 产物齐全/报告>4KB含IC表与A4对照/ledger带features/0 activate
## 最终结论 (认知增量)
- 神奇公式与A4价值指标的本质区别: 数据不支持其增量
  1) EV/EBIT 与 pe_ttm 排名相关 0.881 → 净债务调整在低杠杆质量池几乎不改变排名, 仍是同一个负alpha便宜度维度 (宇宙内 ICIR -1.25, 与a4d的pe -1.37同量级)
  2) ROC 是独立维度(与roe相关仅0.30) 但 IC≈0 (宇宙 -0.15) → 质量/资本效率无定价能力
  3) 实证铁证: 砍掉ev_ebit腿后 v4e g1 ICIR 0.338→0.5753 过线(唯一PASS), 但OOS劣化仍FAIL — 质量腿确实独立但非alpha源
- 战役目标对照: 全部候选 25%/-20%/1.2 不可达 (最佳v4a: 16.53%/-29.86%/1.011, 原教旨反而最好因全市场含高股息池)
- 0 activate; v2b_trr 现役不变
