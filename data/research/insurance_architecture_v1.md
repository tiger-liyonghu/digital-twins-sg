# Insurance Domain Layer — Architecture Design v1.0
## 2026-03-10

---

# 1. 设计目标

保险不是"加 17 个列"——它是一个**知识域（Domain Layer）**，有独立的：
- 数据生命周期（研究迭代 → 重新生成）
- 版本管理（回滚、A/B 对比）
- 前端感知（筛选、展示）
- LLM 感知（保险画像写入 agent prompt）

未来还会有其他域：financial_extended, transport, digital_behavior。保险是第一个，架构要通用。

---

# 2. 数据流全链路

## 2.1 现有链路
```
Frontend (SurveyParams: age/gender/income filters)
  → API POST /api/survey
    → sampling.py: SELECT FROM agents WHERE filters
      → persona.py: agent_to_persona(agent_dict)
        → "35-year-old M Chinese, HDB_4, earning $5,200/month..."
          → llm.py: ask_agent(persona, question, options, context)
            → DeepSeek → probability distribution → sampled choice
```

## 2.2 新增链路（保险域感知）
```
Frontend (SurveyParams + InsuranceFilters + domain='insurance')
  → API POST /api/survey
    → sampling.py: SELECT FROM agents
                   JOIN agent_insurance USING (agent_id)
                   WHERE demographic_filters AND insurance_filters
      → persona.py: agent_to_persona(agent_dict)
                   + insurance_to_persona(insurance_dict)  ← 新增
        → "35-year-old M Chinese, HDB_4, earning $5,200/month...
           Insurance: Has IP (Private tier, AIA, with rider).
           Has term life ($400K) and CI ($200K).
           Spends $350/month on insurance. MediSave $40K.
           Attitude: proactive, aware of protection gap."
          → llm.py: ask_agent(enriched_persona, question, options, context)
            → DeepSeek → probability distribution → sampled choice
```

**关键变化：LLM 看到的 agent 画像从"人口统计"扩展到"人口统计 + 保险画像"。**

---

# 3. 数据库 Schema

## 3.1 domain_versions（通用版本注册表）

```sql
CREATE TABLE domain_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  domain TEXT NOT NULL,            -- 'insurance' | 'financial' | 'transport'
  version TEXT NOT NULL,           -- 'v1.0', 'v1.1'
  is_active BOOLEAN DEFAULT false, -- 每个 domain 只有一个 active
  status TEXT DEFAULT 'draft',     -- draft | generating | validating | active | archived
  description TEXT,

  -- 溯源
  research_doc TEXT,               -- 'insurance_profile_research_v1.md'
  data_sources JSONB,              -- {"PGS_2022": ["T58","T66","T68","T69"], "MOH_2025": ["IP tier"]}
  generation_params JSONB,         -- CPT 参数快照（完整可复现）

  -- 统计
  agent_count INTEGER,
  validation_result JSONB,         -- 边际检验结果

  created_at TIMESTAMPTZ DEFAULT now(),
  activated_at TIMESTAMPTZ,
  UNIQUE(domain, version)
);
```

## 3.2 agent_insurance（保险域数据）

```sql
CREATE TABLE agent_insurance (
  agent_id TEXT NOT NULL REFERENCES agents(agent_id),
  version_id UUID NOT NULL REFERENCES domain_versions(id),

  -- ===== 医疗险 (Health Insurance) =====
  has_medishield_life BOOLEAN NOT NULL DEFAULT true,
  has_ip BOOLEAN NOT NULL DEFAULT false,
  ip_tier TEXT CHECK (ip_tier IS NULL OR ip_tier IN ('private','A','B1','standard')),
  has_rider BOOLEAN DEFAULT false,
  ip_insurer TEXT,                  -- AIA/GE/Prudential/NTUC/Singlife/Raffles

  -- ===== 人寿险 (Life Insurance) =====
  has_term_life BOOLEAN NOT NULL DEFAULT false,
  term_life_coverage INT DEFAULT 0,   -- S$, 0 if no term life
  has_whole_life BOOLEAN NOT NULL DEFAULT false,

  -- ===== 重疾险 (Critical Illness) =====
  has_ci BOOLEAN NOT NULL DEFAULT false,
  ci_coverage INT DEFAULT 0,          -- S$, 0 if no CI

  -- ===== 财务 (Financial) =====
  monthly_insurance_spend INT DEFAULT 0,  -- S$/month, all insurance combined
  medisave_balance INT DEFAULT 0,         -- S$

  -- ===== 行为 (Behavioral) =====
  insurance_attitude TEXT CHECK (insurance_attitude IN
    ('proactive','adequate','passive','resistant','unaware')),
  protection_gap_awareness TEXT CHECK (protection_gap_awareness IN
    ('aware_acting','aware_inactive','unaware','overconfident')),
  preferred_channel TEXT CHECK (preferred_channel IN
    ('agent_tied','ifa','online','bank','employer')),
  last_life_event_trigger TEXT,

  -- ===== 健康使用 (Health Utilization) =====
  annual_hospitalization_freq REAL DEFAULT 0.0,  -- expected visits/year

  PRIMARY KEY (agent_id, version_id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 查询索引：active 版本 + 常用筛选条件
CREATE INDEX idx_ins_version ON agent_insurance(version_id);
CREATE INDEX idx_ins_has_ip ON agent_insurance(version_id, has_ip);
CREATE INDEX idx_ins_ip_tier ON agent_insurance(version_id, ip_tier);
CREATE INDEX idx_ins_attitude ON agent_insurance(version_id, insurance_attitude);
```

