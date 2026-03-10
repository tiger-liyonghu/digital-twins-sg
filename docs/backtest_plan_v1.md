# Backtest Plan: 三个优先级案例
# Digital Twins Singapore — 行为验证基线

> Version: 1.0
> Date: 2026-03-06
> 目标: 用真实新加坡调查数据验证 148K Agent 的行为准确性

---

## 总体方法论

### 验证原则

每个案例遵循相同流程：

```
1. 获取真实调查的原始问题和选项
2. 用完全相同的问题作为 simulation_job 的 question
3. 用分层抽样采样 200 agent（匹配真实调查的人口构成）
4. 对比 agent 回答分布 vs 真实调查分布
5. 计算准确率指标
```

### 准确率指标定义

| 指标 | 公式 | 含义 | 目标 |
|------|------|------|------|
| **方向准确率** | 真实排名前3项中，agent排名也在前3的比例 | 大趋势是否对 | > 70% |
| **比例偏差 (MAE)** | Σ|agent% - real%| / N | 平均每个选项偏多少百分点 | < 10pp |
| **分段一致性** | 各人口分段中方向准确率的平均值 | 不同人群是否都对 | > 60% |
| **排序相关 (Spearman)** | ρ(agent排名, real排名) | 整体排序是否一致 | > 0.7 |

### 采样策略

每个案例采 200 agent，按以下维度分层：

```python
sampling_config = {
    "sample_size": 200,
    "sampling_method": "stratified",
    "strata": {
        "age_group": {
            "18-24": 0.10,   # Gen Z
            "25-34": 0.20,   # Millennials
            "35-44": 0.20,   # Gen X (young)
            "45-54": 0.20,   # Gen X (old)
            "55-64": 0.15,   # Baby Boomers (young)
            "65+":   0.15    # Baby Boomers (old)
        },
        "ethnicity": {
            "Chinese": 0.74,
            "Malay": 0.135,
            "Indian": 0.09,
            "Others": 0.035
        },
        "gender": {
            "Male": 0.486,
            "Female": 0.514
        }
    }
}
```

---

## 案例 1: GST 8%→9% 消费削减反应

### 1.1 真实数据来源

**调查方:** YouGov RealTime Omnibus
**样本:** 1,022 名新加坡成年人 (18+), 按年龄/性别/种族加权
**时间:** 2022 年 2 月 10 日
**方法:** 线上调查
**公开来源:** https://sg.yougov.com/consumer/articles/41082-GST-increase-consumer-spending-impact-survey-poll

### 1.2 真实数据: 整体消费态度

**问题 Q1:** "GST 上调后，你计划如何调整总体消费？"

| 选项 | 真实比例 |
|------|---------|
| 减少消费 | 48.3% |
| 维持现有消费 | 32.5% |
| 增加消费 | 5.3% |
| 未决定 | 14.1% |

### 1.3 真实数据: 消费削减品类（在计划减少消费的人群中）

**问题 Q2:** "你最可能在以下哪些品类减少消费？（多选）"

| 品类 | 真实比例 |
|------|---------|
| 餐饮/外卖 (F&B dining & takeaway) | 50.1% |
| 服装/鞋包 (Clothing & apparel) | 48.7% |
| 外卖配送 (Food delivery) | 48.3% |
| 网约车 (Ride-hailing) | 44.5% |
| IT 产品 (IT gadgets) | 36.6% |
| 美容/健身 (Grooming & wellness) | 33.5% |
| 家具 (Home furniture) | 28.7% |
| 个护产品 (Personal care) | 28.4% |
| 家电 (Household electronics) | 27.6% |
| 游戏 (Video games) | 25.4% |
| 装修 (Home renovation) | 24.9% |

### 1.4 真实数据: 代际差异（最可能削减的第一品类）

**问题 Q3:** "以上品类中，你最优先削减哪个？（单选）"

