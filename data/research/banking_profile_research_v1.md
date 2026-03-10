# Banking Profile Research — Singapore Digital Twins
## Deep Research Report v1.0 (2026-03-10)
## Status: Research Only — DO NOT modify database

---

# 1. Data Sources Summary

| Source | Key Stats | Quality |
|--------|-----------|---------|
| World Bank Global Findex 2021/2025 | 银行账户持有率、信用卡持有率 | **P0** — 全球标准化调查 |
| MAS Monthly Statistical Bulletin (I.17A) | 信用卡/签帐卡数量、账单、滚存余额 | **P0** — 官方月度数据 |
| MAS Housing & Bridging Loans Data | 住房贷款总量、结构 | **P0** — 官方统计 |
| Credit Bureau Singapore (CBS) | 信用记录、拖欠率、违约率（按年龄） | **P1** — 行业权威 |
| SingStat HES 2023 | 按收入五分位的家庭收支、储蓄率 | **P1** — 官方调查 |
| SingStat Personal Disposable Income | 个人储蓄率（季度） | **P1** — 官方统计 |
| MoneySense National Financial Capability Survey 2021 | 金融素养评分（按教育/年龄） | **P1** — 官方委托NUS |
| MOF SRS Statistics | SRS账户持有人数、投资分布 | **P1** — 官方统计 |
| CPF Board Investment Statistics | CPFIS参与人数、投资表现 | **P1** — 官方统计 |
| BankQuality Consumer Survey 2024 | 银行渠道偏好、满意度 | **P2** — 商业调查 |
| Independent Reserve Crypto Index 2024/2025 | 加密货币持有率（按年龄/性别） | **P2** — 行业调查 |
| Singlife Financial Freedom Index 2024 | 应急储蓄、财务自由度 | **P2** — 行业调查 |
| UOB ACSS 2023 | 银行渠道偏好、储蓄行为 | **P2** — 银行调查 |

---

# 2. 银行账户基础数据

## 2.1 银行账户持有率

| 指标 | 值 | 溯源 |
|------|-----|------|
| 15岁以上成人银行账户持有率 | **97%** | **[HARD]** World Bank Global Findex 2025 |
| 2020年每千名成人银行账户数 | **2,405** | **[HARD]** World Bank / FRED (DDAI01SGA642NWDB) |
| 人均银行账户数（推算） | **~2.4个** | **[DERIVED]** 2,405/1,000 |

**关键发现：**
- 新加坡银行渗透率接近饱和（97%），仅3%成人无银行账户
- 人均2.4个账户说明多数人在多家银行开户
- 建模时 has_savings_account 对SC+PR可直接设为 ~98-99%（排除极少数新移入PR）

## 2.2 主要银行市场份额

| 银行 | 主银行渗透率 | 溯源 |
|------|------------|------|
| DBS | **35%** | **[HARD]** BankQuality Survey Jan 2024（12,000消费者，11个亚洲市场） |
| OCBC | ~20-22% | **[ESTIMATED]** 基于行业地位推算，无直接调查数据 |
| UOB | ~18-20% | **[ESTIMATED]** 基于行业地位推算 |
| Standard Chartered | ~5% | **[ESTIMATED]** |
| HSBC | ~3-4% | **[ESTIMATED]** |
| Citibank (legacy) | ~3% | **[ESTIMATED]** 2024年退出零售业务 |
| Maybank | ~3% | **[ESTIMATED]** |
| Trust Bank | ~5-8% | **[DERIVED]** 1M客户/~4.5M成人 ≈ 22%有账户，但非主银行 |
| GXS Bank | ~1-2% | **[DERIVED]** ~200K新加坡用户 |
| MariBank | <1% | **[ESTIMATED]** 公开数据极少 |
| 其他 | ~5% | **[ESTIMATED]** |

**硬数据约束：**
- DBS 35% 主银行份额：**[HARD]** BankQuality Survey
- Trust Bank 达100万客户（2024年初）：**[HARD]** 多家媒体报道
- GXS Bank 新加坡约20万用户：**[HARD]** KR-Asia 2024报道
- DBS/OCBC/UOB 2024年合计净利润 S$250亿：**[HARD]** Asian Banker

**CPT建议：** primary_bank 字段可按 income × age × housing 建CPT
- 高收入 + Private housing → DBS/SCB/HSBC 概率更高
- 年轻人（<30） → Trust Bank/GXS 概率更高
- HDB居民 → DBS/POSB/OCBC/UOB 为主

---

# 3. 数字银行数据

## 3.1 数字银行账户持有率

| 数字银行 | 客户数 | 占成人人口% | 溯源 |
|---------|--------|-----------|------|
| Trust Bank | **1,000,000+** | **~22%** | **[HARD]** FintechNews SG 2025; 第四大零售银行 |
| GXS Bank | **~200,000**（新加坡） | **~4.4%** | **[HARD]** KR-Asia 2024 |
| MariBank | 未公开 | 未知 | **[GAP]** |
| **合计（估）** | **~1,300,000** | **~29%** | **[DERIVED]** |

**FIS 2024调查：** 43%新加坡消费者表示愿意尝试数字银行：**[HARD]**

