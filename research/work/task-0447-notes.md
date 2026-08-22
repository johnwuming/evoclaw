# task-0447 过程笔记 — fin_deep 宇宙过滤修复（R-275 管线债）

状态：进行中 | 开始 2026-08-22 23:44

## 1. 目标文件现状（23:47 核实）

- HP `~/quant-evolve/scripts/factor_expansion_v3ak.py` 42,644B，md5 bb5f46a5202c555429cb3711de49e5fb
- **发现：过滤代码已存在**（今日 15:44 落盘），且有备份 `factor_expansion_v3ak.py.bak-task0447-20260822-154431`（42,295B）——即任务书要求的备份已由前次尝试完成，文件已含改动但验证/回执未做
- diff（bak vs 当前）：仅 1 个 hunk，+3 行（2 行注释 + 1 行过滤），0 行删除：
  ```python
  # [task-0447/R-275] merge 前按 A 股前缀过滤(00/30/60/68系), 剔除 yjbb 引入的新三板(83/87/43/92)/
  # 老三板(40/42)/B股(200/900)/北交所(8/4/9开头) 等非主板代码, 修复宇宙污染(44.57%%缺失率假象, R-275 A股真宇宙口径)
  df = df[df["code"].str[:2].isin(("00", "30", "60", "68"))].copy()
  ```
- 位置：load_ak_wide 内四表循环，`df["code"] zfill(6)` 之后、statDate 派生之前 → 对 yjbb/zcfz/xjll/lrb 四表统一生效，merge 前 → 符合任务书要求（统一生效 + 写法与现有风格一致）

## 2. 定性依据复核（R-275 报告 §一）

- yjbb 20251231 期 11,518 行 = 纯 A 股 5,228 + 新三板 6,062 + 老三板/B 股 203；A 股主流前缀缺失 = 0
- 修复方式 = merge 前前缀过滤，一处改动，无采集成本 ✓（与本 diff 一致）
- 注释里 "44.57%%" 双百分号：py 普通字符串中 %% 无影响（此处是注释，非 print 格式串），不改

## 3. 验证结果（23:52 完成，真实输出）

- `py_compile`：**PASS**
- dry-run 脚本：HP `/tmp/task0447_dryrun.py` + `/tmp/t0447_p.py`（参数化期别），未污染管线目录
- **20251231 期（任务书参照）**：yjbb_before=11,518 → after=**5,215**（预期 ~5,2xx ✓），dropped=6,303
  - dropped 前缀构成：83:2781 / 87:2603 / 92:339 / 43:339（新三板 6,062）+ 40:148 / 42:14（老三板 162）+ 90:41 / 20:38（B 股 79）+ 其他——与 R-275 定性完全吻合
  - 同期 xjll=5,228 / zcfz=5,228 → 过滤后同量级 ✓
  - **A 股前缀零丢失断言 PASS**（被剔除行中 00/30/60/68 前缀数=0；行数守恒）
- **20260630 期（数据最新期，披露季中）**：1,123 → 429，xjll=429 精确匹配，断言 PASS

## 4. 交付物与回执

- 改动：factor_expansion_v3ak.py 仅 +3 行（diff 1 hunk，≤20 行 ✓）；备份已存在（前次尝试 15:44 完成）：`factor_expansion_v3ak.py.bak-task0447-20260822-154431`
- 未改 evolution_pipeline.py / registry / paper_engine / crontab / 采集脚本；未触发重采或重建；未杀任何 HP 进程
- 结论：前次尝试已落盘正确改动但未做验证与回执，本次补齐验证（compile+dry-run×2 期）+ 回执
- [23:5x] 补丁落地：
  - 备份 scripts/factor_expansion_v3ak.py.bak-task0447-20260822-154431
  - diff（183a184,186，load_ak_wide 循环内 zfill 后）：
    ```
    +        # [task-0447/R-275] merge 前按 A 股前缀过滤(00/30/60/68系), 剔除 yjbb 引入的新三板(83/87/43/92)/
    +        # 老三板(40/42)/B股(200/900)/北交所(8/4/9开头) 等非主板代码, 修复宇宙污染(44.57%缺失率假象, R-275 A股真宇宙口径)
    +        df = df[df["code"].str[:2].isin(("00", "30", "60", "68"))].copy()
    ```
  - py_compile OK；四表统一过滤（xjll/zcfz/lrb 本就纯 A 股，过滤为 no-op，future-proof）
