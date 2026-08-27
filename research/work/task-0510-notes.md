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

## §B 集思录