| 代际 | 最优先削减品类 |
|------|--------------|
| Gen Z (1997-2012) | 外卖配送 |
| Millennials (1981-1996) | 外卖配送 |
| Gen X (1965-1980) | 餐饮/外卖 |
| Baby Boomers (1946-1964) | 服装/鞋包 |

### 1.5 Simulation Job 设计

#### Job 1A: 整体消费态度

```python
job_1a = {
    "title": "BT-GST-01A: GST 9% 整体消费态度",
    "mode": "survey",
    "question": (
        "The Singapore government has announced that GST will increase "
        "from 8% to 9% starting January 1, 2024. This is the second phase "
        "of the GST hike (the first was from 7% to 8% in January 2023). "
        "How do you plan to adjust your overall spending after this GST increase?"
    ),
    "options": [
        "I will reduce my spending",
        "I will maintain my current spending",
        "I will increase my spending",
        "I am not sure / undecided"
    ],
    "context": (
        "Background: GST (Goods and Services Tax) is applied to most goods "
        "and services in Singapore. The government has introduced an Assurance "
        "Package to cushion the impact, including cash payouts and CDC vouchers. "
        "Singapore's inflation was around 4-5% in 2023."
    ),
    "sample_size": 200,
    "sampling_method": "stratified"
}
```

**真实基准 (ground truth):**
```python
ground_truth_1a = {
    "I will reduce my spending": 48.3,
    "I will maintain my current spending": 32.5,
    "I will increase my spending": 5.3,
    "I am not sure / undecided": 14.1
}
```

#### Job 1B: 消费削减品类

```python
job_1b = {
    "title": "BT-GST-01B: GST 9% 消费削减品类",
    "mode": "survey",
    "question": (
        "Given the GST increase from 8% to 9%, which of the following "
        "spending categories are you most likely to cut back on in the "
        "next 12 months? Pick up to 3 categories."
    ),
    "options": [
        "Dining and takeaway at F&B outlets",
        "Clothing, footwear and apparel",
        "Food delivery orders",
        "Ride-hailing (Grab, Gojek etc)",
        "IT gadgets and electronics",
        "Grooming and wellness (hair, spa, massage)",
        "Home furniture",
        "Personal care products",
        "Household electronics and appliances",
        "Video games and consoles",
        "Home renovation services"
    ],
    "context": "Same as Job 1A",
    "sample_size": 200,
    "sampling_method": "stratified",
    # 注意：这是多选题，需要在 prompt 中明确说明 "pick up to 3"
    "response_format": "multi_select_3"
}
```

**真实基准:**
```python
ground_truth_1b = {
    "Dining and takeaway at F&B outlets": 50.1,
    "Clothing, footwear and apparel": 48.7,
    "Food delivery orders": 48.3,
    "Ride-hailing (Grab, Gojek etc)": 44.5,
    "IT gadgets and electronics": 36.6,
    "Grooming and wellness (hair, spa, massage)": 33.5,
    "Home furniture": 28.7,
    "Personal care products": 28.4,
    "Household electronics and appliances": 27.6,
    "Video games and consoles": 25.4,
    "Home renovation services": 24.9
}
```

#### Job 1C: 代际差异——最优先削减品类

对每个代际分段单独跑一组：

```python
job_1c_genz = {
    "title": "BT-GST-01C-GenZ: GST 消费削减优先级 (Gen Z)",
    "question": (
        "Given the GST increase, among the spending categories you would "
        "cut back on, which ONE category would you most likely reduce first?"
    ),
    "options": [
        "Dining and takeaway at F&B outlets",
        "Clothing, footwear and apparel",
        "Food delivery orders",
        "Ride-hailing",
        "IT gadgets",
        "Grooming and wellness"
    ],
    "target_filter": {"age_min": 18, "age_max": 27},
    "sample_size": 50
}

# 同理创建 job_1c_millennials, job_1c_genx, job_1c_boomers
# 各 50 agent，对应不同 age_min/age_max
```

