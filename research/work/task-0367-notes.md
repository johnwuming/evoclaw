# task-0367 盘点笔记 — 拥挤度产品化 阶段A（R-237 前置）

时间：2026-08-18 15:39–16:10 | 采样时点：2026-08-18

## 1. crowding-indicators.json 现状

### 三份副本（md5 一致 4321cf9f...）
| 位置 | 路径 | mtime | 用途 |
|---|---|---|---|
| HP 源 | `noname@10.12.192.174:~/quant-evolve/results/crowding-indicators.json` (93,436B) | 08-17 16:16 | 产线原始输出 |
| VPS 看板 | `/root/.openclaw/workspace-quant/results/crowding-indicators.json` | 08-18 00:16 | **server.js 实际消费路径**（QUANT_REPORTS_DIR） |
| VPS 归档 | `/root/.openclaw/workspace/shared/results/04-投资研究/crowding-indicators.json` | 同步 | 研究归档 |

### 当前值与新鲜度
- generated_at=2026-08-17 16:16:10（**手动跑**，R-226/R-231 工作期间）；latest_date=**2026-08-14**（周五）
- overall_flag=**red**：excess_decay 60日斜率 -0.28%/日 t=-7.0 → red；其余三项 green
- 容量三档：保守 13.4M / 中性 26.7M / 乐观 40.1M 元，瓶颈票 603551

### JSON schema（实测，93KB）
```
/generated_at "2026-08-17 16:16:10"
/latest_date "2026-08-14"
/data_source "本地 data/all_stocks_qfq/*_daily_qfq... akshare 不可达(连接失败) 故全本地自算"
/microcap_definition "每日全市场按总市值排序后20%"
/microcap_eqw_index list[1848] of [date, float]   ← 2019-01 起全史，占体积大头
/overall_flag "red"
/indicators/{micro_turnover_share, micro_turnover_pctile, excess_decay, snowball_knockin}
    每项: name/latest/flag/note (+share: monthly_latest, roll20_latest, pct_rank_60d;
          +pctile: pct_rank_60d; +decay: tstat, pct_rank_hist; +snowball: latest_date)
/capacity/per_stock list[11]  (code/name/weight/shares/cost/...)
/capacity/summary  (method, conservative_5pct, neutral_10pct, optimistic_15pct,
                    bottleneck_stock, mean_5/10/15pct)
```
**契约缺口**：无 schema_version；无数据截止 vs 指标截止区分；无 stale 标记；雪球指标用 zz500 代理（zz1000 本地只到 2016）；历史序列只有微盘等权指数嵌 JSON，其余四指标历史只在 CSV。

### crowding_history.csv（282KB，HP + shared/04，**未镜像到看板目录**）
列：date, micro_turnover_share, _roll20, _monthly, micro_turnover_mean, micro_turnover_pct60, excess_slope_60d, excess_slope_tstat_60d, snowball_dist_zz500_12m。2019-01-02 → 2026-08-14，共约 1848 行。

## 2. collect_crowding.py 产线（HP）

- 脚本：`~/quant-evolve/scripts/collect_crowding.py`（20.8KB，task-0276/W7 建，2026-08-15）
- 输入：`data/all_stocks_qfq/*_daily_qfq.parquet`（5206 只，874 万行，分批读，~400MB RAM）+ `data/hs300_daily_*.parquet` + `zz500_daily_*.parquet` + `results/baseline-paper-portfolio.json`（11 持仓，容量估算用）
- 输出：`results/crowding-indicators.json` + `results/crowding_history.csv`
- **cron：`0 7 * * 0`（仅周日 07:00，周频）**，日志 `logs/collect_crowding.log`（末次成功）
- 运行时长：读 5206 parquet，分钟级（重计算）
- flag 逻辑：turnover 类 P90/P95 分位阈值；slope 类结合 tstat 由调用方判定；NaN → unavailable

### 断点风险清单
1. **akshare 在 HP 不可达**（K线停更事件，2026-08-17 复现连接失败）→ 全本地自算；上限=本地 parquet 新鲜度
2. **数据刷新与采集错序**：refresh_data.py 周日 20:00 vs collect 周日 07:00 → collect 用的是上一周五收盘数据（可接受但 latest_date 恒滞后 2 个交易日）
3. zz1000 parquet 陈旧（到 2016）→ 雪球距离用 zz500 替代，口径与经典定义有偏差
4. 周频采集 + 看板 max_age 192h(8天)：容错一次失败，连续两周失败才红——但**失败无主动告警**（日志无 notify 钩子，risk_patrol 只引用不校验 mtime）
5. 手动跑出的 08-17 文件与周日 cron 产物混用同一文件名，无 provenance 字段区分
6. 微盘池=市值后 20%（R-231 已复用此口径），池定义硬编码在脚本内，改口径=改代码

## 3. 量化 Tab 消费点（server.js，708KB）

| 位置 | 内容 |
|---|---|
| L2099 | `QUANT_REPORTS_DIR = '/root/.openclaw/workspace-quant/results'` |
| L2295 | run-status 新鲜度清单项：crowding，mtime 着色 |
| L3576 | freshness 定义：max_age_hours = **192**（8 天） |
| L3605–3636 | **GET /api/quant/crowding**（M4.7）：读 JSON→剔除 microcap_eqw_index 长序列→输出 indicators/capacity/overall_flag/generated_at/latest_date/data_source/microcap_definition；文件缺失→ available:false + 提示文案 |
| L11789–11815 | 前端并行 fetch（quant/crowding 与 summary/nav/trades/portfolio/models/runStatus/riskStatus/reg/timing 一起） |
| L11899+ renderCrowdingCard | 卡片：整体旗色 + 四指标行 + 容量三档 + 定义脚注；`crowding.available=false` 时占位符 |
| L12156 | 嵌入 paper 页 |

**API 已做减法**（strip 长序列）——但看板拿不到任何历史趋势（无 sparkline 数据）；crowding_history.csv 未镜像到看板目录，前端无法画 90 日走势。

## 4. 同步链路

- VPS root crontab：auto_sync_notify.py **每 30 分钟**（task-0279）+ 每日 03:00 full-sync
- MIRROR_INCLUDES 含 `crowding-indicators.json`（task-0352 加入）→ 镜像至 workspace-quant/results；主同步 → shared/04-投资研究
- 实测 VPS 看板副本 mtime 08-18 00:16，与 HP 源 md5 一致 → 同步链路当前健康