## 3.3 约束与 RLS

```sql
-- 确保每个 domain 最多一个 active 版本
CREATE UNIQUE INDEX idx_one_active_per_domain
  ON domain_versions(domain) WHERE is_active = true;

-- RLS
ALTER TABLE domain_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_insurance ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read" ON domain_versions FOR SELECT USING (true);
CREATE POLICY "Public read" ON agent_insurance FOR SELECT USING (true);
CREATE POLICY "Service write" ON domain_versions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write" ON agent_insurance FOR ALL USING (true) WITH CHECK (true);
```

---

# 4. Engine 层改动

## 4.1 lib/persona.py — 新增 insurance_to_persona()

```python
def insurance_to_persona(ins: dict) -> str:
    """Convert insurance profile dict to persona paragraph."""
    if not ins or not ins.get("has_ip") and not ins.get("has_term_life") and not ins.get("has_ci"):
        # 无保险的人也是一种画像
        return (
            "Insurance: Only has basic MediShield Life (government health insurance). "
            "No private Integrated Shield Plan, no life insurance, no critical illness cover."
        )

    parts = []

    # Health insurance
    if ins.get("has_ip"):
        tier_map = {"private": "Private Hospital", "A": "Class A ward", "B1": "Class B1 ward", "standard": "Standard"}
        tier = tier_map.get(ins.get("ip_tier"), "unknown tier")
        rider = "with full rider" if ins.get("has_rider") else "without rider"
        insurer = ins.get("ip_insurer") or "unknown insurer"
        parts.append(f"Has Integrated Shield Plan ({tier}, {insurer}, {rider})")
    else:
        parts.append("No Integrated Shield Plan (only basic MediShield Life)")

    # Life insurance
    life_parts = []
    if ins.get("has_term_life"):
        cov = ins.get("term_life_coverage", 0)
        life_parts.append(f"term life (${cov:,} coverage)")
    if ins.get("has_whole_life"):
        life_parts.append("whole-of-life policy")
    if life_parts:
        parts.append(f"Life insurance: {', '.join(life_parts)}")
    else:
        parts.append("No life insurance")

    # CI
    if ins.get("has_ci"):
        cov = ins.get("ci_coverage", 0)
        parts.append(f"Critical illness coverage: ${cov:,}")
    else:
        parts.append("No critical illness coverage")

    # Financial
    spend = ins.get("monthly_insurance_spend", 0)
    medisave = ins.get("medisave_balance", 0)
    parts.append(f"Monthly insurance spending: ${spend:,}")
    parts.append(f"MediSave balance: ${medisave:,}")

    # Attitude
    att_map = {
        "proactive": "actively seeks adequate coverage",
        "adequate": "believes current coverage is sufficient",
        "passive": "knows coverage may be insufficient but hasn't acted",
        "resistant": "finds insurance too expensive",
        "unaware": "has limited awareness of insurance needs",
    }
    att = att_map.get(ins.get("insurance_attitude"), "")
    if att:
        parts.append(f"Insurance attitude: {att}")

    return "Insurance profile: " + ". ".join(parts) + "."
```

## 4.2 lib/sampling.py — 扩展查询支持 insurance JOIN