**数字银行总渗透率上限：** ~25-30%成人至少拥有一个数字银行账户（含重复计数）：**[ESTIMATED]**

**按年龄分解推算：**

| 年龄段 | 数字银行持有率（估） | 溯源 |
|--------|-------------------|------|
| 18-25 | ~35-40% | **[ESTIMATED]** Gen Z 32%有数字银行账户（Visa调查） |
| 26-35 | ~35-40% | **[ESTIMATED]** 千禧一代数字原生 |
| 36-50 | ~20-25% | **[ESTIMATED]** |
| 51-65 | ~10-15% | **[ESTIMATED]** |
| 65+ | ~3-5% | **[ESTIMATED]** |

---

# 4. 信用卡数据

## 4.1 信用卡持有率与数量

| 指标 | 值 | 溯源 |
|------|-----|------|
| 15岁以上成人信用卡持有率（2021） | **41.7%** | **[HARD]** World Bank Global Findex 2021 |
| 信用卡持有率（最新估计） | **~49-56%** | **[ESTIMATED]** 多来源取值42%-56%不等 |
| 信用卡消费者总数 | **~1,600,000** | **[HARD]** 行业报道引用 |
| 流通信用卡总数 | **~8,000,000张** | **[HARD]** 行业报道（2023年数据） |
| 持卡人平均卡数 | **~5张/人** | **[DERIVED]** 8M卡/1.6M持卡人 |
| 男性持卡率（15+） | **45%** | **[HARD]** Global Findex 2021 |
| 女性持卡率（15+） | **39%** | **[HARD]** Global Findex 2021 |

**按年龄推算：**

| 年龄段 | 信用卡持有率（估） | 平均卡数（估） | 溯源 |
|--------|-------------------|-------------|------|
| 18-20 | ~5% | 1 | **[ESTIMATED]** 最低收入要求S$30K年薪 |
| 21-25 | ~25% | 1-2 | **[ESTIMATED]** 刚开始工作 |
| 26-34 | ~55% | 3-4 | **[ESTIMATED]** |
| 35-49 | ~65% | 5-6 | **[ESTIMATED]** 峰值收入期 |
| 50-64 | ~50% | 4-5 | **[ESTIMATED]** |
| 65+ | ~25% | 2-3 | **[ESTIMATED]** |

**MAS规定约束：**
- 年收入 ≥ S$30,000 才能申请信用卡：**[HARD]** MAS规定
- 年收入 < S$120,000 时，无担保信贷额度上限 = 12倍月薪：**[HARD]** MAS Notice
- 年收入 ≥ S$120,000 时，无上限：**[HARD]** MAS Notice

## 4.2 信用卡消费与债务

| 指标 | 值 | 溯源 |
|------|-----|------|
| 2025年信用卡支付总额 | **S$1,070亿** | **[HARD]** GlobalData（7.6% YoY增长） |
| Q4 2024 滚存余额（revolving） | **S$83亿** | **[HARD]** MAS/CBS数据 |
| Q3 2024 滚存余额 | **S$79亿**（当时历史最高） | **[HARD]** |
| Q3 2024 冲销率（charge-off） | **5.3%** | **[HARD]** MAS数据 |
| 拖欠率（30天+逾期） | **~1-3%** | **[HARD]** CBS数据 |
| Q1 2024 坏账 | **S$8,940万**（同比+20%） | **[HARD]** |

**按年龄的拖欠率变化（Q3→Q4 2024）：**
- 30-34岁拖欠率上升最大：3.7% → 4.06%（+9.69%）：**[HARD]** CBS
- 50-54岁违约率上升最大：0.21% → 0.33%（+53.45%）：**[HARD]** CBS

**每月信用卡消费估算：**

| 收入段 | 估算月均信用卡消费 | 溯源 |
|--------|------------------|------|
| < S$3,000/月 | 无卡或 S$300-500 | **[ESTIMATED]** |
| S$3,000-5,000 | S$800-1,500 | **[ESTIMATED]** |
| S$5,000-10,000 | S$1,500-3,000 | **[ESTIMATED]** |
| S$10,000-20,000 | S$3,000-6,000 | **[ESTIMATED]** |
| > S$20,000 | S$6,000-15,000 | **[ESTIMATED]** |

---

# 5. 储蓄行为数据

## 5.1 全国储蓄率

| 指标 | 值 | 溯源 |
|------|-----|------|
| Q4 2024 个人储蓄率 | **37.6%** | **[HARD]** SingStat |
| Q1 2025 个人储蓄率 | **36.7%** | **[HARD]** SingStat |
| 2024全年平均储蓄率 | **~35.3%** | **[HARD]** SingStat |
| 历史平均（1980-2024） | **21.4%** | **[HARD]** SingStat/CEIC |
| 历史最高（2020 Q2 COVID） | **55.7%** | **[HARD]** |

## 5.2 按收入五分位储蓄率（HES 2023）

