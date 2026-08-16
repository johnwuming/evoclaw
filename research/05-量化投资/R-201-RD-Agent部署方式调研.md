# R-201 RD-Agent 部署方式调研（含 HP 全宿主机实战建议）

> 调研日期：2026-08-12 ｜ 对象：微软 RD-Agent（因子进化框架，依赖 qlib）
> 目标机器：HP 电脑 Ubuntu / 15G 内存 / 无 GPU / conda env `rdagent4qlib`
> 范围：官方标准做法 + GitHub Issue/社区实战 + 针对本机（全市场 daily_pv.h5、DeepSeek/火山/智谱 LLM）的落地建议

---

## 0. TL;DR（结论速览）

| 问题 | 结论 | 关键证据 |
|---|---|---|
| 部署方式 | **官方主推 `pip install rdagent` + Docker 执行**，但 Qlib 场景**代码层面默认 `conda`（`MODEL_COSTEER_ENV_TYPE=conda`）**；无 GPU / 15G 内存机器**强烈建议用 conda 模式，放弃 Docker** | 官方文档 / `rdagent/utils/env.py` |
| CoSTEER 执行环境 | factor.py 用**当前激活的 conda 环境**（`CONDA_DEFAULT_ENV`）子进程执行，默认超时 3600s；回测用 `QlibCondaEnv`（默认 env 名正好叫 **`rdagent4qlib`**）；数据必须放在 `git_ignore_folder/factor_implementation_source_data(_debug)/` 两个目录，目录不存在会**自动触发 Docker 生成数据**（这是路径 bug 的来源） | `factor_coder/config.py`、`qlib/experiment/utils.py` |
| 输出格式错误 | **主要是 LLM 质量问题 + 数据 schema 不匹配**，不是单方面原因。`_normalize_factor_index` 强制要求 `datetime`×`instrument` 两级 MultiIndex；火山 API 返回大写 `True/False` 导致 JSON 解析失败是另一大坑（GitHub #916，新版已修复） | `qlib/developer/utils.py`、#678、#916 |
| 长流程稳定性 | 流式 `CHAT_STREAM=True` 默认开 → 不稳定供应商会挂起，**应关流式**；ML 因子按“每股票每天训练”会跑几小时（#1407，新版已加静态护栏 #1410）；进程静默退出多为 OOM/超时 | `llm_conf.py`、#1407、#1410 |
| LLM 后端 | 默认 **LiteLLM**（`CHAT_MODEL/EMBEDDING_MODEL` 直传 litellm）；官方给出 **DeepSeek + SiliconFlow(bge-m3)** 完整配置；智谱走 `zai/`(zhipu) provider；GLM-4-Flash 免费；火山 coding plan 不推荐用于 RD-Agent | 官方文档、litellm docs |
| qlib 数据格式 | `daily_pv.h5`：h5 key=`data`，`MultiIndex(datetime,instrument)`，列 `$open/$close/$high/$low/$volume/$factor`（带 `$` 前缀）；**回测还需要 `~/.qlib/qlib_data/cn_data` 的 qlib bin 数据**（calendar/instruments/features，默认 csi300） | `factor_data_template/`、#1335、qlib 文档 |

**一句话建议**：升级 RD-Agent 到最新版 → 用 conda 模式（弃 Docker）→ 用 DeepSeek 官方 API（关流式）→ 数据目录放对、建 debug 子集 → 装好 qlib bin 数据 → `health_check` 通过后再跑 `fin_factor`，并把 `evolving_n` 先调小验证。

---

## 1. Q1：官方推荐的部署方式（Docker / Conda / 本地）及各有什么坑

