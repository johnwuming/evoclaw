# R-352 paper_engine 卖出跌停闸与分红入账实施（task-0546）

- 日期：2026-08-29
- 任务：task-0546（用户 2026-08-29 09:34 批准实施，方案依据 R-351 / task-0550 定稿）
- 唯一修改文件：HP `/home/noname/quant-evolve/scripts/paper_engine.py`（1759 → 1870 行）
- 过程笔记：`shared/results/work/task-0546-impl-notes.md`

## 一、改动说明

### ② 卖出跌停闸
- 新增常量（L86 后）：`LIMIT_DOWN_GATE = os.environ.get("PAPER_LIMIT_DOWN_GATE", "1") != "0"`（默认开启，=0 恢复旧行为）、`CREATIVE_LIMIT_PCT = 0.198`。
- 新增函数 `is_limit_down(code, d, st_flags)`（L969）：与 `is_limit_up` 同构（qfq 最近两个收盘，`pct <= -th + 1e-4`）；板块感知阈值——300/301/688/689 开头 → 0.198（创业板/科创板，ST 仍 20%）；主板 ST → 0.05；其余 → 0.098。
- 两处接线：
  - 清仓卖出块（L1548）：遇跌停 `skip` 并保留持仓（不再 `del holdings`）；
  - timing 减仓块（L1577）：遇跌停 `continue` 下一个标的（超配额度顺延）。

### ③ DIV_EVENTS 分红入账
- 新增 `credit_dividends(state, upto_date)`（L1069 附近）+ `_div_ledger_path()`：
  - 水位 `state["last_div_date"]`，窗口 `(水位, upto]`；首次运行无水位 → 以当日初始化、不追溯历史；
  - entitlement：`buy_date < ex_date` 才享有；按当前份额 × `cash_per_share` 毛额入账现金（税务 v1 不预扣）；
  - 台账独立文件 `results/paper-div-ledger.csv`（列：ex_date, code, shares, cash_per_share, amount, credited_on, window_upto），不动 trades.csv schema；
  - 幂等：窗口处理完即推进水位；dividend_events.parquet 读取失败时不推进水位、下次重试。
- 三个挂点：
  - `action_daily` 缺口回填循环：逐日 `credit_dividends(state, t)` 后再估值（L1447）；
  - `action_daily` 当日行：估值前补 credit（L1468）；
  - `action_rebalance`：卖出块之前补 credit（L1531），保证调仓卖出前分红现金已入账。

## 二、验证证据

1. **语法**：`/home/noname/miniconda3/envs/quant/bin/python -m py_compile paper_engine.py` → OK（部署前 .new 与部署后最终文件各验一次）。
2. **单测**：`~/quant-evolve/tests/test_task0546.py`（合成数据+临时目录，monkeypatch `load_kline/load_st_flags/DIV_EVENTS/RESULTS_DIR/STATE_FILE/NAV_FILE`，外部依赖 `data_validator`/择时/选股/写盘全 stub），结果 **33 PASS / 0 FAIL**，覆盖：
   - 板块阈值：300(-19.9% ✓/-19% ✗)、301、688、689、主板普通(-9.8% ✓)、主板ST(-5% ✓、-9% ✗)、创业板ST(-5% ✗)、无K线→False；
   - 清仓路径（rebalance 全链路，ratio=0.12 隔离 trim/买入）：闸开→无 sell 交易+持仓保留；闸关→恢复卖出；
   - 减仓路径：跌停股（市值最大、trim 首先命中）被跳过、额度顺延清掉下一只；闸关→跌停股也被减；
   - 分红：ex_date 当日入账金额精确（0.5×1000+0.2×2000=900）、buy_date>=ex_date 不入账、同窗口重放幂等（0 入账、台账仍 2 行）、空窗口仅推水位、首次无水位不追溯、台账列与行内容正确；
   - daily 回填挂点：入账 +500、水位推进、NAV 行写入；
   - rebalance 卖前挂点：入账 +500、水位推进、台账 1 行；
   - 开关：子进程验证未设 env→True、`PAPER_LIMIT_DOWN_GATE=0`→False。
3. **改动面**：`diff paper_engine.py.bak-task0546-20260829 paper_engine.py` 共 111 行增改，全部属于②③（新常量、is_limit_down、credit_dividends+_div_ledger_path、5 处挂点/闸），无其他改动。
4. **在役数据零污染**：`results/paper-state.json`（mtime 08-28 16:30，当日 cron 所写）、`baseline-paper-trades.csv`（08-17）、`baseline-paper-nav.csv`（08-28）均早于本次部署（08-29 01:43 UTC）；在役 `results/` 下不存在 `paper-div-ledger.csv`；未杀任何在役进程，未跑全量回测。

## 三、回退方法

1. **开关回退（不改代码）**：`PAPER_LIMIT_DOWN_GATE=0` 时卖出路径恢复旧行为（跌停照卖）。②的闸完全失效；③无开关，需按 2 回退。
2. **代码回退**：
   ```bash
   cp ~/quant-evolve/scripts/paper_engine.py ~/quant-evolve/scripts/paper_engine.py.pre-revert-task0546
   cp ~/quant-evolve/scripts/paper_engine.py.bak-task0546-20260829 ~/quant-evolve/scripts/paper_engine.py
   ```
   回退后 state 中可能已存在 `last_div_date` 字段（旧代码会原样保留，无害）；`paper-div-ledger.csv` 保留作审计。

## 四、后续依赖与建议

- **dividend_events.parquet 需定期刷新**（当前 48081 行，mtime 2026-08-13，无 cron）：手动 `prep_dividend_roa --only div`，按批准口径**不加 cron**；若长期不刷新，③窗口内无新事件 → 无入账（fail-quiet，不会错入账）。
- 分红入账按当前份额简化（窗口内减仓/分红孰先的精确份额未逐日追踪），v1.1 可选 10% 预扣税口径，本期均不做。
- 首次在役运行（下次 daily cron）会写一条"初始化分红水位（不追溯历史）"日志并落 `paper-div-ledger.csv`（仅当有合格事件时才有行）。
- 单测脚本保留于 `~/quant-evolve/tests/test_task0546.py`，可重复执行（`/home/noname/miniconda3/envs/quant/bin/python tests/test_task0546.py`）。

## 五、交付物清单

| 项 | 路径 |
|---|---|
| 代码（已部署） | HP `~/quant-evolve/scripts/paper_engine.py`（md5 3de3aa96…，1870 行） |
| 备份 | HP `~/quant-evolve/scripts/paper_engine.py.bak-task0546-20260829`（70504B，md5 c2cc87bb…） |
| 单测 | HP `~/quant-evolve/tests/test_task0546.py`（33 PASS / 0 FAIL） |
| 过程笔记 | `shared/results/work/task-0546-impl-notes.md` |
