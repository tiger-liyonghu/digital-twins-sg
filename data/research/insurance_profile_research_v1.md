# Insurance Profile Research — Singapore Digital Twins
## Deep Research Report v1.2 (2026-03-10) — Updated with PGS Tables 66-69 + Section 16 survey + MOH IP tier + CPF savings
## Status: Research Only — DO NOT modify database (v4.1 frozen)

---

# 1. Data Sources Summary

| Source | Key Stats | Quality |
|--------|-----------|---------|
| LIA Protection Gap Study 2022 (EY) | Coverage rates, policies/person, coverage amounts by age×gender×income | **P0** — Gold standard, actual policy data from insurers |
| MAS Insurance Statistics 2021-2024 | Industry totals, premium volumes | P1 — Macro level |
| MOH IP Comparison Tables (Jan 2025) | 7 IP insurers, plan tiers, premiums by age | P1 — Official |
| CPF MediShield Life (2024 Review) | Universal coverage, premium tables | P1 — Official |
| SAS Medical Insurance Discussion Paper (Nov 2024) | IP lives covered, claims per life | P1 — Actuarial |
| SingStat HES 2023 | Household insurance spending by income | P2 — Indirect |

---

# 2. Population-Level Insurance Statistics (LIA PGS 2022)

## 2.1 Overall Ownership (All Singapore Citizens & PRs)

| Metric | Value | Source |
|--------|-------|--------|
| Total population (SC+PR) | ~4.87M | PGS Table 58 |
| Unique policyholders (incl DPS) | 3,012,491 | PGS Table 57 |
| Unique policyholders (excl DPS) | 2,457,882 | PGS p.59 |
| People with 0 individual policies | **38%** of total pop | PGS p.60 |
| **People with ≥1 individual policy** | **62%** of SC+PR | PGS Section 10.1 |
| Total policies in-force | 7,894,214 | PGS Table 57 |
| Total policies excl DPS | 5,946,644 | PGS p.59 |
| DPS policies (auto-enrollment age 20-60) | 1,947,570 | Derived |
| MediShield Life coverage | **100% of SC+PR** | CPF — auto-enrolled |
| Integrated Shield Plan coverage | **71% of Singaporeans** | MOH Nov 2025 |
| IP policyholders with riders | 67% of IP holders (~2M) | MOH Nov 2025 |
| IP lives covered (2023) | ~3,988,000 | SAS Paper |

## 2.2 Policies per Person (Those WITH Insurance, Excl Riders)

**Table 59 from LIA PGS 2022:**

| Age Band | Male | Female |
|----------|------|--------|
| 0-4 | 1.51 | 1.51 |
| 5-9 | 1.61 | 1.60 |
| 10-14 | 1.71 | 1.71 |
| 15-19 | 1.88 | 1.85 |
| 20-24 | 2.04 | 2.11 |
| 25-29 | 2.47 | 2.64 |
| 30-34 | 2.82 | 3.09 |
| 35-39 | 3.08 | 3.33 |
| 40-44 | 3.33 | 3.69 |
| 45-49 | 3.55 | 3.97 |
| 50-54 | 3.50 | 4.00 |
| 55-59 | 3.22 | 3.82 |
| 60-64 | 2.87 | 3.60 |
| 65-69 | 2.52 | 3.33 |
| 70+ | 1.95 | 2.43 |

**Key insight**: Females have more policies than males from age 25+. Peak at 45-49F (4.00).

## 2.3 Insurance Ownership Rate by Age Band

**Derived from Table 58 (people with 0 policies / total):**

| Age Band | Total Pop | 0 Policies | Ownership Rate |
|----------|-----------|------------|----------------|
| 0-4 | 178,435 | 120,909 | 32.2% |
| 5-9 | 198,760 | 128,888 | 35.1% |
| 10-14 | 199,993 | 123,122 | 38.4% |
| 15-19 | 204,913 | 115,396 | 43.7% |
| 20-24 | 237,720 | 106,569 | 55.2% |
| 25-29 | 278,037 | 85,900 | 69.1% |
| 30-34 | 301,060 | 67,021 | 77.7% |
| 35-39 | 289,221 | 62,414 | 78.4% |
| 40-44 | 292,770 | 56,685 | 80.6% |
| 45-49 | 300,125 | 46,199 | 84.6% |
| 50-54 | 285,962 | 47,471 | 83.4% |
| 55-59 | 298,226 | 79,608 | 73.3% |
| 60-64 | 282,612 | 102,927 | 63.6% |
| 65-69 | 235,391 | 107,004 | 54.6% |
| 70+ | 403,617 | 278,847 | 30.9% |

**Key pattern**: Ownership peaks at 45-49 (84.6%), drops sharply after 60.

---

# 3. Coverage Amounts by Age × Gender

## 3.1 Average Life (Mortality) Insurance Coverage per Insured Person (S$)

**Table 60 from LIA PGS 2022:**

| Age Band | Male | Female |
|----------|------|--------|
| 0-4 | 122,961 | 124,412 |
| 5-9 | 140,986 | 141,147 |
| 10-14 | 139,780 | 142,402 |
| 15-19 | 149,517 | 149,904 |
| 20-24 | 195,161 | 205,313 |
| 25-29 | 312,975 | 319,203 |
| 30-34 | 410,400 | 395,944 |
| 35-39 | 497,188 | 428,534 |
| 40-44 | 515,623 | 425,622 |
| 45-49 | 487,145 | 394,652 |
| 50-54 | 433,300 | 351,261 |
| 55-59 | 345,786 | 293,885 |
| 60-64 | 280,287 | 255,972 |
| 65-69 | 221,641 | 211,859 |
| 70+ | 124,799 | 127,224 |

## 3.2 Average CI Insurance Coverage per Insured Person (S$)

**Table 61 from LIA PGS 2022:**

| Age Band | Male | Female |
|----------|------|--------|
| 0-4 | 196,701 | 198,303 |
| 5-9 | 162,775 | 163,138 |
| 10-14 | 140,064 | 143,461 |
| 15-19 | 127,341 | 131,102 |
| 20-24 | 139,392 | 154,550 |
| 25-29 | 195,292 | 199,624 |
| 30-34 | 232,886 | 226,023 |
| 35-39 | 264,092 | 241,052 |
| 40-44 | 260,469 | 225,581 |
| 45-49 | 239,677 | 194,321 |
| 50-54 | 209,486 | 160,844 |
| 55-59 | 154,471 | 122,934 |
| 60-64 | 116,022 | 96,739 |
| 65-69 | 83,580 | 69,604 |
| 70+ | 64,669 | 47,893 |

---

# 4. Coverage by Product Type

## 4.1 Total Life Insurance Coverage by Product Type (S$ millions)

**Table 64:**

| Product | Total (S$m) | Share |
|---------|-------------|-------|
| Whole of Life (WoL) | 243,911 | 30.0% |
| Term | 256,661 | 31.5% |
| Personal Accident (PA) | 106,550 | 13.1% |
| Endowment | 95,108 | 11.7% |
| MRTA | 35,890 | 4.4% |
| Universal Life | 25,497 | 3.1% |
| Rider | 44,313 | 5.4% |
| Others + Annuity | 6,042 | 0.7% |
| **Total** | **813,972** | **100%** |

## 4.2 Total CI Coverage by Product Type (S$ millions)

**Table 65:**