| 收入五分位 | 月均收入(S$) | 月均支出(S$) | 储蓄率 | 溯源 |
|-----------|------------|------------|--------|------|
| Q1 (最低20%) | 3,254 | 3,233 | **~0.6%** | **[DERIVED]** HES 2023 |
| Q2 (21-40%) | 7,961 | 4,401 | **~44.7%** | **[DERIVED]** |
| Q3 (41-60%) | 13,058 | 5,916 | **~54.7%** | **[DERIVED]** |
| Q4 (61-80%) | 18,751 | 6,981 | **~62.8%** | **[DERIVED]** |
| Q5 (最高20%) | 34,341 | 9,125 | **~73.4%** | **[DERIVED]** |

**关键发现：**
- 最低收入组几乎零储蓄（0.6%），这是家庭层面（含转移支付）
- 最高收入组储蓄率高达73.4% — 收入≠支出的差距极大
- 此数据是**家庭**收入和支出，非个人

## 5.3 应急储蓄

| 指标 | 值 | 溯源 |
|------|-----|------|
| 有≥3个月应急储蓄的消费者比例 | **78%** | **[HARD]** Singlife 2024调查（3,000人） |
| 认为应急储蓄"足够"的比例 | **~33%** | **[HARD]** Singlife 2024调查 |
| MAS建议应急储蓄 | 3-6个月支出 | **[HARD]** MoneySense/MAS |

**CPT建议：** emergency_fund_months 字段
- 主要由 income × age 驱动
- 78%有≥3个月作为全国约束
- 低收入组（Q1）应急储蓄极少：0-1个月
- 高收入组（Q4-Q5）：6-12个月

---

# 6. 住房贷款数据

## 6.1 住房贷款总体统计

| 指标 | 值 | 溯源 |
|------|-----|------|
| 新加坡住房拥有率（2024） | **90.8%** | **[HARD]** SingStat |
| HDB居民比例 | **~77.4%** | **[HARD]** HDB 2024 |
| 私宅居民比例 | **~12.6%** | **[DERIVED]** 90.8%-77.4%-租房 |
| H1 2025 住房贷款总额 | **S$2,306亿** | **[HARD]** MAS / GlobalPropertyGuide |
| 自住房贷占比 | **~80%** | **[HARD]** MAS |
| 投资房贷占比 | **~20%** | **[HARD]** MAS |
| 住房贷款占家庭债务比例 | **~72.7-75%** | **[HARD]** MAS（金融机构61.1% + HDB贷款11.6%） |
| 住房贷款占GDP比 | **30.9%**（2024） | **[HARD]** GlobalPropertyGuide |
| 住房不良贷款率（Q3 2024） | **0.3%** | **[HARD]** MAS Financial Stability Review |
| 平均LTV（贷款/价值比） | **<50%** | **[HARD]** MAS |
| HDB优惠贷款利率 | **2.60%** | **[HARD]** HDB |

**有房贷的家庭比例推算：**

| 条件 | 有房贷率（估） | 溯源 |
|------|-------------|------|
| HDB住户 | ~55-65% | **[ESTIMATED]** 考虑已还清者 |
| 私宅住户 | ~60-70% | **[ESTIMATED]** |
| 年龄 <35 + 有房 | ~80-90% | **[ESTIMATED]** 刚购房 |
| 年龄 35-50 + 有房 | ~60-70% | **[ESTIMATED]** |
| 年龄 50-65 + 有房 | ~30-40% | **[ESTIMATED]** 部分已还清 |
| 年龄 65+ + 有房 | ~10-20% | **[ESTIMATED]** 多数已还清 |

**CPT建议：** has_mortgage 由 age × housing_type × income 驱动
- 关键约束：90.8%住房拥有率 × ~55-60%有在偿贷款 ≈ ~50-55%家庭有房贷

---

# 7. 投资行为数据

## 7.1 投资账户持有率

| 指标 | 值 | 溯源 |
|------|-----|------|
| CPFIS-OA 投资账户持有人 | **>1,000,000** | **[HARD]** CPF Board Q3 2024 |
| CPFIS-OA 总持有额 | **>S$26亿** | **[HARD]** CPF Board |
| SRS 账户持有人（2024年底） | **466,849** | **[HARD]** MOF SRS Statistics |
| SRS 账户持有人（2023年底） | **427,188** | **[HARD]** MOF |
| SRS持有人占工作年龄人口% | **~15-18%** | **[DERIVED]** 466K/~2.7M 工作人口 |
| SRS持有人年龄分布 | **>50%在36-55岁** | **[HARD]** MOF |

## 7.2 零售投资类型分布

| 投资类型 | 持有率（估） | 溯源 |
|---------|-----------|------|
| 股票/REITs/ETF（CDP账户） | ~25-30%成人 | **[ESTIMATED]** 无直接数据 |
| Robo-advisor（StashAway/Syfe/Endowus等） | ~5-8%成人 | **[ESTIMATED]** AUM超S$200亿但用户数未公开 |
| 加密货币 | **26-29%**（2024-2025） | **[HARD]** Independent Reserve Survey 2025 |
| Unit trusts/基金 | ~15-20% | **[ESTIMATED]** |
| 定期存款 | ~30-40% | **[ESTIMATED]** |
| 债券/SSB | ~5-10% | **[ESTIMATED]** |

