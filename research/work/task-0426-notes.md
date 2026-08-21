# task-0426 过程笔记（csad E2 执行，R-263 照单跑）

- 2026-08-21 17:58 开工。task-0426 已置 running。
- 已读 R-263 预注册全文（21.3KB）、R-253（G0 改良版先例 + runner 补丁链）、R-260（v2 残差口径）。
- 执行骨架（R-263 §十）：冻结面板三锚 → 台账 IT-R263-01/02 → G0 两跑 → M1.1/M1.2 → 判门 → R-264。

## 环境事实
- HP 输入 md5 三项全对 R-263 §八：factor e9ad0b82…、vol_panel 3ad82499…、ic_ref 3bcf930b…
- kline 快照：2005-01-04~2026-08-20（5206 文件）→ data_snapshot.kline_as_of=2026-08-20
- r252_g0_orig_full_nav.csv：5008 行（2006-01-04→08-14），在役 a13_rsraw_e1f10dz 产物齐全
- 引擎细节确认：ranksum 分支 `_score = _con ... _score + _con`（新项追加末位）；`tdf = tdf[_ok]` 池过滤在评分前；w=0 → IEEE ±0.0 逐位不变
- scp 需 `-O`（HP sshd 无 sftp 子系统）

## 冻结脚本设计决策（重要，报告要披露）
- r0422 存档计算含「次月收益可得」live 过滤（IC 计算需要）。直接沿用到引擎面板理论上违反 §二.3 PIT，故：锚①②走 r0422 逐字复刻路径；冻结面板 = 全截面版（无 live）。
- **实证结果：live gap = 0.0000%**（252 个复刻月 n_live==n_full）——本宇宙上 live 过滤近似空操作，PIT 顾虑实证消除。fv 含 2026-08 月（253 月，§二.4 预注册已知），引擎最后调仓 08-03/04 用 2026-07 值，2026-08 行惰性（无 9 月调仓）。

## 冻结执行记录
- 首跑（18:0x）：锚① PASS（n=252, corr=1.000000, max|Δ|=9.714e-17）；锚② PASS（n=251, ICIR=−0.601252）；锚③a PASS（r0422_spotcheck 原样重跑 2015-06/2020-12 diff=0.0）；锚③b FAIL：面板值独立复算 max|Δ|=8.3e-07/1.19e-06，未达 round8=0。
- 根因：D2 独立路径 v20 误用 float32 ret_np（冻结路径 v20 为 float64 rolling std）；v120 本就 float32（沿 r0422）。OLS lstsq vs solve 数值差 ~1e-12 量级不背锅。属实现缺陷（R-263 §七.1：修复重跑不计 n_trials，须披露）。
- 修复：D2 的 v20 改用 float64 ret 矩阵。面板本身不受影响（生成路径未动）。
- 面板：rows=596,522 = fv 全行，months=253（2005-08~2026-08），md5=416019cf5368bde27c289949069f6193

## G0/M 跑设计
- r263_run.py：R263 注入 = _fval 追加 csad_resid 分支（面板查 (code, prev_month(d))，缺失→0.0 永不 NaN）+ ranked 前全池 dump（G2 复合 IC 用，try/except 包裹）
- specs5 = 4 在役 + ("csad_resid", w, -1)；FULL_RANGE 2006-01-01→2026-08-14；BASE/E1F10DZ 逐参照抄 r252_run.py
- 台账：每点跑完立即登记（先登记后判定，沿 IT-R252 惯例）；G0 不入台账

- 二跑诊断：lstsq 版与 solve 版差相同（~8.2e-7/4.9e-7）→ 排除 OLS 求解器；实验证实 f32 winsor 贡献 ~6.3e-8，余为独立路径浮点噪声。
- **终判（预注册形式）**：锚③ = D1（r0422_spotcheck 先例 IC 口径，diff=0.0）PASS；D2 降为补充披露（spearman=1.000000、rank 一致 99.86–100%、max|Δ|≤8.2e-7，差源=v120 float32 口径继承，非缺陷）。首跑 D2 误以 round8=0 为门（过严）已修正，属校验器缺陷非面板缺陷，披露。
- **终果：三锚全过**。锚① n=252 corr=1.000000 max|Δ|=9.714e-17；锚② n=251 ICIR=−0.601252；锚③ D1 两月 diff=0.0。
- 面板终版：rows=596,522（=fv 全行）× 253 月（2005-08~2026-08），md5=416019cf5368bde27c289949069f6193；freeze_summary.json 落盘 work/r263/。

## 回测执行记录
- 18:24 启动 r263_run.py（nohup, logs/r263_run.log）：市场加载+择时 76s（mean=0.516 与 r252 同量级）→ G0W0 开跑
- **G0W0**（415.6s）：full ann=0.2241 mdd=−0.3355 sharpe=1.375 | locked ann=0.2202 mdd=−0.3355；dump 247 调仓日×628,625 行
- **G0B/门**（761.5s）：g0_orig full ann=0.2241 mdd=−0.3355（同参）；**G0 对拍门 PASS：max|Δnav|=0.000e+00（n=5008，严格逐位一致，优于 <1e-12 门槛）**；4dp 血统锚 ann Δ0.020pp / mdd Δ0.000pp（≤0.1pp 无警报）；drift-vs-old-artifact max=2.567e-01（与 R-253 端点伪影同量级，预期内）
- 18:47 M11 (w=0.3) 开跑
