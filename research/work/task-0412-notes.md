# task-0412 notes（R-254：T4 candidate 登记 + 评分制 v1.1）
- 2026-08-21 11:40 任务置 running ✓（task 中心返回 ok）
- R-253 读完：T4=bt_r252_t4_f2_l10_20260821，四门 PASS（G1 -8.11%/G2 13.21%/G3 -33.55%,-16.13%/G4 24.96%,0.00pp），胜者=F2 优先规则
- T4 locked 审计口径：full ann 0.221396 / mdd -0.335542（R-253 §3.2）
- R-253 最大编号=253 → 本报告=R-254 ✓
- R-245 先例要点：tar 备份 registry→逐条目写 gate.score/score_components/score_flags/stat_warn/rank_in_pool/score_holdout/ic_coverage/rescored→gen_versions_manifest.py；rescore_20pct_v11.py 为参照脚本；两次干跑确定性验证后 --write
- R-252 §五：E2 胜出仅获评分制资格，不构成激活；评分制 v1.1 = rank1 + 无 stat_warn + holdout PASS + 用户确认
- 在役基准：a13_rsraw_e1f10dz score 0.8781 rank1
