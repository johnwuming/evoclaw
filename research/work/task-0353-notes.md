# task-0353 评分制 v1.1 影子观察期+holdout 晋升门槛 — 工作笔记

## 目标
1. 影子观察期：auto-activate 遇 stat_warn → shadow 标记 + shadow_watch 日志，连续 N=3 评估周期无升级才可上岗
2. holdout 晋升门槛：activate 前算 2024-07~数据末 holdout 指标；年化 ≥ locked 60%，MDD 恶化 ≤ +10pp
3. evaluate/decision-log 双段指标口径
4. 三版回归试算（v5h_xsub/v6a_def/v5i_comb）
5. D-20260817-P04 日志 + 笔记 + completions

## 进度
