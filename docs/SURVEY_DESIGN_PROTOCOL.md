# Research-Driven Survey Design Protocol v2.0

**Authors**: Sophie (Survey Methodologist) + Dr. Chen Wei (Market Research Expert)
**Date**: 2026-03-07
**Architecture**: Universal Core + Vertical Modules

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│            UNIVERSAL CORE PROTOCOL              │
│  (8 phases, applies to ALL simulation topics)   │
├─────────────────────────────────────────────────┤
│                                                 │
│  Phase 0: VERTICAL DETECTION                    │
│     ↓ identifies domain → loads vertical module │
│  Phase 1: Deep Event Research                   │
│  Phase 2: Structural Analysis (6 trap types)    │
│  Phase 3: Question Design                       │
│  Phase 4: Option Design                         │
│  Phase 5: Context Injection                     │
│  Phase 6: Sampling Strategy                     │
│  Phase 7: Pre-flight Validation                 │
│  Phase 8: Client Collaboration                  │
│                                                 │
├──────────┬──────────┬──────────┬────────────────┤
│ ELECTION │ ECONOMIC │ CONSUMER │ POLICY/SOCIAL  │
│ vertical │ vertical │ vertical │ vertical       │
│          │          │          │                │
│ Partial  │ Index    │ Purchase │ Sensitivity    │
│ contest  │ compos.  │ funnel   │ framing        │
│ Seat map │ Basket   │ Price    │ Moral loading  │
│ Swing    │ weights  │ anchors  │ Social desir.  │
│ analysis │ Lag      │ Channel  │ Age/religion   │
│          │ struct.  │ mix      │ cohort gaps    │
└──────────┴──────────┴──────────┴────────────────┘
```

---

## Phase 0: Vertical Detection

Before starting any research, classify the event into a vertical. This determines which specialized module supplements the universal protocol.

### Detection Rules

| Signal | Vertical | Module Loaded |
|--------|----------|---------------|
| Election, vote, candidate, party, constituency, ballot | **ELECTION** | `V-ELEC` |
| CPI, GDP, COE, interest rate, inflation, employment, MAS | **ECONOMIC INDICATOR** | `V-ECON` |
| Buy, subscribe, apply, switch, adopt, usage, BTO, insurance | **CONSUMER BEHAVIOR** | `V-CONS` |
| Support, oppose, attitude, opinion, 377A, death penalty, NS | **POLICY / SOCIAL** | `V-POLI` |
| Multiple signals or unclear | **HYBRID** | Load all matching modules |

### What a Vertical Module Provides

Each vertical module adds domain-specific:
- **Structural traps** (Phase 2 additions)
- **Question templates** (Phase 3 additions)
- **Context injection requirements** (Phase 5 additions)
- **Sampling rules** (Phase 6 additions)
- **Validation benchmarks** (Phase 7 additions)

The universal core always runs. Vertical modules add to it, never replace it.

---

# PART I: UNIVERSAL CORE PROTOCOL

## Phase 1: Deep Event Research

**Applies to**: ALL verticals

Before designing any question, become a domain specialist on the event mechanics.

### 1.1 — Assemble Event Dossier

Collect primary sources on the event's mechanics (not opinions about outcomes):
- Official rules, regulations, methodology
- Historical precedent (past 3-5 instances)
- Institutional constraints
- Participant roster (who is actually involved?)

### 1.2 — 5 Universal Structural Questions

| # | Question | Must Answer |
|---|----------|-------------|
| 1 | **What is the unit of outcome?** | The smallest indivisible unit where the result is determined |
| 2 | **Who are the actual participants at each unit?** | Which actors/options exist at each unit? |
| 3 | **What is the coverage/participation rate?** | What fraction of the total space does each actor cover? |
| 4 | **How does unit-level aggregate to headline?** | The exact formula from unit → reported number |
| 5 | **What media framing might mislead an LLM?** | Common reporting that conflates unit-level with aggregate |

### 1.3 — Map Outcome Space

- What are ALL possible outcomes? (define precisely)
- What mathematical constraints exist? (sums to 100%? bounded?)
- What is the natural unit of prediction?

### Checklist:
- [ ] Event dossier with 3+ primary sources on mechanics
- [ ] All 5 structural questions answered with data
- [ ] Outcome space defined with units and constraints
- [ ] At least one structural trap identified
- [ ] Historical base rates collected
- [ ] **Vertical detected**: _______ → Module loaded

---

## Phase 2: Structural Analysis — Universal Trap Taxonomy

**Applies to**: ALL verticals (each vertical adds domain-specific traps)

### 6 Universal Trap Types

| Trap | Name | Description | Detection Question |
|------|------|-------------|-------------------|
| A | **Aggregation Mismatch** | Headline aggregates heterogeneous sub-units | "If I told an LLM the headline number, would it know how it was constructed?" |
| B | **Participation Asymmetry** | Different actors in different subsets | "Is every option available to every respondent/unit?" |
| C | **Conditional vs Unconditional** | Reported number is conditional on something | "Does media report conditional or unconditional numbers?" |
| D | **Baseline Shift** | Structure changed from last comparable event | "Can I directly compare this event's numbers to the last one?" |
| E | **Selection Bias in Sources** | Available data over-represents certain outcomes | "What information is MISSING from sources the LLM would see?" |
| F | **Multi-Level Outcome** | Outcome determined at multiple levels | "Does the question ask about the right level?" |

### Decomposition Worksheet (one per trap found)

```
STRUCTURAL FEATURE: [Name]
Event:            [e.g., GE2025 / COE Mar 2026 / CPI Feb 2026]
Feature:          [e.g., Partial contestation / Category independence]
Trap type(s):     [A, B, C — often multiple]
Impact if ignored: [Quantified: e.g., +35pp overestimate]
Mitigation:        [Specific action to prevent this error]
```

### Checklist:
- [ ] All 6 universal traps evaluated
- [ ] Vertical-specific traps evaluated (from loaded module)
- [ ] Each found trap has decomposition worksheet
- [ ] Quantified bias estimate for each
- [ ] Mitigation strategy drafted
- [ ] Sign-off from Sophie + Dr. Chen

---

## Phase 3: Question Design

**Core Principle**: The question must mirror the actual choice situation of the real person being simulated.

### 3.1 — Design Template

```
QUESTION DESIGN DOCUMENT
═══════════════════════════════════════

