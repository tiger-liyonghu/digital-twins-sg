# NanNan — 产品 & 项目管理

> 最后更新：2026-03-09

---

## 团队（全 Agent）

### 核心运营层（4 人）
| Agent | 角色 | 职责 | 模型 |
|-------|------|------|------|
| **Tiger** | 创始人 | 产品方向、业务、客户 | 人类 |
| **NanNan** | PM | 路线图、优先级、任务跟踪、团队协调 | Claude |
| **Sophie** | 客户调研顾问 | 引导客户对话、设计问卷 | DeepSeek |
| **Claude Dev** | 全栈工程师 | 前后端开发、架构实现 | Claude |

### 专家层（7 人）— 定义在 `frontend/experts/knowledge.js`
| Agent | 角色 | 核心职责 | 管辖范围 |
|-------|------|----------|----------|
| **Dr. Chen Wei** | 人口科学家 | Agent 人口合成、分布校准、IPF | 合成人口的统计准确性 |
| **DataKai** | 数据工程师 | 外部数据 ETL、事实更新、数据质量审计 | SingStat/data.gov.sg → Supabase |
| **Prof. Rachel Koh** | 调研方法学家 | 问卷设计、抽样、加权、backtest | 调研结果的方法论严谨性 |
| **Dr. Alex Tan** | LLM 仿真专家 | Persona prompt、VS+RP、偏差检测 | Agent 回答的 AI 质量 |
| **Mr. Tan Keng Huat** | 新加坡政策专家 | CPF/HDB/NS/EIP、社会规范 | 本地政策准确性 |
| **Dr. Michael Ong** | 行为建模师 | 大五人格、决策模型、文化心理 | Agent 行为的心理学真实性 |
| **Ms. Adeline Wee** | 合规官 | PDPA、k-匿名、AI 伦理 | 数据隐私与治理 |

### 变更说明（vs 原 9 人团队）
| 变更 | 原因 |
|------|------|
| **新增 DataKai** | 数据质量是 P0 问题，需要专人盯 ETL、事实时效、分布审计 |
| **合并 Prof. Sarah Lim → Dr. Chen Wei** | 社会仿真与人口合成高度重叠，合并为"人口科学家" |
| **合并 Dr. Priya Nair → Dr. Alex Tan** | 社交网络扩散是 LLM 仿真的子场景，不需独立角色 |
| **移除 James Liu（软件架构师）** | Claude Dev 已覆盖架构设计；系统还没大到需要独立架构师 |

> 知识库：`frontend/experts/knowledge.js` + `learning_log.js` + `params.js`

---

## 产品定位

**Digital Twins Singapore** — 新加坡首个 LLM 驱动的合成人口仿真平台

**一句话**：用 172,000 个 AI 市民，在几小时内完成传统需要几周的市场调研和政策预演。

**核心价值主张**：
- 政府：政策发布前预演民意，避免翻车
- 企业：产品上市前用万人级仿真测试，替代百人问卷
- 研究机构：触达传统调研无法覆盖的群体

**目标客户**：新加坡政府部门（MND/MOH/MOT）、金融机构、咨询公司、快消品牌

---

## 产品架构现状

### 已完成 ✅

| 模块 | 状态 | 说明 |
|------|------|------|
| 合成人口 | ✅ 172,173 agents | 年龄/性别/种族/收入/住房/教育/婚姻/生命阶段 |
| Python API Server | ✅ 运行中 | /api/survey, /api/eligible, /api/job, /api/abtest, /api/conjoint |
| VS+RP 仿真方法 | ✅ | Verbalized Sampling + Reformulated Prompting |
| NVIDIA 质量评分 | ✅ | Nemotron-70B reward model |
| Sophie AI 助手 | ✅ | LLM 驱动的对话式调研设计 |
| Sophie 对话流程 | ✅ | 场景选择 → 行业选择 → 2-3轮探索对话 → 自动设计问卷 → 执行 → 结果 |
| Sophie 本体模型 | ✅ | 6张表，51个主题，35+事实，30+提问模板，5种问卷模式 |
| 中英双语 | ✅ | i18n 完整支持 |
| Supabase 数据库 | ✅ | 8张 dt_* 日志表 + 6张 sophie_* 本体表 |
| Backtest 框架 | ✅ | GE2025, GST, 保险渠道等多个验证 |

### 进行中 🔧

| 模块 | 状态 | 阻塞 |
|------|------|------|
| 行业选择 UI | 🔧 前端已建，待浏览器测试 | 无 |
| dt_* 表迁移 | 🔧 SQL 已写，未执行 | 需 run supabase-migration.sql |

### 待建设 📋

| 模块 | 优先级 | 说明 |
|------|--------|------|
| Agent 人口校准 | P0 | 用 SingStat 真实联合分布校准 172K agents |
| Agent 属性扩展 | P0 | 增加 planning_area, occupation, religion, language 等 |
| 外部数据 ETL | P1 | 接入 SingStat API / data.gov.sg 自动拉取 |
| Sophie context 自动更新 | P1 | 从 sg_economic_indicators 自动注入最新数据 |
| 结果导出 (PDF/PPT) | P1 | 客户需要拿走的交付物 |
| 多轮调研会话 | P2 | 一个 session 内多次调研，结果对比 |
| A/B 测试 UI | P2 | 前端接入后端已有的 /api/abtest |
| 联合分析 UI | P2 | 前端接入后端已有的 /api/conjoint |
| 用户认证 | P2 | Supabase Auth，区分客户 |
| 计费系统 | P3 | 按 agent 数 × LLM 调用计费 |
| 部署上线 | P3 | Vercel (前端) + Railway/Fly.io (Python API) |

