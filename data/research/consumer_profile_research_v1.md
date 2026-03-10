# Consumer/Retail Domain Research — Singapore Digital Twins
## Deep Research Report v1.0 (2026-03-10)

---

# 1. 数据源总览

| 数据源 | 关键数据 | 质量等级 |
|--------|----------|----------|
| **SingStat HES 2023**（家庭支出调查） | 支出分类、按收入五分位/住房类型/户主年龄 | **P0** — 官方金标准，5年一次 |
| **LTA 年度车辆统计 2025** | 车辆保有量、按类型、新注册 | P0 — 官方 |
| **IMDA 数字社会报告 2023** | 智能手机/互联网/数字采纳率按年龄 | P1 — 官方 |
| **DataReportal Digital 2025 Singapore** | 社交媒体用户数、平台渗透率、日均使用时长 | P1 — 综合 |
| **Statista/Rakuten Insight 调查** | 消费者偏好、品牌忠诚度、外卖使用、有机食品 | P2 — 调查数据 |
| **YouGov Singapore** | 忠诚度计划、可持续消费意愿 | P2 — 调查数据 |
| **Momentum Works SEA 电商报告** | 电商平台GMV、市场份额 | P2 — 行业报告 |
| **PwC/Simon-Kucher 全球可持续发展调查** | 绿色溢价支付意愿 | P2 — 全球报告含新加坡 |
| **PTC 票价审核报告 2024** | 低收入家庭交通支出占比 | P2 — 专项报告 |
| **NapoleonCat 社交媒体统计** | Facebook/Instagram 按年龄性别 | P2 — 第三方追踪 |

---

# 2. HES 2023 核心支出数据（官方金标准）

## 2.1 总体月均家庭支出

| 指标 | 2012/13 | 2017/18 | 2023 |
|------|---------|---------|------|
| **总月均支出** | $4,768 | $5,163 | **$5,931** |
| 含隐含租金 | $5,815 | $6,161 | $7,119 |

## 2.2 按收入五分位

| 收入五分位 | 月均支出 | 月均收入 | 支出/收入比 |
|-----------|---------|---------|-----------|
| 1st-20th（最低） | $3,233 | $3,254 | 99.4% |
| 21st-40th | $4,401 | $7,961 | 55.3% |
| 41st-60th | $5,916 | $13,058 | 45.3% |
| 61st-80th | $6,981 | $18,751 | 37.2% |
| 81st-100th（最高） | $9,125 | $34,341 | 26.6% |

**[HARD] 来源: SingStat HES 2023 Key Indicators**

## 2.3 按住房类型

| 住房类型 | 月均支出 | 月均收入 |
|---------|---------|---------|
| HDB 组屋 | $4,657 | $11,652 |
| 公寓 | $9,567 | $25,707 |
| 洋房 | $13,545 | $40,884 |

## 2.4 按消费类别（2023）

| 类别 | 月均支出(S$) | 占比 |
|------|-------------|------|
| 食品和餐饮服务 | 1,422 | 24.0% |
| -- 食品和非酒精饮料（在家） | 456 | 7.7% |
| -- 餐饮服务（外出就餐） | 966 | 16.3% |
| 住房及相关 | 2,122 | 35.8% |
| 交通 | 951 | 16.0% |
| 信息和通信 | 270 | 4.6% |
| 休闲/运动/文化 | 335 | 5.6% |
| 教育 | 404 | 6.8% |
| 健康 | 474 | 8.0% |
| 服装和鞋类 | 120 | 2.0% |
| 保险和金融服务 | 590 | 9.9% |
| **合计** | **5,931** | **100%** |

**[HARD] 来源: SingStat HES 2023 Key Indicators**

## 2.5 消费耐用品拥有率

