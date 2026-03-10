# 数据治理框架 Data Governance Framework

## 新加坡数字孪生 — V3 数据管理架构

**版本 Version**: 2.0 (aligned with V3 Architecture + 148K base)
**日期 Date**: 2026-03-06

---

## 目录

1. [数据分级体系](#1-数据分级体系)
2. [数据资产清单](#2-数据资产清单)
3. [断供应急方案](#3-断供应急方案)
4. [数据输入验证](#4-数据输入验证)
5. [数据应用结果验证](#5-数据应用结果验证)
6. [运行时数据治理](#6-运行时数据治理)
7. [数据生命周期管理](#7-数据生命周期管理)
8. [数据血缘追踪](#8-数据血缘追踪)
9. [治理执行机制](#9-治理执行机制)

---

## 1. 数据分级体系

### 1.1 分级定义

| 级别 | 定义 | 断供影响 | 要求 |
|------|------|----------|------|
| **T0 基石层** | 系统无法运行。缺失则无法生成任何 agent | 系统瘫痪 | 必须本地缓存，双源备份，每次合成前校验 |
| **T1 结构层** | Agent 核心属性依赖。缺失则 agent 画像严重失真 | 产出质量不可接受 | 本地缓存 + 年度更新，有降级方案 |
| **T2 丰富层** | 增强 agent 真实感。缺失则可用但精度下降 | 可降级运行 | 定期同步，缺失时用默认值或模型估计 |
| **T3 动态层** | 实时/时效性数据。缺失则用静态快照替代 | 功能受限但不影响核心 | 按需拉取，缓存最近快照 |
| **T4 运行层** | 模拟运行产生的数据（记忆、响应、事件） | 数据丢失但系统可重跑 | Supabase 自动备份 + 导出策略 |

### 1.2 分级决策树

```
该数据缺失时 agent 能否生成？
  ├─ 不能 → T0
  └─ 能 → 生成的 agent 是否严重失真？
           ├─ 是 → T1
           └─ 否 → 该数据是静态的还是动态的？
                     ├─ 静态（年度更新） → T2
                     ├─ 动态（月度/实时） → T3
                     └─ 运行时产生 → T4
```

---

## 2. 数据资产清单

### 2.1 T0 基石层（系统不可运行若缺失）

| ID | 数据源 | 提供方 | 频率 | 用途 | 存储位置 | 状态 |
|----|--------|--------|------|------|----------|------|
| D001 | 人口年龄×性别边际分布 | SingStat Population Trends | 年度(9月) | 增补验证（148K 本身有 age/gender） | `sg_distributions.py` 硬编码 | 已集成 |
| D002 | 种族分布 | SingStat Population Trends | 年度 | 增补验证 | `sg_distributions.py` 硬编码 | 已集成 |
| D003 | 规划区人口分布 | SingStat / OneMap | 年度 | 增补验证 | `sg_distributions.py` 硬编码 | 已集成 |
| D004 | 教育×年龄 CPT | GHS 2025 | 5年(GHS周期) | 增补验证（NVIDIA 已有 education） | `sg_distributions.py` 硬编码 | 已集成 |
| **D005** | **NVIDIA 148K 人群底座** | HuggingFace CC BY 4.0 | 一次性 | **V3 核心底座** — 21字段×148K行 | `data/nvidia_personas_singapore.parquet` | 已下载 |

**V3 变化**：D005 从 T2 升级为 T0。在 V2 架构中 NVIDIA 是"锦上添花"，在 V3 中是系统底座。

**T0 治理规则**：
- 所有 T0 数据**必须本地文件或硬编码**，不得运行时远程拉取
- NVIDIA parquet 文件 SHA-256 校验和：每次加载时验证文件完整性
- 每次合成前自动校验：边际分布之和 = 1.0 ± 1e-6
- D001-D004 用于验证 NVIDIA 148K 的分布是否与 Census 一致

---

### 2.2 T1 结构层（核心画像质量依赖）

V3 中这些数据用于**增补** NVIDIA 148K 缺失的统计维度。

| ID | 数据源 | 提供方 | 频率 | V3 用途 | 存储位置 | 状态 |
|----|--------|--------|------|---------|----------|------|
| D101 | 收入×教育×年龄 CPT | MOM Labour Force + GHS | 年度 | 增补 `monthly_income` | `sg_distributions.py` 硬编码 | 已集成 |
| D102 | 住房类型×收入 CPT | GHS 2025 + HDB统计 | 年度 | 增补 `housing_type` | `sg_distributions.py` 硬编码 | 已集成 |
| D103 | 婚姻×年龄×性别 CPT | Population Trends | 年度 | 验证（NVIDIA 已有 marital_status） | `sg_distributions.py` 硬编码 | 已集成 |
| D104 | 居留身份分布 | Population in Brief | 年度 | 增补 `residency_status` | `sg_distributions.py` 硬编码 | 已集成 |
| D105 | Big Five 亚洲基线 | Schmitt 2007 学术文献 | 固定 | 增补 `big5_o/c/e/a/n` | `personality_init.py` 硬编码 | 已集成 |
| D106 | 特质间相关矩阵 | 元分析文献 | 固定 | Cholesky 分解矩阵 R | `personality_init.py` 硬编码 | 已集成 |
| D107 | 家户规模分布 | GHS 2025 | 5年 | 增补 household 结构 | `household_builder.py` 硬编码 | 已集成 |
| D108 | CPF 贡献率表 | CPF Board | 年度(1月) | 增补 CPF 余额 | `cpf_model.py` 硬编码 | 已集成 |
| D109 | 健康×年龄 CPT | GHS 2025 | 5年 | 增补 `health_status` | `sg_distributions.py` 硬编码 | 已集成 |
| D110 | 生命阶段本体 | 自研 (Elder/Modigliani/Erikson) | 固定 | 增补 `life_phase` | `data/rules/life_ontology.yaml` | 已集成 |

**V3 变化**：D103 从"增补"降为"验证"（NVIDIA 已有 marital_status）。D108-D110 新增。

**T1 治理规则**：
- 硬编码在代码中，有明确 `# Source:` 注释
- **降级方案**：若某年数据延迟，使用上一年数据 + 通胀/增长系数调整
- CPT 采样前自动验证行求和 = 1.0

---

### 2.3 T2 丰富层（增强真实感）

| ID | 数据源 | 提供方 | 频率 | 用途 | 状态 |
|----|--------|--------|------|------|------|
| D201 | NPHS 2024 疾病患病率 | MOH | 2-3年 | 细化 health_status → 具体慢性病 | 待集成 |
| D202 | HES 2023 消费支出结构 | SingStat | 5年 | expenditure_profile 按收入分位 | 待集成 |
| D203 | IPS 政治态度调查 | NUS LKYSPP IPS | 不定期 | 校准 political_leaning 系数 | 待集成 |
| D204 | MAS 金融素养调查 | MAS | 不定期 | financial_literacy 字段 | 待集成 |
| D205 | GE2025 选区投票结果 | ELD | 每届大选 | constituency + 政治氛围 | 待集成 |
| D206 | OneMap 区域交叉表 | SLA OneMap API | 年度 | 区域级 income×edu×age 校准 | 待集成 |
| D207 | 年龄轨迹调整系数 | Soto 2011 | 固定 | Big Five 年龄变化 | 已集成 |
| D208 | 性别差异系数 | McCrae & Costa 2003 | 固定 | Big Five 性别调整 | 已集成 |
| D209 | MOM 职业工资表 | MOM | 年度(8月) | occupation → 精确收入映射 | 待集成 |
| D210 | 宗教×种族交叉表 | Census 2020 | 10年 | religion 字段 | 待集成 |
| D211 | WVS Singapore | World Values Survey | 不定期 | 行为校准(Phase 6) | 待集成 |
| D212 | 保险渗透率 | LIA Singapore | 年度 | 保险垂直校准 | 待集成 |

**T2 治理规则**：
- 缺失时使用默认值或模型估计，不阻塞增补流程
- 每季度检查一次数据源是否有更新版本
- 新集成时必须走数据源接入检查清单（附录 A）

---

### 2.4 T3 动态层（实时/时效性数据）

| ID | 数据源 | 提供方 | 频率 | 用途 | 缓存策略 | 状态 |
|----|--------|--------|------|------|----------|------|
| D301 | HDB 转售价格 | data.gov.sg API | 季度 | 事件注入：房价变动 | 缓存最近一季 | 待开发(P4) |
| D302 | CPI 物价指数 | data.gov.sg API | 月度 | 事件注入：物价变动 | 缓存最近3月 | 待开发(P4) |
| D303 | CNA/ST 新闻 RSS | 新闻网站 | 实时 | 事件注入：新闻事件 | 不缓存 | 待开发(P4) |
| D304 | LTA 交通客流 | LTA DataMall API | 月度 | commute_mode 验证 | 缓存最近月 | 待开发(P4) |
| D305 | Google Trends | SerpAPI | 实时 | 舆论温度注入 | 按查询缓存24h | 待开发(P4) |

**T3 治理规则**：
- 远程 API 调用：timeout 30s + 重试 3 次 + 降级到缓存
- 每个 T3 数据源必须有本地最近快照作为 fallback
- API 断供时：使用缓存 + 在报告中标注 `data_freshness: stale`

---

### 2.5 T4 运行层（模拟运行产生的数据）

V3 新增分类。这些数据在系统运行过程中产生。

| ID | 数据表 | 描述 | 增长速度 | 保留策略 |
|----|--------|------|----------|----------|
| D401 | agent_memories | Agent 持久记忆 | ~1K 行/次事件注入 | 每 agent 上限 50 条 |
| D402 | simulation_jobs | 模拟任务记录 | ~10-50 行/天 | 永久保留 |
| D403 | agent_responses | Agent 响应详情 | ~200 行/次模拟 | 保留 90 天，之后聚合归档 |
| D404 | events | 外部/手动事件 | ~5-20 行/天 | 永久保留 |
| D405 | social_edges (P3) | 社交网络边 | 一次性生成 ~1.5M | 随人群更新 |

**T4 治理规则**：
- Supabase 自动每日备份（Pro plan 含 7 天备份）
- agent_responses 超 90 天的数据：聚合统计后删除明细，保留 job.result
- agent_memories 超 50 条时，按 importance ASC + created_at ASC 清理
- 每月导出一次全量 backup 到本地

**存储增长模型**：

```
月度存储增长（中度使用）:
  agent_memories: 20次事件注入 × 50K agents受影响 × 200B = 200MB/月
  agent_responses: 600次模拟 × 200人 × 500B = 60MB/月
  simulation_jobs: 600 × 2KB = 1.2MB/月
  events: 300 × 1KB = 0.3MB/月

  → 月增量 ≈ 260MB

  Supabase Pro 8GB 限制:
    基础 agents 表 = 450MB
    剩余可用 = 7.5GB
    可支撑 ≈ 28 个月

  容量策略:
    - agent_responses 90 天清理 → 回收 ~540MB/周期
    - agent_memories 50 条限制 → 最大 148K × 50 × 200B = 1.5GB
    - 实际可用 > 2 年
```

---

## 3. 断供应急方案

### 3.1 风险评估矩阵

| 数据源 | 断供概率 | 断供类型 | 影响 | 应急方案 |
|--------|----------|----------|------|----------|
| NVIDIA HuggingFace | 极低 | 数据集下架 | T0：系统底座丢失 | **已本地下载 274MB parquet，永久可用** |
| SingStat 网站 | 极低 | 临时下线/改版 | T0：验证数据缺失 | 已硬编码，无运行时依赖 |
| MOM 工资表 | 低 | 发布延迟 | T1：收入精度下降 | 用上年 × (1 + 工资增长率 2.5%) |
| CPF Board 费率 | 极低 | 变更 | T1：CPF 计算偏差 | 每年 1 月检查并更新 |
| OneMap API | 中 | API改版/限流 | T2：区域校准缺失 | 降级为全国均匀分布 |
| data.gov.sg API | 低 | 改版 | T3：动态数据缺失 | 使用最近缓存快照 |
| CNA/ST RSS | 中 | 格式变更 | T3：新闻自动采集失败 | 手动注入事件 |
| SerpAPI | 中 | 订阅过期 | T3：Trends 缺失 | 不注入 Trends 数据 |
| DeepSeek API | 中 | 限流/下线 | **调研无法执行** | → 降级链（见 3.2） |
| Supabase | 极低 | 服务中断 | **全系统不可用** | 本地 CSV 备份 + 本地 PostgreSQL |

### 3.2 LLM API 降级链

```
主用: DeepSeek Chat (deepseek-chat)
  ├─ 延迟 < 2s
  ├─ 成本 $0.27/M input + $1.10/M output
  └─ 质量: 优秀（中英文）

降级 1: Gemini 2.5 Flash
  ├─ 免费额度 1500 RPD
  ├─ 付费 $0.10/M input + $0.40/M output
  └─ 质量: 良好

降级 2: 本地 Ollama (Llama 3.1 8B)
  ├─ 成本: $0（仅电费）
  ├─ 延迟: 2-5s/请求
  └─ 质量: 可接受（简短回答）

降级 3: 规则引擎（无 LLM）
  ├─ 成本: $0
  ├─ 延迟: < 1ms
  ├─ 质量: 粗糙但方向正确
  └─ 已实现: engine/llm/decision_engine.py → _fallback_decision()
```

**降级触发条件**：
- API 连续 3 次超时 (30s) → 切换到下一级
- API 返回 429 (Rate Limited) → 等待 60s 后重试，再失败则降级
- API 返回 5xx → 立即降级
- 手动切换：环境变量 `LLM_PROVIDER=deepseek|gemini|ollama|rules`

### 3.3 数据陈旧度监控

| 数据 | 有效期 | 过期处理 |
|------|--------|----------|
| Population Trends | 1年 | 发布后30天内更新，否则标注 `stale` |
| GHS | 5年 | 中间年份用线性插值微调 |
| Census | 10年 | 用 GHS + Population Trends 补充 |
| NPHS | 3年 | 沿用上版，标注年份 |
| MOM 工资表 | 1年 | 用上年 × 通胀系数 |
| HDB 转售价 | 1季 | 用上季缓存 |
| NVIDIA 148K | 永久有效 | 底座数据，不更新 |
| 学术文献 | 永久有效 | 仅在更好元分析发表时替换 |

---

## 4. 数据输入验证

### 4.1 验证层级

```
Level 0: 格式验证（数据能被加载吗？）
Level 1: 完整性验证（所有必要字段都存在吗？）
Level 2: 值域验证（值在合理范围内吗？）
Level 3: 统计验证（分布与已知事实一致吗？）
Level 4: 交叉验证（多个数据源之间一致吗？）
```

### 4.2 T0 数据输入验证（每次增补前自动执行）

| 检查项 | 验证规则 | 阈值 | 失败处理 |
|--------|----------|------|----------|
| NVIDIA parquet 可读 | pd.read_parquet 成功 | — | 阻塞：文件损坏 |
| NVIDIA 行数 | rows >= 140,000 | 最少14万行 | 阻塞 |
| NVIDIA 必要字段 | age, sex, education_level, planning_area, marital_status, race, persona 全部存在 | 精确 | 阻塞 |
| NVIDIA 缺失值率 | 每字段 NaN < 5% | 5% | 警告（> 10% 阻塞） |
| NVIDIA 文件校验 | SHA-256 与首次下载时一致 | 精确 | 警告：文件可能被修改 |
| 边际分布求和 | $\sum p_i = 1.0$ | $\|1 - \sum\| < 10^{-6}$ | 阻塞：自动归一化并警告 |
| 年龄组数量 | len(AGE_LABELS) == 21 | 精确 | 阻塞 |
| 性别比 | M/(M+F) ∈ [0.45, 0.52] | 历史范围 | 警告 |
| 种族分布 | Chinese ∈ [0.70, 0.78] | 历史范围 | 警告 |

### 4.3 T1 数据输入验证

| 检查项 | 验证规则 | 阈值 | 失败处理 |
|--------|----------|------|----------|
| CPT 行求和 | $\sum_v P(v\|parents) = 1$ | $10^{-6}$ | 阻塞：自动归一化 |
| 收入中位数合理性 | CPT 加权中位数 ∈ [$4000, $6000] | GHS范围 | 警告 |
| 相关矩阵正定性 | $\lambda_{\min}(\mathbf{R}) > 0$ | 正定 | 阻塞：Cholesky 分解失败 |
| 相关矩阵对称性 | $R_{ij} = R_{ji}$ | $10^{-10}$ | 阻塞 |
| CPF 贡献率表 | employer + employee = total rate | 精确 | 阻塞 |
| 家户分布求和 | $\sum d_s = 1.0$ | $10^{-4}$ | 自动归一化 |

### 4.4 T3/T4 数据输入验证

| 检查项 | 验证规则 | 阈值 | 失败处理 |
|--------|----------|------|----------|
| API 响应码 | HTTP 200 | 精确 | 使用缓存 |
| API 响应格式 | JSON 可解析 | — | 使用缓存 |
| HDB 价格范围 | $100K < price < $2M | 合理范围 | 过滤异常值 |
| CPI 值域 | 80 < CPI < 150 | 历史范围 | 告警 |
| LLM 响应 JSON | json.loads() 成功 | — | 重试 1 次，再失败则跳过 |
| LLM 选项命中 | response.choice ∈ options | — | 用正则提取最近选项 |

---

## 5. 数据应用结果验证

### 5.1 验证体系总览

```
人群增补结果验证（Phase 0，每次增补后自动执行）
  │
  ├── 5.2 边际分布验证（148K vs Census）
  ├── 5.3 联合分布验证（条件关联）
  ├── 5.4 相关结构验证（符号+量级）
  ├── 5.5 聚合统计验证（中位数、均值）
  ├── 5.6 NVIDIA 原始字段 vs 增补字段一致性
  └── 5.7 交叉验证（多源比对）

调研结果验证（Phase 1+，每次调研后自动执行）
  │
  ├── 5.8 采样代表性验证
  ├── 5.9 回答质量验证
  └── 5.10 回测验证（vs 真实结果）
```

### 5.2 边际分布验证

**对象**：增补后的 148K agent 群体 vs Census/GHS 目标

| 维度 | 目标来源 | 指标 | 硬门阈值 | 软门阈值 |
|------|----------|------|----------|----------|
| 性别 | Population Trends | SRMSE | < 0.10 | < 0.20 |
| 种族 | Population Trends | SRMSE | < 0.10 | < 0.20 |
| 年龄 | Population Trends | SRMSE | < 0.10 | < 0.20 |
| 教育(25+) | GHS 2025 | SRMSE | — | < 0.20 |
| 规划区 | SingStat | SRMSE | — | < 0.20 |
| 住房(增补) | GHS 2025 | SRMSE | — | < 0.20 |
| 收入中位数(增补) | MOM 2025 | 相对偏差 | — | < 25% |
| 婚姻状态 | Population Trends | SRMSE | — | < 0.20 |

**V3 特有验证**：前 5 项（性别/种族/年龄/教育/规划区）是验证 NVIDIA 原始数据与 Census 的一致性。后 3 项（住房/收入/婚姻）是验证我们增补字段的质量。

### 5.3 联合分布验证

| 维度对 | 期望关联 | 指标 | 通过标准 |
|--------|----------|------|----------|
| 年龄 × 教育 | 强关联 | Cramer's V | V > 0.30 |
| 教育 × 住房(增补) | 中等关联 | Cramer's V | V > 0.10 |
| 收入(增补) × 教育 | 强正相关 | Spearman ρ | ρ > 0.30 |
| 收入(增补) × 住房(增补) | 正相关 | Spearman ρ | ρ > 0.20 |
| 年龄 × 婚姻 | 强关联 | Cramer's V | V > 0.40 |
| 种族 × 规划区 | 弱关联 | Cramer's V | V < 0.20 |

### 5.4 相关结构验证（Big Five 增补）

| 变量对 | 期望符号 | 期望量级 | 通过标准 |
|--------|----------|----------|----------|
| O vs E | + | r ~ 0.25 | 符号正确 & r > 0.10 |
| C vs N | - | r ~ -0.30 | 符号正确 & r < -0.15 |
| A vs N | - | r ~ -0.35 | 符号正确 & r < -0.20 |
| risk_appetite vs O | + | — | 符号正确 |
| social_trust vs A | + | — | 符号正确 |
| income(增补) vs education | + | r ~ 0.55 | r > 0.30 |

### 5.5 聚合统计验证

| 统计量 | Census 值 | 容许偏差 | 级别 |
|--------|-----------|----------|------|
| 中位年龄 | 43.2 | ±3 | 硬门 |
| 就业者收入中位数 | $5,000 | ±25% | 软门 |
| 30-34已婚率 | 60% | ±15pp | 硬门 |
| 平均家户规模 | 3.06 | ±1.0 | 硬门 |
| 学位率(25+) | 37.3% | ±5pp | 软门 |
| HDB居住率(增补) | 77.2% | ±5pp | 软门 |

### 5.6 NVIDIA 原始字段 vs 增补字段一致性

V3 特有检查：确保增补字段与 NVIDIA 原始字段逻辑一致。

| 一致性规则 | 验证方法 | 失败处理 |
|------------|----------|----------|
| NVIDIA occupation 与增补 monthly_income 方向一致 | 按 occupation 分组，检查收入排序 | 警告 |
| NVIDIA education_level 与增补 monthly_income 正相关 | Spearman ρ > 0.20 | 警告 |
| NVIDIA marital_status 与增补 household_role 一致 | Married → spouse/head | 阻塞（逻辑错误） |
| NVIDIA age 与增补 life_phase 匹配 | age ∈ phase.age_range | 阻塞 |
| NVIDIA planning_area 与增补 housing_type 合理 | 高端区 Condo 比例 > 全国 | 警告 |
| CPF 月缴 = income × rate(age) | 确定性计算验证 | 阻塞 |

### 5.7 交叉验证（多源比对）

| 维度 | 主数据源 | 交叉验证源 | 比对指标 |
|------|----------|------------|----------|
| 收入分布 | 我们的 CPT 增补 | MOM Occupational Wages | 各分位偏差 < 20% |
| 住房分布 | 我们的 CPT 增补 | GHS 2025 原始表 | 大类占比偏差 < 5pp |
| 规划区人口 | NVIDIA 148K | SingStat 各区人口 | 各区偏差 < 15% |
| 教育分布 | NVIDIA 148K | GHS 2025 | 各级偏差 < 5pp |

### 5.8 采样代表性验证（Phase 1+）

每次模拟运行后，验证抽样样本是否代表总体：

| 检查项 | 方法 | 通过标准 |
|--------|------|----------|
| 年龄分布 | 样本 vs 总体 chi-square | p > 0.05 |
| 性别比例 | 样本 vs 总体 | 偏差 < 5pp |
| 种族比例 | 样本 vs 总体 | 偏差 < 5pp |
| 收入中位数 | 样本 vs 总体 | 偏差 < 20% |
| 规划区覆盖 | 样本覆盖区数 / 总区数 | > 50%（200人采样） |

不通过则在报告中标注 `sample_representativeness: WARN`。

### 5.9 回答质量验证（Phase 1+）

| 检查项 | 方法 | 通过标准 |
|--------|------|----------|
| JSON 解析成功率 | json.loads() | > 95% |
| 选项命中率 | choice ∈ options | > 90% |
| reasoning 非空率 | reasoning 字段非空 | > 95% |
| 回答多样性 | 最高频选项占比 | < 80%（避免 LLM 趋同） |
| 成本合理性 | 单 agent 成本 | < $0.005 |

### 5.10 回测验证

| 事件 | 时间 | 真实结果 | 验证指标 |
|------|------|----------|----------|
| PE2023 总统大选 | 2023.09 | 尚达曼 70.4% | 支持率排名一致 |
| GST 9% 实施 | 2024.01 | 60% 减少消费 | 方向一致 |
| GE2025 大选 | 2025.05 | PAP 65.57% | 支持率排名一致 |

**回测标准**：
- 排序准确性：选项排名与真实一致 → PASS
- 比例准确性：偏差 < 15pp → EXCELLENT
- 方向准确性：多数意见方向正确 → ACCEPTABLE

---

## 6. 运行时数据治理

V3 新增章节。系统运行中产生的数据需要独立治理。

### 6.1 记忆数据治理

| 规则 | 实现 |
|------|------|
| 每 Agent 上限 50 条记忆 | INSERT 前 COUNT，超限时先语义压缩相似记忆（importance ≤ 3 的同类合并为 compressed 摘要），再删 retrieval_score 最低的记忆 |
| compressed 记忆治理 | memory_type=compressed 的记忆保留原始来源 ID 列表（source_memory_ids），可追溯压缩前的原始记忆 |
| 记忆内容不含 PII | LLM 写入记忆前检查：无姓名/NRIC/电话/地址 |
| 记忆可追溯 | 每条记忆关联 source_job_id 或 source_event_id |
| 记忆可清除 | 提供 API：清除某 Agent 全部记忆 / 某次事件的全部记忆 |
| 记忆不跨系统泄露 | agent_memories 表有 RLS，anon key 只读 |
| 记忆表分区策略 | `agent_memories` 按 `created_at` 月度分区（Phase 3+ 启用），90 天以前的记忆自动归档至 `memories_archive`，归档后仅保留 compressed 摘要在主表 |

### 6.2 模拟任务数据治理

| 规则 | 实现 |
|------|------|
| 任务不可删除 | 只能标记 status=cancelled，不可物理删除 |
| 成本追踪 | 每个 job 记录 total_tokens + total_cost_usd |
| 日预算上限 | 每天 LLM 总成本 < $10（可配置） |
| 并发限制 | 同时最多 3 个 running job |

### 6.3 事件数据治理

| 规则 | 实现 |
|------|------|
| 手动事件需审计 | 记录操作者 + 时间 |
| 自动事件需标注来源 | source 字段：rss / api / manual |
| 事件去重 | 24h 内同标题事件不重复写入 |
| 影响向量验证 | 六维向量值 ∈ [-5, 5] |

---

## 7. 数据生命周期管理

### 7.1 数据目录结构

```
data/
  ├── nvidia/                        # T0 底座（不可变）
  │   └── nvidia_personas_singapore.parquet  # 274MB, SHA-256 已记录
  │
  ├── reference/                     # T0+T1 参考数据（版本化）
  │   ├── population_trends_2025/    # v2025.09
  │   ├── ghs_2025/                  # v2025.02
  │   ├── mom_wages_2024/            # v2024.08
  │   └── census_religion_2020/      # v2020
  │
  ├── cache/                         # T3 动态缓存
  │   ├── hdb_resale_2026Q1.json
  │   ├── cpi_202603.json
  │   └── lta_ridership_202602.json
  │
  ├── output/                        # 增补输出（版本化）
  │   ├── agents_148k_v3.csv         # V3 当前版本
  │   ├── agents_20k_v2.csv          # V2 历史版本
  │   └── synthesis_v3_summary.json  # 含数据血缘
  │
  ├── backup/                        # 运行数据月度备份
  │   ├── memories_202603.json
  │   └── jobs_202603.json
  │
  ├── rules/
  │   └── life_ontology.yaml
  │
  └── archive/                       # 退役数据
      └── agents_20k_v1.csv
```

### 7.2 更新日历

| 月份 | 预期更新 | 动作 | 影响 |
|------|----------|------|------|
| 1月 | CPF 费率调整 | 更新 D108 CPF 计算表 | 重新增补 CPF 余额 |
| 2月 | GHS/Income Trends 发布 | 更新 D001-D004, D101-D104 | 重新验证增补结果 |
| 3月 | CPI 年度汇总 | 更新价格基准 | 影响 T3 缓存 |
| 5月 | 大选（若有） | 更新 D205 选区数据 | Phase 6 校准 |
| 6月 | MOM 年度劳动力报告 | 交叉验证收入分布 | 可能微调 CPT |
| 8月 | MOM 职业工资表 | 更新 D209 | Phase 7 保险/银行垂直 |
| 9月 | Population Trends 发布 | 更新 D001-D003 边际分布 | 重新验证 NVIDIA 148K 一致性 |
| 11月 | HES 发布（若有） | 更新 D202 消费支出结构 | Phase 7 消费模拟 |

### 7.3 数据退役规则

| 条件 | 动作 |
|------|------|
| 新版本发布且已验证 | 旧版本移入 `archive/`，保留12个月 |
| 数据源永久下线 | 标注 `deprecated`，冻结最后版本 |
| 学术文献被更权威研究取代 | 评估后替换，记录变更理由 |
| API endpoint 改版 | 更新调用代码，保留旧快照 |

### 7.4 备份策略

| 数据类型 | 备份方式 | 频率 | 保留期 |
|----------|----------|------|--------|
| NVIDIA parquet | 本地 + 云盘双备 | 一次性 | 永久 |
| 增补后 CSV | 每次增补后保存 | 按需 | 永久 |
| Supabase 数据库 | Supabase Pro 自动备份 | 每日 | 7 天 |
| 运行数据导出 | 手动导出 JSON | 每月 | 12 个月 |
| 代码仓库 | Git | 每次提交 | 永久 |

---

## 8. 数据血缘追踪

### 8.1 V3 血缘图

每个 agent 字段都可追溯到数据来源。V3 分为三类：NVIDIA 直接继承、CPT 增补、数学模型生成。

```
═══ NVIDIA 直接继承（无修改）═══

agent.age                ← D005 (NVIDIA parquet) .age
agent.gender             ← D005 .sex → 映射 Male→M, Female→F
agent.ethnicity          ← D005 .race → 映射 Chinese/Malay/Indian/Others
agent.education_level    ← D005 .education_level → 标准化到 7 级
agent.planning_area      ← D005 .planning_area → 标准化到 28 区
agent.marital_status     ← D005 .marital_status
agent.occupation         ← D005 .occupation
agent.industry           ← D005 .industry
agent.persona            ← D005 .persona（完整保留）
agent.professional_persona ← D005 .professional_persona
agent.cultural_background  ← D005 .cultural_background
agent.sports_persona     ← D005 .sports_persona
agent.arts_persona       ← D005 .arts_persona
agent.travel_persona     ← D005 .travel_persona
agent.culinary_persona   ← D005 .culinary_persona
agent.hobbies_and_interests ← D005 .hobbies_and_interests
agent.career_goals       ← D005 .career_goals_and_ambitions

═══ CPT 条件采样增补 ═══

agent.monthly_income
  ← D101 (MOM+GHS CPT) × agent.education_level × agent.age × agent.gender
  ← 三角分布在收入区间内连续化

agent.housing_type
  ← D102 (GHS+HDB CPT) × agent.monthly_income × agent.planning_area

agent.residency_status
  ← D104 (Population in Brief) × age-based adjustment

agent.health_status
  ← D109 (GHS CPT) × agent.age × agent.gender

═══ 数学模型生成 ═══

agent.big5_o/c/e/a/n
  ← D105 (Schmitt 2007 基线) + D207 (Soto 2011 年龄轨迹)
     + D208 (McCrae 2003 性别调整)
  ← D106 (相关矩阵) → Cholesky 分解 → 多元正态采样

agent.risk_appetite / political_leaning / social_trust / religious_devotion
  ← Big Five 推导公式 (personality_init.py)

agent.cpf_oa / cpf_sa / cpf_ma / cpf_ra
  ← D108 (CPF 贡献率) × agent.monthly_income × agent.age × agent.residency_status
  ← cpf_model.py 生命周期模拟

agent.household_id / household_role
  ← D107 (家户分布) × agent.marital_status × agent.age × agent.planning_area
  ← household_builder.py 约束满足

agent.life_phase / agent_type / age_group
  ← D110 (生命阶段本体) × agent.age × agent.health × agent.ns_status
  ← life_rules.py 确定性规则

agent.ns_status
  ← 确定性规则：age + gender + residency_status

agent.commute_mode / has_vehicle
  ← 规则 + 概率：planning_area + monthly_income
```

### 8.2 增补报告元数据

每次增补输出的 `synthesis_v3_summary.json` 必须包含：

```json
{
  "version": "3.0",
  "timestamp": "2026-03-06T14:30:00Z",
  "base_population": {
    "source": "nvidia_personas_singapore.parquet",
    "rows": 148000,
    "sha256": "a1b2c3d4...",
    "fields_inherited": 17,
    "fields_augmented": 15,
    "fields_generated": 8
  },
  "data_lineage": {
    "D001_population_trends": {"version": "2025.09"},
    "D005_nvidia_148k": {"version": "1.0", "rows": 148000},
    "D101_income_cpt": {"version": "GHS2025+MOM2024"},
    "D102_housing_cpt": {"version": "GHS2025"},
    "D105_big5_baseline": {"version": "Schmitt2007"},
    "D106_trait_correlations": {"version": "meta-analysis"},
    "D108_cpf_rates": {"version": "2026"}
  },
  "validation": {
    "hard_gates_passed": 4,
    "hard_gates_total": 4,
    "soft_gates_passed": 8,
    "soft_gates_total": 10,
    "srmse_gender": 0.015,
    "srmse_ethnicity": 0.028,
    "median_income_deviation": "12%"
  },
  "stale_data": [],
  "missing_data": ["D201_nphs", "D209_mom_wages_detailed"],
  "degraded_fields": []
}
```

---

## 9. 治理执行机制

### 9.1 自动化检查点

| 时机 | 执行的检查 | 实现位置 | Phase |
|------|------------|----------|-------|
| **增补前** | T0 输入验证 (4.2) | `augment_nvidia.py` 前置检查 | P0 |
| **增补中** | CPT 归一化、Cholesky 正定性 | `math_core.py` + `personality_init.py` | P0 |
| **增补后** | 全量验证 (5.2-5.7) | `synthesis_gate.py` | P0 |
| **入库后** | 行数验证 + 字段完整性 | `03_seed_supabase.py` | P0 |
| **模拟前** | 样本代表性预检 | `sampler.py` | P1 |
| **模拟后** | 回答质量 + 代表性 (5.8-5.9) | `aggregator.py` | P1 |
| **事件注入后** | 记忆写入完整性 | `memory_manager.py` | P2 |
| **每日** | 成本监控 + 预算检查 | 计划任务 | P1 |
| **每月** | 运行数据备份 + 存储监控 | 计划任务 | P2 |
| **每季** | 数据陈旧度扫描 | 计划任务 | P0 |
| **每年** | 全量数据源审计 | 人工审查 + 更新日历 | P0 |

### 9.2 告警级别

| 级别 | 含义 | 动作 |
|------|------|------|
| **BLOCK** | 硬门失败 | 增补/模拟拒绝输出，必须修复 |
| **WARN** | 软门失败或数据陈旧 | 输出但标注警告 |
| **INFO** | 统计偏差在容许范围内 | 记录日志 |
| **STALE** | 数据超过有效期 | 标注在报告中，提示更新 |
| **BUDGET** | LLM 成本接近日预算 | 暂停模拟，等待次日或手动放行 |

### 9.3 变更管理

任何数据源或增补逻辑的变更必须记录：

| 字段 | 说明 |
|------|------|
| change_id | 唯一编号 |
| date | 变更日期 |
| data_id | 受影响的数据 ID（D001-D405） |
| change_type | 新增 / 更新 / 退役 / 降级 |
| old_value | 变更前（版本/值） |
| new_value | 变更后 |
| reason | 变更原因 |
| impact | 影响范围（哪些 agent 字段需要重新增补） |
| validation | 变更后的验证结果 |

### 9.4 数据质量仪表盘指标

| 指标 | 计算方式 | Phase 0 目标 | Phase 6 目标 |
|------|----------|-------------|-------------|
| 数据完整率 | 已集成 / 计划数据源 | > 60% (15/25) | > 85% |
| 数据新鲜度 | 未过期 / 全部数据源 | > 90% | > 95% |
| 硬门通过率 | 硬门通过 / 硬门总数 | 100% | 100% |
| 软门通过率 | 软门通过 / 软门总数 | > 70% | > 90% |
| 回测方向准确率 | 方向正确 / 已验证事件 | > 60% | > 80% |
| LLM 响应质量 | JSON 解析成功率 | > 95% | > 99% |
| 记忆健康度 | 平均记忆数 / 上限 | — | < 60% |
| 日成本控制 | 实际 / 预算 | < 100% | < 80% |

---

## 附录 A: 新数据源接入检查清单

- [ ] 确认数据源的许可证/使用条款
- [ ] 确定数据分级（T0/T1/T2/T3/T4）
- [ ] 设计本地缓存/硬编码策略
- [ ] 编写断供应急方案
- [ ] 定义输入验证规则（格式/完整性/值域）
- [ ] 定义应用结果验证规则（与已有维度的一致性检查）
- [ ] 设计交叉验证方案（至少一个独立数据源比对）
- [ ] 记录数据血缘（该数据如何流向哪些 agent 字段）
- [ ] 添加到更新日历
- [ ] 添加到变更管理记录
- [ ] 估算存储增量和成本影响
- [ ] 更新 synthesis_summary.json 的 data_lineage 部分

## 附录 B: NVIDIA 148K 字段映射表

| NVIDIA 原始字段 | 我们的标准字段 | 映射规则 |
|----------------|---------------|----------|
| sex | gender | Male→M, Female→F |
| race | ethnicity | Chinese/Malay/Indian/Others |
| education_level | education_level | 标准化到 7 级 |
| planning_area | planning_area | 标准化到 28 区 |
| marital_status | marital_status | Single/Married/Divorced/Widowed |
| age | age | 直接取整 |
| persona | persona | 原文保留 |
| professional_persona | professional_persona | 原文保留 |
| cultural_background | cultural_background | 原文保留 |
| sports_persona | sports_persona | 原文保留 |
| arts_persona | arts_persona | 原文保留 |
| travel_persona | travel_persona | 原文保留 |
| culinary_persona | culinary_persona | 原文保留 |
| hobbies_and_interests | hobbies_and_interests | 原文保留 |
| career_goals_and_ambitions | career_goals | 原文保留 |
| occupation | occupation | 原文保留 |
| industry | industry | 原文保留 |
| religion | religion | 部分 agent 有值 |
