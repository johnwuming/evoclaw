# task-0546 实施笔记（2026-08-29）

## 环境事实
- paper_engine.py 实际路径：/home/noname/quant-evolve/scripts/paper_engine.py（1759 行）——注意任务书写的 ~/quant-evolve/paper_engine.py 不准确
- 关键行号（grep 实测）：L61 DIV_EVENTS（仅 1 处引用）；L949 is_limit_up；is_limit_up 调用点 L1251、L1500；L97 LIMIT_UP_PCT=0.098；L98 ST_LIMIT_UP_PCT=0.05
- 报告编号：全库现有最大 R-351 → 本报告用 R-352
- 报告目录：shared/results/05-量化投资/（R-34x/35x 都在这里，不是 04-投资研究）
- dividend_events.parquet schema：['code','ex_date','cash_per_share','period']，48081 行
- 函数锚点：load_state L991 / save_state L1002 / load_trades L1008 / append_nav L1025 / action_daily L1312（回填循环内 tot_b 在 L1350 附近）/ action_rebalance L1385 / 清仓块 for code in sell_list: / 减仓块 for code, pos in held_sorted:
- buy_date 格式 str(d)='YYYY-MM-DD'（建仓块 L1284 确认）
- 备份已建：scripts/paper_engine.py.bak-task0546-20260829（70504B）
- 本地工作副本：/tmp/pe_orig.py（原版）、/tmp/pe_new.py（改后）；scp 子系统失败，用 ssh cat 传输

## 已完成步骤
1. 备份：scripts/paper_engine.py.bak-task0546-20260829（md5 c2cc87bb…）
2. 补丁：本地 apply_patch → ssh cat 上传 .new → HP py_compile COMPILE_OK → 原子 mv；新文件 1870 行，md5 3de3aa96…；diff 111 行全部为②③（is_limit_down 函数、LIMIT_DOWN_GATE/CREATIVE_LIMIT_PCT 常量、credit_dividends+_div_ledger_path、4 个挂点：daily 回填/daily 当日/rebalance 卖前、清仓块 skip、减仓块 continue）

## 实施设计（按已批方案落码）
- ② LIMIT_DOWN_GATE = os.environ.get('PAPER_LIMIT_DOWN_GATE','1') != '0'（默认开，=0 关）；CREATIVE_LIMIT_PCT=0.198；is_limit_down 与 is_limit_up 同构（qfq 近两收盘、pct<=-th+1e-4；300/301/688/689→0.198；ST→0.05；其余→0.098）；清仓块 skip+保留、减仓块 continue
- ③ credit_dividends(state, upto)：窗口 (last_div_date, upto]；首次无水位→初始化水位不追溯；分红文件读取失败→不推进水位；entitlement buy_date<ex_date；按现份额毛额入账 cash；台账 paper-div-ledger.csv（_div_ledger_path() 走 RESULTS_DIR 便于测试 monkeypatch）；挂点：action_daily 回填循环逐日 + 当日行前、action_rebalance 卖出块前