**真实基准:**
```python
ground_truth_1c = {
    "GenZ":       {"top_1": "Food delivery orders"},
    "Millennials": {"top_1": "Food delivery orders"},
    "GenX":       {"top_1": "Dining and takeaway at F&B outlets"},
    "Boomers":    {"top_1": "Clothing, footwear and apparel"}
}
```

### 1.6 评估脚本

```python
def evaluate_gst_backtest(job_result, ground_truth):
    """评估 GST backtest 结果"""
    metrics = {}

    # 1. 比例偏差 (MAE)
    total_abs_error = 0
    for option, real_pct in ground_truth.items():
        agent_pct = job_result.get(option, 0)
        total_abs_error += abs(agent_pct - real_pct)
    metrics["mae_pp"] = total_abs_error / len(ground_truth)

    # 2. 方向准确率：真实 top-3 vs agent top-3
    real_top3 = sorted(ground_truth, key=ground_truth.get, reverse=True)[:3]
    agent_top3 = sorted(job_result, key=job_result.get, reverse=True)[:3]
    overlap = len(set(real_top3) & set(agent_top3))
    metrics["direction_accuracy"] = overlap / 3

    # 3. Spearman 排序相关
    from scipy.stats import spearmanr
    real_ranks = [ground_truth[k] for k in sorted(ground_truth)]
    agent_ranks = [job_result.get(k, 0) for k in sorted(ground_truth)]
    rho, p_val = spearmanr(real_ranks, agent_ranks)
    metrics["spearman_rho"] = rho
    metrics["spearman_p"] = p_val

    # 4. 代际方向准确率（Job 1C 用）
    # 检查每个代际的 top-1 是否匹配真实数据

    return metrics
```

### 1.7 通过标准

| 指标 | 最低要求 | 良好 | 优秀 |
|------|---------|------|------|
| Job 1A 比例偏差 (MAE) | < 12pp | < 8pp | < 5pp |
| Job 1B Spearman ρ | > 0.60 | > 0.75 | > 0.85 |
| Job 1B 方向准确率 (top-3) | 2/3 | 3/3 | 3/3 |
| Job 1C 代际方向准确率 | 2/4 正确 | 3/4 正确 | 4/4 正确 |

### 1.8 如果不通过怎么办

| 问题 | 诊断 | 修复 |
|------|------|------|
| 整体比例偏差大 | Persona prompt 不够强调经济敏感度 | 在 context 中加入更多新加坡生活成本数据 |
| 代际差异不明显 | Agent 的年龄对消费偏好的影响不够 | 在 persona 中强化代际消费特征（kiasu uncle vs 数字原住民）|
| 排序错误 | LLM 对新加坡消费品类的认知偏差 | 在 system prompt 中加入新加坡零售结构知识 |
| 低收入群体不够敏感 | income 维度在 prompt 中权重不够 | 在 prompt 中明确计算 GST 对该收入的实际金额影响 |

---

## 案例 2: UOB ASEAN 消费者信心调查 (2024)

### 2.1 真实数据来源

**调查方:** UOB (ASEAN Consumer Sentiment Study 2024)
**样本:** 1,000 名新加坡消费者
**时间:** 2024 年 5-6 月
**公开来源:** https://www.uobgroup.com/asean-insights/articles/acss-2024-singapore.page

### 2.2 真实数据: 经济情绪

**Q1: 当前经济情绪**

| 情绪 | 真实比例 |
|------|---------|
| 积极 (Positive) | 68% |
| 消极 (Negative) | 32% |

对比 2023 年：积极仅 48%，一年内上升 20 个百分点。

**Q2: 经济衰退预期**

| 选项 | 真实比例 |
|------|---------|
| 认为未来 6-12 个月可能衰退 | 58% |
| 认为不太可能衰退 | 42% |

对比 2023 年：衰退预期 68%，下降 10 个百分点。

### 2.3 真实数据: 储蓄行为

**Q3: 每月储蓄占收入比**

| 选项 | 真实比例 |
|------|---------|
| 储蓄超过收入 20% | 50% (总体) |

**按代际:**

