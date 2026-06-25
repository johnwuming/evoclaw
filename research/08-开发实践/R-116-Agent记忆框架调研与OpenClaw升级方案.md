# Agent 记忆框架行业全景与 OpenClaw 升级方案

> **报告编号**: R-116  
> **分类**: 开发实践  
> **日期**: 2026-06-25  
> **研究状态**: 基于多源网络调研，涵盖 2024-2026 年主流方案

---

## 一、问题背景

OpenClaw 当前的记忆系统存在以下痛点：

| 痛点 | 表现 | 影响 |
|------|------|------|
| 记忆写入不自动 | 依赖 MEMORY.md 手动维护、日志文件 | 用户需显式提醒 AI "记住这个" |
| 检索不精准 | 无向量检索，靠文本匹配 | "昨天的 SSH 密码"找不到 |
| 缺乏上下文关联 | 无法跨会话自动关联信息 | 每次新会话从零开始 |
| 无主动回忆机制 | 没有"想起相关记忆"的能力 | 操作信息（地址、密码、偏好）丢失 |

**核心需求**：让 AI 助手自动判断"这个信息值得记住"并无感写入，在后续对话中精准检索和主动关联。

---

## 二、Agent 记忆框架全景扫描

### 2.1 开源框架对比表

| 框架 | GitHub Stars | 记忆模型 | 自动提取 | 检索方式 | 语言/部署 | 许可证 |
|------|-------------|---------|---------|---------|----------|--------|
| **Mem0** | 59K+ ⭐ | 原子事实 + 图记忆(可选) | ✅ LLM judge 自动 | 向量 + BM25 + 实体混合 | Python/Node, Docker | Apache 2.0 |
| **Letta (MemGPT)** | 23.3K+ ⭐ | 三层(Core/Recall/Archival) | ✅ Agent 自主决定 | 向量搜索(Archival) + 上下文内(Core) | Python, REST API | Apache 2.0 |
| **Cognee** | 19.3K+ ⭐ | 知识图谱 + 向量双存储 | ✅ ECL 管线自动 | 图遍历 + 向量相似度混合 | Python, **OpenClaw 插件** | Apache 2.0 |
| **Zep** | ~5K ⭐ | 时间感知知识图谱(Graphiti) | ✅ 自动摄入 | 图查询 + 时间感知重排 | Python, REST API | Apache 2.0 |
| **LangChain Memory** | (内置) | 多种(Buffer/Summary/KG) | ❌ 需手动配置 | 取决于后端 | Python/JS | MIT |
| **LangGraph** | (内置) | Checkpoint + Store | ⚠️ 半自动 | 向量(Store) + 状态快照 | Python/JS | MIT |
| **MCP Memory Server** | ~3K ⭐ | 知识图谱(实体+关系) | ⚠️ Agent 调用触发 | 图查询 | Node.js (NPX) | MIT |
| **sqlite-vec** | ~4K ⭐ | 向量(纯SQL) | N/A(基础设施) | KNN 向量搜索 | Node/Deno/Bun/Python | MIT/Apache |

### 2.2 商业方案对比

| 方案 | 记忆机制 | 自动化程度 | 无感性 | 可用于 OpenClaw? |
|------|---------|-----------|--------|-----------------|
| **OpenAI ChatGPT Memory** | 四层架构(Saved Memory + Chat History + 文件 + Apps) | ✅ 自动+手动 | ✅ 完全无感 | ❌ 专有，无法接入 |
| **Anthropic Claude Memory Tool** | 文件系统(/memories 目录, CRUD) | ✅ 自动检查+存储 | ✅ 无需指令 | ⚠️ 仅限 Claude API |
| **Google Gemini Memory** | 长期记忆(2025年推出) | ✅ 自动 | ✅ 无感 | ❌ 专有 |

### 2.3 关键技术趋势

1. **LLM-as-Judge 自动提取**：Mem0 首创，用小模型(gpt-4o-mini)判断对话中哪些信息值得记忆，已成为行业标配
2. **混合检索**：向量语义搜索 + BM25 关键词 + 实体匹配的三路融合(Mem0 v3 / Cognee)
3. **时间感知**：Zep/Graphiti 的双时态知识图谱，维护事实的有效期(time-to-live)
4. **记忆即文件**：Claude Memory Tool 和 Letta Context Repositories 都在走向文件系统隐喻
5. **Agent 自管理**：Letta 的核心理念——LLM 通过 tool calls 自主决定何时读写记忆

---

