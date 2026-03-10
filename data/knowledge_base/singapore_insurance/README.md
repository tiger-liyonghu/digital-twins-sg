# Singapore Insurance Vertical Knowledge Base

Knowledge base for Digital Twins Singapore — Insurance vertical backtesting and survey simulation.

Last updated: 2026-03-08

---

## Directory Structure

```
singapore_insurance/
├── README.md                       # This file — index & report summaries
├── sg_insurance_landscape.md       # Structured domain knowledge (9 sections)
├── sg_policyholder_profiles.md     # Policyholder demographics & personas
├── reports/                        # Survey & research reports (PDF)
│   ├── LIA_Protection_Gap_Study_2022.pdf       (2.4M) ★
│   ├── SwissRe_Asia_LH_Consumer_Survey_2025.pdf (728K) ★
│   ├── SwissRe_Singapore_Health_Gap_Infographic.pdf (152K)
│   ├── LIA_PGS_2022_Press_Release.pdf          (423K)
│   └── Capco_Singapore_Insurance_Survey_2023.pdf (47K)
├── official_stats/                 # MAS, MOH, LIA official data
│   ├── MAS_IP_Comparison_ClassA_Jan2025.pdf     (168K)
│   └── MAS_Consultation_Paper_Insurance_Simplification_2024.pdf (834K)
├── backtest_designs/               # Backtest question designs (Protocol v2.0)
│   └── insurance_backtests.md      (6 scenarios: BT-011~014, SV-003~004)
└── data_extracts/                  # Structured data extracted from reports (future)
```

### Knowledge Files

| File | Content | For |
|------|---------|-----|
| `sg_insurance_landscape.md` | 国家医疗保险架构(5层), 产品类型, 渠道, 监管, 品牌, 热点 | Context injection |
| `sg_policyholder_profiles.md` | 4代人群画像, 购买行为, 保障缺口, 收入分层 | Agent persona enrichment |
| `backtest_designs/insurance_backtests.md` | 6个backtest/survey设计 | Simulation execution |

---

## Reports Inventory

### 1. LIA Protection Gap Study 2022 (PGS 2022)

- **File**: `reports/LIA_Protection_Gap_Study_2022.pdf` (2.4 MB)
- **Source**: Life Insurance Association Singapore
- **Published**: September 2023
- **Method**: Policy data from life insurers + market survey of 775 economically active (EA) individuals
- **Coverage**: Singapore residents (citizens + PRs), economically active 21-64

#### Key Findings (Ground Truth for Backtesting)

| Metric | Value |
|--------|-------|
| Mortality protection gap | S$373B (21% gap, 79% covered) |
| Critical illness protection gap | S$579B (74% gap, 26% covered) |
| Avg mortality coverage/policyholder | S$331,200 (3.6x annual income) |
| Avg CI coverage/policyholder | S$193,300 (2.1x annual income) |
| Mortality gap change (2017→2022) | -2% (23% → 21%) |
| CI gap change (2017→2022) | -7% (81% → 74%) |
| Platform workers mortality gap | 59% |
| Platform workers CI gap | 91% |

#### Demographic Breakdowns Available
- By age group (21-30, 31-40, 41-50, 51-64)
- By income level
- By gender
- By marital/family status
- By employment type (employed, self-employed, platform workers)

#### Backtest Applications
- BT-011: "Do you think your insurance coverage is adequate?"
- BT-012: Predict protection gap perception by demographic cohort

---

### 2. Swiss Re Asia L&H Consumer Survey 2025

- **File**: `reports/SwissRe_Asia_LH_Consumer_Survey_2025.pdf` (728 KB)
- **Source**: Swiss Re Institute
- **Published**: July 2025
- **Method**: Survey of 12,000+ consumers across 12 Asian markets
- **Coverage**: Singapore (advanced market) + 11 other Asian markets

#### Key Findings

| Metric | Value |
|--------|-------|
| Health protection gap (12 markets) | USD $258B (+21% vs 2017) |
| Mortality protection gap (12 markets) | USD $132B (+35% vs 2017) |
| Purchase intent (emerging Asia) | 60% plan to buy life insurance next year |
| Pure life policy rejection | >90% don't want pure life, prefer bundled |
| Top barriers | Too expensive, lack of knowledge, product irrelevance |

#### Backtest Applications
- BT-013: "Why don't you buy insurance?" — barrier prediction by demographics
- SV-003: Product preference prediction (bundled vs pure life)
- Cross-market comparison (Singapore vs regional peers)

---

