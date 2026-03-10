# Insurance Vertical — Backtest & Survey Designs

Following Protocol v2.0 (8 Universal Phases)
Vertical: CONSUMER (insurance purchase behavior & attitudes)

---

## BT-011: Protection Adequacy Perception

### Ground Truth Source
LIA Protection Gap Study 2022 (market survey of 775 EA individuals)

### Question Design
**Q**: "Do you think your current life insurance coverage is sufficient to protect your family financially if something happens to you?"

**Options** (5-point scale):
1. Very insufficient — I have little or no coverage
2. Somewhat insufficient — I have some coverage but not enough
3. About right — I think my coverage is adequate
4. More than enough — I'm well covered
5. Don't know / Haven't thought about it

### Context Injection (Protocol v2.0 compliant)
- Singapore's healthcare and insurance system overview (MediShield Life, CPF, IP)
- General cost of living data (housing, education, healthcare costs)
- Average income levels by age group
- **DO NOT include**: PGS results, actual gap percentages, or any survey findings

### Validation Dimensions
- By age group (21-30, 31-40, 41-50, 51-64)
- By income quintile
- By gender
- By marital status (single, married, married with children)
- By housing type (proxy for wealth: HDB 1-2rm, HDB 3-4rm, HDB 5rm/exec, condo, landed)

### Expected Agent Distribution (calibration target)
- Based on PGS 2022: ~21% mortality gap, ~74% CI gap
- Expect majority to answer "somewhat insufficient" or "don't know"
- Higher-income agents should show higher perceived adequacy
- Younger agents more likely to say "haven't thought about it"

---

## BT-012: IP Price Hike Response

### Ground Truth Source
2025 IP premium increases (all but one insurer raised prices) + MOH reform announcement

### Question Design
**Q**: "Your Integrated Shield Plan (IP) premium has increased by 15-25% this year. What will you most likely do?"

**Options**:
1. Keep my current plan and pay the higher premium
2. Downgrade to a lower ward class (e.g., Class A → B1)
3. Remove or reduce my IP rider to lower the cost
4. Switch to a different insurer with lower premiums
5. Drop my IP entirely and rely only on MediShield Life
6. I don't have an IP / Not applicable

### Context Injection
- Explain what IP is (top-up to MediShield Life)
- Mention that premiums have risen across the industry in 2025
- Mention MOH announced new IP rider requirements effective April 2026
- General healthcare cost trends
- **DO NOT include**: actual consumer survey results on IP responses

### Validation Dimensions
- By age (younger = more price-sensitive, older = more concerned about coverage loss)
- By income (lower income = more likely to downgrade/drop)
- By IP ward class (Class A holders have more room to downgrade)

---

## BT-013: Insurance Purchase Barriers

### Ground Truth Source
Swiss Re Asia L&H Consumer Survey 2025

### Question Design
**Q**: "What is the main reason you have not purchased (more) life or health insurance?"

**Options**:
1. Too expensive / Can't afford the premiums
2. I don't understand insurance products well enough
3. I think my existing coverage (CPF, MediShield Life) is sufficient
4. I don't trust insurance companies or agents
5. The products available don't match my needs
6. I'm young and healthy — I don't need it yet
7. I already have adequate private insurance coverage
8. Other reasons

### Context Injection
- Overview of Singapore's compulsory schemes (MediShield Life, CareShield Life, DPS)
- General awareness that Singapore has a multi-layer system
- Cost of insurance products in general terms
- **DO NOT include**: Swiss Re survey results, barrier rankings, or purchase intent percentages

### Validation Dimensions
- By age (young → "don't need yet", middle-aged → "too expensive")
- By income (low → "can't afford", high → "already covered")
- By education level (lower → "don't understand", higher → "products don't match")

---

## BT-014: Brand Trust & Purchase Consideration

### Ground Truth Source
YouGov Brand Equity Ranking 2023

### Question Design
**Q**: "If you were to purchase a new insurance policy today, which insurer would you most likely consider? (Select up to 2)"

**Options**:
1. NTUC Income (Income Insurance)
2. Great Eastern
3. AIA
4. Prudential
5. Singlife
6. Manulife
7. FWD
8. Other / No preference

### Context Injection
- Brief description of major insurers (without brand sentiment data)
- Distribution channel landscape (FA vs tied agent vs online)
- **DO NOT include**: YouGov rankings, brand scores, market share data

### Validation Dimensions
- By age (older → NTUC Income/Great Eastern, younger → Singlife/FWD)
- By income (higher → AIA/Prudential, lower → NTUC Income)
- By channel preference (digital-first → Singlife/FWD, advisor → Great Eastern/AIA)

---

## SV-003: MediShield Life +20% Premium Scenario (Predictive)

### Ground Truth
None — this is a forward-looking simulation. Calibrate with BT-012 results.

### Question Design
**Q**: "The government announces that MediShield Life premiums will increase by 20% over the next 2 years due to rising healthcare costs. Additional subsidies will be provided for lower-income individuals. How would this affect your insurance decisions?"

**Options**:
1. No change — I'll absorb the increase, it's still affordable
2. I'll review and possibly downgrade my IP to offset the cost
3. I'll cut back on other private insurance to compensate
4. I'll increase my MediSave contributions to cover it
5. I'm worried — this is becoming unaffordable
6. I support the increase if it means better coverage

### Simulation Value
- Test sensitivity of different demographic cohorts to premium changes
- Compare responses across income levels and age groups
- Feed into policy advisory scenarios

---

## SV-004: Platform Worker Mandatory Insurance (Predictive)

### Ground Truth
LIA PGS 2022 platform worker data (59% mortality gap, 91% CI gap)

### Question Design
**Q**: "The government is considering requiring platform companies (Grab, Deliveroo, etc.) to provide basic insurance coverage for their workers. As a Singapore resident, what is your view?"

**Options**:
1. Strongly support — platform workers deserve protection
2. Support — but concerned about higher service fees being passed to consumers
3. Neutral — I don't have a strong opinion
4. Oppose — it's the worker's personal responsibility
5. Oppose — it will hurt the gig economy and reduce flexible work options

### Validation Dimensions
- By employment type (platform worker, employed, self-employed)
- By age (younger → more sympathy for gig workers, older → more "personal responsibility")
- By income (lower → support, higher → concern about service fees)
- By political leaning proxy (housing type, education)

---

## Implementation Priority

| Priority | ID | Reason |
|----------|----|--------|
| 1 | BT-011 | Clear ground truth, directly tests agent insurance awareness |
| 2 | BT-012 | Hottest topic in 2025-2026, high commercial value |
| 3 | BT-013 | Rich Swiss Re data for validation |
| 4 | SV-003 | Policy scenario — attractive to potential clients |
| 5 | BT-014 | Brand data available but less directly useful |
| 6 | SV-004 | Policy debate — good for showcasing platform |