## 三、深度评估：Top 5 候选方案

### 3.1 评分矩阵

| 维度 | Mem0 | Letta | Cognee | Zep | MCP Memory Server | sqlite-vec(自建) |
|------|------|-------|--------|-----|-------------------|-----------------|
| **自动化记忆** | 9/10 | 8/10 | 8/10 | 9/10 | 5/10 | 2/10 |
| **无感性** | 9/10 | 7/10 | 7/10 | 9/10 | 4/10 | 1/10 |
| **轻量性** | 7/10 | 4/10 | 5/10 | 3/10 | 8/10 | 10/10 |
| **OpenClaw 集成** | 8/10 | 4/10 | 9/10 | 5/10 | 9/10 | 8/10 |
| **成熟度** | 9/10 | 8/10 | 7/10 | 7/10 | 6/10 | 7/10 |
| **响应速度** | 9/10 | 6/10 | 6/10 | 7/10 | 8/10 | 10/10 |
| **总分** | **8.5** | **6.2** | **7.0** | **6.7** | **6.7** | **6.3** |

### 3.2 各方案深度分析

#### Mem0 — 最佳记忆层
- **架构**：三阶段管线（提取 → 合并 → 检索）
  - 提取：LLM 从最近 10 条消息窗口提取候选事实
  - 合并：Dense embedding + 向量库 cosine 检索相似记忆 → LLM 判断 ADD/UPDATE/DELETE/NOOP
  - 检索：Hybrid search（语义 + BM25 + 实体）~150ms，可选 reranking +200ms
- **自托管**：3 个 Docker 容器（FastAPI + PG/pgvector + Neo4j）
- **API**：REST CRUD（add/search/update/delete），支持 `user_id` 多租户隔离
- **离线**：可替换为 Ollama（bge-m3 embedding + 任意本地 LLM）
- **基准**：LOCOMO 91.6 分（+20），LongMemEval 94.8 分（+27）
- **融资**：$24M Series A（YC / Peak XV / Basis Set）
- **Node.js SDK**：✅ 官方 TypeScript SDK（`npm install mem0ai`）
- **⚠️ 劣势**：需要额外服务进程（3 个 Docker 容器），对 OpenClaw 单机部署增加复杂度

#### Cognee — 最贴合 OpenClaw 的方案
- **架构**：ECL 管线（Extract → Cognify → Load）
  - Extract：从 30+ 数据源摄入
  - Cognify：构建知识图谱（三元组抽取）+ 向量嵌入
  - Load：写入图 DB（Neo4j/FalkorDB/KuzuDB）和向量 DB（Qdrant/Weaviate）
- **🌟 关键优势**：**已有 OpenClaw 官方插件**（`@cognee/cognee-openclaw`）
- **准确率**：复杂场景 92.5%（传统 RAG 仅 60%）
- **支持本地部署**：可配合 Ollama 完全离线运行
- **⚠️ 劣势**：Python 生态为主，知识图谱构建有额外 LLM 调用开销

#### Letta (MemGPT) — 最完整的 Agent 框架
- **架构**：LLM OS 隐喻
  - Core Memory（RAM）：始终在上下文中的 persona/human blocks
  - Recall Memory（缓存）：可搜索的对话历史
  - Archival Memory（硬盘）：向量 DB 长期存储
- **特点**：LLM 自主管理记忆（通过 tool calls 决定读写），Agent-as-a-Service 持久化
- **最新**：Context Repositories（Git-backed memory）、Skill Learning
- **⚠️ 劣势**：完整 Agent 框架而非薄记忆层，与 OpenClaw 架构重叠大，集成成本高

#### Zep — 最佳时间感知方案
- **架构**：Graphiti 时间感知知识图谱引擎
  - 三层子图：Episode → Semantic Entity → Community
  - 双时态模型：维护事实的有效期
  - 多阶段重排序检索
- **基准**：DMR 94.8%（超 MemGPT 93.4%），LongMemEval 准确率 +18.5%，延迟 -90%
- **⚠️ 劣势**：依赖 Neo4j，部署重，企业导向，个人助手场景过重

#### MCP Memory Server — 最轻量集成方案
- **安装**：`npx -y @modelcontextprotocol/server-memory`
- **机制**：基于知识图谱的实体-关系存储
- **优势**：OpenClaw 原生 MCP 支持，零部署成本，直接配置即可使用
- **⚠️ 劣势**：记忆自动化程度低，需 Agent 主动调用，无自动提取机制

---

## 四、OpenClaw 升级方案