| Product | Total (S$m) | Share |
|---------|-------------|-------|
| Whole of Life (WoL) | 140,380 | 48.7% |
| Term | 78,970 | 27.4% |
| Endowment | 13,806 | 4.8% |
| MRTA | 12,232 | 4.2% |
| Rider | 38,334 | 13.3% |
| PA + Others + Annuity | 4,516 | 1.6% |
| **Total** | **288,238** | **100%** |

**Key insight for product ownership modeling:**
- WoL dominates for children and elderly
- Term dominates ages 30-49 (working years)
- CI coverage mostly via WoL (49%) + Term (27%) + Rider (13%)

---

# 5. Protection Gap Statistics

## 5.1 EA (Economically Active) Adults

| Metric | Mortality | CI |
|--------|----------|-----|
| Population | 2,187,833 | 2,187,833 |
| Total Protection Need | S$1,781 bn | S$783 bn |
| Existing Insurance Coverage | S$787 bn | S$204 bn |
| CPF + Other Savings | S$621 bn | — |
| **Protection Gap** | **S$373 bn (21%)** | **S$579 bn (74%)** |
| Avg per EA: Insurance | 3.6x annual income | 1.0x annual income |
| Avg per EA: Gap | 1.9x annual income | 2.9x annual income |

## 5.2 EA Adults by Age Band

**Table 19:**

| Age Band | EA Adults | Avg Annual Income (S$) |
|----------|-----------|------------------------|
| 20-24 | 128,667 | 56,232 |
| 25-29 | 233,367 | 81,505 |
| 30-34 | 295,100 | 98,955 |
| 35-39 | 273,100 | 109,494 |
| 40-44 | 267,400 | 116,645 |
| 45-49 | 253,700 | 117,008 |
| 50-54 | 213,150 | 101,818 |
| 55-59 | 214,550 | 91,495 |
| 60-64 | 191,450 | 65,127 |
| 65-69 | 117,350 | 38,920 |

## 5.3 Platform Workers (PW)

| Metric | Mortality | CI |
|--------|----------|-----|
| Population | 68,568 | 68,568 |
| Avg Insurance Coverage | 5.6x income | — |
| **Protection Gap** | **59%** | **91%** |
| Avg Income | S$35,646/year | S$35,646/year |

---

# 6. Survey Insights (775 EA + 60 PW respondents)

## 6.1 Financial Concerns (EA)
- Healthcare expenses: 65%
- Retirement planning: 62%
- Inability to work due to CI: 30%
- Legacy planning: 23%

## 6.2 Reasons for Buying Additional Insurance
- Insufficient existing coverage: 45% (EA), 43% (PW)
- Financial responsibility for dependents: 32% (EA), 27% (PW)

## 6.3 Reasons for NOT Buying
- Cannot afford: 50% (EA), 37% (PW)
- Too expensive: 47% (EA), 47% (PW)

## 6.4 COVID-19 Impact
- Concern about own medical expenses: 41% (EA), 38% (PW)
- Job/income uncertainty: 23% (EA), 33% (PW)

## 6.5 Group Insurance (PW specific)
- 60% of PW not covered by group insurance
- 16% unaware of any group insurance coverage

---

# 7. Health Insurance Landscape

## 7.1 MediShield Life (Universal)
- **Coverage**: 100% of all SC and PR (automatic enrollment)
- **Premium by age** (annual, approximate):

| Age | Annual Premium (S$) |
|-----|-------------------|
| 0-20 | 130-150 |
| 21-30 | 150-180 |
| 31-40 | 170-210 |
| 41-50 | 300-420 |
| 51-60 | 550-780 |
| 61-70 | 980-1,400 |
| 71-80 | 1,500-2,100 |
| 81+ | 2,200-2,600 |

- Annual Claim Limit: S$150,000
- Lifetime Claim Limit: Unlimited
- Covers Class B2/C wards in public hospitals

## 7.2 Integrated Shield Plans (IP)

**7 IP Insurers:**
1. AIA — HealthShield Gold Max
2. Great Eastern — GREAT SupremeHealth
3. Prudential — PRUShield
4. NTUC Income — IncomeShield
5. Singlife — Shield Plan
6. Raffles Health Insurance — Raffles Shield
7. AXA — (legacy plans being transitioned)

**IP Tier Structure:**
- **Private Hospital**: Highest coverage, highest premiums
- **Class A**: Public hospital Class A wards
- **Class B1**: Public hospital Class B1 wards
- **MediShield Life only**: Class B2/C wards (no IP needed)

**IP Coverage Rate**: 71% of Singaporeans
- Of those, 67% have riders (~2M people)
- Lives covered grew: 3.14M (2014) → 3.99M (2023)
- Gross premium per life (2023): S$668
- Gross claims per life (2023): S$548

---

# 8. Proposed Insurance Profile CPT Structure — 数据溯源标注

**溯源等级说明：**
- **[HARD]** = 直接引用原始数据表，精确到表号/页码
- **[DERIVED]** = 从硬数据经简单计算（除法、减法）得出，可复现
- **[ESTIMATED]** = 无直接数据，基于相关硬数据的推断/内插，需要验证
- **[GAP]** = 无任何数据支撑，纯假设，需要寻找新数据源

---

## 8.1 Field 1: has_medishield_life (boolean)

| CPT 值 | 溯源 |
|--------|------|
| P(true) = 1.00，所有年龄 | **[HARD]** CPF 官网："All Singapore Citizens and Permanent Residents are automatically covered." |

---

## 8.2 Field 2: has_ip (boolean)

**总体边际：** 71% [HARD] MOH 2025-11 新闻稿："71 per cent of Singaporeans have IPs"

**按年龄×收入分解：** **[GAP]** — MOH 只给了总体 71%，没有给出按 age×income 的分解。

现有硬数据约束：
- 总体 71%：[HARD] MOH
- IP lives covered 3.99M (2023)：[HARD] SAS Discussion Paper
- 新加坡 SC+PR 人口 ~4.05M SC + 0.54M PR = ~4.59M：[HARD] SingStat
- 3.99M / 4.59M ≈ 87%（含重复计数？或含 dependents？）→ 与 71% 有差异，需核实

**TODO**: 需要找到 MOH/LIA 按年龄段的 IP 覆盖率数据。目前 age×income 的 CPT 全部是 **[ESTIMATED]**，不可直接使用。

---

## 8.3 Field 3: ip_tier — P(tier | has_ip, income, housing)

### 硬数据来源：MOH Official Statement（Criteria for Inclusion of Medical Specialists into Insurer's Panel）

**IP Tier 分布（占全部新加坡居民的百分比）：**

| IP Tier | % of All Residents | 溯源 |
|---------|-------------------|------|
| Private Hospital IP | **40%** | **[HARD]** MOH 官方声明 |
| Class A IP | **20%** | **[HARD]** MOH 官方声明 |
| Class B1 IP | **10%** | **[HARD]** MOH 官方声明 |
| Standard IP | **<1%** | **[HARD]** MOH 官方声明 |
| MediShield Life only (no IP) | ~29% | **[DERIVED]** 100% - 71% |
| **Total with IP** | **~71%** | **[HARD]** MOH Nov 2025 |

**换算为 IP 持有者中的 tier 分布（条件概率 P(tier | has_ip)）：**

| IP Tier | % of IP Holders | 溯源 |
|---------|----------------|------|
| Private Hospital | **56.3%** (40/71) | **[DERIVED]** |
| Class A | **28.2%** (20/71) | **[DERIVED]** |
| Class B1 | **14.1%** (10/71) | **[DERIVED]** |
| Standard IP | **~1.4%** (<1/71) | **[DERIVED]** |

