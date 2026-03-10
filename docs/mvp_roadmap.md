# Digital Twins Singapore — MVP 路线图

> 约束：仅 Supabase (Free/Pro) + DeepSeek API + 本地 Python
> 目标：可演示的端到端系统，能接受客户问题、Agent 响应、聚合分析

---

## 现状盘点

### 已有（可直接用）
| 组件 | 状态 | 文件 |
|------|------|------|
| 20K Agent 合成引擎 | ✅ 完成 | `scripts/03_synthesize_v2_mathematical.py` |
| NVIDIA 148K 叙事融合 | ✅ 完成 | `scripts/12_merge_nvidia_personas.py` |
| 统计验证框架 | ✅ 完成 | `scripts/04_validate_population.py` |
| Supabase Schema | ✅ 完成 | `supabase/migrations/20260305000000_init.sql` |
| 数据上传脚本 | ✅ 完成 | `scripts/05_seed_supabase.py` |
| LLM 决策引擎 | ✅ 完成 | `engine/llm/decision_engine.py` |
| 客户模拟 Demo | ✅ 完成 | `scripts/10_client_simulation_demo.py` |
| Agent 数据模型 | ✅ 完成 | `engine/core/agent.py` |

### 缺失（MVP 必须补）
| 组件 | 优先级 | 难度 |
|------|--------|------|
| 数据实际入库 | P0 | 低 — 跑脚本即可 |
| Agent Memory 表 | P0 | 低 — 加一张 Supabase 表 |
| Web 前端（查询界面） | P1 | 中 — Next.js 简单页面 |
| 事件注入接口 | P1 | 低 — Supabase Edge Function |
| 批量 Agent 响应引擎 | P1 | 中 — 并发 + 成本控制 |

### 不需要（MVP 砍掉）
- ❌ 实时新闻爬虫（手动注入事件即可）
- ❌ Agent 间互动（Phase 3，不是 MVP）
- ❌ 反思/规划系统（Phase 5，不是 MVP）
- ❌ 行为校准层（Phase 6，不是 MVP）
- ❌ GPU / 本地模型部署

---

## MVP 架构

```
┌─────────────────────────────────────────────────┐
│                  Web 前端 (Next.js)              │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ 提问界面  │  │ 结果仪表板│  │ Agent 浏览器  │ │
│  └─────┬────┘  └─────┬────┘  └───────┬───────┘ │
└────────┼─────────────┼───────────────┼──────────┘
         │             │               │
┌────────┼─────────────┼───────────────┼──────────┐
│        ▼             ▼               ▼          │
│              Supabase (PostgreSQL)               │
│  ┌──────────────────────────────────────────┐   │
│  │ agents (20K)     │ memories              │   │
│  │ households       │ events                │   │
│  │ agent_reactions  │ simulation_jobs       │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │ Edge Functions                            │   │
│  │  • run-simulation (接受问题→采样→调LLM)   │   │
│  │  • inject-event   (注入外部事件)          │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
         │
         ▼
    DeepSeek API ($0.001/K tokens)
```

---

## 分步执行计划

### Sprint 0：数据入库（1天）

**目标：20K enriched agents 进入 Supabase**

```
步骤：
1. python3 scripts/03_synthesize_v2_mathematical.py   # 生成 agents_20k_v2.csv
2. python3 scripts/12_merge_nvidia_personas.py          # 融合 NVIDIA 叙事
3. python3 scripts/05_seed_supabase.py                  # 上传到 Supabase
```

需要修改：
- `05_seed_supabase.py`：添加 NVIDIA 叙事字段（persona, occupation, industry 等）
- `schema.sql`：添加叙事字段列

```sql
-- 新增到 agents 表
ALTER TABLE agents ADD COLUMN IF NOT EXISTS persona TEXT DEFAULT '';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS professional_persona TEXT DEFAULT '';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS cultural_background TEXT DEFAULT '';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS hobbies_and_interests TEXT DEFAULT '';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS career_goals TEXT DEFAULT '';
```