## 7.3 加密货币持有详情

| 指标 | 值 | 溯源 |
|------|-----|------|
| 加密货币认知率 | **94%** | **[HARD]** IR Survey 2024 |
| 加密货币持有率（2024） | **~26-40%** | **[HARD]** 多来源（IR: 29%, Mitrade: 26%, CoinTelegraph: 40%） |
| 千禧+GenX(25-54)占持有者 | **71%** | **[HARD]** IR Survey |
| 男性持有率 | **35%** | **[HARD]** IR Survey |
| 女性持有率 | **24%** | **[HARD]** IR Survey |
| 2024年卖出部分/全部 | **49%** | **[HARD]** IR Survey |

## 7.4 SRS投资分布（2024年底）

| 投资类型 | 占比 | 溯源 |
|---------|------|------|
| 股票/REITs/ETF | **24%** | **[HARD]** MOF |
| 保险产品 | **22%** | **[HARD]** MOF |
| 现金（未投资） | **19%** | **[HARD]** MOF |
| 其他（基金/债券等） | **35%** | **[DERIVED]** |

---

# 8. 数字银行与支付行为

## 8.1 数字支付统计

| 指标 | 值 | 溯源 |
|------|-----|------|
| 数字支付采纳率（2025） | **92%** | **[HARD]** PwC |
| PayNow使用率 | **80%**居民和商户 | **[HARD]** NORBr/2C2P |
| 数字钱包用户率（2025预测） | **94.7%** | **[HARD]** PwC预测 |
| Gen Z首选数字支付 | PayNow **68%** | **[HARD]** |
| 移动钱包用户数（2025预测） | **320万** | **[HARD]** |

## 8.2 银行渠道偏好

| 渠道 | 偏好比例 | 溯源 |
|------|---------|------|
| 移动银行 | **54%** | **[HARD]** UOB ACSS 2023 |
| 网上银行 | **35%** | **[HARD]** UOB ACSS 2023 |
| ATM | ~5% | **[ESTIMATED]** |
| 分行 | ~5% | **[ESTIMATED]** |
| 电话银行 | ~1% | **[ESTIMATED]** |

**信任度：** 7成消费者将移动银行列为最受信任渠道之一：**[HARD]** UOB ACSS

**按年龄分解推算：**

| 年龄段 | 移动银行 | 网上银行 | 分行 | ATM | 溯源 |
|--------|---------|---------|------|-----|------|
| 18-30 | 70% | 20% | 3% | 5% | **[ESTIMATED]** |
| 31-45 | 60% | 25% | 5% | 8% | **[ESTIMATED]** |
| 46-60 | 45% | 30% | 12% | 10% | **[ESTIMATED]** |
| 61+ | 25% | 25% | 30% | 15% | **[ESTIMATED]** |

## 8.3 BNPL（先买后付）

| 指标 | 值 | 溯源 |
|------|-----|------|
| BNPL市场规模（2024） | **US$11.9亿** | **[HARD]** ResearchAndMarkets |
| Gen Z BNPL使用率 | **77%** | **[HARD]** 行业调查 |
| 千禧一代 BNPL使用率 | **47%** | **[HARD]** |
| Gen X BNPL使用率 | **28%** | **[HARD]** |
| 婴儿潮一代 BNPL使用率 | **13%** | **[HARD]** |
| 主要供应商 | Atome, Grab PayLater, SPayLater, ShopBack | **[HARD]** |

---

# 9. 金融素养数据

## 9.1 MoneySense 2021全国金融能力调查

| 指标 | 值 | 溯源 |
|------|-----|------|
| 调查样本 | 2,451人 | **[HARD]** NUS/MoneySense |
| Big Three金融素养均分（0-3） | **2.27** | **[HARD]** Cambridge U Press论文 |
| 全答对"Big Three"比例 | **39.3%** | **[HARD]** |
| 自评"金融素养好"比例 | **44.8%** | **[HARD]** SmartWealth调查2022 |
| 自评"金融素养差"比例 | **55.2%** | **[HARD]** |
| 大学学历答对Big Three | **53%** | **[HARD]** |
| 高中及以下答对Big Three | **21%** | **[HARD]** |
| 部分大学教育答对Big Three | **33%** | **[HARD]** |
| 30-59岁未开始财务规划 | **30%** | **[HARD]** MoneySense |

**关键发现：**
- 金融素养与教育水平高度相关（大学53% vs 高中21%）
- 金融知识在各年龄段"基本持平"（mostly flat across age groups）
- 理解通胀的比例高，但理解复利和风险分散的比例低
- 女性和低收入群体金融素养显著更低

**CPT建议：** financial_literacy_level 字段（high/medium/low）
- 主要由 education_level 驱动，income 次之
- high: ~20%（大学+高收入）
- medium: ~45%（大学or中等收入）
- low: ~35%（低教育+低收入）

---

# 10. 家庭债务结构

## 10.1 总体债务统计