**关键发现：**
- **超过一半的 IP 持有者选择了 Private Hospital tier！** 这出乎意料 — 说明新加坡人普遍愿意为高端医疗付费
- Private > A > B1 的顺序可能反映了 IP 市场早期以 Private 为主的历史格局
- 按收入的分解仍是 [ESTIMATED]，但有了总体分布，约束力强多了

**按 income × housing 的 CPT 推导逻辑：**
- 高收入（>S$8,000/月）+ Private housing → P(Private) ≈ 0.85
- 中收入（S$3,000-8,000）+ HDB 4-5 Room → P(Private) ≈ 0.55, P(A) ≈ 0.30
- 低收入（<S$3,000）+ HDB 1-3 Room → P(B1) ≈ 0.40, P(A) ≈ 0.35, P(Private) ≈ 0.15
- 这些是 **[ESTIMATED]**，但必须 marginalize 到上面的总体分布

---

## 8.4 Field 4: has_rider — P(rider | has_ip)

| CPT 值 | 溯源 |
|--------|------|
| 总体 67% | **[HARD]** MOH 2025-11："67 per cent of these IP policyholders have riders (about two million people)" |
| 按年龄分解（<50: 0.72, 50-64: 0.65, 65+: 0.55） | **[ESTIMATED]** 无直接数据。推理：MOH 提到老年人对保费敏感，可能降级或取消 rider |

---

## 8.5 Field 5: ip_insurer — P(insurer | has_ip)

**[GAP]** — 无公开的 IP 各保险公司市场份额数据。

已知约束：
- 7 家 IP 保险公司名单：[HARD] MOH 比较表
- LIA 行业统计可能有按公司分的保费/人数，但未公开下载

**TODO**: 查找 MAS Annual Report 或 LIA Business Statistics 中是否有按 insurer 分的 IP lives covered。

---

## 8.6 Field 6: has_term_life — P(term_life | age)

### 硬数据来源：PGS Table 68（Lives Covered by Life Insurance by Age Band and Product Type）

| Age Band | Term Lives | Total Pop (T58) | **Term Rate** | 溯源 |
|----------|-----------|-----------------|-------------|------|
| 0-4 | 4,995 | 178,435 | 2.8% | **[DERIVED]** T68/T58 |
| 5-9 | 6,197 | 198,760 | 3.1% | **[DERIVED]** |
| 10-14 | 7,933 | 199,993 | 4.0% | **[DERIVED]** |
| 15-19 | 9,882 | 204,913 | 4.8% | **[DERIVED]** |
| 20-24 | 23,324 | 237,720 | 9.8% | **[DERIVED]** |
| 25-29 | 58,448 | 278,037 | **21.0%** | **[DERIVED]** |
| 30-34 | 106,712 | 301,060 | **35.4%** | **[DERIVED]** |
| 35-39 | 110,337 | 289,221 | **38.2%** | **[DERIVED]** |
| 40-44 | 115,084 | 292,770 | **39.3%** | **[DERIVED]** |
| 45-49 | 132,834 | 300,125 | **44.3%** | **[DERIVED]** |
| 50-54 | 108,623 | 285,962 | **38.0%** | **[DERIVED]** |
| 55-59 | 68,446 | 298,226 | **22.9%** | **[DERIVED]** |
| 60-64 | 44,759 | 282,612 | **15.8%** | **[DERIVED]** |
| 65-69 | 21,961 | 235,391 | **9.3%** | **[DERIVED]** |
| 70+ | 7,649 | 403,617 | **1.9%** | **[DERIVED]** |
| **Total** | **827,184** | **4,866,852** | **17.0%** | **[DERIVED]** |

**关键发现：**
- Term 覆盖率在 45-49 达到峰值（44.3%），远高于之前估计的 ~25%
- 与 Table 68 Total = 4,915,131 比较，同一个人可被多个产品类型计数
- Term 的"lives covered"含义：拥有至少一张 Term 保单的唯一人数
- 注意：Table 68 说明 "the same life can be represented multiple times, once for each product type"，但**同一产品类型内不重复计数**

**按 marital 的分解仍是 [ESTIMATED]**：PGS 没有给出 Term 按婚姻状态的数据。逻辑推理：已婚有 dependents 的人更可能买 Term。

---

## 8.7 Field 7: term_life_coverage (S$)

### 硬数据来源：PGS Table 66（Average Life Insurance Coverage per Life Insured by Age Band and Product Type）

**Term 产品平均保额（S$）：**

| Age Band | Term Avg Coverage (S$) | 溯源 |
|----------|----------------------|------|
| 0-4 | 221,327 | **[HARD]** PGS Table 66 |
| 5-9 | 212,567 | **[HARD]** |
| 10-14 | 185,508 | **[HARD]** |
| 15-19 | 205,044 | **[HARD]** |
| 20-24 | 273,837 | **[HARD]** |
| 25-29 | 406,756 | **[HARD]** |
| 30-34 | 417,242 | **[HARD]** |
| 35-39 | 450,602 | **[HARD]** |
| 40-44 | 421,793 | **[HARD]** |
| 45-49 | 295,218 | **[HARD]** |
| 50-54 | 213,810 | **[HARD]** |
| 55-59 | 150,972 | **[HARD]** |
| 60-64 | 81,416 | **[HARD]** |
| 65-69 | 46,940 | **[HARD]** |
| 70+ | 45,483 | **[HARD]** |

**关键发现：**
- Term 平均保额在 35-39 达峰（S$450,602），高于 WoL（S$161,267）
- Term 是高保额低保费的"纯保障"产品，适合中青年家庭
- 45+ 保额急剧下降，反映续保困难和保费上升
- 注意：这是"per life insured"，即有 Term 保单的人的平均值，不需要再除以覆盖率

**对比 WoL 平均保额（Table 66 WoL 列）：**

| Age Band | WoL Avg (S$) | Term Avg (S$) | Term/WoL 倍数 |
|----------|-------------|--------------|-------------|
| 25-29 | 134,913 | 406,756 | 3.0x |
| 30-34 | 144,678 | 417,242 | 2.9x |
| 35-39 | 161,267 | 450,602 | 2.8x |
| 40-44 | 164,863 | 421,793 | 2.6x |
| 45-49 | 170,537 | 295,218 | 1.7x |

Term 保额是 WoL 的 2-3 倍，符合产品特性（纯保障 vs 储蓄+保障）。

---

## 8.8 Field 8: has_ci — P(CI | age)

### 硬数据来源：PGS Table 69（Lives Covered by CI Insurance by Age Band and Product Type）

**重要注意：Table 69 的 Total 列存在重复计数问题。**
- Table 69 Total 列加总 = 2,053,192（同一人可同时持有 WoL CI + Term CI + Rider CI）
- PGS p.59 给出唯一 CI 持有人 = **1,491,042**
- 重复计数系数 = 2,053,192 / 1,491,042 = **1.377**

**方法：用 Table 69 Total / 1.377 估算每个年龄段的唯一 CI 持有人数**

