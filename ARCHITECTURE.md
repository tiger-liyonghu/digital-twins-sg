# Digital Twins Singapore — 系统架构

## 全局概览

```
┌──────────────────────────────────────────────────────────────┐
│                      用户浏览器                               │
│              http://localhost:3000/simulate                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │        Sophie AI 对话界面 (Next.js 14)               │    │
│  │  场景选择 → 配置问卷 → 试跑/正式调研 → 结果分析      │    │
│  └────────────────────┬─────────────────────────────────┘    │
└───────────────────────┼──────────────────────────────────────┘
                        │ HTTP (fetch)
                        ▼
┌──────────────────────────────────────────────────────────────┐
│              Python API Server (port 3456)                    │
│                                                              │
│  POST /api/survey    → 提交调研任务                          │
│  POST /api/eligible  → 查询符合条件人数                      │
│  POST /api/abtest    → A/B 测试                             │
│  POST /api/conjoint  → 联合分析                             │
│  GET  /api/job/{id}  → 轮询任务状态                         │
│                                                              │
│  内部流程:                                                   │
│  ┌────────┐   ┌────────────┐   ┌──────────────┐            │
│  │ 分层抽样│ → │ LLM 逐人问 │ → │ 汇总分析报告 │            │
│  └────────┘   └─────┬──────┘   └──────────────┘            │
│                     │                                        │
└─────────────────────┼────────────────────────────────────────┘
                      │ API calls
          ┌───────────┼───────────┐
          ▼                       ▼
┌──────────────────┐   ┌──────────────────┐
│   DeepSeek LLM   │   │ NVIDIA Nemotron  │
│  deepseek-chat   │   │  Reward Model    │
│                  │   │ (质量评分)        │
│ VS+RP 方法:      │   │                  │
│ 输出概率分布     │   │ 返回 reward 分数 │
│ 再采样得到选择   │   │ >-5: 高质量      │
└──────────────────┘   │ -5~-15: 可接受   │
                       │ <-15: 低质量     │
                       └──────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│                    Supabase (PostgreSQL)                      │
│           rndfpyuuredtqncegygi.supabase.co                  │
│                                                              │
│  核心数据:                                                   │
│  ┌─────────────┐  172,173 条合成居民                        │
│  │   agents    │  age, gender, ethnicity, income, housing,  │
│  │             │  education, Big5 人格, 风险偏好, 政治倾向  │
│  └─────────────┘                                            │
│                                                              │
│  Sophie 日志:                                                │
│  ┌──────────────────┐ ┌──────────────────┐                  │
│  │ dt_sessions      │ │ dt_conversations │                  │
│  │ dt_survey_jobs   │ │ dt_survey_results│                  │
│  │ dt_error_logs    │ │ dt_quality_incidents│                │
│  │ dt_client_files  │ │ dt_system_learnings│                │
│  └──────────────────┘ └──────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 1. 合成人口层 — 172,173 个 AI 居民

### 生成方法

| 步骤 | 脚本 | 方法 |
|------|------|------|
| 下载人口普查 | `01_download_census.py` | data.gov.sg Census 2020 |
| V1 合成 | `02_synthesize_population.py` | IPF + 随机人格 |
| V2 数学合成 | `03_synthesize_v2_mathematical.py` | Deming-Stephan IPF + 高斯 Copula + k-匿名 |
| 统计验证 | `04_validate_population.py` | 卡方检验, KL散度, SRMSE |
| 导入 Supabase | `05_seed_supabase.py` | 批量 1000 条/次 |
| 扩容至 172K | `20_seed_148k_v3.py` | 基于 20K 扩展, CPF 模型 + 马尔科夫链 |

### Agent 属性（`agents` 表）

```
人口统计:  age, gender, ethnicity, planning_area, residency_status
经济:      monthly_income, education_level, occupation, industry
住房:      housing_type, housing_value
家庭:      marital_status, household_id, num_children
健康:      health_status, chronic_conditions, bmi_category, smoking
公积金:    cpf_oa, cpf_sa, cpf_ma, cpf_ra
人格 Big5: big5_o (开放性), big5_c (尽责性), big5_e (外向性),
           big5_a (宜人性), big5_n (神经质)
态度:      risk_appetite (风险偏好), political_leaning (政治倾向),
           social_trust (社会信任), religious_devotion (宗教虔诚度)
生命阶段:  life_phase (establishment → growth → peak → plateau → decline)
```

---

## 2. Python API 后端 — `scripts/api_server.py`

### 端口: 3456

### 核心流程

```
用户提交调研 → 创建 job → 后台线程执行:

