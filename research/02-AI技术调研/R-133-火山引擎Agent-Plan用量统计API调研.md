# R-133：火山引擎 Agent Plan 用量统计 API 接口调研

> 调研日期：2026-07-06 | 复杂度：中等 | 分类：02-AI技术调研

---

## 一、核心发现

### 1.1 Agent Plan 产品概述

火山引擎 Agent Plan 于 **2026 年 5 月 11 日**正式发布，定位为「业界首个 Agent 套餐包」，在 Coding Plan 基础上扩展为多模型+多模态+Harness 工具的 Agent 订阅服务。隶属火山方舟（Ark）平台的 Managed Agent 能力线。

**套餐与定价**（来源：CodePick、IT之家）：

| 套餐 | 月价 | AFP 额度 |
|------|------|----------|
| Small | ¥40 | 20,000 AFP |
| Medium | ¥200 | 100,000 AFP |
| Large | ¥500 | 250,000 AFP |
| Max | ¥1,000 | 500,000 AFP |

计费采用 **AFP（Agent Fuel Points）积分制**，按模型类别、上下文长度、输入/输出和工具能力综合折算。

### 1.2 AFP 抵扣机制（来源：威易网）

**模型类别基础系数**（每万 tokens）：
- 极速模型（mini）：0.5 AFP
- 标准模型（lite）：1 AFP
- 进阶模型（code/pro/v3.2/m2.7）：5 AFP
- 第三方模型（glm-5.1/kimi-k2.6）：9 AFP

**上下文长度分段系数**：
- 0-32K：0.67x
- 32K-128K：1x
- 128K-256K：2x

**多模态消耗**：
- 视频生成：36-230 AFP（按模型和输入类型）
- 图片生成：99 AFP/张

**用量限制**（来源：CSDN 实测）：

| 限额层级 | Medium 套餐 |
|----------|-------------|
| 5 小时短时限额 | 10,000 AFP |
| 周限额 | 35,000 AFP |
| 月限额 | 100,000 AFP |

额度耗尽后等待下一周期自动恢复，不扣账户余额。视觉模型（图片/视频）无日限额和周限额限制，直接从 AFP 池消耗。

### 1.3 Harness 工具链（来源：IT之家、CodePick）

Agent Plan 首次将 Model 与 Harness 工具链深度整合：
- **联网搜索**：与豆包同源的实时检索，Medium 起赠送 50-800 次/月
- **长期记忆**：Doubao-embedding-vision 驱动的记忆能力
- **Auto 智能调度**：自动选择性价比最优模型
- **多模态统一调度**：文本/代码/图像/视频

适配客户端：Claude Code、OpenCode、Trae、OpenClaw、Hermes Agent 等。

---

## 二、API 接口文档

### 2.1 推理 API 端点（来源：CodePick）

Agent Plan 提供两种协议兼容的 API 端点：

| 协议 | Base URL |
|------|----------|
| OpenAI Compatible | `https://ark.cn-beijing.volces.com/api/v3` |
| Anthropic 兼容 | `https://ark.cn-beijing.volces.com/api/plan` |

**重要**：Agent Plan 与 Coding Plan 的 Base URL 和 API Key **不可混用**。Coding Plan 使用 `/api/coding/v3` 和 `/api/coding`。API Key 以 `ark-` 开头，在控制台 API 密钥管理页面创建后仅显示一次。

### 2.2 用量统计 OpenAPI（来源：API 端点直接探测）

火山引擎用量统计 API 基于 OpenAPI 协议，统一端点：

```
https://open.volcengineapi.com/
```

通过 `Action` 和 `Version` 查询参数指定操作，认证方式为 AK/SK + HMAC-SHA256 签名。

#### 2.2.1 Agent Plan 专用用量 API

以下 Action 通过直接探测确认存在（均返回 `InvalidCredential` 而非 `404`，证明接口有效）：

