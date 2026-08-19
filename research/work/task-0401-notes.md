# task-0401 G3CORR 豁免对称化 过程笔记

## 目标
- 单向豁免（在役持护栏列→候选替身豁免）改为双向（候选持护栏列→在役替身同样豁免）
- 验证：a9_ranksum_raw 评分恢复 ~0.867±0.01；在役 a13 评分不变 0.8781；非 E1 老候选评分逐位不变

## 时间线
- 00:11 开始执行

## 2026-08-20 00:12 步骤1：背景确认（R-245 §3.3）
- a9 新增因子 ret120（原始护栏列）与在役 a13 替身 mom_pen_dz corr=0.7555
- 现行 G3CORR 豁免仅覆盖"在役持护栏列→候选替身"方向
- 目标：对称豁免后 a9 score 0.7715 → ~0.867±0.01（R-241 参考值）

## 2026-08-20 00:15 步骤2：代码修改完成（PATCH OK, py_compile passed）
- 备份：scripts/evolution_pipeline.py.bak-g3sym-20260820
- 4 处替换：
  1. GUARD_CORR_CONFIG 注释块追加 D-20260820-G3SYM 说明
  2. _guard_exempt_pairs(new_factors, active_reg, cand_reg=None)：正向块逻辑原样保留（在役 e1_guard→候选替身豁免）；新增反向块——候选 e1_guard 且护栏列登记在候选 factors、不在候选排序 specs、属 new_factors，且在役因子集含 guard_avatars 名单成员 → 豁免对 (候选护栏列, 在役替身)
  3. gate_max_corr 调用处传 reg
  4. corr_policy 输出标注更新
- 关键前置数据（已核实）：a9 e1_guard=1, factors 含 ret120（不在排序 specs, 属 new_factors vs a13）；a13 factors 含 mom_pen_dz（guard_avatars["ret120"] 成员）

## 2026-08-20 00:17 步骤3：单元验证通过
- G3 a9-vs-a13：exempt=[["ret120","mom_pen_dz"]]; max_abs_corr 0.7555→0.3821 (worst ret120×avg_amount_20d, ≤0.5 → corr 分量满档 1.0); status PASS; corr_policy 标注含 D-20260820-G3SYM
- 旧签名两参调用 _guard_exempt_pairs(new_f, act) → 空集 = 旧行为（向后兼容锚点）
- decision-log 已追加 D-20260820-G3SYM（HP 为 UTC 时区，条目时间 17:11 与既有条目格式一致）