---

## 产品路线图

### Phase 1：Agent 真实度（当前优先）
> 目标：让 172K agents 的人口画像精确还原新加坡真实人口结构

1. **拉取 SingStat 联合分布数据**
   - 年龄 × 性别 × 种族 × 住房类型
   - 收入 × 教育 × 住房类型
   - 规划区 × 人口画像
   - 数据源：SingStat Table Builder API + Census 2020

2. **审计现有 agent 分布**
   - 对比真实分布 vs 当前 agent 分布
   - 识别系统性偏差

3. **扩展 agent 属性**
   - planning_area（55个规划区）
   - occupation（SSOC 职业分类）
   - religion（6种 + 无）
   - language_primary（英/华/马来/泰米尔）
   - car_ownership（有车 = 高收入信号）
   - household_size
   - cpf_balance_range

4. **重新生成/校准 agent 人口**
   - 用条件概率采样替代独立随机
   - 确保联合分布准确

### Phase 2：情境知识自动化
> 目标：Sophie 的知识库自动从政府数据更新

5. **建立数据 ETL 管道**
   - sg_demographic_distributions 表
   - sg_economic_indicators 表
   - sg_spending_patterns 表
   - 定期从 SingStat API 拉取

6. **sophie_context_facts 自动扩充**
   - 每个行业 × 场景自动匹配最新数据
   - 消除硬编码事实

### Phase 3：商业化准备
> 目标：可以给客户演示和试用

7. **结果导出** — PDF 报告 + PPT 模板
8. **A/B 测试 + 联合分析 UI**
9. **用户认证 + 多租户**
10. **部署上线**

---

## 新加坡外部数据源注册表

### Tier 1：Agent 校准（必须接入）

| 数据源 | API | 格式 | 更新频率 | 状态 |
|--------|-----|------|----------|------|
| SingStat Table Builder | ✅ REST | JSON/CSV | 月/季/年 | 📋 待接入 |
| Census 2020 (data.gov.sg) | ✅ REST | CSV | 十年一次 | 📋 待接入 |
| 家庭收入趋势 KHIT | ❌ PDF/XLSX | 表格 | 年 | 📋 待接入 |
| 家庭支出调查 HES 2023 | ✅ data.gov.sg | CSV | 五年一次 | 📋 待接入 |
| CPF 缴费率 | ❌ PDF | 表格 | 年 | 📋 待接入 |
| MOM 就业统计 | ✅ data.gov.sg | CSV | 季 | 📋 待接入 |

### Tier 2：仿真增强

| 数据源 | API | 用途 | 状态 |
|--------|-----|------|------|
| HDB 转售价格 | ✅ data.gov.sg | 资产水平校准 | 📋 待接入 |
| LTA DataMall | ✅ REST (10M/day) | 通勤模式 | 📋 待接入 |
| OneMap 人口查询 | ✅ REST | 空间校准 | 📋 待接入 |
| MOH 健康数据 | ✅ data.gov.sg | 健康状态 | 📋 待接入 |
| MAS 利率/汇率 | ✅ REST | 金融环境 | 📋 待接入 |
| NEA 天气 API | ✅ REST (实时) | 行为修正 | 📋 待接入 |

### Tier 3：Sophie 知识库（已部分完成）

| 数据源 | 用途 | 状态 |
|--------|------|------|
| CPI 分类数据 | 购买力 | ✅ 已在 context_facts |
| 零售销售指数 | 消费行为 | 📋 待补充 |
| MSF 家庭趋势 | 生命事件 | 📋 待补充 |

---

## 关键指标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| Agent 数量 | 172,173 | 172,173（保持） |
| Agent 属性维度 | 8 | 15+ |
| 人口分布准确度 | 未审计 | >95% 各维度 |
| Sophie 本体主题 | 51 | 80+ |
| Sophie context facts | 35 | 200+ |
| 行业覆盖（深度） | 5 | 8 |
| Backtest 验证数 | 4 | 10+ |
| 平均问卷执行时间 (1000人) | ~2 min | <1 min |
| 端到端可用性 | 开发环境 | 生产部署 |

---

## 技术债务

1. **dt_* 日志表未创建** — supabase-migration.sql 写好了但没执行
2. **Python API 未部署** — 只在 localhost:3456 运行
3. **logger.ts 静默失败** — 日志表不存在时 Supabase insert 静默失败
4. **硬编码 context facts** — 部分场景的默认 context 还在 sophie-types.ts 中硬编码
5. **无错误监控** — 生产环境需要 Sentry 或类似服务
6. **Agent 分布未验证** — 172K agents 的联合分布准确度未知

---

## 决策日志

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-03-09 | Sophie 本体存 Supabase | 可动态更新，不需重新部署 |
| 2026-03-09 | 5个行业深度覆盖 + "其他" | 平衡深度和广度，"其他"兜底 |
| 2026-03-09 | Agent 校准列为 P0 | 分布不准 = 所有调研结果都有系统性偏差 |
| 2026-03-09 | NanNan 作为 PM agent | 需要持续跟踪项目状态和优先级 |
| 此前 | DeepSeek 作为 LLM | 性价比高，中英文能力强 |
| 此前 | VS+RP 方法 | 比直接采样更准确（有 backtest 验证） |
| 此前 | Backtest ground truth 隔离 | 不可在 context 中泄露被验证调查的结果 |