| 耐用品 | 2012/13 | 2017/18 | 2023 |
|--------|---------|---------|------|
| **汽车** | 42.1% | 35.3% | **36.3%** |
| 摩托车 | 7.9% | 7.2% | 6.8% |
| 手机 | 97.0% | 98.0% | **99.1%** |
| 互联网接入 | 78.0% | 87.3% | **90.8%** |
| 空调 | 76.1% | 79.7% | 81.9% |
| 烘干机 | 13.3% | 19.2% | **27.8%** |

**[HARD] 来源: SingStat HES 2023 Key Indicators**

---

# 3. 逐字段深度研究

## 字段 1: monthly_grocery_spend（月均杂货支出）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 全国月均（家庭） | S$456 | HES 2023 | **[HARD]** |
| 2017/18 对比 | S$394 → $456（+15.7%） | HES | [HARD] |
| HDB 家庭 | ~S$400 | 按住房支出比推导 | [DERIVED] |
| 公寓家庭 | ~S$600 | 按住房支出比推导 | [DERIVED] |
| 洋房家庭 | ~S$800 | 按住房支出比推导 | [DERIVED] |

**CPT 建议**: 条件变量: `monthly_income`, `housing_type`, `household_size`
- 分布: LogNormal，μ 和 σ 按收入五分位 × 住房类型查表

---

## 字段 2: monthly_dining_out_spend（月均外食支出）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 全国月均（家庭） | S$966 | HES 2023 | **[HARD]** |
| 食品总支出中外食占比 | 68%（966/1422） | HES 2023推导 | [DERIVED] |
| 小贩中心三餐日均 | S$16.89 | IPS Makan Index | **[HARD]** |
| 人均年外食支出 | S$3,200（2022） | Statista | [HARD] |

**CPT 建议**: 条件变量: `monthly_income`, `age`, `marital_status`, `housing_type`
- 按收入五分位: Q1 ~S$500, Q3 ~S$900, Q5 ~S$1,600

---

## 字段 3: monthly_transport_spend（月均交通支出）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 全国月均（家庭） | S$951 | HES 2023 | **[HARD]** |
| 私人道路交通 | S$678（2023） | HES 2023 | **[HARD]** |
| MRT日均客流 | 341万次（2024） | LTA | **[HARD]** |
| 巴士日均客流 | 384万次（2024） | LTA | **[HARD]** |
| 网约车日均行程 | 61.3万次（2023年7月） | LTA/PTC | **[HARD]** |

**CPT 建议**: **关键分支变量**: `has_car`
- has_car=True → LogNormal(μ=1500, σ=500)
- has_car=False → LogNormal(μ=350, σ=150)

---

## 字段 4: monthly_entertainment_spend（月均娱乐支出）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 全国月均（家庭） | S$335 | HES 2023 | **[HARD]** |
| 收入Q5月均 | ~S$843 | Mothership报道 | [HARD] |
| 收入Q1月均 | ~S$151 | Mothership报道 | [HARD] |

**CPT 建议**: 条件变量: `monthly_income`, `age`, `life_phase`
- 收入弹性高（Q5是Q1的5.6倍）

---

## 字段 5: preferred_shopping_channel（购物渠道偏好：online / offline / hybrid）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 线上购物渗透率 | 58.8%（2024） | Statista | **[HARD]** |
| 25-34岁线上购物占比 | 34.3%（最大群体） | Janio Asia | **[HARD]** |
| 线上消费家庭比例 | 82.0% | HES 2023 | **[HARD]** |
| 线上支出占总支出比 | 11.9% | HES 2023 | **[HARD]** |

**年龄-渠道映射 [DERIVED]**:

| 年龄段 | online | hybrid | offline |
|--------|--------|--------|---------|
| 18-24 | 30% | 55% | 15% |
| 25-34 | 35% | 50% | 15% |
| 35-44 | 25% | 50% | 25% |
| 45-54 | 15% | 45% | 40% |
| 55-64 | 8% | 35% | 57% |
| 65+ | 3% | 20% | 77% |