| Age Band | T69 Total | Est. Unique (÷1.377) | Total Pop (T58) | **CI Rate** | 溯源 |
|----------|-----------|---------------------|-----------------|-----------|------|
| 0-4 | 41,179 | 29,904 | 178,435 | 16.8% | **[DERIVED]** T69/T58, 校准系数 |
| 5-9 | 47,794 | 34,709 | 198,760 | 17.5% | **[DERIVED]** |
| 10-14 | 55,825 | 40,541 | 199,993 | 20.3% | **[DERIVED]** |
| 15-19 | 66,217 | 48,088 | 204,913 | 23.5% | **[DERIVED]** |
| 20-24 | 115,549 | 83,913 | 237,720 | 35.3% | **[DERIVED]** |
| 25-29 | 206,253 | 149,784 | 278,037 | **53.9%** | **[DERIVED]** |
| 30-34 | 267,646 | 194,370 | 301,060 | **64.5%** | **[DERIVED]** |
| 35-39 | 260,276 | 189,017 | 289,221 | **65.3%** | **[DERIVED]** |
| 40-44 | 257,653 | 187,112 | 292,770 | **63.9%** | **[DERIVED]** |
| 45-49 | 243,635 | 176,933 | 300,125 | **58.9%** | **[DERIVED]** |
| 50-54 | 185,798 | 134,930 | 285,962 | **47.2%** | **[DERIVED]** |
| 55-59 | 142,940 | 103,806 | 298,226 | **34.8%** | **[DERIVED]** |
| 60-64 | 91,842 | 66,698 | 282,612 | **23.6%** | **[DERIVED]** |
| 65-69 | 45,275 | 32,880 | 235,391 | **14.0%** | **[DERIVED]** |
| 70+ | 25,310 | 18,381 | 403,617 | **4.6%** | **[DERIVED]** |
| **Total** | **2,053,192** | **1,491,042** | **4,866,852** | **30.6%** | **[DERIVED]** |

**关键发现：**
- CI 覆盖率在 35-39 达到峰值（65.3%），远高于之前估计的 ~30%
- 30-44 年龄段超过 60% 有 CI 保险 — 这是购买高峰
- 但 50+ 急剧下降（续保难、保费贵）
- 70+ 仅 4.6%
- **整体 30.6% 被儿童和老年人拉低**，工作年龄段实际覆盖率很高

**溯源评级说明：** 标记为 [DERIVED] 而非 [HARD]，因为使用了均匀重复计数系数假设。实际上年轻人可能 overlap 更多（WoL CI + Rider CI 双持），老年人 overlap 更少。但在没有按年龄的唯一人数硬数据前，这是最合理的估算。

**按 gender 的分解仍是 [ESTIMATED]**：PGS Table 69 不区分性别。Table 61（CI 平均保额）有性别分解，但不是人头数。

---

## 8.9 Field 9: ci_coverage (S$)

| Age Band | Avg CI Coverage per insured M (S$) | Avg CI Coverage per insured F (S$) | 溯源 |
|----------|-----------------------------------|-----------------------------------|------|
| 20-24 | 139,392 | 154,550 | **[HARD]** PGS Table 61 |
| 25-29 | 195,292 | 199,624 | **[HARD]** PGS Table 61 |
| 30-34 | 232,886 | 226,023 | **[HARD]** PGS Table 61 |
| 35-39 | 264,092 | 241,052 | **[HARD]** PGS Table 61 |
| 40-44 | 260,469 | 225,581 | **[HARD]** PGS Table 61 |
| 45-49 | 239,677 | 194,321 | **[HARD]** PGS Table 61 |
| 50-54 | 209,486 | 160,844 | **[HARD]** PGS Table 61 |
| 55-59 | 154,471 | 122,934 | **[HARD]** PGS Table 61 |
| 60-64 | 116,022 | 96,739 | **[HARD]** PGS Table 61 |
| 65-69 | 83,580 | 69,604 | **[HARD]** PGS Table 61 |
| 70+ | 64,669 | 47,893 | **[HARD]** PGS Table 61 |

注意：这是**有 CI 保单的人**的平均保额，不是全人口平均。直接可用。

---

## 8.10 Field 10: has_whole_life — P(WoL | age)

### 硬数据来源：PGS Table 68（Lives Covered by Life Insurance by Age Band and Product Type — WoL 列）

| Age Band | WoL Lives | Total Pop (T58) | **WoL Rate** | 溯源 |
|----------|----------|-----------------|------------|------|
| 0-4 | 35,356 | 178,435 | 19.8% | **[DERIVED]** T68/T58 |
| 5-9 | 41,257 | 198,760 | 20.8% | **[DERIVED]** |
| 10-14 | 48,930 | 199,993 | 24.5% | **[DERIVED]** |
| 15-19 | 57,142 | 204,913 | 27.9% | **[DERIVED]** |
| 20-24 | 90,131 | 237,720 | 37.9% | **[DERIVED]** |
| 25-29 | 136,653 | 278,037 | **49.2%** | **[DERIVED]** |
| 30-34 | 165,843 | 301,060 | **55.1%** | **[DERIVED]** |
| 35-39 | 158,709 | 289,221 | **54.9%** | **[DERIVED]** |
| 40-44 | 169,344 | 292,770 | **57.8%** | **[DERIVED]** |
| 45-49 | 178,982 | 300,125 | **59.6%** | **[DERIVED]** |
| 50-54 | 160,695 | 285,962 | **56.2%** | **[DERIVED]** |
| 55-59 | 144,999 | 298,226 | **48.6%** | **[DERIVED]** |
| 60-64 | 112,416 | 282,612 | **39.8%** | **[DERIVED]** |
| 65-69 | 75,163 | 235,391 | **31.9%** | **[DERIVED]** |
| 70+ | 59,461 | 403,617 | **14.7%** | **[DERIVED]** |
| **Total** | **1,635,081** | **4,866,852** | **33.6%** | **[DERIVED]** |

**关键发现：**
- WoL 覆盖率在 45-49 达到峰值（59.6%），比 Term（44.3%）更高
- WoL 在所有年龄段都比 Term 更普遍（是新加坡最常见的保险产品）
- 25+ 的 WoL 覆盖率均超过 49%
- 50+ WoL 下降较慢（48.6%→14.7%），而 Term 下降更快（38.0%→1.9%）
- 这反映了 WoL 的终身特性 vs Term 的到期不续
- **WoL 不区分 WoL(Life) vs WoL(CI)**，Table 68 的 WoL 含两者

---

## 8.11 Field 11: monthly_insurance_spend (S$)

**[GAP]** — 没有找到按收入分组的保险月支出硬数据。

已知约束：
- HES 2023 报告保险（纯保障类）≈ 5% 的家庭支出：**[HARD]** SingStat HES
- IP gross premium per life (2023) = S$668/year = ~S$56/month：**[HARD]** SAS Paper
- MediShield Life 保费表（按年龄）：**[HARD]** CPF/MOH

**TODO**:
1. 下载 SingStat HES 2023 详细表格，查找按 income quintile 的保险支出
2. 或从 PGS 的 avg insurance coverage × 典型 premium rate 推导

---

## 8.12 Field 12: medisave_balance (S$)

### 硬数据来源：PGS Section 15.4.5（CPF Annual Report 2021）+ CPF Board Statistics

**总 CPF 储蓄（OA+SA+MA）按年龄分布：**

| Age Band | Members ('000) | Total CPF (S$'000) | Avg CPF (S$) | Est. MediSave (S$) | 溯源 |
|----------|---------------|-------------------|-------------|-------------------|------|
| ≤20 | 432 | 1,753,128 | 4,058 | ~1,200 | **[HARD]** PGS p.131 / CPF AR 2021 |
| >20-25 | 228 | 2,459,776 | 10,788 | ~3,200 | **[HARD]** |
| >25-30 | 287 | 14,605,365 | 50,889 | ~12,700 | **[HARD]** |
| >30-35 | 327 | 32,156,591 | 98,337 | ~22,000 | **[HARD]** |
| >35-40 | 312 | 43,161,063 | 138,338 | ~31,000 | **[HARD]** |
| >40-45 | 327 | 58,222,865 | 178,050 | ~40,000 | **[HARD]** |
| >45-50 | 343 | 72,755,965 | 212,119 | ~48,000 | **[HARD]** |
| >50-55 | 342 | 76,132,230 | 222,609 | ~52,000 | **[HARD]** |
| >55-60 | 378 | 73,469,549 | 194,364 | ~55,000 | **[HARD]** |
| >60 | 1,133 | 130,967,397 | 115,595 | ~50,000 | **[HARD]** |