| 指标 | 值 | 溯源 |
|------|-----|------|
| 家庭债务占GDP比（Q3 2024） | **52.0%** | **[HARD]** CEIC |
| 家庭债务占GDP比（Q3 2025） | **51.1%** | **[HARD]** CEIC |
| 住房贷款占家庭债务 | **~75%** | **[HARD]** MAS |
| 信用卡+个人贷款占家庭债务 | **~25%** | **[DERIVED]** |
| 住房不良贷款率 | **0.3%** | **[HARD]** MAS Q3 2024 |

## 10.2 无担保债务

| 指标 | 值 | 溯源 |
|------|-----|------|
| 信用卡滚存余额（Q4 2024） | **S$83亿** | **[HARD]** MAS/CBS |
| MAS无担保信贷上限规则 | 12倍月收入（年收入<S$120K时） | **[HARD]** MAS |
| 信用卡拖欠率 | **~1-3%** | **[HARD]** CBS |
| 信用卡冲销率（Q3 2024） | **5.3%** | **[HARD]** MAS |

---

# 11. 退休规划数据

## 11.1 SRS（补充退休计划）

| 指标 | 值 | 溯源 |
|------|-----|------|
| SRS账户持有人（2024年底） | **466,849** | **[HARD]** MOF |
| SRS账户持有人（2023年底） | **427,188** | **[HARD]** MOF |
| SRS账户持有人（2022年底） | **387,377** | **[HARD]** MOF |
| SRS年贡献上限（SC/PR） | **S$15,300** | **[HARD]** IRAS |
| SRS年贡献上限（外国人） | **S$35,700** | **[HARD]** IRAS |
| >50%持有人年龄 | **36-55岁** | **[HARD]** MOF |
| 持有人占工作人口比 | **~15-18%** | **[DERIVED]** |

**CPT建议：** has_srs_account 字段
- 主要由 income × age 驱动
- SRS是税务优化工具，高收入人群（年收入>S$80K+）使用率高
- 36-55岁峰值（>50%持有人在此段）
- 低收入群体几乎不使用（税务优惠不大）

---

# 12. 推荐字段清单 — 20个 Banking Domain 字段

## 12.1 字段列表及数据质量评估

| # | 字段名 | 类型 | 数据质量 | CPT条件变量 |
|---|--------|------|---------|------------|
| 1 | **has_bank_account** | boolean | [HARD] 97% | age（仅新PR可能无） |
| 2 | **primary_bank** | categorical | [HARD]+[ESTIMATED] | income × age × housing |
| 3 | **num_bank_accounts** | integer (1-5) | [HARD] 均值2.4 | income × age |
| 4 | **has_digital_bank** | boolean | [DERIVED] ~25-30% | age × income |
| 5 | **has_credit_card** | boolean | [HARD] ~42-50% | income × age × gender |
| 6 | **num_credit_cards** | integer (0-10) | [DERIVED] 持卡人均5张 | income × age |
| 7 | **credit_card_spending_monthly** | continuous (S$) | [ESTIMATED] | income × has_credit_card |
| 8 | **has_personal_loan** | boolean | [ESTIMATED] ~8-12% | income × age |
| 9 | **has_mortgage** | boolean | [ESTIMATED] ~50-55%家庭 | age × housing_type × marital |
| 10 | **mortgage_outstanding** | continuous (S$) | [GAP] | age × housing_type × income |
| 11 | **monthly_savings_rate** | continuous (%) | [HARD] by quintile | income (quintile) |
| 12 | **emergency_fund_months** | integer (0-12) | [HARD] 78%≥3月 | income × age |
| 13 | **has_investment_account** | boolean | [ESTIMATED] ~30-35% | income × age × education |
| 14 | **investment_types** | multi-label | [ESTIMATED] | income × age × education |
| 15 | **has_crypto** | boolean | [HARD] ~26-29% | age × gender × income |
| 16 | **has_srs_account** | boolean | [HARD] ~15-18%工作人口 | income × age |
| 17 | **financial_literacy_level** | categorical (H/M/L) | [HARD] by education | education × income |
| 18 | **preferred_banking_channel** | categorical | [HARD] mobile 54% | age × education |
| 19 | **uses_bnpl** | boolean | [HARD] by generation | age |
| 20 | **outstanding_unsecured_debt** | continuous (S$) | [ESTIMATED] | income × age × has_credit_card |

---

## 12.2 每个字段的CPT设计建议

### Field 1: has_bank_account
```
P(true) = 0.97（所有年龄）
P(true | age≥21, SC) = 0.99
P(true | PR, 入境<1年) = 0.90
```
**溯源：** [HARD] Global Findex 2025: 97%

### Field 2: primary_bank
```
P(bank | income, age, housing)
边际约束：DBS 35%, OCBC ~21%, UOB ~19%, SCB ~5%, Others ~20%
```
**溯源：** DBS 35% [HARD], 其余 [ESTIMATED]

### Field 3: num_bank_accounts
```
均值 = 2.4
P(1 | age<25) = 0.50, P(2) = 0.35, P(3+) = 0.15
P(1 | age 25-50, income>median) = 0.20, P(2) = 0.35, P(3) = 0.25, P(4+) = 0.20
P(1 | age 65+) = 0.45, P(2) = 0.35, P(3+) = 0.20
```
**溯源：** [HARD] 均值2.4 (World Bank/FRED), 分布 [ESTIMATED]