---

## 字段 6: primary_ecommerce_platform（Shopee / Lazada / Amazon / TikTok_Shop / Others）

| 平台 | 估算市场份额 | 年龄偏好 | 标签 |
|------|-------------|---------|------|
| Shopee | ~45% | 全年龄段，25-44最强 | [DERIVED] |
| Lazada | ~25% | 25-44岁 | [DERIVED] |
| Amazon | ~12% | 高收入 | [DERIVED] |
| TikTok Shop | ~8% | 18-34岁 | [DERIVED] |
| Others | ~10% | — | — |

来源: Momentum Works SEA, SimilarWeb

---

## 字段 7: brand_loyalty_level（high / medium / low）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 倾向保持品牌忠诚 | 65% | YouGov 2022 | **[HARD]** |
| 最高忠诚（即使对手打折也不换） | 10% | YouGov | **[HARD]** |
| 女性品牌忠诚度 | 67%（高于男性63%） | YouGov | [HARD] |

分布估算: high 10%, medium 55%, low 35% [DERIVED]

---

## 字段 8: price_sensitivity（high / medium / low）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 新加坡人全球最价格敏感 | 排名第1 | Wirecard | **[HARD]** |
| 收入Q1支出/收入比 | 99.4% | HES 2023 | **[HARD]** |
| 不看价格购买 | 仅23% | Wirecard | [HARD] |

分布估算: high 40%, medium 40%, low 20% [DERIVED]

---

## 字段 9: food_delivery_app（GrabFood / foodpanda / Deliveroo / none）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| GrabFood市场份额 | 56% | Statista | **[HARD]** |
| foodpanda市场份额 | 35% | Statista | **[HARD]** |
| Deliveroo市场份额 | 8% | Statista | **[HARD]** |
| 68%新加坡人使用外卖平台 | 68% | 行业调查 | [HARD] |

选择概率 [DERIVED]: GrabFood 48%, foodpanda 24%, Deliveroo 6%, none 22%

---

## 字段 10: ride_hailing_usage（daily / weekly / monthly / rarely / never）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 网约车日均行程 | 61.3万次 | PTC/LTA | **[HARD]** |
| Grab市场份额 | 74% | 行业数据 | [HARD] |
| 有车家庭比例 | 36.3% | HES 2023 | **[HARD]** |

**频率分布 [ESTIMATED]**:

| 频率 | 有车家庭 | 无车家庭 |
|------|---------|---------|
| daily | 1% | 5% |
| weekly | 5% | 25% |
| monthly | 15% | 30% |
| rarely | 30% | 25% |
| never | 49% | 15% |

---

## 字段 11: preferred_supermarket（NTUC_FairPrice / Sheng_Siong / Cold_Storage / Giant / Others）

| 超市 | 概率 | 人群偏好 | 标签 |
|------|------|---------|------|
| NTUC FairPrice | 40% | 全人群，尤其中低收入 | **[HARD]** |
| Sheng Siong | 22% | 价格敏感型，HDB居民 | [DERIVED] |
| Cold Storage | 15% | 中高收入，公寓居民 | [HARD] |
| Giant | 13% | 大家庭，价格敏感 | [HARD] |
| Others | 10% | 外籍、特定族群 | — |

来源: USDA/行业报告, 财报推导

---

## 字段 12: organic_food_preference（always / often / sometimes / rarely / never）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 总是/只买有机 | 5% | Rakuten Insight | **[HARD]** |
| 很少买有机 | 34% | Rakuten Insight | **[HARD]** |
| 愿意多付≤25%溢价 | 46% | Rakuten Insight | **[HARD]** |

分布: always 5%, often 12%, sometimes 25%, rarely 34%, never 24% [HARD]

---

