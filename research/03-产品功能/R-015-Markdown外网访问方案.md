# R-010b: 对 iOS 友好的本地 Markdown 文件外网访问方案

> 研究日期：2026-03-29 | 方法：4 Search Agent + 2 Reviewer + 1 轮迭代补充

---

## 核心结论

**推荐方案 1（最佳体验）：Tailscale + Obsidian（Remotely Save / iCloud 同步）**
**推荐方案 2（轻量 Web 访问）：Tailscale Serve + MkDocs Material**

两个方案均基于用户已有的 Tailscale 网络，不需要额外公网暴露。

---

## 一、方案对比矩阵

| 维度 | 方案 A: Tailscale + Obsidian | 方案 B: Tailscale Serve + MkDocs | 方案 C: Gitea + Working Copy | 方案 D: Cloudflare Pages |
|------|-----|------|------|------|
| **iOS 阅读体验** | ⭐⭐⭐⭐⭐ 原生 App | ⭐⭐⭐⭐ Safari 渲染 | ⭐⭐⭐ Git 客户端 | ⭐⭐⭐ Safari |
| **离线访问** | ✅ 完全离线 | ❌ 需网络 | ✅ 克隆后离线 | ❌ 需网络 |
| **全文搜索** | ✅ 原生支持 | ✅ 插件支持 | ⚠️ 有限 | ⚠️ 需配置 |
| **实时性** | 同步后即时 | 需重新构建 | Pull 后即时 | Push + CI 构建 |
| **国内可用性** | ✅ Tailscale P2P | ✅ Tailscale P2P | ✅ Tailscale P2P | ⚠️ 移动网络差 |
| **部署复杂度** | 低 | 中 | 中 | 中 |
| **成本** | 免费~$4/月 | 免费 | $15.99 一次性 | 免费 |
| **编辑能力** | ✅ 完整编辑 | ❌ 只读 | ⚠️ 有限编辑 | ❌ 只读 |

---

## 二、推荐方案详解

### 方案 A：Tailscale + Obsidian（Remotely Save）⭐ 首选

**工作流：** Linux 编辑 MD → Remotely Save 同步到 S3/R2 → iOS Obsidian 自动拉取

