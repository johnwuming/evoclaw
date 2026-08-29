# task-0552 阶段B：Phase C 治理切换执行 runbook

- 开始：2026-08-29 10:45 前后；窗口约束：16:30 前完成切换主体
- 依据：R-336 v1.5 §8 Phase C 动作1-5；R-353 §6 切换前注意4项；用户已批准当日切完、不考虑回退
- 例外授权：治理写路径（registry/engines/composites 事件化）+ paper 指针 + 镜像钩子接线；HP crontab / 在役进程 / evolution_pipeline / registry active 零改动

## 步骤0 探明 HP 侧现状
