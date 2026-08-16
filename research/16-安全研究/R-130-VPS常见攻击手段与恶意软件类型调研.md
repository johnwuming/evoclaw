# R-130 VPS常见攻击手段与恶意软件类型调研

> **研究编号**: R-130  
> **分类**: 05-安全研究  
> **完成日期**: 2026-07-03  
> **研究周期**: 2023-2026  
> **数据来源**: MITRE ATT&CK, CrowdStrike 2026全球威胁报告, OWASP Top 10:2025, IBM, Aqua Security, 腾讯云安全文档, NVD, CIS Benchmarks  

---

## 目录

1. [攻击入口与途径](#1-攻击入口与途径)
2. [恶意软件类型与行为特征](#2-恶意软件类型与行为特征)
3. [持久化机制大全](#3-持久化机制大全)
4. [日志清理与隐藏手段](#4-日志清理与隐藏手段)
5. [近年实际案例（2023-2026）](#5-近年实际案例2023-2026)
6. [VPS安全自查清单](#6-vps安全自查清单)
7. [来源列表](#7-来源列表)

---

## 1. 攻击入口与途径

### 1.1 SSH暴力破解

| 项目 | 详情 |
|------|------|
| **攻击原理** | 攻击者使用自动化工具（Hydra、John the Ripper、Hashcat、Ncrack）对SSH服务进行持续密码猜测。IBM报告显示，全球性暴力破解活动曾利用近**300万个独立IP**同时发起攻击。微软数据显示平均**每秒阻止4000次**身份攻击。 |
| **常见手段** | ①字典攻击（常见密码列表如123456、admin、password）；②混合攻击（常见词+数字符号变体如Spring2025!）；③凭证填充（使用泄露数据库批量尝试登录）。 |
| **高危特征** | 中国VPS因暴露SSH端口（默认22）且大量使用弱密码，是暴力破解的重灾区。暴力破解约占确认安全违规的**5%**。 |
| **检测方法** | ①监控 `/var/log/auth.log` 中的 Failed password 记录；②统计同IP短时间失败次数；③使用 `lastb` 查看失败登录尝试；④部署 fail2ban/fail2ban-regex 分析日志。 |
| **防护措施** | ①**密钥认证替代密码**（最有效）；②修改默认SSH端口（22→随机高端口）；③部署 fail2ban 自动封禁IP；④限制登录IP白名单（安全组/hosts.allow）；⑤启用双因素认证；⑥设置 MaxAuthTries 和 LoginGraceTime。 |
| **MITRE ATT&CK** | T1110 Brute Force |

### 1.2 Web应用漏洞利用（RCE）

| 项目 | 详情 |
|------|------|
| **攻击原理** | 利用Web应用的未修补漏洞实现远程代码执行。OWASP Top 10:2025排名前列的风险：A01越权访问、A02安全配置错误、A05注入攻击。CrowdStrike 2026报告显示**82%的检测为无恶意软件攻击**（malware-free），攻击者更多利用合法工具和配置缺陷。 |
| **典型攻击路径** | ①未修补框架漏洞（Apache Struts、Spring Framework、Laravel）；②反序列化漏洞；③SSRF→内网渗透；④文件上传漏洞→WebShell；⑤SQL注入→数据窃取。 |
| **高危趋势** | **边缘设备**（VPN、防火墙、负载均衡器）成为2024-2025年最重要的初始访问入口之一。中国关联攻击者**40%的漏洞利用针对边缘设备**。云环境入侵同比增长**266%**。 |
| **检测方法** | ①Web应用防火墙（WAF）日志分析；②文件完整性监控（FIM）；③监控Web目录下新增/修改的文件；④OSSEC/Wazuh等HIDS告警。 |
| **防护措施** | ①及时修补漏洞（关注CVE和KEV目录）；②部署WAF；③最小权限原则运行Web服务；④禁用危险函数；⑤定期漏洞扫描。 |
| **MITRE ATT&CK** | T1190 Exploit Public-Facing Application |

### 1.3 数据库弱密码与暴露端口

| 项目 | 详情 |
|------|------|
| **攻击原理** | 暴露在公网的数据库服务是VPS最常被扫描和攻击的目标。攻击者通过Shodan/Censys扫描暴露端口→尝试默认凭据或无认证连接→植入挖矿木马/勒索/数据窃取。 |
| **高危服务** | **Redis**（默认无认证，绑定0.0.0.0）、**MongoDB**（默认无认证）、**MySQL**（弱密码）、**ElasticSearch**（默认无认证）。 |
| **国内云环境特点** | 腾讯云和阿里云环境下常见问题：安全组未正确配置导致数据库端口（3306/6379/27017/9200等）暴露公网。 |
| **检测方法** | ①定期检查安全组规则，确认数据库端口未对公网开放；②使用 `ss -tlnp` 检查监听端口；③外部端口扫描（nmap）。 |
| **防护措施** | ①数据库端口仅对内网开放；②启用认证和TLS加密；③使用安全组/iptables严格限制源IP；④Redis配置 `bind 127.0.0.1` + `requirepass`；⑤MongoDB启用 `--auth`。 |

### 1.4 容器逃逸攻击

| 项目 | 详情 |
|------|------|
| **攻击原理** | 容器环境通过namespace和cgroups实现隔离，但配置不当可导致逃逸。逃逸后攻击者获取宿主机完全控制权，可横向移动到同集群其他节点。 |
| **典型逃逸路径** | ①内核漏洞利用（如CVE-2022-0847 Dirty Pipe类漏洞）；②Docker socket暴露（挂载 `/var/run/docker.sock`）；③privileged模式滥用；④namespace隔离不充分；⑤危险capabilities（CAP_SYS_ADMIN等）。 |
| **检测方法** | ①监控容器内执行特权操作；②检查容器是否以 `--privileged` 运行；③审计Docker socket访问；④使用Falco/Tracee运行时安全监控。 |
| **防护措施** | ①避免privileged模式；②使用非root用户运行容器；③限制capabilities（`--cap-drop ALL`）；④不挂载宿主机敏感路径；⑤及时修补内核漏洞；⑥使用gVisor/Kata Containers增强隔离。 |

### 1.5 供应链攻击

| 项目 | 详情 |
|------|------|
| **攻击原理** | OWASP Top 10:2025将软件供应链失败列为**第3大风险**（A03:2025）。攻击者通过投毒公共包仓库实现大规模分发。 |
| **常见手法** | ①Typosquatting（仿冒包名如 `reqeusts` 代替 `requests`）；②恶意更新（维护者账号被盗后发布带后门版本）；③依赖混淆（上传与内部私有包同名的恶意包）；④恶意容器镜像。 |
| **检测方法** | ①锁文件完整性校验（package-lock.json/requirements.txt哈希）；②SBOM（软件物料清单）分析；③私有仓库代理+白名单。 |
| **防护措施** | ①锁定依赖版本；②使用私有仓库镜像；③生成并验证SBOM；④定期扫描依赖漏洞（Snyk/Trivy）。 |

### 1.6 AI增强攻击（新兴威胁）

| 项目 | 详情 |
|------|------|
| **攻击原理** | CrowdStrike 2026报告揭示**AI驱动攻击同比增长89%**。攻击者利用AI更快速地发现暴露服务、生成针对性利用代码、自动化漏洞扫描和利用链构建。 |
| **关键数据** | 最快一次电子犯罪突破（breakout time）仅耗时**27秒**，同比平均突破速度提升**65%**。ChatGPT在犯罪论坛中被提及频率比其他模型高**550%**。 |
| **防护启示** | VPS从被攻破到完全失控的窗口期极短，需要实时检测和自动化响应（SOAR）。 |

---

## 2. 恶意软件类型与行为特征

### 2.1 挖矿木马（国内云服务器最常见威胁）

**代表家族**：Kinsing（S0599）、TeamTNT（G0139）、XMRig（滥用）、Hildegard（S0601）、Skidmap（S0468）

| 项目 | 详情 |
|------|------|
| **攻击原理** | 部署加密货币挖矿程序（主要挖Monero/XMR），消耗服务器CPU资源。腾讯云数据显示挖矿木马是**国内云服务器最常见安全威胁**。 |
| **行为特征** | ①CPU持续100%占用；②异常进程（`kdevtmpfsi`、`kinsing`、`xmrig`）；③矿机文件常位于 `/tmp/`；④持久化通过crontab/bashrc/rc.local；⑤使用 `/etc/ld.so.preload` hook libc隐藏进程。 |
| **传播方式** | ①利用CVE漏洞（如CVE-2023-32315 Openfire）；②配置错误的Docker API（2375端口）；③暴露的Redis（6379）写入SSH key/crontab；④暴露的Kubelet API（10250）。 |
| **IOC指标** | 进程名：`kdevtmpfsi`、`kinsing`、`xmrig`；文件路径：`/tmp/kdevtmpfsi`、`/tmp/.X11-unix/`；持久化：crontab、bashrc、ld.so.preload。 |
| **高级隐蔽** | Skidmap使用内核rootkit**伪造CPU使用率**，使top命令显示正常值。Hildegard修改 `/etc/ld.so.preload` hook readdir使 `ls` 看不到矿机文件。 |
| **检测方法** | ①监控CPU使用率异常（注意Skidmap可伪造）；②`ps aux --sort=-%cpu | head -20`；③检查 `/tmp/` 和 `/dev/shm/` 下可执行文件；④crontab -l 检查定时任务；⑤对比 `lsmod` 与 `/proc/modules`。 |
| **防护措施** | ①关闭不必要的端口；②Redis/MongoDB不暴露公网；③Docker API加TLS认证；④部署HIDS（OSSEC/Wazuh/腾讯云主机安全）。 |

### 2.2 DDoS僵尸网络

**代表家族**：Mirai变种、Linux Rabbit（S0362）、NKAbuse（S1107）、KV Botnet（C0035）

| 项目 | 详情 |
|------|------|
| **攻击原理** | 将VPS纳入僵尸网络，听从C2指令发起DDoS攻击。通过扫描Telnet(23/2323/9527)/SSH(22)端口暴力破解弱密码传播。 |
| **行为特征** | ①异常出站流量激增（腾讯云检测为"外发流量异常"）；②连接未知IRC服务器；③监听异常端口；④通过rc.local和.bashrc持久化。 |
| **演化趋势** | Mirai变种集成更多CVE漏洞利用模块，攻击范围从IoT扩展到云服务器。2024年KV Botnet利用路由器组建僵尸网络。NKAbuse为2023-2024新出现的基于Go的DDoS工具。 |
| **检测方法** | ①监控出站流量异常突增；②`netstat -antp` 检查异常连接；③检查IRC相关端口（6667等）。 |
| **防护措施** | ①修改默认密码；②关闭Telnet服务；③配置安全组限制出站流量；④部署DDoS防护。 |

### 2.3 后门程序

**代表家族**：BPFDoor（S1161）、COATHANGER（S1105）、Chaos（S0220）、Exaramel for Linux（S0401）

| 类型 | 详情 |
|------|------|
| **Reverse Shell后门** | BPFDoor利用BPF过滤器隐藏通信，创建reverse shell并支持vt100终端格式化；COATHANGER针对FortiGate防火墙提供BusyBox reverse shell；Chaos在8338/TCP上提供AES加密的reverse shell。 |
| **Web Shell** | 通过漏洞上传cmd.jsp/cmd.php等，Kinsing攻击链中使用Java webshell作为初始入口。ASPXSpy（S0073）是典型webshell。 |
| **C2框架后门** | Exaramel for Linux（S0401）可执行shell命令，由Telebot(Sandworm)使用。J-magic（S1203）通过magic packet激活的后门。 |
| **检测难点** | 这些后门通常使用合法端口(443/80)通信，或使用BPF过滤器绕过netstat检测。 |
| **检测方法** | ①监控异常出站连接（特别是未知IP的443/80）；②检查Web目录下的可疑文件；③使用 `lsof -i` 分析网络连接；④部署NIDS（Suricata/Zeek）。 |
| **防护措施** | ①文件完整性监控；②Web目录只读挂载；③限制出站连接（egress filtering）；④定期Web Shell扫描。 |

### 2.4 Rootkit

**代表家族**：Diamorphine（开源）、REPTILE（S1219）、Drovorub（S0502）、Skidmap（S0468）、Ebury（S0377）、MEDUSA（S1220）

| 类型 | 说明 |
|------|------|
| **内核态Rootkit (LKM)** | 运行在Ring 0，hook系统调用隐藏进程/文件/网络连接。Diamorphine被TeamTNT广泛使用；Drovorub由俄罗斯GRU使用；Skidmap**伪造CPU使用率**使挖矿不被发现；REPTILE和MEDUSA被UNC3886用于针对VMware ESXi。 |
| **用户态Rootkit** | 通过LD_PRELOAD hook libc函数。Ebury作为SSH后门+用户态rootkit；Hildegard和Rocke修改 `/etc/ld.so.preload` hook readdir隐藏矿机；Winnti for Linux使用Azazel rootkit变体。 |
| **检测方法** | ①对比 `lsmod` 输出与 `/proc/modules`；②检查 `/etc/ld.so.preload` 是否存在；③使用rkhunter/chkrootkit扫描；④内核完整性检查（IMA）；⑤内存取证分析（Volatility）。 |

### 2.5 勒索软件与擦除器

**代表家族**：Akira（S1129）、AcidRain（S1125）、AcidPour（S1167）

| 项目 | 详情 |
|------|------|
| **攻击原理** | 加密或销毁服务器数据以勒索赎金，或纯粹破坏（wiper）。Linux ESXi勒索软件成为主流，因可一次性加密多台VM。 |
| **Akira (RaaS)** | C++编写，使用ChaCha20/ChaCha8流密码加密。有专门针对VMware ESXi的Akira_v2（Rust编写）变体。攻击北美/欧洲/澳洲制造业和教育业。 |
| **AcidRain** | ELF二进制，针对MIPS架构调制解调器/路由器。2022年乌克兰冲突中用于ViaSat KA-SAT通信中断，关联Sandworm。 |
| **AcidPour** | AcidRain的x86变体，可擦除UBI/DM/flash内存存储设备并自我删除。2023年针对乌克兰ISP。 |
| **2025趋势** | 波兰能源行业遭Linux wiper攻击（使用dd覆盖磁盘数据）。Linux ESXi勒索继续增长。 |
| **检测方法** | ①监控批量文件修改/加密操作；②监控 `dd` 命令对块设备的写入；③文件完整性监控告警。 |
| **防护措施** | ①定期离线备份（3-2-1规则）；②最小权限原则；③及时修补漏洞；④网络分段隔离关键系统。 |

---

## 3. 持久化机制大全

攻击者在成功入侵后，会建立持久化机制确保重启后仍能保持访问。以下是 Linux VPS 上已知的持久化技术全景：

### 3.1 systemd 服务持久化

| 项目 | 详情 |
|------|------|
| **原理** | 创建恶意 `.service` 单元文件，配置 `WantedBy=multi-user.target` 实现开机自启。 |
| **技术路径** | `/etc/systemd/system/`（管理员级）、`/lib/systemd/system/`（包管理器级）。`/etc/systemd/system/` 优先级高于 `/lib/systemd/system/`（同名覆盖）。 |
| **示例** | 创建 `/etc/systemd/system/bad.service`：`ExecStart=/opt/backdoor`，`WantedBy=multi-user.target`。启用：`systemctl enable bad`。 |
| **检测** | ①`systemctl list-unit-files --state=enabled` 查找未知服务；②auditd: `-w /etc/systemd/system/ -p wa -k systemd_persist`；③`systemd-analyze unit-paths` 枚举加载路径。 |
| **MITRE** | T1543.002 System Services |

### 3.2 systemd Timer 持久化

| 项目 | 详情 |
|------|------|
| **原理** | 创建 `.timer` 单元文件配合同名 `.service`，比cron更隐蔽。 |
| **示例** | `/etc/systemd/system/bad.timer`：`OnCalendar=*:0/15`（每15分钟）。启用：`systemctl enable --now bad.timer`。 |
| **检测** | ①`systemctl list-timers --all`；②检查 `/etc/systemd/system/` 下 `.timer` 文件。 |
| **MITRE** | T1053.006 Systemd Timers |

### 3.3 cron 定时任务持久化

| 项目 | 详情 |
|------|------|
| **原理** | 添加计划任务实现持久化，包括 `@reboot`（启动时执行）或定时执行。 |
| **技术路径** | 用户级：`/var/spool/cron/crontabs/`（`crontab -e`）；系统级：`/etc/crontab`、`/etc/cron.d/`、`/etc/cron.hourly/`、`/etc/cron.daily/`。 |
| **示例** | `*/30 * * * * /tmp/backdoor`（每30分钟）；`@reboot /opt/payload`（开机执行）。 |
| **检测** | ①`crontab -l -u <user>` 列出各用户cron；②检查 `/etc/crontab`、`/etc/cron.d/*`、`/etc/cron.*/`；③auditd: `-w /etc/cron.d/ -p wa -k cron_persist`。 |
| **MITRE** | T1053.003 Cron |

### 3.4 SSH authorized_keys 后门

| 项目 | 详情 |
|------|------|
| **原理** | 追加攻击者公钥到 `~/.ssh/authorized_keys`，实现免密码SSH持久化登录。 |
| **技术细节** | 直接添加：`echo 'ssh-rsa AAAA...攻击者公钥...' >> /root/.ssh/authorized_keys`。可能同时修改 `sshd_config`：`PermitRootLogin yes`、`PubkeyAuthentication yes`。云环境（GCP/Azure）可通过API修改。 |
| **检测** | ①监控 `authorized_keys` 文件变化；②auditd: `-w /root/.ssh/authorized_keys -p wa -k ssh_key_mod`；③对比已知合法SSH密钥列表；④检查 `sshd_config` 是否被异常修改。 |
| **MITRE** | T1098.004 SSH Authorized Keys |

### 3.5 内核模块（LKM）持久化

| 项目 | 详情 |
|------|------|
| **原理** | 加载恶意内核模块（.ko），运行在Ring 0最高权限，实现进程/文件/网络隐藏。 |
| **加载方式** | 直接加载：`insmod /path/to/malicious.ko`；通过modprobe：放入 `/lib/modules/$(uname -r)/` + `depmod -a` + `modprobe`。开机自加载：写入 `/etc/modules-load.d/backdoor.conf`。 |
| **已知工具** | Diamorphine（进程隐藏+root提权+魔法kill）、Reptile（隐藏进程/网络/文件）。实际恶意软件：Drovorub（GRU）、Skidmap、TeamTNT使用Diamorphine。 |
| **检测** | ①`lsmod` 列出已加载模块，对比已知清单；②检查 `/etc/modules` 和 `/etc/modules-load.d/`；③auditd: `-w /sbin/insmod -p x -k module_load`；④检查 `/sys/module/` 中未知模块；⑤对比 `/proc/modules` 与 `lsmod` 输出差异。 |
| **MITRE** | T1547.006 Kernel Modules / T1014 Rootkit |

### 3.6 Shell 配置文件后门

| 项目 | 详情 |
|------|------|
| **原理** | 用户登录或打开终端时，shell依次执行配置脚本，攻击者在其中插入恶意命令。 |
| **系统级** | `/etc/profile`、`/etc/profile.d/*.sh`、`/etc/bash.bashrc`（对所有用户生效）。 |
| **用户级** | `~/.bash_profile`（优先）、`~/.bash_login`、`~/.profile`、`~/.bashrc`、`~/.bash_logout`。 |
| **检测** | ①auditd: `-w /etc/profile -p wa -k shell_config`、`-w /etc/profile.d/ -p wa`；②检查所有用户家目录中的shell配置文件；③监控文件时间戳异常变化。 |
| **MITRE** | T1546.004 Unix Shell Config Modification |

### 3.7 rc.local 与 init.d 持久化

| 项目 | 详情 |
|------|------|
| **原理** | rc.local和init.d脚本在系统启动时执行。新版Linux的systemd-rc-local-generator会自动检测 `/etc/rc.local` 是否存在且可执行，若存在则创建rc-local.service。 |
| **技术细节** | 创建 `/etc/rc.local`（`#!/bin/bash` + 恶意命令），`chmod +x /etc/rc.local`。init.d：在 `/etc/init.d/` 创建脚本 + `update-rc.d enable`。 |
| **检测** | ①检查 `/etc/rc.local` 是否存在且可执行（新系统中通常不存在）；②`systemctl status rc-local` 检查是否激活；③检查 `/etc/init.d/` 脚本清单；④auditd: `-w /etc/rc.local -p wa -k rclocal`。 |

### 3.8 LD_PRELOAD 动态链接器劫持

| 项目 | 详情 |
|------|------|
| **原理** | 通过LD_PRELOAD环境变量或 `/etc/ld.so.preload` 文件注入恶意共享库，hook系统函数（execve、readdir等），实现资源窃取、提权和隐藏。 |
| **全局持久化** | `echo '/path/to/malicious.so' >> /etc/ld.so.preload`（影响所有动态链接程序）。 |
| **会话级持久化** | `echo 'export LD_PRELOAD=/path/to/malicious.so' >> ~/.bashrc`。 |
| **已知恶意软件** | Ebury（hook SSH后门）、Hildegard（修改ld.so.preload hook readdir隐藏挖矿软件）、Symbiote、Rocke。 |
| **检测** | ①检查 `/etc/ld.so.preload` 文件是否存在（正常系统通常不存在）；②`env \| grep LD_PRELOAD`；③auditd: `-w /etc/ld.so.preload -p wa -k ld_preload`；④对比系统库函数地址检测hook。 |
| **MITRE** | T1574.006 Dynamic Linker Hijacking |

### 3.9 systemd-generators 持久化（隐蔽性极高）

| 项目 | 详情 |
|------|------|
| **原理** | systemd generators在引导过程中**非常早期**执行——早于任何服务启动，也早于auditd/syslog/sysmon等安全传感器。可篡改服务文件、禁用安全监控。 |
| **投放路径** | `/etc/systemd/system-generators/`、`/usr/local/lib/systemd/system-generators/`、`/lib/systemd/system-generators/`。 |
| **危害** | generator可在 `/run/systemd/system/` 创建恶意服务并符号链接到 `multi-user.target.wants`，也可创建覆盖文件禁用 `sysmon.service` 和 `auditbeat.service`。 |
| **检测** | ①枚举generator目录，对比已知合法清单；②检查 `/run/systemd/system/` 和 `/run/systemd/generator.early/` 中的运行时生成文件。 |

### 3.10 motd 登录触发持久化

| 项目 | 详情 |
|------|------|
| **原理** | `/etc/update-motd.d/` 下的脚本在用户SSH登录时**以root权限**运行。攻击者在其中插入恶意命令，实现登录触发型持久化。 |
| **检测** | ①检查 `/etc/update-motd.d/` 目录下所有脚本内容；②auditd: `-w /etc/update-motd.d/ -p wa -k motd_persist`。 |

### 持久化机制速查表

| 机制 | 触发时机 | 文件/路径 | 隐蔽性 | 检测难度 |
|------|----------|-----------|--------|----------|
| systemd service | 开机 | `/etc/systemd/system/*.service` | 中 | 低 |
| systemd timer | 定时 | `/etc/systemd/system/*.timer` | 中高 | 中 |
| cron | 定时/开机 | `/etc/crontab`, `/etc/cron.d/` | 中 | 低 |
| SSH authorized_keys | SSH登录 | `~/.ssh/authorized_keys` | 中 | 低 |
| LKM rootkit | 加载即生效 | `/lib/modules/`, `/etc/modules-load.d/` | 极高 | 高 |
| Shell配置文件 | 打开终端 | `~/.bashrc`, `/etc/profile` | 中 | 低 |
| rc.local/init.d | 开机 | `/etc/rc.local`, `/etc/init.d/` | 低 | 低 |
| LD_PRELOAD | 程序执行 | `/etc/ld.so.preload` | 高 | 中高 |
| systemd-generator | 引导最早期 | `*-generators/` 目录 | 极高 | 高 |
| motd | SSH登录 | `/etc/update-motd.d/` | 中高 | 中 |

---

## 4. 日志清理与隐藏手段

### 4.1 命令历史清除

| 项目 | 详情 |
|------|------|
| **技术** | ①`history -c && rm -f ~/.bash_history`（清除当前会话历史并删除文件）；②`export HISTFILE=/dev/null`（重定向历史到空设备）；③`export HISTSIZE=0`（设置历史记录条数为0）；④`export HISTCONTROL=ignorespace`（命令前加空格则不记录）；⑤`shred -f -z -u ~/.bash_history`（安全删除，无法恢复）。 |
| **检测方法** | ①auditd: `-w /home/*/.bash_history -p wa -k hist_modification`；②检查HISTFILE和HISTSIZE环境变量异常设置；③使用远程日志服务器记录操作审计。 |
| **MITRE ATT&CK** | T1070.003 Clear Command History |

### 4.2 系统日志清除

| 项目 | 详情 |
|------|------|
| **技术** | ①`cat /dev/null > /var/log/syslog`（清空系统日志）；②`cat /dev/null > /var/log/auth.log`（清空认证日志）；③`rm /var/log/wtmp /var/log/btmp`（删除登录记录）；④`> /var/log/lastlog`（清除最后登录记录）；⑤篡改logrotate配置干扰日志轮转。 |
| **检测方法** | ①监控 `/var/log/` 目录文件大小突然归零；②检查wtmp/btmp/lastlog文件是否被截断：`ls -la /var/log/wtmp /var/log/btmp /var/log/lastlog`；③部署远程syslog服务器防止本地日志被篡改；④使用inotify监控关键日志文件。 |
| **MITRE ATT&CK** | T1070.002 Clear Linux or Mac System Logs |

### 4.3 隐藏文件与目录

| 项目 | 详情 |
|------|------|
| **技术** | ①以点(.)开头的文件/目录对默认 `ls` 不可见（如 `/tmp/.hidden_dir/`）；②伪装系统文件名（如 `/usr/sbin/sshd-backdoor`）；③`chattr +i` 设置不可变属性防止删除；④深层目录投放（如 `/usr/local/lib/.hidden/`）。 |
| **常见隐藏位置** | `/tmp/.*`、`/dev/shm/.*`、`/var/tmp/.*`、`/usr/local/lib/.*`。 |
| **实际案例** | COATHANGER创建隐藏安装目录；FIN13在 `/tmp` 创建隐藏目录；CoinTicker在 `/tmp` 投放 `.info.enc`、`.info.py` 等隐藏文件。 |
| **检测方法** | ①`ls -laR /tmp /dev/shm /var/tmp` 定期扫描临时目录；②`find / -name '.*' -type f` 搜索所有隐藏文件；③使用AIDE/Tripwire文件完整性监控；④检查 `/dev/shm` 中的可疑文件（正常应为空）；⑤监控 `chattr` 命令使用。 |
| **MITRE ATT&CK** | T1564.001 Hidden Files and Directories |

### 4.4 Rootkit 级隐藏

| 项目 | 详情 |
|------|------|
| **内核态隐藏** | Hook `sys_call_table`，拦截 `readdir`/`readdir64` 隐藏指定文件/进程/网络连接。Diamorphine通过魔法kill信号隐藏进程。Skidmap伪造CPU和网络统计数据，使top/vmstat显示正常值。 |
| **用户态隐藏** | LD_PRELOAD hook libc函数（readdir/execve/ptrace），使 `ls`、`ps`、`netstat` 等命令过滤恶意条目。Ebury hook SSH函数窃取凭证。 |
| **检测方法** | ①内存取证分析（Volatility框架）；②对比 `/proc/modules` 与 `lsmod` 输出；③从内存dump分析 `sys_call_table` 完整性；④使用 `strace` 分析函数调用差异；⑤部署文件完整性监控（AIDE/Tripwire）。 |
| **MITRE ATT&CK** | T1014 Rootkit |

---

## 5. 近年实际案例（2023-2026）

### 5.1 TeamTNT — Docker/K8s 蠕虫式挖矿攻击

| 项目 | 详情 |
|------|------|
| **时间** | 2021-2024年持续活跃 |
| **攻击链** | ①通过Docker Hub发布6个恶意容器镜像（wescopwn、tornadopwn、jaganod、awspwner等）；②扫描配置错误的Docker daemon（端口2375/2376）；③利用Kubeflow仪表板和Weave Scope入侵；④运行恶意容器→部署挖矿木马+蠕虫+后门；⑤窃取AWS凭证→扫描下一个受害者。 |
| **C2基础设施** | `45[.]9[.]148[.]85`、`borg[.]wtf`。 |
| **IOC** | Docker镜像名：wescopwn/tornadopwn/jaganod/awspwner；目标端口：Docker 2375/2376、Kubelet 10250。 |
| **来源** | Aqua Security详细分析 |

### 5.2 8220 挖矿团伙 — 全链路攻击 + 专门规避国内云安全

| 项目 | 详情 |
|------|------|
| **时间** | 2022-2024年持续活跃 |
| **初始入侵** | 利用CVE-2022-26134（Confluence RCE）和配置错误的Docker daemon。 |
| **持久化** | 创建多个cron job确保重启后执行，含备份机制（atd/infinite loop）。 |
| **防御规避（专门针对国内云）** | ①关闭阿里云、百度云、GCP安全工具；②禁用UFW防火墙；③`setenforce 0` 将SELinux设为permissive；④删除 `/etc/ld.so.preload` 阻止安全库预加载；⑤恶意文件放在 `/tmp` 目录（部分无代理安全方案盲区）；⑥清除cron日志、wtmp、secure日志、`/var/spool/mail/root`。 |
| **横向移动** | ①masscan扫描内网（10.0.0.0/8、172.16.0.0/12、192.168.0.0/16）SSH端口；②使用spirit/spirit-pro工具暴力破解；③窃取 `known_hosts` 文件和SSH密钥，枚举所有密钥/主机/用户组合，设置 `StrictHostKeyChecking=no` 实现免密登录传播。 |
| **载荷** | cryptominer(dbused) + Tsunami后门(IRC bot)，启用HugePages加速挖矿20-30%。 |
| **关键启示** | **攻击者对中国云服务商安全产品有深入研究**，专门编写脚本关闭国内云安全工具。 |
| **来源** | Aqua Security详细分析 |

### 5.3 Kinsing — Openfire 漏洞挖矿攻击

| 项目 | 详情 |
|------|------|
| **时间** | 2023年5月CVE披露，7月开始大规模利用，持续到2024年 |
| **攻击链** | ①扫描互联网发现Openfire服务器；②利用CVE-2023-32315（路径遍历）创建管理员用户；③上传恶意Metasploit插件；④部署web shell；⑤下载Kinsing主payload和cryptominer。 |
| **影响规模** | Shodan发现**6419个公网Openfire实例**，其中**19.5%（984个）存在漏洞**。蜜罐在不到2个月内记录超过**1000次攻击**，**91%归因于Kinsing**。 |
| **受影响地区** | 美国、中国、巴西最严重。 |
| **来源** | Aqua Security详细分析 |

### 5.4 CrowdStrike 2026 全球威胁统计

| 指标 | 数据 |
|------|------|
| 最快eCrime突破时间 | **27秒**（同比提升65%） |
| AI赋能攻击增长 | **89%** |
| 无恶意软件攻击占比 | **82%**（living-off-the-land） |
| 中国关联对手边缘设备漏洞利用 | **40%** |
| 国家级云意识入侵增长 | **266%** |

### 5.5 腾讯云安全违规处置机制揭示的常见被入侵表现

根据腾讯云官方文档，VPS被入侵后最常见的表现：

1. **设备外发流量异常突增**（非正常业务流量）→ 已沦为DDoS僵尸节点或C2中转
2. **CPU被异常程序大量占用** → 挖矿木马感染
3. **文件被加密删除并留有勒索信息** → 勒索软件攻击
4. **被植入木马后门对外攻击** → 已成为攻击跳板
5. **被搭建网络代理服务**（frp、HAProxy等） → 作为攻击基础设施

> 腾讯云数据显示，**封禁或挖矿相关违规**是最高频的处置类型，说明挖矿木马是国内云服务器最常见安全威胁。

---

## 6. VPS安全自查清单

以下清单供运维人员对照检查，覆盖攻击面、持久化、隐藏手段三大维度。

### 🔴 SSH 安全

- [ ] SSH已禁用密码登录，仅使用密钥认证（`PasswordAuthentication no`）
- [ ] SSH默认端口22已修改为非标准端口
- [ ] root登录已禁用或限制（`PermitRootLogin no` 或 `prohibit-password`）
- [ ] 已部署 fail2ban 并配置合理的封禁策略
- [ ] `MaxAuthTries` 设为3-5次
- [ ] `LoginGraceTime` 设为30-60秒
- [ ] 检查 `~/.ssh/authorized_keys` 中无未知公钥
- [ ] SSH使用IP白名单限制（安全组/iptables/hosts.allow）

### 🔴 端口与服务暴露

- [ ] 数据库端口（3306/6379/27017/9200/5432）未对公网开放
- [ ] Redis已配置 `bind 127.0.0.1` + `requirepass`
- [ ] MongoDB已启用 `--auth`
- [ ] Docker API（2375/2376）未暴露公网或已启用TLS
- [ ] Kubelet API（10250）未暴露公网
- [ ] Telnet服务已关闭
- [ ] 使用 `ss -tlnp` 确认无意外监听端口
- [ ] 安全组规则遵循最小暴露原则

### 🔴 持久化排查

#### systemd
- [ ] `systemctl list-unit-files --state=enabled` 无未知服务
- [ ] `systemctl list-timers --all` 无未知定时器
- [ ] `/etc/systemd/system/` 下无可疑 `.service`/`.timer` 文件
- [ ] `/etc/systemd/system-generators/` 下无未知generator

#### cron
- [ ] `crontab -l -u root` 及各用户cron无未知任务
- [ ] `/etc/crontab` 无可疑条目
- [ ] `/etc/cron.d/`、`/etc/cron.hourly/` 等目录无可疑脚本
- [ ] `/var/spool/cron/` 无异常变化

#### 启动脚本
- [ ] `/etc/rc.local` 不存在或内容正常
- [ ] `systemctl status rc-local` 未激活或内容正常
- [ ] `/etc/init.d/` 下无未知脚本

#### Shell配置
- [ ] `/etc/profile`、`/etc/profile.d/` 无可疑命令
- [ ] `~/.bashrc`、`~/.bash_profile`、`~/.profile` 无可疑命令
- [ ] `/etc/update-motd.d/` 下脚本无篡改

#### SSH密钥
- [ ] `~/.ssh/authorized_keys` 中无未知公钥
- [ ] `sshd_config` 未被异常修改（特别是PermitRootLogin/PubkeyAuthentication）

#### 内核模块
- [ ] `lsmod` 无未知模块
- [ ] `/etc/modules` 和 `/etc/modules-load.d/` 无异常条目
- [ ] `/proc/modules` 与 `lsmod` 输出一致

#### LD_PRELOAD
- [ ] `/etc/ld.so.preload` 文件不存在或内容正常
- [ ] `env | grep LD_PRELOAD` 无异常设置

### 🔴 隐藏与日志检查

- [ ] `ls -la /tmp/ /dev/shm/ /var/tmp/` 无可疑隐藏文件（以.开头）
- [ ] `/var/log/wtmp`、`/var/log/btmp`、`/var/log/lastlog` 文件大小正常（未被截断）
- [ ] `/var/log/auth.log` 中无异常清除痕迹
- [ ] `find / -name '.*' -type f -executable 2>/dev/null` 无可疑结果
- [ ] 使用 `rkhunter --check` 或 `chkrootkit` 扫描无异常
- [ ] `chattr` 属性检查无异常不可变文件

### 🔴 进程与网络

- [ ] `ps aux --sort=-%cpu | head -20` 无可疑高CPU进程（排除已知服务）
- [ ] `netstat -antp` 或 `ss -antp` 无异常出站连接
- [ ] 无未知进程连接IRC端口（6667等）或异常C2端口
- [ ] `lsof -i` 无可疑网络连接

### 🔴 账户与权限

- [ ] `/etc/passwd` 中无未知用户账户
- [ ] 检查UID为0的用户只有root
- [ ] sudo权限配置合理（`visudo` 检查）
- [ ] 应用服务不以root运行

### 🔴 系统更新与加固

- [ ] 系统补丁已更新至最新
- [ ] 已参照CIS Benchmarks进行基线加固
- [ ] auditd已部署并配置关键文件监控规则
- [ ] 已部署HIDS（OSSEC/Wazuh/腾讯云主机安全/阿里云安骑士）
- [ ] 已配置远程syslog服务器
- [ ] 已配置文件完整性监控（AIDE/Tripwire）

### 🟡 容器安全（如使用Docker/K8s）

- [ ] 无容器以 `--privileged` 模式运行
- [ ] Docker socket未挂载到容器内
- [ ] 容器以非root用户运行
- [ ] capabilities已最小化（`--cap-drop ALL`）
- [ ] 容器镜像来源可信，已扫描漏洞（Trivy/Clair）
- [ ] 已部署容器运行时安全监控（Falco/Tracee）

---

## 7. 来源列表

| # | 来源 | URL |
|---|------|-----|
| 1 | MITRE ATT&CK — Brute Force (T1110) | https://attack.mitre.org/techniques/T1110/ |
| 2 | MITRE ATT&CK — Exploit Public-Facing Application (T1190) | https://attack.mitre.org/techniques/T1190/ |
| 3 | MITRE ATT&CK — Unix Shell (T1059.004) | https://attack.mitre.org/techniques/T1059/004/ |
| 4 | MITRE ATT&CK — Rootkit (T1014) | https://attack.mitre.org/techniques/T1014/ |
| 5 | MITRE ATT&CK — Kernel Modules (T1547.006) | https://attack.mitre.org/techniques/T1547/006/ |
| 6 | MITRE ATT&CK — Dynamic Linker Hijacking (T1574.006) | https://attack.mitre.org/techniques/T1574/006/ |
| 7 | MITRE ATT&CK — System Services (T1543.002) | https://attack.mitre.org/techniques/T1543/002/ |
| 8 | MITRE ATT&CK — Cron (T1053.003) | https://attack.mitre.org/techniques/T1053/003/ |
| 9 | MITRE ATT&CK — SSH Authorized Keys (T1098.004) | https://attack.mitre.org/techniques/T1098/004/ |
| 10 | MITRE ATT&CK — Clear Command History (T1070.003) | https://attack.mitre.org/techniques/T1070/003/ |
| 11 | MITRE ATT&CK — Hidden Files and Directories (T1564.001) | https://attack.mitre.org/techniques/T1564.001/ |
| 12 | MITRE ATT&CK — Kinsing (S0599) | https://attack.mitre.org/software/S0599/ |
| 13 | MITRE ATT&CK — Hildegard (S0601) | https://attack.mitre.org/software/S0601/ |
| 14 | MITRE ATT&CK — Skidmap (S0468) | https://attack.mitre.org/software/S0468/ |
| 15 | MITRE ATT&CK — Drovorub (S0502) | https://attack.mitre.org/software/S0502/ |
| 16 | MITRE ATT&CK — BPFDoor (S1161) | https://attack.mitre.org/software/S1161/ |
| 17 | MITRE ATT&CK — COATHANGER (S1105) | https://attack.mitre.org/software/S1105/ |
| 18 | MITRE ATT&CK — Chaos (S0220) | https://attack.mitre.org/software/S0220/ |
| 19 | MITRE ATT&CK — Akira (S1129) | https://attack.mitre.org/software/S1129/ |
| 20 | MITRE ATT&CK — AcidRain (S1125) | https://attack.mitre.org/software/S1125/ |
| 21 | MITRE ATT&CK — AcidPour (S1167) | https://attack.mitre.org/software/S1167/ |
| 22 | MITRE ATT&CK — REPTILE (S1219) | https://attack.mitre.org/software/S1219/ |
| 23 | MITRE ATT&CK — Linux Rabbit (S0362) | https://attack.mitre.org/software/S0362/ |
| 24 | MITRE ATT&CK — NKAbuse (S1107) | https://attack.mitre.org/software/S1107/ |
| 25 | MITRE ATT&CK — KV Botnet (C0035) | https://attack.mitre.org/campaigns/C0035/ |
| 26 | CrowdStrike 2026 Global Threat Report | https://www.crowdstrike.com/en-us/global-threat-report/ |
| 27 | OWASP Top 10:2025 | https://owasp.org/Top.10/2025/ |
| 28 | IBM — Brute Force Attack | https://www.ibm.com/think/topics/brute-force-attack |
| 29 | Imperva — Brute Force Attack | https://www.imperva.com/learn/application-security/brute-force-attack/ |
| 30 | IBM — Container Security | https://www.ibm.com/think/topics/container-security |
| 31 | NVD (National Vulnerability Database) | https://nvd.nist.gov/vuln/data-feeds |
| 32 | Aqua Security — TeamTNT Campaign | https://www.aquasec.com/blog/teamtnt-campaign-against-docker-kubernetes-environment/ |
| 33 | Aqua Security — 8220 Gang CVE-2022-26134 | https://www.aquasec.com/blog/8220-gang-confluence-vulnerability-cve-2022-26134/ |
| 34 | Aqua Security — Kinsing Openfire Exploit | https://www.aquasec.com/blog/kinsing-malware-exploits-novel-openfire-vulnerability/ |
| 35 | Aqua Security — Container Threats in MITRE | https://www.aquasec.com/news/container-security-threats-added-to-mitre-attack-framework/ |
| 36 | 腾讯云 — Linux入侵排查指南 | https://cloud.tencent.com/document/product/296/9604 |
| 37 | 腾讯云 — 安全违规处置机制 | https://cloud.tencent.com/document/product/301/9610 |
| 38 | CIS Benchmarks | https://www.cisecurity.org/cis-benchmarks |
| 39 | MongoDB — Security Manual | https://www.mongodb.com/docs/manual/security/ |
| 40 | Kaspersky — Dark Web Predictions 2025 | https://securelist.com/ksb-dark-web-predictions-2025/114966/ |
| 41 | pberba — Linux Threat Hunting: Persistence | https://pberba.github.io/security/2022/01/30/linux-threat-hunting-for-persistence-systemd-timers-cron/ |
| 42 | pberba — Linux Threat Hunting: Shell Config | https://pberba.github.io/security/2022/02/06/linux-threat-hunting-for-persistence-initialization-scripts-and-shell-configuration/ |
| 43 | pberba — Linux Threat Hunting: Systemd Generators | https://pberba.github.io/security/2022/02/07/linux-threat-hunting-for-persistence-systemd-generators/ |

---

## 8. 方法论反思

### 做得好的方面
- 覆盖了5大攻击入口、5大类恶意软件、10种持久化机制、4类隐藏手段，结构完整
- 以MITRE ATT&CK框架为骨架，技术分类权威
- 重点纳入了腾讯云/阿里云环境下的实际攻击模式（8220团伙专门规避国内云安全产品）
- 提供了实用的VPS安全自查清单，可直接用于运维

### 知识缺口
- 部分2025年最新恶意软件变种的技术细节有限（主要安全报告通常在年中发布）
- 国内云服务商（腾讯云/阿里云）的官方安全年报数据未完全公开获取
- 未深入覆盖容器编排平台（Kubernetes）的特定攻击场景

---

> **免责声明**：本报告基于公开来源调研，供安全防御参考。具体防护措施应结合业务场景和合规要求实施。恶意软件 IOC 可能随时间失效，建议结合实时威胁情报使用。