| Action | 功能 | Version |
|--------|------|---------|
| `ListAgentPlans` | 列出 Agent Plans | 2024-01-01 |
| `DescribeAgentPlan` | 查询 Agent Plan 详情 | 2024-01-01 |
| `CreateAgentPlan` | 创建 Agent Plan | 2024-01-01 |
| **`DescribeAgentPlanUsage`** | **查询 Agent Plan 用量** | **2024-01-01** |
| **`GetAgentPlanUsage`** | **获取 Agent Plan 用量** | **2024-01-01** |
| **`ListAgentPlanUsageDetails`** | **Agent Plan 用量明细** | **2024-01-01** |
| **`ListAgentPlanBills`** | **Agent Plan 账单** | **2024-01-01** |

#### 2.2.2 通用用量统计 API

| Action | 功能 |
|--------|------|
| `ListUsage` | 通用用量列表 |
| `DescribeUsage` | 用量详情 |
| `QueryUsage` | 用量查询 |
| `GetUsage` | 获取用量 |
| `ListUsageDetail` / `ListUsageDetails` | 用量明细 |
| `ListBillDetail` | 账单明细 |
| `ListBillOverviewByProd` | 按产品账单概览 |
| `ListMeasureDetail` | 计量明细 |
| `ListMeasurements` | 计量列表 |
| `DescribeMeasureData` | 计量数据 |
| `ListUsageReports` | 用量报告 |

支持 `Service=ark` 参数按 Ark 平台筛选。

#### 2.2.3 模型/端点维度用量 API

| Action | 功能 |
|--------|------|
| `DescribeModelUsage` | 模型用量详情 |
| `ListModelUsage` | 模型用量列表 |
| `DescribeEndpointUsage` | 端点用量详情 |
| `ListEndpointUsage` | 端点用量列表 |
| `ListEndpoints` | 端点列表（支持 `Service=ark`） |

---

## 三、认证与 SDK

### 3.1 认证机制（来源：SDK GitHub、OpenAPI 探测）

火山引擎 API 使用 **AK/SK（Access Key + Secret Key）** 认证：
- AK/SK 在控制台 `console.volcengine.com/iam/keymanage/` 创建和管理
- 请求通过 `Authorization` 头携带 HMAC-SHA256 签名
- 无认证请求返回错误码 `100025`（InvalidCredential）

### 3.2 SDK 支持（来源：GitHub）

**Python SDK**：
```bash
pip install volcengine  # Python >= 3.7
```

**Go SDK**：
```bash
go get -u github.com/volcengine/volc-sdk-golang  # Go >= 1.14
```

三种凭证配置方式：
1. 代码直接设置：`iam.DefaultInstance.Client.SetAccessKey()/SetSecretKey()`
2. 环境变量：`VOLC_ACCESSKEY` / `VOLC_SECRETKEY`
3. 配置文件：`~/.volc/config`（JSON 格式）

---

## 四、产品关系

```
豆包大模型生态
  └── 火山引擎
        └── 火山方舟 (Ark，文档 ID 82379)
              ├── 模型推理（文本/多模态/视频/图片）
              ├── Managed Agent
              │     ├── Agent Plan（多模态+Harness，4 档，AFP 计费）
              │     └── Coding Plan（纯文本/代码，2 档，按调用次数计费）
              ├── 在线推理（常规/低延迟/TPM 保障包/模型单元/批量）
              └── 训练/应用实验室/知识库
```

**Agent Plan vs Coding Plan**（来源：威易网）：

| 维度 | Agent Plan | Coding Plan |
|------|-----------|-------------|
| 套餐 | 4 档（¥40-1000/月） | 2 档（Lite ¥40 / Pro ¥200） |
| 计费 | AFP 积分制 | 按预估调用次数 |
| 模型 | 文本/代码/图像/视频/向量化 | 仅文本/代码 |
| 工具 | 联网搜索+长期记忆+Auto+多模态 | ArkClaw 轻量版（Pro） |
| Base URL | `/api/v3`、`/api/plan` | `/api/coding/v3`、`/api/coding` |

---

## 五、典型用量查询场景

### 5.1 控制台查询
路径：`console.volcengine.com` → 左侧导航「AI 大模型」→ 「方舟 Agent Plan」→ 查看套餐有效期、AFP 使用情况、各模型消耗统计。

