# 🦞 Evolving Claw — 进化中的爪子

OpenClaw 多 Agent 交付物仓库。

## 目录结构

```
├── research/          # 研究团队交付物
│   ├── reports/       #   研究报告
│   ├── plans/         #   方案/设计文档
│   └── internal/      #   研究过程文件
├── dev/               # 开发团队交付物
│   └── <project>/     #   每个项目一个目录
├── main/              # 主 Agent 产出
│   ├── analysis/      #   分析文档
│   ├── config/        #   配置方案
│   └── plans/         #   方案文档
└── infra/             # 基础设施
    └── scripts/       #   自动化脚本
```

## 自动同步

通过 inotifywait 实时监控本地交付物目录，文件变更后自动 commit + push。
