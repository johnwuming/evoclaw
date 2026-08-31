# task-0602 过程笔记：runtime 真实回撤审计与四基线对齐（R-387）

## 核验点 1：runtime 实仓构成（paper-state.json，04-投资研究/）
- cash = 40393.0，initial_capital = 100000 → 现金占比 40.39%
- holdings 8 只 → 股票腿约 59.6%（名义），与任务书「8 股约 60.6% + 现金 40.4%」基本一致（60.6% 或按市值浮动）
- baseline-paper-nav.csv 仅 12 行：2026-08-14（0.9996）→ 2026-08-28（1.00993），为 paper 组合日频 NAV，窗口仅 2 周
- versions-manifest.json 121KB（>30KB，未全读，后续按需 grep）

## 核验点 2：R 号占用实查
- 05-量化投资/ 当前最大 R-386（R-386-资产类别级去相关腿论证-利率债与QDII盘点.md）
- 本任务取 R-387

## 待办
- [ ] 读 R-378/R-380/R-381 提取四基线口径数字
- [ ] 找微盘腿 runtime 级 NAV / 权益序列（长窗口），或确认只有 12 天 paper NAV → 数据缺口判定
- [ ] 直算 runtime 组合 MDD/年化/波动
- [ ] 四基线并列总表
- [ ] 报告 R-387 + README + completions + 状态 pending_review