**Est. MediSave 列推导逻辑（[DERIVED]）：**
- MediSave 占总 CPF 的比例随年龄变化：年轻人 ~25%（OA 占比高），55+ ~30%（OA 已提取/转入 RA）
- 2025Q3 全国 MediSave 总余额 S$148.7bn / 总 CPF S$649.3bn = **22.9%**：**[HARD]** CPF Board Statistics
- BHS 上限 S$71,500（2025）：**[HARD]** CPF 官网
- 55+ MediSave 余额受 BHS 上限约束，估算偏保守
- PW 平均 CPF 储蓄仅 S$25,829：**[HARD]** PGS Table 42

**MediSave 估算的关键约束：**
1. MediSave 占总 CPF ~23%（全国平均）
2. 年轻人 OA 占比高（买房），MediSave 占比低 ~20-25%
3. 55+ BHS 上限 S$71,500，实际多数人远低于此
4. 60+ 平均 CPF 仅 S$115,595，因已大量提取 OA/SA

注意：以上是**总 CPF** 而非纯 MediSave。Est. MediSave 列是 **[DERIVED]**（总 CPF × 估算比例），不是 [HARD]。真正的 MediSave by age 需要 CPF Annual Report 详细表格。

---

## 8.13 Field 13: insurance_attitude

### 硬数据来源：PGS Section 16（Detailed Supplementary Market Survey，775 EA + 60 PW）

**16.2.1 财务担忧来源（EA）：**

| 担忧类型 | EA % | PW % | 溯源 |
|---------|------|------|------|
| Healthcare expenses | 65% | 68% | **[HARD]** PGS Section 16.2.1 / 16.4.1 |
| Retirement planning | 62% | 45% | **[HARD]** |
| Inability to work due to CI | 30% | 32% | **[HARD]** |
| Funding children's education | 26% | 27% | **[HARD]** |
| Funding expenses of ageing parents | 25% | 28% | **[HARD]** |
| Legacy and wealth planning | 23% | 17% | **[HARD]** |
| Paying off mortgage loans | 22% | 15% | **[HARD]** |

**16.2.4 购买保险的原因（EA vs PW）：**

| 原因 | EA % | PW % | 溯源 |
|------|------|------|------|
| Existing coverage not enough | 45% | 43% | **[HARD]** PGS Section 16.2.4 / 16.4.5 |
| Financial responsibilities for dependents | 32% | 27% | **[HARD]** |
| Feel less healthy than before | 22% | 18% | **[HARD]** |
| Entering a new phase of life | 22% | 13% | **[HARD]** |
| No other financial commitments | 22% | 10% | **[HARD]** |
| Intend to leave inheritance | 17% | 12% | **[HARD]** |
| Advise from family/friends | 17% | 23% | **[HARD]** |
| Know family/friends with same policy | 10% | 10% | **[HARD]** |

**16.2.5 不购买保险的原因（EA vs PW）：**

| 原因 | EA % | PW % | 溯源 |
|------|------|------|------|
| Cannot afford additional expense | 50% | 37% | **[HARD]** PGS Section 16.2.5 / 16.4.6 |
| Insurance premium too expensive | 47% | 47% | **[HARD]** |
| Existing coverage is sufficient | 31% | 23% | **[HARD]** |
| Enough savings to cover illness | 13% | 3% | **[HARD]** |
| No need, extremely healthy | 9% | 15% | **[HARD]** |

**16.2.6 对保险行业的改善诉求：**

| 诉求 | % | 溯源 |
|------|---|------|
| Use plain language | 52% | **[HARD]** PGS Section 16.2.6 |
| Simple illustration/tools | 52% | **[HARD]** |
| More straightforward products | 52% | **[HARD]** |
| More accessible touchpoints | 39% | **[HARD]** |
| Higher flexibility/customization | 36% | **[HARD]** |

**16.2.8 保额认知差距：**
- 受访者自报平均死亡保额 S$433K（含团险） vs 保单数据 S$381K：**[HARD]**
- 受访者自报平均 CI 保额 S$106K ≈ 保单数据 S$106K：**[HARD]**
- 86% EA 目标死亡保额 < 实际需求（avg needed S$551K vs targeted S$289K）：**[HARD]**
- 76% EA 目标 CI 保额 < 实际需求（avg needed S$354K vs targeted S$265K）：**[HARD]**

**16.2.2 COVID-19 影响：**
- 41% EA 因 COVID 对保险覆盖产生担忧（post-COVID 31% 情况变差）：**[HARD]**
- 主要担忧：自身医疗费用 41% EA / 38% PW，收入不确定性 23% EA / 33% PW：**[HARD]**

**5 分类态度 CPT 推导（[DERIVED]）：**

基于以上硬数据，可以构建态度分类：

| 态度类型 | 定义 | 估算比例 | 推导逻辑 | 溯源 |
|---------|------|---------|---------|------|
| **proactive** | 主动寻求更多保障 | ~20% | 22% "entering new life phase" + 22% "no other commitments" 的交集 | **[DERIVED]** |
| **adequate** | 认为现有保障足够 | ~25% | 31% "coverage sufficient" - 部分实际不足 | **[DERIVED]** |
| **passive** | 知道不足但不行动 | ~25% | 63% 意识 CI 不足 - 实际购买者 | **[DERIVED]** |
| **resistant** | 认为太贵/负担不起 | ~20% | 50% "can't afford" ∩ 47% "too expensive" 去重 | **[DERIVED]** |
| **unaware** | 不了解保障缺口 | ~10% | 74% 不意识死亡保额不足 × (1-insurance ownership) | **[DERIVED]** |

---

## 8.14 Field 14: protection_gap_awareness

| 数据点 | 值 | 溯源 |
|--------|---|------|
| EA 意识到死亡保额不足 | 26% | **[HARD]** PGS Executive Summary |
| EA 意识到 CI 保额不足 | 63% | **[HARD]** PGS Executive Summary |

**综合后的 40%/60% 分布是 [DERIVED]**（简单加权平均）。
按年龄、收入的分解是 **[GAP]**。

---

## 8.15 Field 15: preferred_channel

**[ESTIMATED]** — 没有直接的渠道分布硬数据，但有间接约束。

间接硬数据：
- 17% EA 购买保险因 "advise from family/friends"：**[HARD]** PGS S16.2.4
- 23% PW 购买保险因 "advise from family/friends"（PW 依赖社交圈更多）：**[HARD]** PGS S16.4.5
- 39% EA 希望 "more accessible touchpoints/helpline"：**[HARD]** PGS S16.2.6
- 52% EA 希望 "simple illustrations or tools"：**[HARD]** PGS S16.2.6 — 暗示线上工具需求强

**估算的渠道分布 [ESTIMATED]：**

| Channel | Est. % | 推理 |
|---------|--------|------|
| Insurance agent (tied) | 45% | 新加坡传统主力渠道 |
| Financial advisor (IFA) | 20% | 独立理财顾问 |
| Online/direct | 15% | 年轻化趋势，COVID 加速 |
| Bank (bancassurance) | 12% | 银行交叉销售 |
| Employer/group | 8% | 团险渠道 |

