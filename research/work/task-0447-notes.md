# task-0447 · fin_deep 宇宙过滤管线债修复 — 过程笔记

## 任务
HP 侧 fin_deep 面板构建链路 merge 前按 A 股前缀过滤（剔除新三板 83/87/43/92、老三板 40/42、B股 900/200；北交所按 R-275 口径=参照 r0414 宇宙，不含 8/4/9 开头）。只改过滤一件事；备份+diff；重建验证（宇宙数/三要素覆盖/缺失率）；不碰 evolution_pipeline.py/registry/paper_engine/crontab。

## 基准（R-275 / task-0442 §1）
- 污染机制：yjbb 为主表 outer merge 四表 → 宇宙并集 11,765（含新三板/B股）；A 股真宇宙 ~5,100-5,200
- 44.57% 缺失率 = 污染口径（5244/11765）；A 股真宇宙三要素全史 96.6% / 近3年 99.4% → 三要素缺失应 <5%
- A 股前缀集（R-275 VPS 重采口径）：00/30/60/68 系（000/001/002/003/300/301/302/600/601/603/605/688/689）

## 时间线
- [23:4x] 启动：已读 R-275 报告（5,046B）与 task-0442-notes §1（10,644B）。

- [23:5x] 定位：脚本 ~/quant-evolve/scripts/factor_expansion_v3ak.py（42,295B，不全读）。
  - load_ak_wide() L163：读 data/fin_deep/{yjbb,zcfz,xjll,lrb}.parquet，循环内 L183 `df["code"]=...zfill(6)` 后 dedup，L209 yjbb 为主表 outer merge。
  - build_fin_deep_monthly_panel() L282：cache 存在则直接读 FIN_PANEL_CACHE（data/derived/fin_deep_monthly_panel_ak.parquet，73MB，08-16），否则 load_ak_wide→逐 code merge_asof 月度化→写回 cache。`__main__` 有 guard，import 安全。
  - 重建方案：不改产物路径（不顺手改其他逻辑），写独立 driver：import 模块后 monkeypatch FIN_PANEL_CACHE → data/derived/fin_deep_monthly_panel_ak.ashare.parquet，调 build_fin_deep_monthly_panel()。旧面板零改动。
- BEFORE（旧面板实测）：
  - shape (3,004,665 × 24)，code nunique 11,783，ym 2005-06→2026-08
  - accrual_quality nonnull：全史 27.73%，近12月(2025-09~2026-08) 44.38%；cf_or_ratio 44.37%；ocf_stability 44.36% —— 复现 R-266/R-275 的 44.5% 污染口径
- 过滤口径（依 R-275）：保留前缀 00/30/60/68 系（000/001/002/003/300/301/302/600/601/603/605/688/689）；剔除新三板 83/87/43/92、老三板 40/42、B股 200/900、北交所 8/4/9 开头（R-275 参照宇宙 r0414 无北交所）。
