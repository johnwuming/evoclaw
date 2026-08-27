# R-325 · fin_deep yjbb 宇宙污染 A 股前缀过滤修复（task-0505，零回测）

- 时间：2026-08-27 12:14~13:05，VPS 本地完成；**禁 SSH HP 全程遵守**，未触碰引擎/registry/crontab/HP 文件
- 前序：R-266（44.5% 缺失发现）→ R-274/task-0442 阶段A（污染定位）→ **R-275（实锤：44.57%=5244/11765 系 yjbb 把非 A 股带入面板分母的宇宙污染，修复=merge 前前缀过滤）** → 本任务 = R-275 登记的管线修复 todo 落地
- 过程笔记（含全部证据与坑位）：`work/task-0505-notes.md`；验证产物：`work/r325/{pre_baseline.json,verify_output.json,inputs_fingerprint.json,r325_verify_filter.py}`

## 一、改了什么（最小化改动，共 2 处逻辑 + 1 个验证脚本）

| 文件 | 改动 | 作用 |
|---|---|---|
| `scripts/task-0285/factor_expansion_v3ak.py` | 新增 `A_SHARE_PREFIXES`(13前缀)+`is_a_share_code()`；`load_ak_wide()` 读表循环 zfill 后、**merge 前**过滤并打印剔除计数 | 合并端兜底：重建面板时无论上游表多干净都不再让非 A 股进分母 |
| `tmp_hp/collect_fin_deep_ak.py` | 同款 helper + `process()` 采集落盘前过滤（含日志） | 采集源头：未来 HP 续采增量不再写入新三板/B股行 |
| `shared/results/work/r325/r325_verify_filter.py` | 新增验证脚本（build/baseline/full 三阶段） | 本报告全部数字的可复现来源 |

白名单逐字对齐 R-275 口径：`000/001/002/003/300/301/302/600/601/603/605/688/689`。zcfz/xjll/lrb 三表本就纯 A 股（实测 nonA=0 行），过滤为恒等操作；yjbb 是唯一污染源。

## 二、修复前基线（改代码前先落盘，notes §基线留存）

HP 生产基准（R-275/task-0442 已存证 `_meta_ak.json`）：yjbb 451,669 行/**11,765 只** vs zcfz/xjll/lrb 各 279,074/287,642/288,443 行/**5,244 只** → **5244/11765 = 44.57%** 即 R-266 的"44.5% 数据债"真相：非收益缺口 = 分母被污染的假象。

本地同源 EM 重采快照（r275 chunks，86 期×3 表）：yjbb 453,749 行/11,733 只、zcfz 280,143/5,247、xjll 288,715/5,247。未过滤管线仿真（原 load_ak_wide 外连语义转录）：宽表 455,037 行/**11,751 只宇宙**，其中非 A 股行 **165,474 行（36.4%）** 每期纯贡献 NaN 分母。

**对照表（复现成功）**：

| 指标 | R-275 锚点(HP) | 本次本地 | 判定 |
|---|---|---|---|
| 污染比（三表股票数/yjbb 股票数） | **44.57%** (5244/11765) | 44.72% (5247/11733) | ✓ 快照漂移 +0.15pp |
| A 股口径行数 yjbb/zcfz/xjll | 288,275 / 280,143 / 288,715 | 完全相同三连 | ✓ 精确一致 |
| 20251231 单期缺失构成 | 新三板 6,062+老三板 162+B股 79, A股缺=0 | 6,072+164+78, a_prefix_missing=0 | ✓ 构成一致 |
| 修复后三要素齐全率 全史/近3年 | **96.6% / 99.4%** | **0.966 / 0.9939** | ✓ 对得上 |

## 三、修复后验证（真模块实跑，非仿真）

把补丁后的 `factor_expansion_v3ak.load_ak_wide()` 直接加载执行（scipy/factors_ext stub 注入，FIN_DEEP_DIR 重定向到 /tmp 隔离副本）：

```
[a-share-filter] yjbb: 453749 -> 288275 行 (-165474 非A股代码)
wide(before-derive): (289563, 22)
```

- 断言通过：宽表内非 A 股代码数 = 0；宽表股票宇宙 11,751 → **5,247**（= 纯 A 股 zcfz/xjll 并集）
- **保留行完整性（md5 抽验双重）**：
  - 全量级：三表修复前后「保留行」帧哈希（pandas hash_pandas_object→md5，按键排序消序）逐一相等；
  - 抽样级：每表 150 行按同键重算 md5，mismatch=0（样本清单见 verify_output.json `sample_md5_kept`）。
  - 结论：过滤只删行、不改任何保留数据。
- **剔除规则可解释性**：yjbb 被剔 6,504 只 code **100%** 命中"A 白名单外"，构成：新三板/北交所 6,134 + 老三板/两网退市 291 + B股 79；抽验样例 200761(深B)、430047 等 30 条带净利数值列入 `removal_sample`——即 R-275 表格结构在 code 级别的完整再现。
- 分年齐全率复算与 `r275/breadth_a_share.csv`（2023:0.9922 / 2024:0.9915 / 2025:0.9961 / 2026:1.000，全史年均 0.9631）同源吻合，近 3 年行池化 99.39% 与 R-275 记录一致。

## 四、影响面与部署说明

- 本任务只动采集合并两环节 workspace 内副本（VPS 不持有生产运行时）；**HP 生产尚未同步**（禁 SSH），上线路径：常规任务将 `scripts/task-0285/factor_expansion_v3ak.py` 与 tmp_hp 增量 collect_fin_deep_ak.py 推至 HP `~/quant-evolve/scripts/` 后重跑管线即可（fin_deep 表不需重采：load 层过滤已覆盖存量）。
- 未来收益：应计/SUE/ROE 族等财务因子面板的现金流系列广度从 ~44.5% 修复到 ≈纯 A 股真实覆盖率（96%+），PIT 可信度提升；对在役 W1/W2 因子无回测扰动（它们本就不消费非 A 股财务行）。
- 兼容性：ybb 净利派生列在 non-A 行上的历史值从"有值但错宇宙"变为不存在，目录 v3 口径不受影响；lrb 在本地子集缺席走原版 WARN 分支，HP 上有 lrb 数据无此问题。

## 附：证据文件

- `work/task-0505-notes.md` — 全程笔记（修改前基线先行落盘）
- `work/r325/pre_baseline.json` — 修复前面板计数基线 + 未过滤帧指纹
- `work/r325/verify_output.json` — 修复后真模块输出（对照/md5/剔除明细抽样）
- `work/r325/inputs_fingerprint.json` — 输入数据指纹（行数/股票数/键 md5）
- `work/r325/r325_verify_filter.py` — 一键复现脚本（build/baseline/full）