1. SAMPLING (分层抽样)
   - 从 Supabase 加载 172K agents (内存缓存)
   - 按 age × gender 分层, 按用户筛选条件过滤
   - 抽取 N 个 agent

2. RUNNING (逐人调研)
   对每个 agent:
   ├── agent_to_persona(agent)  →  第三人称描述
   │   "50岁华人男性，月入$5,000，住HDB 4房，已婚..."
   │
   ├── DeepSeek LLM 调用 (VS+RP 方法)
   │   系统提示: "你是调研分析师，根据受访者画像估算回答概率"
   │   返回: {"probabilities": {"选项A": 0.3, "选项B": 0.5, ...}, "reasoning": "..."}
   │   采样: choice = random.choices(options, weights=probabilities)
   │
   └── NVIDIA Nemotron 评分 (可选, 非阻塞)
       返回: reward score (-30 to 0)

3. ANALYSIS (汇总)
   - 选项分布: {选项: 票数}
   - 年龄分组: {18-29: {n, positive_rate}, 30-44: ...}
   - 收入分组: {<$3K: {n, positive_rate}, ...}
   - 质量摘要: {high_quality_pct, acceptable_pct, low_quality_pct}
   - 成本: {total_tokens, total_cost_usd, cost_per_agent}
```

### API 端点

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/survey` | POST | 提交调研, 返回 `{job_id}` |
| `/api/eligible` | POST | 查询符合筛选条件的人数 |
| `/api/abtest` | POST | A/B 测试 (双臂对比 + z检验) |
| `/api/conjoint` | POST | 联合分析 (产品偏好) |
| `/api/job/{id}` | GET | 轮询任务状态和结果 |

### LLM 方法: Verbalized Sampling + Reformulated Prompting

```
传统方法: LLM 直接回答 → 社会期望偏差严重
VS+RP 方法: LLM 输出概率分布 → 采样 → 减少偏差

关键原则:
- Context 中绝不引用被验证调查的结果 (Ground Truth 隔离)
- 不同 agent 画像 → 不同概率分布
- 基于人口统计 + 人格特征独立预测
```

---

## 3. Next.js 前端 — `web/`

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 14 (App Router) | 框架 |
| TypeScript | 5.x | 类型安全 |
| Tailwind CSS | 3.x | 样式 |
| Recharts | 2.x | 图表 (柱状图、饼图) |
| Supabase JS | 2.x | 云端日志 |
| React | 18 | UI |

### 页面

| 路径 | 文件 | 功能 |
|------|------|------|
| `/` | `app/page.tsx` | 首页, Sophie 介绍, 入口 |
| `/simulate` | `app/simulate/page.tsx` → `ChatInterface.tsx` | Sophie 对话界面 |

### Sophie 对话流程 (3 步)

```
Step 1: 选场景
  Sophie: "你想调研什么？选个场景。"
  → 3 张场景卡片 (政策预演 / 产品测试 / 受众洞察)

Step 2: 配置 + 启动
  Sophie: "我帮你配好了，改改或直接跑。"
  → SurveyConfigCard: 问题 + 选项 + 受众 + 样本量 + 启动按钮

Step 3: 结果 + 迭代
  Sophie: "试跑完成！扩大规模还是改改再跑？"
  → ResultsDisplay: 分布图 / 年龄分组 / 个体引用
  → 按钮: 扩大到 2000 人 / 修改再跑
```

### 3 个预设场景

| ID | 名称 | Tagline | 默认受众 |
|----|------|---------|----------|
| `policy_simulation` | 政策预演 | 政策发布前，先听听民声 | 21-75岁 |
| `product_pricing` | 产品与定价测试 | 用一万人测试，而非一百人 | 21-64岁 |
| `audience_intelligence` | 受众洞察 | 看见问卷触达不到的人群 | 18-80岁 |

### 组件结构

```
web/components/sophie/
├── ChatInterface.tsx    核心对话引擎
│   - 状态机 (Phase: welcome → confirm → test_run → results → qa)
│   - 消息渲染 + widget 嵌入
│   - API 调用 + 轮询
│   - Supabase 日志
│
└── widgets.tsx          UI 组件
    ├── ScenarioCards       场景选择卡片 (3 个)
    ├── SurveyConfigCard    一站式配置 (问题+选项+受众+样本量+启动)
    ├── ProgressBar         进度条 + 中间结果
    └── ResultsDisplay      结果展示 (3 tab: 分布/年龄/个体引用)
```

### 双语支持 (EN/ZH)