**产出：Supabase 中有 20K 完整 Agent 数据，可查询**

---

### Sprint 1：Memory 系统 + 增强 Persona（2-3天）

**目标：Agent 有记忆，LLM 响应更真实**

#### 1a. Memory 表

```sql
CREATE TABLE IF NOT EXISTS agent_memories (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),
    memory_type TEXT NOT NULL CHECK (memory_type IN (
        'experience',    -- 经历过的事件
        'decision',      -- 做过的决策
        'observation',   -- 观察到的信息
        'reflection'     -- 反思总结（Phase 5 用）
    )),
    content TEXT NOT NULL,          -- 记忆内容
    importance INTEGER DEFAULT 5,   -- 1-10 重要性
    source_event_id UUID,           -- 关联事件

    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ           -- 可选过期时间
);

CREATE INDEX idx_memories_agent ON agent_memories(agent_id);
CREATE INDEX idx_memories_type ON agent_memories(agent_id, memory_type);
CREATE INDEX idx_memories_importance ON agent_memories(agent_id, importance DESC);
```

#### 1b. 增强 Persona Prompt

当前的 `agent_to_persona()` 只用统计字段。增强版加入：
- NVIDIA 叙事（professional_persona, cultural_background, hobbies）
- 最近 5 条记忆
- 组合成更丰富的 persona prompt

```python
def build_rich_persona(agent: dict, memories: list) -> str:
    """构建包含叙事+记忆的完整 persona prompt"""

    # 基础统计画像（现有）
    base = f"You are a {agent['age']}-year-old {agent['ethnicity']} ..."

    # NVIDIA 叙事（新增）
    narrative = ""
    if agent.get('persona'):
        narrative += f"\nBackground: {agent['persona']}"
    if agent.get('professional_persona'):
        narrative += f"\nProfessional life: {agent['professional_persona']}"
    if agent.get('cultural_background'):
        narrative += f"\nCultural context: {agent['cultural_background']}"
    if agent.get('hobbies_and_interests'):
        narrative += f"\nHobbies: {agent['hobbies_and_interests']}"

    # 记忆（新增）
    memory_text = ""
    if memories:
        memory_text = "\nRecent experiences:\n"
        for m in memories[-5:]:
            memory_text += f"- {m['content']}\n"

    return base + narrative + memory_text
```

**产出：Agent 有记忆表，persona prompt 包含叙事+记忆**

---

### Sprint 2：批量模拟引擎（2-3天）

**目标：输入一个问题/场景，系统自动采样+调 LLM+聚合结果**

#### 2a. Simulation Job 表

```sql
CREATE TABLE IF NOT EXISTS simulation_jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,

    -- 输入
    client_name TEXT NOT NULL,
    question TEXT NOT NULL,
    options JSONB NOT NULL,             -- ["选项A", "选项B", ...]
    context TEXT DEFAULT '',

    -- 采样配置
    sample_size INTEGER DEFAULT 50,
    sampling_strategy TEXT DEFAULT 'stratified',  -- stratified / random / targeted
    target_filter JSONB,                -- 可选：只针对特定人群

    -- 状态
    status TEXT DEFAULT 'pending' CHECK (status IN (
        'pending', 'sampling', 'running', 'aggregating', 'completed', 'failed'
    )),

    -- 结果
    agents_sampled INTEGER DEFAULT 0,
    agents_responded INTEGER DEFAULT 0,
    result JSONB,                       -- 聚合结果

    -- 成本
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(8,4) DEFAULT 0,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 2b. 执行引擎（Python 脚本，本地跑）

```
流程：
1. 从 simulation_jobs 表取 pending job
2. 按 sampling_strategy 从 agents 表采样
3. 对每个 agent：
   a. 读取 agent 完整画像 + 最近记忆
   b. 构建 rich persona prompt
   c. 调 DeepSeek API
   d. 解析响应，写入 agent_reactions
   e. 写入新记忆（"我被问了XX，我选了YY"）
