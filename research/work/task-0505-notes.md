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