- 原表过滤后三要素覆盖（HP results/work/task0447/breadth.py 实测，口径=yjbb 过滤后行 left join xjll/zcfz）：
  - universe codes：yjbb 5,226 / zcfz 5,244 / xjll 5,244 / lrb 5,244（对照污染口径 11,765→5,226）
  - 三要素(net_profit∧ocf∧total_asset) 按年齐全率：2005 96.7% ... 2009 最低 91.1% ... 2023 99.2% / 2024 99.2% / 2025 99.6% / 2026 100%
  - **全史 pooled 96.59%（R-275 基准 96.6% ✓）；2023 起 99.39%（基准 99.4% ✓）；2024 起 99.46%**

## 重建结果（HP results/work/task0447/rebuild.log，38s 完成）

- driver：results/work/task0447/rebuild_panel.py（import 模块 + monkeypatch FIN_PANEL_CACHE → 新文件，不改产物路径；nohup 后台跑）
- **新产物：data/derived/fin_deep_monthly_panel_ak.ashare.parquet（58.5MB, 1,337,220 × 24, codes 5,244, ym 2005-06→2026-08）**
- 旧面板 data/derived/fin_deep_monthly_panel_ak.parquet 零改动（73,980,207B, Aug 16 02:40，在役消费方不受影响）

## 前后对照表（口径一致：同一构建代码，唯一差异=宇宙过滤）

| 指标 | BEFORE（旧面板/原表） | AFTER（新面板/过滤后原表） | 基准 |
|---|---|---|---|
| 面板宇宙 codes | 11,783 | **5,244**（yjbb 原表过滤后 5,226） | ~5,100-5,200 ✓ |
| 面板行数 | 3,004,665 | 1,337,220（剔除 55.5% 非A股行） | — |
| accrual_quality 近12月(2025-09~2026-08) nonnull | 44.38%（缺失 55.62%） | **99.71%（缺失 0.29%）** | 从 44.57% 大幅下降 ✓ |
| cf_or_ratio / ocf_stability 近12月 nonnull | 44.37% / 44.36% | 99.69% / 99.67% | ✓ |
| accrual_quality 全史 nonnull | 27.73% | 62.31% | — |
| 三要素(NP∧ocf∧TA) 全史 pooled（原表口径） | — | **96.59%** | R-275: 96.6% ✓ |
| 三要素 近3年(2023起) pooled | — | **99.39%**（2024起 99.46%） | R-275: 99.4% ✓ |
| 三要素缺失率 | （污染口径缺失 44.57%） | 全史 3.4% / 近3年 0.6% | <5% ✓ |

- 面板全史 62.31% 的剩余缺失为 PIT 可见性结构（早年 EM pubDate 回填 → usable_from 晚 1-2 年 + TTM/滚动列热身期），分年 nonnull：2005 0.1% → 2015 63.0% → 2023 97.9% → 2026 99.9%，与 R-275 PIT 诊断一致，非数据债。
- 原表分年三要素齐全率（2009 最低 91.1%，2023-2025 99.2-99.6%）逐项对上 R-275 breadth_a_share.csv。

## 复算命令（HP）
```bash
grep -n "task-0447" ~/quant-evolve/scripts/factor_expansion_v3ak.py   # 插入位置 L184-186（load_ak_wide 内 zfill 后）
/home/noname/miniconda3/envs/quant/bin/python -c "
import pandas as pd
p=pd.read_parquet('/home/noname/quant-evolve/data/derived/fin_deep_monthly_panel_ak.ashare.parquet')
rec=p[p.ym>='2025-09']
print(p.shape,'codes',p.code.nunique(),'all',round(p.accrual_quality.notna().mean(),4),'rec12m',round(rec.accrual_quality.notna().mean(),4))"
# 输出: (1337220, 24) codes 5244 all 0.6231 rec12m 0.9971
/home/noname/miniconda3/envs/quant/bin/python ~/quant-evolve/results/work/task0447/breadth.py | tail -4
# 输出: OVERALL all-history pooled = 0.9659 / recent ym>=2023 pooled = 0.9939 (n=67750) / recent ym>=2024 pooled = 0.9946
```

## 结论
- R-275 定性的宇宙污染债已在生产脚本修复（一处过滤，3 行，merge 前生效于全部四表）；A 股真宇宙三要素缺失率 0.6-3.4% <5%，与 R-275 基准逐位一致。
- 新面板落 .ashare.parquet 供对照；在役 canonical 面板未动（切换属后续决策）。备份：scripts/factor_expansion_v3ak.py.bak-task0447-20260822-154431。
- 未触碰 evolution_pipeline.py / registry / paper_engine / crontab；未杀任何已跑进程。

## 产物清单
- HP: scripts/factor_expansion_v3ak.py（已修补+编译验证）；scripts/factor_expansion_v3ak.py.bak-task0447-20260822-154431；data/derived/fin_deep_monthly_panel_ak.ashare.parquet；results/work/task0447/{breadth.py,rebuild_panel.py,rebuild.log}
- VPS: shared/results/work/task-0447-notes.md（本文件）
