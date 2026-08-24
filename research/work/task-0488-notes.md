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

## 06:31 补丁与实测结果（全部 PASS）

### 改动（HP scripts/paper_engine.py，66959→70504 bytes）
- 备份：`scripts/paper_engine.py.bak.r310_202608242223`（66959 bytes）
- L52 新增 `import re`（首轮 heredoc 转义 bug 漏插，已修复；regex/replace 逐行目检无误）
- L349-350：SPOT_TIMEOUT=10 / SPOT_BATCH_MAX=40
- L353-360 `_mkt_sym`：6→sh；0/1/2/3→sz；其余(北交所)返回 None（两备用源不覆盖，由现有"不全则弃用"门兜底）
- L362-364 `_err_brief`：异常摘要截 120 字符
- L366-392 `_spot_from_sina`：hq.sinajs.cn，Referer 头，GBK，逗号索引3=最新价
- L395-421 `_spot_from_tencent`：qt.gtimg.cn，GBK，~索引3=最新价
- L423-469 `fetch_spot_closes` 重写：东财→新浪→腾讯→空dict回退 parquet；每级失败仅一行 log；成功即返回
- 其余函数/NAV 口径/append 门/append_nav 零改动（diff hunk 全落 347-467+52）

### 实测证据（HP 本地时间 2026-08-24 22:29-22:31 UTC）
1. **真实东财现状**：akshare stock_zh_a_spot_em → `Connection aborted, RemoteDisconnected`（HP→东财确挂）
2. **备用源直连**：新浪 8/8、腾讯 8/8，8 只持仓两源价格完全一致（如 600867=7.95、601600=9.5）
3. **降级链（mock 东财）**：log `源1/3 东财失败` → `源2/3 新浪 取价成功 8/8`，返回值=新浪直连，一致 ✅
4. **三源全挂**：4 行 log 链完整（源1/2/3 失败+全源失败回退 parquet），返回空 dict ✅
5. **parquet 口径**：8/8 全等（08-24 收盘，如 000848=8.43 三方 EQ），CONSISTENCY_BAD_COUNT=0
6. **生产级真实 daily 运行（非 mock）**：
   - run1: `源1/3 东财(akshare) 失败: Connection aborted, RemoteDisconnected` → `源2/3 新浪 取价成功 8/8` → NAV 0.983190
   - run2（幂等）：同上
   - 前后对比：nav.csv 8 行不变、末行 `2026-08-24,0.98319` 不变、无重复日期（uniq -d=0）、last_daily=2026-08-24 / model_version=a13_rsraw_e1f10dz / last_data_date=2026-08-24 均不变
7. py_compile PASS ×2（补丁后+加 import re 后）

### 未动清单
- crontab（6 条 paper_engine 引用原样）、paper_engine_gold.py、registry、evolution_pipeline.py、NAV/append 逻辑、其他函数
- scripts/ 目录仅 paper_engine.py + 备份变化；results/ 4 文件为 daily 常规重写（值不变）
