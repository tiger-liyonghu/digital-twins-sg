# Digital Twins Singapore — System Architecture V3

> Status: **DRAFT — 待审阅**
> Author: System Architect
> Date: 2026-03-06

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **148K First** | NVIDIA 148K 人群是底座，不是附加品。所有统计维度增补到 148K 上 |
| **Supabase Only** | 单一后端。PostgreSQL + Edge Functions + Realtime。不引入额外服务器 |
| **按需采样** | 每次模拟按需抽取 N 人（50/200/1000），不跑全量。控制成本和延迟 |
| **记忆驱动** | Agent 有持久记忆。事件→记忆→影响后续决策。这是核心差异化 |
| **三层决策不变** | Layer 1 规则 → Layer 2 概率 → Layer 3 LLM。已验证的架构保留 |
| **渐进式复杂度** | 先跑通最简路径，再逐步加认知能力（反思、互动、学习） |

---

## 2. 系统全景

```
                    ┌─────────────────────────────────────┐
                    │           Web Frontend               │
                    │     Next.js (Vercel, $0/月)          │
                    │                                      │
                    │  /ask       提问 → 创建模拟任务       │
                    │  /results   结果仪表板 + 人群分析      │
                    │  /agents    Agent 浏览器（148K）       │
                    │  /events    事件注入 + 历史事件线       │
                    │  /compare   多轮对比（记忆效应）        │
                    └──────────────┬──────────────────────┘
                                   │ Supabase JS SDK
                    ┌──────────────▼──────────────────────┐
                    │         Supabase (PostgreSQL)         │
                    │                                      │
                    │  ┌─────────┐ ┌──────────┐ ┌───────┐ │
                    │  │ agents  │ │ memories │ │ jobs  │ │
                    │  │ 148K    │ │          │ │       │ │
                    │  └─────────┘ └──────────┘ └───────┘ │
                    │  ┌─────────┐ ┌──────────┐ ┌───────┐ │
                    │  │ events  │ │reactions │ │h/hold │ │
                    │  └─────────┘ └──────────┘ └───────┘ │
                    │                                      │
                    │  Edge Functions:                      │
                    │    create-job  → 创建模拟任务          │
                    │    inject-event → 注入事件             │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │       Simulation Runner               │
                    │       (本地 Python 进程)               │
                    │                                      │
                    │  Poll jobs → Sample → Build Persona   │
                    │  → 3-Layer Decision → Write Results   │
                    │  Heartbeat: 每 60s 写入 runner_status │
                    │                                      │
                    │  ┌─────────────────────────────────┐ │
                    │  │ engine/                          │ │
                    │  │  synthesis/  models/  rules/     │ │
                    │  │  llm/       compliance/          │ │
                    │  └─────────────────────────────────┘ │
                    └──────────────┬──────────────────────┘
                                   │
                              DeepSeek API
                           ($0.001/K tokens)
```

---

## 3. 数据模型重构

### 3.1 核心变化：从 "合成 20K" 到 "增强 148K"

```
旧流程（V2）:
  Census 数据 → IPF 生成 20K 空壳 → Bayesian Network 填属性
  → Cholesky 采样 Big Five → 家庭构建 → NVIDIA 叙事嫁接

新流程（V3）:
  NVIDIA 148K parquet（已有：age, gender, education, planning_area,
                       marital_status, 6个叙事字段）
  → 统计增强引擎（复用现有 math_core + sg_distributions）
  → 按 agent 已有属性，从 CPT 采样缺失维度
  → 输出 148K 完整 Agent → 入库 Supabase
```

### 3.2 NVIDIA 148K 已有字段

```
直接可用（无需合成）:
  ├── age, sex, education_level, planning_area
  ├── marital_status, race
  ├── persona (综合叙事)
  ├── professional_persona (职业叙事)
  ├── cultural_background (文化背景)
  ├── sports_persona, arts_persona, travel_persona
  ├── culinary_persona
  ├── hobbies_and_interests
  ├── career_goals_and_ambitions
  ├── occupation, industry
  └── religion (部分)
```

### 3.3 需要增补的维度

```
从 CPT 采样（复用现有引擎）:
  ├── monthly_income         ← build_income_cpt(education, age, gender)
  ├── housing_type           ← build_housing_income_cpt(income, area)
  ├── residency_status       ← RESIDENCY_MARGINAL + area-based adjustment
  ├── health_status          ← build_health_age_cpt(age, gender)
  ├── ns_status              ← deterministic rule (age + gender + residency)
  ├── commute_mode           ← rule-based (area + income)
  ├── has_vehicle            ← logistic (income, housing_type)
  └── household_id/role      ← household_builder (marital + age + area)

从 Cholesky 采样（复用 personality_init.py）:
  ├── big5_o/c/e/a/n         ← SE Asian baseline + age/gender adjustment
  └── risk_appetite, political_leaning, social_trust, religious_devotion

从规则引擎（复用 life_rules.py）:
  ├── life_phase             ← determine_life_phase(age, health, ns, children)
  ├── agent_type             ← determine_agent_type(age)
  └── age_group              ← age bin mapping

从 CPF 模型（复用 cpf_model.py）:
  └── cpf_oa/sa/ma/ra        ← simulate_lifetime_cpf(age, income, residency)
```

### 3.4 数据库 Schema（V3）

