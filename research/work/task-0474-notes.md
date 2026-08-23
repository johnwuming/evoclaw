# task-0474 笔记（边查边写）

## 2026-08-23 22:44 启动
- 任务：可转债线去相关强化（正股行业中性化新 E2 预注册），目标 corr(A,组合)<0.5
- 必读：R-289（判门过、corr 0.583 卡点、§6 去相关路径）、R-288（V2 冻结参数）、R-291（B 主候选=可转债、独立性未达标=可修复）、R-262（行业轮动关闭=形态级，正股行业中性化≠行业轮动，不混淆）
- 任务中心 expected_output: shared/results/01-AI行业研究/R-293-可转债去相关强化.md（路径疑为 01/05 笔误；正文按 05-量化投资/ 落盘 R-293 预注册 + R-294 执行报告）
- 数据位置修正：r281 面板实际在 /root/.openclaw/workspace/work/r281/（非 shared/results/work/r281）
  - month_end_panel.parquet（3.7MB）、panel_daily.parquet（25MB）、ic_*.csv
- a13 在役 NAV：/root/.openclaw/workspace/shared/results/04-投资研究/a13_rsraw_e1f10dz_locked_nav.csv（R-289 corr 0.583 用的口径）

## 继续（重试恢复点）
- r467 gate json independence: a13_e1f10dz_locked 0.583 / a13_e1f10_locked 0.583 / i3_abs_s4 0.590 / i3_base 0.585（102月重叠）
- a13 locked nav 止于 2024-06-28（与 2018-02..2026-07 重叠=77 月）；i3 覆盖全窗（102月）
- e2v2_backtest.py 逻辑已读：Top-30 sqrt 梯度、规模中性化 OLS、BUFFER=50、成本 0.001 单边、基准 /tmp/r281/csi_cb_index.parquet
- akshare 1.18.94 可用；panel 1001 唯一 bond code
- 回测窗口过滤 universe：675 唯一 bond（2018-01..2026-06），月均约 37 券
- 需 akshare 采集：bond→正股代码→申万/东财行业
- R-281 面板无正股代码列（只 code/date/close/prem/convval/dbval/ym/债券简称/list_dt/发行规模/信用评级/issue_sz/mdate/mom...）
- bond_zh_cov_info_ths() 无参返回当前全部转债 957 行，含 正股代码/正股简称 → 可作 bond→正股映射（但仅当前在册）
- 回测窗口 675 唯一券（2018-01..2026-06 过滤后）；需评估当前快照覆盖率，缺口用 bond_zh_cov_info(symbol) 单券补
- bond_zh_cov_info(symbol, '基本信息') 单券可回历史：110002→正股600219(南山铝业, 2009已退市) → 映射能力 OK
- 计划：① 用 bond_zh_cov_info_ths() 全量 957 当前券建 bond→正股映射 ② 对回测窗口 675 券中未覆盖的历史券按需 bond_zh_cov_info() 补 ③ 正股→行业 用 akshare 全A股所属行业（stock_zh_a_spot_em 含行业列 或 stock_individual_info_em 单股）
- task中心 expected_output 确认 R-293 编号（路径 01-AI行业研究 疑笔误，正文按 05-量化投资 落盘 R-293 预注册 + R-294 执行报告）
- stock_zh_a_spot_em() 首试连接错误 → 重试；备选 stock_individual_info_em(symbol) 单股行业
- 东财 EM 接口（stock_zh_a_spot_em / stock_individual_info_em）连续 ConnectionError（可能限流/封禁）
- bond_zh_cov_info_ths（同花顺源）可用；转测行业源：THS 行业板块 / cninfo / 申万
- THS 行业板块 stock_board_industry_name_ths() 可用（90 个 881xxx）；EM 板块接口被封 → 行业映射优先 THS 源（akshare stock_board_industry_cons_ths）
- 任务设计：V2 冻结形态基础上新增「正股行业暴露中性化」腿；n_trials≤4；独立性门 corr(A,组合)<0.5（77月重叠 a13 口径 + 102月 i3 口径披露）
- akshare 可用行业映射函数盘点：sw_index_third_cons / index_component_sw / stock_industry_category_cninfo / stock_industry_clf_hist_sw / stock_board_industry_cons_em(EM被封) / stock_board_industry_info_ths
- 下一探针：stock_industry_clf_hist_sw（申万历史分类单调用）与 stock_industry_category_cninfo（巨潮）与 stock_zh_a_spot_em 重试
- sw_index_third_cons / index_component_sw / sw_index_third_info 存在（申万源）
- stock_industry_clf_hist_sw SSL 失败（swsresearch 不可达）
- 候选映射路线：A) 申万三/一级成分（sw_index_third_info 全量 + sw_index_third_cons 每指数成分）B) EM spot 单调用（被封，可重试）C) cninfo
- 正股行业用途：仅中性化腿（去相关），TAXONOMY 需在预注册写明；优先申万（R-255/262 遗产同源，便于对照）
