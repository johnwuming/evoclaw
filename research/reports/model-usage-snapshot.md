# 模型用量快照

> 查询时间：2026-03-31 22:17 CST

## 汇总

| Provider | 套餐 | 状态 | 备注 |
|----------|------|------|------|
| **ZAI（智谱）** | Pro | 🟡 部分可用 | 月度 token 44% 剩余，时间配额 30% 剩余 |
| **MiniMax** | Token Plan | 🔴 已耗尽 | 文本模型 5h/周额度均已用完 |
| **Kimi** | Coding Plan | ⚪ 无法查询 | Coding API 不暴露用量接口 |
| **腾讯云 Token Plan** | Token Plan | ⚪ 无法查询 | 无公开用量 API |

---

## 详细数据

### 1. ZAI（智谱）— Pro 套餐

**端点**: `GET https://api.z.ai/api/monitor/usage/quota/limit`

| 额度类型 | 已用/总额 | 剩余 | 维度 | 重置时间 |
|----------|-----------|------|------|----------|
| TOKENS_LIMIT | 56% | **44%** | 月度 | 2026-04-01 02:58 CST |
| TOKENS_LIMIT | 28% | **72%** | 周度 | ~2026-04-03 |
| TIME_LIMIT | 307/1000 | **30%** (693 remaining) | 月度 | 2026-06-28 |

TIME_LIMIT 使用明细：search-prime: 307, web-reader: 0, zread: 0

### 2. MiniMax — Token Plan

**端点**: `GET https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains`

| 模型 | 5h 窗口已用 | 5h 总额 | 5h 剩余 | 周已用 | 周总额 | 周剩余 |
|------|------------|---------|---------|--------|--------|--------|
| MiniMax-M* (文本) | 1500 | 1500 | **0%** 🔴 | 15000 | 15000 | **0%** 🔴 |
| speech-hd (TTS) | 9000 | 9000 | **0%** 🔴 | 63000 | 63000 | **0%** 🔴 |
| image-01 | 99 | 100 | **1%** 🔴 | 699 | 700 | **0.1%** 🔴 |
| Hailuo-2.3-Fast | 0 | 0 | N/A | 0 | 0 | N/A |
| Hailuo-2.3 | 0 | 0 | N/A | 0 | 0 | N/A |
| music-2.5 | 0 | 0 | N/A | 0 | 0 | N/A |

> 5h 窗口重置时间约 23:17 CST（约 1 小时后）

### 3. Kimi — Coding Plan

**Key**: `sk-kimi-wmHvAql...` (kimi.com/coding 专用)

- ✅ API key 有效（`/v1/models` 正常返回）
- ❌ 无公开用量查询 API
- Coding Plan 的 balance 需通过 moonshot.cn 平台查询，但 coding key 与 moonshot key 不互通
- 建议：登录 [platform.kimi.com](https://platform.kimi.com) 查看

### 4. 腾讯云 Token Plan

**Key**: `sk-tp-ulYc2Ly...`

- ✅ API key 有效（chat completions 正常返回）
- ❌ 无公开用量查询 API（`/plan/v3/usage` 等端点返回 `not_authorized`）
- 建议：登录腾讯云控制台查看

---

## 原始 JSON

<details>
<summary>ZAI 响应</summary>

```json
{"code":200,"msg":"Operation successful","data":{"limits":[{"type":"TOKENS_LIMIT","unit":3,"number":5,"percentage":44,"nextResetTime":1774972703795},{"type":"TOKENS_LIMIT","unit":6,"number":1,"percentage":72,"nextResetTime":1775181642998},{"type":"TIME_LIMIT","unit":5,"number":1,"usage":1000,"currentValue":307,"remaining":693,"percentage":30,"nextResetTime":1777255242999,"usageDetails":[{"modelCode":"search-prime","usage":307},{"modelCode":"web-reader","usage":0},{"modelCode":"zread","usage":0}]}],"level":"pro"},"success":true}
```

</details>

<details>
<summary>MiniMax 响应</summary>

```json
{"model_remains":[...],"base_resp":{"status_code":0,"status_msg":"success"}}
```

</details>
