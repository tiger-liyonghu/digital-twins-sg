# Technical Architecture: Individual Agent Synthesis

## Digital Twins Singapore -- Population Foundation Layer

**Version**: 2.0 (Proposed V3 with NVIDIA Nemotron-Personas)
**Last Updated**: 2026-03-06

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Data Sources & Statistical Authority](#2-data-sources--statistical-authority)
3. [Phase 1: Joint Demographic Distribution via IPF](#3-phase-1-joint-demographic-distribution-via-ipf)
4. [Phase 2: Bayesian Network Attribute Assignment](#4-phase-2-bayesian-network-attribute-assignment)
5. [Phase 3: Marginal Calibration](#5-phase-3-marginal-calibration)
6. [Phase 4: Continuous Income Sampling](#6-phase-4-continuous-income-sampling)
7. [Phase 5: Personality Layer (Big Five)](#7-phase-5-personality-layer-big-five)
8. [Phase 6: Attitude Derivation](#8-phase-6-attitude-derivation)
9. [Phase 7: Household Formation](#9-phase-7-household-formation)
10. [Phase 8: Privacy Protection (k-Anonymity)](#10-phase-8-privacy-protection-k-anonymity)
11. [Phase 9: Narrative Persona Grafting (NVIDIA Nemotron)](#11-phase-9-narrative-persona-grafting-nvidia-nemotron)
12. [Validation Framework](#12-validation-framework)
13. [Quality Gate](#13-quality-gate)
14. [Agent-to-Persona Prompt Engineering](#14-agent-to-persona-prompt-engineering)
15. [Proposed V3: NVIDIA 148K Base Architecture](#15-proposed-v3-nvidia-148k-base-architecture)
16. [Mathematical Guarantees Summary](#16-mathematical-guarantees-summary)
17. [References](#17-references)

---

## 1. Architecture Overview

Each synthetic agent is constructed through a **7-phase pipeline** that transforms aggregate census statistics into individual-level records with demographic, economic, psychological, and narrative attributes. The pipeline preserves joint distributions, conditional dependencies, and marginal constraints at every stage.

```
Census Marginals (GHS 2025)
        |
        v
[Phase 1] Deming-Stephan IPF on 4D Contingency Table
        |  age(21) x gender(2) x ethnicity(4) x area(28) = 4,704 cells
        v
[Phase 2] Bayesian Network (DAG-ordered conditional sampling)
        |  education | age
        |  income    | education, age
        |  housing   | income
        |  marital   | age, gender
        |  health    | age
        v
[Phase 3] Marginal Calibration (Devill-Sarndal post-hoc correction)
        |  Force education, housing aggregates to GHS 2025 targets
        v
[Phase 4] Continuous Income Sampling (Triangular within band)
        |
[Phase 5] Big Five Personality (Multivariate Normal + Cholesky)
        |
[Phase 6] Attitude Derivation (Linear models from Big Five + demographics)
        |
[Phase 7] Household Formation (9-phase constraint-driven + redistribution)
        |
[Phase 8] k-Anonymity Enforcement (k >= 5 on quasi-identifiers)
        |
[Phase 9] NVIDIA Persona Grafting (best-fit matching from 148K narratives)
        |
        v
    Final Agent Record (29+ attributes per agent)
```

**Code location**: `scripts/03_synthesize_v2_mathematical.py` orchestrates all phases.
**Core math library**: `engine/synthesis/math_core.py`

---

## 2. Data Sources & Statistical Authority

All marginal distributions and conditional probability tables are calibrated to official Singapore government statistics:

| Source | Publisher | Year | Used For |
|--------|-----------|------|----------|
| General Household Survey (GHS) 2025 | SingStat | Feb 2026 | Age, gender, ethnicity, education, housing, household size |
| Population Trends 2025 | SingStat | Sep 2025 | Age structure, sex ratio, marital status by age |
| Key Household Income Trends 2025 | SingStat | Feb 2026 | Income distribution by education and age |
| MOM Labour Force Survey 2025 | Ministry of Manpower | 2025 | Median income ($5,000 excl. employer CPF) |
| Population in Brief 2025 | NPTD/PMO | 2025 | Citizen/PR/non-resident breakdown |
| HDB Key Statistics 2024/25 | HDB | 2025 | Housing type distribution |
| National Health Survey 2020 | MOH | 2020 | Chronic disease prevalence by age |
| Schmitt et al. (2007) | Journal of Cross-Cultural Psychology | 2007 | SE Asian Big Five baseline |
| Soto et al. (2011) | Journal of Personality & Social Psychology | 2011 | Age trajectories of Big Five |
| NVIDIA Nemotron-Personas-Singapore | NVIDIA / HuggingFace | 2026 | 148K narrative personas (CC BY 4.0) |

**Key reference values (GHS 2025)**:

| Statistic | Value |
|-----------|-------|
| Total population | 6.11M (residents 4.20M) |
| Resident median age | 43.2 years |
| Sex ratio | 947 males per 1,000 females (M: 48.6%, F: 51.4%) |
| Ethnicity | Chinese 73.9%, Malay 13.5%, Indian 9.0%, Others 3.5% |
| Median monthly income (employed, excl. CPF) | $5,000 |
| HDB residents | 77.2% |
| Degree+ among 25+ residents | 37.3% |
| Mean household size | 3.06 persons |
| TFR | 1.1 |

---

## 3. Phase 1: Joint Demographic Distribution via IPF

### 3.1 Problem Statement

Given $K$ marginal constraints $\{m_k\}_{k=1}^{K}$ derived from census cross-tabulations, find a joint distribution $T^*$ over a 4-dimensional contingency table that satisfies all marginals simultaneously while staying as close as possible to a seed (prior) distribution $T^{(0)}$.

### 3.2 Table Dimensions

$$T \in \mathbb{R}^{21 \times 2 \times 4 \times 28}$$

| Axis | Dimension | Size | Labels |
|------|-----------|------|--------|
| 0 | Age group | 21 | 0-4, 5-9, ..., 95-99, 100 |
| 1 | Gender | 2 | M, F |
| 2 | Ethnicity | 4 | Chinese, Malay, Indian, Others |
| 3 | Planning area | 28 | Bedok, Tampines, ..., Others |

Total cells: $21 \times 2 \times 4 \times 28 = 4{,}704$

### 3.3 Seed Matrix (Maximum Entropy Prior)

We initialize with a uniform seed:

$$T^{(0)}_{ijkl} = 1 \quad \forall\, i, j, k, l$$

This corresponds to the **maximum entropy principle**: absent any prior knowledge of interaction effects, assume no interactions between dimensions. The IPF solution will then be the minimum-information-gain adjustment that satisfies all marginal constraints.

### 3.4 Marginal Constraints

Four marginal constraints are imposed:

**M1: Age x Gender (42 cells)**

$$\sum_{k,l} T^*_{ijkl} = N \cdot p^{\text{age}}_i \cdot p^{\text{gender}}_j \quad \forall\, i, j$$

where $p^{\text{age}}_i$ and $p^{\text{gender}}_j$ are the Census marginal proportions.

**M2: Ethnicity (4 cells)**

$$\sum_{i,j,l} T^*_{ijkl} = N \cdot p^{\text{eth}}_k \quad \forall\, k$$

**M3: Planning Area (28 cells)**

$$\sum_{i,j,k} T^*_{ijkl} = N \cdot p^{\text{area}}_l \quad \forall\, l$$

**M4: Age x Ethnicity (84 cells)**

$$\sum_{j,l} T^*_{ijkl} = N \cdot p^{\text{age-eth}}_{ik} \quad \forall\, i, k$$

This constraint captures the empirically observed age-ethnicity interaction: elderly population skews more Chinese (TFR historically lower), younger population has slightly higher Malay representation (TFR historically higher). The age-ethnicity interaction table is itself constructed by sub-IPF:

1. Start with outer product: $p^{\text{age-eth}}_{ik} = p^{\text{age}}_i \cdot p^{\text{eth}}_k$
2. Apply interaction adjustments:
   - Age 60+: Chinese factor $\times 1.05$, Malay factor $\times 0.90$
   - Age 0-19: Chinese factor $\times 0.97$, Malay factor $\times 1.10$
3. Iterate 50 rounds of row/column normalization to ensure consistency with both marginals.

### 3.5 IPF Algorithm (Deming-Stephan 1940)

**Update rule** for constraint $m$ over dimensions $D_m$:

$$T^{(t+1)}_{ij\ldots} = T^{(t)}_{ij\ldots} \cdot \frac{m_{D_m}}{\sum_{\bar{D}_m} T^{(t)}_{ij\ldots}}$$

where $\bar{D}_m$ denotes the dimensions not in $D_m$ (i.e., we sum over all other dimensions to get the current marginal, then scale to match the target).

**Convergence criterion**: $\max_m \max_{c \in D_m} \left| \frac{T^{(t)}_{m,c} - m_c}{m_c} \right| < \epsilon$

We use $\epsilon = 5 \times 10^{-4}$, $\text{max\_iter} = 500$.

**Theoretical guarantee** (Csiszar 1975): The IPF solution minimizes the I-projection:

$$T^* = \arg\min_{T \in \mathcal{C}} D_{\text{KL}}(T \| T^{(0)})$$

where $\mathcal{C}$ is the constraint set (all tables matching the specified marginals).

### 3.6 Controlled Rounding (Integerization)

The IPF output $T^*$ contains real-valued cell counts. We need integer counts summing to exactly $N = 20{,}000$.

**Algorithm: Truncate-Residual-Sample (TRS)**

1. Scale: $s_{ij} = T^*_{ij} \cdot \frac{N}{\sum T^*}$
2. Truncate: $\lfloor s_{ij} \rfloor$ for all cells
3. Compute residuals: $r_{ij} = s_{ij} - \lfloor s_{ij} \rfloor$
4. Deficit: $\delta = N - \sum \lfloor s_{ij} \rfloor$
5. Sample $\delta$ cells without replacement, probability proportional to $r_{ij}$
6. Round up the selected cells

**Mathematical property**: $\mathbb{E}[I_{ij}] = s_{ij}$ (unbiased at cell level).

### 3.7 Record Expansion

Each cell $(i, j, k, l)$ with integer count $c$ generates $c$ individual records. Within each age band, a specific age is sampled uniformly: for band "30-34", $\text{age} \sim \text{Uniform}\{30, 31, 32, 33, 34\}$.

**Code**: `step1_ipf_contingency_table()` in `scripts/03_synthesize_v2_mathematical.py`

---

## 4. Phase 2: Bayesian Network Attribute Assignment

### 4.1 DAG Structure

After Phase 1 establishes the 4 core demographics (age, gender, ethnicity, area), remaining attributes are sampled via a Bayesian Network with the following DAG:

```
           age_group
          /    |     \
         v     v      v
  education  marital  health
      |     status    status
      v
  income_band
      |
      v
  housing_type
```

Additional deterministic rules:
- `ns_status` = $f(\text{gender}, \text{residency}, \text{age})$ (deterministic)
- `residency_status` ~ Marginal (independent of DAG)
- `commute_mode` ~ Marginal (independent)
- `has_vehicle` ~ $\text{Bernoulli}(\sigma(-3.0 + 0.0003 \cdot \text{income}))$ (logistic)

### 4.2 Conditional Probability Tables (CPTs)

Each edge in the DAG is defined by a CPT: $P(\text{child} \mid \text{parents})$.

**Education | Age**: $P(\text{edu} \mid \text{age\_group})$

Source: GHS 2025 education attainment by age group (21 age groups x 7 education levels = 147 conditional probabilities). Key calibration: Degree+ among 25+ = 37.3%.

Example (age 30-34):

| Education Level | P |
|----------------|---|
| No_Formal | 0.01 |
| Primary | 0.03 |
| Secondary | 0.09 |
| Post_Secondary | 0.12 |
| Polytechnic | 0.15 |
| University | 0.45 |
| Postgraduate | 0.15 |

Children (0-14) have deterministic education (No_Formal for 0-4, Primary for 5-9, etc.).

**Income | Education, Age**: $P(\text{income\_band} \mid \text{edu}, \text{age\_group})$

Source: MOM Labour Force Survey 2025 + Key Household Income Trends 2025. 8 income bands x 7 education levels x 21 age groups (with many sharing a common CPT for efficiency). Calibrated to $5,000 median (excl. employer CPF).

**Housing | Income**: $P(\text{housing\_type} \mid \text{income\_band})$

Source: GHS 2025 dwelling type by household income decile. 6 housing types x 8 income bands = 48 conditional probabilities. Target aggregate: HDB 77.2%, Condo 17.9%, Landed 4.7%.

**Marital Status | Age, Gender**: $P(\text{marital} \mid \text{age\_group}, \text{gender})$

Source: Population Trends 2025 (marital status by age and sex). 4 marital statuses x 21 age groups x 2 genders = 168 conditional probabilities. Key constraint: ~60% married at age 30-34.

**Health Status | Age**: $P(\text{health} \mid \text{age\_group})$

Source: National Health Survey 2020 + MOH chronic disease data. 4 health states x 21 age groups. Chronic prevalence increases roughly exponentially with age.

### 4.3 Sampling Procedure

For each of the $N = 20{,}000$ agents, we sample in **topological order** of the DAG:

```
For agent i with known (age_group_i, gender_i):
    1. education_i     ~ P(edu | age_group_i)
    2. income_band_i   ~ P(income | education_i, age_group_i)
    3. housing_type_i  ~ P(housing | income_band_i)
    4. marital_i       ~ P(marital | age_group_i, gender_i)
    5. health_i        ~ P(health | age_group_i)
    6. residency_i     ~ P(residency)  [marginal, independent]
```

**Mathematical property**: This sampling procedure generates the joint distribution:

$$P(\text{age}, \text{gen}, \text{eth}, \text{area}, \text{edu}, \text{inc}, \text{hou}, \text{mar}, \text{hea}, \text{res}) = P(\text{age}, \text{gen}, \text{eth}, \text{area}) \cdot P(\text{edu} \mid \text{age}) \cdot P(\text{inc} \mid \text{edu}, \text{age}) \cdot P(\text{hou} \mid \text{inc}) \cdot P(\text{mar} \mid \text{age}, \text{gen}) \cdot P(\text{hea} \mid \text{age}) \cdot P(\text{res})$$

This factorization preserves conditional independence: e.g., $\text{housing} \perp\!\!\!\perp \text{age} \mid \text{income}$ (housing depends on age only through income).

**CPT validation**: Every CPT entry is verified to sum to 1: $\sum_v P(V = v \mid \text{parents}) = 1$. An assertion error is raised if $|\sum - 1| > 10^{-6}$.

**Code**: `step2_bayesian_network_attributes()` in `scripts/03_synthesize_v2_mathematical.py`
**CPT definitions**: `engine/synthesis/sg_distributions.py`

---

## 5. Phase 3: Marginal Calibration

### 5.1 Problem

CPT-based sampling correctly encodes $P(Y \mid X)$, but the realized marginal $P(Y)$ depends on the joint distribution of $X$. Due to finite-sample effects and interactions between multiple CPTs, the output marginals may drift from Census targets.

### 5.2 Method: Deville-Sarndal Post-Hoc Calibration

For each calibrated attribute, we:

1. Compute actual marginal distribution in the synthesized population
2. Identify surplus and deficit categories
3. Perform targeted swaps: for agents in surplus categories, re-sample their attribute value from the CPT conditional on their parents, with probability weighted toward deficit categories

This is repeated iteratively until the marginal matches the target to within $\pm 1/N$.

### 5.3 Calibrated Attributes

**Education (25+ population)**:

Target distribution (GHS 2025):

| Level | Target |
|-------|--------|
| No_Formal | 8% |
| Primary | 12% |
| Secondary | 15% |
| Post_Secondary | 10% |
| Polytechnic | 17% |
| University | 28% |
| Postgraduate | 10% |

**Housing (aggregate)**:

| Type | Target |
|------|--------|
| HDB (all subtypes) | 77.2% |
| Condo | 17.9% |
| Landed | 4.7% |

### 5.4 Mathematical Guarantee

After calibration, for every calibrated attribute $A$ with target distribution $\pi_A$:

$$\left| \hat{P}(A = a) - \pi_A(a) \right| \leq \frac{1}{N} \quad \forall\, a$$

where $\hat{P}$ is the empirical distribution in the synthetic population.

**Code**: `step2b_marginal_calibration()` in `scripts/03_synthesize_v2_mathematical.py`

---

## 6. Phase 4: Continuous Income Sampling

### 6.1 Problem

Income is sampled as a discrete band in Phase 2 (e.g., "5000-6999"). We need continuous values for realistic agent behavior.

### 6.2 Method: Triangular Distribution Within Band

For each agent with income band $[L, U]$ and education rank $r \in \{0, 1, \ldots, 6\}$:

$$\text{income}_i \sim \text{Triangular}(L, \text{mode}, U)$$

where:

$$\text{mode} = L + (U - L) \cdot \min(0.3 + 0.1r, \, 0.9)$$

**Rationale**: Higher education shifts the mode toward the upper end of the band, reflecting the earnings premium. The triangular distribution is the maximum entropy distribution given known bounds and mode.

For the "$15000+" band, $U$ is set to $30{,}000$ (empirical cap for top-coded income).

**Code**: `sample_income_in_band()` in `scripts/03_synthesize_v2_mathematical.py`

---

## 7. Phase 5: Personality Layer (Big Five)

### 7.1 Model

Each agent receives a Big Five personality profile: Openness (O), Conscientiousness (C), Extraversion (E), Agreeableness (A), Neuroticism (N), on a 1-5 scale.

### 7.2 Baseline Means (SE Asian Norms)

From Schmitt et al. (2007), SE Asian baseline:

| Trait | Mean | SD |
|-------|------|----|
| O | 3.45 | 0.55 |
| C | 3.30 | 0.58 |
| E | 3.20 | 0.60 |
| A | 3.55 | 0.52 |
| N | 2.85 | 0.62 |

### 7.3 Age Adjustments (Soto et al. 2011)

Per-decade deltas from the 20-29 baseline:

| Decade | O | C | E | A | N |
|--------|---|---|---|---|---|
| 20s (baseline) | 0 | 0 | 0 | 0 | 0 |
| 30s | -0.05 | +0.10 | -0.05 | +0.08 | -0.08 |
| 40s | -0.08 | +0.15 | -0.08 | +0.12 | -0.12 |
| 50s | -0.10 | +0.18 | -0.12 | +0.15 | -0.15 |
| 60s | -0.12 | +0.20 | -0.15 | +0.18 | -0.18 |
| 70+ | -0.15 | +0.18 | -0.18 | +0.20 | -0.20 |

**Interpretation**: With age, people become more conscientious, more agreeable, less neurotic, and slightly less open and extraverted. This is the "maturity principle" (Roberts et al. 2006).

### 7.4 Gender Adjustments (McCrae & Costa 2003)

| Gender | O | C | E | A | N |
|--------|---|---|---|---|---|
| M | +0.05 | 0 | -0.05 | -0.10 | -0.15 |
| F | -0.05 | 0 | +0.05 | +0.10 | +0.15 |

### 7.5 Sampling: Multivariate Normal with Cholesky Decomposition

The adjusted mean vector for agent $i$:

$$\boldsymbol{\mu}_i = \boldsymbol{\mu}_{\text{baseline}} + \boldsymbol{\delta}_{\text{age}}(\text{decade}_i) + \boldsymbol{\delta}_{\text{gender}}(\text{gender}_i)$$

Inter-trait correlation matrix $\mathbf{R}$ (from meta-analytic estimates):

$$\mathbf{R} = \begin{pmatrix}
1.00 & 0.10 & 0.25 & 0.10 & -0.15 \\
0.10 & 1.00 & 0.15 & 0.20 & -0.30 \\
0.25 & 0.15 & 1.00 & 0.15 & -0.25 \\
0.10 & 0.20 & 0.15 & 1.00 & -0.35 \\
-0.15 & -0.30 & -0.25 & -0.35 & 1.00
\end{pmatrix}$$

Compute Cholesky factor: $\mathbf{R} = \mathbf{L} \mathbf{L}^T$

Sampling:

$$\mathbf{z}_i \sim \mathcal{N}(\mathbf{0}, \mathbf{I}_5)$$

$$\mathbf{b}_i = \boldsymbol{\mu}_i + \boldsymbol{\sigma} \odot (\mathbf{L} \mathbf{z}_i)$$

$$\text{big5}_i = \text{clip}(\mathbf{b}_i, 1.0, 5.0)$$

where $\boldsymbol{\sigma}$ is the vector of per-trait standard deviations and $\odot$ denotes element-wise multiplication.

**Mathematical properties**:
- $\text{Corr}(\text{big5}_{i,k}, \text{big5}_{i,l}) \approx R_{kl}$ (by construction)
- $\mathbb{E}[\text{big5}_{i,k}] \approx \mu_{i,k}$ (adjusted for clipping bias near boundaries)
- Inter-individual independence: $\text{big5}_i \perp\!\!\!\perp \text{big5}_j$ for $i \neq j$

**Validation**: We verify:
- Population mean of each trait within $\pm 0.15$ of the SE Asian baseline
- Realized inter-trait correlations match $\mathbf{R}$ to within sampling error ($\pm 0.03$ for $N = 20{,}000$)

**Code**: `engine/synthesis/personality_init.py`

---

## 8. Phase 6: Attitude Derivation

### 8.1 Model

Four attitude dimensions are derived as linear combinations of Big Five traits plus demographic covariates, with additive Gaussian noise:

**Risk Appetite** (Dohmen et al. 2011):

$$\text{risk}_i = 0.3 \cdot O_i - 0.2 \cdot N_i - 0.15 \cdot C_i + 0.15 \cdot \alpha_{\text{age}} + 2.5 + \varepsilon_i$$

where $\alpha_{\text{age}} = -0.01 \cdot (\text{age}_i - 30)$ and $\varepsilon_i \sim \mathcal{N}(0, 0.3^2)$.

**Political Leaning** (Tilley & Evans 2014):

$$\text{pol}_i = 0.35 \cdot O_i - 0.15 \cdot C_i - 0.008 \cdot (\text{age}_i - 25) + 1.8 + \varepsilon_i$$

where $\varepsilon_i \sim \mathcal{N}(0, 0.35^2)$.

**Social Trust**:

$$\text{trust}_i = 0.25 \cdot A_i + 0.15 \cdot E_i - 0.15 \cdot N_i + 2.2 + \varepsilon_i$$

where $\varepsilon_i \sim \mathcal{N}(0, 0.3^2)$.

**Religious Devotion**:

$$\text{relig}_i = 0.15 \cdot C_i + 0.10 \cdot A_i + \beta_{\text{eth}} + 0.005 \cdot (\text{age}_i - 25) + 2.0 + \varepsilon_i$$

where $\beta_{\text{eth}} \in \{0.0\text{ (Chinese)}, 0.5\text{ (Malay)}, 0.3\text{ (Indian)}, 0.1\text{ (Others)}\}$ and $\varepsilon_i \sim \mathcal{N}(0, 0.4^2)$.

All attitudes are clipped to $[1, 5]$.

**Code**: `engine/synthesis/personality_init.py` (class `AttitudeInitializer`)

---

## 9. Phase 7: Household Formation

### 9.1 Target Distribution (GHS 2025)

| Household Size | Target % |
|----------------|----------|
| 1-person | 15.3% |
| 2-person | 18.8% |
| 3-person | 18.0% |
| 4-person | 22.3% |
| 5-person | 15.5% |
| 6-person | 6.5% |
| 7-person | 2.6% |
| 8+-person | 1.0% |

Mean: 3.16 persons/household.

### 9.2 Formation Algorithm (9 Phases + Redistribution)

**Phase 1: Married Couples** -- Pair married males with married females. These couples form the anchor of most households.

**Phase 2: Minor Children (0-17)** -- Attach to parent couples. Age compatibility constraint: parent must be 22-45 years older than child. Number of children per couple follows a calibrated distribution:
- Head age < 32: P(0,1,2) = (0.50, 0.38, 0.12)
- Head age 32-41: P(0,1,2,3) = (0.25, 0.38, 0.22, 0.15)
- Head age 42-54: P(0,1,2,3) = (0.30, 0.32, 0.22, 0.16)
- Head age 55+: 0 children (already adults)

**Phase 3: Unmarried Adults (18-34)** -- Singapore cultural norm: unmarried adults overwhelmingly live with parents. Probability of living with parents:
- Age 18-25: 85%
- Age 26-30: 70%
- Age 31-34: 50%

Age compatibility: parent 22-40 years older.

**Phase 4: Elderly Parents** -- ~40% of unassigned elderly (65+) join adult children's households. Age compatibility: parent 18+ years older than head.

**Phase 5: Foreign Domestic Workers (FDWs)** -- Placed with employer families (income >= $5,000 and has children or elderly). ~25% acceptance rate.

**Phase 6: WP/SP Workers** -- Grouped into shared accommodation (2-6 per unit).

**Phase 7-8: Remaining children and elderly** -- Placed with compatible households or form elderly pairs.

**Phase 9: Singles** -- Remaining unassigned adults form 1-person households.

### 9.3 Constraint Redistribution (Phase 10)

After organic formation, the household size distribution may deviate from Census targets. A multi-strategy redistribution algorithm iterates up to 10 rounds:

**Strategy A**: Merge surplus 1-person households into 2/3/4-person groups.

**Strategy B**: Expand small surplus households (e.g., 4p) by attaching surplus 1-person singles to create 5p/6p.

**Strategy C**: Split surplus large households (6+) by detaching adult non-core members.

**Strategy D**: Merge pairs of surplus households (e.g., 4p + 2p -> 6p if 6p has deficit).

**Strategy E**: Split 4p -> 3p + 1p, then reattach freed singles to other 4p -> 5p.

**Convergence metric**: $\text{SRMSE} < 0.05$ vs Census target.

**Code**: `engine/synthesis/household_builder.py`

---

## 10. Phase 8: Privacy Protection (k-Anonymity)

### 10.1 Definition

A dataset satisfies $k$-anonymity if every combination of quasi-identifiers appears in at least $k$ records (Sweeney 2002).

### 10.2 Quasi-Identifiers

Three sets are checked:

1. (age_group, gender, planning_area) -- geographic re-identification risk
2. (age_group, gender, ethnicity) -- demographic re-identification risk
3. (planning_area, housing_type) -- spatial re-identification risk

### 10.3 Enforcement

We enforce $k \geq 5$. Violations are resolved by generalizing age bands or merging small planning areas into "Others" bucket.

### 10.4 Verification

Post-synthesis check: for each quasi-identifier set, compute $\min_g |g|$ where $g$ ranges over all equivalence classes. The synthesis is flagged if any $\min_g |g| < 5$.

**Code**: `enforce_k_anonymity()` in `engine/synthesis/math_core.py`

---

## 11. Phase 9: Narrative Persona Grafting (NVIDIA Nemotron)

### 11.1 Source Dataset

NVIDIA Nemotron-Personas-Singapore: 148,000 synthetic persons with 21 fields, generated via:
1. Probabilistic Graphical Model (PGM) on Census marginals (age, gender, education, marital_status, planning_area)
2. GPT-OSS-120B narrative generation: 6 persona dimensions per record

### 11.2 Narrative Fields

| Field | Description |
|-------|-------------|
| `persona` | Comprehensive personality narrative |
| `professional_persona` | Career, skills, work attitudes |
| `sports_persona` | Exercise preferences, fitness habits |
| `arts_persona` | Cultural and artistic interests |
| `travel_persona` | Travel style and preferences |
| `culinary_persona` | Food preferences, cooking culture |
| `hobbies_and_interests` | General leisure activities |
| `career_goals_and_ambitions` | Professional aspirations |
| `cultural_background` | Cultural identity and practices |
| `occupation` | Specific job title |
| `industry` | Industry sector |

### 11.3 Matching Algorithm

For each of our agents, find the best-fit NVIDIA persona:

**Step 1: Key Lookup** -- Exact match on (planning_area, gender, education_level). Education is mapped via:

| Our Label | NVIDIA Label |
|-----------|-------------|
| No_Formal | No Qualification |
| Primary | Primary |
| Secondary | Secondary |
| Post_Secondary | Post Secondary (Non-Tertiary) |
| Polytechnic | Polytechnic |
| University | University |
| Postgraduate | University |

**Step 2: Fallback Hierarchy**
- Fallback 1: Relax area (any area, same gender + education)
- Fallback 2: Relax education (same gender only)
- Fallback 3: Any persona (last resort)

**Step 3: Scoring** -- Among candidates, compute a combined score:

$$\text{score}_c = |\text{age}_c - \text{age}_i| - 2 \cdot \mathbf{1}[\text{marital}_c = \text{marital}_i] - 3 \cdot \mathbf{1}[c \notin \text{used}]$$

Lower is better. The unused bonus maximizes diversity (prevents many agents from sharing the same persona).

**Step 4: Selection** -- Pick randomly from top-5 lowest-scoring candidates.

**Code**: `scripts/12_merge_nvidia_personas.py`

---

## 12. Validation Framework

### 12.1 Metrics

| Metric | Formula | Quality Thresholds |
|--------|---------|-------------------|
| **SRMSE** | $\frac{\sqrt{\frac{1}{K}\sum_k (O_k - E_k)^2}}{\bar{E}}$ | < 0.05 Excellent, < 0.10 Good, < 0.20 Acceptable |
| **Chi-Square GoF** | $\sum_k \frac{(O_k - E_k)^2}{E_k}$ | $p > 0.05$ (not significantly different) |
| **KL Divergence** | $\sum_k p_k \ln \frac{p_k}{q_k}$ | < 0.01 Excellent, < 0.05 Good |
| **Hellinger Distance** | $\frac{1}{\sqrt{2}} \sqrt{\sum_k (\sqrt{p_k} - \sqrt{q_k})^2}$ | < 0.05 Excellent, < 0.15 Good |
| **Cramer's V** | $\sqrt{\frac{\chi^2}{n \cdot \min(r-1, c-1)}}$ | 0: no association, 1: perfect |
| **Pearson/Spearman r** | Standard correlation | Sign and magnitude check |

### 12.2 Tests Performed

**Marginal distribution tests** (5 variables):
- Age distribution vs Census (21 age groups)
- Gender distribution vs Census (2 categories)
- Ethnicity distribution vs Census (4 categories)
- Planning area distribution vs Census (28 areas)
- Education distribution vs GHS 2025 (7 levels, 25+ population only)

**Joint distribution tests** (5 pairs):
- age_group x gender (expected: weak, V < 0.1)
- age_group x education (expected: strong, V > 0.3)
- education x housing (expected: moderate, V > 0.1)
- ethnicity x planning_area (expected: weak)
- gender x marital_status (expected: weak)

**Correlation structure** (6 pairs):
- age vs income (expected: inverted-U, weak positive)
- O vs E (expected: positive, r ~ 0.25)
- C vs N (expected: negative, r ~ -0.30)
- A vs N (expected: negative, r ~ -0.35)
- risk_appetite vs O (expected: positive)
- social_trust vs A (expected: positive)

**Aggregate statistics** (4 checks):
- Median age vs 43.2 (Census)
- Median income (employed) vs $5,000 (MOM)
- Married rate at 30-34 vs 60% (Census)
- Mean household size vs 3.06 (GHS)

**Big Five validation** (5 traits):
- Each trait mean within +/- 0.15 of SE Asian baseline (Schmitt 2007)
- Inter-trait correlation matrix matches meta-analytic estimates

**Code**: `scripts/04_validate_population.py`

---

## 13. Quality Gate

### 13.1 Hard Gates (must pass, block output)

| Gate | Metric | Threshold |
|------|--------|-----------|
| Gender distribution | SRMSE | < 0.10 |
| Ethnicity distribution | SRMSE | < 0.10 |
| Median age | Relative deviation | < 10% |
| Married at 30-34 | Relative deviation | < 10% |

### 13.2 Soft Gates (warning only)

| Gate | Metric | Threshold |
|------|--------|-----------|
| Household size distribution | SRMSE | < 0.20 |
| k-Anonymity | min_group_size | >= 5 |
| Housing aggregate (HDB/Condo/Landed) | SRMSE | < 0.20 |
| Education Degree+ (25+) | Relative deviation | < 20% |
| Median income (employed) | Relative deviation | < 20% |

### 13.3 Gate Logic

$$\text{PASS} = \bigwedge_{g \in \text{Hard}} g.\text{passed}$$

A synthesis is **REJECTED** and must be re-run if any hard gate fails.

**Code**: `engine/synthesis/synthesis_gate.py`

---

## 14. Agent-to-Persona Prompt Engineering

### 14.1 Current Persona Template (V2)

When an agent participates in a survey, its attributes are rendered into a persona prompt:

```
You are a {age}-year-old {gender} {ethnicity} resident of Singapore.
You live in {planning_area}, in a {housing_type} flat.
Education: {education_level}, currently {income_desc}.
Marital status: {marital_status}. Health: {health_status}.
Personality: O={big5_o}, C={big5_c}, E={big5_e}, A={big5_a}, N={big5_n}.
Risk appetite: {risk_appetite}/5.
```

### 14.2 Proposed V3 Enriched Persona Template

After NVIDIA persona grafting, the prompt gains narrative depth:

```
You are a {age}-year-old {gender} {ethnicity} resident of Singapore.
You live in {planning_area}, in a {housing_type} flat.
Education: {education_level}, currently {income_desc}.
Occupation: {occupation} in {industry}.

PERSONALITY: O={big5_o}, C={big5_c}, E={big5_e}, A={big5_a}, N={big5_n}.

ABOUT YOU: {persona}
CAREER: {professional_persona}
CULTURAL BACKGROUND: {cultural_background}
HOBBIES: {hobbies_and_interests}
```

Context-dependent fields (sports_persona, travel_persona, culinary_persona, arts_persona) are injected only when relevant to the survey question.

### 14.3 Quality Scoring

Each agent response is scored by NVIDIA Llama-3.1-Nemotron-70B-Reward:

$$\text{score} \in (-\infty, 0], \quad \text{higher} = \text{better}$$

| Range | Quality |
|-------|---------|
| > -5 | High quality |
| -5 to -15 | Acceptable |
| < -15 | Low quality |

**Code**: `scripts/api_server.py` (functions `agent_to_persona()`, `score_response_quality()`)

---

## 15. Proposed V3: NVIDIA 148K Base Architecture

### 15.1 Rationale

Instead of our 20K as base + grafting NVIDIA narratives, flip the architecture:

- **Base**: NVIDIA 148K (rich narratives, occupation, industry already present)
- **Augment**: Our statistical methods to add income, housing, ethnicity, residency, Big Five

### 15.2 Advantages

1. **7x sample size**: 148K agents, stronger statistical power per demographic cell
2. **Narrative irreversibility**: LLM-generated narratives cannot be algorithmically computed; statistical dimensions can
3. **Occupation/industry included**: No additional generation needed
4. **6 persona dimensions**: Selective injection by survey topic

### 15.3 Augmentation Pipeline

For each of the 148K NVIDIA records with known (age, gender, education, marital_status, planning_area):

| Step | Attribute | Method | Source |
|------|-----------|--------|--------|
| 1 | ethnicity | Sample from $P(\text{eth} \mid \text{planning\_area})$ | Census area-level ethnic composition |
| 2 | monthly_income | Sample from $P(\text{inc} \mid \text{edu}, \text{age})$ via CPT + Triangular | GHS 2025 |
| 3 | housing_type | Sample from $P(\text{hou} \mid \text{inc})$ via CPT | GHS 2025 |
| 4 | residency_status | Sample from $P(\text{res} \mid \text{eth}, \text{age})$ | Population in Brief |
| 5 | Big Five | $\mathcal{N}(\boldsymbol{\mu}(\text{age}, \text{gender}), \boldsymbol{\Sigma})$ via Cholesky | Schmitt 2007 |
| 6 | Attitudes | Linear model from Big Five + demographics | Dohmen 2011 |
| 7 | Household | Constraint-driven formation (same algorithm) | GHS 2025 |
| 8 | Ethnicity validation | Cross-check `cultural_background` text vs assigned ethnicity | Heuristic NLP |

**Step 8 detail**: After assigning ethnicity from area-level distribution, validate against the `cultural_background` narrative. Flag contradictions (e.g., assigned "Malay" but `cultural_background` describes Chinese New Year traditions). Flagged records are re-assigned to the ethnicity implied by the narrative.

### 15.4 Post-hoc Calibration

Same marginal calibration framework (Section 5) applied to the 148K population to ensure all Census targets are met.

### 15.5 Validation

Same validation framework (Section 12) and quality gate (Section 13) applied to the 148K population.

---

## 16. Mathematical Guarantees Summary

| Property | Guarantee | Mechanism |
|----------|-----------|-----------|
| Marginal fidelity | Each marginal matches Census to $\leq 1/N$ | IPF + post-hoc calibration |
| Joint distribution | I-projection: minimum KL divergence from maximum entropy prior | Deming-Stephan IPF (Csiszar 1975) |
| Conditional independence | DAG structure preserved: $X \perp\!\!\!\perp Y \mid Z$ | Bayesian Network sampling |
| Controlled rounding | $\mathbb{E}[I_{ij}] = T^*_{ij}$ (cell-level unbiased) | TRS algorithm |
| Personality correlations | $\text{Corr}(T_k, T_l) \approx R_{kl}$ | Cholesky decomposition of $\mathbf{R}$ |
| Privacy | $k \geq 5$ for all quasi-identifier groups | k-Anonymity enforcement |
| Household size | SRMSE < 0.05 vs GHS 2025 | 10-round constraint redistribution |
| Reproducibility | Deterministic given seed | $\text{rng} = \text{default\_rng}(42)$ throughout |

---

## 17. References

1. Deming, W.E. & Stephan, F.F. (1940). "On a least squares adjustment of a sampled frequency table when the expected marginal totals are known." *Annals of Mathematical Statistics*, 11(4), 427-444.

2. Csiszar, I. (1975). "I-divergence geometry of probability distributions and minimization problems." *Annals of Probability*, 3(1), 146-158.

3. Fienberg, S.E. (1970). "An iterative procedure for estimation in contingency tables." *Annals of Mathematical Statistics*, 41(3), 907-917.

4. Muller, K. & Axhausen, K.W. (2011). "Population synthesis for microsimulation: State of the art." *Transportation Research Record*, 2225(1), 18-25.

5. Beckman, R.J., Baggerly, K.A. & McKay, M.D. (1996). "Creating synthetic baseline populations." *Transportation Research Part A*, 30(6), 415-429.

6. Sklar, A. (1959). "Fonctions de repartition a n dimensions et leurs marges." *Publications de l'Institut de Statistique de l'Universite de Paris*, 8, 229-231.

7. Sweeney, L. (2002). "k-Anonymity: A model for protecting privacy." *International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems*, 10(5), 557-570.

8. Voas, D. & Williamson, P. (2001). "Evaluating goodness-of-fit measures for synthetic microdata." *Geographical & Environmental Modelling*, 5(2), 177-200.

9. Deville, J.C. & Sarndal, C.E. (1992). "Calibration estimators in survey sampling." *Journal of the American Statistical Association*, 87(418), 376-382.

10. Schmitt, D.P. et al. (2007). "The geographic distribution of Big Five personality traits." *Journal of Cross-Cultural Psychology*, 38(2), 173-212.

11. Soto, C.J. et al. (2011). "Age differences in personality traits from 10 to 65." *Journal of Personality and Social Psychology*, 100(2), 330-348.

12. McCrae, R.R. & Costa, P.T. (2003). *Personality in Adulthood: A Five-Factor Theory Perspective.* Guilford Press.

13. Roberts, B.W. et al. (2006). "Patterns of mean-level change in personality traits across the life course." *Psychological Bulletin*, 132(1), 1-25.

14. Dohmen, T. et al. (2011). "Individual risk attitudes: Measurement, determinants, and behavioral consequences." *Journal of the European Economic Association*, 9(3), 522-550.

15. Tilley, J. & Evans, G. (2014). "Ageing and generational effects on vote choice." *Electoral Studies*, 33, 19-27.

16. NVIDIA (2026). "Nemotron-Personas-Singapore: 148K Synthetic Digital Twins." HuggingFace Dataset, CC BY 4.0.