### 4.1 方案 A：快速落地（推荐 ⭐）

**技术选型**：MCP Memory Server + 增强 Prompt + sqlite-vec

**架构**：
```
┌─────────────────────────────────────────────┐
│                OpenClaw Agent               │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ MCP Memory  │  │  System Prompt 增强  │  │
│  │  Server     │  │  "每轮对话结束后,    │  │
│  │  (知识图谱)  │  │   自动检查是否有     │  │
│  │             │  │   值得记住的信息"    │  │
│  └──────┬──────┘  └──────────────────────┘  │
│         │                                   │
│  ┌──────▼──────────────────────────────┐   │
│  │  SQLite + sqlite-vec (向量搜索)     │   │
│  │  ┌─────────┐   ┌─────────────────┐  │   │
│  │  │memories │   │ memory_vectors  │  │   │
│  │  │  table  │   │   (vec0 vtab)   │  │   │
│  │  └─────────┘   └─────────────────┘  │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**实施步骤**：

1. **安装 MCP Memory Server**（1 小时）
   ```json
   // OpenClaw MCP 配置
   {
     "servers": {
       "memory": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-memory"]
       }
     }
   }
   ```

2. **System Prompt 增强**（核心改动）
   ```
   ## 记忆规则
   每轮对话结束后，自动检查是否有值得记住的信息：
   - 用户提供的凭据（密码、SSH地址、API Key）
   - 用户偏好和习惯
   - 重要的事实声明
   如果有，调用 memory tool 存储为知识图谱节点。
   对话开始时，先用 memory_search 检索相关记忆。
   ```

3. **sqlite-vec 备用向量层**（可选增强）
   ```sql
   CREATE VIRTUAL TABLE memory_vectors USING vec0(
     embedding float[768]
   );
   -- 配合 better-sqlite3 + sqlite-vec npm 包
   ```

**优点**：零额外服务、纯 Node.js 生态、当天可上线  
**缺点**：自动记忆依赖 prompt，不如 LLM judge 精准  
**适用**：快速解决"SSH 密码忘记"类痛点

---

### 4.2 方案 B：理想架构（中期升级）

**技术选型**：Mem0 自托管 + OpenClaw 自定义工具

**架构**：
```
┌──────────────────────────────────────────────────────┐
│                   OpenClaw Agent                      │
│  ┌────────────────┐  ┌─────────────────────────┐     │
│  │ 自定义工具:     │  │  Post-对话 Hook (新)   │     │
│  │ memory_add()   │  │  每轮对话后异步触发:    │     │
│  │ memory_search()│  │  1. 提取候选事实        │     │
│  │ memory_update()│  │  2. LLM judge 筛选      │     │
│  └───────┬────────┘  │  3. 调用 Mem0 API 写入  │     │
│          │           └─────────────────────────┘     │
│          │                                           │
└──────────┼───────────────────────────────────────────┘
           │ HTTP REST API