```sql
-- ============================================================
-- V3 SCHEMA: 148K Agents + Memory + Jobs
-- ============================================================

-- [RESTRUCTURED] agents 表 — 148K 完整人群
CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,            -- NV000001..NV148000

    -- === NVIDIA 原始字段（直接导入）===
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,                  -- Male/Female
    ethnicity TEXT NOT NULL,               -- Chinese/Malay/Indian/Others
    education_level TEXT,
    planning_area TEXT NOT NULL,
    marital_status TEXT DEFAULT 'Single',
    occupation TEXT DEFAULT '',
    industry TEXT DEFAULT '',
    religion TEXT DEFAULT '',

    -- NVIDIA 叙事（完整保留，不截断）
    persona TEXT DEFAULT '',
    professional_persona TEXT DEFAULT '',
    cultural_background TEXT DEFAULT '',
    sports_persona TEXT DEFAULT '',
    arts_persona TEXT DEFAULT '',
    travel_persona TEXT DEFAULT '',
    culinary_persona TEXT DEFAULT '',
    hobbies_and_interests TEXT DEFAULT '',
    career_goals TEXT DEFAULT '',

    -- === 统计增补字段（我们的引擎生成）===
    residency_status TEXT DEFAULT 'Citizen',
    monthly_income INTEGER DEFAULT 0,
    housing_type TEXT,
    health_status TEXT DEFAULT 'Healthy',
    ns_status TEXT DEFAULT 'Not_Applicable',
    commute_mode TEXT DEFAULT 'MRT',
    has_vehicle BOOLEAN DEFAULT FALSE,

    -- 家庭
    household_id TEXT,
    household_role TEXT DEFAULT '',
    num_children INTEGER DEFAULT 0,

    -- 财务（CPF 模型生成）
    cpf_oa INTEGER DEFAULT 0,
    cpf_sa INTEGER DEFAULT 0,
    cpf_ma INTEGER DEFAULT 0,
    cpf_ra INTEGER DEFAULT 0,
    monthly_savings INTEGER DEFAULT 0,

    -- 人格（Cholesky 采样）
    big5_o NUMERIC(3,2) DEFAULT 3.0,
    big5_c NUMERIC(3,2) DEFAULT 3.0,
    big5_e NUMERIC(3,2) DEFAULT 3.0,
    big5_a NUMERIC(3,2) DEFAULT 3.0,
    big5_n NUMERIC(3,2) DEFAULT 3.0,

    -- 态度
    risk_appetite NUMERIC(3,2) DEFAULT 3.0,
    political_leaning NUMERIC(3,2) DEFAULT 3.0,
    social_trust NUMERIC(3,2) DEFAULT 3.0,
    religious_devotion NUMERIC(3,2) DEFAULT 3.0,

    -- 生命状态
    life_phase TEXT DEFAULT 'establishment',
    agent_type TEXT DEFAULT 'active',
    age_group TEXT,
    is_alive BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引：支持高效采样
CREATE INDEX idx_agents_area ON agents(planning_area);
CREATE INDEX idx_agents_age_gender ON agents(age, gender);
CREATE INDEX idx_agents_ethnicity ON agents(ethnicity);
CREATE INDEX idx_agents_income ON agents(monthly_income);
CREATE INDEX idx_agents_housing ON agents(housing_type);
CREATE INDEX idx_agents_education ON agents(education_level);
CREATE INDEX idx_agents_life_phase ON agents(life_phase);

-- [NEW] 记忆表 — Agent 持久化记忆
CREATE TABLE agent_memories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),

    memory_type TEXT NOT NULL CHECK (memory_type IN (
        'experience',     -- 经历过的事件（"GST涨了，我减少了外出用餐"）
        'decision',       -- 做过的决策（"我选择不买这个保险"）
        'observation',    -- 观察到的信息（"最近很多人被裁员"）
        'belief_update'   -- 信念更新（"我现在觉得经济前景不好"）
    )),

    content TEXT NOT NULL,
    importance INTEGER DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),

    -- 来源追溯
    source_job_id UUID,          -- 哪次模拟产生的
    source_event_id UUID,        -- 哪个事件触发的

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mem_agent ON agent_memories(agent_id);
CREATE INDEX idx_mem_agent_importance ON agent_memories(agent_id, importance DESC);
CREATE INDEX idx_mem_agent_time ON agent_memories(agent_id, created_at DESC);

-- [NEW] 模拟任务表
CREATE TABLE simulation_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- 输入
    title TEXT NOT NULL,                    -- "AIA 重疾险市场调研"
    question TEXT NOT NULL,
    options JSONB NOT NULL,                 -- ["选项A", "选项B", ...]
    context TEXT DEFAULT '',

    -- 采样配置
    sample_size INTEGER DEFAULT 100,
    sampling_method TEXT DEFAULT 'stratified',  -- stratified / random / targeted
    target_filter JSONB DEFAULT '{}',       -- {"age_min":25,"age_max":45,"housing":"Condo"}

    -- 执行状态
    status TEXT DEFAULT 'pending' CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled'
    )),
    progress INTEGER DEFAULT 0,             -- 0-100

    -- 已采样的 agent IDs
    sampled_agent_ids JSONB DEFAULT '[]',

    -- 聚合结果
    result JSONB,                            -- 完整分析报告

    -- 成本追踪
    agents_responded INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(8,4) DEFAULT 0,

    -- 时间
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON simulation_jobs(status);
CREATE INDEX idx_jobs_created ON simulation_jobs(created_at DESC);

-- [NEW] Agent 响应表（每个 agent 对每个 job 的响应）
CREATE TABLE agent_responses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES simulation_jobs(id),
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),

    -- LLM 响应
    choice TEXT,
    reasoning TEXT,
    willingness_score INTEGER,
    key_concern TEXT,

    -- 情绪变化
    emotion_delta JSONB,

    -- 决策层
    decision_layer TEXT DEFAULT 'llm',      -- rule / probability / llm

    -- 成本
    tokens_used INTEGER DEFAULT 0,
    cost_usd NUMERIC(6,4) DEFAULT 0,
    model_used TEXT DEFAULT 'deepseek-chat',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_resp_job ON agent_responses(job_id);
CREATE INDEX idx_resp_agent ON agent_responses(agent_id);

-- [RESTRUCTURED] 事件表
CREATE TABLE events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    title TEXT NOT NULL,                    -- "GST 涨至 10%"
    description TEXT,
    event_type TEXT NOT NULL,               -- macro / policy / market / social / personal
    source TEXT DEFAULT 'manual',           -- manual / rss / api

    -- 六维影响向量 (-5 to +5)
    impact_biological NUMERIC(3,1) DEFAULT 0,
    impact_psychological NUMERIC(3,1) DEFAULT 0,
    impact_social NUMERIC(3,1) DEFAULT 0,
    impact_economic NUMERIC(3,1) DEFAULT 0,
    impact_cognitive NUMERIC(3,1) DEFAULT 0,
    impact_spiritual NUMERIC(3,1) DEFAULT 0,

    -- 影响范围
    target_filter JSONB DEFAULT '{}',       -- 哪些人受影响

    -- 元数据
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- [KEEP] 家庭表
CREATE TABLE households (
    household_id TEXT PRIMARY KEY,
    planning_area TEXT,
    housing_type TEXT,
    household_size INTEGER DEFAULT 1,
    household_income INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.5 存储估算

| 表 | 行数 | 每行大小 | 总计 |
|---|---|---|---|
| agents | 148,000 | ~3 KB（含叙事文本） | ~450 MB |
| agent_memories | 初始 0 → 增长 | ~200 bytes | 按需增长 |
| simulation_jobs | 按使用量 | ~2 KB | < 1 MB |
| agent_responses | 按使用量 | ~500 bytes | 按需增长 |
| events | 按使用量 | ~1 KB | < 1 MB |
| households | ~50,000 | ~200 bytes | ~10 MB |
| **总计** | | | **~500 MB 起步** |

**结论：Supabase Pro ($25/月, 8GB) 完全足够。** Free plan (500MB) 也可以起步，但会很紧。

---

## 4. 模块架构重构

### 4.1 目录结构（V3）

```
digital-twins-sg/
├── engine/                          # 核心引擎（纯 Python，不依赖 web 框架）
│   ├── core/
│   │   └── agent.py                 # [UPDATE] Agent 数据模型 + NVIDIA 字段
│   │
│   ├── synthesis/                   # 人群合成
│   │   ├── augment_nvidia.py        # [NEW] 148K 增强主引擎
│   │   ├── math_core.py             # [KEEP] IPF / 控制舍入 / 验证
│   │   ├── sg_distributions.py      # [KEEP] Census 分布 + CPT
│   │   ├── personality_init.py      # [KEEP] Big Five + 态度
│   │   ├── household_builder.py     # [KEEP] 家庭构建
│   │   └── synthesis_gate.py        # [UPDATE] 验证 148K 而非 20K
│   │
│   ├── simulation/                  # [RESTRUCTURED] 模拟运行
│   │   ├── sampler.py               # [NEW] 采样引擎（分层/随机/定向）
│   │   ├── persona_builder.py       # [NEW] 富 Persona Prompt 构建
│   │   ├── memory_manager.py        # [NEW] 记忆读写 + 检索
│   │   ├── job_runner.py            # [NEW] 模拟任务执行器
│   │   └── aggregator.py            # [NEW] 响应聚合 + 统计分析
│   │
│   ├── decision/                    # [RENAMED from llm/ + rules/ + models/]
│   │   ├── layer1_rules.py          # [KEEP] 确定性规则
│   │   ├── layer2_probability.py    # [KEEP] 概率模型
│   │   ├── layer3_llm.py            # [UPDATE] LLM 引擎 + 增强 prompt
│   │   └── cpf_model.py             # [KEEP] CPF 数学模型
│   │
│   ├── compliance/                  # [KEEP] 合规与治理
│   │   ├── privacy_engine.py
│   │   ├── ai_governance.py
│   │   └── validation_framework.py
│   │
│   └── db/                          # [NEW] 数据库层
│       ├── supabase_client.py       # Supabase 连接 + 通用操作
│       ├── agent_repo.py            # Agent CRUD + 采样查询
│       ├── memory_repo.py           # 记忆 CRUD + 检索
│       ├── job_repo.py              # Job CRUD + 状态管理
│       └── event_repo.py            # 事件 CRUD
│
├── scripts/                         # 可执行脚本
│   ├── 01_augment_148k.py           # [NEW] 主脚本：NVIDIA 148K → 增强
│   ├── 02_validate_population.py    # [UPDATE] 验证 148K
│   ├── 03_seed_supabase.py          # [UPDATE] 上传 148K 到 Supabase
│   ├── 04_run_simulation.py         # [NEW] 模拟运行器（poll jobs or CLI）
│   └── 05_demo_scenarios.py         # [NEW] Demo 场景合集
│
├── web/                             # [NEW] Next.js 前端
│   ├── app/
│   │   ├── page.tsx                 # 首页
│   │   ├── ask/page.tsx             # 提问界面
│   │   ├── jobs/[id]/page.tsx       # 结果页
│   │   ├── agents/page.tsx          # Agent 浏览器
│   │   ├── agents/[id]/page.tsx     # Agent 详情
│   │   └── events/page.tsx          # 事件管理
│   ├── lib/
│   │   └── supabase.ts              # Supabase JS client
│   └── components/
│       ├── AskForm.tsx              # 提问表单
│       ├── ResultDashboard.tsx      # 结果图表
│       ├── AgentCard.tsx            # Agent 卡片
│       └── DemographicChart.tsx     # 人口统计图
│
├── supabase/
│   └── migrations/
│       └── 20260306000000_v3.sql    # V3 Schema
│
├── data/
│   ├── nvidia_personas_singapore.parquet
│   ├── census/
│   ├── output/
│   └── rules/
│       └── life_ontology.yaml
│
└── docs/
    ├── system_architecture_v3.md    # 本文档
    ├── technical_architecture_agent_synthesis.md
    └── data_governance_framework.md