| 代际 | 储蓄超过 20% 的比例 |
|------|-------------------|
| Gen Z | 60% |
| Gen Y (Millennials) | 52% |
| Gen X | ~45% (估算) |
| Boomers | ~40% (估算) |

**Q4: 应急基金**

| 选项 | 真实比例 |
|------|---------|
| 有应急基金 | 92% |
| 其中有 3 个月以上支出 | 60% |

**Q5: 退休规划**

| 选项 | 真实比例 |
|------|---------|
| 对退休所需资金有相当/很好的了解 | 70% |

### 2.4 真实数据: 消费忧虑

**Q6: 最担忧的财务问题 (top concerns)**

| 忧虑 | 排名 |
|------|------|
| 通胀上升 | #1 |
| 家庭开支增加 | #2 |
| GST 上调 | #3 |
| 工作相关忧虑 | #4 (近六成) |

工作忧虑细分: 担心找不到更好的工作、可能被减薪。

### 2.5 Simulation Job 设计

#### Job 2A: 经济情绪

```python
job_2a = {
    "title": "BT-UOB-02A: 新加坡经济情绪",
    "question": (
        "How do you feel about Singapore's current economic situation? "
        "Consider factors like job market, cost of living, inflation, "
        "and the overall business environment."
    ),
    "options": [
        "Very positive",
        "Somewhat positive",
        "Somewhat negative",
        "Very negative"
    ],
    "context": (
        "It is mid-2024. Singapore's economy grew 2.7% year-on-year in Q1 2024. "
        "GST was raised from 8% to 9% in January 2024. "
        "Inflation has moderated from the 2022-2023 highs but remains above pre-COVID levels. "
        "The job market is stable with unemployment at around 2%."
    ),
    "sample_size": 200,
    "sampling_method": "stratified"
}
```

**聚合时:** "Very positive" + "Somewhat positive" = Positive，对标 UOB 的 68%。

**真实基准:**
```python
ground_truth_2a = {
    "positive": 68.0,  # Very positive + Somewhat positive
    "negative": 32.0   # Somewhat negative + Very negative
}
```

#### Job 2B: 衰退预期

```python
job_2b = {
    "title": "BT-UOB-02B: 经济衰退预期",
    "question": (
        "Do you think Singapore is likely to face an economic recession "
        "within the next 6 to 12 months?"
    ),
    "options": [
        "Very likely",
        "Somewhat likely",
        "Somewhat unlikely",
        "Very unlikely"
    ],
    "context": "Same context as Job 2A",
    "sample_size": 200
}
```

**真实基准:**
```python
ground_truth_2b = {
    "likely": 58.0,    # Very likely + Somewhat likely
    "unlikely": 42.0   # Somewhat unlikely + Very unlikely
}
```

#### Job 2C: 储蓄行为

```python
job_2c = {
    "title": "BT-UOB-02C: 月度储蓄率",
    "question": (
        "What percentage of your monthly income do you save each month? "
        "Include contributions to savings accounts, investments, and "
        "any other forms of savings, but exclude CPF contributions."
    ),
    "options": [
        "Less than 10%",
        "10% to 20%",
        "More than 20%",
        "I don't save regularly"
    ],
    "sample_size": 200
}
```

**真实基准:**
```python
ground_truth_2c = {
    "More than 20%": 50.0
}
# 按代际分段对比：GenZ 60%, GenY 52%
```

#### Job 2D: 应急基金

```python
job_2d = {
    "title": "BT-UOB-02D: 应急基金",
    "question": (
        "Do you have an emergency fund (money set aside for unexpected "
        "expenses or financial emergencies)? If so, how many months of "
        "living expenses does it cover?"
    ),
    "options": [
        "No emergency fund",
        "Less than 3 months of expenses",
        "3 to 6 months of expenses",
        "More than 6 months of expenses"
    ],
    "sample_size": 200
}
```

**真实基准:**
```python
ground_truth_2d = {
    "has_emergency_fund": 92.0,       # 后三个选项之和
    "has_3_months_plus": 60.0         # 后两个选项之和
}
```