### Field 4: has_digital_bank
```
总体 ~25-30%
P(true | age 18-35) ≈ 0.35-0.40
P(true | age 36-50) ≈ 0.20-0.25
P(true | age 51-65) ≈ 0.10-0.15
P(true | age 65+) ≈ 0.03-0.05
```
**溯源：** Trust Bank 1M [HARD], Gen Z 32%数字银行 [HARD], 总体 [DERIVED]

### Field 5: has_credit_card
```
总体 ~45-50%（15岁以上）
约束：income ≥ S$30K/yr 才能申请 [HARD MAS]
P(true | income<$2,500/mo) ≈ 0.10  // 未达门槛
P(true | income $2,500-4,000) ≈ 0.35
P(true | income $4,000-8,000) ≈ 0.60
P(true | income $8,000-15,000) ≈ 0.75
P(true | income >$15,000) ≈ 0.85
```
**溯源：** [HARD] Findex 41.7%(2021), MAS门槛S$30K [HARD], 按收入 [ESTIMATED]

### Field 6: num_credit_cards
```
P(cards | has_credit_card, income)
持卡人均值 = 5张
低收入持卡人: 1-2张
中等收入: 3-4张
高收入: 5-8张
```
**溯源：** [HARD] 8M卡/1.6M持卡人=5, 按收入 [ESTIMATED]

### Field 7: credit_card_spending_monthly
```
连续变量，log-normal分布
中位数 ≈ income × 0.25（估算）
约束：2025年总信用卡支付 S$1,070亿 / 1.6M持卡人 / 12月 ≈ S$5,570/月
```
**溯源：** 总额 [HARD], 人均 [DERIVED]

### Field 8: has_personal_loan
```
总体 ~8-12%
P(true | age 25-34, income<median) ≈ 0.15
P(true | age 35-50) ≈ 0.10
P(true | age 50+) ≈ 0.05
```
**溯源：** [ESTIMATED] — 无直接数据

### Field 9: has_mortgage
```
约束：90.8%住房拥有率 × ~55-60%有在偿贷款
P(true | age<30, has_home) ≈ 0.85
P(true | age 30-45, has_home) ≈ 0.70
P(true | age 45-60, has_home) ≈ 0.40
P(true | age 60+, has_home) ≈ 0.15
```
**溯源：** 拥有率 [HARD], 有贷款比例 [ESTIMATED]

### Field 10: mortgage_outstanding
```
连续变量
参考：H1 2025总额 S$2,306亿 / ~1.3M有房贷家庭 ≈ S$177K人均
HDB: S$100K-350K
Private: S$300K-1,500K
按age递减（越老越少）
```
**溯源：** 总额 [HARD], 人均 [DERIVED], 分布 [ESTIMATED]

### Field 11: monthly_savings_rate
```
连续变量(%)
P(rate | income_quintile) — 直接可用HES 2023数据
Q1: ~0-5%
Q2: ~40-50%
Q3: ~50-60%
Q4: ~60-65%
Q5: ~70-75%
```
**溯源：** [DERIVED] HES 2023 收入-支出

### Field 12: emergency_fund_months
```
约束：78%有≥3个月 [HARD]
P(0-1月 | income Q1) ≈ 0.40
P(3-6月 | income Q2-Q3) ≈ 0.55
P(6-12月 | income Q4-Q5) ≈ 0.45
```
**溯源：** [HARD] 78%≥3月(Singlife 2024), 按收入 [ESTIMATED]

### Field 13: has_investment_account
```
总体 ~30-35%
P(true | income>$8K, age 30-55) ≈ 0.50-0.60
P(true | income<$4K) ≈ 0.10-0.15
P(true | age<25) ≈ 0.10
P(true | age 65+) ≈ 0.15
```
**溯源：** [ESTIMATED] — CPFIS 1M+投资者, CDP账户数未知

### Field 14: investment_types
```
多标签字段（给定has_investment_account=true）：
- stocks_reits: 60%
- etf: 40%
- unit_trusts: 35%
- robo_advisor: 20%
- bonds_ssb: 15%
- fixed_deposit: 50% (广义投资)
```
**溯源：** [ESTIMATED] — 无直接分布数据

### Field 15: has_crypto
```
总体 ~26-29% (2025)
P(true | age 18-24) ≈ 0.30
P(true | age 25-34) ≈ 0.35
P(true | age 35-44) ≈ 0.30
P(true | age 45-54) ≈ 0.25
P(true | age 55+) ≈ 0.10
P(true | male) ≈ 0.35, P(true | female) ≈ 0.24
```
**溯源：** [HARD] IR Survey 2025: 29%, 年龄/性别分布 [HARD]

### Field 16: has_srs_account
```
总体 ~15-18%工作人口
P(true | income>$10K, age 36-55) ≈ 0.40
P(true | income $5K-10K, age 36-55) ≈ 0.20
P(true | income<$5K) ≈ 0.03
P(true | age<30) ≈ 0.05
P(true | age 56+) ≈ 0.10（已开始提取）
```
**溯源：** [HARD] 466K持有人, >50%在36-55岁, 按收入 [ESTIMATED]

