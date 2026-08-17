# task-0338 A7 过程笔记（边查边写）

> 生成 2026-08-17 09:30 | 任务书见同目录 task-0338 任务

## 访问路径首查（09:31）
- HP SSH 10.12.192.174:22 Connection refused（09:30-09:33 重试 3 次均拒，ping 通，22/2222/22022/222 全 closed）
- **替代路径：HP HTTP API http://10.12.192.174:8060 + X-API-Key 可用**
  - /health OK：quant env 存在，merged_file 304MB，qfq_files 5448，disk free 31.7GB
  - /run 可执行命令（cwd=/home/noname/quant-evolve，env=quant，timeout 上限 1800s=30min）
  - /data/status OK：data_path=/home/noname/quant-evolve/data，merged mtime 2026-08-11 01:46
  - DANGEROUS_PATTERNS 仅拦截 rm -rf /等，常规 python 命令可跑
- 结论：本任务以 HTTP API 为执行路径（SSH 备用，后续再试）
- a7 现有结果文件数：0

## 阶段0 首查两项（factor_db 字段 / dividend_events 公告日）
（待填写）

### 09:40 追加：factor_db 结构
- factor_db.sqlite 表：factors(3行)、evolution_history(0行)、sqlite_sequence
- factors 列：id,name,description,code,source,created_at,status,ic_mean,ic_ir,ic_history,weight,llm_hypothesis,iteration —— 这是因子元数据表，不是行情数据表
- 行情字段（amount/turnover）需查 all_stocks_merged.parquet（v4b 基建实际用表）
- merged parquet 读取报错（疑似 pyarrow/engine 问题），待复读

### 09:45 追加：merged kline 字段核对（首查项①部分结论）
- all_stocks_merged.parquet：14,613,191 行 × 8 列 = date,code,open,close,high,low,volume,amount
- **有 amount（成交额），无 turnover（换手率）** → 换手率需用股本数据计算（查 fundamentals_monthly 是否含总/流通股本）
- factor_db.sqlite 是因子元数据表（3 因子），非行情表；amount/turnover 在 kline

### 09:50 追加
- merged kline 已核对：有 amount，无 turnover（首查①过半结论；换手需股本表）
- factor_db.sqlite=因子元数据表（非行情表）；行情字段在 merged parquet
- dividend_events 列名查询多次 segfault（API 瞬时），改用落盘脚本再查
- 访问路径确定：HP HTTP API（8060+key），SSH 端口拒绝

### 10:05 首查两项结论（A7 开工）
**首查① factor_db 字段核对**：
- factor_db.sqlite = 因子元数据表（factors 3 行：id,name,description,code,source,created_at,status,ic_mean,ic_ir,ic_history,weight,llm_hypothesis,iteration），非行情表
- 行情表 all_stocks_merged.parquet：8 列 date,code,open,close,high,low,volume,**amount**（有成交额，无 turnover）
- fundamentals_monthly.parquet：code,date,div_yield_ttm,**circ_mv**,roe_ttm,roa_ttm → 有流通市值（月频），无总股本
- 结论：成交额版因子直接可用；**换手率版需日频股本（无）→ 用 amount/circ_mv 月频近似或只测成交额版**

**首查② dividend_events 公告日**：
- dividend_events.parquet：5 列 code, ex_date, cash_per_share, period, __index_level_0__
- **只有除权除息日 ex_date，无预案公告日** → F13 股息事件 PIT（预案公告日）**本批不可行，不测**（只查不测达成）

### 10:20 恢复执行（上次超时，A5 runner 机制已读通）
- a5_runner.py 机制：patch 引擎 run_backtest（ext 排序分支 P1 + inv_vol P2 + rank_buffer P3 + vt_target P4 + dd_trigger P5 + value/mom lookup P6/P8 + gq 排序 P9），等价校验 diffs={} 后跑候选
- a5_post_bt.py：registry 注册（fork 自 parent）+ ledger_append（带 features 字段）
- a5_ic_ext.py：月度 IC（spearman，方向调整，W1 口径）
- A7 计划：基于 v4b_mve1（sort=mv + e1_guard + q3z_tr 择时）骨架，新增 P0 因子 ext 分支（low_amount/amihud/cv）+ 日历降仓 + 涨停剔除 + 次新剔除，逐一单维度叠加
