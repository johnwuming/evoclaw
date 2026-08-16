# 调研底稿：量化平台自动化与风控（WorldQuant BRAIN 指标）

## WorldQuant BRAIN alpha 检测标准（可直接引用的关键数据）
- Sharpe ≥ 1.25（BRAIN 平台提交门槛）
- Turnover 介于 1%–70% 之间
- Fitness > 1.0（fitness ≈ Sharpe × sqrt(abs(returns)/max(turnover, 0.125))）
- 子考察指标：Margin (bps)、Weight coverage、Long/Short counts、Sub-universe Sharpe、Self-correlation < 0.7（与已提交 alpha 的相关性）、Prod-correlation < 0.7
- Fitness 公式：来自 WorldQuant International Quant Championship 页面："Alphas are individually scored with a secret formula that weights their Sharpe ratio, turnover, and a custom metric named fitness"

## 来源
- Scribd WorldQuant Brain Alpha Documentation: https://www.scribd.com/document/728780335/World-Quant-Brain-Alpha-Documentation
- WQ Championship scoring: https://jglazar.github.io/projects/wq_project/
- Medium simulation settings: https://medium.com/@mapongo/worldquant-brain-how-to-apply-the-simulation-environment-settings-9dc232831bb6
- GitHub alpha-trading notes: https://github.com/alexisdpc/WorldQuant-alpha-trading

## RD-Agent(Q) 要点（来自 zread.ai/microsoft/RD-Agent）
- 首个以数据为中心的多 Agent 框架，因子与模型协同优化，自动化量化策略全栈研发
- 闭环：LLM 在 Docker 隔离环境持续提出/编写/回测/演化 alpha 因子与预测模型
- 三种工作流：Factor / Model / Quant（联合），Quant 模式用 Bandit 动作选择器决定下一迭代是探索新因子还是改进模型
- Trace DAG 记录实验谱系（hypothesis → 实现 → 评估反馈 → 知识积累）
- 效果：因子数量减少 70%+ 情况下 ARR 约为基准因子库 2 倍
- Web UI：Streamlit 离线查看器 + Vue/Flask 实时仪表盘，Playground 控制中心
- 论文: R&D-Agent (arXiv:2505.15155), R&D-Agent-Quant (NeurIPS 2025)
