# task-0348 [A8-收尾] 分桶打分版补跑 + 三方式对照 — 过程笔记（边查边写）

## 上下文恢复（20:20）
- HP runner 基建在 ~/quant-evolve/scripts/a9_sel.py + a9_common.py（/tmp 下原始 a9 runner 已清理，scripts/ 内为持久版本）
- a9_common.patch_engine: PA raw_universe / PB ext 排序(zscore|ranksum) / PC e1_guard+xsub / PD pb 列 / PE 返回扩展
- E3 因子集 SUM_SPECS = [("log_mv",1.0,-1), ("amt20",1.0,-1), ("pb_inv",0.7,+1), ("roe",0.3,+1)]
- locked=2006-01-01~2024-06-30(AUDIT_LOCK_END), full=2006-01-01~2026-08-31; 成本v2+一字板on, n_hold=20, 月度调仓, capital 1e7
- 择时 q3z_tr: MA200, floor0.30, pos mean=0.516
- timing: 市场加载 ~70-80s, 每回测 ~60s; a9_sel.log 已验证 equiv2 逐位一致机制

## 基线（locked 口径, 已有结果勿重跑）
| 版本 | 年化 | MDD | Sharpe | Calmar | 换手 | 来源 |
|---|---|---|---|---|---|---|
| 现役 v5h_xsub | 15.74% | -29.80% | 0.998 | 0.528 | 0.320 | a7_v5h_xsub_formal |
| zscore 四因子 quality | 15.94% | -29.52% | 1.036 | 0.540 | 0.330 | a9_zsum_quality |
| zscore 四因子 raw | 19.85% | -34.59% | 1.264 | 0.574 | 0.258 | a9_zsum_raw |
| ranksum 四因子 quality | 15.33% | -28.78% | 1.009 | 0.533 | 0.347 | a9_ranksum_quality |
| ranksum 四因子 raw | 21.76% | -33.55% | 1.344 | 0.649 | 0.466 | a9_ranksum_raw |
| E1 raw(纯mv去闸门) | 21.76% | -36.78% | 1.215 | 0.592 | 0.271 | a9_raw_universe |
| A7 v5b(混排血统, 不同因子集) | 14.52% | -30.76% | — | — | — | A7 报告 |

## 方案（20:22 定稿）
- 新 runner: ~/quant-evolve/scripts/a8_bucket.py（新文件，不动现有代码）
- patch 链: import a9_common → 取 inspect.getsource(patch_engine) → 定点替换加入 bucket 模式（替换处 assert count==1）→ exec 编译
  - 保证与 a9 补丁链逐字一致，仅新增 bucket 分支；锚定校验(a8x_equiv_v5h vs a7_v5h_xsub_formal 逐位)背书
- bucket 语义: 每因子月度截面 rank(pct) → 符号翻转(sgn<0 取 1-r) → floor(r×5).clip(0,4) 得桶号 0-4（4=最优）→ score=Σ w_i×桶号_i；同 E3 权重
- 跑 3 个回测: a8x_equiv_v5h(锚) + a8_bucket_quality + a8_bucket_raw，各出 full+locked 双窗（每 tag 10 文件）
- E4 线: bucket raw locked 年化 ≥17.74%(+2pp vs 现役) 且 MDD ≥-31.80%(恶化≤2pp) → 过线记 decision-log；否则 closeout
- ledger: IT-A8-01 (bucket_quality) / IT-A8-02 (bucket_raw)，features 字段必带

## 进度
- [x] 20:20 上下文恢复 + 基线确认
- [x] 20:27 a8_bucket.py 写入 scripts/（9.9KB, py_compile OK; scp 不可用 → ssh cat 管道上传）
  - patch 链 = a9_common.patch_engine 源码定点替换（2 处 assert anchor），exec 重编译；bucket 自检（10票×2/桶、端点符号）PASS
  - 流程: S0 加载 → S1 a8x_equiv_v5h 锚(逐位, FAIL即exit3) → S2 bucket_quality/raw → S3 汇总 a8_bucket_summary.json
- [x] 20:28 nohup 启动 pid 21644, log=~/quant-evolve/logs/a8_bucket.log
- [ ] 锚定校验 PASS
- [ ] bucket quality/raw 双跑完成
- [ ] 三方式对照表 + a8-iteration-report.md(HP)
- [ ] ledger + decision-log
- [ ] completions