**TODO**: 查找 LIA/MAS 的分销渠道报告（Distribution Channel Statistics），获取硬数据。

---

## 8.16 Field 16: last_life_event_trigger

### 硬数据来源：PGS Section 16.2.4（Reasons for Purchasing Insurance）

**购买保险的触发因素可以直接作为 life_event_trigger 的分布基础：**

| Trigger | EA % | PW % | 映射到 life_event_trigger | 溯源 |
|---------|------|------|------------------------|------|
| Existing coverage not enough | 45% | 43% | "coverage_review" | **[HARD]** PGS S16.2.4 |
| Financial responsibilities for dependents | 32% | 27% | "new_dependent" (marriage/child) | **[HARD]** |
| Feel less healthy than before | 22% | 18% | "health_scare" | **[HARD]** |
| Entering a new phase of life | 22% | 13% | "life_phase_change" (job/marriage/parent) | **[HARD]** |
| No other financial commitments | 22% | 10% | "financial_capacity" | **[HARD]** |
| Intend to leave inheritance | 17% | 12% | "legacy_planning" | **[HARD]** |
| Advise from family/friends | 17% | 23% | "social_influence" | **[HARD]** |
| Know family/friends with same policy | 10% | 10% | "social_influence" | **[HARD]** |

**注意：** 这些百分比是"购买保险的人"的原因分布（多选），不是全人口的 life_event_trigger 分布。
但可以作为 trigger CPT 的有力约束。

**从 trigger → life_event_trigger 字段的映射 [DERIVED]：**

| life_event_trigger 值 | 估算比例 | 推导逻辑 |
|---------------------|---------|---------|
| marriage | 15% | "new phase" 22% × ~50%（结婚占比）+ "dependents" 部分 |
| new_child | 20% | "dependents" 32% × ~60%（有孩子的占比） |
| health_concern | 15% | "feel less healthy" 22% × 调整 |
| job_change | 10% | "new phase" 22% × ~30%（换工作占比） |
| home_purchase | 10% | "mortgage" 相关 + MRTA 需求 |
| aging_parents | 8% | "funding ageing parents" 25% × 调整 |
| none_recent | 22% | 无特定触发事件 |

这些比例是 **[DERIVED]** — 基于硬数据的合理推断，但具体映射比例有主观成分。

---

## 8.17 Field 17: annual_hospitalization_frequency

**[ESTIMATED]** — 引用了 "MOH data, 12% per year" 但没有标注具体出处。

**TODO**: 查找 MOH Hospital Statistics（admissions per 1,000 population by age）获取硬数据。

---

# 9. Key Derived Statistics for CPT Construction

## 9.1 Marginal Targets (All-Age Benchmarks) — 更新后

| Field | Category | Target % | 溯源 |
|-------|----------|----------|------|
| has_medishield_life | TRUE | 100% | **[HARD]** CPF |
| has_ip | TRUE | 71% | **[HARD]** MOH 2025 |
| has_ip (with rider) | TRUE | 47.6% (71% × 67%) | **[DERIVED]** MOH |
| has_any_individual_insurance | TRUE | 62% | **[HARD]** PGS S10.1 |
| has_ci | TRUE | **30.6%** (1,491,042/4,866,852) | **[DERIVED]** PGS p.59/T58 |
| has_term_life | TRUE | **17.0%** (827,184/4,866,852) | **[DERIVED]** PGS T68/T58 |
| has_whole_life | TRUE | **33.6%** (1,635,081/4,866,852) | **[DERIVED]** PGS T68/T58 |

**修正说明：**
- has_term_life 从之前估计的 ~25% 修正为 17.0%（Table 68 硬数据）
- has_whole_life 从之前估计的 ~45% 修正为 33.6%（Table 68 硬数据）
- 这些是全年龄段平均值，被大量儿童和老年人拉低；工作年龄段（30-49）Term 覆盖率 35-44%，WoL 覆盖率 55-60%

## 9.2 Sum Assured Caps by Income Quintile × Age × Gender (S$ millions)

**Mortality — Table 16:**

| Quintile→ | Q1 M | Q1 F | Q3 M | Q3 F | Q5 M | Q5 F |
|-----------|------|------|------|------|------|------|
| 20-24 | 1.8 | 1.6 | 3.1 | 2.6 | 3.8 | 3.5 |
| 30-34 | 1.8 | 1.7 | 3.0 | 2.7 | 4.1 | 3.9 |
| 40-44 | 1.5 | 1.4 | 2.5 | 2.3 | 3.6 | 3.3 |
| 50-54 | 1.1 | 1.0 | 1.5 | 1.4 | 2.5 | 2.4 |
| 60-64 | 0.7 | 0.7 | 1.1 | 1.1 | 1.5 | 1.5 |

**CI — Table 29:**

| Quintile→ | Q1 M | Q1 F | Q3 M | Q3 F | Q5 M | Q5 F |
|-----------|------|------|------|------|------|------|
| 20-24 | 0.5 | 0.4 | 0.7 | 0.7 | 1.4 | 0.9 |
| 30-34 | 0.5 | 0.4 | 1.0 | 0.7 | 1.2 | 0.8 |
| 40-44 | 0.5 | 0.4 | 0.9 | 0.7 | 1.1 | 0.9 |
| 50-54 | 0.4 | 0.3 | 0.5 | 0.5 | 0.7 | 0.7 |
| 60-64 | 0.3 | 0.2 | 0.4 | 0.4 | 0.5 | 0.5 |

---

# 10. Implementation Priorities

## Phase 1 (Core — 5 fields)
1. **has_medishield_life** — trivial (all TRUE)
2. **has_ip** — CPT on age × income
3. **ip_tier** — CPT on income × housing
4. **has_term_life** — CPT on age × marital × income
5. **has_ci** — CPT on age × gender

## Phase 2 (Coverage amounts — 4 fields)
6. **term_life_coverage** — continuous, log-normal by age × income
7. **ci_coverage** — continuous, log-normal by age × gender
8. **monthly_insurance_spend** — derived from product holdings
9. **medisave_balance** — CPT on age × income

## Phase 3 (Behavioral — 4 fields)
10. **insurance_attitude** — CPT on age × income × education
11. **protection_gap_awareness** — CPT on education × income
12. **preferred_channel** — CPT on age × education
13. **last_life_event_trigger** — CPT on age × marital

## Phase 4 (Supplementary — 4 fields)
14. **has_rider** — CPT on has_ip × income
15. **ip_insurer** — categorical, uniform-ish with market share weights
16. **has_whole_life** — CPT on age × income
17. **annual_hospitalization_frequency** — CPT on age

---

# 11. Raw Data: PGS Tables 66-69（完整原始数据）

## 11.1 Table 66: Average Life Insurance Coverage per Life Insured by Age Band and Product Type (S$)

