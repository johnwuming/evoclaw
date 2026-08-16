# task-0292 Q1 基建笔记（重试）
- 开始: 2026-08-16 12:08
- 备份: /tmp/evolution_pipeline.py.bak-q1, /tmp/bdqi.bak-q1, /tmp/bmti4.bak-q1
- 目标文件: evolution_pipeline.py(E6+E3), backtest_dividend_quality_iter.py(WF3), backtest_macro_timing_iter4.py(WF3), audit_lock_check.py(新)
- 关键定位:
  - evolution_pipeline.py: L58 GATE_CONFIG.oos_split_ym=2021-01; L307 gate_icir(); L351 gate_max_corr(); L665 cmd_evaluate
  - WF 窗口: bdqi L565-568 / bmti4 L131-134, WF3 OOS=2021-01-01~2026-12-31 穿透审计段
  - v1.4 gate-report: g2 n_months_oos=67 (2021-01~2026-07, 穿透), g3 平凡PASS (无新增因子)

## 改动1（E6）OOS止于审计段 ✅ 2026-08-16 12:2x
- 新建 scripts/audit_lock.py: AUDIT_LOCK_END=2024-06-30, AUDIT_LOCK_END_YM=2024-06, clamp_date/clamp_ym/breaches_lock
- evolution_pipeline.py:
  - import 区加 sys.path.insert + from audit_lock import AUDIT_LOCK_END, clamp_ym
  - gate_icir() L~318: oos_mask = (~is_mask) & (ic_df["ym"] <= AUDIT_LOCK_END[:7]) — OOS终点强制2024-06
  - gate2 输出加 oos_end_ym + audit_lock_end_ym 字段；report 加 audit_lock_end
- backtest_dividend_quality_iter.py: RESULT_DIR 后 import；WF windows 建完后统一 clamp_date(w[4])（WF3 2026-12-31→2024-06-30）
- backtest_macro_timing_iter4.py: 同样 import + windows clamp（stage_wf）
- py_compile 全部 OK
- 干跑验证（合成IC 2016-01~2026-06，rnd seed=42）：
  - A: split=2021-01 → oos_end_ym=2024-06, n_months_oos=42（原66，穿透消除）ASSERT PASS
  - B: split=2018-01 → oos_end_ym=2024-06, gate2 status 正常计算 ASSERT PASS
  - C: split=2024-02 → OOS不足5月 → N/A（不穿透不误判）ASSERT PASS

## 改动2（E3残留）g6 MDD门禁 + g3非平凡化 ✅ 2026-08-16 12:3x
- evolution_pipeline.py:
  - GATE_CONFIG 加 mdd_vs_parent_max_pp: 2.0
  - 新函数 gate_mdd_vs_parent(reg, active=None)：|MDD_cand|-|MDD_parent| ≤2pp → PASS，>2pp → FAIL（进 decisive 集=一票否决），缺数据/无active → N/A
  - gate_max_corr：无新增因子分支由"平凡PASS"改为 status=N/A + max_abs_corr=None（不折减总判定）
  - cmd_evaluate：g5 之后插入 gates["g6_mdd_vs_parent"]；registry 回写加 mdd_deterioration_pp
- py_compile OK
- 合成用例验证（全部 ASSERT PASS）：
  - C1 恶化1.5pp → PASS (det_pp=1.5)
  - C2 恶化3.0pp → FAIL (det_pp=3.0)
  - C3 改善5pp → PASS (det_pp=-5.0)
  - C4 缺MDD → N/A；C5 无active(正确mock) → N/A
  - g3 无新增因子 → N/A + max_abs_corr=None；g3 有新增因子 → 正常计算 n_new=1
  - verdict 接线：g1-g5全PASS+g6FAIL → REJECT（一票否决生效）；g6PASS → PASS；g3 N/A 不参与判定

## 改动3 审计段预检工具 ✅ 2026-08-16 12:4x
- 新脚本 scripts/audit_lock_check.py（184行）：
  - 扫描 results/bt_*/gate-report.json（g2 oos_end_ym 或按 n_months_oos 推算终点）
  - 扫描 3 个源码文件的 WF 窗口定义 + clamp 保护在位检查
  - 退出码 0/1，输出人读摘要 + findings JSON
- py_compile OK
- 验证（历史病例自证）：
  - full scan: 3个旧gate-report(v1.2/v1.3/v1.4) 报告穿透 [2021-01~2026-07]，exit=1 ✅
  - WF1/WF2 干净；WF3 定义穿透但显示"运行期clamp已拦截→实际2024-06-30" 🛡
  - --report bt_v1.4: 单独报告 g2 穿透，exit=1 ✅

## 任务完成状态
- 三件改动全部完成+验证，py_compile 5个文件全 OK
- 备份: /tmp/*.bak-q1（evolution_pipeline / bdqi / bmti4）
- 未动 data/、未动 v1.4 历史结论、未动其它无关文件