- `lib/i18n.ts` — 翻译字符串
- `lib/locale-context.tsx` — React Context + LangSwitch 组件
- 所有 widget 内部通过 `useLocale()` 动态切换

---

## 4. Supabase 数据层

### 连接信息

```
URL:  https://rndfpyuuredtqncegygi.supabase.co
前端: NEXT_PUBLIC_SUPABASE_ANON_KEY (web/.env.local)
后端: SUPABASE_KEY (.env)
```

### 核心表

| 表名 | 数据量 | 用途 |
|------|--------|------|
| `agents` | 172,173 | 合成居民主表 |
| `households` | ~50,000 | 家庭单元 |
| `dt_sessions` | 动态 | Sophie 会话 |
| `dt_conversations` | 动态 | 每条对话消息 |
| `dt_survey_jobs` | 动态 | 调研任务元数据 |
| `dt_survey_results` | 动态 | 调研结果数据 |
| `dt_error_logs` | 动态 | 错误日志 |
| `dt_quality_incidents` | 动态 | LLM 质量事件 |
| `dt_system_learnings` | 动态 | 系统自进化记录 |
| `dt_client_files` | 动态 | 导出文件记录 |

### 索引

```sql
idx_agents_strata ON agents (age_group, gender, residency_status)
idx_conv_session ON dt_conversations (session_id)
idx_errors_session ON dt_error_logs (session_id)
idx_errors_category ON dt_error_logs (category)
```

---

## 5. 端到端数据流

```
用户选场景 "政策预演"
    ↓
SurveyConfigCard 展示预填的 CPF 提取年龄问题
    ↓
用户点击 "试跑 10 个居民"
    ↓
前端 POST /api/survey {question, options, context, sample_size: 10}
    ↓
后端创建 job, 后台线程启动:
    ↓
从 Supabase 加载 172K agents (内存缓存)
    ↓
分层抽样 10 人 (按 age × gender)
    ↓
逐人调用 DeepSeek:
  Agent A00234 (35岁华人女性, $4K/月, HDB 3房)
  → LLM: {"probabilities": {"强烈支持": 0.15, "有点支持": 0.35, ...}}
  → 采样: "有点支持"
  → Nemotron 评分: -3.2 (高质量)
    ↓
10 人全部完成 → 汇总分析
    ↓
前端轮询 GET /api/job/{id} 每 2 秒
    ↓
收到 status: "done" → 显示 ResultsDisplay
  - 柱状图: 选项分布
  - 饼图: 比例
  - 个体引用: "♀ 35yo Chinese S$4,000/mo → 有点支持"
    ↓
用户点击 "扩大到 2,000 人" → 重复以上流程
    ↓
全部结果 + 对话记录存入 Supabase dt_* 表
```

---

## 6. 外部依赖

| 服务 | 用途 | 费用 |
|------|------|------|
| DeepSeek API | LLM 调研回答 | ~$1.50/百万 token (~$0.0003/agent) |
| NVIDIA NIM | 回答质量评分 | 免费 (API Key 限额) |
| Supabase | 数据库 + 存储 | 免费 tier (500MB) |

---

## 7. 本地开发

```bash
# 启动后端 (port 3456)
cd "/Users/tigerli/Desktop/Digital Twins Singapore"
python scripts/api_server.py

# 启动前端 (port 3000)
cd web
npm run dev

# 访问
open http://localhost:3000
```

### 环境变量

**根目录 `.env`** (Python 后端):
```
SUPABASE_URL=https://rndfpyuuredtqncegygi.supabase.co
SUPABASE_KEY=eyJ...
DEEPSEEK_API_KEY=sk-...
NVIDIA_API_KEY=nvapi-...
```

**`web/.env.local`** (Next.js 前端):
```
NEXT_PUBLIC_SUPABASE_URL=https://rndfpyuuredtqncegygi.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:3456
DEEPSEEK_API_KEY=sk-...
```

---

## 8. 关键目录

| 目录 | 用途 |
|------|------|
| `/scripts/` | Python 后端 (API server, 合成, 回测, 模拟) |
| `/lib/` | Python 共享库 (LLM, 抽样, 分析, 配置) |
| `/engine/` | 核心引擎 (IPF 合成, 社会模拟, LLM 决策) |
| `/web/` | Next.js 前端 |
| `/web/components/sophie/` | Sophie 对话 UI |
| `/web/lib/` | 前端工具库 (API client, 类型, 日志, i18n) |
| `/data/output/` | 调研结果 JSON |
| `/supabase/migrations/` | 数据库迁移 SQL |
| `/docs/` | 架构文档, 策略报告 |