## 字段 13: dining_frequency_weekly（每周外出用餐次数，0-21）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 80%每周≥1次小贩中心 | 80% | 行业引用 | [ESTIMATED] |
| 44%每天外食>1次 | 44% | 行业引用 | [ESTIMATED] |
| 外食占食品支出68% | 968/1422 | HES 2023推导 | **[DERIVED]** |
| 小贩三餐日均 | S$16.89 | IPS Makan Index | **[HARD]** |

估算均值 ~10次/周。单身/年轻人 14-18次，已婚有孩 7-10次

---

## 字段 14: hawker_vs_restaurant_ratio（0.0-1.0）

| 收入分位 | hawker_ratio | 标签 |
|---------|-------------|------|
| Q1（最低） | 0.85 | [ESTIMATED] |
| Q3 | 0.65 | [ESTIMATED] |
| Q5（最高） | 0.35 | [ESTIMATED] |

CPT: Beta分布，α/β 按收入调整

---

## 字段 15: social_media_platforms（多选集合）

| 平台 | 用户数 | 渗透率 | 标签 |
|------|--------|--------|------|
| WhatsApp | ~5.2M | 88.5% | **[HARD]** |
| YouTube | 5.15M | 88% | **[HARD]** |
| Facebook | 5.32M | 80.9% | **[HARD]** |
| Instagram | 3.28M | 49.9% | **[HARD]** |
| TikTok | 3.4M | 58% | **[HARD]** |
| Telegram | ~3M | ~51% | [HARD] |
| RedNote/小红书 | 75-85万 | ~13% | [ESTIMATED] |
| X (Twitter) | ~1.5M | ~25% | [HARD] |

**年龄×平台矩阵 [DERIVED]**:

| 年龄 | YouTube | Facebook | Instagram | TikTok | RedNote |
|------|---------|----------|-----------|--------|---------|
| 18-24 | 95% | 65% | 75% | 80% | 15% |
| 25-34 | 92% | 78% | 65% | 65% | 18% |
| 35-44 | 88% | 85% | 45% | 40% | 10% |
| 45-54 | 82% | 82% | 30% | 25% | 5% |
| 55-64 | 70% | 75% | 20% | 12% | 2% |
| 65+ | 50% | 60% | 10% | 5% | 1% |

来源: DataReportal 2025, NapoleonCat 2024

---

## 字段 16: daily_screen_time_hours

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 新加坡日均上网时间 | 6小时49分 | DataReportal | **[HARD]** |
| TikTok月均使用 | 34小时29分 | DataReportal | [HARD] |
| 青少年日均娱乐屏幕 | 8小时39分 | 研究报告 | [HARD] |

估算: 18-24岁 8.5h, 25-34岁 7.5h, 35-44岁 6.5h, 45-54岁 5.5h, 55-64岁 5.0h, 65+ 4.0h [ESTIMATED]

---

## 字段 17: sustainability_awareness（high / medium / low）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 认为可持续发展重要 | 70% | Singlife 2024 | **[HARD]** |
| 积极践行可持续 | 仅30% | Singlife 2024 | **[HARD]** |
| 不愿多付可持续产品 | 62% | Rakuten Insight | **[HARD]** |

分布: high 20%, medium 45%, low 35% [DERIVED]

---

## 字段 18: willing_to_pay_green_premium（yes_10pct / yes_5pct / no）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 愿付≤10%溢价 | 60%（在愿意者中） | YouGov | **[HARD]** |
| 完全不愿多付 | 62%（全体） | Rakuten Insight | **[HARD]** |

分布: yes_10pct 25%, yes_5pct 20%, no 55% [DERIVED]

---

## 字段 19: has_car（boolean）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| 家庭拥车率（2023） | **36.3%** | HES 2023 | **[HARD]** |
| 全国车辆保有量（2024） | 569,956辆 | LTA | **[HARD]** |

**按住房类型估算 [ESTIMATED]**:

