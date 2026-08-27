# task-0505 R-325 yjbb 宇宙污染 A 股前缀过滤修复 — 过程笔记

## 时间线
- [12:14] 任务启动。目标：fin_deep 管线 yjbb 采集合并环节加 A 股代码前缀过滤，消除 R-275 实锤的宇宙污染；零回测数据级验证。

## 定位结论
- 合并端修复点：`scripts/task-0285/factor_expansion_v3ak.py` → `load_ak_wide()`：yjbb 为主表 outer merge 四表（load_ak_wide 循环读 parquet 后、merge 前）。R-275 建议「merge 前按 code 前缀过滤（一处改动，load_ak_wide）」。
- 采集端脚本副本：`tmp_hp/collect_fin_deep_ak.py`（workspace 内唯一副本，task-0442-notes §4 明确「该脚本在 workspace/tmp_hp/ 有副本」）。HP 生产原件不动（禁 SSH HP）；workspace 内两处同步修改，供后续部署参考。
- 复现锚点数字（R-275 / task-0442-notes）：
  - 面板股票池污染比：zcfz/xjll/lrb 每表仅 5,244 只纯 A 股 vs yjbb 11,765 只（含新三板/B股/老三板）→ 5244/11765 = 44.57%，即 fin_deep 现金流系列近月 nonnull 44.5% 的分母污染来源
  - 20251231 单期：yjbb 11,518 行 − xjll 5,228 行 = 6,303 缺口 = 新三板(83/87/43/92 前缀) 6,062 + 老三板/两网(40/42) 162 + B股(90xxxx 沪B 41 + 20xxxx 深B 38)；A股主流前缀缺失=0
  - 修复后预期：A 股真宇宙三要素(NP∧OCF∧TA 同期齐全)率全史 96.6%、近 3 年 99.4%；A股前缀过滤后 yjbb 本地重采 288,275 行 / zcfz 280,143 / xjll 288,715

## 基线留存（修复前面板行为）
- HP 生产 _meta_ak.json（task-0442-notes 引用）：yjbb 451,669 行/11,765 股；zcfz 279,074/5,244；xjll 287,642/5,244；lrb 288,443/5,244。修复前面板构建会把 yjbb 的非 A 股行保留进宽表（outer merge），构成被污染宇宙。
- VPS 本地验证基线将用同源 EM 接口重采原始（未过滤）yjb b 分期截面重建「修复前」计数。

## 待办
- [ ] 检查修复是否已被其他任务完成（防重复）
- [ ] 读 r275/chunks 判断原始/已过滤
- [ ] 写过滤补丁
- [ ] 数据级对照验证

## 基线留存（修改代码前，r325/pre_baseline.json @ build+baseline stage）
- 本地 r275 chunks（与 HP 同源 EM 接口，采集日 2026-08-22/23 快照）：yjbb 453,749 行/11,733 股/86期；zcfz 280,143 行/5,247 股；xjll 288,715 行/5,247 股
- 与 HP 生产 _meta_ak.json（yjbb 451,669/11,765；zcfz 279,074/5,244）对照：行数差 <0.5%、股票数差 <0.3% = EM 快照漂移，结构一致
- **污染比复现：本地 5247/11733 = 44.72% ↔ R-275 锚点 5244/11765 = 44.57%（同口径，漂移 +0.15pp，对得上）**
- 修复前宽表仿真（原 load_ak_wide 外连语义转录）：wide 455,037 行/11,751 股，其中非 A 股行 165,474（36.4%）
- 20251231 单期：yjbb 11,486 vs xjll 5,231 → 45.54%；缺失 6,268 全部为非 A 股前缀（83x/87x/43x/920=新三板~6,072、40x/42x=老三板两网 164、900/20x=B股 78）；**A 股主流前缀缺失=0**（a_prefix_missing=0）
- 输入指纹 md5 已落盘 inputs_fingerprint.json；未过滤 yjbb 关键列帧 hash c61bc784…315（修复后保留行须与此恒等）

## 补丁落地（12:47~12:58）
1. `scripts/task-0285/factor_expansion_v3ak.py`：load_ak_wide 读表循环 zfill 后加 `is_a_share_code` 前缀过滤（merge 前）；新增 `A_SHARE_PREFIXES`（13 前缀，与 R-275/r275_ic 逐字一致）+ helper。lrb 缺表 WARN 分支原样保留。
2. `tmp_hp/collect_fin_deep_ak.py`：process() 内 zfill 后同款过滤（采集源头）；helper 同口径。
3. 验证脚本 `work/r325/r325_verify_filter.py`：build/baseline/full 三阶段。全程未动 engine/registry/crontab/HP 文件；py_compile 通过。
   - 过程坑位记录：①本地子集缺 lrb 表→曾造零行 stub，但 pandas3 空 parquet 在真函数内丢 schema，改为把 lrb 派生源列(total_profit/op_profit)以 NaN 挂靠 zcfz + 走原版 WARN 跳过分支（等价且更诚实）；②抽验逻辑两处自我修正（排序先后、pre 侧需先限 A 股子集再比 hash）。

## 最终验证结果（r325/verify_output.json @ stage full，真模块实跑）
- 真函数 load_ak_wide 端到端：yjbb 过滤日志 `453749 -> 288275 (-165474)`，宽表 (289563, 22)；断言无任何非 A 股代码残留通过
- 行数锚点三连（vs R-275 记录）：yjbb 288,275 =✓ / zcfz 280,143 =✓ / xjll 288,715 =✓（精确一致）
- 宇宙对照：宽表股票数修复前 11,751 → 修复后 5,247；yjbb 股票 11,733→5,229
- **污染比：本地 44.72%（5247/11733）↔ R-275 HP 锚点 44.57%（5244/11765）**，快照漂移 +0.15pp
- **修复后三要素齐全率：全史 0.966 / 近 3 年 0.9939 ↔ R-275 锚点 96.6% / 99.4%** ✓
- md5 抽验：①三表「保留行」全量帧哈希修复前后恒等（kept_full_hash_equal=true×3）；②每表 150 行抽样按同行键重算 md5 逐一相等（post_resample_match=true×3, mismatch=0）
- 剔除明细：6,504 只 code 全部被白名单规则解释（all_explained=true）：新三板/北交所 6,134 + 老三板/两网退市 291 + B股 79；样本如 200761(深B)、430047(新三板) 等 30 条入 verify_output.json removal_sample
- 结论：复现成功，补丁生效，与 R-275 数字对得上；报告编号 R-325（避让并行 R-323/R-324）