```

### 4.2 模块依赖关系

```
                    ┌──────────────┐
                    │  scripts/*   │  入口脚本
                    └──────┬───────┘
                           │
              ┌────────────┼──────────────┐
              ▼            ▼              ▼
     ┌────────────┐ ┌───────────┐ ┌──────────────┐
     │ synthesis/ │ │simulation/│ │ compliance/  │
     │            │ │           │ │              │
     │ augment    │ │ sampler   │ │ privacy      │
     │ math_core  │ │ persona   │ │ governance   │
     │ sg_dist    │ │ memory    │ │ validation   │
     │ personality│ │ job_runner│ │              │
     │ household  │ │ aggregator│ │              │
     └─────┬──────┘ └─────┬─────┘ └──────────────┘
           │               │
           │        ┌──────┼──────┐
           │        ▼      ▼      ▼
           │  ┌──────┐┌───────┐┌─────┐
           │  │ L1   ││ L2    ││ L3  │   decision/
           │  │rules ││ prob  ││ llm │
           │  └──────┘└───────┘└──┬──┘
           │                      │
           │                      ▼
           │               DeepSeek API
           │
           └──────────┬───────────┘
                      ▼
               ┌─────────────┐
               │    db/      │  数据库层
               │  supabase   │
               │  repos      │
               └──────┬──────┘
                      ▼
               Supabase PostgreSQL
```

---

## 5. 关键流程设计

### 5.1 人群合成流程（一次性）

```
┌─────────────────────────────────────────────────────────┐
│ Script: 01_augment_148k.py                               │
│                                                          │
│ 1. 读取 nvidia_personas_singapore.parquet (148K)          │
│    ↓                                                     │
│ 2. 字段映射 & 标准化                                       │
│    sex → gender (Male→M, Female→F)                       │
│    race → ethnicity                                      │
│    education_level → 标准化到我们的 7 级                    │
│    planning_area → 标准化到 28 个区                        │
│    ↓                                                     │
│ 3. 统计增补（按已有属性从 CPT 采样）                         │
│    for each agent:                                       │
│      income = sample(build_income_cpt(edu, age, gender)) │
│      housing = sample(build_housing_cpt(income, area))   │
│      residency = sample(RESIDENCY_MARGINAL, age_adj)     │
│      health = sample(build_health_cpt(age, gender))      │
│    ↓                                                     │
│ 4. 人格 & 态度（Cholesky 批量采样）                         │
│    big5 = PersonalityInitializer.batch_sample(148K)      │
│    attitudes = AttitudeInitializer.derive(big5, age)     │
│    ↓                                                     │
│ 5. 家庭构建                                               │
│    households = HouseholdBuilder.build(agents, area)     │
│    ↓                                                     │
│ 6. CPF 初始化                                             │
│    cpf = CPFModel.init_balances(age, income, residency)  │
│    ↓                                                     │
│ 7. 生命状态                                               │
│    life_phase = determine_life_phase(...)                 │
│    agent_type = determine_agent_type(age)                │
│    ns_status = determine_ns(age, gender, residency)      │
│    ↓                                                     │
│ 8. 验证（复用 synthesis_gate.py）                          │
│    SynthesisQualityGate.validate(agents_148k)            │
│    ↓                                                     │
│ 9. 输出 agents_148k_enriched.csv (或直接入库)              │
└─────────────────────────────────────────────────────────┘
```

**关键设计：不用 IPF。**

V2 用 IPF 是因为要从零生成人群，需要 4D 联合分布。V3 人群已经存在（NVIDIA 148K 本身就是按 Census 分布生成的），我们只需要**条件采样缺失维度**。IPF 仍保留在代码中用于验证（检验增补后的联合分布是否合理）。

### 5.2 模拟执行流程

```
┌──────────────────────────────────────────────────────────┐
│ 用户在 Web 端 /ask 页面提交问题                             │
│                                                           │
│   题目: "GST涨到10%，你会减少消费吗？"                       │
│   选项: [减少很多, 减少一些, 不变, 增加消费]                  │
│   样本量: 200                                              │
│   筛选: {"age_min": 18, "income_max": 10000}               │
│                                                           │
│   → 写入 simulation_jobs 表 (status = pending)             │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│ Simulation Runner (本地 Python，轮询 pending jobs)          │
│                                                           │
│ STEP 1: 采样                                               │
│   sampler.stratified_sample(                               │
│     n=200,                                                 │
│     filter={"age_min": 18, "income_max": 10000},           │
│     strata=["age_group", "gender", "ethnicity"]            │
│   )                                                        │
│   → 200 agent_ids                                          │
│                                                           │
│ STEP 2: 构建 Persona（并行预取）                             │
│   for each agent_id:                                       │
│     agent = agent_repo.get(agent_id)                       │
│     memories = memory_repo.get_recent(agent_id, limit=10)  │
│     persona = persona_builder.build(agent, memories)       │
│                                                           │
│ STEP 3: 三层决策                                            │
│   for each agent:                                          │
│     # Layer 1: 规则检查（是否有确定性答案）                    │
│     rule_result = layer1.check(agent, question)            │
│     if rule_result: → 直接记录，跳过 LLM                    │
│                                                           │
│     # Layer 2: 概率预判（倾向性）                             │
│     prior = layer2.estimate(agent, question)               │
│                                                           │
│     # Layer 3: LLM 推理                                    │
│     response = layer3.ask(                                 │
│       persona=persona,                                     │
│       question=question,                                   │
│       options=options,                                     │
│       context=context + prior_hint                         │
│     )                                                      │
│     → 写入 agent_responses                                  │
│     → 写入 agent_memories（"我被问了X，我选了Y"）             │
│                                                           │
│ STEP 4: 聚合分析                                            │
│   result = aggregator.analyze(                              │
│     agents=sampled_agents,                                 │
│     responses=all_responses,                               │
│     breakdowns=["age_group","income_band","ethnicity",      │
│                 "housing_type","education","planning_area"] │
│   )                                                        │
│   → 更新 simulation_jobs.result = result                    │
│   → status = completed                                     │
└──────────────────────────────────────────────────────────┘
```

### 5.3 记忆系统设计

```
记忆生命周期：

  事件注入                  模拟运行                 再次模拟
     │                        │                        │
     ▼                        ▼                        ▼
  ┌──────┐              ┌──────────┐            ┌──────────┐
  │Event │─────────────→│Agent被问  │           │Agent被问   │
  │"GST涨"│             │"你会买保险│           │同一个问题   │
  └──────┘              │ 吗？"     │           │           │
     │                  └────┬─────┘            └─────┬────┘
     │                       │                        │
     ▼                       ▼                        ▼
  写入记忆              LLM 看到记忆              LLM 看到更多记忆
  ┌─────────────┐      ┌──────────────┐        ┌──────────────┐
  │ experience: │      │ persona +    │        │ persona +     │
  │ "GST将涨到  │      │ "GST涨了..." │        │ "GST涨了..."  │
  │  10%"       │      │ → 影响决策   │        │ "我上次选了不买"│
  │ importance:7│      └──────┬───────┘        │ → 态度一致性   │
  └─────────────┘             │                └──────┬───────┘
                              ▼                       ▼
                         写入记忆                  写入记忆
                         ┌───────────┐           ┌────────────┐
                         │ decision: │           │ decision:   │
                         │ "选了不买" │           │ "仍然不买"  │
                         │ import: 6 │           │ import: 5   │
                         └───────────┘           └────────────┘
```

**记忆检索策略（衰减加权版）：**

```python
from datetime import datetime, timezone

def memory_retrieval_score(memory: dict, now: datetime) -> float:
    """衰减函数：recency × importance 加权。受 Stanford Generative Agents 启发。"""
    created = datetime.fromisoformat(memory["created_at"])
    hours_ago = (now - created).total_seconds() / 3600
    recency = 1.0 / (1.0 + hours_ago / 24)   # 24h 半衰
    importance_norm = memory["importance"] / 10.0
    alpha, gamma = 0.4, 0.6
    return alpha * recency + gamma * importance_norm

def get_relevant_memories(agent_id: str, context: str = "", limit: int = 10):
    """
    MVP: 拉取候选记忆 → 衰减加权排序 → 取 top-N。
    Phase 5 升级: 加入 pgvector 语义检索，score += β·cosine_sim(query, memory)
    """
    now = datetime.now(timezone.utc)
    candidates = supabase.table("agent_memories") \
        .select("*") \
        .eq("agent_id", agent_id) \
        .order("created_at", desc=True) \
        .limit(limit * 3)  # 拉 3 倍候选，再按衰减分排序
        .execute().data
    scored = sorted(candidates, key=lambda m: memory_retrieval_score(m, now), reverse=True)
    return scored[:limit]
```

**语义压缩机制：**

```
记忆超限时（>50 条）的处理流程：

1. 按 memory_type 分组，识别同类 experience 记忆
2. 对 importance ≤ 3 的同类记忆做语义压缩：
   LLM 将 N 条相似记忆 → 1 条 compressed 摘要
   例："2026-01-15 GST涨价" + "2026-02-01 物价上涨感受"
      → compressed: "2026年初经历 GST 涨价，感受到物价压力"
3. 原始记忆标记删除，compressed 记忆保留 importance = max(原始)
4. 若仍超限，删除 retrieval_score 最低的记忆
```

**memory_type 枚举（含扩展）：**

```sql
-- Phase 2: experience, decision, observation, belief_update, compressed
-- Phase 3: + interaction（Agent 间对话产生）
-- Phase 5: + reflection（反思型高层记忆）
CHECK (memory_type IN (
  'experience', 'decision', 'observation', 'belief_update',
  'compressed', 'interaction', 'reflection'
))
```

### 5.4 Persona Prompt 构建

```python
def build_persona(agent: dict, memories: list) -> str:
    """
    三层 Persona Prompt:

    Layer A — 统计身份（硬事实）
      "You are a 32-year-old Chinese male..."

    Layer B — NVIDIA 叙事（软画像）
      "Background: Born and raised in Tampines..."
      "Professional: Senior software engineer at a local fintech..."
      "Hobbies: Enjoys hawker food, weekend cycling..."

    Layer C — 记忆流（动态上下文）
      "Recent experiences:
       - You heard that GST will increase to 10% next year
       - Last month you decided not to buy CI insurance (too expensive)
       - You recently got promoted and your income increased"
    """

    # Layer A: 统计身份（~150 tokens）
    stats = f"""You are a {agent['age']}-year-old {agent['ethnicity']} {agent['gender']} living in {agent['planning_area']}, Singapore.
Education: {agent['education_level']}. Monthly income: ${agent['monthly_income']:,}.
Housing: {agent['housing_type']}. Marital status: {agent['marital_status']}.
Life phase: {agent['life_phase']}.
Personality: O={agent['big5_o']:.1f} C={agent['big5_c']:.1f} E={agent['big5_e']:.1f} A={agent['big5_a']:.1f} N={agent['big5_n']:.1f}.
Risk appetite: {agent['risk_appetite']:.1f}/5. Social trust: {agent['social_trust']:.1f}/5."""

    # Layer B: NVIDIA 叙事（~200 tokens，截取关键部分）
    narrative = ""
    if agent.get('persona'):
        narrative += f"\nBackground: {agent['persona'][:300]}"
    if agent.get('professional_persona'):
        narrative += f"\nProfessional: {agent['professional_persona'][:200]}"
    if agent.get('hobbies_and_interests'):
        narrative += f"\nHobbies: {agent['hobbies_and_interests'][:150]}"
    if agent.get('cultural_background'):
        narrative += f"\nCultural: {agent['cultural_background'][:150]}"

    # Layer C: 记忆流（~100 tokens）
    memory_text = ""
    if memories:
        memory_text = "\n\nRecent experiences and decisions:"
        for m in memories[:8]:
            memory_text += f"\n- {m['content'][:100]}"

    return stats + narrative + memory_text
```

**Token 预算：**
- Layer A: ~150 tokens（固定）
- Layer B: ~200 tokens（NVIDIA 叙事截取）
- Layer C: ~100 tokens（最多 8 条记忆）
- System prompt: ~100 tokens
- Question + options: ~100 tokens
- **总 input: ~650 tokens/agent**
- Output: ~100 tokens/agent
- **DeepSeek 成本: ~$0.0003/agent**
- 200 人模拟: **~$0.06**

---

## 6. 采样引擎设计

### 6.1 三种采样模式

```python
class Sampler:
    """从 148K agents 中采样 N 人"""

    def stratified_sample(self, n: int, filter: dict = {},
                          strata: list = ["age_group", "gender"]) -> list:
        """
        分层抽样：保持总体的人口比例。

        步骤:
        1. 按 filter 筛选候选人群
        2. 按 strata 分组
        3. 每组按比例分配名额
        4. 组内随机抽取

        保证: 采样结果的人口分布 ≈ 总体分布
        """

    def random_sample(self, n: int, filter: dict = {}) -> list:
        """简单随机抽样"""

    def targeted_sample(self, n: int, target: dict) -> list:
        """
        定向采样：精确匹配条件。

        例: target={"planning_area": "Punggol", "age_min": 25, "age_max": 35}
        → 只从榜鹅 25-35 岁居民中采样

        适用: 区域性政策评估、特定人群产品测试
        """
```

### 6.2 采样 SQL（在数据库端完成）

```sql
-- 分层采样示例：按 age_group + gender 分层，采 200 人
WITH population AS (
    SELECT *,
           CASE WHEN age < 18 THEN 'youth'
                WHEN age < 35 THEN 'young_adult'
                WHEN age < 55 THEN 'middle'
                WHEN age < 75 THEN 'senior'
                ELSE 'elderly' END AS age_bin
    FROM agents
    WHERE monthly_income <= 10000  -- 用户筛选条件
      AND age >= 18
),
strata_counts AS (
    SELECT age_bin, gender, COUNT(*) as cnt,
           COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () as pct
    FROM population
    GROUP BY age_bin, gender
),
sampled AS (
    SELECT p.*,
           ROW_NUMBER() OVER (
               PARTITION BY p.age_bin, p.gender
               ORDER BY RANDOM()
           ) as rn,
           CEIL(sc.pct * 200) as quota  -- 200 = 目标样本量
    FROM population p
    JOIN strata_counts sc ON p.age_bin = sc.age_bin AND p.gender = sc.gender
)
SELECT agent_id FROM sampled WHERE rn <= quota;
```

---

## 7. 事件系统设计

### 7.1 事件注入流程

```
管理员（Web /events 页面）
    │
    │ 输入: "政府宣布 GST 将从 9% 涨至 10%，2027年生效"
    │
    ▼
┌─────────────────────────────────┐
│ Step 1: LLM 评估影响              │
│                                   │
│ prompt: "评估以下事件对新加坡       │
│ 不同人群的影响，返回六维向量和       │
│ 受影响人群筛选条件"                 │
│                                   │
│ → impact_economic: -3             │
│ → impact_psychological: -2        │
│ → target_filter: {"age_min": 18}  │
│   (所有成年人受影响)                │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Step 2: 写入 events 表           │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│ Step 3: 批量写入记忆               │
│                                   │
│ 对所有匹配 target_filter 的agent:  │
│ INSERT INTO agent_memories         │
│   (agent_id, memory_type,          │
│    content, importance)            │
│ SELECT agent_id, 'experience',     │
│   'GST将从9%涨至10%，2027年生效',   │
│   7  -- 经济类事件 importance=7     │
│ FROM agents                        │
│ WHERE age >= 18;                   │
│                                   │
│ → 约 120K agents 获得这条记忆       │
└─────────────────────────────────┘
```

### 7.2 记忆容量管理

```
每个 Agent 最多保留 50 条记忆。
超过时，按 importance ASC, created_at ASC 删除最旧最不重要的。

存储估算：
  148K agents × 50 memories × 200 bytes = 1.5 GB

  Supabase Pro (8GB) 足够。

  如果需要压缩:
  - 降到 20 条/agent = 600 MB
  - 或只给"活跃 agent"（被采样过的）保留记忆
```

---

## 8. 前端设计

### 8.1 核心页面

#### `/ask` — 提问界面（MVP 核心）

```
┌─────────────────────────────────────────────┐
│  Digital Twins Singapore                     │
│  ─────────────────────                       │
│                                              │
│  📋 研究问题                                  │
│  ┌──────────────────────────────────────┐    │
│  │ GST 涨至 10%，你会如何调整消费？       │    │
│  └──────────────────────────────────────┘    │
│                                              │
│  选项 (每行一个):                             │
│  ┌──────────────────────────────────────┐    │
│  │ 1. 大幅减少非必需消费                   │    │
│  │ 2. 略微减少消费                         │    │
│  │ 3. 不变                                │    │
│  │ 4. 不确定                              │    │
│  └──────────────────────────────────────┘    │
│                                              │
│  背景信息 (可选):                             │
│  ┌──────────────────────────────────────┐    │
│  │ 新加坡 GST 从 9% 涨至 10%...          │    │
│  └──────────────────────────────────────┘    │
│                                              │
│  ⚙️ 采样配置                                 │
│  样本量: [50] [100] [200] [500] [1000]       │
│  采样方式: ◉ 分层  ○ 随机  ○ 定向            │
│                                              │
│  🎯 筛选条件 (可选)                           │
│  年龄: [18] - [100]                          │
│  收入: [0] - [无上限]                         │
│  地区: [全部 ▼]                               │
│  住房: [全部 ▼]                               │
│                                              │
│  预估成本: ~$0.06 (200 agents)               │
│                                              │
│  [ 🚀 开始模拟 ]                              │
└─────────────────────────────────────────────┘
```

#### `/jobs/[id]` — 结果仪表板

```
┌─────────────────────────────────────────────┐
│  模拟结果 #a3f2...                            │
│  "GST 涨至 10%，你会如何调整消费？"              │
│  200 人 | 已完成 | 耗时 3m42s | $0.06        │
│                                              │
│  ┌─────────────────────────────────────┐     │
│  │  📊 总体分布                          │     │
│  │  ██████████████ 大幅减少 35%          │     │
│  │  ████████████████████ 略微减少 42%    │     │
│  │  ██████ 不变 15%                     │     │
│  │  ███ 不确定 8%                       │     │
│  └─────────────────────────────────────┘     │
│                                              │
│  ┌─── 按年龄 ───┐ ┌─── 按收入 ───┐          │
│  │ 18-29: 28%   │ │ <$3K: 52%    │          │
│  │ 30-44: 40%   │ │ $3-7K: 38%   │          │
│  │ 45-59: 45%   │ │ $7-15K: 22%  │          │
│  │ 60+: 38%     │ │ $15K+: 8%    │          │
│  └──────────────┘ └──────────────┘          │
│                                              │
│  🗣️ 典型回答                                 │
│  ┌──────────────────────────────────────┐    │
│  │ A42380 (35岁 华人 女 $4,500/月 HDB4)  │    │
│  │ "作为两个孩子的妈妈，GST涨价意味着      │    │
│  │  每月要多花$200，我会减少外出用餐..."    │    │
│  └──────────────────────────────────────┘    │
│  ┌──────────────────────────────────────┐    │
│  │ A89120 (52岁 印度裔 男 $12,000 Condo) │    │
│  │ "对我来说影响不大，1%的差别可以忽略..."   │    │
│  └──────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

---

## 9. 现有代码资产清单

### 9.1 直接复用（不改或小改）

| 文件 | 功能 | 改动 |
|------|------|------|
| `engine/synthesis/math_core.py` | IPF、控制舍入、ValidationSuite | 不改 |
| `engine/synthesis/sg_distributions.py` | Census CPT | 不改 |
| `engine/synthesis/personality_init.py` | Big Five + 态度 | 不改 |
| `engine/synthesis/household_builder.py` | 家庭构建 | 小改：接受 148K 输入 |
| `engine/models/cpf_model.py` | CPF 计算 | 不改 |
| `engine/models/probability_models.py` | Layer 2 概率模型 | 不改 |
| `engine/rules/life_rules.py` | Layer 1 规则 | 不改 |
| `engine/compliance/*` | 合规引擎 | 不改 |
| `data/rules/life_ontology.yaml` | 生命阶段本体 | 不改 |

### 9.2 需要重构

| 文件 | 原功能 | 重构为 |
|------|--------|--------|
| `engine/llm/decision_engine.py` | LLM 决策 | `decision/layer3_llm.py` — 加入 rich persona + memory |
| `engine/core/agent.py` | Agent 数据模型 | 加入 NVIDIA 叙事字段 |
| `engine/synthesis/synthesis_gate.py` | 20K 验证 | 148K 验证 |
| `scripts/05_seed_supabase.py` | 上传 20K | 上传 148K + 叙事 |

### 9.3 新建

| 文件 | 功能 |
|------|------|
| `engine/synthesis/augment_nvidia.py` | 148K 增强主引擎 |
| `engine/simulation/sampler.py` | 采样引擎 |
| `engine/simulation/persona_builder.py` | 三层 Persona 构建 |
| `engine/simulation/memory_manager.py` | 记忆管理 |
| `engine/simulation/job_runner.py` | 模拟任务执行 |
| `engine/simulation/aggregator.py` | 结果聚合分析 |
| `engine/db/*.py` | 数据库访问层 |
| `scripts/01_augment_148k.py` | 一次性增强脚本 |
| `scripts/04_run_simulation.py` | 模拟运行入口 |

### 9.4 废弃

| 文件 | 原因 |
|------|------|
| `scripts/02_synthesize_population.py` | V1 合成，被 V3 替代 |
| `scripts/03_synthesize_v2_mathematical.py` | V2 合成，被 augment_nvidia 替代 |
| `scripts/12_merge_nvidia_personas.py` | 方向翻转，不再需要 |
| `engine/synthesis/ipf.py` | V1 IPF，被 math_core.py 的 DemingStephanIPF 替代 |
| `engine/pipeline/tick_manager.py` | MVP 不需要 tick 系统（Phase 2+） |
| `engine/pipeline/snapshot_manager.py` | MVP 不需要快照系统 |
| `engine/pipeline/version_manager.py` | MVP 不需要版本系统 |
| `engine/pipeline/collectors/*.py` | MVP 不需要自动数据采集 |
| `frontend/*.html` | 静态 HTML demo，被 Next.js 替代 |
| `dashboard/index.html` | 同上 |

**注意：废弃 ≠ 删除。** 这些文件移入 `archive/` 目录保留，后续 Phase 可能复用 tick_manager、snapshot_manager 等。

---

## 10. 执行计划

### Phase 1: 数据层（Week 1）

```
Day 1-2:
  ✦ 编写 augment_nvidia.py
    - 读取 148K parquet
    - 字段标准化
    - CPT 采样所有缺失维度
    - 输出 148K enriched CSV

Day 3:
  ✦ 验证 148K（复用 synthesis_gate）
  ✦ 编写 V3 schema migration
  ✦ 上传到 Supabase

Day 4:
  ✦ 编写 db/ 层（supabase_client, agent_repo）
  ✦ 验证数据库查询性能
```

### Phase 2: 模拟引擎（Week 2）

```
Day 5-6:
  ✦ sampler.py（三种采样模式）
  ✦ persona_builder.py（三层 prompt）
  ✦ memory_manager.py（CRUD + 检索）

Day 7-8:
  ✦ job_runner.py（任务执行器）
  ✦ aggregator.py（结果统计）
  ✦ 端到端测试：CLI 提交问题 → 采样 → LLM → 聚合结果
```

### Phase 3: Web 前端（Week 3）

```
Day 9-10:
  ✦ Next.js 项目搭建 + Supabase SDK
  ✦ /ask 页面（提问 + 采样配置）
  ✦ /jobs/[id] 页面（结果仪表板）

Day 11-12:
  ✦ /agents 浏览器
  ✦ /events 事件注入
  ✦ 图表组件（人口分布、选项分布）
```

### Phase 4: 事件系统 + 打磨（Week 4）

```
Day 13:
  ✦ 事件注入 → 批量写记忆
  ✦ 记忆容量管理

Day 14:
  ✦ Demo 场景测试（保险 + 政策 + 记忆效应）
  ✦ 性能优化 + Bug 修复
  ✦ 文档更新
```

---

## 11. 技术决策记录

### 11.1 为什么不用 Edge Function 跑 LLM？

Supabase Edge Function 有 **50 秒超时限制**。200 个 agent 串行调 LLM 需要 ~3 分钟。所以模拟执行必须在本地 Python 进程中完成。Edge Function 只用来创建 job 和注入事件（<1s 操作）。

后续如果需要云端执行，可以用 Vercel Serverless（60s）或 AWS Lambda（15min），但 MVP 不需要。

### 11.2 为什么 148K 不需要 IPF？

IPF 的作用是从 **边际分布** 推导 **联合分布**，用于从零生成人群。NVIDIA 148K 已经是按新加坡 Census 分布生成的完整人群，各维度的联合分布已经存在。我们只需要条件采样（给定 age+gender+education → 采样 income），这是简单的 CPT lookup，不需要 IPF。

IPF 仍然保留在 math_core.py 中，用于 **验证**：检验增补后的联合分布（如 income×education）是否与 Census 目标一致。

### 11.3 为什么 MVP 不做 Agent 间互动？

互动（Agent-Agent 对话）需要：
1. 社交网络拓扑（谁和谁可以互动）
2. 对话管理器（多轮对话）
3. 信息传播模型（舆论扩散）
4. 计算量 × 10+

MVP 的核心价值是 **"问 → 答 → 分析"**，不需要互动。互动是 Phase 3 的事。

### 11.4 为什么采样在数据库端做？

148K 行数据不适合每次全量读到 Python 内存再采样。在 PostgreSQL 用 `ORDER BY RANDOM()` + `PARTITION BY` 做分层抽样，只返回 N 行结果，节省带宽和内存。

### 11.5 LLM 并发策略

DeepSeek API 限速 ~60 RPM。200 agents 串行 ≈ 3.3 分钟。可以用 asyncio 并发 5-10 路，缩短到 30-60 秒。

```python
async def run_batch(agents, question, max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)
    async with aiohttp.ClientSession() as session:
        tasks = [ask_agent(session, semaphore, agent, question)
                 for agent in agents]
        return await asyncio.gather(*tasks)
```

### 11.6 Runner 心跳与 LLM 重试策略

**心跳监控：**

```python
# Runner 每 60 秒写入心跳
async def heartbeat_loop():
    while True:
        supabase.table("runner_status").upsert({
            "runner_id": RUNNER_ID,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "active_jobs": len(current_jobs)
        }).execute()
        await asyncio.sleep(60)

# 外部可查询：若 last_heartbeat > 10 分钟前 → Runner 失联
```

**LLM API 重试（指数退避 + jitter）：**

```python
async def call_llm_with_retry(payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await call_deepseek(payload)
        except (RateLimitError, TimeoutError) as e:
            if attempt == max_retries - 1:
                raise
            base_delay = 2 ** attempt  # 1s, 2s, 4s
            jitter = random.uniform(0, base_delay * 0.5)
            await asyncio.sleep(base_delay + jitter)
    # 连续 3 次失败 → 标记该 agent 为 skipped，job 继续
```

**Realtime 安全策略：**

Supabase Realtime 订阅 `simulation_jobs` 表变更时，只广播 `id` 和 `status` 字段。详细的 `result` 数据由前端通过 RLS 受控查询获取，防止广播通道泄露敏感分析结果。

```sql
-- Realtime 配置：只启用 status 变更通知
ALTER PUBLICATION supabase_realtime ADD TABLE simulation_jobs;
-- RLS 策略确保 result 字段仅 authenticated 用户可读
```

---

## 12. 成本模型

### 12.1 固定成本

| 项目 | 月成本 |
|------|--------|
| Supabase Pro | $25 |
| Vercel Hobby | $0 |
| 域名（可选） | ~$1 |
| **固定合计** | **$26/月** |

### 12.2 可变成本（DeepSeek API）

| 场景 | agents/次 | tokens/次 | 成本/次 | 如果每天 10 次 |
|------|----------|----------|---------|-------------|
| 快速测试 | 50 | 37K | $0.02 | $6/月 |
| 标准模拟 | 200 | 150K | $0.06 | $18/月 |
| 深度研究 | 1,000 | 750K | $0.30 | $90/月 |
| 压力测试 | 5,000 | 3.75M | $1.50 | $450/月 |

### 12.3 典型月度预算

| 使用强度 | 描述 | 月成本 |
|----------|------|--------|
| 轻度 | 每天 5 次标准模拟 | $26 + $9 = **$35/月** |
| 中度 | 每天 20 次标准模拟 | $26 + $36 = **$62/月** |
| 重度 | 每天 50 次 + 深度研究 | $26 + $200 = **$226/月** |

---

## 13. 扩展路径（MVP 之后）

| Phase | 功能 | 依赖 | 额外成本 |
|-------|------|------|----------|
| **Phase 2** | 向量记忆检索（pgvector） | Supabase 已内置 | $0 |
| **Phase 3** | Agent 间互动 + 社交网络 | 图算法库 | $0（计算量增加） |
| **Phase 4** | 实时事件接入（RSS + API） | 复用现有 collectors | $10/月（API费用） |
| **Phase 5** | 反思 + 规划 | LLM 调用量 ×3 | API成本 ×3 |
| **Phase 6** | 行为校准层 | 真实调查数据 | 数据获取成本 |
| **Phase 7** | 本地模型部署 | GPU 服务器 | $2000+/月 |

---

## 14. 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| NVIDIA 148K 分布偏差 | 中 | 高 | 增补后用 Census 验证，发现偏差则校准 |
| DeepSeek API 不稳定 | 低 | 中 | 备选 Gemini Flash（免费额度） |
| Supabase 500MB Free 不够 | 高 | 低 | 升 Pro ($25) 解决 |
| 148K 上传耗时过长 | 中 | 低 | 分批 upsert，500行/批 |
| LLM 响应质量不一 | 中 | 中 | temperature=0.5 + 异常检测 + 重试 |
| 记忆膨胀 | 低 | 中 | 容量上限 + 定期清理策略 |

---

## 附录 A: NVIDIA Parquet 字段清单

需要在 Sprint 0 执行 `pd.read_parquet` 确认精确字段名。已知字段：
- `age`, `sex`, `education_level`, `planning_area`
- `marital_status`, `race`
- `persona`, `professional_persona`, `cultural_background`
- `sports_persona`, `arts_persona`, `travel_persona`
- `culinary_persona`, `hobbies_and_interests`
- `career_goals_and_ambitions`
- `occupation`, `industry`
- `religion`

## 附录 B: 现有 Census CPT 清单

来自 `sg_distributions.py`：
- `AGE_MARGINAL` (21 groups)
- `GENDER_MARGINAL` (M/F)
- `ETHNICITY_MARGINAL` (4 groups)
- `AREA_MARGINAL` (28 areas)
- `RESIDENCY_MARGINAL` (8 types)
- `build_education_cpt(age_group)` → P(education | age)
- `build_income_cpt(education, age, gender)` → P(income_bracket | edu, age, gender)
- `build_housing_income_cpt(income_bracket, area)` → P(housing | income, area)
- `build_marital_age_cpt(age, gender)` → P(marital | age, gender)
- `build_health_age_cpt(age)` → P(health | age)
