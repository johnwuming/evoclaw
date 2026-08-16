# task-0325 A2-b2 第二批模型迭代笔记（DSR 友好化方向）

## 阶段0 读数（2026-08-16 22:30~）
- 第一批报告 results/a2-model-iteration-report.md（5986B）已通读：
  5 候选全 REJECT，g4 DSR 唯一全灭（0.644-0.760 < 0.95，n_trials=39）
- ledger 现状：12 行，n_trials_cum=39（backtest 计数 5 + offset 34）；evaluate 行不增加 n_trials
  （ep.ledger_backtest_count 只数 type=backtest → 本批 6 候选全 append 后，evaluate 统一 N=45）
- g4 精确参数（bt_v1e_vol/gate-report.json）：
  - v1e_vol: dsr=0.6905, sr=0.0456, sr0=0.038055, T=4490, skew=-0.654, kurt=8.124
  - v1b_mvq: dsr=0.7597, sr=0.05502, sr0=0.044321（σ 日度更大→sr0 更大）
  - 关键：sr0 = c(N)·σ_daily，**σ 越低 sr0 越低**；且 sr=Sharpe/15.875。降 σ 对 DSR 双重利好
- 引擎结构（scripts/backtest_dividend_quality_iter.py run_backtest）：
  - 月度调仓，等权 w=1/len(new_pool)（L455）；日度 eff_ret=day_ret*pos_ratio*timing_ratio（L367）
  - market[\"timing_pos\"] 注入即启用择时（task-0255 原生机制，ffill 月度系数）
  - 成本 v2：等权近似 w_each=1/n_new 估单笔冲击（对 ivw 候选保持该近似，文档说明）
- 择时层（macro_timing_layer_iter4.py）可用：q3z=36月窗 PE zscore 择时（hi=1.0,cut=0.40）
  - 实测信号：q3z pos 248月 mean=0.581 min=0.3；q5z mean=0.598；corr(q3z,q5z)=0.964
  - T 线证据：T-i4_q3z DSR=0.9715（n=174，task-0297 回溯）→ 择时是最强 DSR 友好组件
  - 估值数据 data/macro/index_valuation.parquet 在位（2026-08-16 06:30）
- registry v1e_vol.json 结构已取（fork 模板）；ep.save_version 写 registry 不动代码 ✓

## DSR 通过线计算（N=45）
- c(45)=0.42278*Φ⁻¹(1-1/45)+0.57722*Φ⁻¹(1-1/(45e))≈2.2323（c(39)=2.18）
- 通过条件：sr ≥ sr0 + 1.6449·√denom/√4489，denom≈1.03 → margin≈0.0249
- 换算成「锁定窗 Sharpe 需 ≥」：
  - v0_seed（σ_d≈0.0203, sr0=0.0453@N45）→ 需 Sharpe≥1.09（父本 0.885，够不着）
  - σ_d=0.018（ivw/低波族）→ sr0=0.0402 → 需 Sharpe≥1.03（难）
  - σ_d=0.0125（q3z 择时预期）→ sr0=0.0279 → 需 Sharpe≥0.84（现实）
  - σ_d=0.0113（vol target 18%）→ sr0=0.0253 → 需 Sharpe≥0.80（大概率）
- 结论：**仓位类（择时/波动率目标）是过 g4 的主攻方向**；排序/加权/缓冲带是方向覆盖
# task-0325 A2-b2 设计稿（阶段1，先写设计再跑数）

## 6 候选（对照 v0_seed 各只改一个维度；g5 经济逻辑预埋）

| IT编号 | 版本 | 改动维度(唯一) | 实现方式 | 经济逻辑(g5) |
|---|---|---|---|---|
| IT-A2B-01 | v1f_lv70 | 排序: mv→0.3·(−z mv)+0.7·(−z vol20) 低波主导 | ext排序分支(权重参数化) | 方向a覆盖: v1e(0.5:0.5)已证低波降回撤(MDD−2.78pp)但SR掉到0.72; 本候选检验更深低波倾斜能否用σ↓换DSR门槛↓(sr0∝σ)。预期: 若SR<1.0则难过关, 属方向验证 |
| IT-A2B-02 | v1g_ivw | 组合构建: 等权→波动率倒数加权 | weight_mode=inv_vol patch(重平衡日按1/vol20归一) | 方向b: 池内个股风险平价, 高波股降杠杆→组合σ↓约10-20%、尾部↓; 风险预算均衡化是经典SR↑手段。成本仍按等权近似(文档注明, 二阶误差) |
| IT-A2B-03 | v1h_buf | 交易治理: 排名缓冲带 top20进/top40出 | rank_buffer=20 patch(持仓仍在top40则保留, 空位才补新) | 方向c: 月频换手是成本与冲击的主要来源; hysteresis降低不必要换手→成本v2冲击↓→净SR↑; 且减少噪音交易 |
| IT-A2B-04 | v1i_q3z | 择时叠加: v0_seed+q3z估值择时 | market["timing_pos"]注入(引擎原生机制, T线同款) | 方向d: q3z=36月窗PE zscore, T线已证DSR 0.9715(n=174); 估值高位降仓→危机段暴露↓→MDD与σ大幅↓, 直接改善DSR分子分母 |
| IT-A2B-05 | v1j_vt18 | 仓位管理: 组合目标波动率18% | vt_target patch(每日按自身trailing 63d已实现波动缩放, 无前视) | 方向e: A股小盘波动强聚集(可预测), 波动目标化把σ_d压到~1.1%; DSR的sr0=c(N)·σ, σ↓直接压低通过线(需Sharpe≥0.80 vs 父本需1.09) |
| IT-A2B-06 | v1k_q5z | 择时叠加(备份): v0_seed+q5z | 同v1i, 60月窗 | 方向d备份: q5z与q3z corr 0.964, 长窗更保守; 若q3z边际差, q5z提供家族第二抽签 |

## DSR 通过线速查（N=45, T≈4490, denom≈1.03）
- sr0=2.2323·σ_d；需 sr ≥ sr0+0.0249，sr=Sharpe/15.875
- σ_d=0.020(v0族) → 需 Sharpe≥1.09 | σ_d=0.018 → ≥1.03 | σ_d=0.0125 → ≥0.84 | σ_d=0.0113 → ≥0.80
- 主攻: v1i/v1j/v1k(仓位类)；v1f/g/h 为维度覆盖，通过概率低但完整批次方向矩阵

## 工程要点
- run_backtest_a2b = 第一批ext方法扩展: P1 ext排序(复用) + P2 inv_vol + P3 rank_buffer + P4 vt_target, 全部cfg开关守卫, 引擎文件零改动
- 等价性校验: 开关全关闭 → 必须逐位复现 seedB_v0_full/locked_metrics.json (diffs={}); 另复跑 v1e_vol 核对第一批可复现性
- 择时注入用 market dict (run 后 pop, 不污染共享 mk)
- 产物命名 results/a2b_<ver>_{full,locked}_*; 汇总 a2b_backtest_summary.json

## 阶段2 执行留痕（22:4x~）
- a2b_run_candidates.py 已启动(HP PID 1283026, /tmp/a2b_bt.log)
- 等价性校验通过: full diffs={} / locked diffs={} (a2b ext runner 开关全关逐位复现 seedB 基线)
- v1e_vol 复跑核对进行中(结果待记)

## 阶段2 中途读数（~23:1x）
- v1e_vol 复跑核对: full diffs={} / locked diffs={} —— 第一批数字可复现 ✓（a2b_repro_* 文件即证据）
- 候选陆续出数:
  - v1f_lv70 full: ann=0.1708 mdd=-0.6551 sharpe=0.749 turn=0.5149
    （对照 v1e full 0.1773/-0.6671/0.759：深低波倾斜 MDD 再降 1.2pp 但 SR 持平略降，
     σ≈0.018 档需 Sharpe≥1.03 → v1f 预计过不了 g4，属方向覆盖件，符合设计预期）

## 阶段2 读数更新（~23:3x，12/14 腿完成）
| 候选 | full ann/mdd/sharpe | locked ann/mdd/sharpe | 换手 | 初判 |
|---|---|---|---|---|
| v0_seed(父) | 0.2635/-0.6949/0.903 | 0.2626/-0.6949/0.885 | 0.27 | 基线 |
| v1f_lv70 | 0.1708/-0.6551/0.749 | 0.1647/-0.6551/0.721 | 0.51 | σ≈0.018→需Sharpe≥1.03，0.72差远，预期REJECT(g4) |
| v1g_ivw | 0.2694/-0.6973/0.929 | 0.2732/-0.6973/0.920 | 0.27 | σ未降多少(MDD同父)，需≥1.09，预期REJECT(g4) |
| v1h_buf | 0.2707/-0.6891/0.934 | 0.2699/-0.6891/0.915 | 0.17 | 换手降37%成本友好，但SR仍0.92<1.09，预期REJECT(g4) |
| v1j_vt18 | 0.1852/-0.5015/0.865 | 0.1808/-0.5015/0.840 | 0.27 | MDD改善19.3pp! σ_d≈0.0136→sr0≈0.0303，需sr≥0.0552，实际sr=0.0529→贴线，DSR≈0.93边缘 |
- v1i_q3z 跑数中（主攻候选）
- 注意 v1g_ivw 换手显示 0.2726 与父相同——合理：inv_vol 只改权重不改进出名单，调仓名单变化仍同父

## 阶段2 读数更新2（~23:5x，14/14腿+q3z完成）
- v1i_q3z full: ann=0.1584 mdd=-0.3474 sharpe=0.921 | locked: ann=0.1580 mdd=-0.3474 sharpe=0.905
  - MDD 从 -69.49% 改善到 -34.74%（+34.75pp，史诗级）
  - DSR 精确估算（N=45, c=2.2356, σ_d≈0.0108, sr0≈0.0242, sr=0.0570, T=4489）: DSR≈0.988 > 0.95 → g4 预计 PASS
  - 换手 0.2721 与父完全一致（择时不改进出名单，只改仓位系数——维度隔离干净）
- v1j_vt18 locked DSR≈0.935 边缘（贴线不过 0.95）
- 剩 v1k_q5z 两条腿跑数中
- a2b_* 文件已 70 个（equiv 10 + repro 10 + 5候选×10），v1k 完成后 80

## 阶段3 门禁裁决（N=45, n_trials_cum=44）
| 候选 | g1 | g2 | g3 | g4 DSR | g5 | g6 | 裁决 |
|---|---|---|---|---|---|---|---|
| v1f_lv70 | PASS | PASS | PASS | FAIL 0.6834 | PASS | PASS | REJECT |
| v1g_ivw | PASS | PASS | N/A | FAIL 0.7666 | PASS | PASS | REJECT |
| v1h_buf | PASS | PASS | N/A | FAIL 0.7656 | PASS | PASS | REJECT |
| v1i_q3z | PASS | PASS | N/A | **PASS 0.9776** | PASS | PASS | **PASS** |
| v1j_vt18 | PASS | PASS | N/A | FAIL 0.8953 | PASS | PASS | REJECT |
| v1k_q5z | PASS | PASS | N/A | **PASS 0.9743** | PASS | PASS | **PASS** |
- g3 N/A: v1g/v1h/v1i/v1j/v1k 因子集与 active 相同（择时/加权/缓冲不是新因子），无信息量
- 两 PASS：v1i_q3z（DSR 更高 0.9776 + MDD 更深改善 -34.74% vs -37.37%）与 v1k_q5z（收益更高 17.0% vs 15.8%）
- activate 选择 v1i_q3z：DSR 余量更大（约束门禁上更稳）、MDD 改善更深、T线预验证主候选（q5z 是设计备份）、窗口36月适应更快

## 阶段4 收口（~23:5x 完成）
- activate v1i_q3z: D-20260816-015 (activate) + D-20260816-016 (a2b_batch_activate)
  main.json md5 fbba3372→35b8e6a7; v0_seed→sota, v1i_q3z→active; switch_log: v0_seed->v1i_q3z
- v1k_q5z PASS 留 pending 备选(registry 在位)
- ledger: 24 行(12 旧+12 新: 6 backtest n_trials_cum 39→44 + 6 evaluate N=45)
- 产物: a2b_v1* 60 件(6候选×10) + equiv/repro 20 件 + summary + gate_table + 报告 7284B
- 报告: results/a2b-iteration-report.md (含通过线推导/逐候选表/门禁表/风险披露/下批建议)
- 回滚兜底: v0_seed.main.json.snapshot 在位; registry.timing 登记 data_source/disable_switch
