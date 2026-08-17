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