Event:         [name]
Target metric: [what client wants to predict]
Natural unit:  [smallest indivisible unit]

WRONG QUESTION: [generic/national-level]
→ Fails because: [specific structural reason]

RIGHT QUESTION: [unit-level, situation-specific]
→ Works because: [matches real decision context]

AGGREGATION FORMULA:
[Exact formula: headline = f(unit-level results)]
```

### 3.2 — 5-Point Calibration Check

| # | Criterion | Test |
|---|-----------|------|
| 1 | **Specificity** | Does it specify the exact choice situation? |
| 2 | **Option Completeness** | Do options exactly match what's available in reality? |
| 3 | **Temporal Anchoring** | Is the time context specified? |
| 4 | **Information Parity** | Does agent have same info as real person? |
| 5 | **Aggregation Transparency** | Is the aggregation formula written and validated? |

### Checklist:
- [ ] Question design doc with wrong/right comparison
- [ ] All 5 calibration criteria passed
- [ ] Aggregation formula verified against official methodology
- [ ] Pilot tested on 5-10 agents
- [ ] Domain expert reviewed

---

## Phase 4: Option Design

### 5 Universal Rules

1. **Exhaustive & mutually exclusive** at the unit level
2. **Real labels** — use same names the real person encounters
3. **Include "no action"** where applicable (not vote, not buy, defer)
4. **Anchor numerics** — provide reference points, don't ask open-ended
5. **No signaling** — options don't hint at "correct" answer

### Checklist:
- [ ] Option sets for every distinct unit
- [ ] Cross-checked against official source
- [ ] "No action" option included where applicable

---

## Phase 5: Context Injection

### 4 Universal Sections

**A. Event Structure** — Mandatory structural facts the LLM must know
**B. Common Misconceptions** — Proactive "do NOT confuse X with Y"
**C. Decision-Relevant Information** — What a real person would know
**D. Constraints** — Mathematical/logical bounds

### 5 Universal Rules

1. State structural decomposition explicitly
2. Correct likely conflation errors proactively
3. Anchor to official data, not media narratives
4. Match information horizon of the real person (no data leakage)
5. Separate facts from framing

### Checklist:
- [ ] All 4 sections completed
- [ ] 2+ misconception corrections included
- [ ] Domain expert verified factual accuracy
- [ ] No outcome data leaked
- [ ] Tested on 2-3 sample agents for comprehension

---

## Phase 6: Sampling Strategy

### Universal Principle

> **Strata must match the EVENT'S structure, not generic demographics.**

- Primary stratum = natural unit of the event
- Secondary strata = demographics relevant to this specific decision
- Minimum 30 agents per stratum
- Every response weighted to population
- Non-participating units identified and handled

### Checklist:
- [ ] Strata match event structure (not generic age×gender)
- [ ] ≥30 per stratum
- [ ] Weighting formula defined and sums to 1.0
- [ ] Non-participating units identified and handled

---

## Phase 7: Pre-flight Validation

### 5 Universal Checks

| # | Check | Kill If |
|---|-------|---------|
| 1 | **Boundary Test** — extreme personas give sane results | Die-hard supporter votes wrong party |
| 2 | **Structural Consistency** — aggregated estimates in plausible range | Outside historical bounds |
| 3 | **Context Comprehension** — agents correctly describe their situation | Mention options not available to them |
| 4 | **Sensitivity Test** — with vs without context injection | Delta < 5pp (context not working) |
| 5 | **Historical Backtest** — protocol on known past event | MAE > target threshold |

### Kill Criteria — stop and redesign if:
- Any structural consistency check fails
- >20% agents show data leakage or context misunderstanding
- Historical backtest exceeds target MAE

### Checklist:
- [ ] All 5 checks passed
- [ ] No kill criteria triggered
- [ ] Pre-flight results documented
- [ ] Go/no-go decision recorded

---

## Phase 8: Client Collaboration

### Kickoff
1. Objective alignment — what to predict, at what level?
2. Precision requirements — acceptable MAE?
3. Structural briefing — share Phase 1-2 findings
4. Timeline and deliverables

### Design Review
- Share question design, context, sampling plan
- Client sign-off: "Is this the right question?"

### Delivery
1. Point estimates + confidence intervals
2. Structural decomposition (unit-level, not just headline)
3. Methodology transparency
4. Known limitations
5. Sensitivity analysis

---

# PART II: VERTICAL MODULES

---

## V-ELEC: Election Vertical

**Triggered by**: election, vote, candidate, party, constituency, ballot, GRC, SMC

### Additional Structural Traps

| Trap | Name | Description |
|------|------|-------------|
| E1 | **Partial Contestation** | Parties contest only a fraction of seats. National share ≠ contested-seat share. |
| E2 | **Walkover Seats** | Uncontested seats = 100% for winner, 0% for others. Must be hardcoded, not simulated. |
| E3 | **GRC/SMC Size Asymmetry** | GRCs have 4-5 seats, SMCs have 1. National share must weight by electorate, not by ward count. |
| E4 | **Multi-Cornered Fights** | 3+ parties in one ward split opposition vote. Must model per-ward, not nationally. |
| E5 | **"Shy Tory" / Silent Majority** | Incumbent supporters underrepresented online. LLM training data biased toward vocal opposition. |
| E6 | **Swing vs Level** | A 5pp swing looks different at 40% vs 70% baseline. Must anchor to last-election baseline per ward. |

### Question Template

```
You live in [CONSTITUENCY_NAME].
The candidates running in your constituency are:
  - [Name A] from [Party A] (incumbent / challenger)
  - [Name B] from [Party B]
  [- [Name C] from [Party C] — if multi-cornered]