```python
# 新增常量
INSURANCE_FIELDS = (
    "has_ip,ip_tier,has_rider,ip_insurer,"
    "has_term_life,term_life_coverage,has_whole_life,"
    "has_ci,ci_coverage,monthly_insurance_spend,medisave_balance,"
    "insurance_attitude,protection_gap_awareness,preferred_channel"
)

def get_active_version(domain: str) -> str:
    """Get active version_id for a domain."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/domain_versions",
        headers=HEADERS,
        params={"domain": f"eq.{domain}", "is_active": "eq.true", "select": "id"},
    )
    rows = resp.json()
    return rows[0]["id"] if rows else None

def stratified_sample(n, strata, domains=None, insurance_filters=None, **demo_filters):
    """
    Fetch agents with optional domain layer JOIN.

    domains: list of domain names to JOIN, e.g. ['insurance']
    insurance_filters: dict of insurance-specific filters
    """
    # 如果需要保险域，用 Supabase RPC 或 view 做 JOIN
    if domains and 'insurance' in domains:
        version_id = get_active_version('insurance')
        # 使用 Supabase view 或 RPC 实现 JOIN
        # ...
```

## 4.3 API 层 — SurveyParams 扩展

```python
# scripts/api_server.py — 新增 insurance 相关参数
params = {
    # ... 现有人口统计筛选 ...

    # 域层
    "domains": request.json.get("domains", []),        # ["insurance"]

    # 保险筛选
    "has_ip": request.json.get("has_ip"),               # true/false/null
    "ip_tier": request.json.get("ip_tier"),             # "private"/"A"/"B1"
    "has_term_life": request.json.get("has_term_life"),
    "has_ci": request.json.get("has_ci"),
    "insurance_attitude": request.json.get("insurance_attitude"),
}
```

---

# 5. 前端改动

## 5.1 web/lib/api.ts — 类型扩展

```typescript
export interface SurveyParams {
  // ... 现有字段 ...

  // 域层
  domains?: string[];              // ['insurance']

  // 保险筛选
  has_ip?: boolean;
  ip_tier?: 'private' | 'A' | 'B1' | 'standard';
  has_term_life?: boolean;
  has_ci?: boolean;
  insurance_attitude?: 'proactive' | 'adequate' | 'passive' | 'resistant' | 'unaware';
}

export interface EligibleParams {
  // ... 现有字段 ...

  // 保险筛选
  domains?: string[];
  has_ip?: boolean;
  ip_tier?: string;
  has_term_life?: boolean;
  has_ci?: boolean;
  insurance_attitude?: string;
}

// 保险画像（用于详情展示）
export interface InsuranceProfile {
  has_medishield_life: boolean;
  has_ip: boolean;
  ip_tier: string | null;
  has_rider: boolean;
  ip_insurer: string | null;
  has_term_life: boolean;
  term_life_coverage: number;
  has_whole_life: boolean;
  has_ci: boolean;
  ci_coverage: number;
  monthly_insurance_spend: number;
  medisave_balance: number;
  insurance_attitude: string;
  protection_gap_awareness: string;
  preferred_channel: string;
}

// AgentLog 扩展
export interface AgentLog {
  // ... 现有字段 ...
  insurance?: InsuranceProfile;   // 保险调查时附带
}

// SurveyResult breakdowns 扩展
export interface SurveyResult {
  // ... 现有字段 ...
  breakdowns: {
    by_age: Record<string, { n: number; positive_rate: number }>;
    by_income: Record<string, { n: number; positive_rate: number }>;
    // 新增：保险维度交叉分析
    by_ip_tier?: Record<string, { n: number; positive_rate: number }>;
    by_insurance_attitude?: Record<string, { n: number; positive_rate: number }>;
  };
}
```

## 5.2 前端 UI 扩展点

```
调查配置页面:
  ├── 受众筛选（现有）
  │   ├── 人口统计: age, gender, income, housing, education
  │   └── 🆕 保险画像: has_ip, ip_tier, has_term_life, has_ci, attitude
  │
  ├── 🆕 域层选择
  │   └── ☑ 保险画像 (Include insurance profile in agent prompt)
  │       → 勾选后，LLM 会看到 agent 的保险画像
  │       → 不勾选，LLM 只看人口统计（通用调查）
  │
  └── 结果展示
      ├── 现有: by_age, by_income 交叉分析
      └── 🆕 by_ip_tier, by_insurance_attitude 交叉分析
```

---

# 6. Sophie 本体集成

## 6.1 sophie_topics 中的保险相关话题

Sophie 的 `finance` 行业下的话题（如 IP Price Hike, Insurance Awareness）自动携带 `domains: ['insurance']`：

```sql
-- sophie_topics 新增 domains 列
ALTER TABLE sophie_topics ADD COLUMN domains TEXT[] DEFAULT '{}';

-- 保险相关话题自动标记
UPDATE sophie_topics
SET domains = ARRAY['insurance']
WHERE industry_id = 'finance'
  AND (name ILIKE '%insurance%' OR name ILIKE '%IP%' OR name ILIKE '%shield%'
       OR scenario_type = 'product_pricing');
```

## 6.2 自动域感知

