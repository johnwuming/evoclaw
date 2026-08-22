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

