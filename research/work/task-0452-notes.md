# task-0452 在役切换：fin_deep canonical 面板 → ashare 净化版

时间：2026-08-22 23:56 开始
决策依据：用户 2026-08-22 23:55 拍板切换（task-0447 验收结论：新面板 5,244 只/前缀纯净 100%/三要素齐全率 96.59%全史·99.39%近3年 vs 旧 canonical 11,765 含新三板/B股/44.57% 缺失假象）

## 进度日志（边查边写）

### 步骤1：消费方盘点（2026-08-23 完成，只读 grep）

文件现状（HP ls -la data/derived/）：
- 旧 canonical `fin_deep_monthly_panel_ak.parquet` 73,980,207 B，mtime 2026-08-16 02:40
- 新净化版 `fin_deep_monthly_panel_ak.ashare.parquet` 58,531,886 B，mtime 2026-08-22 15:46

引用 `fin_deep_monthly_panel_ak` 的 py 文件共 5 个：
1. `scripts/factor_expansion_v3ak.py` — **上游生成器（覆盖风险源）**：L30 `FIN_PANEL_CACHE=canonical`；L286-288 存在则读缓存；**L311 `panel.to_parquet(FIN_PANEL_CACHE)` 会覆盖 canonical**；L767-768 `--no-fin-cache` 会删缓存。L184-186 已带 A 股前缀过滤（task-0447/R-275 修复），重跑产物也是净化口径，但行数细节可能与 ashare 版有漂移 → 见「上游覆盖风险」节
2. `scripts/a4b_run.py` — 下游消费者：L212 `pd.read_parquet(canonical)`（PIT growth 因子用，usable_from 月频）
3. `scripts/r251_sue_profile.py` — 下游消费者：L134 `pd.read_parquet(canonical)`
4. `scripts/fix_v3_catalog_report.py` — 仅文档字符串提及（L211/222），无实际读写
5. `results/work/task0447/rebuild_panel.py` — task-0447 重建脚本本体（NEW=ashare 路径），一次性工作脚本

结论：文件级换名对所有真实消费者（a4b_run/r251_sue_profile）透明生效；无需改任何代码。

### 步骤2：换名三步（2026-08-23 00:0x 完成）

- a) 备份：`cp -a fin_deep_monthly_panel_ak.parquet → fin_deep_monthly_panel_ak.parquet.pre-0447.20260823`（73,980,207 B，原 mtime 2026-08-16 02:40 已保留）
- b) 换名：`cp -a fin_deep_monthly_panel_ak.ashare.parquet → fin_deep_monthly_panel_ak.parquet`（cp 非 mv，ashare 原件未动，58,531,886 B，mtime 2026-08-22 15:46 保留）
- c) 校验：
  - canonical 行数 **shape=(1337220, 24)** ✓（=预期 1337220）
  - canonical 代码数 **5244** ✓
  - md5：canonical `1ed28f47f3342f3210d51403cbf5a05e` == ashare 原件 `1ed28f47f3342f3210d51403cbf5a05e` ✓；备份 `7d364c876953fac2ecf89a236253d4e1`（旧件，与预期不同=正确）

### 步骤3：冒烟验证（2026-08-23 00:0x 完成）

**分布对比（ym=2023-06，无股息率列，用应计类 accrual_quality + roe_report/gp_margin）**：
- 宇宙数：old 全表 11,783 只 → old 限 A 股前缀子集 (oldA) 5,244 只 → new 5,244 只（吻合）
- accrual_quality 均值：old=2.2883 / oldA=2.2883 / new=2.2883（非 A 股行该列多为 NaN，无影响）
- roe_report 均值：**old=12.87 → oldA=2.4051 = new=2.4051**（旧全表被污染股拉高 5 倍多；新面板与旧表 A 股子集完全一致 → 差异恰为「剔除污染股」量级，非全表漂移）
- gp_margin 均值：old=29.8998 / oldA=29.8973 / new=29.8973（同上）
- 结论：new ≡ oldA（逐列到小数点后 4 位），面板变更语义 = 纯过滤，A 股存量数据未动

**行级抽查（3 只跨新旧都在的 A 股，22 个因子列全量比对，tol=1e-10）**：
- 000001：255 行，失配 0
- 600000：255 行，失配 0
- 300750：255 行，失配 0
- 3 只股票 oldA_total = new_total = 255（过滤未触碰任何 A 股行）

### 上游覆盖风险与守护建议（未实施，仅记录）

- `factor_expansion_v3ak.py` L311 `panel.to_parquet(FIN_PANEL_CACHE)` 会在重跑时**覆盖 canonical**；L767-768 `--no-fin-cache` 会删缓存文件。
- 缓解现状：L184-186 已带 A 股前缀过滤（R-275），重跑产物也是净化口径，但重建细节（去重/对齐逻辑）与 task-0447 的 rebuild_panel.py 可能有行数漂移，覆盖后 1337220/5244 基线会变。
- 守护建议（不在本任务实施）：cron 定期校验 canonical 行数∈[133万,134万] 且 md5 != 备份 md5，异常时告警；或将 v3ak 的 L184-186 过滤口径与 rebuild_panel.py 对齐后再允许重跑。
- HP crontab 未改动（红线遵守）；未杀任何进程。

### 交付结论

canonical `fin_deep_monthly_panel_ak.parquet` 已切换为 ashare 净化版（133.7 万行/5,244 只），备份 `.pre-0447.20260823` 在位，ashare 原件保留，消费方零代码改动自动生效。
