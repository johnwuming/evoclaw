# 猪周期自动化跟踪系统 — 技术设计文档

> 设计日期：2026-03-31 | 研究代号：R-021b | 基于：R-021 猪周期研究报告 + R-020c 数据源评估
> 状态：**设计阶段**，待 dev team 实施

---

## 目录

1. [系统架构设计](#1-系统架构设计)
2. [数据采集模块详细设计](#2-数据采集模块详细设计)
3. [存储模块设计](#3-存储模块设计)
4. [分析模块设计](#4-分析模块设计)
5. [输出模块设计](#5-输出模块设计)
6. [运维设计](#6-运维设计)
7. [实施路线图](#7-实施路线图)
8. [风险和限制](#8-风险和限制)
9. [附录](#9-附录)

---

## 1. 系统架构设计

### 1.1 整体架构

```
                          ┌─────────────────────┐
                          │   定时调度器 (cron)   │
                          │  日更/周更/月更/季更   │
                          └────────┬────────────┘
                                   │
                          ┌────────▼────────────┐
                          │   数据采集层          │
                          │   DataCollector      │
                          │  ┌───────────────┐   │
                          │  │ AKShare (免费) │   │
                          │  │ 网页抓取 (半自)│   │
                          │  │ 手动录入 (兜底)│   │
                          │  └───────────────┘   │
                          └────────┬────────────┘
                                   │ 写入
                          ┌────────▼────────────┐
                          │   存储层             │
                          │   DuckDB             │
                          │   pig_cycle.duckdb   │
                          └────────┬────────────┘
                                   │ 读取
                          ┌────────▼────────────┐
                          │   分析层             │
                          │   CycleAnalyzer      │
                          │  · 周期位置评分      │
                          │  · 趋势检测          │
                          │  · 异常检测          │
                          └────────┬────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
           ┌───────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐
           │  报告生成层   │ │  告警层   │ │  可视化层    │
           │  ReportGen   │ │  Alerter │ │  md-viewer   │
           │  周报/月报    │ │ Telegram │ │  OpenClaw    │
           │  Markdown    │ │  推送    │ │  集成        │
           └──────────────┘ └──────────┘ └──────────────┘
```

### 1.2 各模块职责与接口

| 模块 | 职责 | 输入接口 | 输出接口 |
|------|------|---------|---------|
| **DataCollector** | 从各数据源采集生猪产业数据 | 无（被 cron 触发） | 写入 DuckDB |
| **DuckDB** | 存储时序数据，支持分析查询 | SQL INSERT/SELECT | SQL 查询结果 |
| **CycleAnalyzer** | 评分模型、趋势判断、异常检测 | 从 DuckDB 读取 | JSON 分析结果 |
| **ReportGen** | 生成 Markdown 周报/月报 | 分析结果 + 原始数据 | `.md` 文件 |
| **Alerter** | 阈值告警推送 | 分析结果 | Telegram 消息 |
| **md-viewer** | 在 OpenClaw 中展示报告 | Markdown 文件路径 | 用户可读页面 |

### 1.3 技术栈

| 组件 | 技术选择 | 理由 |
|------|---------|------|
| 语言 | Python 3.10+ | AKShare 生态、数据分析工具链 |
| 数据库 | DuckDB（单文件嵌入式） | 列式存储，时序分析性能好，零运维 |
| 数据采集 | AKShare + requests + BeautifulSoup | 免费、覆盖度足够 |
| 调度 | cron（系统级） | 简单可靠，无需额外服务 |
| 报告输出 | Markdown | 与 OpenClaw md-viewer 兼容 |
| 告警推送 | OpenClaw Telegram 集成 | 现有能力，无需额外开发 |
| 版本管理 | Git | 配置文件、脚本版本追踪 |

### 1.4 目录结构

```
pig-tracker/
├── config/
│   ├── config.yaml           # 全局配置（数据库路径、告警阈值等）
│   └── akshare_fields.yaml   # AKShare 接口字段映射
├── collector/
│   ├── __init__.py
│   ├── base.py               # BaseCollector 基类
│   ├── akshare_collector.py  # AKShare 数据采集
│   ├── web_scraper.py        # 网页抓取（发改委、华储网等）
│   └── manual_input.py       # 手动录入辅助脚本
├── storage/
│   ├── __init__.py
│   ├── schema.py             # DuckDB 建表语句
│   └── repository.py         # 数据读写操作封装
├── analyzer/
│   ├── __init__.py
│   ├── cycle_scorer.py       # 周期位置评分模型
│   ├── trend_detector.py     # 趋势检测（环比、移动平均）
│   └── alert_rules.py        # 告警规则引擎
├── reporter/
│   ├── __init__.py
│   ├── weekly_report.py      # 周报生成
│   ├── monthly_report.py     # 月报生成
│   └── templates/
│       ├── weekly.md.j2      # 周报 Jinja2 模板
│       └── monthly.md.j2     # 月报模板
├── alerter/
│   ├── __init__.py
│   └── telegram_alerter.py   # Telegram 推送
├── jobs/
│   ├── daily_collect.py      # 日度采集入口
│   ├── weekly_analyze.py     # 周度分析+报告入口
│   └── monthly_collect.py    # 月度采集入口
├── tests/
│   └── ...
├── pig_cycle.duckdb          # 数据库文件（.gitignore）
├── requirements.txt
└── README.md
```

---

## 2. 数据采集模块详细设计

### 2.1 指标与采集方案完整映射

基于 R-021 §2.1 的 15 个核心指标，逐一明确采集方案：

#### 指标 1：能繁母猪存栏量

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐⭐⭐ 最核心指标，领先猪价 ~10 个月 |
| **AKShare** | `ak.futures_pig_spot()` 返回产能子集，含"能繁母猪存栏"字段 |
| **数据频率** | 月度（官方农业农村部数据，月中旬发布上月数据） |
| **AKShare 可靠性** | 中。接口存在但字段映射需实测验证，历史数据深度不确定 |
| **备选方案** | ① 农业农村部官网新闻发布会文字稿抓取 ② 重庆市农委等地方农业部门网站同步转载 ③ 手动从券商研报提取 |
| **增量策略** | 查询 DuckDB 中最新月份，只插入新月份。官方数据不会修订，无需回刷 |
| **错误处理** | AKShare 失败 → 记录日志 → 跳过本次（月度数据滞后容忍度高）→ 3 天后重试。若连续 3 次失败 → 触发 Telegram 通知运维人员 |

#### 指标 2：生猪存栏量

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐⭐ |
| **AKShare** | `ak.futures_pig_spot()` 产能子集，含"生猪存栏"字段 |
| **数据频率** | 季度（国家统计局发布） |
| **备选方案** | 国家统计局官网数据发布库 |
| **增量策略** | 按季度去重，只插入新季度 |
| **错误处理** | 同指标 1 |

#### 指标 3：仔猪价格

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐⭐ |
| **AKShare** | ⚠️ `futures_pig_rank()` 不含仔猪价格。需测试 `ak.futures_pig_spot()` 是否有仔猪字段 |
| **数据频率** | 日度/周度 |
| **备选方案** | ① 我的农产品网网页抓取（部分免费）② 博亚和讯 ③ 手动从行业微信订阅号截图提取 |
| **AKShare 不可用时** | 设为"需手动补充"字段，周报中标注数据缺失 |
| **增量策略** | 仔猪价格日度更新但波动相对平缓，建议采集频率为**周度**（每周一采集上周均价）。按日期去重 |

#### 指标 4：母猪价格

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐ |
| **AKShare** | ❌ 不支持。涌益咨询付费数据 |
| **数据频率** | 周度 |
| **备选方案** | 券商研报定期引用涌益数据，可半自动从公开研报提取。**优先级低，Phase 3 后考虑** |
| **增量策略** | 手动录入，按周 |
| **错误处理** | 无数据时跳过，分析模型中该指标权重设为 0 |

#### 指标 5：猪粮比

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐⭐ |
| **AKShare** | ✅ `ak.futures_pig_spot()` 含"猪粮比价"字段 |
| **数据频率** | 周度（国家发改委价格监测中心） |
| **备选方案** | 可用外三元猪价 ÷ 玉米价格自行计算 |
| **增量策略** | 按周去重，记录发布日期 |
| **错误处理** | AKShare 失败 → 用日度价格自行计算近似值 |

#### 指标 6：猪料比

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐⭐ |
| **AKShare** | ❌ 不直接支持。卓创资讯付费数据 |
| **数据频率** | 周度 |
| **备选方案** | ① 用玉米+豆粕加权计算全价料成本 → 反推猪料比 ② 行业公开报告引用 |
| **增量策略** | 估算值可日度生成（依赖玉米、豆粕日度价格） |
| **错误处理** | 玉米/豆粕价格缺失时跳过 |

#### 指标 7：屠宰量/开工率

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐ |
| **AKShare** | ❌ 不支持。卓创资讯付费数据 |
| **数据频率** | 周度 |
| **备选方案** | 中国期货业协会/行业公开文章偶尔引用。**Phase 2 后考虑手动补充** |
| **增量策略** | 手动录入 |

#### 指标 8：二次育肥入场情况

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐ |
| **AKShare** | ❌ 不支持。数据不透明 |
| **数据频率** | 周度 |
| **备选方案** | 通过出栏体重变化间接推断（体重↑ 暗示压栏/二次育肥）。出栏体重见指标 14 |
| **建议** | 不直接采集，通过出栏体重间接代理 |

#### 指标 9：饲料销量

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐ |
| **AKShare** | ❌ 不支持 |
| **数据频率** | 月度 |
| **备选方案** | 饲料工业协会官网发布全国饲料产量月报 → 网页抓取 |
| **增量策略** | 按月去重 |
| **错误处理** | 跳过，权重设为 0 |

#### 指标 10：养殖利润/亏损幅度

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐⭐⭐ |
| **AKShare** | ⚠️ 需验证。`ak.futures_pig_spot()` 可能包含"自繁自养利润"字段，但不确定 |
| **数据频率** | 周度 |
| **备选方案** | ① 用猪价 - 饲料成本估算 ② 涌益/卓创公开引用数据 |
| **估算公式** | `自繁自养利润 ≈ (猪价 - 料肉比×全价料价格) × 出栏体重 - 固定成本分摊`。其中料肉比 ≈ 2.8，固定成本约 150-200 元/头 |
| **增量策略** | 按周去重 |
| **错误处理** | AKShare 无数据 → 用估算公式生成近似值，报告中标注"估算值" |

#### 指标 11：能繁母猪淘汰量

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐⭐ |
| **AKShare** | ❌ 不支持。涌益咨询付费数据 |
| **数据频率** | 月度 |
| **备选方案** | 通过能繁母猪存栏环比变化间接推算：`淘汰量 ≈ 上月存栏 - 本月存栏 + 后备转能繁` |
| **增量策略** | 依赖能繁母猪月度数据 |
| **建议** | 不直接采集，间接推算 |

#### 指标 12：冻肉库存

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐ |
| **AKShare** | ❌ 不支持 |
| **数据频率** | 周度 |
| **备选方案** | 华储网收储/放储公告 → 网页抓取；卓创库存容数据需付费 |
| **增量策略** | 抓取华储网公告，解析公告文本 |
| **错误处理** | 低优先级，缺失不影响核心分析 |

#### 指标 13：猪肉进出口数据

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐ |
| **AKShare** | ✅ `ak.china_import_export()` 或海关相关接口 |
| **数据频率** | 月度 |
| **备选方案** | 海关总署在线查询平台 |
| **增量策略** | 按月去重 |
| **注意** | 进口占比 <5%，对分析影响有限，可降低优先级 |

#### 指标 14：出栏体重

| 项目 | 说明 |
|------|------|
| **重要性** | ⭐⭐⭐⭐ |
| **AKShare** | ❌ 不支持 |
| **数据频率** | 周度 |
| **备选方案** | 涌益/卓创公开引用。**通过上市公司月度出栏数据中的体重信息间接参考**（牧原月报含出栏体重） |
| **增量策略** | 手动录入 |
| **替代方案** | 监测牧原/温氏月度销售简报中的出栏体重数据 |

#### 指标 15：天气/疫病因素

| 项目 | 说明 |
|------|------|
| **重要性** | 不定期，极端情况重要 |
| **AKShare** | ❌ |
| **数据频率** | 不定期 |
| **备选方案** | 农业农村部疫病公告网页抓取；新闻搜索 |
| **建议** | 不自动采集，由人工判断后手动录入重大事件 |

### 2.2 采集能力总结

| 采集方式 | 覆盖指标 | 自动化程度 |
|---------|---------|-----------|
| **AKShare 全自动** | 外三元猪价、内三元猪价、玉米价格、豆粕价格、猪粮比、能繁母猪存栏、生猪存栏、生猪出栏、猪肉产量 | 高（核心指标基本覆盖） |
| **AKShare + 计算** | 猪料比（估算）、养殖利润（估算）、母猪淘汰量（推算）、二次育肥（间接） | 中 |
| **网页抓取** | 华储网收储公告、饲料工业协会饲料产量、海关进出口 | 中 |
| **手动录入** | 仔猪价格、屠宰开工率、冻肉库存、出栏体重、母猪价格 | 低 |

### 2.3 增量更新通用策略

```python
class BaseCollector:
    """所有采集器的基类，封装增量逻辑"""

    def get_latest_date(self, table_name: str, date_column: str = "date") -> Optional[str]:
        """查询表中最新日期"""
        result = self.conn.execute(
            f"SELECT MAX({date_column}) FROM {table_name}"
        ).fetchone()
        return result[0] if result and result[0] else None

    def upsert_data(self, table_name: str, df: pd.DataFrame, key_columns: list[str]):
        """插入新数据，忽略已存在的（按 key 去重）"""
        # 使用 DuckDB 的 INSERT ... ON CONFLICT DO NOTHING
        # 或先过滤掉已有日期的数据
        existing = self.conn.execute(
            f"SELECT {','.join(key_columns)} FROM {table_name}"
        ).fetchall()
        existing_set = set(existing)
        for _, row in df.iterrows():
            key = tuple(row[k] for k in key_columns)
            if key not in existing_set:
                # INSERT
                pass
```

### 2.4 错误处理策略

```
采集失败处理流程：

1. 单次采集失败
   → 记录 warning 日志（指标名、错误类型、时间戳）
   → 跳过该指标，不影响其他指标采集
   → 数据库中该指标该日期标记为 NULL

2. 同一指标连续 3 次失败
   → 记录 error 日志
   → 触发 Telegram 告警："⚠️ {指标名} 连续 3 次采集失败，需人工介入"
   → 在周报中标注该指标数据缺失

3. AKShare 接口整体不可用
   → 切换到降级模式：仅使用本地已有数据生成报告
   → Telegram 通知运维人员
   → 记录 incident 日志

4. 数据异常值检测
   → 采集后对比前一值：涨跌幅 >20% 触发 warning
   → 对比历史同期均值：偏差 >30% 标记为"待验证"
   → 异常值不自动修正，但在报告中标注
```

### 2.5 AKShare 请求策略

- **请求间隔**：≥3 秒（反爬策略）
- **重试**：最多 3 次，指数退避（3s, 9s, 27s）
- **超时**：单次请求 30 秒
- **User-Agent**：使用 AKShare 默认
- **错误日志**：记录完整的 API 调用参数和返回状态

---

## 3. 存储模块设计

### 3.1 设计决策：按频率分表 vs 统一时序表

**选择：按频率分表（4 张核心表 + 2 张辅助表）**

理由：
1. 不同频率的数据时间粒度不同（日/周/月/季），统一表会导致大量 NULL
2. 分表后 SQL 查询更简洁，无需按频率过滤
3. DuckDB 对多表 JOIN 性能足够好

### 3.2 表结构 Schema

#### 表 1：`daily_prices` — 日度价格数据

```sql
CREATE TABLE daily_prices (
    date         DATE NOT NULL,              -- 日期（主键）
    pig_waisan   DECIMAL(6,2),               -- 外三元猪价 元/kg
    pig_neisan   DECIMAL(6,2),               -- 内三元猪价 元/kg
    pig_tuza     DECIMAL(6,2),               -- 土杂猪猪价 元/kg
    corn         DECIMAL(6,2),               -- 玉米价格 元/kg
    soybean_meal DECIMAL(6,2),               -- 豆粕价格 元/kg
    piglet_price DECIMAL(6,2),               -- 仔猪价格 元/kg（可能为 NULL）
    source       VARCHAR DEFAULT 'akshare',  -- 数据来源
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date)
);

-- 索引：日期范围查询
CREATE INDEX idx_daily_date ON daily_prices (date);
```

#### 表 2：`weekly_indicators` — 周度指标

```sql
CREATE TABLE weekly_indicators (
    week_end_date    DATE NOT NULL,           -- 周截止日期（周六，主键）
    pig_corn_ratio   DECIMAL(6,4),            -- 猪粮比（官方）
    pig_feed_ratio   DECIMAL(6,4),            -- 猪料比（估算）
    profit_self      DECIMAL(8,2),            -- 自繁自养利润 元/头
    profit_buy_piglet DECIMAL(8,2),           -- 外购仔猪利润 元/头
    slaughter_rate   DECIMAL(6,2),            -- 屠宰开工率 %
    frozen_inv_rate  DECIMAL(6,2),            -- 冻肉库存容 %
    avg_weight       DECIMAL(6,2),            -- 出栏均重 kg
    sow_price        DECIMAL(6,2),            -- 母猪价格 元/kg（可能为 NULL）
    source           VARCHAR DEFAULT 'mixed',
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (week_end_date)
);

CREATE INDEX idx_weekly_date ON weekly_indicators (week_end_date);
```

#### 表 3：`monthly_capacity` — 月度产能数据

```sql
CREATE TABLE monthly_capacity (
    month           DATE NOT NULL,            -- 月份（YYYY-MM-01，主键）
    breeding_sow    DECIMAL(8,1),             -- 能繁母猪存栏 万头
    pig_inventory   DECIMAL(8,1),             -- 生猪存栏 万头
    pig_slaughter   DECIMAL(8,1),             -- 生猪出栏 万头（月度可能为 NULL，季度有值）
    pork_production DECIMAL(8,1),             -- 猪肉产量 万吨
    feed_production DECIMAL(8,1),             -- 全国饲料产量 万吨（可能为 NULL）
    sow_mom_change  DECIMAL(6,2),             -- 能繁母猪环比变化 %
    sow_yoy_change  DECIMAL(6,2),             -- 能繁母猪同比变化 %
    source          VARCHAR DEFAULT 'akshare',
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (month)
);

CREATE INDEX idx_monthly_date ON monthly_capacity (month);
```

#### 表 4：`quarterly_macro` — 季度宏观数据

```sql
CREATE TABLE quarterly_macro (
    quarter         DATE NOT NULL,            -- 季度首日（YYYY-01-01/04-01/07-01/10-01，主键）
    gdp_agri_yoy    DECIMAL(6,2),            -- GDP农业分项同比 %
    cpi_pork_yoy    DECIMAL(6,2),            -- CPI猪肉分项同比 %
    pig_inventory   DECIMAL(8,1),            -- 季末生猪存栏 万头（国家统计局）
    pig_slaughter_q DECIMAL(8,1),            -- 季度生猪出栏 万头
    source          VARCHAR DEFAULT 'manual',
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (quarter)
);
```

#### 辅助表 5：`alerts` — 告警记录

```sql
CREATE TABLE alerts (
    id          INTEGER PRIMARY KEY DEFAULT nextval('alert_seq'),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alert_type  VARCHAR NOT NULL,             -- 告警类型标识
    indicator   VARCHAR NOT NULL,             -- 触发指标
    value       DECIMAL(10,2) NOT NULL,       -- 当前值
    threshold   DECIMAL(10,2) NOT NULL,       -- 阈值
    direction   VARCHAR NOT NULL,             -- 'above' | 'below'
    message     TEXT,                          -- 告警消息
    notified    BOOLEAN DEFAULT FALSE,        -- 是否已推送
    acknowledged BOOLEAN DEFAULT FALSE         -- 是否已确认
);

CREATE SEQUENCE alert_seq START 1;
CREATE INDEX idx_alerts_type ON alerts (alert_type);
CREATE INDEX idx_alerts_created ON alerts (created_at);
```

#### 辅助表 6：`collection_log` — 采集日志

```sql
CREATE TABLE collection_log (
    id          INTEGER PRIMARY KEY DEFAULT nextval('log_seq'),
    run_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    job_type    VARCHAR NOT NULL,             -- 'daily' | 'weekly' | 'monthly' | 'quarterly'
    indicator   VARCHAR NOT NULL,
    status      VARCHAR NOT NULL,             -- 'success' | 'partial' | 'failed'
    rows_added  INTEGER DEFAULT 0,
    error_msg   TEXT,
    duration_ms INTEGER                       -- 执行耗时
);

CREATE SEQUENCE log_seq START 1;
CREATE INDEX idx_log_run ON collection_log (run_at);
```

### 3.3 索引策略

- **主键索引**：每张表的日期/月份字段（DuckDB 自动创建）
- **额外索引**：仅 `alerts` 和 `collection_log` 需要按类型/时间查询
- **不建索引**：daily_prices 的价格字段（无需按价格范围查询）

### 3.4 数据保留策略

| 表 | 保留期限 | 理由 |
|------|---------|------|
| `daily_prices` | **10 年** | 猪周期 ~4-6 年，需至少 2 个完整周期历史 |
| `weekly_indicators` | **10 年** | 同上 |
| `monthly_capacity` | **永久** | 月度数据量极小（120 行/10 年），无清理必要 |
| `quarterly_macro` | **永久** | 同上 |
| `alerts` | **3 年** | 告警历史参考价值有限 |
| `collection_log` | **1 年** | 运维排查用，1 年足够 |

### 3.5 数据库文件管理

- **文件位置**：`pig-tracker/pig_cycle.duckdb`（单文件）
- **预估大小**：10 年日度数据约 3,650 行 × 8 列 ≈ 30KB（DuckDB 列式压缩后更小），总库 <10MB
- **备份**：每日 rsync 到备份目录（见 §6.3）
- **WAL 模式**：不需要（单进程写入）

---

## 4. 分析模块设计

### 4.1 周期阶段定义

| 阶段 | 编号 | 典型特征 | 评分区间 |
|------|------|---------|---------|
| **顶部** | P5 | 能繁母猪高位/持续增加、猪价高于成本线 30%+、利润丰厚、补栏积极 | 0-20 |
| **下降早期** | P4 | 能繁母猪仍在增长但增速放缓、猪价开始回落、利润收窄 | 20-35 |
| **下降中后期** | P3 | 能繁母猪开始去化、猪价低于成本线、行业亏损 | 35-50 |
| **底部去化** | P2 | 能繁母猪加速去化（环比 -1%+）、深度亏损、政策收储启动 | 50-65 |
| **底部确认** | P1 | 能繁母猪降至正常保有量以下、仔猪价格企稳回升、期货远月升水 | 65-75 |
| **上升期** | P0 | 能繁母猪持续低位、猪价回升突破成本线、利润转正、补栏恢复 | 75-100 |

> **注意**：评分越高表示周期位置越接近投资机会（底部确认→上升期），越低表示风险越大（顶部→下降期）。

### 4.2 多指标加权评分模型

```python
# analyzer/cycle_scorer.py

CYCLE_WEIGHTS = {
    "breeding_sow_level":     0.25,   # 能繁母猪绝对水平
    "breeding_sow_momentum":  0.15,   # 能繁母猪环比变化趋势
    "profit_level":           0.20,   # 养殖利润水平
    "pig_corn_ratio":         0.10,   # 猪粮比
    "avg_weight_trend":       0.08,   # 出栏体重趋势（压栏/抛售信号）
    "piglet_price_trend":     0.07,   # 仔猪价格趋势
    "futures_structure":      0.05,   # 期货期限结构（远月升/贴水）
    "slaughter_rate":         0.05,   # 屠宰开工率
    "frozen_inventory":       0.03,   # 冻肉库存水平
    "feed_production_trend":  0.02,   # 饲料产量趋势
}

class CycleScorer:
    """
    每个指标根据当前值映射到 0-100 的子评分，
    然后按权重加权求和得到综合评分。
    """

    def score_breeding_sow_level(self, current_sow: float) -> tuple[int, str]:
        """能繁母猪绝对水平 → 子评分"""
        if current_sow >= 4300:
            return (5, "能繁母猪严重过剩（>4300万头）")
        elif current_sow >= 4100:
            return (15, "能繁母猪高于正常保有量上沿")
        elif current_sow >= 3900:
            return (30, "能繁母猪处于绿色区域上沿，略高于正常保有量")
        elif current_sow >= 3700:
            return (65, "能繁母猪降至正常保有量以下，反转信号增强")
        elif current_sow >= 3500:
            return (80, "能繁母猪显著低于正常保有量，强反转信号")
        else:
            return (95, "能繁母猪严重去化，极强反转信号（但需警惕过度去化风险）")

    def score_breeding_sow_momentum(self, mom_3m_avg: float) -> tuple[int, str]:
        """能繁母猪 3 个月环比均值 → 子评分"""
        if mom_3m_avg > 1.0:
            return (5, "能繁母猪快速扩张")
        elif mom_3m_avg > 0:
            return (20, "能繁母猪缓慢增长")
        elif mom_3m_avg > -0.5:
            return (40, "能繁母猪微幅去化")
        elif mom_3m_avg > -1.0:
            return (65, "能繁母猪加速去化")
        else:
            return (85, "能繁母猪快速去化，底部特征明显")

    def score_profit_level(self, profit: float) -> tuple[int, str]:
        """自繁自养利润 元/头 → 子评分"""
        if profit > 500:
            return (5, "超高利润，产能扩张动力强")
        elif profit > 200:
            return (15, "利润丰厚，补栏积极")
        elif profit > 0:
            return (35, "微利，行业观望")
        elif profit > -100:
            return (50, "小幅亏损，去产能缓慢开始")
        elif profit > -300:
            return (70, "中度亏损，去产能加速")
        else:
            return (90, "深度亏损（>-300元/头），去产能剧烈")

    def score_pig_corn_ratio(self, ratio: float) -> tuple[int, str]:
        """猪粮比 → 子评分"""
        if ratio >= 9.0:
            return (5, "猪粮比≥9，过度上涨预警")
        elif ratio >= 6.0:
            return (20, "猪粮比正常偏高，行业盈利")
        elif ratio >= 5.5:
            return (40, "猪粮比接近盈亏平衡")
        elif ratio >= 5.0:
            return (60, "猪粮比低于平衡线，二级预警")
        elif ratio >= 4.5:
            return (75, "猪粮比≤5，一级预警，收储可能启动")
        else:
            return (90, "猪粮比严重失衡，深度亏损")

    # 其他指标类似实现...

    def compute_overall_score(self, data: dict) -> dict:
        """
        输入：各指标当前值
        输出：综合评分、阶段判定、各指标子评分明细
        """
        scores = {}
        signals = []

        scores["breeding_sow_level"], sig = self.score_breeding_sow_level(data["breeding_sow"])
        signals.append(sig)
        # ... 对每个指标计算子评分

        weighted_score = sum(
            scores[k] * CYCLE_WEIGHTS[k]
            for k in CYCLE_WEIGHTS
            if k in scores
        )

        # 归一化（如果有指标缺失，按实际权重归一化）
        total_weight = sum(CYCLE_WEIGHTS[k] for k in scores)
        if total_weight > 0:
            weighted_score = weighted_score / total_weight

        return {
            "overall_score": round(weighted_score, 1),
            "phase": self._map_phase(weighted_score),
            "phase_description": self._phase_description(weighted_score),
            "sub_scores": scores,
            "signals": signals,
            "missing_indicators": [k for k in CYCLE_WEIGHTS if k not in scores],
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def _map_phase(score: float) -> str:
        if score < 20:  return "P5_TOP"
        elif score < 35: return "P4_EARLY_DECLINE"
        elif score < 50: return "P3_MID_DECLINE"
        elif score < 65: return "P2_BOTTOM_DERATING"
        elif score < 75: return "P1_BOTTOM_CONFIRM"
        else:            return "P0_RISING"
```

### 4.3 趋势检测

```python
# analyzer/trend_detector.py

class TrendDetector:
    """检测各指标的趋势方向和拐点"""

    def detect_sow_trend(self, months: int = 6) -> dict:
        """
        能繁母猪趋势检测
        返回：方向、速度、拐点信号
        """
        # 取最近 N 个月数据
        # 计算环比变化率序列
        # 判断：持续下降？加速下降？减速下降？反弹？
        # 3 个月移动平均交叉判断拐点
        pass

    def detect_profit_trend(self, weeks: int = 12) -> dict:
        """养殖利润趋势"""
        pass

    def detect_price_momentum(self, days: int = 30) -> dict:
        """猪价动量：30 日涨幅/跌幅"""
        pass
```

### 4.4 告警规则

```python
# analyzer/alert_rules.py

ALERT_RULES = [
    {
        "id": "sow_below_normal",
        "name": "能繁母猪跌破正常保有量",
        "indicator": "breeding_sow",
        "condition": "value < 3900",
        "severity": "HIGH",
        "message": "⚠️ 能繁母猪跌破 3900 万头正常保有量！产能去化确认，周期底部信号增强。",
        "cooldown_days": 30,  # 同一告警 30 天内不重复触发
    },
    {
        "id": "sow_mom_fast_decrease",
        "name": "能繁母猪快速去化",
        "indicator": "sow_mom_change",
        "condition": "value < -1.0",
        "severity": "MEDIUM",
        "message": "📊 能繁母猪环比降幅超 1%，去产能加速中。",
        "cooldown_days": 30,
    },
    {
        "id": "pig_price_below_10",
        "name": "猪价跌破 10 元/kg",
        "indicator": "pig_waisan",
        "condition": "value < 10.0",
        "severity": "HIGH",
        "message": "🔴 生猪价格跌破 10 元/kg！极端低位，历史性底部区域。",
        "cooldown_days": 7,
    },
    {
        "id": "pig_corn_ratio_alert_1",
        "name": "猪粮比一级预警",
        "indicator": "pig_corn_ratio",
        "condition": "value < 4.5",
        "severity": "HIGH",
        "message": "🔴 猪粮比跌破 4.5:1，一级预警！国家将加大收储力度。",
        "cooldown_days": 14,
    },
    {
        "id": "pig_corn_ratio_alert_2",
        "name": "猪粮比二级预警",
        "indicator": "pig_corn_ratio",
        "condition": "value < 5.0",
        "severity": "MEDIUM",
        "message": "⚠️ 猪粮比跌破 5:1，二级预警，国家可能启动收储。",
        "cooldown_days": 14,
    },
    {
        "id": "deep_loss",
        "name": "深度亏损",
        "indicator": "profit_self",
        "condition": "value < -300",
        "severity": "MEDIUM",
        "message": "⚠️ 自繁自养亏损超 300 元/头，深度亏损加速去产能。",
        "cooldown_days": 14,
    },
    {
        "id": "profit_turn_positive",
        "name": "养殖利润转正",
        "indicator": "profit_self",
        "condition": "value > 0 and previous_value <= 0",
        "severity": "HIGH",
        "message": "🟢 养殖利润由负转正！周期反转确认信号。",
        "cooldown_days": 30,
    },
    {
        "id": "piglet_price_rally",
        "name": "仔猪价格大涨",
        "indicator": "piglet_price",
        "condition": "wow_change > 10",  # 周环比涨幅 >10%
        "severity": "MEDIUM",
        "message": "📊 仔猪价格周环比大涨 >10%，补栏意愿恢复信号。",
        "cooldown_days": 14,
    },
    {
        "id": "policy_storage",
        "name": "国家收储启动",
        "indicator": "policy_event",
        "condition": "event_type == '收储'",
        "severity": "MEDIUM",
        "message": "📢 国家启动冻猪肉收储，政策底信号。",
        "cooldown_days": 30,
    },
]

class AlertEngine:
    """告警引擎：检查所有规则，触发匹配的告警"""

    def check_all(self, data: dict) -> list[dict]:
        """返回触发的告警列表"""
        triggered = []
        for rule in ALERT_RULES:
            if self._evaluate(rule["condition"], data):
                if not self._in_cooldown(rule):
                    triggered.append(rule)
        return triggered

    def _in_cooldown(self, rule: dict) -> bool:
        """检查该规则是否在冷却期内"""
        # 查询 alerts 表中最近一次同 id 告警时间
        pass
```

### 4.5 报告生成逻辑

#### 周报内容清单

1. **关键指标速览表**：本周 vs 上周 vs 上月同期 vs 去年同期
2. **周期位置评分**：综合评分、阶段判定、评分变动
3. **趋势分析**：
   - 能繁母猪去化趋势（最近 6 个月环比折线图描述）
   - 猪价走势（最近 3 个月）
   - 养殖利润走势
4. **告警事项**：本周触发的告警
5. **数据更新状态**：哪些指标有更新、哪些缺失
6. **简要投资建议**：基于当前阶段的模板化建议
7. **前瞻关注**：下周应关注的事件（如数据发布日期、政策会议）

#### 月报额外内容

1. 月度数据详细分析（能繁母猪、出栏量、饲料产量）
2. 期货期限结构分析
3. 上市公司月度出栏数据汇总
4. 政策动态梳理
5. 行业新闻摘要

---

## 5. 输出模块设计

### 5.1 周报 Markdown 模板

```markdown
# 🐷 猪周期周报 — {year}年第{week_num}周

> 生成时间：{generated_at}
> 周期阶段：**{phase_name}**（评分 {score}/100，{score_change}）

---

## 📊 关键指标速览

| 指标 | 本周 | 上周 | 变化 | 状态 |
|------|------|------|------|------|
| 外三元猪价 | {price} 元/kg | {prev_price} 元/kg | {price_change} | {profit_status} |
| 猪粮比 | {ratio}:1 | {prev_ratio}:1 | {ratio_change} | {warning_level} |
| 能繁母猪（月） | {sow} 万头 | — | {sow_mom} | {sow_zone} |
| 自繁自养利润 | {profit} 元/头 | {prev_profit} 元/头 | {profit_change} | {profit_status} |
| 出栏均重 | {weight} kg | {prev_weight} kg | {weight_change} | — |

## 🔄 周期位置判断

**当前阶段：{phase_name}**

{phase_description}

### 评分明细

| 指标 | 权重 | 子评分 | 贡献 |
|------|------|--------|------|
| 能繁母猪水平 | 25% | {sub1} | {contrib1} |
| 能繁母猪趋势 | 15% | {sub2} | {contrib2} |
| 养殖利润 | 20% | {sub3} | {contrib3} |
| 猪粮比 | 10% | {sub4} | {contrib4} |
| ... | ... | ... | ... |

## 📈 趋势分析

### 能繁母猪存栏趋势（近 6 月）

{6 个月数据表格}

**趋势判断**：{trend_description}

### 猪价走势（近 3 月）

{价格走势描述}

## ⚠️ 告警事项

{本周触发告警列表，无告警则显示"本周无新增告警"}

## 📅 前瞻关注

- {下周关注事项 1}
- {下周关注事项 2}

## 📋 数据更新状态

| 指标 | 最新日期 | 状态 |
|------|---------|------|
| {各指标更新状态} |

---

*本报告由猪周期自动跟踪系统生成。数据来源于 AKShare 等公开数据源，仅供参考，不构成投资建议。*
```

### 5.2 报告存储

```
shared/results/pig-cycle-weekly/
├── 2026/
│   ├── W01-20260106.md       # 按周编号
│   ├── W02-20260113.md
│   ├── ...
│   └── W13-20260330.md
├── 2026-monthly/
│   ├── 2026-01.md
│   ├── 2026-02.md
│   └── ...
└── README.md                  # 索引文件，列出所有报告链接
```

### 5.3 Telegram 告警格式

```
🐷 猪周期告警

🔴 等级：HIGH
📋 指标：生猪价格（外三元）
📉 当前值：9.99 元/kg
🎯 阈值：< 10.0 元/kg
📝 说明：生猪价格跌破 10 元/kg！极端低位，历史性底部区域。

⏰ 触发时间：2026-03-18 10:30 CST

—猪周期自动跟踪系统
```

---

## 6. 运维设计

### 6.1 部署方式

**选择：cron 定时任务（而非 systemd 服务）**

理由：
1. 采集任务是离散的（每天/周/月运行一次），不是持续运行的服务
2. cron 简单可靠，调试方便
3. 每次运行独立进程，互不影响

#### cron 配置

```cron
# 猪周期跟踪系统 - cron 配置
# 用户：openclaw（或当前用户）

# 日度采集：每个工作日 19:30（A股收盘后，数据源更新完毕）
30 19 * * 1-5 cd /path/to/pig-tracker && python jobs/daily_collect.py >> logs/daily.log 2>&1

# 周度分析+报告：每周日 20:00
0 20 * * 0 cd /path/to/pig-tracker && python jobs/weekly_analyze.py >> logs/weekly.log 2>&1

# 月度采集：每月 15 日 19:00（官方月中发布数据）
0 19 15 * * cd /path/to/pig-tracker && python jobs/monthly_collect.py >> logs/monthly.log 2>&1

# 季度数据：每季末月 25 日（国家统计局数据发布）
0 19 25 3,6,9,12 * cd /path/to/pig-tracker && python jobs/quarterly_collect.py >> logs/quarterly.log 2>&1

# 数据库备份：每天 02:00
0 2 * * * cp /path/to/pig-tracker/pig_cycle.duckdb /path/to/pig-tracker/backup/pig_cycle_$(date +\%Y\%m\%d).duckdb

# 清理旧备份（保留 30 天）
0 3 * * 0 find /path/to/pig-tracker/backup/ -name "*.duckdb" -mtime +30 -delete
```

### 6.2 日志策略

```
pig-tracker/logs/
├── daily.log          # 日度采集日志（追加模式）
├── weekly.log         # 周度分析日志
├── monthly.log        # 月度采集日志
├── quarterly.log      # 季度采集日志
└── alert.log          # 告警推送日志
```

- **日志级别**：INFO（正常运行）、WARNING（采集失败但可恢复）、ERROR（需要人工介入）
- **日志轮转**：通过 logrotate 管理，保留 90 天
- **关键信息**：每次运行记录开始时间、结束时间、各指标采集结果、成功/失败数

#### logrotate 配置

```
/path/to/pig-tracker/logs/*.log {
    weekly
    rotate 12
    compress
    missingok
    notifempty
}
```

### 6.3 数据备份

| 策略 | 频率 | 保留 | 方式 |
|------|------|------|------|
| DuckDB 文件备份 | 每日 02:00 | 30 天 | cp 到 backup/ 目录 |
| 远程备份 | 每周日 | 4 份 | rsync 到远程存储（如有的话） |
| 报告文件 | 每次生成 | 永久 | Git 版本管理（shared/results/） |

### 6.4 与 OpenClaw 生态集成

#### md-viewer 集成

- 周报/月报存放在 `shared/results/pig-cycle-weekly/` 目录
- OpenClaw 的 md-viewer 可直接渲染这些 Markdown 文件
- 用户可通过对话请求："给我看最新猪周期周报" → OpenClaw 调用 md-viewer 展示

#### Telegram 通知集成

- 告警推送：通过 OpenClaw 现有的 Telegram 通知能力
- 周报摘要：每周日分析完成后，推送一段 3-5 句摘要到 Telegram
- 实现：`alerter/telegram_alerter.py` 调用 OpenClaw 的通知 API 或直接使用 python-telegram-bot

#### OpenClaw Agent 调用

- 用户可在对话中触发："更新猪周期数据" → OpenClaw 执行 `daily_collect.py`
- 用户可查询："当前猪周期评分是多少？" → OpenClaw 读取 DuckDB 返回最新评分
- 未来可通过 OpenClaw Agent Skill 封装这些操作

---

## 7. 实施路线图

### Phase 1：数据采集 + 存储（MVP）

**目标**：能够自动采集 AKShare 数据并存入 DuckDB

**时间**：2-3 天

**交付物**：
1. `storage/schema.py` — DuckDB 建表脚本
2. `collector/akshare_collector.py` — AKShare 数据采集器
3. `collector/base.py` — 基类（增量逻辑、错误处理）
4. `jobs/daily_collect.py` — 日度采集入口
5. `jobs/monthly_collect.py` — 月度采集入口
6. `pig_cycle.duckdb` — 初始化数据库
7. cron 配置文件

**验收标准**：
- [ ] `daily_collect.py` 能成功采集日度价格（外三元、玉米、豆粕）并存入 DuckDB
- [ ] `monthly_collect.py` 能成功采集能繁母猪存栏、生猪存栏
- [ ] 增量逻辑正确：重复运行不会产生重复数据
- [ ] 采集失败时正确记录日志，不影响其他指标
- [ ] 已有至少 1 个月的历史数据在库中

### Phase 2：分析 + 报告生成

**目标**：自动生成周报 Markdown 文件

**时间**：2-3 天

**交付物**：
1. `analyzer/cycle_scorer.py` — 周期位置评分模型
2. `analyzer/trend_detector.py` — 趋势检测
3. `analyzer/alert_rules.py` — 告警规则引擎
4. `reporter/weekly_report.py` — 周报生成
5. `reporter/templates/weekly.md.j2` — 周报模板
6. `jobs/weekly_analyze.py` — 周度分析入口
7. 首份周报文件

**验收标准**：
- [ ] 评分模型能正确输出综合评分和阶段判定
- [ ] 当前阶段判定与手动分析一致（2026年3月应判定为 P2/P3 附近）
- [ ] 周报 Markdown 格式正确，能在 md-viewer 中正常渲染
- [ ] 告警规则能正确匹配（如猪价<10 应触发 HIGH 告警）
- [ ] 报告中缺失指标正确标注

### Phase 3：告警 + Telegram 通知

**目标**：关键指标突破阈值时自动推送 Telegram 告警

**时间**：1-2 天

**交付物**：
1. `alerter/telegram_alerter.py` — Telegram 推送
2. 告警冷却机制实现
3. 告警记录持久化（alerts 表）
4. cron 告警检查任务（可合并到日度/周度任务中）

**验收标准**：
- [ ] 告警消息能成功推送到 Telegram
- [ ] 冷却机制有效（同一告警不重复推送）
- [ ] 告警记录写入 DuckDB alerts 表
- [ ] 手动触发测试告警成功

### Phase 4：md-viewer 集成 + 完善

**目标**：与 OpenClaw 深度集成，补充第三方数据

**时间**：持续迭代

**交付物**：
1. OpenClaw Agent Skill 定义（用户可通过对话触发数据更新、查看报告）
2. 网页抓取器（华储网收储公告、饲料工业协会数据）
3. 月报模板和生成器
4. 手动录入辅助脚本（CLI 交互式录入第三方数据）
5. 数据质量监控（AKShare vs 计算值对比）

**验收标准**：
- [ ] 用户通过 Telegram 对话可触发数据更新和查看报告
- [ ] 华储网公告自动抓取成功
- [ ] 月报格式完整
- [ ] 手动录入流程可用

---

## 8. 风险和限制

### 8.1 AKShare 数据质量风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 接口返回数据字段名变化 | 采集失败 | 字段映射配置化（yaml），便于快速调整；增加字段校验 |
| 数据源网站反爬升级 | 采集中断 | 请求间隔 ≥3 秒；备选数据源；手动录入兜底 |
| 历史数据深度不足 | 无法做长期回测 | 初始化时尽可能拉取全部可用历史；必要时手动补录 |
| `futures_pig_spot()` 接口实际字段与文档不一致 | 需要适配 | Phase 1 首先做接口实测，根据实际返回调整字段映射 |

**关键待验证项**（Phase 1 首日需完成）：
- [ ] `ak.futures_pig_rank()` 返回字段名和数据范围
- [ ] `ak.futures_pig_spot()` 返回字段名，确认是否包含能繁母猪、猪粮比、利润等
- [ ] 数据历史深度（最早可追溯到何时）
- [ ] 日度更新延迟（当日数据何时可获取）

### 8.2 农业农村部数据获取难度

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 官方数据仅通过新闻发布会发布，无结构化接口 | 无法自动采集月度产能数据 | ① AKShare 可能已封装 ② 新闻稿网页抓取 + 文本提取 ③ 手动录入 |
| 数据发布时间不固定 | cron 采集可能跑空 | 月度任务设为每月 15 日和 20 日各运行一次，取有数据的那次 |
| 季度数据（国家统计局）与月度数据格式不统一 | 存储需适配 | 分表存储（monthly_capacity + quarterly_macro） |

### 8.3 第三方数据源限制

- 涌益咨询、卓创资讯数据为**付费订阅**，免费方案无法获取
- 券商研报引用的数据有**时滞**（研报发布通常滞后 1-2 周）
- 解决方案：Phase 1-2 仅使用 AKShare + 估算值，Phase 4 评估是否值得付费订阅

### 8.4 服务器资源消耗

| 资源 | 估算消耗 | 说明 |
|------|---------|------|
| 磁盘 | <50MB/年 | DuckDB 压缩后极小，报告文件也很小 |
| CPU | 极低 | 每天运行一次，单次 <1 分钟 |
| 内存 | <200MB | Python + AKShare + DuckDB，运行时短暂占用 |
| 网络 | 极低 | 每次采集几个 HTTP 请求 |

**结论**：资源消耗可忽略不计，在当前 OpenClaw 服务器上运行无压力。

### 8.5 模型风险

- 评分模型的权重和阈值基于历史经验设定，**未经回测验证**
- 规模化养殖改变了猪周期的传统规律，历史阈值可能需要动态调整
- **缓解措施**：每季度回溯评分与实际价格走势的匹配度，调整权重

### 8.6 合规与免责

- 本系统仅供个人研究使用，不构成投资建议
- 数据来源于公开渠道，需注意版权
- 报告中应标注"自动生成，仅供参考"

---

## 9. 附录

### 9.1 AKShare 接口速查

```python
import akshare as ak

# 1. 生猪价格排行（日度）
#    含：外三元、内三元、土杂猪、玉米、豆粕
df = ak.futures_pig_rank()

# 2. 生猪供应维度综合数据
#    含：猪肉批发价、储备冻猪肉、饲料原料、白条肉、
#        生猪产能、育肥猪、肉类价格指数、猪粮比价
df = ak.futures_pig_spot()

# 3. 生猪期货主力合约
df = ak.futures_main_sina(symbol="lh0")

# 4. 生猪期货所有合约（用于期限结构分析）
#    待确认具体接口

# 5. 进出口数据
df = ak.china_import_export()
```

### 9.2 能繁母猪绿黄红区间参考

| 区间 | 范围（万头） | 对应正常保有量比例 | 调控措施 |
|------|-------------|------------------|---------|
| 绿色 | 3,588 - 4,095 | 92%-105% | 常规监测 |
| 黄色（下） | 3,315 - 3,588 | 85%-92% | 引导产能调控 |
| 黄色（上） | 4,095 - 4,290 | 105%-110% | 引导产能调控 |
| 红色（下） | < 3,315 | < 85% | 强制性产能调控 |
| 红色（上） | > 4,290 | > 110% | 强制性产能调控 |

正常保有量基准：3,900 万头（2024 年修订版《生猪产能调控实施方案》）

### 9.3 关键阈值汇总

| 指标 | 阈值 | 含义 |
|------|------|------|
| 能繁母猪 | 3,900 万头 | 正常保有量（绿/黄分界线） |
| 猪粮比 | 5.5:1 | 传统盈亏平衡线 |
| 猪粮比 | 5.0:1 | 二级预警线（启动收储） |
| 猪粮比 | 4.5:1 | 一级预警线（加大收储） |
| 猪粮比 | 9.0:1 | 过度上涨预警 |
| 自繁自养利润 | 0 元/头 | 盈亏平衡 |
| 自繁自养利润 | -300 元/头 | 深度亏损 |
| 猪价 | 10 元/kg | 心理关口 / 极端低位 |
| 能繁母猪环比 | -1.0% | 快速去化标志 |

### 9.4 配置文件模板（config.yaml）

```yaml
# pig-tracker/config/config.yaml

database:
  path: "pig_cycle.duckdb"

akshare:
  request_interval: 3        # 请求间隔（秒）
  max_retries: 3
  timeout: 30

report:
  weekly_output_dir: "shared/results/pig-cycle-weekly"
  monthly_output_dir: "shared/results/pig-cycle-monthly"

alert:
  telegram_enabled: true
  cooldown_default_days: 14

collection:
  daily_time: "19:30"
  weekly_time: "20:00"
  monthly_day: 15
  monthly_time: "19:00"

logging:
  level: "INFO"
  dir: "logs"
  retention_days: 90
```

---

*设计文档结束。本文档由 Research Lead 基于猪周期研究报告（R-021）和数据源评估（R-020c）编写，供 dev team 实施参考。*


---

## 附录: 猪周期核心经济逻辑与历史数据（R-021）

# 猪周期（Pig Cycle）完整逻辑、观测指标体系与投资跟踪系统设计

> 研究完成时间：2026年3月31日 | 研究代号：R-021

---

## 目录
1. [猪周期核心逻辑与历史规律](#1-猪周期核心逻辑与历史规律)
2. [前瞻性观测指标体系](#2-前瞻性观测指标体系)
3. [各指标数据获取途径](#3-各指标数据获取途径)
4. [当前周期判断（2026年3月）](#4-当前周期判断2026年3月)
5. [投资标的与策略](#5-投资标的与策略)
6. [自动化跟踪系统方案设计](#6-自动化跟踪系统方案设计)
7. [来源列表](#7-来源列表)

---

## 1. 猪周期核心逻辑与历史规律

### 1.1 经济学原理：蛛网模型（Cobweb Model）

猪周期的核心经济学解释是**蛛网模型**：

- **核心逻辑**：当期价格决定下期生产决策，但生猪生产存在天然滞后，导致供需错配形成周期性波动
- **产能传导链**：后备母猪培育约4个月 → 能繁母猪受孕分娩约114天（~3.8个月） → 仔猪育肥至出栏约6个月 → **合计约10个月**
- **完整周期形成**：扩产约2年（从能繁母猪补充到商品猪大量出栏）+ 缩产约2年 = **传统4年左右周期**
- **价格与供给的反向波动**：高价刺激补栏 → 10个月后供给暴增 → 价格暴跌 → 亏损去产能 → 10个月后供给收缩 → 价格回升

### 1.2 中国猪周期历史（2002年至今）

| 轮次 | 时间区间 | 周期长度 | 核心驱动因素 | 特征 |
|------|----------|----------|-------------|------|
| 第1轮 | 2002-2006年 | ~4年 | 常规供需波动 | 波动幅度较小 |
| 第2轮 | 2006-2010年 | ~4年 | 蓝耳病疫情 | 波幅加大 |
| 第3轮 | 2010-2014年 | ~4年 | 常规周期 | 波幅继续加大 |
| 第4轮 | 2014-2018年 | ~4年 | **环保禁养政策** | 各地划定禁养区，2016年底前关闭拆除，能繁母猪存栏累计下降38%，规模化加速 |
| 第5轮 | 2018-2022年 | ~4年 | **非洲猪瘟** | 极端波动：能繁母猪从4400万头骤降至2019年2800万头，猪价突破40元/kg |
| 第6轮 | 2022-至今 | >3年（进行中） | 规模化+供给过剩 | 下行期异常漫长，规模化企业扛亏损致去产能缓慢 |

**关键趋势**：波动幅度逐渐加大，周期长度从4年拉长至6年以上，由发散型蛛网向收敛型蛛网转变。

### 1.3 第5轮周期（非洲猪瘟）详细时间线

- **2018年8月**：中国首例非洲猪瘟确诊
- **2019年**：疫情大规模扩散，能繁母猪从4400万头骤降至2800万头（降幅36%）
- **2019年10月**：猪价突破40元/kg（历史极值）
- **2020年Q2**：能繁母猪恢复至非瘟前水平
- **2020年底**：能繁母猪达4400万头
- **2021年6月**：能繁母猪达4564万头历史高位，猪价暴跌至~10元/kg
- **2022年**：短暂反弹后进入新一轮下行

### 1.4 第6轮周期（当前）

- **2022年**：周期启动，猪价经历短暂上涨
- **2023-2025年**：持续下行，规模化企业扛亏损，产能去化极为缓慢
- **2025年全年**：猪价均价约13.74元/kg，为近五年最低
  - 1月最高：15.76元/kg
  - 10月最低：11.52元/kg
  - 10月下旬一度跌破11元/kg
  - 10月起自繁自养陷入亏损
- **2025年10月**：能繁母猪存栏4035万头，仍高于3900万头正常保有量
- **2025年末**：能繁母猪3961万头，同比下降2.9%
- **2026年1-2月**：牧原销售均价分别为12.57、11.59元/kg，2月已出现亏损
- **2026年3月18日**：全国均价跌破10元/kg（9.99元/kg），时隔12年再现

### 1.5 影响猪周期的关键变量

| 变量 | 作用机制 | 影响方向 |
|------|----------|----------|
| 能繁母猪存栏 | 决定未来10个月生猪供给 | 存栏↑ → 猪价↓（滞后10个月） |
| 生猪存栏 | 决定短期供给能力 | 存栏↑ → 猪价↓ |
| 出栏体重 | 影响实际猪肉供给量 | 体重↑ → 有效供给↑ |
| 屠宰量 | 反映当前需求端消化能力 | 屠宰↑ → 短期支撑猪价 |
| 饲料成本（玉米/豆粕） | 决定养殖成本和补栏意愿 | 成本↑ → 利润↓ → 抑制补栏 |
| 疫病 | 突发减产 | 疫病→ 存栏骤降 → 猪价↑ |
| 政策调控 | 收储放储、产能调控方案 | 收储→支撑猪价；放储→压制猪价 |
| 规模化程度 | 改变去产能速度 | 规模化↑ → 去产能慢 → 下行期拉长 |
| PSY（每头母猪年断奶仔猪数） | 生产效率提升 | PSY↑ → 同样存栏下实际供给↑ |

**重要变化**：PSY从2016年的17.56头提升至2025年的24.34头（行业平均），头部企业牧原、神农达29-32头。这意味着同样数量的能繁母猪能产出更多商品猪，3900万头能繁母猪对应的实际供给能力已大幅提升。

---

## 2. 前瞻性观测指标体系

### 2.1 核心指标全景表

| # | 指标名称 | 含义 | 数据来源 | 发布频率 | 前瞻时间 | 稳定性 | 历史有效性 |
|---|---------|------|---------|---------|---------|--------|-----------|
| 1 | **能繁母猪存栏量** | 可繁殖母猪数量，决定未来10个月生猪供给 | 农业农村部（官方月度）、涌益咨询（周度样本） | 月度（官方）/周度（第三方） | **领先猪价~10个月** | 高，官方数据连续可靠 | 极高，业界公认最核心指标 |
| 2 | 生猪存栏量 | 各阶段生猪总存栏，反映中短期供给 | 农业农村部/国家统计局 | 季度 | 领先猪价~3-6个月 | 高 | 高 |
| 3 | 仔猪价格 | 反映补栏意愿和对后市预期 | 我的农产品网/涌益咨询 | 日度/周度 | 领先猪价~6个月 | 高 | 高，补栏意愿的晴雨表 |
| 4 | 母猪价格 | 反映产能扩张/收缩信号 | 涌益咨询 | 周度 | 领先猪价~10个月 | 中 | 中高 |
| 5 | **猪粮比** | 生猪价格/玉米价格，判断盈亏平衡 | 国家发改委/AKShare | 周度 | **同步/微滞后** | 高 | 传统有效，但5.5:1平衡线部分失效 |
| 6 | **猪料比** | 考虑全价饲料成本的盈亏指标 | 饲料行业/卓创资讯 | 周度 | 同步 | 高 | 比猪粮比更准确 |
| 7 | 屠宰量/开工率 | 反映当前需求端消化能力 | 卓创资讯 | 周度 | 同步/短期前瞻 | 高 | 中高 |
| 8 | 二次育肥入场情况 | 投机性压栏，短期减少供给推高猪价 | 涌益咨询/行业调研 | 周度 | 影响短期（1-2个月） | 中（数据不透明） | 中，需结合体重数据判断 |
| 9 | 饲料销量 | 前瞻母猪补栏和存栏变化 | 饲料工业协会/涌益咨询 | 月度 | 领先~1-2个月 | 中 | 中高 |
| 10 | **养殖利润/亏损幅度** | 自繁自养与外购仔猪头均利润 | 涌益咨询/卓创资讯 | 周度 | **同步**，决定未来去产能动力 | 高 | 极高，亏损深度决定去产能幅度 |
| 11 | 能繁母猪淘汰量 | 直接反映产能去化速度 | 涌益咨询 | 月度 | 领先~10个月 | 中（样本数据） | 高 |
| 12 | 冻肉库存 | 收储/商业库存的蓄水池作用 | 卓创资讯/华储网 | 周度 | 同步/短期 | 中 | 中 |
| 13 | 猪肉进出口数据 | 进口冲击/出口拉动 | 海关总署 | 月度 | 滞后1-2月发布 | 高 | 低（进口占比<5%，影响有限） |
| 14 | 出栏体重 | 压栏/抛售信号 | 涌益咨询/卓创资讯 | 周度 | 领先~1个月 | 高 | 中高，体重↑暗示压栏惜售 |
| 15 | 天气/疫病因素 | 突发供给冲击 | 农业农村部疫病公告/新闻 | 不定期 | 不确定 | 低 | 极端情况影响极大 |

### 2.2 关键指标详解

#### 能繁母猪存栏量（最核心）
- **领先逻辑**：能繁母猪配种→妊娠114天→仔猪出生→育肥6个月→出栏，合计约10个月
- **数据标准**：2024年修订版《生猪产能调控实施方案》确定3900万头为正常保有量
- **绿黄红区间**：
  - 绿色区域：正常保有量的92%-105%（3588-4095万头）
  - 黄色区域：85%-92%或105%-110%
  - 红色区域：低于85%或高于110%
- **2025年末数据**：3961万头，处于绿色区域上沿

#### 猪粮比与猪料比
- **猪粮比** = 生猪价格（元/kg）÷ 玉米价格（元/kg）
- **传统盈亏平衡线**：5.5:1
- **⚠️ 重要更新**：传统5.5:1平衡线在现代养殖条件下已部分失效，行业更关注**猪料比**（考虑玉米+豆粕全价料成本）
- **国家发改委调控预警**：
  - ≥9:1 → 过度上涨三级预警
  - ≤6:1 → 过度下跌三级预警
  - ≤5:1 → 二级预警（启动收储）
  - ≤4.5:1 → 一级预警（加大收储力度）

#### 养殖利润
- **自繁自养**：从母猪繁育到肥猪出栏全链条
- **外购仔猪**：购买仔猪育肥至出栏
- 两种模式趋势高度相关（相关度99.6%），但外购仔猪利润整体低于自繁自养
- **2026年3月**：自繁自养头均亏损达283元（3月13日当周），深度亏损正在加速去产能

---

## 3. 各指标数据获取途径

### 3.1 官方数据源

| 数据源 | 数据内容 | 频率 | 获取方式 | 备注 |
|--------|---------|------|---------|------|
| **农业农村部** | 能繁母猪存栏、生猪存栏、出栏量 | 月度/季度 | 官网发布、新闻发布会 | 最权威，但有滞后 |
| **国家统计局** | 季度生猪存出栏、CPI猪肉分项 | 季度/月度 | 官网数据发布库 | CPI猪肉分项反映终端消费 |
| **国家发改委** | 猪粮比、猪料比、养殖利润 | 周度 | 官网价格监测中心 | 核心盈亏判断数据 |
| **海关总署** | 猪肉进出口量值 | 月度 | 海关统计数据在线查询平台 | 影响相对有限 |
| **华储网** | 中央储备冻猪肉收储/放储公告 | 不定期 | 华储网官网 | 政策风向标 |

### 3.2 第三方数据源

| 数据源 | 数据内容 | 频率 | 获取方式 | 备注 |
|--------|---------|------|---------|------|
| **涌益咨询** | 能繁母猪存栏样本、淘汰量、饲料销量、二次育肥 | 周度/月度 | 付费订阅，部分期货公司引用 | 被多家券商/期货公司引用，质量高 |
| **卓创资讯** | 屠宰企业开工率、冻肉库存、猪价 | 周度/日度 | 付费订阅 | 屠宰端数据最全 |
| **我的农产品网** | 生猪/仔猪日度价格 | 日度 | 部分免费+付费 | 实时报价 |
| **博亚和讯** | 饲料原料价格、生猪价格 | 日度/周度 | 部分免费 | 饲料端数据丰富 |
| **饲料工业协会** | 全国饲料产量 | 月度 | 官网发布 | 领先指标之一 |

### 3.3 AKShare Python API 接口

AKShare（开源Python金融数据库）提供以下生猪相关接口：

| 接口函数 | 数据内容 | 备注 |
|---------|---------|------|
| `futures_pig_rank()` | 生猪价格排行：外三元、内三元、土杂猪、玉米、豆粕 | 日度更新 |
| `futures_pig_spot()` | 供应维度综合数据：猪肉批发价、储备冻猪肉、饲料原料、白条肉、生猪产能、育肥猪、肉类价格指数、猪粮比价 | 多维度数据集 |
| 生猪产能子接口 | 能繁母猪存栏（万头）、猪肉产量（万吨）、生猪存栏（万头）、生猪出栏（万头） | 月度/季度 |

```python
# AKShare 示例用法
import akshare as ak

# 生猪价格排行（含外三元、内三元、玉米、豆粕）
pig_rank = ak.futures_pig_rank()

# 生猪供应维度综合数据
pig_spot = ak.futures_pig_spot()

# 生猪期货主力合约行情
# 可通过 ak.futures_main_sina(symbol="lh0") 获取
```

### 3.4 上市公司公告

| 公司 | 代码 | 关键数据 | 披露频率 |
|------|------|---------|---------|
| 牧原股份 | 002714 | 月度出栏量、销售均价、养殖成本 | 月度（出栏）、季度/年度（财务） |
| 温氏股份 | 300498 | 月度出栏量、销售均价 | 月度/季度 |
| 新希望 | 000876 | 季度出栏量、成本数据 | 季度 |

**牧原股份2025年年报**（2026年3月发布）：
- 营收1441.45亿元，同比+4.49%
- 净利润158.12亿元，同比-16.45%
- 2026年1-2月养殖成本约12元/kg
- 2026年2月销售均价11.59元/kg，已出现经营性亏损

---

## 4. 当前周期判断（2026年3月）

### 4.1 最新关键数据

| 指标 | 最新数据 | 时间点 | 状态判断 |
|------|---------|--------|---------|
| 全国生猪均价 | **9.99元/kg**（跌破10元关口） | 2026年3月18日 | 接近2018年历史最低9.92元/kg |
| 生猪期货LH2605 | 10,005元/吨 | 2026年3月30日 | 低位震荡 |
| 能繁母猪存栏 | 3,961万头 | 2025年12月末 | 绿色区域上沿，仍高于正常保有量 |
| 自繁自养利润 | 头均亏损283元 | 2026年3月13日当周 | 深度亏损 |
| 2025年全国出栏 | 71,973万头，同比+2.4% | 2025年全年 | 供给充裕 |
| 2025年末生猪存栏 | 42,967万头 | 2025年末 | 高位 |
| 猪肉进口 | 97.58万吨 | 2025年全年 | 回落 |
| PSY（行业平均） | 24.34头 | 2025年 | 同样存栏下产出更多 |

### 4.2 期货期限结构

| 合约 | 收盘价（元/吨） | 日期 |
|------|----------------|------|
| LH2605 | 10,005 | 2026-3-30 |
| LH2607 | 11,065 | 2026-3-30 |
| LH2609 | 12,275 | 2026-3-30 |
| LH2611 | 12,645 | 2026-3-30 |
| LH2701 | 13,165 | 2026-3-30 |
| LH2703 | 12,945 | 2026-3-30 |

**期限结构判断**：近低远高，呈明显**backwardation结构**（近月贴水、远月升水）。市场预期：
- 近月（5月合约）反映当前供给过剩现实
- 远月（11月、次年1月）升水30%+，隐含市场对下半年产能去化→供给收缩→价格回升的预期

### 4.3 周期位置判断

**当前（2026年3月）处于猪周期第6轮的产能去化中后期。**

判断依据：
1. ✅ **猪价深度跌破成本线**：10元/kg远低于行业平均成本~12元/kg
2. ✅ **全面亏损**：自繁自养亏损283元/头，已持续近半年
3. ✅ **能繁母猪开始加速去化**：2025年10月单月去化45万头（此前月减仅5万头）
4. ⚠️ **但去化仍不充分**：3961万头仍高于3900万头正常保有量
5. ✅ **政策加码**：2026年中央一号文件首次提出"强化生猪产能综合调控"
6. ⚠️ **规模化延缓去化**：大型企业融资能力强，亏损容忍度高

**预计时间线**：
- 2026年Q2：能繁母猪有望降至3850-3900万头区间（接近正常保有量）
- 2026年下半年：供给边际改善，猪价有望回升
- 2026年全年均价预测：12-13元/kg（前低后高）
- 价格最高点可能在Q4或2027年Q1

---

## 5. 投资标的与策略

### 5.1 可用投资标的

| 标的类型 | 具体标的 | 特点 |
|---------|---------|------|
| **生猪期货** | 大连商品交易所 LH（合约月份1/3/5/7/9/11） | 最直接的猪周期投资工具，16吨/手，涨跌停4% |
| **股票-牧原** | 002714 | 行业龙头，成本最低（~12元/kg），2025年净利158亿，市值~1900亿 |
| **股票-温氏** | 300498 | 第二大养殖企业，2025年净利52亿（同比-44%），市值~1050亿 |
| **股票-新希望** | 000876 | 2025年预亏15-18亿，抗周期能力较弱 |
| **畜牧ETF** | 159867（畜牧ETF）、159865（养殖ETF） | 分散风险，追踪中证畜牧养殖指数 |
| **其他ETF** | 516670、159165、512450、159007 | 多家基金公司的畜牧养殖ETF |

### 5.2 投资策略建议

#### 核心判断：周期底部左侧，但反转时点尚需观察

**策略一：期货做多远月（中等风险）**
- **标的**：LH2609或LH2701远月合约
- **逻辑**：远月已部分反映去产能预期，但若去化加速仍有上行空间
- **入场时机**：等待能繁母猪降至3900万头以下确认
- **止损**：LH2609跌破11,000元/吨

**策略二：股票左侧布局龙头（中长期）**
- **标的**：牧原股份（成本优势最大，周期反转弹性最大）
- **逻辑**：当前猪价底部区域，龙头估值偏低
- **风险**：下行期可能持续超预期（规模化延缓去化）
- **建议**：分批建仓，不宜一次性重仓

**策略三：ETF定投（低风险）**
- **标的**：畜牧ETF(159867)
- **逻辑**：分散单一公司风险，获取行业Beta
- **方式**：月度定投，持续6-12个月

**策略四：观望等待（保守）**
- **适用**：若判断去产能不足（能繁母猪持续>3900万头）
- **信号**：等待能繁母猪连续3个月加速去化+仔猪价格企稳回升

### 5.3 关键风险

1. **去产能不及预期**：规模化企业持续扛亏损，能繁母猪始终在正常水平之上
2. **疫病风险**：非瘟等可能突发改变供需格局（双向：减少供给利好，但引发恐慌性抛售利空）
3. **政策不确定性**：收储力度、环保政策变化
4. **饲料成本波动**：玉米、豆粕价格受国际市场和天气影响
5. **PSY持续提升**：同等存栏下产出增加，可能延缓供需平衡

---

## 6. 自动化跟踪系统方案设计

### 6.1 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    定时调度（cron）                        │
│              周更任务 / 月更任务 / 日更任务                  │
└──────────┬──────────────────────────────┬────────────────┘
           │                              │
     ┌─────▼──────┐              ┌────────▼────────┐
     │  数据采集层  │              │   AKShare API    │
     │  (Python)   │              │   (免费数据)      │
     └─────┬──────┘              └────────┬─────────┘
           │                              │
           └──────────┬───────────────────┘
                      │
              ┌───────▼───────┐
              │   存储层       │
              │   DuckDB/     │
              │   SQLite      │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │   分析层       │
              │ 周期位置判断    │
              │ 指标评分模型    │
              └───────┬───────┘
                      │
           ┌──────────┼──────────┐
           │          │          │
    ┌──────▼───┐ ┌───▼────┐ ┌──▼─────────┐
    │ 周报输出  │ │ 告警层  │ │ 月报生成   │
    │ (md格式) │ │(Telegram│ │(shared/    │
    │          │ │ 推送)   │ │  results/) │
    └──────────┘ └────────┘ └────────────┘
```

### 6.2 数据采集模块

#### 免费数据（AKShare）— 自动采集

```python
# data_collector.py
import akshare as ak
import duckdb
from datetime import datetime

class PigCycleCollector:
    """猪周期数据自动采集器"""

    def __init__(self, db_path="pig_cycle.duckdb"):
        self.conn = duckdb.connect(db_path)
        self._init_tables()

    def collect_daily(self):
        """日度采集：生猪价格排行"""
        df = ak.futures_pig_rank()
        # 包含：外三元、内三元、土杂猪、玉米、豆粕
        self.conn.execute("INSERT INTO daily_prices SELECT * FROM df")

    def collect_weekly(self):
        """周度采集：猪粮比等综合数据"""
        df = ak.futures_pig_spot()
        # 包含：猪粮比价、猪肉批发价、白条肉等
        self.conn.execute("INSERT INTO weekly_indicators SELECT * FROM df")

    def collect_monthly(self):
        """月度采集：生猪产能数据"""
        df = ak.futures_pig_spot()  # 产能子集
        # 包含：能繁母猪存栏、生猪存栏、出栏、猪肉产量
        self.conn.execute("INSERT INTO monthly_capacity SELECT * FROM df")
```

#### 第三方数据（需补充）— 半自动/手动

| 数据 | 来源 | 建议方式 |
|------|------|---------|
| 涌益咨询样本数据 | 付费订阅/券商报告引用 | 定期从公开研报提取 |
| 卓创屠宰开工率 | 付费订阅 | 从中国期货业协会公开文章提取 |
| 上市公司月度出栏 | 深交所/上交所公告 | 可用akshare的`stock_notice_report`接口 |
| 发改委猪粮比 | 国家发改委价格监测中心 | 网页抓取或AKShare |
| 华储网收储公告 | 华储网官网 | 网页抓取 |

### 6.3 存储层设计

使用 **DuckDB**（轻量级列式数据库，适合时序分析）：

```sql
-- 核心表结构
CREATE TABLE daily_prices (
    date DATE PRIMARY KEY,
    pig_price_waisanyuan DECIMAL(6,2),  -- 外三元猪价 元/kg
    pig_price_neisanyuan DECIMAL(6,2),
    corn_price DECIMAL(6,2),             -- 玉米价格
    soybean_meal_price DECIMAL(6,2),     -- 豆粕价格
    pig_corn_ratio DECIMAL(6,2)          -- 猪粮比
);

CREATE TABLE monthly_capacity (
    month DATE PRIMARY KEY,
    breeding_sow DECIMAL(8,1),           -- 能繁母猪存栏 万头
    pig_inventory DECIMAL(8,1),          -- 生猪存栏 万头
    pig_slaughter DECIMAL(8,1),          -- 生猪出栏 万头
    pork_production DECIMAL(8,1)         -- 猪肉产量 万吨
);

CREATE TABLE weekly_indicators (
    week_date DATE PRIMARY KEY,
    slaughter_rate DECIMAL(6,2),         -- 屠宰开工率 %
    frozen_inventory_rate DECIMAL(6,2),  -- 冻肉库存容 %
    profit_self_breed DECIMAL(8,2),      -- 自繁自养利润 元/头
    profit_buy_piglet DECIMAL(8,2),      -- 外购仔猪利润 元/头
    avg_live_weight DECIMAL(6,2)         -- 出栏均重 kg
);

CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    indicator VARCHAR,
    value DECIMAL(10,2),
    threshold DECIMAL(10,2),
    direction VARCHAR,  -- above/below
    message TEXT
);
```

### 6.4 分析层：周期位置判断模型

```python
# cycle_analyzer.py
class CyclePositionAnalyzer:
    """基于多维指标判断猪周期位置"""

    WEIGHTS = {
        "breeding_sow_level": 0.25,     # 能繁母猪存栏水平
        "breeding_sow_momentum": 0.15,  # 能繁母猪环比变化趋势
        "profit_level": 0.20,           # 养殖利润水平
        "pig_corn_ratio": 0.10,         # 猪粮比
        "slaughter_weight": 0.10,       # 出栏体重（压栏信号）
        "piglet_price": 0.10,           # 仔猪价格
        "frozen_inventory": 0.05,       # 冻肉库存
        "feed_sales": 0.05,             # 饲料销量
    }

    def score_cycle_position(self, data: dict) -> dict:
        """
        评分体系：0-100
        0-20: 周期顶部（产能高峰，猪价即将下行）
        20-40: 下行早期
        40-60: 下行中后期/底部区域
        60-80: 上行早期
        80-100: 周期顶部
        """
        score = 0
        signals = []

        # 能繁母猪水平评分
        sow = data["breeding_sow"]
        if sow > 4200:
            score += 5  # 严重过剩
            signals.append("能繁母猪严重过剩")
        elif sow > 3900:
            score += 15  # 略高于正常
            signals.append("能繁母猪略高于正常保有量")
        elif sow > 3600:
            score += 65  # 低于正常，反转信号
            signals.append("能繁母猪低于正常保有量，反转信号")
        else:
            score += 85  # 严重去化
            signals.append("能繁母猪严重去化，强反转信号")

        # ... 其他指标评分逻辑

        return {
            "score": score,
            "phase": self._map_phase(score),
            "signals": signals,
            "recommendation": self._recommend(score)
        }
```

### 6.5 输出层

#### 周报格式
```markdown
# 猪周期周报 - {YYYY}年第{W}周

## 关键指标速览
| 指标 | 本周 | 上周 | 变化 | 状态 |
|------|------|------|------|------|
| 外三元猪价 | xx元/kg | xx元/kg | ↑/↓ | 亏损/盈利 |
| 猪粮比 | x.x:1 | x.x:1 | ↑/↓ | 预警等级 |
| 能繁母猪（月） | xxxx万头 | - | 环比 | 绿/黄/红 |

## 周期位置：{阶段}（评分 xx/100）
## 投资建议：{建议}
## 告警事项：{如有}
```

#### 月报格式（写入 shared/results/）
更详细的月度分析报告，包含趋势图表描述、行业动态、政策变化等。

### 6.6 告警层

```python
ALERT_THRESHOLDS = {
    "breeding_sow_below_3900": {"value": 3900, "direction": "below",
        "message": "⚠️ 能繁母猪跌破3900万头正常保有量！产能去化信号确认"},
    "pig_corn_ratio_below_5": {"value": 5.0, "direction": "below",
        "message": "🔴 猪粮比跌破5:1！一级预警，国家可能启动收储"},
    "pig_price_below_10": {"value": 10.0, "direction": "below",
        "message": "🔴 生猪价格跌破10元/kg！极端低位"},
    "profit_loss_over_300": {"value": -300, "direction": "below",
        "message": "⚠️ 自繁自养亏损超300元/头，深度亏损加速去产能"},
    "sow_mom_decrease_over_1pct": {"value": -1.0, "direction": "below",
        "message": "📊 能繁母猪环比降幅超1%，去产能加速"},
}
```

告警通过 Telegram 推送（利用 OpenClaw 现有通知能力）。

### 6.7 更新频率规划

| 任务 | 频率 | 数据内容 | 自动化程度 |
|------|------|---------|-----------|
| 日更 | 每工作日 | 生猪价格、玉米/豆粕价格 | 全自动（AKShare） |
| 周更 | 每周日 | 猪粮比、屠宰开工率、冻肉库存、养殖利润 | 半自动（AKShare+手动补充） |
| 月更 | 每月中旬 | 能繁母猪存栏、生猪存栏、出栏量、饲料产量 | 半自动（官方数据发布后采集） |
| 季更 | 每季末 | GDP农业分项、CPI猪肉分项、上市公司季报 | 手动 |
| 告警 | 实时 | 关键指标阈值触发 | 全自动 |

### 6.8 实施路径

利用现有 **OpenClaw dev team + research team** 实现：

1. **Phase 1（1-2天）**：搭建 DuckDB 存储层 + AKShare 数据采集脚本
2. **Phase 2（1天）**：实现周期位置评分模型
3. **Phase 3（1天）**：接入 Telegram 告警 + 周报/月报自动生成
4. **Phase 4（持续）**：逐步接入第三方数据源（涌益/卓创），完善模型参数

可通过 OpenClaw 的 cron 调度定期触发数据采集和分析任务。

---

## 7. 来源列表

| # | 来源 | URL | 用途 |
|---|------|-----|------|
| 1 | 君百略咨询 - 猪周期研究报告 | https://kingparallel.com/research_reports/1052.html | 历史周期规律、蛛网模型 |
| 2 | 一德期货/新浪财经 | https://finance.sina.com.cn/stock/bxjj/2025-10-30/doc-infvskcp9496443.shtml | 第4-5轮周期详情、政策调控 |
| 3 | 卓创资讯/新浪财经 | https://finance.sina.cn/futuremarket/qsyw/2026-01-15/detail-inhhiyxz3487356.d.html | 2025年全年猪价回顾 |
| 4 | 搜狐/期货日报 | https://www.sohu.com/a/974032181_121123739 | 2026年展望、能繁母猪去化数据 |
| 5 | 新浪财经/中国猪业 | https://finance.sina.com.cn/wm/2026-03-19/doc-inhrpnfu4676510.shtml | 2026年3月猪价跌破10元 |
| 6 | 博亚和讯 | https://www.boyar.cn/article/1253033.html | 生猪期货各合约价格 |
| 7 | 大连商品交易所 | http://www.dce.com.cn/dce/channel/list/2279.html | 生猪期货合约规格 |
| 8 | 东方财富/牧原年报 | https://emcreative.eastmoney.com/app_fortune/article/index.html?artCode=20260327215437030667970 | 牧原2025年财务数据 |
| 9 | 第一财经/温氏业绩快报 | https://www.yicai.com/news/103056996.html | 温氏2025年业绩 |
| 10 | 东方财富 | http://quote.eastmoney.com/sz159867.html | 畜牧ETF列表 |
| 11 | 知乎/AKShare官方 | https://zhuanlan.zhihu.com/p/612292954 | AKShare生猪接口说明 |
| 12 | AKShare官方文档 | https://akshare-hh.readthedocs.io/en/latest/data/futures/futures.html | 产能接口字段 |
| 13 | 重庆市农业农村委员会 | https://nyncw.cq.gov.cn/zwxx_161/ywxx/202603/t20260317_15539434.html | 能繁母猪3961万头数据 |
| 14 | 国家发改委 | https://www.ndrc.gov.cn/xxgk/zcfb/gg/201510/W020190905485530722623.pdf | 猪粮比调控预案 |
| 15 | 方正证券 | https://www.foundersc.com/u/cms/www/ZX/20230610/b5c1df9ca01342ffab21340d4118c6cc.pdf | 能繁母猪领先10个月论述 |
| 16 | 联合资信 | https://www.lhratings.com/file/fe4038fc38e.pdf | 产能传导周期（4+3.8+6=10个月） |
| 17 | 新浪财经/猪易通 | https://finance.sina.com.cn/roll/2026-02-04/doc-inhkrihp9885440.shtml | PSY数据（24.34头） |
| 18 | 永赢基金/新浪财经 | https://finance.sina.com.cn/stock/relnews/cn/2026-03-27/doc-inhskrvx9670450.shtml | 2025年10月猪价、亏损数据 |

---

## 8. 知识缺口与待更新

1. **2026年1-3月能繁母猪月度数据**尚未公布，需持续跟踪
2. 仔猪价格领先猪价的**具体量化月数**缺乏权威数据
3. 饲料销量作为前瞻指标的**领先时间**需进一步研究
4. 二次育肥入场/出场数据**获取渠道有限**，需探索
5. AKShare的`futures_pig_spot`接口**完整参数**待实际测试验证
6. 猪料比的**精确盈亏平衡值**（替代猪粮比5.5:1）需进一步确认

---

## 9. 方法论反思

**做得好的**：
- 三个搜索Agent并行，覆盖了理论、指标、投资三个维度
- 获取到了2026年3月最新数据（猪价跌破10元、期货价格）
- 找到了AKShare的具体接口函数名
- 识别了PSY提升对周期分析的重要影响

**需改进的**：
- 各历史周期的具体波峰波谷价格数据不够完整（仅第5轮有精确数据）
- 第三方数据（涌益/卓创）的具体获取成本和订阅方式未深入调研
- 自动化跟踪系统的技术实现细节需进一步细化