#### Job 2E: 最大财务忧虑

```python
job_2e = {
    "title": "BT-UOB-02E: 最大财务忧虑",
    "question": (
        "What are your biggest financial concerns right now? "
        "Pick the top 2 that weigh most on your mind."
    ),
    "options": [
        "Rising inflation / cost of living",
        "Increased household expenses",
        "GST increase impact",
        "Job security / finding a better job",
        "Retirement planning",
        "Housing costs / mortgage",
        "Healthcare costs",
        "Children's education costs"
    ],
    "sample_size": 200,
    "response_format": "multi_select_2"
}
```

**真实基准:**
```python
ground_truth_2e_ranking = [
    "Rising inflation / cost of living",           # #1
    "Increased household expenses",                 # #2
    "GST increase impact",                          # #3
    "Job security / finding a better job"           # #4
]
```

### 2.6 通过标准

| 指标 | 最低要求 | 良好 | 优秀 |
|------|---------|------|------|
| 经济情绪正面比例偏差 | < 15pp | < 10pp | < 5pp |
| 衰退预期比例偏差 | < 15pp | < 10pp | < 5pp |
| 储蓄率 >20% 偏差 | < 15pp | < 10pp | < 5pp |
| 储蓄率代际排序 | 方向正确 | ρ > 0.7 | ρ > 0.9 |
| 应急基金比例偏差 | < 10pp | < 7pp | < 5pp |
| 忧虑排名 Spearman ρ | > 0.5 | > 0.7 | > 0.85 |

### 2.7 特别分析: 收入分段

UOB 数据暗示了明显的收入效应。额外跑以下分段:

```python
income_segments = [
    {"label": "Low income",    "target_filter": {"income_max": 3000}},
    {"label": "Middle income", "target_filter": {"income_min": 3001, "income_max": 8000}},
    {"label": "High income",   "target_filter": {"income_min": 8001}}
]
```

预期: 低收入群体衰退忧虑更高、储蓄率更低、财务忧虑集中在 cost of living。

---

## 案例 3: IPS 种族与宗教和谐调查 (2024)

### 3.1 真实数据来源

**调查方:** Institute of Policy Studies (IPS) + OnePeople.sg
**报告:** IPS Working Papers No. 59 (February 2025)
**样本:** 新加坡公民和 PR, 18 岁以上, 按种族和年龄加权
**公开来源:** https://lkyspp.nus.edu.sg/ips/research/surveys
**受访者补偿:** $20 (PayNow 或现金)

### 3.2 真实数据

**Q1: 种族多样性是否有益**

| 选项 | 真实比例 |
|------|---------|
| 同意/非常同意种族多样性对新加坡有益 | 71.1% |

对比 2018 年: 66.7%（上升 4.4pp）。

**按种族:**

| 种族 | 同意比例 | 说明 |
|------|---------|------|
| Malay | 最高 | 少数族裔更重视多样性 |
| Indian | 较高 | 同上 |
| Chinese | 较低 | 多数族群 |

**Q2: 种族/宗教紧张感**

| 选项 | 真实比例 |
|------|---------|
| 日常生活中没有经历种族/宗教紧张 | > 80% |

**Q3: 职场舒适度**

| 选项 | 真实比例 |
|------|---------|
| 与不同种族/宗教背景的人共事感到舒适 | > 90% |

**Q4: 年龄效应**

| 年龄段 | 感知和谐程度 |
|--------|------------|
| 年长者 | 更可能报告高/非常高的和谐水平 |
| 年轻者 | 和谐感知较低（但仍为正面） |

**Q5: 年轻人的看法**

年轻受访者更倾向于认为华人和欧亚裔不需要那么努力就能成功，而马来和印度裔需要更加努力。

**Q6: 种族间努力认知的变化**

认为"所有种族需要同等努力才能成功"的比例（按种族）:

| 种族 | 曾认为某些种族更不受歧视的比例 | 趋势 |
|------|---------------------------|------|
| Malay | 25.7% | 较2018年略降 |
| Indian | 21.7% | 较2018年略降 |

### 3.3 Simulation Job 设计

#### Job 3A: 种族多样性价值

```python
job_3a = {
    "title": "BT-IPS-03A: 种族多样性价值认知",
    "question": (
        "To what extent do you agree with the following statement: "
        "'Racial diversity is beneficial for Singapore'?"
    ),
    "options": [
        "Strongly agree",
        "Agree",
        "Neutral",
        "Disagree",
        "Strongly disagree"
    ],
    "context": (
        "Singapore is a multi-racial society with Chinese (~74%), Malay (~13.5%), "
        "Indian (~9%), and Others (~3.5%). The government promotes racial harmony "
        "through policies like HDB ethnic integration, bilingual education, and "
        "racial harmony day."
    ),
    "sample_size": 200,
    "sampling_method": "stratified"
}
```

**真实基准:**
```python
ground_truth_3a = {
    "agree_or_strongly_agree": 71.1,
    # 按种族分段:
    "by_ethnicity": {
        "Malay":   {"agree_plus": "highest"},
        "Indian":  {"agree_plus": "high"},
        "Chinese": {"agree_plus": "lowest_among_3"}
    }
}
```

#### Job 3B: 日常紧张感

```python
job_3b = {
    "title": "BT-IPS-03B: 日常种族/宗教紧张感",
    "question": (
        "In your daily life in Singapore, do you experience any racial "
        "or religious tensions? This could include at work, in your "
        "neighbourhood, on public transport, or in social settings."
    ),
    "options": [
        "I never experience any tensions",
        "I rarely experience tensions",
        "I sometimes experience tensions",
        "I frequently experience tensions"
    ],
    "sample_size": 200
}
```

**真实基准:**
```python
ground_truth_3b = {
    "no_tension": 80.0  # "never" + "rarely" 应 > 80%
}
```

#### Job 3C: 职场多元舒适度

```python
job_3c = {
    "title": "BT-IPS-03C: 职场多元文化舒适度",
    "question": (
        "How comfortable are you working alongside colleagues from "
        "different racial and religious backgrounds?"
    ),
    "options": [
        "Very comfortable",
        "Comfortable",
        "Neutral",
        "Uncomfortable",
        "Very uncomfortable"
    ],
    "sample_size": 200
}
```

**真实基准:**
```python
ground_truth_3c = {
    "comfortable_plus": 90.0  # "Very comfortable" + "Comfortable" > 90%
}
```

#### Job 3D: 种族间机会平等感知 (按种族分段)

```python
job_3d = {
    "title": "BT-IPS-03D: 种族间努力与成功",
    "question": (
        "In Singapore, do you think people of all races need to work "
        "equally hard to achieve success in life, or do some races have "
        "it easier than others?"
    ),
    "options": [
        "All races need to work equally hard",
        "Some races have it easier (Chinese / Eurasians have advantages)",
        "Some races face more barriers (Malays / Indians need to work harder)",
        "It depends on the individual, not race"
    ],
    "sample_size": 200
}
```

**按种族分段跑:** 分别为 Chinese (100), Malay (40), Indian (40), Others (20) 各跑一组。

**真实基准:**
```python
ground_truth_3d = {
    # 年轻人更倾向于选"Some races have it easier"
    # 马来/印度裔更可能感受到不平等
    "by_age": {
        "young": "more likely to perceive inequality",
        "old": "more likely to say equal effort"
    },
    "by_ethnicity": {
        "Malay": {"perceive_harder": 25.7},   # 25.7% 认为马来人需要更努力
        "Indian": {"perceive_harder": 21.7}    # 21.7% 认为印度人需要更努力
    }
}
```

### 3.4 通过标准