| Age | WoL | Term | PA | Endowment | MRTA | Universal Life | Others | Rider | Annuity |
|-----|-----|------|----|-----------|------|----------------|--------|-------|---------|
| 0-4 | 108,771 | 221,327 | 31,976 | 33,574 | 1,220,776 | 700,000 | 10,422 | 115,889 | - |
| 5-9 | 117,161 | 212,567 | 31,176 | 40,172 | 1,584,262 | 768,750 | - | 121,104 | - |
| 10-14 | 116,278 | 185,508 | 27,832 | 38,802 | 1,685,667 | 1,110,000 | 100,000 | 105,938 | - |
| 15-19 | 115,430 | 205,044 | 55,774 | 36,949 | 1,387,493 | 1,112,121 | 73,049 | 95,080 | - |
| 20-24 | 122,745 | 273,837 | 108,871 | 42,861 | 1,170,627 | 1,572,402 | 59,149 | 104,063 | - |
| 25-29 | 134,913 | 406,756 | 142,130 | 54,853 | 1,116,071 | 1,641,373 | 64,300 | 126,111 | 30,650 |
| 30-34 | 144,678 | 417,242 | 162,875 | 58,950 | 1,004,013 | 1,943,786 | 63,280 | 144,264 | 24,488 |
| 35-39 | 161,267 | 450,602 | 189,600 | 63,489 | 762,843 | 2,230,344 | 68,453 | 141,528 | 30,824 |
| 40-44 | 164,863 | 421,793 | 200,496 | 71,176 | 652,321 | 2,058,255 | 83,138 | 128,014 | 38,034 |
| 45-49 | 170,537 | 295,218 | 202,743 | 84,407 | 571,161 | 2,206,047 | 105,071 | 121,785 | 35,461 |
| 50-54 | 170,742 | 213,810 | 207,404 | 99,082 | 505,675 | 2,136,233 | 113,478 | 108,858 | 29,887 |
| 55-59 | 165,210 | 150,972 | 192,262 | 106,084 | 385,701 | 2,051,219 | 108,391 | 95,675 | 26,535 |
| 60-64 | 156,292 | 81,416 | 183,208 | 112,805 | 319,991 | 2,086,848 | 82,894 | 94,543 | 26,699 |
| 65-69 | 137,558 | 46,940 | 149,465 | 112,744 | 321,966 | 2,013,781 | 55,633 | 82,216 | 14,015 |
| 70+ | 102,833 | 45,483 | 69,533 | 104,685 | 465,328 | 2,056,092 | 3,186 | 78,622 | 14,431 |

## 11.2 Table 67: Average CI Insurance Coverage per Life Insured by Age Band and Product Type (S$)

| Age | WoL | Term | PA | Endowment | MRTA | Others | Rider | Annuity |
|-----|-----|------|----|-----------|------|--------|-------|---------|
| 0-4 | 184,712 | 442,126 | - | 95,005 | 1,355,556 | 10,000 | 115,907 | - |
| 5-9 | 141,859 | 394,136 | - | 48,071 | 1,010,953 | - | 129,233 | - |
| 10-14 | 126,101 | 372,295 | - | 41,329 | 1,385,172 | 100,000 | 125,386 | - |
| 15-19 | 119,538 | 327,708 | 24,087 | 32,254 | 695,583 | 73,269 | 95,787 | - |
| 20-24 | 129,359 | 296,973 | 8,931 | 27,260 | 543,494 | 58,858 | 99,461 | - |
| 25-29 | 143,999 | 359,796 | 8,309 | 32,540 | 479,405 | 65,766 | 116,290 | - |
| 30-34 | 146,715 | 396,437 | 6,598 | 35,402 | 457,164 | 71,964 | 131,807 | - |
| 35-39 | 150,668 | 419,833 | 12,526 | 36,021 | 466,273 | 83,758 | 143,355 | - |
| 40-44 | 145,400 | 392,547 | 11,679 | 37,460 | 469,159 | 93,490 | 132,123 | 100,000 |
| 45-49 | 135,454 | 352,601 | 15,529 | 41,840 | 436,425 | 97,713 | 115,860 | 35,000 |
| 50-54 | 123,308 | 295,031 | 18,966 | 46,887 | 406,995 | 88,985 | 100,373 | 35,000 |
| 55-59 | 106,367 | 225,654 | 12,272 | 47,569 | 359,330 | 78,662 | 78,671 | - |
| 60-64 | 91,961 | 166,164 | 15,156 | 42,842 | 295,596 | 63,779 | 66,926 | - |
| 65-69 | 76,541 | 130,982 | 11,424 | 21,553 | 190,044 | 55,065 | 53,723 | - |
| 70+ | 60,119 | 126,342 | 17,663 | 17,902 | 250,818 | 48,839 | 39,453 | - |

## 11.3 Table 68: Total Number of Lives Covered by Life Insurance by Age Band and Product Type

| Age | WoL | Term | PA | Endowment | MRTA | Univ.Life | Others | Rider | Annuity | **Total** |
|-----|-----|------|----|-----------|------|-----------|--------|-------|---------|-----------|
| 0-4 | 35,356 | 4,995 | 26,992 | 10,411 | 16 | 20 | 4 | 8,359 | - | **86,153** |
| 5-9 | 41,257 | 6,197 | 27,440 | 19,542 | 31 | 24 | - | 14,913 | - | **109,404** |
| 10-14 | 48,930 | 7,933 | 25,406 | 25,456 | 37 | 20 | 1 | 20,663 | - | **128,446** |
| 15-19 | 57,142 | 9,882 | 26,779 | 33,962 | 101 | 33 | 309 | 21,410 | - | **149,618** |
| 20-24 | 90,131 | 23,324 | 43,266 | 51,311 | 326 | 111 | 3,540 | 23,168 | - | **235,177** |
| 25-29 | 136,653 | 58,448 | 70,046 | 86,987 | 1,202 | 255 | 10,769 | 35,579 | 10 | **399,949** |
| 30-34 | 165,843 | 106,712 | 76,750 | 111,791 | 2,869 | 453 | 12,335 | 46,747 | 37 | **523,537** |
| 35-39 | 158,709 | 110,337 | 64,365 | 116,478 | 6,803 | 693 | 12,317 | 43,459 | 94 | **513,255** |
| 40-44 | 169,344 | 115,084 | 65,854 | 129,338 | 11,366 | 1,273 | 9,849 | 39,436 | 189 | **541,733** |
| 45-49 | 178,982 | 132,834 | 69,583 | 136,434 | 14,490 | 2,000 | 7,117 | 39,248 | 373 | **581,061** |
| 50-54 | 160,695 | 108,623 | 57,334 | 130,216 | 11,400 | 2,272 | 5,415 | 32,604 | 656 | **509,215** |
| 55-59 | 144,999 | 68,446 | 52,721 | 124,972 | 7,460 | 2,177 | 3,896 | 24,570 | 952 | **430,193** |
| 60-64 | 112,416 | 44,759 | 43,150 | 100,703 | 3,543 | 1,527 | 2,177 | 12,756 | 1,540 | **322,571** |
| 65-69 | 75,163 | 21,961 | 28,903 | 68,355 | 901 | 904 | 906 | 5,146 | 5,162 | **207,401** |
| 70+ | 59,461 | 7,649 | 24,414 | 46,121 | 148 | 499 | 4,797 | 2,085 | 32,244 | **177,418** |
| **Total** | **1,635,081** | **827,184** | **703,003** | **1,192,077** | **60,693** | **12,261** | **73,432** | **370,143** | **41,257** | **4,915,131** |

## 11.4 Table 69: Total Number of Lives Covered by CI Insurance by Age Band and Product Type