### Field 17: financial_literacy_level
```
P(level | education)
P(high | university) ≈ 0.40
P(medium | university) ≈ 0.45
P(low | university) ≈ 0.15
P(high | diploma/poly) ≈ 0.20
P(medium | diploma/poly) ≈ 0.45
P(low | diploma/poly) ≈ 0.35
P(high | secondary-) ≈ 0.08
P(medium | secondary-) ≈ 0.35
P(low | secondary-) ≈ 0.57
```
**溯源：** [HARD] Big Three 答对率 by education, mapping到H/M/L [DERIVED]

### Field 18: preferred_banking_channel
```
P(channel | age)
总体约束：mobile 54%, online 35%, branch ~5%, ATM ~5%
年轻人(18-35): mobile 70%, online 20%
中年(36-55): mobile 55%, online 30%
老年(56+): mobile 25%, online 25%, branch 30%, ATM 15%
```
**溯源：** [HARD] UOB ACSS mobile 54% + online 35%, 按年龄 [ESTIMATED]

### Field 19: uses_bnpl
```
P(true | age_generation)
Gen Z (18-28): 0.77
Millennials (29-43): 0.47
Gen X (44-58): 0.28
Boomers (59+): 0.13
```
**溯源：** [HARD] 行业调查按世代分布

### Field 20: outstanding_unsecured_debt
```
连续变量(S$)
约束：Q4 2024 信用卡滚存 S$83亿 / ~1.6M持卡人 ≈ S$5,188人均
但含非revolving部分，实际revolving用户更少
P(>0 | has_credit_card) ≈ 0.30-0.40（滚存比例）
```
**溯源：** [HARD] S$83亿总额, [DERIVED] 人均

---

# 13. 实施优先级

## Phase 1 — 核心银行字段（6个）
1. **has_bank_account** — trivial（~97-99% TRUE）
2. **has_credit_card** — CPT on income × age × gender
3. **primary_bank** — CPT on income × age × housing
4. **has_mortgage** — CPT on age × housing_type × marital
5. **monthly_savings_rate** — CPT on income_quintile
6. **financial_literacy_level** — CPT on education × income

## Phase 2 — 数字与信用（6个）
7. **has_digital_bank** — CPT on age × income
8. **num_credit_cards** — CPT on income × has_credit_card
9. **preferred_banking_channel** — CPT on age × education
10. **has_crypto** — CPT on age × gender
11. **uses_bnpl** — CPT on age
12. **emergency_fund_months** — CPT on income × age

## Phase 3 — 投资与退休（4个）
13. **has_investment_account** — CPT on income × age × education
14. **has_srs_account** — CPT on income × age
15. **num_bank_accounts** — CPT on income × age
16. **credit_card_spending_monthly** — continuous, on income × has_credit_card

## Phase 4 — 补充字段（4个）
17. **has_personal_loan** — CPT on income × age
18. **mortgage_outstanding** — continuous, on age × housing × income
19. **investment_types** — multi-label, on income × age × education
20. **outstanding_unsecured_debt** — continuous, on income × has_credit_card

---

# 14. Data Gaps Summary

## 14.1 数据质量分级汇总

| 质量等级 | 字段数 | 字段列表 |
|---------|--------|---------|
| **[HARD]** 有直接硬数据 | 8 | has_bank_account, monthly_savings_rate, has_crypto, financial_literacy_level, uses_bnpl, preferred_banking_channel, has_srs_account（总量）, has_credit_card（总量） |
| **[DERIVED]** 可从硬数据推导 | 5 | num_bank_accounts, num_credit_cards, credit_card_spending_monthly, outstanding_unsecured_debt, emergency_fund_months |
| **[ESTIMATED]** 有间接数据但需验证 | 5 | primary_bank, has_digital_bank, has_mortgage, has_investment_account, has_personal_loan |
| **[GAP]** 无数据 | 2 | mortgage_outstanding（具体分布）, investment_types（详细持有率） |

## 14.2 关键数据缺口与获取建议

| 缺口 | 需要的数据 | 可能数据源 |
|------|-----------|-----------|
| primary_bank 按收入/年龄 | 各银行零售客户市场份额 | DBS/OCBC/UOB年报、BankQuality付费报告 |
| has_credit_card 按年龄 | 信用卡持有率按年龄段 | MAS I.17A详细表（需下载CSV） |
| has_mortgage 具体比例 | 有在偿房贷的家庭比例按年龄 | HDB年报、CPF Board房屋统计 |
| mortgage_outstanding 分布 | 平均房贷余额按年龄/房屋类型 | MAS Housing Loan详细表 |
| has_investment_account | CDP账户持有人总数 | SGX年报 |
| has_personal_loan | 个人贷款借款人数 | MAS银行业统计 |
| investment_types 分布 | 各类投资品持有率 | SGX/MAS投资者调查 |

---

# 15. References