| 指标 | 最低要求 | 良好 | 优秀 |
|------|---------|------|------|
| 多样性有益同意率偏差 | < 15pp | < 10pp | < 5pp |
| 种族排序 (谁更重视多样性) | 方向正确 | 3种族排序全对 | 比例偏差<5pp |
| 无紧张感 >80% | 达标 | > 85% | > 90% |
| 职场舒适度 >90% | 达标 | > 92% | > 95% |
| 年龄效应方向 | 正确 | 显著 | p<0.05 |
| 少数族裔感知差异 | 方向正确 | 比例偏差<10pp | 比例偏差<5pp |

### 3.5 此案例的特殊价值

这个案例测试的不是消费行为，而是**社会态度**。如果你的 agent 在消费行为和社会态度两个完全不同的维度上都能匹配真实数据，说明 148K 底座的人格建模（Big Five + cultural_background + ethnicity）是有效的——不是只对"买东西"有效。

---

## 执行时间表

```
Day 1 (准备):
  ├── 确认 148K agents 已入库
  ├── 确认 job_runner 可正常运行
  ├── 编写 backtest_runner.py (批量提交上述所有 job)
  └── 编写 evaluate_backtest.py (自动计算所有指标)

Day 2 (执行案例1 + 案例2):
  ├── 运行 Job 1A, 1B, 1C (GST)    → ~600 agent calls → ~$0.20
  ├── 运行 Job 2A-2E (UOB)          → ~1000 agent calls → ~$0.35
  ├── 初步分析结果
  └── 如有严重偏差，调整 persona prompt 后重跑

Day 3 (执行案例3 + 综合分析):
  ├── 运行 Job 3A-3D (IPS)          → ~800 agent calls → ~$0.28
  ├── 综合分析三个案例
  ├── 生成 Backtest Report
  └── 标记需要修复的维度

总 LLM 成本: ~$0.83 (约 2400 次 DeepSeek 调用)
```

---

## 输出: Backtest Report 模板

```markdown
# Digital Twins Singapore — Backtest Report v1.0
# Date: YYYY-MM-DD

## 总体结果

| 案例 | 方向准确率 | 平均比例偏差 | Spearman ρ | 通过? |
|------|-----------|------------|-----------|------|
| GST 消费态度 | X/4 | X.Xpp | 0.XX | Y/N |
| GST 品类排序 | X/3 | X.Xpp | 0.XX | Y/N |
| GST 代际差异 | X/4 | N/A | N/A | Y/N |
| UOB 经济情绪 | N/A | X.Xpp | N/A | Y/N |
| UOB 衰退预期 | N/A | X.Xpp | N/A | Y/N |
| UOB 储蓄率 | N/A | X.Xpp | N/A | Y/N |
| UOB 忧虑排名 | X/4 | X.Xpp | 0.XX | Y/N |
| IPS 多样性价值 | N/A | X.Xpp | N/A | Y/N |
| IPS 种族排序 | X/3 | N/A | 0.XX | Y/N |
| IPS 紧张感 | N/A | X.Xpp | N/A | Y/N |
| IPS 职场舒适度 | N/A | X.Xpp | N/A | Y/N |

## 综合评分

整体行为验证准确率 = (通过指标数 / 总指标数) × 100 = XX%

## 最强维度: [...]
## 最弱维度: [...]
## 改进建议: [...]
```

---

## 最终产出: 对客户展示时的叙事

```
"我们用 11 个不同维度测试了我们的 148,000 个虚拟新加坡居民——

  涵盖消费行为（GST 反应）、经济信心（衰退预期和储蓄习惯）、
  以及社会态度（种族和谐）三个完全不同的领域。

  在 11 个指标中，X 个达到'良好'以上水准。

  我们的虚拟新加坡人知道:
  - Baby Boomers 更可能削减服装消费而不是外卖
  - Gen Z 储蓄率其实比 Boomers 更高
  - 马来和印度裔比华人更重视种族多样性
  - 年轻人比年长者更能感受到种族间的不平等

  这不是 ChatGPT 猜出来的。这是 148,000 个有完整人生画像的
  虚拟居民，基于新加坡真实的人口统计和文化特征做出的判断。"
```
