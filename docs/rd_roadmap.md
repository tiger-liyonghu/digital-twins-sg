# Digital Twins Singapore — 研发规划路线图

> 版本: 1.0
> 日期: 2026-03-06
> 状态: DRAFT — 待审阅

---

## 目录

1. [项目愿景与定位](#1-项目愿景与定位)
2. [研发阶段总览](#2-研发阶段总览)
3. [Phase 0: 基座构建](#3-phase-0-基座构建148k-底座--统计增强)
4. [Phase 1: MVP 问答系统](#4-phase-1-mvp-问答系统)
5. [Phase 2: 记忆与事件系统](#5-phase-2-记忆与事件系统)
6. [Phase 3: Agent 社交网络与互动](#6-phase-3-agent-社交网络与互动)
7. [Phase 4: 实时感知层](#7-phase-4-实时感知层)
8. [Phase 5: 认知能力——反思与规划](#8-phase-5-认知能力反思与规划)
9. [Phase 6: 行为校准与自进化](#9-phase-6-行为校准与自进化)
10. [Phase 7: 垂直行业应用](#10-phase-7-垂直行业应用)
11. [Phase 8: 规模化与性能](#11-phase-8-规模化与性能)
12. [数据治理演进](#12-数据治理演进)
13. [技术债务管理](#13-技术债务管理)
14. [团队与资源规划](#14-团队与资源规划)
15. [风险登记册](#15-风险登记册)
16. [成功指标](#16-成功指标)

---

## 1. 项目愿景与定位

### 1.1 愿景

构建全球首个**基于 148K 真实分布人群画像的新加坡社会数字孪生系统**，使企业和政府能够在虚拟人群上测试政策、产品、传播策略，获得**比传统问卷更快、更便宜、更可重复**的洞察。

### 1.2 核心价值主张

| 对比维度 | 传统问卷调研 | 我们的 Digital Twins |
|----------|-------------|---------------------|
| 样本量 | 500-2000 人 | 148,000 人（按需采样） |
| 成本 | $20,000-50,000/次 | $0.06-1.50/次 |
| 周期 | 2-6 周 | 3-30 分钟 |
| 可重复性 | 不可能 | 完全可重复（固定种子） |
| 记忆效应 | 无（每次独立） | 有（Agent 记住历史事件） |
| 人口代表性 | 依赖招募 | 数学保证（Census 校准） |
| 深度分析 | 受限于问卷设计 | 可追问、交叉分析、连续实验 |

### 1.3 技术壁垒

1. **148K 人群底座**：NVIDIA Nemotron-Personas-Singapore 叙事 + 我们的 20 维统计增强，全球唯一
2. **数学严谨性**：IPF + Bayesian Network + Cholesky + Census 校准，经 16 项统计检验验证
3. **三层决策架构**：规则→概率→LLM，成本可控且质量分层
4. **新加坡特化**：10 个生命阶段本体、CPF 模型、NS 规则、HDB 逻辑，无法简单复制

### 1.4 目标用户

| 用户类型 | 使用场景 | 价值 |
|----------|----------|------|
| **保险公司** | 产品定价验证、市场需求评估 | 替代焦点小组，节省 90% 成本 |
| **政府部门** | 政策影响预评估（GST、BTO、CPF 调整） | 政策出台前的虚拟压力测试 |
| **银行/金融** | 零售产品需求预测、客群画像 | 精准 segment 分析 |
| **学术研究** | 社会学/经济学仿真实验 | 大样本低成本虚拟实验 |
| **媒体/咨询** | 舆论趋势预测、民意模拟 | 快速洞察 |

---

## 2. 研发阶段总览

```
2026 Q1                Q2                Q3                Q4           2027
 │                      │                 │                 │              │
 ├── Phase 0 ──────┤    │                 │                 │              │
 │   基座构建        │    │                 │                 │              │
 │   148K增强+入库   │    │                 │                 │              │
 │                   │    │                 │                 │              │
 │    ├── Phase 1 ──────┤ │                 │                 │              │
 │    │   MVP问答系统    │ │                 │                 │              │
 │    │   Web+采样+LLM   │ │                 │                 │              │
 │    │                  │ │                 │                 │              │
 │    │    ├── Phase 2 ──────┤              │                 │              │
 │    │    │   记忆+事件     │              │                 │              │
 │    │    │                 │              │                 │              │
 │    │    │      ├── Phase 3 ──────┤       │                 │              │
 │    │    │      │   社交网络+互动  │       │                 │              │
 │    │    │      │                  │       │                 │              │
 │    │    │      │        ├── Phase 4 ──────┤                │              │
 │    │    │      │        │   实时感知       │                │              │
 │    │    │      │        │                  │                │              │
 │    │    │      │        │      ├── Phase 5 ──────┤         │              │
 │    │    │      │        │      │   反思+规划      │         │              │
 │    │    │      │        │      │                   │         │              │
 │    │    │      │        │      │    ├── Phase 6 ──────┤     │              │
 │    │    │      │        │      │    │   行为校准       │     │              │
 │    │    │      │        │      │    │                  │     │              │
 │    │    │      │        │      │    │    ├── Phase 7 ──────────┤           │
 │    │    │      │        │      │    │    │   垂直行业            │           │
 │    │    │      │        │      │    │    │                      │           │
 │    │    │      │        │      │    │    │     ├── Phase 8 ──────────┤     │
 │    │    │      │        │      │    │    │     │   规模化+性能        │     │
```

### 阶段概览表

| Phase | 名称 | 时长 | 前置 | 核心产出 | 成本增量 |
|-------|------|------|------|----------|----------|
| **0** | 基座构建 | 1 周 | 无 | 148K enriched agents in Supabase | $25/月 |
| **1** | MVP 问答 | 3 周 | P0 | Web 端可用的问答系统 | +$20/月 API |
| **2** | 记忆+事件 | 2 周 | P1 | Agent 有记忆，事件影响行为 | +$0 |
| **3** | 社交互动 | 4 周 | P2 | Agent 间对话、信息传播 | +$50/月 API |
| **4** | 实时感知 | 3 周 | P1 | 自动接入新闻/API 事件 | +$30/月 API |
| **5** | 反思规划 | 4 周 | P2 | 高阶认知、目标分解 | +$100/月 API |
| **6** | 行为校准 | 6 周 | P2+数据 | 真实行为数据校准 LLM 偏差 | 数据获取成本 |
| **7** | 垂直行业 | 持续 | P1+ | 保险/银行/政府专属模块 | 按客户需求 |
| **8** | 规模化 | 4 周 | P5+ | 本地模型、高并发 | +$2000/月 GPU |

---

## 3. Phase 0: 基座构建（148K 底座 + 统计增强）

### 3.1 目标

将 NVIDIA 148K 人群画像增强为完整的 Digital Twin 底座，入库 Supabase。

### 3.2 详细任务

| 任务 | 描述 | 交付物 | 天数 |
|------|------|--------|------|
| P0.1 NVIDIA 数据探索 | 读取 parquet，确认精确字段名、分布、缺失值 | 数据探索报告 | 0.5 |
| P0.2 字段映射设计 | NVIDIA 字段 → 我们标准字段的映射规则 | 映射表文档 | 0.5 |
| P0.3 增强引擎开发 | `augment_nvidia.py`：CPT 采样 income/housing/residency/health | 脚本 + 148K CSV | 2 |
| P0.4 人格批量采样 | 复用 `personality_init.py`，148K Cholesky 批量采样 | Big Five + 态度 | 0.5 |
| P0.5 家庭构建 | 复用 `household_builder.py`，148K 家庭分配 | household_id/role | 1 |
| P0.6 CPF 初始化 | 复用 `cpf_model.py`，按 age+income 估算 CPF 余额 | cpf_oa/sa/ma/ra | 0.5 |
| P0.7 统计验证 | 复用 `synthesis_gate.py`，全量验证 148K | 验证报告 | 0.5 |
| P0.8 Schema V3 | 新 Supabase migration（含叙事字段+索引） | SQL 文件 | 0.5 |
| P0.9 批量入库 | 148K agents + households 上传 Supabase | 线上数据 | 0.5 |

### 3.3 技术决策

**Q: 为什么不用 IPF？**
A: NVIDIA 148K 已按 Census 分布生成。IPF 用于从零构建联合分布。我们只需条件采样缺失维度。IPF 保留用于验证。

**Q: 148K 入库性能？**
A: 分 300 批 × 500 行 upsert，每批 1-2 秒，总计 ~10 分钟。

**Q: Supabase 存储够吗？**
A: 148K × ~3KB/行（含叙事）≈ 450MB。Pro plan 8GB 充裕。Free plan 500MB 紧张但可行。

### 3.4 验收标准

- [ ] 148K agents 全部入库 Supabase
- [ ] 所有边际分布 SRMSE < 0.20（vs Census）
- [ ] Big Five 均值偏差 < 0.15（vs Schmitt 2007）
- [ ] 中位收入偏差 < 25%（vs MOM 2025）
- [ ] 数据库查询 < 1s（按 area+age+gender 筛选）

---

## 4. Phase 1: MVP 问答系统

### 4.1 目标

非技术用户可以通过 Web 界面向 148K Agent 群体提问，获得结构化分析结果。

### 4.2 详细任务

| 任务 | 描述 | 交付物 | 天数 |
|------|------|--------|------|
| P1.1 采样引擎 | `sampler.py`：分层/随机/定向三种模式 | Python 模块 | 2 |
| P1.2 Persona 构建 | `persona_builder.py`：统计+叙事 两层 prompt | Python 模块 | 1 |
| P1.3 Job Runner | `job_runner.py`：poll pending → sample → LLM → aggregate | Python 模块 | 2 |
| P1.4 聚合引擎 | `aggregator.py`：人口统计学交叉分析 | Python 模块 | 1 |
| P1.5 DB 层 | `db/*.py`：Supabase 连接 + 各表 CRUD | Python 模块 | 1 |
| P1.6 Web /ask | Next.js 提问页面：问题+选项+采样配置 | 前端页面 | 2 |
| P1.7 Web /jobs | 任务列表 + 单任务结果仪表板 | 前端页面 | 2 |
| P1.8 Web /agents | Agent 浏览器：搜索/筛选/详情 | 前端页面 | 2 |
| P1.9 成本控制 | LLM 调用限速、预算上限、异常检测 | 配置 + 日志 | 1 |
| P1.10 Demo 场景 | 3 个完整 demo（保险/BTO/GST） | 运行报告 | 1 |

### 4.3 核心交互流程

```
用户 (Web)                   Supabase                  Runner (Python)
  │                             │                            │
  │─── POST /ask ──────────────>│                            │
  │    (question, options,      │                            │
  │     sample_size=200)        │                            │
  │                             │── INSERT simulation_jobs ──>│
  │                             │   status='pending'         │
  │                             │                            │
  │                             │                      poll ─┤
  │                             │<── SELECT pending jobs ─────┤
  │                             │                            │
  │                             │                  采样 200人 ─┤
  │                             │<── SELECT agents (sample) ──┤
  │                             │                            │
  │                             │              逐个调 LLM ────┤
  │                             │                  (并发 5)   │
  │                             │                            │
  │                             │<── INSERT agent_responses ──┤
  │                             │<── UPDATE job.result ───────┤
  │                             │    status='completed'       │
  │                             │                            │
  │<── Supabase Realtime ───────│                            │
  │    (job status changed)     │                            │
  │                             │                            │
  │─── GET /jobs/[id] ─────────>│                            │
  │<── 返回结果仪表板 ──────────│                            │
```

### 4.4 验收标准

- [ ] 用户可通过 Web 提交问题，200 人采样模拟 < 5 分钟完成
- [ ] 结果页展示：选项分布、年龄/收入/种族/住房 交叉分析
- [ ] 单次模拟成本 < $0.10（200 agents）
- [ ] 3 个 Demo 场景全部运行成功
- [ ] JSON 解析成功率 > 95%
- [ ] 同画像 Agent 响应多样性：Simpson 多样性指数 > 0.6（同 age_group+gender+ethnicity 的 agent 对同一问题的回答不应高度趋同）

---

## 5. Phase 2: 记忆与事件系统

### 5.1 目标

Agent 拥有持久记忆。外部事件写入记忆后，影响后续提问的回答。

### 5.2 详细任务

| 任务 | 描述 | 交付物 | 天数 |
|------|------|--------|------|
| P2.1 Memory Schema | `agent_memories` 表 + 索引 | SQL migration | 0.5 |
| P2.2 Memory Manager | `memory_manager.py`：写入/检索/容量管理 | Python 模块 | 2 |
| P2.3 Persona V2 | 三层 prompt：统计+叙事+记忆 | 更新 persona_builder | 1 |
| P2.4 事件注入 | Web /events 页面 + 批量写记忆 | 前端 + 后端 | 2 |
| P2.5 LLM 影响评估 | 事件注入时用 LLM 评估六维影响向量 | Python 函数 | 1 |
| P2.6 记忆效应 Demo | 连续 3 轮实验展示记忆影响 | Demo 报告 | 1 |
| P2.7 记忆容量策略 | 每 Agent 上限 50 条，溢出清理 | 策略 + 实现 | 0.5 |
| P2.8 语义压缩 | 超限时先将相似记忆压缩为摘要（memory_type=compressed），再删最旧最低分 | Python 函数 | 1.5 |
| P2.9 衰减检索函数 | 基于 recency×importance 加权排序替代简单排序 | Python 函数 | 0.5 |

### 5.3 记忆检索策略

**V1（MVP，本 Phase 实现）— 衰减加权检索：**
```python
def memory_retrieval_score(memory, current_time):
    """
    受 Stanford Generative Agents (Park 2023) 启发的衰减函数。
    α 控制时效权重，γ 控制重要性权重。
    """
    hours_ago = (current_time - memory.created_at).total_seconds() / 3600
    recency = 1.0 / (1.0 + hours_ago / 24)   # 24h 半衰
    importance_norm = memory.importance / 10.0
    alpha, gamma = 0.4, 0.6
    return alpha * recency + gamma * importance_norm
```

**V2（Phase 5 升级）：**
```python
# 向量语义检索（pgvector）
# score = α·recency(t) + β·cosine_sim(query, memory) + γ·importance
# Stanford Generative Agents 的检索公式，在 V1 衰减函数基础上加入语义相关性
```

### 5.4 事件影响模型

```
事件注入后的处理流程：

1. 用户输入事件描述（如 "GST 将涨至 10%"）
2. LLM 评估：
   a. 六维影响向量 (biological, psychological, social, economic, cognitive, spiritual)
   b. 受影响人群筛选条件 (target_filter)
   c. 重要性评分 (1-10)
3. 对所有匹配 target_filter 的 agent 写入 experience 记忆
4. 可选：自动触发一轮快速模拟，观察即时反应
```

### 5.5 验收标准

- [ ] Agent 在被问同一问题时，第二次回答受记忆影响（≥ 30% 的 agent 态度变化）
- [ ] 事件注入后，受影响 agent 的记忆中包含事件信息
- [ ] 记忆容量不超过 50 条/agent，自动清理正常工作
- [ ] 三轮连续实验 Demo 展示清晰的记忆效应

---

## 6. Phase 3: Agent 社交网络与互动

### 6.1 目标

Agent 之间建立社交关系，可以互相对话、影响观点、传播信息。

### 6.2 为什么需要互动

- 舆论传播：一个负面消息如何从少数人扩散到全社会
- 群体决策：朋友/家人的意见如何影响个人决策
- 社区效应：同一小区的人共同面对噪音/拥堵等问题
- 职场网络：同事之间的信息交流

### 6.3 详细任务

| 任务 | 描述 | 天数 |
|------|------|------|
| P3.1 社交网络生成 | 基于 planning_area + age + education + workplace 生成社交图 | 3 |
| P3.2 关系类型定义 | 家人(household)、朋友(area+age proximity)、同事(industry)、弱连接 | 1 |
| P3.3 对话引擎 | Agent-Agent 对话（≤2轮），一个问另一个的意见 | 3 |
| P3.4 意见传播模型 | 社交影响力模型：opinion_new = α·own + β·Σ(influence_j × opinion_j) | 2 |
| P3.5 信息级联模拟 | 注入事件 → 核心节点知道 → 传播到社交网络 → 观察扩散速度 | 3 |
| P3.6 Web 可视化 | 社交网络局部图 + 信息传播动画 | 3 |
| P3.7 传播验证 | 对比真实社交媒体传播速度校准参数 | 2 |

### 6.4 社交网络生成算法

```python
def generate_social_network(agents: list) -> nx.Graph:
    """
    Small-World 网络 (Watts-Strogatz) + 属性亲和力

    规则:
    1. 家庭连边: 同 household_id 的 agent 全连接 (weight=1.0)
    2. 邻居连边: 同 planning_area，age 差 < 10，P(连接) = 0.02 (weight=0.3)
    3. 同事连边: 同 industry，P(连接) = 0.01 (weight=0.5)
    4. 弱连接: 随机跨区连边，P = 0.001 (weight=0.1)

    目标网络属性:
    - 平均度: 15-25（新加坡社交密度）
    - 聚类系数: 0.3-0.5
    - 平均路径长度: 4-6
    """
```

### 6.5 数据模型

```sql
CREATE TABLE social_edges (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_a TEXT NOT NULL REFERENCES agents(agent_id),
    agent_b TEXT NOT NULL REFERENCES agents(agent_id),
    edge_type TEXT NOT NULL,  -- family / friend / colleague / weak
    weight NUMERIC(3,2) DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_a, agent_b)
);
```

### 6.6 计算成本估算

```
148K agents × 平均 20 条边 = 1.48M 边（social_edges 表 ~200MB）
一次传播模拟（BFS 5跳）: ~10K 个 agent 被激活
如果 10% 需要 LLM 对话: 1K LLM 调用 ≈ $0.30
完整传播模拟: 约 $0.50-3.00

成本控制措施：
- 对话深度限制 ≤ 2 轮（防止互动链无限延伸）
- 简单意见传播用规则引擎（P3.4），仅争议性话题走 LLM
- 传播模拟前预估成本，超 $5 需用户确认
```

### 6.7 验收标准

- [ ] 社交网络平均度 15-25，聚类系数 > 0.3
- [ ] 家庭成员全连接，邻居/同事有合理概率连接
- [ ] 信息传播 Demo：从 100 个核心节点开始，观察 5 轮传播
- [ ] 意见传播后，社区内意见更趋同（量化度量）

---

## 7. Phase 4: 实时感知层

### 7.1 目标

系统自动接入新加坡新闻、政策变化、市场数据，转化为事件注入。

### 7.2 详细任务

| 任务 | 描述 | 天数 |
|------|------|------|
| P4.1 RSS 新闻采集 | 复用 `rss_collector.py`：CNA, ST, Today | 2 |
| P4.2 Gov Data 采集 | 复用 `gov_data_collector.py`：HDB, CPI, unemployment | 2 |
| P4.3 LLM 事件分类 | 新闻 → LLM 评估 → 是否相关 + 六维影响 + target_filter | 2 |
| P4.4 自动注入流水线 | 事件采集 → 评估 → 自动写入 events + memories | 2 |
| P4.5 事件时间线 | Web /events 页面展示自动+手动事件的时间线 | 2 |
| P4.6 感知频率控制 | 每天扫描 2 次新闻，重大事件实时推送 | 1 |
| P4.7 去重与降噪 | 同一事件不同新闻源去重，忽略娱乐/体育等无关新闻 | 1 |

### 7.3 自动感知流水线

```
每天 08:00 + 20:00 自动执行:

RSS Feeds ──┐
            │
Gov APIs ───┤──→ LLM 筛选+分类 ──→ 相关事件 ──→ 影响评估 ──→ 写入 events 表
            │     "这条新闻是否        └─ 不相关     ├─ target_filter
Market ─────┘      影响新加坡居民？"      → 丢弃      ├─ 六维向量
                                                    └─ importance

                                                        │
                                                        ▼
                                              批量写入 agent_memories
                                              （匹配 target_filter 的 agents）
```

### 7.4 新闻分类逻辑

| 类别 | 关键词/规则 | 影响维度 | 典型 target_filter |
|------|-------------|----------|-------------------|
| 房产政策 | HDB, BTO, ABSD, mortgage | economic, psychological | age 25-45, housing_type |
| 就业市场 | layoff, hiring, salary, PMET | economic, psychological | working age, industry |
| 医疗健康 | dengue, COVID, hospital, MediShield | biological, economic | all / age > 60 |
| 交通出行 | MRT, ERP, COE, bus | economic, cognitive | commute_mode, area |
| 教育 | PSLE, university, SkillsFuture | cognitive, economic | age < 30 / parents |
| 金融市场 | STI, interest rate, SGD | economic | income > median |
| 政策变动 | GST, CPF, retirement age, NS | economic, social | varies |

### 7.5 验收标准

- [ ] 每天自动采集 10-50 条新加坡相关新闻
- [ ] LLM 筛选后保留 3-10 条相关事件
- [ ] 自动写入事件表 + 受影响 agent 的记忆
- [ ] Web 时间线可视化所有历史事件

---

## 8. Phase 5: 认知能力——反思与规划

### 8.1 目标

Agent 能够反思自己的经历，形成高阶洞察；能够制定目标和计划。

### 8.2 理论基础

**Stanford Generative Agents (Park 2023)**:
- 反思触发：当 importance 累积超过阈值 → 自动问自己 "最重要的3个高阶问题是什么？"
- 反思输出：比原始记忆更抽象的洞察（如 "我越来越担心退休金不够"）
- 规划：每天生成日程计划，根据事件动态调整

**CoALA Framework**:
- 工作记忆 → 内部推理 → 长期记忆更新
- 信念-欲望-意图 (BDI) 循环

### 8.3 详细任务

| 任务 | 描述 | 天数 |
|------|------|------|
| P5.1 反思触发器 | importance 累积 > 40 → 触发反思 | 2 |
| P5.2 反思生成 | LLM 生成高阶洞察，写入 belief_update 类型记忆 | 3 |
| P5.3 向量记忆 | pgvector 存储 memory embedding，语义检索 | 3 |
| P5.4 检索公式 | score = α·recency + β·relevance + γ·importance | 2 |
| P5.5 目标系统 | Agent 有 current_goals（如 "买房"、"存够退休金"） | 3 |
| P5.6 计划生成 | 基于目标 + 当前状态 → LLM 生成行动计划 | 3 |
| P5.7 计划执行 | 计划影响后续决策（"因为我在攒钱买房，所以不买新手机"） | 2 |
| P5.8 认知验证 | 对比有/无反思的 agent 行为一致性和真实感 | 2 |

### 8.4 反思流程

```
Agent A12345 的记忆流：
  [imp=7] "GST 将涨至 10%"
  [imp=6] "我选择了减少外出用餐"
  [imp=8] "公司宣布裁员 10%"
  [imp=5] "我被问了对经济前景的看法，我选了'悲观'"
  [imp=7] "我决定增加储蓄比例"

  importance 累积 = 7+6+8+5+7 = 33

  再来一条 [imp=8] "利率上涨到 4%"
  importance 累积 = 41 > 阈值 40 → 触发反思

反思 LLM Prompt:
  "以下是你最近的经历。请总结出 3 个最重要的高阶洞察：
   [记忆列表]"

反思输出:
  [belief_update, imp=9] "我对新加坡经济前景越来越悲观，正在主动缩减开支和增加储蓄"
  [belief_update, imp=8] "我的工作可能不安全，需要考虑技能提升或副业"
  [belief_update, imp=7] "高利率让我推迟了买房计划"

这些高阶记忆在后续所有提问中优先被检索到，深刻影响 Agent 的回答。
```

### 8.5 向量检索升级

```sql
-- 启用 pgvector（Supabase 已内置）
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE agent_memories ADD COLUMN embedding vector(384);

-- 语义检索
SELECT *,
  (0.3 * (1.0 / (1.0 + EXTRACT(EPOCH FROM NOW() - created_at) / 86400))  -- recency
   + 0.4 * (1 - (embedding <=> query_embedding))  -- relevance
   + 0.3 * (importance / 10.0))  -- importance
  AS retrieval_score
FROM agent_memories
WHERE agent_id = $1
ORDER BY retrieval_score DESC
LIMIT 10;
```

### 8.6 验收标准

- [ ] 反思生成的洞察比原始记忆更抽象
- [ ] 向量检索的记忆相关性 > 按时间排序（人工评估 > 70% 相关）
- [ ] 有目标的 Agent 决策一致性更高（连续 5 次提问方向一致率 > 80%）
- [ ] 有反思的 Agent vs 无反思的 Agent，人类评估者更难区分前者与真人

---

## 9. Phase 6: 行为校准与自进化

### 9.1 目标

用真实行为数据校准 LLM 的系统性偏差，使 Agent 群体响应更接近真实新加坡人。

### 9.2 背景

**Digital Twins Mega-Study (arxiv 2509.19088)** 发现的 5 大偏差：
1. **刻板化**：LLM 过度用人口统计预测行为
2. **个体化不足**：同画像的不同 Agent 回答太相似
3. **表征偏差**：某些群体被系统性误表征
4. **意识形态偏差**：LLM 偏自由派/进步价值观
5. **超理性**：Agent 太理性，缺乏真人的非理性行为

### 9.3 校准数据源

| 数据 | 来源 | 用途 |
|------|------|------|
| World Values Survey (Singapore) | WVS Wave 7 | 价值观分布校准 |
| GE2025 投票结果 × 选区 | ELD | 政治态度校准 |
| PE2023 投票结果 | ELD | 方向性验证 |
| NUS IPS 调查系列 | IPS | 社会态度校准 |
| SingStat HES 2023 | SingStat | 消费行为校准 |
| MAS 金融素养调查 | MAS | 金融决策校准 |
| 保险渗透率数据 | LIA Singapore | 保险决策校准 |

### 9.4 详细任务

| 任务 | 描述 | 天数 |
|------|------|------|
| P6.1 校准数据收集 | 收集上述 7 个数据源，标准化格式 | 5 |
| P6.2 偏差量化 | 对每个维度，计算 LLM 输出 vs 真实数据的偏差 | 3 |
| P6.3 校准层设计 | 设计 post-hoc 校准函数：LLM 原始输出 → 校准后分布 | 5 |
| P6.4 Temperature 调优 | 不同问题类型的最优 temperature 映射 | 2 |
| P6.5 个体化增强 | 增加噪声注入策略，降低同画像 Agent 的回答相似度 | 3 |
| P6.6 反偏差 Prompt | System prompt 中加入反刻板化指令 | 2 |
| P6.7 校准验证 | 回测 5+ 真实事件，比较校准前后准确率 | 5 |
| P6.8 持续校准管线 | 新真实数据 → 自动更新校准参数 | 3 |

### 9.5 校准层设计

```python
class BehaviorCalibrator:
    """
    Post-hoc 校准层。

    arxiv 2601.06111 的方法：
    将 LLM 的离散选项输出转为概率向量，
    然后用校准函数修正偏差。

    P_calibrated(choice | agent) = f(P_llm(choice | agent), agent.demographics)

    f 的形式：
    - 群体级修正：已知华人 30-40 岁的保险购买率是 65%，
      如果 LLM 给出 80%，则乘以 65/80 = 0.8125 的修正系数
    - Temperature 修正：增加 temperature 降低确定性偏差
    - 噪声注入：对同画像 Agent 加入个体差异噪声
    """
```

### 9.6 验收标准

- [ ] 校准后的群体分布与真实调查数据偏差 < 10pp（5+ 维度）
- [ ] 同画像 Agent 的回答多样性增加（Simpson 多样性指数 > 0.6）
- [ ] 回测 5 个历史事件，方向准确率 > 80%
- [ ] 比例准确率（偏差 < 15pp）在 3+ 事件上达标

---

## 10. Phase 7: 垂直行业应用

### 10.1 目标

基于通用 Digital Twin 平台，开发面向特定行业的深度模块。

### 10.2 垂直一：保险行业

| 功能 | 描述 | Phase 依赖 |
|------|------|-----------|
| 产品需求评估 | 向 Agent 群体推介保险产品，分析购买意愿 | P1 |
| 保单生命周期模拟 | Agent 在不同生命事件下的续保/退保决策 | P2 |
| Claims 模拟 | 基于 health_status + life_event 的理赔触发 | P2 |
| 渠道偏好测试 | 线上 vs 线下 vs agent(代理人) vs bancassurance | P1 |
| 产品定价验证 | 不同定价下的购买率曲线 | P1 |
| 竞品对比测试 | "AIA vs Prudential vs Great Eastern，你选哪个？" | P1 |
| 退保预警模型 | 经济下行 → Agent 退保概率 | P2+P4 |

**数据扩展**:
```sql
-- 保险垂直表（已有框架，需扩展）
CREATE TABLE insurance_policies (
    agent_id TEXT REFERENCES agents(agent_id),
    product_type TEXT,     -- life / health / CI / motor / home
    insurer TEXT,
    premium_monthly NUMERIC,
    sum_assured NUMERIC,
    status TEXT,           -- active / lapsed / surrendered / claimed
    purchase_reason TEXT,  -- 购买原因（LLM 生成）
    lapse_risk NUMERIC,    -- 退保风险评分
    ...
);
```

### 10.3 垂直二：政府政策

| 功能 | 描述 | Phase 依赖 |
|------|------|-----------|
| 政策影响预评估 | GST/CPF/retirement age 调整的全民反应 | P1+P2 |
| BTO 需求预测 | 各区域、各户型的 BTO 申请率预测 | P1 |
| 社会转移支付模拟 | CDC Voucher、GST Voucher 的影响 | P2 |
| 人口老龄化模拟 | 10 年人口结构变化 + 对政策的需求 | P5 |
| 舆论传播模拟 | 政策发布后的民意变化（需社交网络） | P3 |
| 选区分析 | 不同选区居民对政策的态度差异 | P1+P6 |

### 10.4 垂直三：银行/金融

| 功能 | 描述 | Phase 依赖 |
|------|------|-----------|
| 零售产品需求 | 信用卡/贷款/投资产品的购买意愿 | P1 |
| 消费行为模拟 | 经济事件下的消费-储蓄决策 | P2 |
| 投资偏好测试 | 不同风险等级产品的分布 | P1 |
| 客群细分 | 基于 agent 属性的自然聚类 | P0 |
| 利率敏感度分析 | 利率变化对贷款/储蓄行为的影响 | P2+P4 |

### 10.5 验收标准

- [ ] 每个垂直至少有 3 个可运行的 Demo 场景
- [ ] 结果包含行业特定的分析维度
- [ ] 与行业 KPI 对齐（如保险渗透率、BTO 申请比等）

---

## 11. Phase 8: 规模化与性能

### 11.1 目标

支持更大规模模拟（5000+/次）、更快响应（< 1 分钟）、更低成本。

### 11.2 详细任务

| 任务 | 描述 | 天数 |
|------|------|------|
| P8.1 本地模型部署 | Llama 3 70B 或 Qwen2 72B 本地部署 | 5 |
| P8.2 vLLM 推理优化 | vLLM 批量推理，吞吐 > 5K tok/s | 3 |
| P8.3 异步并发架构 | asyncio + 连接池，并发 20-50 路 LLM 调用 | 3 |
| P8.4 结果缓存 | 同一问题+同一 agent → 缓存结果（可配置 TTL） | 2 |
| P8.5 增量更新 | 只更新受事件影响的 agent 记忆，不全量刷新 | 2 |
| P8.6 数据库优化 | 分区表、物化视图、查询优化 | 3 |
| P8.7 监控告警 | Grafana 监控 LLM 延迟、成本、错误率 | 2 |

### 11.3 本地模型 vs API 对比

| 维度 | DeepSeek API | 本地 Llama 70B (4×A100) |
|------|-------------|------------------------|
| 延迟 | 500ms-2s/请求 | 200-500ms/请求 |
| 吞吐 | ~60 RPM（限速） | ~5K tok/s（无限制） |
| 1000 agents | ~3 分钟 | ~30 秒 |
| 月成本 | $50-200（按量） | $8,000（固定） |
| 临界点 | < 5000 次/月 用 API 更划算 | > 5000 次/月 用本地更划算 |

### 11.4 验收标准

- [ ] 1000 agent 模拟 < 2 分钟完成
- [ ] 本地模型质量与 DeepSeek API 质量偏差 < 10%（人工评估）
- [ ] 系统 uptime > 99%

---

## 12. 数据治理演进

### 12.1 各 Phase 的数据治理要求

| Phase | 数据治理新增要求 |
|-------|-----------------|
| **P0** | T0+T1 数据全部硬编码验证通过；148K 入库完整性 100% |
| **P1** | 采样代表性验证自动化；调研结果 JSON 解析率 > 95% |
| **P2** | 记忆表容量监控；事件注入审计日志 |
| **P3** | 社交网络一致性检查（无孤立节点、无自环） |
| **P4** | 新闻源可用性监控；事件去重准确率 > 90% |
| **P5** | 向量索引质量监控；反思内容合理性抽检 |
| **P6** | 校准数据版本管理；校准参数变更审计 |
| **P7** | 行业数据合规审查（客户数据不进系统） |
| **P8** | 本地模型输出质量监控；与 API 基线对比 |

### 12.2 数据治理框架更新（与 data_governance_framework.md 对齐）

随着系统演进，数据资产从 Phase 0 的 ~15 个增长到 Phase 7 的 ~40+ 个。数据治理框架需要在每个 Phase 完成时更新：

1. **新数据源接入**：按检查清单（T0-T3 分级、缓存策略、断供预案、验证规则）
2. **新维度验证**：加入联合分布验证、相关结构验证
3. **新 API 监控**：加入可用性监控和降级策略
4. **数据血缘更新**：新字段追溯到数据源

---

## 13. 技术债务管理

### 13.1 已知技术债务

| 债务 | 产生原因 | 影响 | 计划偿还 |
|------|----------|------|----------|
| V1/V2 合成脚本未清理 | 快速迭代 | 代码混乱 | P0 时移入 archive/ |
| 静态 HTML 前端 | 原型快速搭建 | 无法维护 | P1 用 Next.js 替代 |
| API Key 硬编码 | 原型阶段 | 安全风险 | P0 迁移到环境变量 |
| 无单元测试 | 快速迭代 | 回归风险 | P1 同步补测试 |
| 无 CI/CD | 手动部署 | 部署风险 | P1 后配置 GitHub Actions |
| pipeline/ 模块未使用 | 提前设计 | 代码浪费 | P0 归档，P4 时复用 |

### 13.2 每 Phase 的测试要求

| Phase | 单元测试 | 集成测试 | 端到端测试 |
|-------|---------|---------|-----------|
| P0 | 增强函数 + CPT 采样 | 148K 全量合成 | 入库 + 查询 |
| P1 | 采样 + 聚合 | Job 全流程 | Web → 结果 |
| P2 | 记忆 CRUD | 事件→记忆→影响 | 三轮连续实验 |
| P3 | 图生成 + 传播 | 端到端传播模拟 | Web 可视化 |
| P4 | RSS 解析 + 分类 | 自动感知管线 | 24h 无人运行 |
| P5 | 反思生成 + 向量检索 | 完整认知循环 | 与 P2 对比评估 |
| P6 | 校准函数 | 校准前后对比 | 回测 5 事件 |

### 13.3 代码质量标准

- Python: `ruff` 格式化 + `mypy` 类型检查
- TypeScript: `eslint` + `prettier`
- 提交前: pre-commit hooks 自动检查
- 每 Phase 完成时: 代码审查 + 文档更新

---

## 14. 团队与资源规划

### 14.1 各 Phase 人力需求

| Phase | 全栈工程师 | AI/ML 工程师 | 数据工程师 | 总人天 |
|-------|-----------|-------------|-----------|--------|
| P0 | 1 | 0 | 0 | 7 |
| P1 | 1 | 0 | 0 | 15 |
| P2 | 1 | 0 | 0 | 10 |
| P3 | 1 | 0.5 | 0 | 20 |
| P4 | 0.5 | 0 | 0.5 | 15 |
| P5 | 0.5 | 1 | 0 | 20 |
| P6 | 0 | 1 | 1 | 30 |
| P7 | 1 | 0.5 | 0.5 | 持续 |
| P8 | 1 | 1 | 0 | 20 |

**P0-P2 只需 1 个全栈工程师。** P3 开始需要 AI/ML 专长。P6 需要数据工程师处理校准数据。

### 14.2 基础设施成本演进

| Phase | Supabase | LLM API | GPU | 其他 | 月总计 |
|-------|----------|---------|-----|------|--------|
| P0 | $25 | $0 | $0 | $0 | **$25** |
| P1 | $25 | $20 | $0 | $0 | **$45** |
| P2 | $25 | $30 | $0 | $0 | **$55** |
| P3 | $25 | $80 | $0 | $0 | **$105** |
| P4 | $25 | $50 | $0 | $30 API | **$105** |
| P5 | $25 | $150 | $0 | $0 | **$175** |
| P6 | $25 | $100 | $0 | 数据$200 | **$325** |
| P7 | $25 | $200 | $0 | $0 | **$225** |
| P8 | $25 | $0 | $8,000 | $0 | **$8,025** |

**P0-P6 总成本 < $400/月。P8（本地 GPU）是唯一大跳跃。**

---

## 15. 风险登记册

| ID | 风险 | 概率 | 影响 | Phase | 缓解策略 |
|----|------|------|------|-------|----------|
| R1 | NVIDIA 148K 分布与 Census 偏差大 | 中 | 高 | P0 | 增补时用 Census CPT 校准 + 验证 |
| R2 | DeepSeek API 不稳定/下线 | 低 | 高 | P1+ | 备选 Gemini Flash + 规则引擎降级 |
| R3 | LLM 响应质量不一致 | 中 | 中 | P1+ | temperature 调优 + 异常重试 + 大样本平滑 |
| R4 | Supabase Free plan 存储不够 | 高 | 低 | P0 | 升 Pro ($25/月) |
| R5 | 148K agents 上传超时 | 中 | 低 | P0 | 分批 500行/批 + 重试 |
| R6 | 记忆膨胀导致存储爆炸 | 中 | 中 | P2+ | 容量上限 + 定期清理 |
| R7 | 社交网络生成计算量过大 | 中 | 中 | P3 | 分区生成 + 稀疏存储 |
| R8 | RSS 新闻源改版/下线 | 中 | 低 | P4 | 多源冗余 + 定期检查 |
| R9 | 向量检索在 Supabase 上性能不够 | 低 | 中 | P5 | pgvector HNSW 索引 + 分批查询 |
| R10 | 校准数据获取困难（WVS 等） | 中 | 高 | P6 | 用公开数据（选举结果、GHS）先做粗校准 |
| R11 | 本地 GPU 成本过高 | 高 | 中 | P8 | 延迟 P8，继续用 API；或用 8B 模型替代 |
| R12 | LLM 刻板化偏差无法消除 | 高 | 高 | 全程 | 定位为"群体趋势"而非"个体预测"；校准层 |
| R13 | 竞争对手（Synthetic Users 等） | 中 | 中 | 全程 | 新加坡特化 + 数学严谨性 + 记忆系统 |
| R14 | 数据合规风险（PDPA） | 低 | 高 | 全程 | 合成数据无真实个人信息；compliance 模块持续审计 |

---

## 16. 成功指标

### 16.1 技术指标

| 指标 | P1 目标 | P3 目标 | P6 目标 |
|------|---------|---------|---------|
| Agent 总数 | 148K | 148K | 148K |
| 单次模拟延迟（200人） | < 5 min | < 3 min | < 1 min |
| 单次模拟成本（200人） | < $0.10 | < $0.10 | < $0.05 |
| JSON 解析成功率 | > 95% | > 98% | > 99% |
| 边际分布 SRMSE | < 0.20 | < 0.15 | < 0.10 |
| 回测方向准确率 | > 60% | > 70% | > 80% |
| 回测比例偏差 | < 20pp | < 15pp | < 10pp |

### 16.2 产品指标

| 指标 | P1 目标 | P3 目标 | P7 目标 |
|------|---------|---------|---------|
| Demo 场景数 | 3 | 10 | 20+ |
| 可查询维度 | 8 | 12 | 15+ |
| 用户可操作功能 | 提问+浏览 | +事件+记忆 | +垂直模块 |
| 系统 uptime | 90% | 95% | 99% |

### 16.3 商业指标（Phase 7+）

| 指标 | 目标 |
|------|------|
| 付费客户数 | 3-5 |
| 每客户月费 | $500-2000 |
| 客户满意度 | > 80% |
| 报告准确率（客户评估） | > 70% 认为"有价值" |

---

## 附录 A: 与全球 AI Agent 标准的对齐

| 维度 (CoALA/Stanford) | Phase 覆盖 | 状态 |
|-----------------------|-----------|------|
| Profile（身份画像） | P0 | 全球领先 |
| Memory（持久记忆） | P2 | MVP 简版 → P5 向量检索 |
| Interaction（社交互动） | P3 | 小世界网络 + 对话 |
| Perception（环境感知） | P4 | RSS + Gov API |
| Reflection（反思） | P5 | Stanford 方法复现 |
| Planning（规划） | P5 | BDI 循环 |
| Learning（学习进化） | P6 | 行为校准层 |
| Emotion（情绪建模） | P2 (基础) | emotion_delta in responses |
| Temporal（时间感知） | P0 (life_phase) | 静态 → P5 动态化 |

**Phase 6 完成后，覆盖 9/10 维度，达到全球研究前沿水平。**

---

## 附录 B: 关键依赖版本

| 依赖 | 当前版本 | 用途 |
|------|----------|------|
| Python | 3.11+ | 核心引擎 |
| Supabase | Pro plan | 数据库 + Auth + Realtime |
| Next.js | 14+ | Web 前端 |
| DeepSeek API | v1 | LLM 推理 |
| pandas | 2.0+ | 数据处理 |
| scipy | 1.11+ | 统计检验 |
| numpy | 1.24+ | 数值计算 |
| pgvector | 0.5+ (Phase 5) | 向量检索 |
| networkx | 3.0+ (Phase 3) | 社交网络 |

---

## 附录 C: 文档体系

| 文档 | 位置 | 更新频率 |
|------|------|----------|
| 系统架构 V3 | `docs/system_architecture_v3.md` | 每 Phase 更新 |
| 研发规划路线图 | `docs/rd_roadmap.md`（本文档） | 每 Phase 更新 |
| 数据治理框架 | `docs/data_governance_framework.md` | 每 Phase 更新 |
| Agent 合成技术文档 | `docs/technical_architecture_agent_synthesis.md` | P0 后更新为 V3 |
| API 文档 | `docs/api_reference.md` | P1 创建 |
| 垂直行业手册 | `docs/vertical_*.md` | P7 创建 |