| Age | WoL | Term | PA | Endowment | MRTA | Others | Rider | Annuity | **Total** |
|-----|-----|------|----|-----------|------|--------|-------|---------|-----------|
| 0-4 | 29,264 | 970 | - | 2,599 | 9 | 1 | 8,336 | - | **41,179** |
| 5-9 | 28,581 | 1,521 | - | 2,942 | 21 | - | 14,729 | - | **47,794** |
| 10-14 | 30,480 | 1,840 | - | 3,363 | 29 | 1 | 20,112 | - | **55,825** |
| 15-19 | 36,838 | 2,910 | 23 | 5,560 | 79 | 308 | 20,499 | - | **66,217** |
| 20-24 | 63,866 | 9,332 | 251 | 18,069 | 268 | 3,371 | 20,392 | - | **115,549** |
| 25-29 | 103,405 | 25,405 | 821 | 33,109 | 990 | 9,609 | 32,914 | - | **206,253** |
| 30-34 | 128,884 | 37,982 | 1,062 | 43,976 | 2,073 | 9,966 | 43,703 | - | **267,646** |
| 35-39 | 121,084 | 38,541 | 841 | 45,430 | 3,742 | 9,189 | 41,449 | - | **260,276** |
| 40-44 | 122,691 | 35,488 | 698 | 47,905 | 5,156 | 7,717 | 37,997 | 1 | **257,653** |
| 45-49 | 120,787 | 29,316 | 532 | 47,218 | 6,578 | 6,128 | 33,074 | 2 | **243,635** |
| 50-54 | 95,300 | 18,685 | 399 | 38,055 | 4,999 | 4,574 | 23,784 | 2 | **185,798** |
| 55-59 | 76,966 | 10,364 | 375 | 32,797 | 2,957 | 3,151 | 16,330 | - | **142,940** |
| 60-64 | 53,274 | 4,730 | 272 | 21,722 | 1,196 | 1,584 | 9,064 | - | **91,842** |
| 65-69 | 30,032 | 1,472 | 172 | 8,666 | 248 | 527 | 4,158 | - | **45,275** |
| 70+ | 17,202 | 442 | 80 | 5,773 | 11 | 116 | 1,686 | - | **25,310** |
| **Total** | **1,058,654** | **218,998** | **5,526** | **357,184** | **28,356** | **56,242** | **328,227** | **5** | **2,053,192** |

**注：** CI Total 存在重复计数（同一人可持有 WoL CI + Term CI + Rider CI）。唯一 CI 持有人 = 1,491,042（PGS p.59），总计数 2,053,192，重复系数 1.377。

---

# 12. Data Gaps Summary（更新后）

## 12.1 已解决（从 [ESTIMATED]/[GAP] 升级）

| Field | 原状态 | 新状态 | 数据来源 |
|-------|--------|--------|---------|
| has_term_life by age | [ESTIMATED] | **[DERIVED]** | PGS Table 68 Term lives / Table 58 pop |
| has_whole_life by age | [ESTIMATED] | **[DERIVED]** | PGS Table 68 WoL lives / Table 58 pop |
| has_ci by age | [ESTIMATED] | **[DERIVED]** | PGS Table 69 (with dedup factor 1.377) |
| term_life_coverage by age | [ESTIMATED] | **[HARD]** | PGS Table 66 Term column |
| ci_coverage by age×gender | already [HARD] | **[HARD]** | PGS Table 61 |
| **ip_tier distribution** | **[GAP]** | **[HARD]** | MOH 官方声明：Private 40%, A 20%, B1 10%, Std <1% |
| **medisave_balance by age** | **[ESTIMATED]** | **[DERIVED]** | PGS p.131 CPF savings by age → MediSave ≈23% |
| **insurance_attitude** | **[ESTIMATED]** | **[DERIVED]** | PGS Section 16 全套调查数据（购买/不购买/诉求/COVID影响） |
| **last_life_event_trigger** | **[GAP]** | **[DERIVED]** | PGS S16.2.4 购买原因 → trigger 映射 |

## 12.2 仍需解决的 [GAP] / [ESTIMATED]

| Field | 当前状态 | 需要的数据 | 候选数据源 |
|-------|---------|-----------|-----------|
| has_ip by age×income | [ESTIMATED] | IP 按年龄段的覆盖率 | MOH/MAS statistics |
| ip_insurer market share | [GAP] | 7家 IP 保险公司的市场份额 | MAS Annual Report |
| has_rider by age | [ESTIMATED] | Rider 按年龄段的持有率 | MOH statistics |
| monthly_insurance_spend | [GAP] | 保险月支出按收入分组 | SingStat HES 2023 详细表 |
| preferred_channel | [ESTIMATED] | 购买渠道分布 | LIA/MAS distribution reports |
| annual_hospitalization_frequency by age | [ESTIMATED] | 住院率按年龄 | MOH data.gov.sg (被 rate limit) |

**进展总结：从 11 个 GAP/ESTIMATED 减少到 6 个。**

---

# 13. References

1. LIA Singapore, "2022 Protection Gap Study — Singapore", prepared by Ernst & Young Advisory Pte Ltd, published 8 September 2023. https://www.lia.org.sg/media/3974/lia-pgs-2022-report_final_8-sep-2023.pdf
2. MAS, "Insurance Statistics 2021-2024". https://www.mas.gov.sg/statistics/insurance-statistics/annual-statistics/insurance-statistics-2021-2024
3. MOH, "About Integrated Shield Plans". https://www.moh.gov.sg/managing-expenses/schemes-and-subsidies/integrated-shield-plans/about-integrated-shield-plans/
4. MOH, "Comparison of Integrated Shield Plans (Jan 2025)". https://www.moh.gov.sg/managing-expenses/schemes-and-subsidies/integrated-shield-plans/comparision-of-integrated-shield-plans/
5. CPF Board, "MediShield Life". https://www.cpf.gov.sg/member/healthcare-financing/medishield-life
6. CPF Board, "MediShield Life 2024 Review". https://www.cpf.gov.sg/member/infohub/news/cpf-related-announcements/medishield-life-2024-review
7. MOH, "New Requirements for IP Riders" (Nov 2025). https://www.moh.gov.sg/newsroom/new-requirements-for-integrated-shield-plan-riders-to-strengthen-sustainability-of-private-health-insurance-and-address-rising-healthcare-costs/
8. Society of Actuaries Singapore, "Discussion Paper: Medical Insurance Premiums" (Nov 2024). https://www.actuaries.org.sg/sites/default/files/2024-11/SAS%20Discussion%20Paper%20Medical%20Insurance%20Premiums%20Nov24%20Final.pdf
9. SingStat, "Household Expenditure Survey 2023". https://www.singstat.gov.sg/publications/households/household-expenditure-survey
10. SmartWealth, "Life Insurance Claims Statistics in Singapore". https://smartwealth.sg/life-insurance-claim-statistics/
11. MOH, "Criteria for Inclusion of Medical Specialists into Insurer's Panel for Integrated Shield Plans". https://www.moh.gov.sg/newsroom/criteria-for-inclusion-of-medical-specialists-into-insurer's-panel-for-integrated-shield/ — **IP tier distribution: Private 40%, A 20%, B1 10%, Standard <1%**
12. CPF Board, "CPF Balances Statistics (Quarterly)". https://www.cpf.gov.sg/member/infohub/reports-and-statistics/cpf-statistics/balances-statistics — **Total MediSave S$148.7bn (2025 Q3)**
13. MOH, "Hospital Admission Rates by Age and Sex 2023". https://www.moh.gov.sg/others/resources-and-statistics/-healthcare-institution-statistics-hospital-admission-rates-by-age-and-sex-hospital-admission-rates-by-age-and-sex-2023/ — **数据存在但 403 无法抓取，需手动查看**
14. Data.gov.sg, "Hospital Admission Rate by Age and Sex". https://data.gov.sg/datasets/d_dd32a9abff167b63efc11fb2f25cb341/view — **CSV 可下载，被 rate limit**
