# task-0436 看板量化页模型解释模板更新 — 过程笔记

## 1. 现场取证（旧文案，node 跑 server.js 提取的模板函数 + a13 实参数）

渲染输入：registry `/root/.openclaw/workspace-quant/model/registry/a13_rsraw_e1f10dz.json` + mj `/root/.openclaw/workspace-quant/results/a13_rsraw_e1f10dz_locked_metrics.json`

### 旧输出（2026-08-21 取证，/tmp/t0436_before_a13.txt）

```
== selection ==
  [股息闸门] 股息率(TTM) ≥ 2.0%：只留持续真正分红的公司
  [盈利闸门] ROE(TTM) ≥ 15%：盈利质量门槛
  [资产闸门] ROA(TTM) ≥ 10%：资产回报门槛
  [价格闸门] 收盘价 ≤ 10 元：锁定小盘低价域
  [排序] 按扩展因子排序：复合因子
  [持仓] 每月选前 20 只等权持有
  [次新剔除] 上市不足 365 天的次新股不参与（基本面不足、波动极端）
== timing ==
  [信号 A · 估值仓位] q3z 估值分位信号：q3z(win36,zscore,hi1.0,cut0.40,w_min0.3)，估值越低仓位系数越高（区间约 0.6~1.0）
  [信号 B · 趋势仓位] 池内等权指数(含退市)月末收盘 vs MA200, 破位×0.6，跌破趋势线时仓位 ×0.6
  [合成] 月度乘法合成, 无重裁剪(自然下限0.18)
  [仓位下限] 乘法合成后仓位自然下限约 0.18（0.3 × 0.6），不清仓
  [说明] q3z × 趋势二信号 [v2b_trr 血统]
  [信号定义] EW指数月末<MA200 → ×0.6; 与q3z仓位系数相乘
== trading ==
  [成本模型] v2：买卖双边计入佣金+印花税+冲击成本
  [一字板约束] 一字涨停不追买、一字跌停不强卖，该笔放弃成交（保守口径）
  [换手] 月均换手约 45%
  [平均持仓] 平均持仓 19.9 只
  [初始资金] 1000 万
```

## 2. 过时/失真点清单（当前显示 vs 应该显示）

| # | 旧文案 | 问题 | 应该显示 |
|---|---|---|---|
| 1 | 股息闸门 ≥2.0% | a13 mj 标 `gates:"OFF(div/roe/roa/price_cap)"`，闸门未启用，数值是残留参数 | 原始全市场宇宙，无预筛闸门 |
| 2 | 盈利闸门 ROE≥15% | 同上，虚假条目 | 同上 |
| 3 | 资产闸门 ROA≥10% | 同上 | 同上 |
| 4 | 价格闸门 ≤10元 | 同上 | 同上 |
| 5 | 排序「按扩展因子排序：复合因子」 | 只认老 ext_factor/ext_weights schema，不认 ext_mode=ranksum+ext_specs 四因子 | ranksum 四因子+权重+方向 |
| 6 | （无 E1 条目） | e1_guard=0 导致护栏消失，但 e1_lambda=1.0/e1_deadzone=0.3 因子化守卫在用（a13 核心特征 e1f10dz） | E1 因子化惩罚条目 |
| 7 | （无股票池说明） | raw_universe=1 未渲染 | 原始宇宙条目 |
| 8 | timing「区间约 0.6~1.0」 | q_key 实为 w_min0.3 → 区间 0.3~1.0（0.6 是老参数遗留，写死） | 从 q_key 解析 w_min/hi 动态渲染 |
| 9 | trading 无调仓节奏 | 月频调仓未体现 | 月频调仓条目（222次/18.5年佐证） |
| 10 | trading cost_model/limit_board 仅依赖 mj | mj 缺字段时 trading 层空白（registry 有值也不渲染） | fallback 到 selParams |

正确无需动的：持仓20只、次新剔除365天、timing 趋势/合成/下限、trading 成本v2/一字板/换手/持仓数/初始资金。

## 3. 兼容面（老版本 registry 实查）

- v1i_q3z / v2b_trr：sort=mv，无 ext_mode/raw_universe/e1 字段 → 闸门照旧渲染（当年真启用），老分支保留
- v5h_xsub：ext_factor=low_amount + ext_weights + e1_guard=true → 老 ext 分支 + 老剔除护栏保留
- a9_ranksum_raw：ranksum + raw_universe=1 + e1_guard=1（老剔除护栏仍开）→ e1_guard 优先走老文案
- a14_crowdf2 / a15_csad_resid：ranksum + e1_lambda=1.0 因子化 → 同 a13 走新分支
- 所有 q3z 版本 q_key 均为 w_min0.3 → 区间修正对老版本同样更准

## 4. 改动方案（只动模板函数区 L3043-3114）