| 住房类型 | 拥车率 |
|---------|--------|
| HDB 1-2房 | ~5% |
| HDB 3房 | ~15% |
| HDB 4房 | ~30% |
| HDB 5房/EC | ~45% |
| 公寓 | ~65% |
| 洋房 | ~90% |

---

## 字段 20: num_loyalty_memberships（数值 0-10）

| 数据点 | 值 | 来源 | 标签 |
|--------|------|------|------|
| Gen Z定期使用≥1个 | 36% | Statista 2024 | **[HARD]** |
| 最受欢迎: Yuu Rewards | 第1名 | YouGov | **[HARD]** |
| 第2: NTUC Link Rewards | 第2名 | YouGov | [HARD] |
| 最受欢迎奖励类型 | 返现(cashback) | YouGov | **[HARD]** |

分布: 0个 25%, 1-2个 35%, 3-4个 25%, 5+个 15%。均值 ~2.5

---

# 4. 数据缺口分析

| 字段 | 缺口描述 | 严重度 | 缓解策略 |
|------|----------|--------|---------|
| **按族群的消费差异** | 几乎没有公开的族群×消费交叉表 | **高** | 只能通过 income × housing 间接推导 |
| **小贩中心vs餐厅频率** | 没有官方调查数据 | 中 | 用外食总支出÷均价反推 |
| **品牌忠诚度按年龄/收入** | YouGov仅提供总体和性别分组 | 中 | 用收入→价格敏感度→品牌忠诚度链式推导 |
| **网约车使用频率** | 只有总行程数，无人口分布 | 中 | 用 has_car + income + age 建模 |
| **屏幕时间按新加坡年龄** | 无新加坡专项调查 | 中 | 用全球年龄趋势校准到6h49m均值 |
| **HES按户主年龄的细分支出** | HES 2023公开文档未包含 | 高 | 需购买完整报告或data.gov.sg API |
| **电商平台选择按人群** | 仅有总访问量 | 中 | 用 age + income + ethnicity 先验 |

---

# 5. CPT 架构总体建议

## 5.1 字段间依赖图

```
monthly_income ──┬──→ housing_type（已有）
                 ├──→ has_car ──→ car_type
                 ├──→ price_sensitivity ←──→ brand_loyalty_level
                 ├──→ monthly_grocery_spend
                 ├──→ monthly_dining_out_spend
                 ├──→ monthly_transport_spend（分支: has_car）
                 ├──→ monthly_entertainment_spend
                 ├──→ preferred_supermarket
                 └──→ sustainability_awareness ──→ willing_to_pay_green_premium

age ──┬──→ preferred_shopping_channel
      ├──→ primary_ecommerce_platform
      ├──→ social_media_platforms（多个Bernoulli）
      ├──→ daily_screen_time_hours
      ├──→ food_delivery_app
      ├──→ ride_hailing_usage
      ├──→ dining_frequency_weekly
      └──→ num_loyalty_memberships

ethnicity ──→ preferred_supermarket（Halal偏好）
           ──→ xiaohongshu_user（华人偏好）
```

## 5.2 生成顺序建议

1. **第一层**（直接从核心字段推导）: `has_car`, `price_sensitivity`, `brand_loyalty_level`, `sustainability_awareness`
2. **第二层**（依赖第一层）: `willing_to_pay_green_premium`, `monthly_transport_spend`
3. **第三层**（消费行为）: `monthly_grocery_spend`, `monthly_dining_out_spend`, `monthly_entertainment_spend`, `preferred_supermarket`, `preferred_shopping_channel`
4. **第四层**（数字行为）: `primary_ecommerce_platform`, `food_delivery_app`, `ride_hailing_usage`, `social_media_platforms`, `daily_screen_time_hours`, `num_loyalty_memberships`
5. **第五层**（细分）: `hawker_vs_restaurant_ratio`, `organic_food_preference`, `dining_frequency_weekly`

## 5.3 硬约束（全局校准目标）

