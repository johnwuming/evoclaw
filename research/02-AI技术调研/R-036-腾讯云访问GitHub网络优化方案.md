# R-036 腾讯云访问 GitHub 网络优化方案

> 2026-04-07 | 研究搜索员调研

## 问题概述

腾讯云 VPS 上 git push 到 github.com 频繁失败，错误包括 GnuTLS recv error (-110) 和 port 443 连接超时（130s+）。根因是 GitHub CDN 域名（如 `github.global.ssl.fastly.net`）的 DNS 解析在国内被污染或返回不稳定 IP，导致 TLS 握手或 TCP 连接失败。

---

## 方案评估

### 方案 1：Hosts 固定 IP + DNS 优化 ⭐ 推荐

**原理**：绕过国内 DNS 解析，直接将 GitHub 域名指向可达的 IP。

**操作步骤**：

```bash
# 1. 获取当前最佳 IP（手动或脚本化）
# 使用 https://www.ipaddress.com/ 或 https://github.com.com/ 查询
# 常见可用 IP（2025-2026 年验证）：
# github.com → 20.205.243.166 或 140.82.114.4
# github.global.ssl.fastly.net → 199.232.69.194
# objects.githubusercontent.com → 185.199.108.153
# raw.githubusercontent.com → 185.199.108.133

# 2. 写入 /etc/hosts
echo "20.205.243.166 github.com
140.82.114.4 gist.github.com
199.232.69.194 github.global.ssl.fastly.net
185.199.108.153 objects.githubusercontent.com
185.199.108.133 raw.githubusercontent.com
185.199.108.133 gist.githubusercontent.com
185.199.108.133 camo.githubusercontent.com
185.199.108.133 avatars.githubusercontent.com" >> /etc/hosts

# 3. 刷新 DNS 缓存
resolvectl flush_caches 2>/dev/null || systemctl restart nscd 2>/dev/null || true
```

**优点**：零成本、立竿见影、无需额外服务
**缺点**：IP 可能随时间失效，需定期更新（建议每月检查）
**自动化**：可写脚本定期验证并更新 hosts

来源：[腾讯云开发者社区 - 优化hosts](https://cloud.tencent.com/developer/article/1997069)、[知乎 - 腾讯云服务器GitHub高速下载](https://zhuanlan.zhihu.com/p/648833253)

---

### 方案 2：Gitee 镜像中转 ⭐ 推荐

**原理**：git push 先推到 Gitee（国内稳定），Gitee 再自动镜像同步到 GitHub。

**操作步骤**：

1. 在 Gitee 创建对应仓库
2. 配置仓库镜像管理（Gitee → 管理 → 仓库镜像管理 → 添加 Push 方向镜像）
3. 填入 GitHub 仓库地址和 GitHub Personal Access Token
4. 修改本地 git remote，先 push Gitee，Gitee 自动同步到 GitHub

```
# 本地添加 Gitee 远程
git remote add gitee https://gitee.com/yourname/repo.git
# 或直接替换
git remote set-url origin https://gitee.com/yourname/repo.git
```

**优点**：push 到 Gitee 几乎不会失败，同步到 GitHub 由 Gitee 服务端处理（有重试机制）
**缺点**：有几分钟延迟、需维护 Gitee 仓库、Gitee 镜像同步偶尔也会失败
**成本**：免费

来源：[Gitee 帮助中心 - 仓库镜像管理](https://help.gitee.com/repository/settings/sync-between-gitee-github)

---

### 方案 3：SSH over 443 端口

**原理**：SSH 22 端口常被运营商封阻，GitHub 支持通过 443 端口走 SSH。

```bash
# ~/.ssh/config 添加
Host github.com
    Hostname ssh.github.com
    User git
    Port 443

# 测试
ssh -T -p 443 git@ssh.github.com

# 切换 remote 为 SSH
git remote set-url origin git@github.com:user/repo.git
```

**优点**：443 端口一般不被封阻
**缺点**：SSH 传输大文件仍受网络影响，非根本解决方案
**适合**：作为 hosts 方案的补充

来源：[GitHub 官方文档](https://docs.github.com/zh/authentication/troubleshooting-ssh/using-ssh-over-the-https-port)

---

### 方案 4：Git 参数调优 + 增强重试

**立即可做的配置**：

```bash
# 增大 HTTP 缓冲区（解决大 push 失败）
git config --global http.postBuffer 524288000

# 增大超时
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999

# SSH KeepAlive
# ~/.ssh/config 加：
# ServerAliveInterval 60
# ServerAliveCountMax 3
```

**auto-sync.sh 增强重试**：

```bash
MAX_RETRIES=10
RETRY_DELAY=30  # 秒，指数退避

for i in $(seq 1 $MAX_RETRIES); do
    if git push origin main; then
        break
    fi
    delay=$((RETRY_DELAY * (2 ** (i-1))))
    sleep $delay
done
```

**优点**：零成本，立即可用
**缺点**：不解决根本网络问题，重试多了也只是碰运气

---

### 方案 5：HTTP 代理

**方案**：在可访问 GitHub 的境外 VPS 上搭建代理（如 squid/nginx stream forward），腾讯云通过代理访问。

```bash
git config --global http.proxy http://proxy-server:port
git config --global https.proxy http://proxy-server:port
```

**优点**：最稳定
**缺点**：需要额外服务器，有维护成本，增加延迟

---

## 不推荐的方案

| 方案 | 原因 |
|------|------|
| ghproxy.com 等第三方加速 | 仅加速 clone/download，不支持 push |
| GitHub API 替代 git push | 单文件 API 调用次数有限，不适合批量同步 |
| 腾讯云安全组放行 | 出站规则默认全放行，不是问题所在 |

---

## 最终推荐

### 🥇 首选：Hosts 固定 IP + 增强重试

成本为零，5 分钟部署。在 auto-sync.sh 中加入 IP 可达性检查（push 前先 curl 测试 github.com），失败则自动切换备用 IP。

### 🥈 备选：Gitee 镜像中转

如果 hosts 方案仍不稳定（IP 频繁变化），用 Gitee 做中转。push 到 Gitee 几乎不会失败，Gitee 服务端负责同步 GitHub。几分钟延迟对自动同步场景完全可接受。

### 建议的组合策略

1. **立即执行**：hosts 固定 IP + git 参数调优 + 增强重试（10 次指数退避）
2. **如果仍不稳定**：启用 Gitee 镜像中转作为 fallback
3. **可选**：SSH over 443 替代 HTTPS

---

## 来源

- [腾讯云 - 完美优化Github访问缓慢问题](https://cloud.tencent.com/developer/article/1997069)
- [知乎 - 基于hosts修改的腾讯云服务器GitHub高速下载](https://zhuanlan.zhihu.com/p/648833253)
- [Gitee 帮助中心 - 仓库镜像管理](https://help.gitee.com/repository/settings/sync-between-gitee-github)
- [GitHub Docs - SSH over HTTPS port](https://docs.github.com/zh/authentication/troubleshooting-ssh/using-ssh-over-the-https-port)
- [掘金 - Git fatal remote end hung up unexpectedly](https://juejin.cn/post/7488256354127183913)
- [腾讯云 - 9种提高GitHub访问速度方案](https://cloud.tencent.com/developer/article/1920978)
