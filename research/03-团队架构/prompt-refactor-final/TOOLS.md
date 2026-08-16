# TOOLS.md — 环境事实与工具速查（优化稿）

> 本文件只放“下一次操作需要的事实”。排查过程、根因故事放 `memory/YYYY-MM-DD.md`。
> **明文秘密禁止写入本文件。** 秘密统一放 `/root/.openclaw/secrets.env`（chmod 600），本文件只引用变量。

## 秘密读取约定

| 用途 | 读取方式 | 示例 |
|---|---|---|
| NAS SSH | 首选 SSH key；备选从 secrets.env 读 `NAS_SSH_PASSWORD` | `ssh -i ~/.ssh/id_nas -p 222 wuming@10.12.192.241` 或 `sshpass -p "$NAS_SSH_PASSWORD" ssh -p 222 wuming@10.12.192.241` |
| DSH 访问码 | secrets.env 的 `DSH_ACCESS_CODE` | 登录时从环境变量取，不打印、不贴进回复 |
| sudo 密码 | secrets.env 的 `SUDO_PASSWORD` | 仅脚本使用；当前 root 环境优先用免密方式，不把密码写命令行 |

创建方式（只执行一次，不要写入值到本文件）：

```bash
touch /root/.openclaw/secrets.env && chmod 600 /root/.openclaw/secrets.env
```

首次迁移清单（从旧 TOOLS.md 抽取，迁完即验证可用）：`NAS_SSH_PASSWORD`、`SUDO_PASSWORD`、`DSH_ACCESS_CODE`、`QUANT_SSH_PASSWORD`（HP 量化主机）。已暴露于旧文件的密码建议同期轮换（机器有入侵史）。

## 服务速查

| 服务 | 地址 | 认证 | 常驻/日志 |
|---|---|---|---|
| DeepSeek Harness (DSH) | `https://82.156.124.186:6080` | 访问码 + Cookie（`$DSH_ACCESS_CODE`） | `dsh-web.service`；日志 `journalctl -u dsh-web` |
| 账单编辑器 | `https://82.156.124.186:8052` | 站点认证 | 项目 `/root/.openclaw/workspace/tools/bill-editor/`；systemd 单元用 `systemctl list-units | grep -i bill` 确认 |
| WSS 网关 | `https://82.156.124.186:8060` | — | 按 nginx 配置 |

## HTTPS 证书（Let's Encrypt IP 证书）

- 证书：`/etc/nginx/ssl/ip-fullchain.cer` + `/etc/nginx/ssl/ip.key`，仅 IP SAN，6 天有效期。
- 续期：`ip-cert-renew.timer` 每 12h 调 `/usr/local/bin/ip-cert-renew.sh`。
- 全站强制 HTTPS，明文 http 返回 400。
- 排查：`journalctl -t ip-cert-renew`；`/tmp/ip-cert-renew.log`；`openssl s_client -connect 82.156.124.186:6080`。

## DSH 运维要点（只保留操作必需项）

- 服务监听 `127.0.0.1:3080`，systemd 常驻。
- nginx `/api/` 块中有两行关键重写：`Host=127.0.0.1` 和 `Origin=http://127.0.0.1`（用于特权 API 回环校验）。**新增 location 时不要改这两行。**
- 普通 API 依赖 systemd ExecStart 中的 `--trusted-host`（已包含公网 IP）。
- 登录页：`/etc/nginx/dsh-gate.html`；认证路径 `/__gate`。
- 排查历史（basic auth 弹窗根因、双栅栏细节）见 `memory/` 对应日期笔记，不写在本文件。

## 群晖 NAS

- ZeroTier：网络 `a581878f7dc4f35d`；NAS `10.12.192.241`，VPS `10.12.192.225`。
- SSH：端口 `222`，用户 `wuming`，用 SSH key（或 secrets.env 密码变量）。
- Docker：`/usr/local/bin/docker`；配置目录 `/volume1/docker/`。
- 运行容器：`seerr、sonarr、radarr、prowlarr、flaresolverr、chinesesubfinder、jproxy、homeassistant、zerotier、portainer、mysql`。
- Seerr：容器名 `seerr`，端口 `5055:5055`，配置 `/volume1/docker/overseerr/config`。
  - 重建时必须带 `--dns 8.8.8.8 --dns 1.1.1.1`，否则 TMDB 图片加载失败。
  - Seerr 访问 Radarr/Sonarr/Plex 用 Docker 网关 `172.17.0.1`（NAS 自身 LAN IP 在容器内不可达）。
  - 旧容器 `linuxserver-overseerr-old` 与备份 `overseerr-config-backup-20260802.tar.gz` 仅作回滚，不再更新。

## ASR

- SenseVoice：`venv-asr/bin/python3 scripts/sensevoice-cli.py <file>`
- GLM-ASR：`venv-asr/bin/python3 scripts/glm-asr-cli.py <file>`（需要 `ZAI_API_KEY`）
- whisper-cli：`/usr/local/bin/whisper-cli`
- ffmpeg：已安装
- 模型：`/home/noname/.openclaw/workspace/models/SenseVoiceSmall/`
- venv：`/home/noname/.openclaw/workspace/venv-asr/`

## GitHub

- 仓库：`evoclaw`（原名 evolving-claw-repo）
- Remote：`https://github.com/johnwuming/evoclaw.git`
- 本地路径：`/root/.openclaw/evolving-claw-repo/`（目录名未改）

## 维护规则

- 新增环境事实：只加一行或一行表格；背景故事写 memory。
- 秘密变更：先更新 `secrets.env`，本文件只改变量名。
- 过期条目直接删除，不用删除线堆历史。