No other parties are running here.

In the last election (GE2020), Party A won this seat with [X]%.

On polling day, which candidate would you vote for?
```

### Context Injection (mandatory additions)

```
ELECTION STRUCTURE:
This election has [N] parliamentary seats across [X] GRCs and [Y] SMCs.
[Party] contests [Z] of [N] seats ([P]% coverage).
IMPORTANT: A party's national vote share is NOT the same as its
contested-seat vote share. If a party gets 50% in 26/97 seats,
its national share is approximately 50% × 26/97 ≈ 13%.

NOTE: Media coverage reports contested-seat figures (e.g., "WP
at 50%"). These are NOT national vote share figures.
```

### Sampling Rules

- **Primary stratum**: Constituency (not age/gender)
- Each contested constituency: ≥30 agents
- Walkover constituencies: hardcode result, don't simulate
- Within each constituency: stratify by age × housing × ethnicity matching constituency demographics
- **Aggregation**: National share = Σ(constituency share × constituency electorate) / total electorate

### Validation Benchmarks

- PAP national share plausible range: [55%, 75%] based on 1965-2025 history
- No opposition party's national share > its seat coverage × 100%
- Sum of all parties = 100% in each constituency
- Historical backtest target: MAE ≤ 3pp

---

## V-ECON: Economic Indicator Vertical

**Triggered by**: CPI, GDP, COE, interest rate, inflation, employment, wages, MAS, SingStat

### Additional Structural Traps

| Trap | Name | Description |
|------|------|-------------|
| C1 | **Index Composition** | CPI/GDP are weighted composites. Must decompose into components, not predict headline directly. |
| C2 | **Basket Weight Mismatch** | CPI basket weights change periodically. LLM may use outdated weights. |
| C3 | **Lag Structure** | Economic data has release delays (1-3 months). Prediction date ≠ data date. |
| C4 | **Category Independence** | COE categories, sectoral GDP are independent. Must predict each separately. |
| C5 | **Base Effect** | YoY % change depends on base period. A low base inflates the number. |
| C6 | **Supply-Side vs Demand-Side** | CPI measures prices (supply-side), not consumer sentiment (demand-side). Don't confuse. |

### Question Template

```
COMPONENT-LEVEL (not headline):
"You run a [hawker stall / supermarket / petrol station] in [area].
Given that [specific input cost change], how would you adjust your
prices for [specific product] in the next month?"

Or for COE:
"You are bidding for COE Category [A/B/C/D/E].
Current quota: [X]. Last month's clearing price: $[Y].
Your maximum budget for COE: $[Z].
Would you bid this round? If yes, your maximum bid?"
```

### Context Injection (mandatory additions)

```
INDICATOR STRUCTURE:
[CPI/GDP/etc.] is a COMPOSITE INDEX with these components and weights:
  - Food: [X]%
  - Housing: [Y]%
  - Transport: [Z]%
  [...]
The headline number = Σ(component × weight).

NOTE: Each component can move independently. "Inflation is 3%"
is the weighted average — individual components may range from -2% to +8%.

[For COE]: Each COE category is an INDEPENDENT market. Cat A prices
have no direct relationship to Cat B. Predict each separately.
```

### Sampling Rules

- **Primary stratum**: Index component / category
- Sample SUPPLIERS (for CPI), not consumers — CPI measures what sellers charge
- For COE: sample car BUYERS stratified by buyer type × budget × urgency
- For GDP: sample by SECTOR (manufacturing, services, construction, etc.)
- **Aggregation**: Official index formula with official weights

### Validation Benchmarks

- CPI prediction: target MAE ≤ 0.3pp
- COE prediction: target MAE ≤ $5,000 per category
- GDP prediction: target MAE ≤ 0.5pp
- Must pass: component predictions weighted-sum to headline within rounding

---

## V-CONS: Consumer Behavior Vertical

**Triggered by**: buy, subscribe, apply, switch, adopt, usage, BTO, insurance, product, service

### Additional Structural Traps

| Trap | Name | Description |
|------|------|-------------|
| B1 | **Purchase Funnel Stages** | Awareness → Consideration → Intent → Purchase → Usage are different metrics. Don't conflate. |
| B2 | **Eligibility Filtering** | Not everyone is eligible (BTO: first-timer couples; insurance: health screening). Must filter before asking. |
| B3 | **Price Anchoring** | Without specific prices, LLM defaults to abstract "affordable/expensive." Must provide exact prices. |
| B4 | **Channel/Location Specificity** | BTO in Tengah ≠ BTO in Bishan. Must specify location with real details. |
| B5 | **Stated vs Revealed Preference** | People say they'll buy but don't. Apply historical conversion rate discount. |
| B6 | **Competitive Context** | Choices depend on alternatives available. Must specify the full choice set. |

### Question Template

```
"You are a [age]-year-old [marital status] [residency status] with
household income of $[X]/month, living in [current housing].

[Product/service] is available at $[exact price] with these features:
  - [Feature 1]
  - [Feature 2]

Alternative options:
  - [Alternative A] at $[price A]
  - [Alternative B] at $[price B]
  - Do nothing / keep current arrangement

Would you [buy/apply/switch]? If yes, which option?"
```

### Context Injection (mandatory additions)

```
MARKET CONTEXT:
[Product] launched on [date] at [price point].
Comparable products: [list with prices].
Previous round: [oversubscription rate / adoption rate / sales volume].

ELIGIBILITY:
You are [eligible / not eligible] for this product because [reason].
[For BTO]: First-timer priority, income ceiling $[X], must be [married/35+ single].
```

### Sampling Rules

- **Primary stratum**: Eligibility status (eligible vs not)
- Only simulate eligible population for demand predictions
- Stratify by: income band × age × current-product-ownership
- For BTO: stratify by location preference × marital × first-timer status
- **Aggregation**: Demand = eligible population × intent rate × historical conversion factor

### Validation Benchmarks

- Apply stated-to-revealed preference discount: typically 0.3-0.6x
- BTO oversubscription: target within ±1x of actual
- Product adoption: target within ±10pp of actual uptake rate
- Must pass: predicted demand > 0 for products that sold; predicted demand < supply for products that undersold

---

## V-POLI: Policy / Social Attitude Vertical

**Triggered by**: support, oppose, attitude, opinion, policy, 377A, death penalty, NS, racial, religion

### Additional Structural Traps

| Trap | Name | Description |
|------|------|-------------|
| P1 | **Social Desirability Bias** | People give "acceptable" answers on sensitive topics. LLM amplifies this. |
| P2 | **Question Framing Effects** | "Do you support X?" vs "Do you oppose X?" produce different results for the same topic. |
| P3 | **Moral Loading** | Emotionally charged language shifts responses. Must use neutral wording. |
| P4 | **Age-Cohort vs Life-Stage** | Young people's views: is it their generation or their age? Different prediction implications. |
| P5 | **Religious/Cultural Clustering** | On social issues, religion predicts better than income or education. Must include in strata. |
| P6 | **Overton Window Shift** | Acceptable range of opinion changes over time. LLM training data may reflect outdated window. |

### Question Template

```
Third-person neutral framing (Reformulated Prompting):
"A survey asks: '[Neutral question wording].'

How would this respondent most likely answer?"

NEVER use:
- "Do you support..." (leading)
- "Should the government..." (authority framing)
- Emotionally loaded terms

ALWAYS:
- Third person ("this respondent")
- Present both sides neutrally
- Include "no opinion" option
```

### Context Injection (mandatory additions)

```
SURVEY CONTEXT:
This survey is about [topic]. There is no right or wrong answer.
People in Singapore hold diverse views on this topic.

FACTUAL BACKGROUND (neutral):
[Fact 1 — what the policy is]
[Fact 2 — current status]
[Fact 3 — what supporters say]
[Fact 4 — what opponents say]

NOTE: Do NOT assume that the majority view is correct.
Real surveys on this topic have found a wide range of opinions
across different demographic groups.
```

### Sampling Rules

- Must include **religion** and **religiosity** as strata for social issues
- Must include **ethnicity × age** interaction (attitudes vary by generation within ethnic groups)
- For sensitive topics: oversample minorities and extreme-view demographics
- **Aggregation**: Population-weighted; report by subgroup, not just national average

### Validation Benchmarks

- Compare against benchmark survey's METHODOLOGY, not just results
- Match question wording as closely as possible to benchmark
- Social desirability gap estimate: 5-15pp on sensitive topics
- Must report: national average AND subgroup breakdown (age × ethnicity × religion)
- Target MAE ≤ 5pp for attitudes; ≤ 8pp for behavioral intent

---

# PART III: PROTOCOL OPERATIONS

## Vertical Detection Decision Tree

```
START
  │
  ├─ Contains: vote/election/candidate/party/GRC/SMC?
  │   YES → Load V-ELEC
  │
  ├─ Contains: CPI/GDP/COE/inflation/employment/MAS?
  │   YES → Load V-ECON
  │
  ├─ Contains: buy/apply/subscribe/BTO/insurance/adopt?
  │   YES → Load V-CONS
  │
  ├─ Contains: attitude/opinion/support/oppose/policy?
  │   YES → Load V-POLI
  │
  ├─ Contains signals from 2+ verticals?
  │   YES → Load HYBRID (all matching modules)
  │
  └─ None match?
      → Use universal core only + flag for Sophie manual review
```

## Failure Mode → Phase/Module Mapping

| Failure Mode | Caught By | Module |
|---|---|---|
| Contested-vs-national conflation | Phase 2 + V-ELEC E1 | Election |
| Options include non-contesting parties | Phase 4 + V-ELEC template | Election |
| CPI components predicted as single number | Phase 1 Q1 + V-ECON C1 | Economic |
| COE categories mixed together | Phase 1 Q2 + V-ECON C4 | Economic |
| BTO demand without eligibility filter | Phase 6 + V-CONS B2 | Consumer |
| Stated intent treated as actual behavior | Phase 7 + V-CONS B5 | Consumer |
| Social desirability inflation | Phase 5 + V-POLI P1 | Policy |
| Leading question wording | Phase 3 + V-POLI P2 | Policy |
| LLM using media framing | Phase 5 Rule 2 | Universal |
| Data leakage (outcome in context) | Phase 5 Rule 4 + Phase 7 Check 3 | Universal |
| Generic demographics instead of event strata | Phase 6 principle | Universal |

## Post-Simulation Feedback Loop

After every simulation:

1. **Error Decomposition**: Which trap types caused the biggest errors?
2. **Module Update**: Add newly discovered traps to the relevant vertical
3. **Benchmark Update**: Update validation benchmarks with actual results
4. **Protocol Version**: Increment version number, document what changed

```
GE2025 post-mortem → Added E1 (Partial Contestation) to V-ELEC
                   → Updated PAP plausible range to [55%, 75%]
                   → Added "Shy Tory" trap E5
                   → Updated validation target to MAE ≤ 3pp
```

---

## Quick Start: Which Phases Get Vertical Additions?

| Phase | Universal | V-ELEC adds | V-ECON adds | V-CONS adds | V-POLI adds |
|-------|-----------|------------|------------|------------|------------|
| 1. Research | 5 questions | Seat map, candidate list | Index components, weights | Eligibility rules, pricing | Benchmark survey methodology |
| 2. Traps | 6 types | +6 election traps | +6 economic traps | +6 consumer traps | +6 policy traps |
| 3. Question | 5 criteria | Per-constituency Q | Per-component Q | Eligibility-gated Q | Third-person neutral Q |
| 4. Options | 5 rules | Real candidate names | Price brackets | Full choice set | Both-sides neutral |
| 5. Context | 4 sections | Coverage math, baseline | Official weights, lags | Market context, alternatives | Neutral background |
| 6. Sampling | Event strata | By constituency | By component/category | By eligibility × income | By religion × ethnicity × age |
| 7. Validation | 5 checks | Sum=100% per ward | Components→headline | Demand > 0 for sold items | Subgroup spread check |
| 8. Client | 3 meetings | National vs seat-level? | Headline vs component? | Intent vs actual? | National vs subgroup? |
