# 🦞 Evoclaw — OpenClaw 多 Agent 交付物仓库

## 目录结构

```
evolving-claw-repo/
├── research/           # 文档交付物（全部平铺）
│   ├── R-xxx-*.md      #   研究报告（research 团队产出）
│   ├── M-xxx-*.md      #   Main agent 产出
│   └── internal/       #   研究过程文件
├── dev/                # 开发项目
│   └── <project>/      #   每个项目独立目录
├── infra/scripts/      # 自动化脚本
└── README.md
```

## 命名规范

| 前缀 | 来源 | 格式 | 示例 |
|------|------|------|------|
| R-xxx | 研究团队 | R-xxx-kebab-case.md | R-001-research-team-config.md |
| M-xxx | Main agent | M-xxx-kebab-case.md | M-001-issue-channel-bug.md |

- xxx：三位递增编号，不复用
- kebab-case：英文，≤5 词

## 自动同步

本地 `~/.openclaw/` 下各 workspace 的产出物通过 auto-sync.sh 自动同步到本仓库，1:1 路径映射，无二次分类。
