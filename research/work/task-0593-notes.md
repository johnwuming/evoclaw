# task-0593 笔记

## 现状确认
- Candidates.jsx L306-308：滚动行仅 ann/mdd 内联 toFixed(2) 渲染；已有 fmtPct(L20)/fmtPct1(L21)，无 fmtNum。
- Version.jsx L115 同构参照：`{label}：ann {fmtPct(RC.ann)} / vol {fmtPct(RC.vol)} / sharpe {fmtNum(RC.sharpe)} / mdd {fmtPct(RC.mdd)}（{note}）`；fmtNum 定义 L123。
- policy.json caliber.rolling_compare 四字段齐全：ann 0.1012 / vol 0.0664 / sharpe 1.5233 / mdd -0.0571；note 同源。
- rel_tol 位置：caliber/static_recalc/rel_tol = 1e-10（不在顶层）。
- CSS：.cand-caliber 已有 overflow-wrap:anywhere（styles.css L497），390 宽下自然换行，无横向滚动风险。

## 改动
1. Candidates.jsx：新增 fmtNum helper；滚动行改四指标（与 Version.jsx 同格式）。
2. policy.json：rel_tol 1e-10 → 1e-9。