### 3. Swiss Re Singapore Health Gap Infographic

- **File**: `reports/SwissRe_Singapore_Health_Gap_Infographic.pdf` (152 KB)
- **Source**: Swiss Re Institute
- **Key Finding**: 64% of consumers who think they are healthy contribute to 67% of the protection gap
- **Backtest Application**: Predict health confidence vs actual coverage gap

---

### 4. LIA PGS 2022 Press Release

- **File**: `reports/LIA_PGS_2022_Press_Release.pdf` (423 KB)
- **Summary**: Official press release with key statistics and quotes

---

## Official Statistics

### 5. MAS Insurance Statistics 2021-2024

- **URL**: https://www.mas.gov.sg/statistics/insurance-statistics/annual-statistics/insurance-statistics-2021-2024
- **Content**: Annual premiums, policies, claims, distribution channel data
- **Use**: Context injection for insurance market backtests

### 6. MAS Consultation Paper — Insurance Simplification 2024

- **File**: `official_stats/MAS_Consultation_Paper_Insurance_Simplification_2024.pdf` (834 KB)
- **Content**: Proposals to simplify requirements and facilitate access to simple insurance products
- **Use**: Context for SV scenarios on regulatory changes

### 7. MOH Integrated Shield Plan (IP) Reform

- **URL**: https://www.moh.gov.sg/newsroom/new-requirements-for-integrated-shield-plan-riders-to-strengthen-sustainability-of-private-health-insurance-and-address-rising-healthcare-costs/
- **Effective**: April 1, 2026
- **Key Changes**: New IP rider design requirements, ~30% lower premiums for new private hospital riders
- **Use**: Context for IP-related backtests (BT-012, SV-003)

### 8. MAS IP Comparison Table (Class A, Jan 2025)

- **URL**: https://isomer-user-content.by.gov.sg/3/abba3002-6370-4e6b-b7e5-7ab0e8fa095d/Comparison%20of%20IPs%20(Jan%202025)(Class%20A%20IP).pdf
- **Content**: Side-by-side comparison of all Class A Integrated Shield Plans

---

## Market Context Data (for Context Injection)

### Distribution Channels (Q1 2025)

| Channel | Sum Assured | Share |
|---------|------------|-------|
| Financial Advisers (FA) | S$14.6B | 43.3% |
| Tied Representatives | S$10.9B | 32.4% |
| Direct/Online/Insurtech | Fastest growing (16.98% CAGR) | ~10% |
| Bancassurance | Remainder | ~14% |

### Brand Equity (YouGov 2023)

| Brand | Index Score | Purchase Consideration |
|-------|-----------|----------------------|
| NTUC Income | 26.5 | 26.5% |
| Great Eastern | 23.6 | 22.2% |
| AIA | 16.9 | 18.2% |
| Prudential | 16.2 | 16.9% |
| Singlife | 9.8 | 9.6% |
| Manulife | 8.0 | 8.3% |

### Market Size

| Year | Value | Growth |
|------|-------|--------|
| 2024 | USD $66.4B | — |
| 2025 (proj) | +3.0% life, +6.7% general | — |
| 2030 (proj) | USD $115.5B | ~10% CAGR |

### IP Premium Trends (2025)

- All but one private insurer raised IP premiums in 2025
- Drivers: MediShield Life base adjustments, healthcare cost inflation, claims management
- New IP riders (April 2026): expected ~30% lower premiums

---

## Backtest Design Queue

See `backtest_designs/` for detailed question designs following Protocol v2.0.

| ID | Scenario | Ground Truth Source | Status |
|----|----------|-------------------|--------|
| BT-011 | Protection adequacy perception | LIA PGS 2022 | Designed |
| BT-012 | IP price hike response | 2025 premium data + MOH reform | Designed |
| BT-013 | Barriers to insurance purchase | Swiss Re 2025 | Designed |
| BT-014 | Brand trust & preference | YouGov 2023 | Planned |
| SV-003 | MediShield Life +20% scenario | Predictive (calibrate with BT-012) | Planned |
| SV-004 | Platform worker mandatory insurance | LIA PGS platform worker data | Planned |

---

## Key URLs for Future Data Collection

- MAS Insurance Stats: https://www.mas.gov.sg/statistics/insurance-statistics
- LIA Singapore: https://www.lia.org.sg
- MOH Healthcare Schemes: https://www.moh.gov.sg
- Swiss Re Institute: https://www.swissre.com/institute
- YouGov Singapore: https://sg.yougov.com
- GIA Singapore: https://www.gia.org.sg
