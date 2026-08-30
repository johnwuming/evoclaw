# task-0592 过程笔记（2026-08-31 00:45 开始）

任务：BFF 维护窗口合批开发四项
① perf-history.js fallback 手写字面 label 清除 → 从 policy.json 派生
② policy-lint.mjs 扩扫 BFF 源码
③ candidates 徽标 computed height 断言
④ lint 输出附扫描面清单

## 文件清单确认（00:45）
- /root/.openclaw/workspace/tools/quant-bff/src/perf-history.js = 6202 bytes（可全读）
- /root/.openclaw/workspace/tools/quant-dashboard/scripts/policy-lint.mjs = 24382 bytes（<30KB 可全读）
- BFF src 其他文件：app.js 22340 / config.js 2128 / ctx.js 6046 / ledger.js 10097 / nav-series.js 4971 / pending-risks.js 2258 / replay.js 8213 / risk-gates.js 13892 / server.js 1712


## 现状确认（00:47）
### ① 手写字面位置
- perf-history.js activeEntry: `label: perf.label ?? 'vC-0 现役（权威·等波动率 58/42）'`
- **performance.json 无 label 字段**（实测 label=None）→ 线上实际输出的正是旧 fallback，含 task-0590 已撤销的「权威」字样，与 policy.json 矛盾。改动必要性强。
- policy.json（/root/.openclaw/workspace/tools/quant-dashboard/policy.json，3090B）caliber.display_name = "设计口径·提案轨迹（静态 58/42 月度再平衡·无风控层）"（08-30 task-0590 版本，已无权威字样）
- BFF src 现无任何 policy.json 引用；config.js 需加 policyPath（env POLICY_FILE 可覆盖，默认 ../../quant-dashboard/policy.json）
- 派生方案：perf.label 缺失 → 读 policy.caliber.display_name → 仍缺则降级 portfolio_version_id（禁手写字面）
### ② policy-lint 现状
- ⑤d 现有：Candidates.jsx/Version.jsx 断言无「权威口径（等波动率」字面 + 必须引用 rolling_compare/display_name
- 需扩：旧字面清单加入「vC-0 现役（权威·等波动率 58/42）」，扫 BFF src/*.js（口径相关源码）
### systemd 实况
- LEDGER_DIR=/root/.openclaw/workspace/tools/quant-bff/live（dataDir=live/data）
- ReadWritePaths 仅 state（BFF 零写面，读 policy.json 无碍）

## 改前基线（00:50）
- curl 127.0.0.1:8180/api/v1/perf-history → versions[0].label = "vC-0 现役（权威·等波动率 58/42）"（旧字面在场，与 policy.display_name 矛盾）
- dist/assets 无「权威·等波动率」「权威口径（等波动率」旧字面（前端产物干净）
- BFF src 旧字面唯一处：perf-history.js:75；app.js 等注释中「权威」单词不属徽标字面（lint 断言用完整子串防误伤）
- t0594 编号未占用；无头检查模板=t0593-headless-check.cjs + t0578-static-server.cjs(8981, /quantv6/api→8180 代理)

## 实施方案
1. config.js: +policyPath（env POLICY_FILE 覆盖，默认 ../../quant-dashboard/policy.json）
2. perf-history.js: activeEntry label = perf.label ?? policy.caliber.display_name ?? portfolio_version_id（readPolicyLabel 全异常→null，不阻塞列表）
3. lint ⑤d 扩：OLD_LABEL_LITERALS=['权威口径（等波动率','现役（权威·等波动率','权威·等波动率 58/42']，扫 DASH pages jsx + DASH dist/assets/*.js + BFF src/*.js；perf-history.js 加 display_name 同源派生断言
4. lint 输出末尾加扫描面清单（SCAN 面与实际循环同数据源）
5. scripts/t0594-headless-check.cjs：8981 起服→390x844→bodyScrollW/docScrollW=390 + .cand-badge-auth computed height (0<h≤90px 实测) + badge text==policy.display_name + /quantv6/api/v1/perf-history versions[0].label==policy.display_name
6. 前端源码零改动（只加 scripts 脚本）→ 无需 rebuild；dist 已验证无旧字面

## ①验证证据（00:53）
- node --check src/config.js src/perf-history.js → PASS
- systemctl restart quant-bff && is-active → active
- policyPath 实测 = /root/.openclaw/workspace/tools/quant-dashboard/policy.json
- /perf-history versions[0].label = "设计口径·提案轨迹（静态 58/42 月度再平衡·无风控层）" == policy.caliber.display_name（逐字断言 ASSERT_OK，旧字面消失）
- 抽端点：/perf-history/vC-0 → 200；/engines → 200

## ②④验证证据（00:58）
- node --check scripts/policy-lint.mjs → PASS；node scripts/policy-lint.mjs → PASS + 扫描面清单（实扫 13 文件，禁字面 3 条，在扫/不扫盲区明示）
- 首跑曾 FAIL：perf-history.js 注释里残留完整旧字面被⑤f抓到 → 注释改写后 PASS（防回流断言连注释同禁，符合「任何位置禁手写」）
- 负样本自测：复制 BFF 到 /tmp 注入旧字面 fallback → lint FAIL 抓到「残留旧口径字面」→ 防回流有效，已清理临时目录
- BFF 重启后 is-active=active

## ③验证证据（01:05）
- 实测发现：原 CSS .cand-badge-auth 为 white-space:nowrap → 30 字长文案不折行而是溢出画出徽标框（height=19px 单行），与任务③「会折 2-3 行」预期不符——断言兜底正是抓这类「CSS 声称 vs 实际渲染」偏差
- 修正 styles.css：white-space:normal + overflow-wrap:anywhere + line-height 1.5 + border-radius 999px→10px（折行形态）
- rebuild：VITE_API_BASE=/quantv6 npm run build → 产物 dist/assets/index-DKUl66bW.js，注入值核对 /quantv6 ✓
- t0594-headless-check.cjs（自含起 t0578 服 8981）：CHECK_PASS
  bodyScrollW=390 docScrollW=390 / badgeHeight=19 (0<h≤90 兜底界) / whiteSpace=normal / badgeText∋policy.display_name / BFF apiLabel==policy.display_name
  （当前文案在 390px 恰好单行放下；文案升版变长时 max-width:100% 内折，height≤90 断言兜底）
- 截图存证：shared/results/work/task-0592-candidates-390.png（视觉抽查：无横滚、无布局崩坏、徽标文案完整无重叠）
- 前端源码改动=styles.css（徽标样式）→ 已 rebuild；scripts/t0594 为新增测试脚本不入 bundle

## 终态汇总（01:06，预算内 ~21min）
### 修改文件
1. tools/quant-bff/src/config.js —— +policyPath（env POLICY_FILE 覆盖，默认 ../../quant-dashboard/policy.json）
2. tools/quant-bff/src/perf-history.js —— activeEntry label 同源派生：perf.label → policy.caliber.display_name → portfolio_version_id；旧手写字面全文件清除（含注释）
3. tools/quant-dashboard/scripts/policy-lint.mjs —— ⑤d 重构为 LITERAL_SCANS 扫描面（dash pages jsx + dash dist/assets/*.js + bff src/*.js，13 文件实扫，3 条禁字面）；新增 ⑤e perf-history label 同源派生断言、⑤f 旧口径字面防回流扫描；PASS 输出追加「扫描面清单」在扫/不扫盲区
4. tools/quant-dashboard/src/styles.css —— .cand-badge-auth 折行化
5. tools/quant-dashboard/scripts/t0594-headless-check.cjs —— 新增（390x844 徽标 computed height + 同源断言 + 截图）
6. dist/ 产物 rebuild（index-DKUl66bW.js / index-SJZFrKgN.css，/quantv6 注入核对）
### 验证命令与结果
- node --check ×4 → 全 OK
- node scripts/policy-lint.mjs → PASS（6 检查 + 扫描面清单）
- 负样本自测：/tmp 伪造 BFF 注入旧字面 → lint FAIL 抓到（防回流有效）
- systemctl restart quant-bff && is-active → active；/api/v1/perf-history、/perf-history/vC-0、/engines → 200
- API label == policy.caliber.display_name → True（python 逐字断言）
- node scripts/t0594-headless-check.cjs → CHECK_PASS（bodyScrollW=390、badgeHeight=19、文本/label 同源）
