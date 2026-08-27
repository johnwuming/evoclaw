# task-0510 过程笔记 — 可转债剩余余额免费数据源侦察（R-332）

日期：2026-08-27 18:15 起（Asia/Shanghai）
约束：禁 SSH HP；零回测零采购；纯桌面侦察。编号 R-332 预占。
上下文基线：R-299 结论「剩余余额中性化需公告级数据采购（免费源缺）」→ 本任务实测推翻或坐实。

## 笔记结构
- §A 东方财富源
- §B 集思录源
- §C akshare 源
- §D 兜底通道（wayback/交易所）
- §E 十券抽样
- §F 结论分级

---

## §A 东方财富

### A1 akshare `bond_zh_cov()` → 东财 datacenter 接口（实测 2026-08-27 18:2x）
- 实现：`RPT_BOND_CB_LIST` 报表，URL `https://datacenter-web.eastmoney.com/api/data/v1/get`（源码 bond_zh_cov.py L322）。
- 注：裸拼该报表名会报「报表配置不存在」（需完整 quoteColumns 参数组合）；经本机 python 调 `ak.bond_zh_cov()` 成功。
- 返回 1050 行 × 19 列，落盘 `/tmp/em_cov_all.json`（520KB→52万字节内）。
- **列清单**：债券代码/简称、申购日期、申购代码、申购上限、正股代码/简称、正股价、转股价、转股价值、债现价、转股溢价率、股权登记日、每股配售额、**发行规模**、中签号发布日、中签率、上市时间、信用评级。
- 相关字段仅有「发行规模」（发行时点静态值）、无「剩余规模」「转股进度」。行情类列（正股价/债现价/溢价率）为实时快照，非历史序列。
- 结论 A1：bond_zh_cov 无剩余余额字段 ❌。

### A2 akshare 源码全局搜索「剩余规模」
- 仅命中 `bond/bond_convert.py`：`curr_iss_amt → 剩余规模`，数据源是**集思录**（cb_list_new / redeem_list），即剩余规模字段归 §B 集思录通道，非东财。
- 东财 bond 目录其他文件（bond_em.py 等）无剩余规模字段。
- 待测 A3：东财个券 detail 页（data.eastmoney.com/kzz/detail/{code}.html）是否有当前剩余规模展示。

- 待测 A3 已做：kzz/detail/{code}.html 为 JS 骨架页无余额文本；`bond_zh_cov_info(基本信息)` 全列拿到：仅 `ACTUAL_ISSUE_SCALE`（实际发行规模，静态）；已退市券（吉视转债 113017, LISTING 2018-01-15, DELIST 2023-12-27）也可查 → 覆盖退市券 +。
- **A 结论：东财系无任何「剩余余额/转股进度」字段；仅有静态发行规模 + 实时行情快照 ❌**

## §C akshare

- 本机版本：**akshare 1.18.94**（python3.12, /usr/local/lib）。
- 全局搜「剩余规模」仅集思录系函数命中（bond_convert.py：bond_cb_jsl/bond_cb_redeem_jsl 的 curr_iss_amt 映射）；东财系函数无余额字段。
- `bond_cb_jsl(cookie)` 明确需要登录 cookie 才能拿全量；未登录只能像 B1 自拼请求限 30 条。
- 无任何函数提供「历史某月末剩余余额」序列。

## §D 兜底通道

### D1 Wayback Machine（2026-08-27 实测）
- `web.archive.org` CDX API 连 sanity 检查（url=baidu.com）都返回空且进程超时退出 → **本机到 archive.org 不通/被阻断，通道在本环境不可达**（不排除海外代理下可用，但当日桌面环境无法验证；存档是否覆盖 jsl cb_list_new JSON 亦无从谈起——spider 通常不会 POST 该端点）。
- 结论 D1：回填 2019 历史 ❌（本环境）。


### B1 未登录实测（curl/python POST cb_list_new，2026-08-27）
- `POST https://www.jisilu.cn/data/cbnew/cb_list_new/` 无 cookie 可用！未拦截、无验证码。
- 但 rp=999 仍只返回 **30 行**（分页墙）→ 免费墙是条数限制而非登录墙；网页版 data/cb/list 为 JS 骨架页（3898B）。
- 字段证据（原文摘录）：`"curr_iss_amt":5.5,"year_left":5.981,"maturity_dt":"2032-08-18","orig_iss_amt":...` → **剩余规模✅ 存在**，30/30 行有值；样例落盘 /tmp/jsl_cells.json。
- **关键限制：该端点仅为当前快照，无任何历史参数**（请求体只有筛选器，无日期维度）→ 自身历史深度 = 0。
- PIT 风险评级：低（快照实时），但对回填无用——过去某月末的余额无法从此端点取。