4. 聚合所有响应 → 写入 job.result
5. 更新 job status = completed
```

成本估算：
- 50 agents × ~1000 tokens/agent = 50K tokens
- DeepSeek 价格：$0.27/M input + $1.10/M output
- 每次模拟成本 ≈ **$0.05-0.10**
- 每天跑 100 次 = **$5-10/天**

**产出：可复用的模拟引擎，输入问题→输出结构化分析**

---

### Sprint 3：Web 前端（3-5天）

**目标：非技术人员可以通过网页使用系统**

技术栈：Next.js + Supabase JS SDK（你已经熟悉）

```
页面结构：
/                       首页 — 系统介绍 + 快速入口
/ask                    提问界面 — 输入问题+选项 → 提交模拟
/jobs                   任务列表 — 查看历史模拟任务
/jobs/[id]              结果页 — 图表+人口统计分析+Agent 个案
/agents                 Agent 浏览器 — 搜索/筛选 20K agents
/agents/[id]            Agent 详情 — 完整画像+记忆+历史反应
/events                 事件管理 — 手动注入事件
```

核心页面优先级：
1. `/ask` + `/jobs/[id]` — 这就是产品核心
2. `/agents/[id]` — 展示 Agent 丰富度
3. 其余页面后补

**产出：可访问的 Web 界面，可以提问+看结果**

---

### Sprint 4：事件系统（2天）

**目标：注入外部事件，观察 Agent 群体反应变化**

```
事件注入流程：
1. 管理员在 /events 页面输入事件（如 "GST 将从 9% 涨到 10%"）
2. 系统自动：
   a. 用 LLM 评估事件影响维度（经济、社会、心理...）
   b. 确定受影响人群（target_filter）
   c. 创建 simulation_job 自动跑一轮模拟
   d. 将事件写入受影响 agent 的记忆
3. 下次问同一批 agent 问题时，他们会"记住"这个事件
```

这就是**记忆的核心价值**：
- 注入 "经济衰退" 事件 → Agent 记住了
- 再问 "你会买保险吗" → 回答会因为记忆而改变
- **这是静态问卷做不到的**

**产出：事件→记忆→影响决策的闭环**

---

## 资源需求

| 资源 | MVP 需求 | 月成本 |
|------|----------|--------|
| Supabase Free | 500MB DB, 50K 行, 500K Edge Function 调用 | $0 |
| Supabase Pro（推荐） | 8GB DB, 无行数限制, 2M Edge Function | $25/月 |
| DeepSeek API | ~$5-20/月（取决于使用频率） | $5-20/月 |
| Vercel（前端） | Hobby plan 足够 | $0 |
| 域名（可选） | .com / .sg | $10-15/年 |
| **总计** | | **$25-45/月** |

Supabase Free plan 限制：
- 500MB 数据库 — 20K agents 约 50MB，够用
- 50,000 行 — agents(20K) + memories + reactions 初期够用
- 边缘函数 500K 调用/月 — 够用

**建议：先用 Free plan 开始，数据量增长后升 Pro ($25/月)**

---

## 时间线

```
Week 1: Sprint 0 + Sprint 1
        ├── Day 1: 数据入库 + Schema 升级
        ├── Day 2-3: Memory 表 + 增强 Persona
        └── Day 3: 端到端测试（脚本跑通）

Week 2: Sprint 2
        ├── Day 4-5: 批量模拟引擎
        └── Day 6: 成本控制 + 错误处理

Week 3: Sprint 3
        ├── Day 7-9: Web 前端核心页面
        └── Day 10: /ask + /jobs/[id] 完成

Week 4: Sprint 4 + 打磨
        ├── Day 11-12: 事件系统
        └── Day 13-14: Bug 修复 + Demo 准备

