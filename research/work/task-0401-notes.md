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

## 2026-08-20 00:22 步骤4：全量兼容性重评验证通过（rescore_g3sym_test.py 干跑，输出仅写 /tmp）
- 11 个老候选 vs 旧 summary 对比：10 个 SAME（v0_seed/v1a/v1b/v1c/v1d/v1g/v1h/v3a/v3b/v4d，score+全部分量逐位一致）
- 唯一 CHANGED：a9_ranksum_raw 0.7715 → 0.8715；分量级对比：corr 0→1.0，其余 9 个分量（p/dsr/oos_calmar/oos_sharpe/is_calmar/is_sharpe/dd/logic）全部不变 → 变化完全隔离在豁免消除的双重计价项
- 目标核验：0.8715 ∈ 0.867±0.01 ✓（推算 0.7715+0.10×1.0 与实测一致）
- a9 g3 明细：max_abs_corr=0.3821（worst ret120×avg_amount_20d，来自月度IC 兜底源），guard_exempt_pairs=[["ret120","mom_pen_dz"]]，status PASS
- a13_score.py 副本改路径后因 SUPP_IC 重新生成分支 merge 列重叠报错（副本路径改动副作用，非 pipeline 改动问题）；a13 评分改用直接调函数方式重验

## 2026-08-20 00:28 步骤5：在役 a13 评分不变验证（A/B 对照）
- registry 锁定值 a13 score=0.8781（未触碰，无 rescored 标记）
- A/B：旧版（.bak-g3sym-20260820 加载）vs 新版，同一输入 gate_max_corr(a13, active=v5h_xsub)：
  两侧完全一致：max_abs_corr=0.6249, worst (avg_amount_20d,circ_mv), exempt=[["mom_pen_dz","ret120"]]（正向豁免两侧同样生效）, corr_sources {matrix:4, ic_monthly:10}
- registry 记录 0.2066 与重算 0.6249 的差异 = 数据源时变（a13 evaluate 时点 09:27 与现在 factor_ic_corr.csv 覆盖范围不同，现缺 mom_pen_dz 列走月度IC兜底），旧版跑同输入也得 0.6249 → 与本次改动无关
- 完整评分链路不变性已由 rescore 干跑 10 个老候选逐位一致覆盖（score_composite+全部gates+holdout）

## 2026-08-20 00:31 步骤6：收尾确认 + 交付摘要

### 文件变更清单（HP ~/quant-evolve）
| 文件 | 变更 |
|---|---|
| scripts/evolution_pipeline.py | 修改（78193→80340 字节，md5 9c50b188…） |
| scripts/evolution_pipeline.py.bak-g3sym-20260820 | 新增备份（md5 0896bbac…，即改前版本） |
| scripts/apply_g3sym_patch.py | 新增（补丁脚本，4 处替换带断言，可追溯） |
| model/decision-log.jsonl | 追加 1 条 D-20260820-G3SYM |
| 临时测试副本 | rescore_g3sym_test.py / a13_score_g3sym_test.py 已删；测试输出仅写 /tmp/ |

未触碰：paper_engine、a9_common、registry 条目 status/score（a9 registry 仍 0.7715 旧值，未回写）、crontab、results/ 既有 summary（mtime 仍 0819）。

### diff 摘要（4 处替换，均为断言唯一锚点后替换 + py_compile 通过）
1. GUARD_CORR_CONFIG 注释块：追加 D-20260820-G3SYM 对称化依据（R-245 §3.3）
2. _guard_exempt_pairs(new_factors, active_reg, cand_reg=None)：正向块（在役 e1_guard→候选替身）逻辑逐字保留；新增反向块——候选 e1_guard 且护栏列 ∈ 候选 factors、∉ 候选排序 specs、∈ new_factors，且在役因子集含 guard_avatars 名单成员 → 豁免对（候选护栏列, 在役替身）；缺任一条件不豁免
3. gate_max_corr 内调用改为 _guard_exempt_pairs(new_factors, act, reg)
4. corr_policy 输出标注更新为 "+ D-20260820-G3SYM 对称化"

### 验证结论（全部通过）
1. 兼容性：11 老候选重评（rescore 部署函数干跑），10 个 score+全部分量逐位不变
2. 目标：a9_ranksum_raw 0.7715 → 0.8715（corr 分量 0→1.0，其余 9 分量逐位不变；0.8715 ∈ 0.867±0.01 ✓）；g3 max_corr 0.7555→0.3821，豁免对 [["ret120","mom_pen_dz"]]
3. 在役 a13：registry 锁定 0.8781 未动；A/B（旧备份 vs 新版，同输入 gate_max_corr(a13,active=v5h)）输出完全一致（0.6249/同豁免对/同源计数）
4. 旧签名两参调用返回空集 = 旧行为锚点；数据源时变（0.2066 记录值 vs 0.6249 重算）经 A/B 排除与本次改动无关

### 受影响版本清单
- a9_ranksum_raw（sota）：重评口径 score 0.7715→0.8715；registry 未回写（是否回写留用户决策）
- 其余全部版本（含在役 a13、v0~v4 老候选、v5 系）：零漂移
- 未来场景：候选持护栏登记项 × 在役含替身的 E1 交互评估从此双向豁免

### 晋升建议（仅建议，无动作）
a9 重评 0.8715 仍低于在役 a13 0.8781（rank2），未过线，无需晋升动作。若用户希望 registry/manifest 反映新口径 a9 score，需另批 rescore --write 回写。