┌──────────▼───────────────────────────────────────────┐
│              Mem0 自托管服务                           │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ FastAPI  │  │ PostgreSQL   │  │   Neo4j       │  │
│  │ :8888    │  │ + pgvector   │  │  (图记忆可选)  │  │
│  │          │  │              │  │               │  │
│  │ /memories│  │ 向量索引     │  │ 实体关系       │  │
│  │ /search  │  │ + 元数据     │  │               │  │
│  └──────────┘  └──────────────┘  └───────────────┘  │
│                                                       │
│  LLM: Ollama (bge-m3 + qwen2.5) 完全离线              │
└───────────────────────────────────────────────────────┘
```

**实施步骤**：

1. **部署 Mem0 自托管**（半天）
   ```bash
   mkdir -p mem0-deploy && cd mem0-deploy
   # 创建 docker-compose.yml
   docker compose up -d  # 启动 FastAPI + PG + Neo4j
   ```

2. **配置 OpenClaw 自定义工具**（1-2 天）
   - 注册 `memory_add`、`memory_search`、`memory_update` 工具
   - 每个工具通过 HTTP 调用 Mem0 REST API
   - Agent 可在对话中自然调用

3. **添加 Post-对话 Hook**（核心创新）
   - 每轮对话结束后，异步触发记忆提取
   - 用小模型（如 GLM-4-Flash）判断"这轮对话有什么值得记住的"
   - 将提取的事实 POST 到 Mem0 API

4. **对话前记忆注入**
   - 新对话开始时，用最近话题搜索 Mem0
   - 将相关记忆作为 system prompt 的一部分注入

**优点**：完整的 LLM judge 自动提取、混合检索、成熟的记忆管理  
**缺点**：需额外 3 个 Docker 服务、有一定延迟（~150ms 检索）  
**适用**：需要高质量记忆管理的长期方案

---

### 4.3 方案 C：Cognee 插件（生态原生）

**技术选型**：`@cognee/cognee-openclaw` 插件

**架构**：
```
┌──────────────────────────────────────┐
│           OpenClaw Agent             │
│  ┌─────────────────────────────┐     │
│  │  @cognee/cognee-openclaw    │     │
│  │  (npm 插件, 原生集成)        │     │
│  └──────────┬──────────────────┘     │
│             │                        │
│  ┌──────────▼──────────────────┐     │
│  │  Cognee ECL 引擎            │     │
│  │  Extract → Cognify → Load   │     │
│  │                             │     │
│  │  ┌─────────┐ ┌───────────┐ │     │
│  │  │ 图 DB   │ │ 向量 DB   │ │     │
│  │  │(Neo4j/  │ │(Qdrant/   │ │     │
│  │  │ KuzuDB) │ │ Weaviate) │ │     │
│  │  └─────────┘ └───────────┘ │     │
│  └─────────────────────────────┘     │
└──────────────────────────────────────┘
```

**优点**：已有 OpenClaw 官方插件、知识图谱+向量双引擎、92.5% 准确率  
**缺点**：Python 生态为主、知识图谱构建有额外 LLM 开销、社区较新  
**适用**：希望用最原生的方案，且需要复杂关系推理

---

## 五、场景验证：SSH 地址密码记忆

以"用户给过群晖 NAS 的 SSH 地址密码"为例：

| 步骤 | 方案 A (MCP) | 方案 B (Mem0) | 方案 C (Cognee) |
|------|-------------|---------------|-----------------|
| **记忆写入** | Agent 识别"SSH地址"关键词 → 调用 memory tool 存储实体 | LLM judge 从对话提取 `<事实: 群晖SSH地址=192.168.x.x, 密码=xxx>` → 自动写入 Mem0 | ECL 管线提取实体(群晖NAS)和关系(SSH地址→密码) → 写入知识图谱 |
| **记忆检索** | 用户说"连一下NAS" → memory_search "NAS SSH" | 用户说"连一下NAS" → Mem0 search "群晖 SSH 地址" | 用户说"连一下NAS" → 图查询(群晖→SSH→地址) + 向量搜索 |
| **精度** | 中等（依赖 prompt 触发） | 高（LLM judge 精准提取 + 混合检索） | 高（图谱关系推理强） |
| **延迟** | <50ms | ~150ms | ~300-500ms（图构建开销） |
| **自动化** | ⚠️ 需 prompt 引导 | ✅ 完全自动 | ✅ 完全自动 |

---

## 六、推荐路径

### 第一阶段（1 周内）：方案 A 快速落地
1. 安装 MCP Memory Server
2. 增强 System Prompt 加入记忆规则
3. 解决 80% 的"忘记"痛点

### 第二阶段（1 个月内）：方案 B 理想架构
1. 部署 Mem0 自托管
2. 开发 OpenClaw 自定义工具（memory_add/search/update）
3. 实现 Post-对话 Hook 自动记忆提取
4. 实现 Pre-对话记忆注入

### 可选：方案 C 混合
- 用 Cognee 插件增强复杂关系推理
- 与 Mem0 并行：Mem0 做事实记忆，Cognee 做关系图谱

---

## 七、技术细节

### 7.1 Mem0 REST API 速查

```bash
# 添加记忆
curl -X POST http://localhost:8888/memories \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"我的群晖NAS SSH地址是192.168.1.100，端口22，用户名admin，密码MyPass123"}],"user_id":"user-001"}'

# 搜索记忆
curl -X POST http://localhost:8888/memories/search \
  -H "Content-Type: application/json" \
  -d '{"query":"NAS SSH 地址","user_id":"user-001"}'

# 获取所有记忆
curl http://localhost:8888/memories?user_id=user-001
```

### 7.2 sqlite-vec Node.js 示例

```javascript
import { DatabaseSync } from "node:sqlite";
import * as sqliteVec from "sqlite-vec";

const db = new DatabaseSync(":memory:", { allowExtension: true });
sqliteVec.load(db);

// 创建向量表
db.exec(`CREATE VIRTUAL TABLE memory_vectors USING vec0(
  embedding float[768]
)`);