- 新增 `quantTplFactorName`（因子→人话映射，未知名原样）
- 新增 `quantTplE1Penalty`（e1_lambda>0 的因子化守卫文案）
- quantTplSelection：raw_universe/gates OFF 分支（跳过四闸门渲染，显示原始宇宙）；ext_mode=ranksum 分支（四因子权重方向）；ext_filter_all；e1_guard=0&&e1_lambda>0 的护栏分支
- quantTplTiming：从 q_key 解析 w_min/hi 动态渲染估值仓位区间与合成下限，解析失败降级
- quantTplTrading：签名加 selParams（mj 缺字段时 fallback cost_model/limit_board）；月频调仓条目
- quantExplainVersion：trading 调用传 selParams

## 5. 验证记录（全部通过）

- `node --check server.js`：SYNTAX OK（改后多次复查）
- 本地渲染（/tmp/t0436_after_a13.txt，脚本 /tmp/t0436_render.js 喂 a13 registry+locked metrics）：见下方「新文案」
- 服务重启：`systemctl restart agent-dashboard` → active
- 线上 `/api/quant/active`：active=a13_rsraw_e1f10dz，explanation 含 ranksum/市值/低PB/E1 守卫/q3z/0.3~1.0 全部关键字
- 历史版本线上抽查：`?version=v5h_xsub` 闸门条目保留（该版本确实启用）、老 ext schema「低成交额（权重 1/0）」正常、老剔除护栏正常；`?version=v1i_q3z` ok
- 本地兼容矩阵（/tmp/t0436_compat.js）：v1i_q3z（mv+单信号兜底）、v2b_trr（mv+双信号）、v5h_xsub（ext 老 schema+e1_guard 老剔除）、a9（ranksum+raw+老剔除护栏）全部按各自血统正确渲染，无回归
- 未触碰 usage/接口代码（task-0433 区域），git 分 hunk 提交隔离

### 新文案（a13 在役渲染，全量）

```
== selection ==
  [股票池] 原始全市场宇宙（不预筛市值/估值/流动性，质量约束内嵌于排序因子）
  [排序] 复合排序（ranksum）：市值[权重1.0·越小越好] + 20日均成交额[权重1.0·越小越好] + 低PB(倒数)[权重0.7·越大越好] + ROE(TTM)[权重0.3·越大越好]，各因子截面排名加权求和后取前 N
  [因子缺值] 任一排序因子缺值的股票整体剔除（ext_filter_all）
  [持仓] 每月选前 20 只等权持有
  [护栏 E1] E1 守卫（因子化）：暴跌股惩罚因子以 λ=1.0 权重计入排序总分，死区 30%（回看期跌幅 30% 以内不罚，超出部分计罚）——软约束压排名，不再整只剔除
  [次新剔除] 上市不足 365 天的次新股不参与（基本面不足、波动极端）
== timing ==
  [信号 A · 估值仓位] q3z 估值分位信号：q3z(win36,zscore,hi1.0,cut0.40,w_min0.3)，估值越低仓位系数越高（区间 0.3~1.0）
  [信号 B · 趋势仓位] 池内等权指数(含退市)月末收盘 vs MA200, 破位×0.6，跌破趋势线时仓位 ×0.6
  [合成] 月度乘法合成, 无重裁剪(自然下限0.18)
  [仓位下限] 乘法合成后仓位自然下限 约 0.18（0.3 × 0.6），不清仓
  [说明] q3z × 趋势二信号 [v2b_trr 血统]
  [信号定义] EW指数月末<MA200 → ×0.6; 与q3z仓位系数相乘
== trading ==
  [成本模型] v2：买卖双边计入佣金+印花税+冲击成本
  [一字板约束] 一字涨停不追买、一字跌停不强卖，该笔放弃成交（保守口径）
  [调仓节奏] 月频调仓（18.5 年 222 次）
  [换手] 月均换手约 45%
  [平均持仓] 平均持仓 19.9 只
  [初始资金] 1000 万
```

### 旧 vs 新关键对照

- 4 个假闸门（股息/盈利/资产/价格）→ 消失，替换为「原始全市场宇宙」条目（依据 mj `gates:OFF` + selParams.raw_universe=1）
- 「按扩展因子排序：复合因子」→「复合排序（ranksum）：市值[权重1.0·越小越好] + 20日均成交额[权重1.0·越小越好] + 低PB(倒数)[权重0.7·越大越好] + ROE(TTM)[权重0.3·越大越好]」+ ext_filter_all 条目
- E1 条目从无 → 「E1 守卫（因子化）：λ=1.0，死区 30%」（e1f10dz 血统核心特征）
- timing「区间约 0.6~1.0」→「区间 0.3~1.0」（q_key w_min0.3 动态解析，不再写死）
- trading 新增「月频调仓（18.5 年 222 次）」；cost_model/limit_board 增加 registry 回退

## 6. git 提交

- commit `bc89c31`（仅模板区 68 insertions/16 deletions，server.js L3043-3165）
- 与并行 task-0433 隔离：工作区混有其未提交改动（L5359+/L7033/L13433 区域，usage/接口），用 `git apply --cached` 分 hunk 只提交自己的部分；0433 随后自行提交 `5f93320`，历史无交叉

## 7. 结论

10 个过时/失真点全部处理；老版本（v1i/v2b/v5h/a9）兼容验证通过；服务 active；线上 API 关键字验证通过。