MVP 完成 ≈ 4 周
```

---

## MVP Demo 场景（用于验证/展示）

### Demo 1：保险产品市场调研
```
客户：AIA Singapore
问题："月保费$200的重疾险，你会买吗？"
Agent 样本：50人（分层抽样）
输出：
  - 整体购买意愿 42%
  - 30-44岁最高意愿（58%）
  - 收入<$3K群体核心顾虑："太贵"
  - 收入>$10K群体核心顾虑："保额不够"
  - 华人vs马来vs印度裔的差异分析
```

### Demo 2：政策影响评估
```
客户：新加坡政府
场景：GST 从 9% 涨到 10%
步骤：
  1. 先问："你目前的消费习惯如何？" → 基线
  2. 注入事件："政府宣布 GST 将于 2027 年涨至 10%"
  3. 事件写入 Agent 记忆
  4. 再问："你会如何调整消费？" → 受记忆影响的回答
输出：
  - 65% 会减少非必需消费
  - 低收入群体（<$3K）影响最大
  - Condo 住户几乎无影响
  - 和2024年 GST 8→9% 的实际调查数据对比
```

### Demo 3：记忆效应展示
```
同一批 Agent，连续 3 轮：
  Round 1: "你对新加坡经济前景乐观吗？" → 基线
  Round 2: 注入事件 "科技业大规模裁员" → Agent 记住
  Round 3: 重新问同样的问题 → 乐观度下降

展示：记忆使 Agent 响应随时间演化，不是静态问卷
```

---

## 关键技术决策

### 1. 本地脚本 vs Edge Function
**MVP 选择：本地 Python 脚本**
- 开发快，调试方便
- Supabase Edge Function 有 50s 超时限制，不适合批量 LLM 调用
- 后续可迁移到 Edge Function 或 Vercel Serverless

### 2. 采样策略
**MVP 选择：分层抽样 50 人**
- 50 人 × $0.001/call = $0.05/次模拟
- 统计上：50 人分层抽样，95% CI 约 ±14%
- 对比：100 人 ±10%，200 人 ±7%
- MVP 够用，后续可调大

### 3. 记忆容量
**MVP 选择：每 Agent 最多 20 条记忆**
- 20K agents × 20 memories × ~200 bytes = ~80MB
- Supabase Free 500MB 够用
- 超过 20 条时，丢弃最低 importance 的

### 4. LLM 选择
**MVP 选择：DeepSeek Chat**
- 最便宜：$0.27/M input, $1.10/M output
- 质量足够（中文+英文都好）
- 备选：Gemini Flash（免费额度 1500 RPD）

---

## 风险与缓解

| 风险 | 缓解策略 |
|------|----------|
| DeepSeek API 不稳定 | 备选 Gemini Flash；关键 demo 预跑结果缓存 |
| Supabase Free 行数超限 | 定期清理旧 memories/reactions；或升 Pro ($25) |
| LLM 响应质量不一致 | 设 temperature=0.5；结果异常时自动重试；50人样本平滑噪声 |
| 50人样本太小 | 展示时强调"定性洞察"而非"精确数字"；后续可扩到200人 |
| 前端开发时间 | 先用 Streamlit 快速出 Demo，再做 Next.js 正式版 |

---

## 立即可以执行的第一步

```bash
# 确认 NVIDIA 数据存在
ls data/nvidia_personas_singapore.parquet

# 确认 agents_20k_v2.csv 存在（或重新合成）
ls data/output/agents_20k_v2.csv

# 如果不存在，先跑合成
python3 scripts/03_synthesize_v2_mathematical.py

# 融合 NVIDIA 叙事
python3 scripts/12_merge_nvidia_personas.py

# 上传到 Supabase（需先升级 schema）
python3 scripts/05_seed_supabase.py
```

**Sprint 0 做完，你就有了一个有 20K 丰富 Agent 的在线数据库。这就是 MVP 的地基。**