1. World Bank, "Global Findex Database 2021/2025". https://globalfindex.worldbank.org/ — **银行账户持有率97%**
2. FRED/World Bank, "Number of Bank Accounts for Singapore". https://fred.stlouisfed.org/series/DDAI01SGA642NWDB — **2,405 accounts per 1,000 adults (2020)**
3. MAS, "Credit and Charge Card Statistics (I.17A)". https://www.mas.gov.sg/statistics/monthly-statistical-bulletin/i-17a-credit-and-charge-card-statistics
4. data.gov.sg, "Credit and Charge Card Statistics, Annual". https://data.gov.sg/datasets/d_7a747bbf23166674020989ce7af0e72e/view
5. MAS, "Data on Housing and Bridging Loans". https://www.mas.gov.sg/statistics/monthly-statistical-bulletin/data-on-housing-and-bridging-loans
6. MAS, "Unsecured Credit Borrowing Limit". https://www.mas.gov.sg/regulation/explainers/ongoing-credit-checks-and-requirements/borrowing-limit-on-unsecured-credit — **12x月薪上限**
7. SingStat, "Household Expenditure Survey 2023". https://www.singstat.gov.sg/publications/households/household-expenditure-survey — **按收入五分位的收支数据**
8. SingStat, "Personal Disposable Income and Saving". https://www.singstat.gov.sg/pdips — **个人储蓄率35.3% (2024)**
9. MOF, "Compiled SRS Statistics". https://isomer-user-content.by.gov.sg/153/28551aa7-fd3e-41af-b95e-1db5641b5ab2/compiled-srs-statistics.pdf — **466,849 SRS账户(2024)**
10. CPF Board, "Investment Statistics". https://www.cpf.gov.sg/member/infohub/reports-and-statistics/cpf-statistics/investment-statistics — **CPFIS >1M成员**
11. MoneySense/NUS, "National Financial Capability Survey 2021". https://www.mom.gov.sg/newsroom/announcements/2024/1006-moneysense-national-financial-capability-survey — **Big Three均分2.27/3**
12. SmartWealth, "Financial Literacy Statistics Singapore". https://smartwealth.sg/financial-literacy-singapore-statistics/ — **44.8%自评素养好**
13. BankQuality, "Singapore Report 2024". https://tabinsights.com/reports/bankquality-singapore-report-2024 — **DBS 35%主银行渗透率**
14. FintechNews SG, "Trust Bank 1 Million Customers". https://fintechnews.sg/113040/digital-banking-news-singapore/inside-dwaipayan-sadhu-trust-bank-singapore-1-million-customers/
15. KR-Asia, "Singapore Digital Banks". https://kr-asia.com/profits-and-customers-prove-elusive-for-singapores-digital-banks — **GXS ~200K新加坡用户**
16. Independent Reserve, "Singapore Cryptocurrency Index 2025". https://www.prnewswire.com/apac/news-releases/selective-bull-market-driving-smarter-more-thoughtful-crypto-plays-among-singaporeans---2025-independent-reserve-cryptocurrency-index-shows-302461821.html — **加密持有率29%, 男35%女24%**
17. UOB, "ASEAN Consumer Sentiment Study 2023 (Singapore)". https://www.uobgroup.com/asean-insights/articles/acss-2023-singapore.page — **移动银行54%, 网上银行35%**
18. Singlife, "Financial Freedom Index 2024". https://singlife.com/en/about-us/newsroom/2024/financial-freedom-index-2024 — **78%有≥3月应急储蓄**
19. PwC, "Payments State of Play 2026". https://www.pwc.com/sg/en/publications/payments-state-of-play.html — **数字支付92%**
20. Credit Bureau Singapore / MAS, "Credit Card Rollover Balances Q4 2024". 引用自 https://www.openprivilege.com/personal-finance/banking/credit/singaporeans-sink-deeper-into-credit-card-debt — **S$83亿滚存**
21. GlobalPropertyGuide, "Singapore Residential Property Market 2025". https://www.globalpropertyguide.com/asia/singapore/price-history — **住房贷款S$2,306亿, 占GDP 30.9%**
22. Statista, "Home Ownership Rate Singapore 2024". https://www.statista.com/statistics/664518/home-ownership-rate-singapore/ — **90.8%**
23. GlobalData, "Singapore Credit and Charge Card Payments 2026". https://www.globaldata.com/media/banking/singapore-credit-and-charge-card-payments-to-grow-by-9-2-in-2026-forecasts-globaldata/ — **S$1,070亿(2025)**
24. ResearchAndMarkets, "Singapore BNPL Report 2026". https://www.globenewswire.com/news-release/2026/01/16/3220369/28124/en/Singapore-Buy-Now-Pay-Later-Business-Report-2026.html — **BNPL US$11.9亿(2024)**
25. Cambridge University Press, "The Importance of Financial Literacy: Evidence from Singapore". https://www.cambridge.org/core/journals/journal-of-financial-literacy-and-wellbeing/article/importance-of-financial-literacy-evidence-from-singapore/C15B89BE5FF82B23AFB3C951F9EA06A3
26. MAS, "Financial Stability Review November 2024". https://www.mas.gov.sg/-/media/mas-media-library/publications/financial-stability-review/2024/financial-stability-review-2024.pdf — **住房不良贷款率0.3%, 家庭债务52% GDP**