### 1.1 官方标准做法
- **安装**：纯用户 `pip install rdagent`（Python 3.10/3.11，官方 CI 实测版本；Linux only，Windows/macOS 需 Docker/WSL2/虚拟机）。（来源：[官方安装文档](https://rdagent.readthedocs.io/en/stable/installation_and_configuration.html)、[dev.to RD-Agent 教程](https://dev.to/henry_lin_3ac6363747f45b4/rd-agent-jiao-cheng-di-zhang-ji-chu-ru-men-ben-jiao-cheng-wei-jing-quan-bu-yan-zheng-jin-gong-can-kao--30kd)）
- **执行环境**：官方文档明确 “RDAgent is designed…primarily using **Docker** for code execution… Users must ensure Docker is installed before attempting most scenarios”，并要求当前用户**无 sudo 跑 docker**（`docker run hello-world` 验证）。
- **关键**：**Qlib 场景（fin_factor/fin_model/fin_quant）在代码层面默认 `env_type="conda"`**（`rdagent/components/coder/model_coder/conf.py` 中 `env_type: str = "conda"`，env var 为 `MODEL_COSTEER_ENV_TYPE`）。`QlibFBWorkspace.execute()` 按 `MODEL_COSTEER_SETTINGS.env_type` 分流：`docker`→`QTDockerEnv`，`conda`→`QlibCondaEnv`（`rdagent/scenarios/qlib/experiment/workspace.py`）。
- 因此：**官方文档强调 Docker（文档优先、隔离性好），但 Qlib 场景的代码默认值已经是 conda，且社区大量用户直接用 conda 本地跑**。对无 GPU 小内存机器，conda 模式是唯一现实选择。

### 1.2 三种方式的坑（社区实证）
**Docker 模式坑（我们已踩，建议直接放弃）**
1. **镜像重**：Qlib 场景 Dockerfile 基于 `pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime`（约 6–8GB），还要 clone 并 `pip install -e` 固定 commit 的 qlib（`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`）。无 GPU 机器纯浪费。（来源：`rdagent/scenarios/qlib/docker/Dockerfile`）
2. **已知路径/挂载 bug**：
   - `get_factor_env()/get_model_env()` 无条件用空 dict 覆盖 `extra_volumes`，把默认的 `~/.qlib/ → /root/.qlib/` 挂载弄丢，导致 `QTDockerEnv.prepare()` 抛 `StopIteration`，Docker 模式 factor/model 直接起不来 → **issue #1428 / PR #1435（2026-06 才修）**。
   - `normalize_volumes()` 把容器路径也当宿主机路径处理（Windows 下变成 `C:\workspace\qlib_workspace` → `too many colons` 挂载被拒）→ **issue #1064 / PR #1418**。
   - workspace 固定挂到容器 `/workspace/qlib_workspace/`，数据如果只在宿主机 git_ignore_folder 而不在挂载内，因子代码在容器里读不到 `daily_pv.h5`。
3. **数据生成也会强依赖 Docker**：`get_data_folder_intro()` 发现 `factor_implementation_source_data` 或 `_debug` 目录**任一不存在**时，会调用 `generate_data_folder_from_qlib()`，而它**硬编码 `QTDockerEnv()`**（`rdagent/scenarios/qlib/experiment/utils.py`）——也就是说即便你配置了 conda 模式，只要数据目录没建好就会去拉 Docker 镜像，从而踩上面 1/2 的坑。**这就是“原版有路径 bug”最常见的触发路径。**

**Conda 模式坑**
- `QlibCondaEnv.prepare()` 只在 env **不存在**时自动创建（装 python3.10 + qlib@固定commit + catboost/xgboost/tables/torch）；若 env 已存在则不检查依赖版本。**我们的 `rdagent4qlib` 正好是默认名**（`QlibCondaConf.conda_env_name="rdagent4qlib"`），但要人工确认 qlib 版本与 RD-Agent 期望的固定 commit 对齐，否则回测行为可能不一致。
- conda 模式本质是 `LocalEnv` 子进程：`qrun conf.yaml` / `python factor.py` 直接跑在宿主机，**没有隔离**，库冲突/环境漂移要自己管理。
- 因子实现阶段的 `python_bin` 默认就是 `python`，即**随运行 `rdagent fin_factor` 时激活的那个 conda 环境**（`get_factor_env()` 取 `CONDA_DEFAULT_ENV`），所以启动脚本里 `activate rdagent4qlib` 这一行非常关键。

**本地/直接跑坑**
- 无隔离，依赖装在同一个 env；对纯因子实验（不开 docker）是最省事路径，等同于 conda 模式。

---

## 2. Q2：因子执行环境（CoSTEER evaluator 执行 factor.py）如何正确配置本地 conda 环境

RD-Agent 因子流水线有两个执行点，分别说明：

### 2.1 因子实现执行（CoSTEER 编码评估阶段，跑 `factor.py`）
- 执行器：`FactorFBWorkspace.execute()`（`rdagent/components/coder/factor_coder/factor.py`）。
- 机制：把源数据目录里的文件**软链接/复制到每个因子工作区** → `subprocess.check_output(f"{python_bin} factor.py", cwd=workspace, timeout=file_based_execution_timeout)` → 读 `result.h5`（key=`data`）。
- 配置（env 前缀 `FACTOR_COSTEER_`，见 `factor_coder/config.py` 与 [docs 配置参考](https://rdagent.readthedocs.io/en/latest/scens/quant_agent_fin.html)）：
  - `FACTOR_COSTEER_DATA_FOLDER`（默认 `git_ignore_folder/factor_implementation_source_data`）
  - `FACTOR_COSTEER_DATA_FOLDER_DEBUG`（默认 `.../factor_implementation_source_data_debug`）
  - `FACTOR_COSTEER_FILE_BASED_EXECUTION_TIMEOUT`（默认 **3600s**）
  - `FACTOR_COSTEER_PYTHON_BIN`（默认 `python` → 当前激活的 conda env）
- **正确姿势**：
  1. 在**运行 `rdagent fin_factor` 的项目根目录**下建好**两个**数据目录（`data_folder` 与 `data_folder_debug` 都必须存在），各放一个 `daily_pv.h5` + `README.md`（README 可复制 `rdagent/scenarios/qlib/experiment/factor_data_template/README.md`）。目录不存在 → 触发 Docker 自动生成（见 Q1）。
  2. `daily_pv.h5` 用符号链接即可（`FactorFBWorkspace` 会 `link_all_files_in_folder_to_workspace` 把文件链到子工作区），但**目录本身必须真实存在**且 h5 可读、schema 正确（见 Q6）。
  3. 调试目录放**小样本**（官方默认 debug 数据是 2018–2019 两年 + 前 100 只股票 `daily_pv_debug.h5`）。在 15G 内存机器上，CoSTEER 每轮迭代都用全市场 1400 万行数据算因子会非常慢且易 OOM，**务必给 `_debug` 目录建子集**。
  4. 保证 `run_rdagent.sh` 里 `activate rdagent4qlib` 生效（`python_bin=python` 依赖它）。

### 2.2 回测执行（runner 阶段，跑 `qrun conf*.yaml`）
- `QlibFBWorkspace.execute()` 按 `MODEL_COSTEER_ENV_TYPE` 选环境：
  - `conda` → `QlibCondaEnv`（env 名 `rdagent4qlib`），在**当前激活的 conda env** 里跑 `qrun conf.yaml` + `python read_exp_res.py`（`rdagent/scenarios/qlib/experiment/workspace.py`）。
  - 该环境需要：qlib、lightgbm（LGBModel 默认模型）、pyarrow（读 `combined_factors_df.parquet`）、tables、catboost/xgboost/torch。
- 每个 `qrun` 命令外层有 `timeout --kill-after=10 {running_timeout_period}` 兜底（Local/Docker 通用，`Env.run()`，默认 3600s，`RETRY_COUNT` 默认 5、`RETRY_WAIT_SECONDS` 10）。
- **结论**：把 `MODEL_COSTEER_ENV_TYPE=conda` 写进 `.env`，即可完全绕开 Docker 路径/挂载问题；执行环境就是你的 `rdagent4qlib`。

---

## 3. Q3：因子输出格式反复报“输出格式错误”（空 DataFrame / 简单 Index 而非 MultiIndex）

### 3.1 框架到底要求什么格式
- 官方要求（R&D-Agent(Q) 论文 [arXiv:2505.15155](https://arxiv.org/html/2505.15155v2) 的 Output 描述）：**“Save computed factor to result.h5 as a pandas DataFrame with index `[datetime, instrument]` and one column named by the factor.”**
- 代码强制校验在 `rdagent/scenarios/qlib/developer/utils.py` 的 `_normalize_factor_index()`：
  - `df` 为空 → 丢弃；
  - **index.names 必须同时包含 `datetime` 和 `instrument`**（`"datetime" not in index_names → return None`；缺 `instrument` → warning “Skip factor dataframe because index misses 'instrument'”）；
  - 只允许 2 级；出现重复 level 名会尝试合并，歧义则丢弃；
  - 出现 1 分钟频率数据（`pd.Timedelta(minutes=1) in time_diff`）→ 丢弃（分钟级数据不被接受）。
- 也就是说你看到的“空 DataFrame / 简单 Index”报错，绝大多数来自这里被 `_process_message_and_df` 拒收，日志形如：
  `Factor data from {source} is not generated because of {message}. index_info=index_type=RangeIndex/Index, nlevels=1, names=[None]`。

### 3.2 是 LLM 质量问题还是环境/数据问题？（社区实证：两者都有）
- **LLM 质量（主因，占比高）**：模型生成的 `factor.py` 常见三类病：
  1. `.unstack()` 后直接 `.to_frame()` 忘了 `.stack()` / 忘了 `set_index(['datetime','instrument'])` → 返回普通 Index；
  2. `reset_index()` 后多带了一列 instrument 造成 **3 级 MultiIndex** → concat 时 `AssertionError: Length of new_levels (3) must be <= self.nlevels (2)` → **issue #678**；
  3. 逻辑在空切片上执行 → 空 DataFrame。
- **数据 schema 不匹配（次因，很常见）**：如果我们的 `daily_pv.h5` 的 index **不是**两级且**名字不是 `datetime`/`instrument`**（例如名字叫 `date`/`code`、或单级），模型照样例写的 `sort_index(level=['datetime','instrument'])` / `stack()` 会失败或产出错误结构 → 反被当成“模型输出格式错误”。**先把数据格式按 Q6 校正**，能显著减少这类报错。
- **火山 API 的 JSON 大写布尔（我们场景的独立元凶）**：火山/部分国产端点返回 `True/False`（Python 风格）而不是 JSON 的 `true/false`，导致 `json.loads` 抛 `Expecting value: line xx column xx`——这正是“格式反复出错”的一种表现 → **issue #916**。新版本 `JSONParser._fix_python_booleans` 已自动修复（`rdagent/oai/backend/base.py`）。**务必升级到包含该修复的版本。**

### 3.3 社区怎么解决
1. **升级 RD-Agent 到最新版**（#916 大写布尔、#1410 ML 因子护栏、#1435 挂载修复、`_normalize_factor_index` 更强的容错都在新版）。
2. **数据格式先做对**（Q6），让模型的“标准写法”能直接跑通。
3. **提示词侧**：新版在 `qlib_factor_strategy` 里加了“禁止 per-instrument/per-day 重训模型、用 panel 一次 fit + 批量 predict 或 groupby/rolling/apply 向量化”的显式规则（PR #1410）；我们若要彻底稳住，也可在本地 `prompts.yaml` 里追加一条“输出必须是 index=[datetime,instrument] 的 2 级 MultiIndex、单列、列名=因子名、写入 result.h5(key='data')”的硬约束。
4. **减小迭代成本**：CoSTEER 每轮对 `_debug` 子集执行 factor.py，先把 debug 数据做成 100 只/2 年的子集，格式问题能快速暴露且不烧钱（很多用户用此法定位“格式错误”到底是模型问题还是数据问题）。

---

## 4. Q4：长流程（10 轮进化）稳定性：流式挂起、静默退出

### 4.1 流式 LLM 调用挂起
- RD-Agent **默认 `chat_stream=True`**（`rdagent/oai/llm_conf.py`），经 litellm 流式返回；对不稳定供应商（尤其国产 long-context / 推理模型）流式长调用容易挂起或中断。
- **规避**：`.env` 里 `CHAT_STREAM=False`（关流式），并配合 `MAX_RETRY`（默认 10）、`RETRY_WAIT_SECONDS`（默认 1，官方 `.env.example` 建议 20）、`TIMEOUT_FAIL_LIMIT`（默认 10）。
- 底层对 `finish_reason=="length"` 会自动续写（`_create_chat_completion_auto_continue`，最多 `try_n=6` 次续写），长代码不会因为一次截断就废掉；`REASONING_THINK_RM=True` 用于去掉推理模型的 `thinking/response` 标签干扰（官方 DeepSeek 配置文档）。

### 4.2 进程静默退出 / 跑几小时
- **ML 因子是最大杀手**：LLM 常生成“每只股票、每天重训 LSTM/RandomForest/XGB”的代码，复杂度 O(股票×天数×epoch)，在 5000+ 股票 / 1400 万行数据上**可达上亿次训练迭代，跑数小时、100% CPU**，随后被 `file_based_execution_timeout`(3600s) 或 OOM 杀掉，看起来像“静默退出” → **issue #1407**；官方/社区已通过 AST 静态检测 `detect_per_instrument_training_antipattern` + 提示词加固修复（**PR #1410**）。**升级版本可规避；老版本可在 prompt 里禁止该写法，或用简单（非 ML）因子起步。**
- **OOM（15G 内存尤其要防）**：单因子 df 在 1300 万行时约 **615–665MB**（issue #678 实测），`process_factor_data` 会把多个因子 concat 成 `combined_factors_df.parquet`，再交给 qrun 回测（还要读 qlib bin + Alpha158 特征 + LGBM 训练），峰值内存很容易超 15G。规避：
  - `RD_AGENT_SETTINGS.multi_proc_n=1`（`MULTI_PROC_N=1`）避免并行因子同时占内存；
  - debug 阶段用子集数据；
  - 若坚持全市场，考虑把回测 universe 从 csi300 之外的部分裁剪（见 Q6）。
- **超时与重试**：qrun 命令默认 `running_timeout_period=3600s`，超时会 `timeout --kill-after=10` 杀掉并记录；`retry_count=5`。`FACTOR_COSTEER_FILE_BASED_EXECUTION_TIMEOUT` 单独控制 factor.py（默认 3600s）。可根据数据量调小让“坏因子”快速失败而不是挂住。

### 4.3 日志与检查点
- 官方提供 `rdagent health_check`（真实发一次 completion + embedding，验证 .env 端到端可用），**先跑通再开长任务**。
- 用 `nohup ... > log 2>&1 &` 后台跑，`tail -f` 观察；每次实验/因子都会写进 `git_ignore_folder/RD-Agent_workspace/`，可回看某个因子到底是执行失败还是格式失败。
- 建议：首次把 `evolving_n` 调小（如 3–5）验证全链路，再放 10 轮；10 轮在无 GPU 机器上按经验数小时起步（每次 qrun 回测 + 多轮 CoSTEER），做好心理预期。

---

## 5. Q5：LLM 后端选择（LiteLLM/OpenAI/国产模型）

### 5.1 RD-Agent 官方支持哪些后端
- **默认/推荐：LiteLLM**（`BACKEND=rdagent.oai.backend.LiteLLMAPIBackend`）。`CHAT_MODEL`、`EMBEDDING_MODEL` 直接传给 `litellm.completion/embedding`，所以**任何 litellm 支持的 provider 都能用**：openai、azure/azure-openai、deepseek、anthropic、gemini、zhipu(Z.AI)、siliconflow、moonshot 等（官方文档 + dev.to 教程的 LiteLLM 供应商表）。
- 配置要点（[官方安装配置文档](https://rdagent.readthedocs.io/en/stable/installation_and_configuration.html)）：
  - 统一 base：`CHAT_MODEL=gpt-4o` + `EMBEDDING_MODEL=text-embedding-3-small` + `OPENAI_API_BASE` + `OPENAI_API_KEY`；
  - 分离：chat 走 `OPENAI_API_*`，embedding 走 **`litellm_proxy/` 前缀**（如 `EMBEDDING_MODEL=litellm_proxy/BAAI/bge-large-en-v1.5`，配 `LITELLM_PROXY_API_KEY/BASE`）。
  - 推理模型：`REASONING_THINK_RM=True`；DeepSeek 等不支持 response schema 的模型会自动忽略 `response_format` 走 `json_target_type` 校验路径（日志可见 “does not support response schema, ignoring response_format argument”，正常现象）。
- 智谱：litellm 支持 Z.AI/Zhipu（`zai/glm-4.7` 等，[litellm Z.AI 文档](https://docs.litellm.ai/docs/providers/zai)）；GLM-4-Flash / GLM-4.7-Flash 免费。
- Azure OpenAI：官方给出 `azure/<deployment>` + `AZURE_API_BASE/KEY/VERSION` 配置示例。

### 5.2 我们试过的三个后端为什么出问题（社区证据）
1. **DeepSeek（余额不足）**：官方已把 DeepSeek 列为“experimental support / cost-effective”推荐；**钱不够不是后端问题，是预算问题**（DeepSeek 很便宜：`deepseek-chat`(V3.x) 输入约 $0.14–0.56/百万 token、输出约 $1 量级，官方定价见 [api-docs.deepseek.com/pricing](https://api-docs.deepseek.com/quick_start/pricing/)）。
2. **火山 coding plan deepseek-v4-flash（流式不稳 + 格式反复出错）**：#916 已证实火山端点返回大写 `True/False` 破坏 JSON；v4-flash 是推理/流式模型，长调用更易中断。**不建议把 coding plan 的对话接口直接塞给 RD-Agent 做结构化 JSON 任务**。
3. **智谱 glm-4-flash（重试 10 次失败）**：多为网络/端点/模型不支持 `response_format` 等原因；先跑 `rdagent health_check` 定位，再考虑换 `zai/glm-4.7-flash` 这类新免费模型（智谱开放平台），并 `CHAT_STREAM=False`。

### 5.3 对“中文 A 股因子生成”的模型推荐（成本/质量权衡）
- **首选（性价比）**：`deepseek/deepseek-chat`（当前 V3.x/V4 系列，代码强、便宜、官方示例配置完整）+ `litellm_proxy/BAAI/bge-m3`（SiliconFlow）做 embedding。
- **次选（免费/极低成本）**：`zai/glm-4.7-flash`（或 glm-4-flash，智谱免费档）做 chat；embedding 用 SiliconFlow 免费额度 bge 系列。
- **要求更稳的格式输出**：可用响应 schema 支持较好的模型（如 OpenAI gpt-4o / 国内兼容 `json_object` 的模型），或保持 JSON 解析修复 + `CHAT_STREAM=False` 组合拳。
- 不建议：火山 coding plan 对话流直接接 RD-Agent；DeepSeek-reasoner 需 `REASONING_THINK_RM=True` 且延迟高。

---

## 6. Q6：qlib 数据格式要求 & A 股数据如何准备

### 6.1 `daily_pv.h5`（因子实现源数据）的硬性要求
依据 `rdagent/scenarios/qlib/experiment/factor_data_template/`（README.md + generate.py）：
- **HDF5 key 恒为 `data`**（`pd.read_hdf("daily_pv.h5", key="data")`）。
- **Index = 2 级 MultiIndex，级名 `datetime` × `instrument`**（官方用 `D.features(...).swaplevel().sort_index()` 生成，即 (datetime, instrument)）。
- **列名带 `$` 前缀**：`$open / $close / $high / $low / $volume / $factor`（qlib 约定），LLM 样例代码里会写 `df['$close']`。
- 官方全量版 `daily_pv_all.h5`：2008-12-29 起全市场；调试版 `daily_pv_debug.h5`：2018–2019 两年 + 前 100 只。
- 验证脚本（可放到部署步骤里跑一遍）：
```python
import pandas as pd
df = pd.read_hdf("daily_pv.h5", key="data")
assert isinstance(df.index, pd.MultiIndex), df.index
assert list(df.index.names) == ["datetime", "instrument"], df.index.names
print(df.columns.tolist())  # 应含 $open $close $high $low $volume $factor
```

### 6.2 回测需要的 qlib bin 数据（易被忽略的硬前提）
- `fin_factor/fin_model/fin_quant` 的回测 `qrun conf*.yaml` 里：
  - `provider_uri: "~/.qlib/qlib_data/cn_data"`（qlib 原生 bin 数据）；
  - `market: csi300`、`benchmark: SH000300`（**默认是沪深300，不是全市场**）；
  - 特征用 `Alpha158DL` + `StaticDataLoader` 读 `combined_factors_df.parquet`；LGBModel 训练；train 2008-01-01~2014-12-31 / valid 2015-2016 / test 2017-2020-08-01（`conf_baseline.yaml` / `conf_combined_factors.yaml`）。
- **issue #1335** 明确指出：官方文档没有清晰说明“需要先下载 qlib 数据”，导致很多用户第一步就失败。准备方式（qlib 官方文档 [Data Layer](https://qlib.readthedocs.io/en/latest/component/data.html)）：
  - 方式 A（直接下载现成 cn_data）：`python scripts/get_data.py qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn`（A 股 1d 数据，含 calendars/instruments/features）；
  - 方式 B（用自己的 CSV）：每只股票一个 CSV（如 `SH600000.csv`，列含 date/open/high/low/close/volume/factor），再用 qlib 的 `scripts/dump_bin.py` 转成 .bin 格式，并补 calendars、instruments、features 目录。
- **注意两层数据的关系**：`daily_pv.h5`（因子实现用）理论上可从 qlib bin 数据用 `generate.py` 生成，但也可以直接用你的市场数据；**回测层必须另有 `~/.qlib/qlib_data/cn_data`**。我们目前只有 `daily_pv.h5`，很可能缺回测层数据——这是“跑到 qrun 就失败/静默退出”的高频原因。

### 6.3 A 股社区实战
- 社区普遍做法：先 `get_data.py` 拉 cn_data（或 dump_bin 自转），再自行用因子模板 `generate.py` 出一份 `daily_pv.h5` 放进 `factor_implementation_source_data`，最后改 `conf*.yaml` 的 `market`/`benchmark`/日期段匹配自己的数据（默认 csi300 与“全市场 5000+”不一致时，回测 universe 仍是 csi300，因子在 csi300 上才有意义）。
- qlib 官方只对中/美市场给出 dump_bin 指导；非中国市场需自定义（官方文档亦承认，见 zread “问题与反馈”一节）。

---

## 7. 针对 HP 场景的最优部署方案（可执行步骤）

前置条件确认：Ubuntu / 15G 内存 / 无 GPU；conda env `rdagent4qlib`（qlib/lightgbm/rdagent CLI 已装）；`daily_pv.h5`（全市场 1413 万行，5000+ 股票）。

### Step 0：升级 RD-Agent（最高优先级，一次解决多个已知 bug）
```bash
cd ~/RD-Agent            # 你的 RD-Agent 项目根目录（若从 git 安装）
git pull
pip install -e . --no-deps   # 或直接: pip install -U rdagent
rdagent --version
```
> 修复项：火山大写布尔 JSON 解析（#916）、ML 因子 per-stock 重训护栏（#1410）、Docker extra_volumes 覆盖（#1435）、挂载路径（#1418）、factor index 校验增强（`_normalize_factor_index`）。

### Step 1：`.env`（项目根目录）——conda 模式 + DeepSeek + SiliconFlow + 关流式
```bash
cat > ~/RD-Agent/.env <<'EOF'
# ---- LLM（LiteLLM 后端）----
BACKEND=rdagent.oai.backend.LiteLLMAPIBackend
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=sk-your-deepseek-key
EMBEDDING_MODEL=litellm_proxy/BAAI/bge-m3
LITELLM_PROXY_API_KEY=sk-your-siliconflow-key
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
# 若用推理模型(deepseek-reasoner 等)则打开：
# REASONING_THINK_RM=True

# ---- 稳定性 ----
CHAT_STREAM=False          # 关键：关流式，避免长调用挂起
MAX_RETRY=6
RETRY_WAIT_SECONDS=20
TIMEOUT_FAIL_LIMIT=3

# ---- 执行环境：本地 conda，不用 Docker ----
MODEL_COSTEER_ENV_TYPE=conda
FACTOR_COSTEER_FILE_BASED_EXECUTION_TIMEOUT=1800
MULTI_PROC_N=1             # 15G 内存别并行

# ---- 数据/回测参数（按需覆盖，env 前缀见 docs）----
# QLIB_FACTOR_EVOLVING_N=3   # 首次先跑 3 轮验证
EOF
```

### Step 2：数据目录（两个目录必须都存在，否则触发 Docker 生成）
```bash
cd ~/RD-Agent
mkdir -p git_ignore_folder/factor_implementation_source_data
mkdir -p git_ignore_folder/factor_implementation_source_data_debug

# 全量数据 → 正式目录（符号链接即可）
ln -sf /绝对路径/daily_pv.h5  git_ignore_folder/factor_implementation_source_data/daily_pv.h5
cp rdagent/scenarios/qlib/experiment/factor_data_template/README.md \
   git_ignore_folder/factor_implementation_source_data/README.md

# 调试子集（100 只 / 2018-2019）→ 调试目录，CoSTEER 迭代用它
python - <<'PY'
import pandas as pd
src = "git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
df = pd.read_hdf(src, key="data")
assert isinstance(df.index, pd.MultiIndex) and list(df.index.names)==["datetime","instrument"]
sub = df.loc[pd.IndexSlice["2018-01-01":"2019-12-31",
                          df.index.get_level_values("instrument").unique()[:100]]]
sub.to_hdf("git_ignore_folder/factor_implementation_source_data_debug/daily_pv.h5", key="data", mode="w")
print("debug subset:", sub.shape)
PY
```

### Step 3：回测层 qlib bin 数据（缺失是 qrun 失败/静默退出的高发原因，issue #1335）
```bash
# 方式 A：下载官方 cn_data（A股 1d）
cd ~/RD-Agent && python scripts/get_data.py qlib_data \
    --target_dir ~/.qlib/qlib_data/cn_data --region cn
# 方式 B：用自己的 CSV 转 bin（qlib 文档 scripts/dump_bin.py），并补 calendars/instruments/features
# 校验：ls ~/.qlib/qlib_data/cn_data  # 应看到 calendars/ instruments/ features/
```
> 若想跑全市场而非 csi300，需同步改 `rdagent/scenarios/qlib/experiment/factor_template/conf_*.yaml` 的 `market`/`benchmark`，并确保 bin 数据含对应股票池；否则回测 universe 仍默认 csi300。

### Step 4：健康检查（先验证 LLM + Docker 无关链路）
```bash
cd ~/RD-Agent
rdagent health_check                 # 全查；失败看它给的具体提示
rdagent health_check --no-check-docker   # 我们不用 Docker，可跳过该项
```

### Step 5：启动（后台 + 日志 + 先小轮次）
```bash
cd ~/RD-Agent
# 修改 run_rdagent.sh 确保：export PATH + source conda + activate rdagent4qlib + rdagent fin_factor
nohup bash run_rdagent.sh > rdagent_run.log 2>&1 &
tail -f rdagent_run.log
# 首跑建议 QLIB_FACTOR_EVOLVING_N=3；稳定后再去掉限制跑 10 轮
```

### Step 6：如果仍报“输出格式错误”（排查顺序）
1. `ls git_ignore_folder/RD-Agent_workspace/` 找最近因子目录，看 `execution feedback` 与 `index_info=`；
2. 用 Step 2 的 python 校验 `daily_pv.h5`（key/data、MultiIndex 名、$ 列）；
3. 确认 rdagent 已升级（`_fix_python_booleans` 是否存在：`grep -r "_fix_python_booleans" $(python -c "import rdagent,os;print(os.path.dirname(rdagent.__file__))")`）；
4. 在 `rdagent/components/coder/factor_coder/prompts.yaml` 的 factor 提示中追加硬约束（2 级 MultiIndex datetime×instrument、单列、列名=因子名、写 result.h5 key=data）；
5. 若持续与模型生成质量相关，换 `zai/glm-4.7-flash` 或 gpt-4o 类模型对比，排除数据问题。

### 内存红线提示（15G）
- 全市场因子 df 单列约 600MB+，`process_factor_data` 会 concat 多个 → **全市场 + 多因子 + qrun 回测峰值易超 15G**。
- 建议：正式跑时把 `daily_pv.h5` 裁剪到回测 universe（csi300 约 300 只）或按 `QLIB_FACTOR_TRAIN/VALID/TEST` 日期段截取；调试必用子集。必要时 `free -g` 监控。

---

## 8. 参考来源

**官方文档 / 代码**
- RD-Agent 安装与配置文档：<https://rdagent.readthedocs.io/en/stable/installation_and_configuration.html>
- RD-Agent Quant 场景文档（配置参考、模板说明）：<https://rdagent.readthedocs.io/en/latest/scens/quant_agent_fin.html>
- RD-Agent GitHub：<https://github.com/microsoft/RD-Agent>（`rdagent/core/conf.py`、`rdagent/utils/env.py`、`rdagent/components/coder/factor_coder/config.py`、`rdagent/components/coder/model_coder/conf.py`、`rdagent/scenarios/qlib/experiment/workspace.py`、`rdagent/scenarios/qlib/developer/utils.py`、`rdagent/scenarios/qlib/experiment/factor_data_template/*`、`rdagent/scenarios/qlib/docker/Dockerfile`、`rdagent/oai/llm_conf.py`、`rdagent/oai/backend/base.py`、`rdagent/oai/backend/litellm.py`、`.env.example`）
- R&D-Agent(Q) 论文（因子输出格式定义）：<https://arxiv.org/html/2505.15155v2>
- Qlib 官方数据文档（get_data / dump_bin / cn_data 结构）：<https://qlib.readthedocs.io/en/latest/component/data.html>
- LiteLLM Z.AI(Zhipu) provider：<https://docs.litellm.ai/docs/providers/zai>
- DeepSeek 官方定价：<https://api-docs.deepseek.com/quick_start/pricing/>

**GitHub Issues / PR（社区实证）**
- #1428 / PR #1435：`get_factor_env/get_model_env` 覆盖默认 Docker 挂载 → `StopIteration`（Docker 模式起不来）
- #1064 / PR #1418：Windows 下 `normalize_volumes` 容器路径被当宿主机路径 → `too many colons` 挂载失败
- #678：因子 3 级 MultiIndex 导致 concat `AssertionError`（与“简单/错误 Index”同类问题）
- #916：火山/部分端点返回大写 `True/False` → `json.loads` 失败（新版 `_fix_python_booleans` 已修）
- #1308：DeepSeek 场景下评估阶段 `NoneType.merge` 崩溃（并发任务空反馈未优雅处理）
- #1407 / PR #1410：ML 因子 per-stock-per-day 重训导致数小时 100% CPU 挂起（静态 AST 护栏 + 提示词加固已修）
- #1335：`fin_factor/fin_model/fin_quant` 需要先准备 qlib 数据（文档缺失）

**社区博客 / 教程**
- dev.to《RD-Agent 教程——第一章：基础入门》（Linux-only、Python 3.10/3.11、LiteLLM 供应商表、health_check、Docker 权限）：<https://dev.to/henry_lin_3ac6363747f45b4/rd-agent-jiao-cheng-di-zhang-ji-chu-ru-men-ben-jiao-cheng-wei-jing-quan-bu-yan-zheng-jin-gong-can-kao--30kd>
- saulius.io《Automated Quant Research with AI Agents》（RD-Agent 架构深读）：<https://saulius.io/blog/automated-quant-research-ai-agents-rd-agent>
- 墨滴《RD-Agent + QLib：微软开源的量化研发自动化工具》（环境准备/数据转换/配置任务）：<https://mdnice.com/writing/0b20975699a5493db3419e0d256cfac9>
- 知乎《Qlib研究(一)：数据下载与处理》（cn_data 目录结构）：<https://zhuanlan.zhihu.com/p/446333670>
- 智谱 GLM-4.7-Flash 开源免费：<https://www.zhipuai.cn/en/news/148>