当 Sophie 选中一个 `domains = ['insurance']` 的话题时：
1. 前端自动勾选"Include insurance profile"
2. API 自动添加 `domains: ['insurance']`
3. Engine 自动 JOIN `agent_insurance` 并在 persona 中加入保险画像

用户也可以手动覆盖（取消勾选 = 故意不用保险画像做对照实验）。

---

# 7. 版本管理操作

## 7.1 生成新版本
```bash
python scripts/41_generate_insurance.py --version v1.0 --description "Initial insurance profiles based on PGS 2022"
# 1. 创建 domain_versions 记录 (status=generating)
# 2. 读取 CPT 参数 (data/cpt/insurance_v1.yaml)
# 3. 为 172,173 agents 生成保险画像
# 4. 批量写入 agent_insurance
# 5. 运行边际验证（IP 71%? Term 17%? WoL 33.6%?）
# 6. 更新 status=validating, validation_result=...
```

## 7.2 激活版本
```bash
python scripts/42_activate_insurance_version.py --version v1.0
# 1. SET is_active=false 对当前 active 版本
# 2. SET is_active=true, activated_at=now() 对 v1.0
# 3. 清除 sampling 缓存
```

## 7.3 回滚
```bash
python scripts/42_activate_insurance_version.py --version v0.9  # 切回旧版本
# 数据都在，秒切
```

## 7.4 A/B 对比
```python
# 同一个调查，分别用 v1.0 和 v1.1 的保险画像跑
result_v10 = run_survey(question, options, insurance_version='v1.0')
result_v11 = run_survey(question, options, insurance_version='v1.1')
compare(result_v10, result_v11)  # 看 CPT 参数调整的影响
```

---

# 8. 文件结构

```
Digital Twins Singapore/
├── data/
│   ├── research/
│   │   ├── insurance_profile_research_v1.md    ← 研究报告（现有）
│   │   └── insurance_architecture_v1.md        ← 本文档
│   └── cpt/
│       └── insurance_v1.yaml                   ← CPT 参数（待创建）
│
├── supabase/migrations/
│   └── 20260311000000_insurance_domain.sql     ← DB migration（待创建）
│
├── engine/core/
│   └── agent.py                                ← 不改（保险不是核心人口统计）
│
├── lib/
│   ├── persona.py                              ← 新增 insurance_to_persona()
│   ├── sampling.py                             ← 扩展 insurance JOIN + filters
│   └── llm.py                                  ← 不改（persona 字符串透传）
│
├── scripts/
│   ├── 41_generate_insurance.py                ← 保险画像生成脚本（待创建）
│   ├── 42_activate_insurance_version.py        ← 版本激活脚本（待创建）
│   └── api_server.py                           ← 扩展 insurance filters
│
└── web/lib/
    └── api.ts                                  ← 扩展 SurveyParams + InsuranceProfile
```

---

# 9. 实施计划

| 阶段 | 内容 | 前置条件 |
|------|------|---------|
| **P0: Schema** | 创建 domain_versions + agent_insurance 表 | 无 |
| **P1: CPT** | 编写 insurance_v1.yaml，定义所有 17 个字段的条件概率表 | 研究报告 v1.2 |
| **P2: Generation** | scripts/41_generate_insurance.py — 为 172K agents 生成保险画像 | P0 + P1 |
| **P3: Validation** | 边际检验（IP 71%, Term 17%, WoL 33.6%, CI 30.6%, IP tier 56/28/14/1） | P2 |
| **P4: Engine** | persona.py + sampling.py 扩展 | P2 |
| **P5: API** | api_server.py 扩展 insurance filters + domain JOIN | P4 |
| **P6: Frontend** | SurveyParams 扩展 + 筛选 UI + 结果交叉分析 | P5 |
| **P7: Sophie** | sophie_topics.domains 标记 + 自动域感知 | P6 |

**P0-P3 可以在不动前后端的情况下完成**（纯数据层），这是最安全的路径。

---

# 10. 设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 保险数据放在独立表 vs agents 表加列 | **独立表** | 版本管理、独立回滚、关注点分离 |
| 版本号用全局 vs 域内独立编号 | **域内独立** (insurance_v1.0) | 各域独立迭代 |
| agent.py 是否加保险字段 | **不加** | 保险不是核心人口统计，通过 JOIN 获取 |
| LLM prompt 默认是否含保险画像 | **不默认，按 domain 声明** | 通用调查不需要，保险调查才需要 |
| 前端筛选 vs Sophie 自动 | **两者兼有** | Sophie 自动 + 手动覆盖 |
| 保险画像写入 persona 的位置 | **追加在人口统计段落之后** | 保持现有 persona 不变，新增段落 |