// 插入向量
const stmt = db.prepare(
  "INSERT INTO memory_vectors(rowid, embedding) VALUES (?, ?)"
);
stmt.run(1, new Uint8Array(embedding.buffer));

// KNN 搜索
const results = db.prepare(
  `SELECT rowid, distance FROM memory_vectors
   WHERE embedding MATCH ?
   ORDER BY distance LIMIT 5`
).get(queryEmbedding);
```

### 7.3 OpenClaw 自定义工具模板

```typescript
// tools/memory.ts
export const memoryTools = [
  {
    name: "memory_add",
    description: "存储一条记忆。当用户提供了重要信息（地址、密码、偏好等）时调用。",
    parameters: {
      type: "object",
      properties: {
        content: { type: "string", description: "要记忆的内容" },
        category: { type: "string", enum: ["credential", "preference", "fact", "context"] }
      },
      required: ["content"]
    },
    handler: async ({ content, category }) => {
      const res = await fetch("http://localhost:8888/memories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content }],
          user_id: "openclaw-user"
        })
      });
      return await res.json();
    }
  },
  {
    name: "memory_search",
    description: "搜索记忆。在需要回忆之前的信息时调用。",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string", description: "搜索查询" }
      },
      required: ["query"]
    },
    handler: async ({ query }) => {
      const res = await fetch("http://localhost:8888/memories/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, user_id: "openclaw-user" })
      });
      return await res.json();
    }
  }
];
```

---

## 八、知识缺口

| 缺口 | 说明 | 影响等级 |
|------|------|---------|
| LangGraph Checkpoint 细节 | 最新 checkpoint + store 机制未深入 | 低（非首选方案） |
| A-MEM 实际可用性 | 学术论文为主，生产实现有限 | 低 |
| Google Gemini Memory | 实现细节未公开 | 低（不可接入） |
| Mem0 大规模性能 | 百万级记忆下的表现未知 | 中 |
| 各框架第三方独立评测 | 各家基准测试自说自话，缺乏中立对比 | 中 |

---

## 九、方法论反思

**做得好的方面**：
- 覆盖了主流开源 + 商业方案共 10+ 个框架
- 从架构、自动化、部署、集成多维度评估
- 给出了可操作的分阶段升级路径

**需改进的方面**：
- 搜索员因 rate limit 多次失败，部分查询由主管手动补充
- 缺乏各框架的实际部署测试（仅基于文档调研）
- Cognee OpenClaw 插件的具体能力未深入测试

---

## 十、来源列表

| 来源 | URL |
|------|-----|
| Mem0 GitHub | https://github.com/mem0ai/mem0 |
| Mem0 论文 | https://arxiv.org/abs/2504.19413 |
| Mem0 自托管文档 | https://docs.mem0.ai/open-source/overview |
| Mem0 Docker 部署指南 | https://mem0.ai/blog/self-host-mem0-docker |
| Letta GitHub | https://github.com/letta-ai/letta |
| Letta 官方文档 | https://docs.letta.com |
| Letta 研究博客 | https://www.letta.com/blog-categories/research |
| Zep 论文 (arXiv) | https://arxiv.org/abs/2501.13956 |
| Graphiti/Neo4j 博客 | https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/ |
| Cognee GitHub | https://github.com/topoteretes/cognee |
| Cognee OpenClaw 插件 | https://www.npmjs.com/package/@cognee/cognee-openclaw |
| OpenAI Memory FAQ | https://help.openai.com/en/articles/8590148-memory-faq |
| OpenAI Memory 公告 | https://openai.com/index/memory-and-new-controls-for-chatgpt/ |
| Claude Memory Tool 文档 | https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool |
| Anthropic Context Management | https://claude.com/blog/context-management |
| MCP Memory Server | https://mcpservers.org/servers/modelcontextprotocol/memory |
| sqlite-vec | https://alexgarcia.xyz/sqlite-vec |
| LanceDB GitHub | https://github.com/lancedb/lancedb |
| LangChain Memory | https://python.langchain.com/docs/modules/memory/ |
| Letta 研究分析 | https://github.com/Lin-Guanguo/llm-memory-research/blob/main/letta.research.md |
| Letta Commonplace 分析 | https://zby.github.io/commonplace/sources/letta-memgpt-stateful-agents |
| TechCrunch Mem0 融资 | https://techcrunch.com/2025/10/28/mem0-raises-24m-from-yc-peak-xv-and-basis-set-to-build-the-memory-layer-for-ai-apps/ |