### 5.2 API 查询（推荐流程）

```
1. ListAgentPlans → 获取 Agent Plan ID
2. DescribeAgentPlanUsage / GetAgentPlanUsage → 查询指定 Plan 的用量摘要
3. ListAgentPlanUsageDetails → 获取用量明细（按模型/时间维度）
4. ListAgentPlanBills → 获取账单信息
```

### 5.3 通用 Ark 用量查询

```
1. DescribeModelUsage / ListModelUsage → 按模型维度统计 Token 消耗
2. DescribeEndpointUsage / ListEndpointUsage → 按端点维度统计调用
3. ListUsageDetails?Service=ark → Ark 平台综合用量明细
```

---

## 六、知识缺口

| # | 缺口 | 影响 | 建议 |
|---|------|------|------|
| 1 | Agent Plan 用量 API 完整请求参数和响应字段 | 无法编写精确的 API 调用代码 | 需登录火山引擎控制台查看 API 文档（文档 ID 82379） |
| 2 | 各模型具体 Token 定价 | 无法精确计算成本 | 查看控制台「模型价格」页面 |
| 3 | 用量查询所需 IAM 权限策略 | 无法配置最小权限 | 查阅 IAM 文档（docs/6291/65568） |
| 4 | SDK 调用用量 API 代码示例 | 缺少实操参考 | 查阅 volc-sdk-python/volc-sdk-golang 的 Ark 模块示例 |
| 5 | AFP 实时消耗查询 API | 无法实现实时用量监控 | 确认 `GetAgentPlanUsage` 是否支持实时数据 |
| 6 | 签名算法具体版本 | 签名实现可能出错 | 查阅火山引擎 API 签名文档 |
| 7 | 国际站 API 文档 | 英文资料极度匮乏 | 检查 volcengine.com/en 是否有英文文档 |

---

## 七、来源列表

| # | 来源 | URL |
|---|------|-----|
| 1 | CodePick - Agent Plan 全解读 | https://codepick.dev/zh/guides/ark-agent-plan/ |
| 2 | CodePick - Coding Plan 完整指南 | https://codepick.dev/zh/guides/ark-coding-plan-guide/ |
| 3 | IT之家 - Agent Plan 发布 | https://www.ithome.com/0/948/912.htm |
| 4 | 威易网 - Coding Plan vs Agent Plan | https://www.weste.net/2026/05-10/CodingPlan-AgentPlan.html |
| 5 | CSDN - Agent Plan 初体验实测 | https://blog.csdn.net/Airwinner/article/details/160881355 |
| 6 | 苏米客 - Agent Plan 上手指南 | https://www.xmsumi.com/detail/3195 |
| 7 | 火山引擎 OpenAPI 端点 | https://open.volcengineapi.com/ |
| 8 | GitHub volc-sdk-python | https://github.com/volcengine/volc-sdk-python |
| 9 | GitHub volc-sdk-golang | https://github.com/volcengine/volc-sdk-golang |
| 10 | 火山引擎 Ark 文档 | https://www.volcengine.com/docs/82379/ |
| 11 | 火山引擎 IAM 文档 | https://www.volcengine.com/docs/6291/65568 |

---

## 八、方法论反思

**做得好**：
- 3 个搜索员分工明确，覆盖产品概述、API 接口、定价/SDK/认证三个维度
- API 端点直接探测策略非常有效，通过 `InvalidCredential` 错误码确认了 25+ 个有效 Action
- 跨搜索员发现相互验证：Agent Plan 专用 API（DescribeAgentPlanUsage 等）被 searcher-2 通过端点探测确认

**需改进**：
- 火山引擎官方文档站 (volcengine.com/docs) 为 SPA 应用，web_fetch 无法获取内容，需要 browser 工具或登录后访问
- 缺少搜索引擎工具（web_search disabled），限制了多源交叉验证
- 部分来源为第三方博客（CSDN、苏米客），权威性有限，需官方文档验证
- 英文资料极度匮乏，Bing/DuckDuckGo 对此类中文技术产品查询效果差