| 约束 | 目标值 | 来源 |
|------|--------|------|
| 家庭拥车率 | 36.3% | HES 2023 |
| 月均总支出 | S$5,931 | HES 2023 |
| 食品支出占比 | 24.0% | HES 2023 |
| 交通支出占比 | 16.0% | HES 2023 |
| 线上消费家庭比例 | 82.0% | HES 2023 |
| 线上支出占比 | 11.9% | HES 2023 |
| 社交媒体渗透率 | 88.2% | DataReportal 2025 |
| 外卖平台使用率 | 68% | 行业调查 |

---

# 6. 最终字段清单（20个推荐字段）

| # | 字段名 | 类型 | 主要条件变量 | 数据质量 |
|---|--------|------|-------------|---------|
| 1 | monthly_grocery_spend | 数值(SGD) | income, housing, household_size | [HARD]+[DERIVED] |
| 2 | monthly_dining_out_spend | 数值(SGD) | income, age, marital_status | [HARD]+[DERIVED] |
| 3 | monthly_transport_spend | 数值(SGD) | has_car, income | [HARD] |
| 4 | monthly_entertainment_spend | 数值(SGD) | income, age | [HARD] |
| 5 | preferred_shopping_channel | 枚举(3) | age, education | [HARD]+[DERIVED] |
| 6 | primary_ecommerce_platform | 枚举(5) | age, income, ethnicity | [HARD]+[DERIVED] |
| 7 | brand_loyalty_level | 枚举(3) | income, gender, age | [HARD]+[DERIVED] |
| 8 | price_sensitivity | 枚举(3) | income, age | [HARD]+[DERIVED] |
| 9 | food_delivery_app | 枚举(4) | age, income | [HARD] |
| 10 | ride_hailing_usage | 枚举(5) | has_car, age, income | [ESTIMATED] |
| 11 | preferred_supermarket | 枚举(5) | housing, income, ethnicity | [HARD]+[DERIVED] |
| 12 | organic_food_preference | 枚举(5) | income, education, age | [HARD] |
| 13 | dining_frequency_weekly | 数值(0-21) | marital_status, age | [ESTIMATED] |
| 14 | hawker_vs_restaurant_ratio | 数值(0-1) | income, housing | [ESTIMATED] |
| 15 | social_media_platforms | 多选集合 | age, ethnicity, education | [HARD] |
| 16 | daily_screen_time_hours | 数值(hrs) | age, occupation | [ESTIMATED] |
| 17 | sustainability_awareness | 枚举(3) | age, education, income | [HARD] |
| 18 | willing_to_pay_green_premium | 枚举(3) | sustainability_awareness, income | [HARD] |
| 19 | has_car | Boolean | housing_type, income, age | **[HARD]** |
| 20 | num_loyalty_memberships | 数值(0-10) | age, shopping_channel | [HARD]+[DERIVED] |

**数据质量总结**:
- **[HARD]**: 12个字段有直接的新加坡官方/调查数据支撑
- **[DERIVED]**: 6个字段需要从多个来源交叉推导
- **[ESTIMATED]**: 4个字段需要基于相关数据估算
- **[GAP]**: 0个完全无数据的字段

---

## 参考文献

- SingStat HES 2023 Key Indicators
- LTA Vehicle Statistics 2025
- DataReportal Digital 2025 Singapore
- IMDA Digital Society Report 2023
- Statista - Food Delivery/Social Media/E-commerce in Singapore
- NapoleonCat Social Media Users Singapore 2024
- Momentum Works SEA Platform E-commerce Report
- YouGov - Singapore Loyalty Programs / Brand Consciousness
- Singlife Sustainability Index 2024
- PwC Voice of Consumer Survey 2024
- IPS Makan Index 2017
- Hashmeta/FY Ads - Xiaohongshu User Statistics
- PTC Fare Review 2024
- Janio Asia - Singapore Online Consumers
- Rakuten Insight - Singapore Consumer Surveys
