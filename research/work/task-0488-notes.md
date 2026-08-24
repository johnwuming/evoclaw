# task-0488 / R-310 备用行情源降级链 过程笔记

## 2026-08-25 06:02 开始

- SSH OK：`ssh -p 22 noname@10.12.192.174`，~/quant-evolve 存在
- scripts/paper_engine.py = 66959 bytes（>30KB，不全读，只取 fetch_spot_closes 及周边）


## 06:04 源可用性实测（HP，2026-08-25 06:0x，行情为 08-24 收盘数据）

- **新浪 hq.sinajs.cn：HP 可达** ✅ 需 `Referer: https://finance.sina.com.cn`
  - 单/批量均支持（`list=sh600000,sz000001,sz300750`）
  - 格式（GBK）：`var hq_str_sh600000="名称,开盘9.010,昨收9.050,最新9.220,高,低,...,2026-08-24,15:34:59,00";`
  - **字段依据：逗号分隔索引3=最新价**；收盘后即当日收盘价。600000=9.220
- **腾讯 qt.gtimg.cn：HP 可达** ✅ 无需特殊头
  - 单/批量均支持（`q=sh600000,...`）
  - 格式（GBK）：`v_sh600000="1~名称~600000~9.22~昨收9.05~开盘9.01~...~20260824161431~..."`
  - **字段依据：`~` 分隔索引3=最新价**。600000=9.22，与新浪一致 ✅
- 东财 spot（akshare stock_zh_a_spot_em）：任务书已知 HP 连接被重置（本任务动机）
- 北交所代码（4/8/92 开头）新浪/腾讯不覆盖 → 降级源返回缺该代码 → 调用方现有"不全则弃用"逻辑兜底（口径安全不变）

## 代码结构（改造前）

- fetch_spot_closes：L348-374（东财单源，异常仅 log 一行回退）
- 调用方：L1263 `overrides = fetch_spot_closes(...)`；L1264-1269 不全则弃用（口径全量一致门）
- REFERENCE_CODES L98；返回键= zfill(6) 的 6 位码

## 06:07 改造前代码事实

- holdings 键格式：zfill(6) 字符串，8 只：300824/002107/603551/000848/300009/600867/002027/601600（全沪深，无北交所）
- holdings_value_at(state,d,overrides)：`code in overrides` 直接按 holdings 键匹配 → 新源返回键同样 zfill(6) 即可
- 模块级 imports（L42-54）无 re/requests；quant env requests=2.34.2 可用 → 顶部加 `import re`，requests 在函数内惰性 import
- STATE: results/paper-state.json；last_daily=2026-08-24，model_version=a13_rsraw_e1f10dz
- NAV: results/baseline-paper-nav.csv（末行 2026-08-24,0.98319）
- 补丁方式：按 `def fetch_spot_closes` → `def load_st_flags` 边界整段替换（规避全角引号精确匹配陷阱）+ hashlib 后插一行 `import re`