**为什么是首选：**
- Obsidian iOS 是原生 App，阅读和编辑体验远优于浏览器方案
- 核心功能完全离线，无需网络即可读写所有笔记 [[Obsidian Forum](https://forum.obsidian.md/t/a-setting-to-entirely-restrict-internet-access-by-the-app/35117)]
- Remotely Save 插件支持 S3/Cloudflare R2/WebDAV 等 11+ 存储后端，支持端到端加密 [[GitHub](https://github.com/remotely-save/remotely-save)]
- 全文搜索原生支持，包括中文内容
- Tailscale 提供安全的内网通道，无需公网暴露

**具体实施步骤：**

1. **Linux 端安装 Obsidian**
   ```bash
   # AppImage 方式
   wget https://github.com/obsidianmd/obsidian-releases/releases/latest/download/Obsidian-1.x.AppImage
   chmod +x Obsidian-*.AppImage
   ./Obsidian-*.AppImage
   ```
   将 MD 文件仓库作为 Obsidian Vault 打开

2. **配置 Cloudflare R2（免费存储）**
   - 注册 Cloudflare，创建 R2 bucket
   - 免费额度：10GB 存储 + 每月 1000 万次读取 [[Cloudflare Docs](https://developers.cloudflare.com/pages/platform/limits/)]
   - 生成 API Token（需要 Object Read & Write 权限）

3. **安装 Remotely Save 插件**
   - Obsidian 设置 → 第三方插件 → 搜索 "Remotely Save"
   - 选择 S3 兼容存储，填入 R2 的 endpoint、bucket、access key、secret key
   - 开启端到端加密（可选但推荐）
   - 设置自动同步间隔（建议 5-10 分钟）

4. **iOS 端配置**
   - App Store 下载 Obsidian（免费）
   - 创建空 Vault → 安装 Remotely Save 插件
   - 同步配置与 Linux 端一致
   - 首次同步会拉取所有 MD 文件

5. **可选：Tailscale 辅助**
   - 如需直接访问 Linux 上的文件（如 SMB/NFS），Tailscale 提供安全通道
   - iOS Tailscale App 支持 iOS 15+ [[Tailscale Docs](https://tailscale.com/docs/install/ios)]

**注意事项：**
- Obsidian iOS 存在离线→在线切换时偶发丢失内容的 bug [[Bug Report](https://forum.obsidian.md/t/losing-work-on-ipad-ios-when-go-from-offline-to-online/100503)]，建议频繁手动同步
- Remotely Save 的 Google Drive/Box 等为 PRO 付费功能，S3/R2/WebDAV 免费
- 如果 Obsidian Sync 官方服务国内速度不理想，R2 方案是更好的替代

**替代同步路径：**
- **iCloud 同步：** 适合纯 Apple 生态用户，但 Linux 端需通过 iCloud 网页版或第三方工具 [[少数派](https://sspai.com/post/72388)]
- **坚果云 WebDAV：** 国内速度快，Remotely Save 支持 WebDAV 协议 [[少数派](https://sspai.com/post/72388)]
- **Syncthing：** ❌ iOS 无官方支持，iOS 后台限制导致无法正常工作 [[腾讯云](https://cloud.tencent.com/developer/article/2543913)]

---

### 方案 B：Tailscale Serve + MkDocs Material（轻量 Web 访问）

**工作流：** Linux 编辑 MD → MkDocs 构建 → Tailscale Serve 暴露 → iOS Safari 访问

**适合场景：** 以阅读为主、不需要在 iOS 端编辑、希望他人也能查看

**具体实施步骤：**

1. **安装 MkDocs Material**
   ```bash
   pip install mkdocs-material
   cd /path/to/md-files
   mkdocs new .
   # 编辑 mkdocs.yml 配置主题和导航
   ```

2. **配置 Tailscale Serve**
   ```bash
   # 启用 HTTPS
   tailscale cert <hostname>
   # 启动 Serve
   tailscale serve --bg https+insecure://localhost:8000
   # 或使用 Funnel（公网访问）
   tailscale funnel --bg https+insecure://localhost:8000
   ```

3. **iOS Safari 访问**
   - 确保安装了 Tailscale iOS App
   - Safari 访问 `https://<hostname>.<tailnet>.ts.net`
   - MagicDNS 自动签发 TLS 证书，Safari 直接信任 [[Tailscale Docs](https://tailscale.com/docs/features/tailscale-serve)]

4. **设置自动构建**
   ```bash
   # 使用 fswatch 或 systemd watch 监控文件变化
   # 文件变更时自动 mkdocs build
   ```

**注意事项：**
- MkDocs Material 在 Safari 18.3+ 存在导航渲染 bug [[Issue #7978](https://github.com/squidfunk/mkdocs-material/issues/7978)]，关注更新
- mdBook 移动端侧边栏体验不佳 [[Issue #476](https://github.com/rust-lang/mdBook/issues/476)]，不推荐作为替代
- Tailscale Funnel 仍为 Beta，存在偶发性性能问题 [[Reddit](https://www.reddit.com/r/Tailscale/comments/1pzguv4/)]，建议仅用 Serve（内网）
- MkDocs 支持全文搜索（自带 search 插件），50+ 插件生态 [[Grokipedia](https://grokipedia.com/page/Comparison_of_documentation_generators)]

---

### 方案 C：Gitea + Working Copy（开发者向）

**工作流：** Linux git push → Gitea → Working Copy pull → iOS Obsidian/其他编辑器打开

**适合场景：** 熟悉 Git 工作流、需要版本历史、技术人员

**实施要点：**
- Gitea 可在 1GB 内存的机器上运行 [[Hacker News](https://news.ycombinator.com/item?id=19295531)]
- Working Copy 专业版 $15.99 一次性买断 [[Working Copy](https://workingcopy.app/)]
- Working Copy 通过 iOS Files API 与 Obsidian、iA Writer 等协作 [[V2EX](https://www.v2ex.com/t/535525)]
- Gitea 新版编辑器改为 Monaco，Markdown 编辑体验下降 [[Gitea Forum](https://forum.gitea.com/t/markdown-side-by-side-editor-in-newer-versions-of-gitea/2560)]
- Reddit 社区推荐 Gitea + Working Copy + Obsidian 三件套 [[Reddit](https://www.reddit.com/r/selfhosted/comments/qxnbdq/)]

---

## 三、不推荐的方案

| 方案 | 原因 |
|------|------|
| **Syncthing iOS** | 无官方 iOS App，iOS 后台限制导致无法工作 |
| **飞书文档** | Markdown 导入支持差，不支持表格语法，不支持 .md 文件导入 [[飞书帮助](https://www.feishu.cn/hc/zh-CN/articles/118804574721)] |
| **语雀** | 不支持原生 Markdown 编写，需 Typora 中转 [[51CTO](https://blog.51cto.com/u_15116285/14327652)] |
| **微信读书** | 不支持导入 Markdown，仅支持导出笔记 |
| **Cloudflare Pages 公网访问** | 国内移动网络经常全挂，电信联通也不稳定 [[Colinx Blog](https://blog.colinx.one/posts/)]，与之前 R-010 推荐有矛盾，**建议修正** |
| **Tailscale Funnel 公网** | Beta 阶段，偶发性严重性能问题，且安全性不如 Serve 直连 |

---

## 四、Tailscale iOS 关键信息

- **系统要求：** iOS 15.0+ [[Tailscale](https://tailscale.com/docs/install/ios)]
- **VPN On Demand：** 支持按域名自动连接，但 iOS 同一时间只能有一个 VPN App 启用 [[Tailscale](https://tailscale.com/docs/features/client/ios-vpn-on-demand)]
- **电池影响：** 少数用户（~2%）有明显续航问题 [[Tailscale Blog](https://tailscale.com/blog/reimagining-tailscale-for-ios)]
- **DNS 路由：** VPN 激活后所有 DNS 流量经 Tailscale，导致不易自动断开 [[GitHub Issue](https://github.com/tailscale/tailscale/issues/17157)]
- **安全性：** Tailscale 采用 P2P mesh VPN 端到端加密，优于 Cloudflare Tunnel（TLS 终止点嗅探流量）[[Tailscale](https://tailscale.com/compare/cloudflare-access)]

---

## 五、成本总结

| 方案 | 一次性费用 | 月费 | 备注 |
|------|----------|------|------|
| Obsidian + Remotely Save + R2 | $0 | $0 | R2 免费额度充足 |
| Obsidian + 坚果云 WebDAV | $0 | ¥0~30/月 | 免费版有 API 限制 |
| Obsidian Sync 官方 | $0 | $4~8/月 | 端到端加密，国内速度慢 |
| Tailscale Serve + MkDocs | $0 | $0 | 完全免费 |
| Gitea + Working Copy | $15.99 | $0 | Working Copy 一次性买断 |
| Tailscale 免费版 | $0 | $0 | 最多 100 台设备 |

---

## 六、知识缺口

1. **Obsidian iOS 离线→在线 bug 的修复状态** — 社区已知但未确认是否已修复
2. **Remotely Save PRO 版具体价格** — 未找到公开定价
3. **MkDocs Material Safari 渲染 bug 修复进度** — Issue 仍然开放
4. **Tailscale Funnel 具体带宽/速率限制** — 官方未公布
5. **各方案在弱网环境下的同步延迟** — 缺乏量化数据

---

## 七、方法论反思

**做得好的：**
- 多角度并行搜索，覆盖了同步、Web、自建、云端四个方向
- 发现并修正了 R-010 中 Cloudflare Pages 国内访问速度的乐观评估
- Reviewer 指出的关键缺口在第二轮搜索中得到补充

**需改进的：**
- 部分关键数据（如同步延迟、具体性能基准）缺乏公开来源
- iOS 端实际体验多为社区反馈，缺乏系统性评测
- 国内网络环境的复杂性使得"速度"类结论难以一概而论

---

## 来源列表

1. [Tailscale 官方博客 - iOS 重构](https://tailscale.com/blog/reimagining-tailscale-for-ios)
2. [Tailscale 文档 - iOS](https://tailscale.com/docs/install/ios)
3. [Tailscale 文档 - Serve](https://tailscale.com/docs/features/tailscale-serve)
4. [Tailscale 文档 - Funnel](https://tailscale.com/docs/features/tailscale-funnel)
5. [Tailscale 文档 - VPN On Demand](https://tailscale.com/docs/features/client/ios-vpn-on-demand)
6. [Tailscale vs Cloudflare](https://tailscale.com/compare/cloudflare-access)
7. [Obsidian 官方定价](https://obsidian.md/pricing)
8. [Remotely Save 插件](https://github.com/remotely-save/remotely-save)
9. [Working Copy 官网](https://workingcopy.app/)
10. [Gitea Forum - Markdown 编辑器](https://forum.gitea.com/t/markdown-side-by-side-editor-in-newer-versions-of-gitea/2560)
11. [MkDocs Material Issue #7978](https://github.com/squidfunk/mkdocs-material/issues/7978)
12. [mdBook Issue #476](https://github.com/rust-lang/mdBook/issues/476)
13. [Cloudflare Pages Limits](https://developers.cloudflare.com/pages/platform/limits/)
14. [飞书 Markdown 支持](https://www.feishu.cn/hc/zh-CN/articles/118804574721)
15. [国内静态托管速度对比](https://blog.colinx.one/posts/)
16. [稀土掘金 - Cloudflare Pages 国内评测](https://juejin.cn/post/7438822895227256832)
17. [少数派 - Obsidian 同步方案](https://sspai.com/post/72388)
18. [PKMer - Obsidian 同步](https://pkmer.cn/Pkmer-Docs/10-obsidian/obsidian%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8/obsidian%E5%90%8C%E6%AD%A5/)
19. [Reddit - Gitea + Working Copy + Obsidian](https://www.reddit.com/r/selfhosted/comments/qxnbdq/)
20. [V2EX - Working Copy](https://www.v2ex.com/t/535525)


---

## 附录: 通用访问方案补充：Tailscale + MkDocs（R-010）

# 本地 MD 文件外网访问方案研究报告

> 任务编号：R-010 | 日期：2026-03-29 | 方法论：v4 深度研究（4 Search → 双 Review → Citation）

---

## 一、核心发现

### 发现 1：最快上手方案 — Tailscale Serve/Funnel + 轻量 MD 服务器

**结论：这是最适合当前环境的方案。** 用户已有 Tailscale，无需额外购买服务。

- **Tailscale Serve**（tailnet 内访问）：将本地 Web 服务路由到 tailnet 内所有设备，手机装 Tailscale app 即可访问 [1][2]
- **Tailscale Funnel**（公网访问）：无需公网 IP，通过加密中继暴露本地服务到互联网 [1]
- Funnel 限制：仅支持 443/8443/10000 端口，有不可配置带宽限制，仅 TLS 连接 [1]
- Funnel 可直接作为文件服务器：`tailscale funnel --bg 443 /path/to/folder` [3]
- Funnel 也可反代本地 HTTP 服务：`tailscale funnel --bg 443 http://localhost:3000` [3]

**推荐的 MD 服务器搭配（按推荐度排序）**：

| 工具 | 语言 | 部署难度 | 搜索功能 | 移动端 | 适合场景 |
|------|------|----------|----------|--------|----------|
| **MkDocs** | Python | ⭐ 极低 | ✅ 插件支持 | ✅ 响应式 | 纯文档浏览，最推荐 |
| **mdBook** | Rust | ⭐ 极低（单二进制） | ✅ 内置 | ✅ 响应式 | 轻量文档，无需 Python |
| **Quartz** | Node.js | ⭐⭐ 中等 | ✅ 内置全文 | ✅ SPA | 数字花园，与 Obsidian 兼容 |
| **code-server** | TS | ⭐⭐ 中等 | ✅ VS Code 搜索 | ⚠️ 可用但重 | 需要远程编辑能力 |

**来源**：Tailscale 官方文档 [1][2][3]；MD 工具对比 [7][8]；code-server [5]

### 发现 2：零部署方案 — 通过 OpenClaw Agent 直接查询

**当前即可使用**，无需额外部署任何服务：

- OpenClaw agent 有完整文件系统访问权限，可通过 Telegram/其他渠道直接要求 agent 读取并返回 MD 文件内容
- **局限**：不支持批量浏览文件列表的 UI，不适合"翻阅"大量文件，适合定向查询
- 社区已开发 Telegram 文件浏览器插件，可通过按钮导航 workspace 文件夹（medium 置信度）
- Control UI（Dashboard）目前无内置 workspace 文件浏览器（GitHub Issue #8192）

### 发现 3：第三方托管方案（适合非技术用户或需要协作的场景）

| 方案 | 费用 | 实时性 | 安全性 | 移动端 |
|------|------|--------|--------|--------|
| GitHub 私有 repo + GitHub Pages | 免费（公开）/ Enterprise（私有） | 需 git push | 公开 Pages 不适合敏感数据 [6] | ✅ |
| Syncthing 同步 | 免费 | 实时 P2P | 端到端加密 | ⚠️ 需另配查看器 |
| Obsidian Sync | $4/月 | 实时 | 加密同步 | ✅ 原生 app |
| Notion 导入 | 免费起步 | 需手动同步 | 云端存储 | ✅ 原生 app |

**来源**：GitHub Pages 限制 [6]；code-server [5]

### 发现 4：方案组合的架构建议

**最佳实践架构**：

```
本地 MD 文件
    │
    ├──→ Tailscale Serve → MkDocs/mdBook（tailnet 内浏览）
    │
    ├──→ Tailscale Funnel → MkDocs/mdBook（公网访问，可选）
    │
    └──→ OpenClaw Agent（通过 Telegram 智能查询）
```

三个通道互补：Serve 覆盖日常浏览，Funnel 覆盖无 Tailscale 设备的临时访问，Agent 覆盖智能查询。

---

## 二、推荐方案与实施步骤

### 🏆 方案 A：Tailscale + MkDocs（推荐首选）

**为什么选 MkDocs 而非其他**：Python 生态，`mkdocs.yml` 单文件配置，插件丰富（搜索、导航），Material 主题移动端体验极佳。

**实施步骤**：

```bash
# 1. 安装 MkDocs 和 Material 主题
pip install mkdocs mkdocs-material

# 2. 在 workspace 目录初始化（或指向现有 MD 目录）
cd /home/noname/.openclaw/workspace
mkdocs new .  # 如果已有 MD 文件，只需创建 mkdocs.yml

# 3. 配置 mkdocs.yml
cat > mkdocs.yml << 'EOF'
site_name: My Knowledge Base
theme:
  name: material
  features:
    - search.suggest
    - search.highlight
    - navigation.instant
plugins:
  - search
docs_dir: .
site_dir: /tmp/mkdocs-site
EOF

# 4. 构建并启动
mkdocs build
mkdocs serve -a 127.0.0.1:8000

# 5. Tailscale Serve（tailnet 内访问）
tailscale serve --bg 8000 http://127.0.0.1:8000

# 6. （可选）Tailscale Funnel（公网访问）
tailscale funnel --bg 443 http://127.0.0.1:8000
```

**注意**：`docs_dir: .` 会将整个 workspace 作为文档源，可用 `exclude_docs` 过滤不需要的文件。

### 🥈 方案 B：Tailscale + mdBook（更轻量）

适合不希望依赖 Python 环境、追求极致轻量的场景：

```bash
# 1. 下载 mdBook 单二进制
curl -sSL https://github.com/rust-lang/mdBook/releases/latest/download/mdbook-v*-x86_64-unknown-linux-gnu.tar.gz | tar -xz -C ~/.local/bin/

# 2. 初始化
cd /home/noname/.openclaw/workspace
mdbook init

# 3. 配置 book.toml（支持搜索默认开启）
# 4. 构建
mdbook build -d /tmp/mdbook-site

# 5. 启动并暴露
mdbook serve -n 127.0.0.1:3000
tailscale serve --bg 3000 http://127.0.0.1:3000
```

---

## 三、实践建议

1. **优先用 Tailscale Serve**（非 Funnel）：带宽无限制，速度更快，安全性更高。只有需要在未安装 Tailscale 的设备上访问时才开启 Funnel
2. **安全提示**：Funnel 暴露的服务对全互联网可见，建议搭配 HTTP Basic Auth 或仅对特定路径开放。MkDocs 无内置认证，可用 Caddy 反代加认证 [4]
3. **自动重建**：可用 `inotifywait` 或 systemd watch 监控 MD 文件变化，自动触发 `mkdocs build`
4. **OpenClaw Agent 查询**作为补充：日常用 Web 界面浏览，需要"找出某段内容"时直接在 Telegram 问 agent

---

## 四、知识缺口

| 缺口 | 影响程度 | 建议 |
|------|----------|------|
| Funnel 在中国大陆的实际访问速度和稳定性 | 中 | 实际测试后再决定是否启用 |
| MkDocs/mdBook 全文搜索对中文的分词效果 | 中 | 需实际测试，可能需要额外插件 |
| OpenClaw Control UI 文件浏览器功能进展 | 低 | 关注 GitHub Issue #8192 |
| 各方案实际资源占用（RAM/CPU）对比 | 低 | 量化数据缺失但不影响方案选择 |

---

## 五、来源列表

| # | 标题 | 类型 | URL |
|---|------|------|-----|
| [1] | Tailscale Funnel · Tailscale Docs | 官方文档 | https://tailscale.com/docs/features/tailscale-funnel |
| [2] | Tailscale Serve · Tailscale Docs | 官方文档 | https://tailscale.com/docs/features/tailscale-serve |
| [3] | Tailscale Funnel examples · Tailscale Docs | 官方文档 | https://tailscale.com/docs/reference/examples/funnel |
| [4] | Use Caddy to manage Tailscale HTTPS certificates | 官方博客 | https://tailscale.com/blog/caddy |
| [5] | coder/code-server: VS Code in the browser | GitHub | https://github.com/coder/code-server |
| [6] | GitHub Pages limits | 官方文档 | https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits |
| [7] | Text in, docs out: Popular Markdown documentation tools compared | 技术博客 | https://www.azalio.io/text-in-docs-out-popular-markdown-documentation-tools-compared/ |
| [8] | MkDocs vs Docusaurus for technical documentation | 技术博客 | https://blog.damavis.com/en/mkdocs-vs-docusaurus-for-technical-documentation/ |
| [9] | denzyldick/mserver | GitHub | https://github.com/denzyldick/mserver |

---

## 六、方法论反思

**做得好**：4 角度并行搜索效率高；Tailscale 方案调研充分（官方文档支撑强）；方案对比有实际操作性

**需改进**：OpenClaw 相关发现来源可信度偏低（缺少一手官方文档）；缺少各方案的实际部署测试数据；中文搜索能力评估不足
