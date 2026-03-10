"""
Script 18: Run ALL pending cases — backtests, surveys, and predictions.
N=1000 per case, sequential execution. Estimated runtime: ~65 min total.

Usage:
    python3 -u scripts/18_run_all_pending.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from datetime import datetime

from lib.sampling import stratified_sample, ADULT_STRATA, CITIZEN_VOTER_STRATA
from lib.persona import agent_to_persona, agent_response_meta
from lib.llm import ask_agents_batch
from lib.analysis import compute_distribution, print_breakdown

SAMPLE_SIZE = 1000


# ============================================================
# ALL CASES DEFINITION
# ============================================================

CASES = [
    # --- BACKTESTS ---
    {
        "id": "BT-004", "name": "377A Repeal Attitudes", "seed": 50,
        "questions": [{
            "label": "377A Repeal",
            "question": "What is this respondent's view on the repeal of Section 377A (the law that criminalized sex between men)?",
            "options": [
                "Strongly support repeal",
                "Somewhat support repeal",
                "Neutral / No opinion",
                "Somewhat oppose repeal",
                "Strongly oppose repeal",
            ],
        }],
        "ground_truth": {"Support retaining 377A": 44, "Oppose retaining 377A": 20, "Neutral": 36},
        "source": "Ipsos Survey, Jun 2022 (n=500)",
        "context": (
            "SECTION 377A — SINGAPORE CONTEXT:\n\n"
            "- Section 377A of the Penal Code criminalized sex between men. It was enacted in 1938 during British colonial rule.\n"
            "- In November 2022, Singapore repealed Section 377A, decriminalizing sex between men.\n"
            "- Simultaneously, the government amended the Constitution to define marriage as between a man and a woman, "
            "preventing legal challenges to expand marriage definitions.\n"
            "- PM Lee Hsien Loong described the approach as 'live and let live' — decriminalize but not endorse.\n"
            "- Singapore's society is multi-religious: Buddhism (~31%), Christianity (~19%), Islam (~15%), Taoism (~9%), Hinduism (~5%), no religion (~20%).\n"
            "- Older Singaporeans and religious communities tend to hold more conservative views on homosexuality.\n"
            "- Younger Singaporeans, especially university-educated, tend toward more liberal views.\n"
            "- Pink Dot (annual LGBT rally) has grown from ~1,000 (2009) to ~28,000 (2023) attendees.\n\n"
            "NOTE: Consider the respondent's age, religion/ethnicity, education level, and personality. "
            "This is a highly polarized issue with strong generational divide."
        ),
    },
    {
        "id": "BT-005", "name": "Death Penalty Attitudes", "seed": 51,
        "questions": [{
            "label": "Death Penalty",
            "question": "Does this respondent support or oppose the death penalty for the most serious crimes (e.g., drug trafficking, murder)?",
            "options": [
                "Strongly support",
                "Somewhat support",
                "Neutral",
                "Somewhat oppose",
                "Strongly oppose",
            ],
        }],
        "ground_truth": {"Support (combined)": 77.4, "Oppose (combined)": 22.6},
        "source": "MHA Survey 2023 (n=2000)",
        "context": (
            "DEATH PENALTY IN SINGAPORE — KEY FACTS:\n\n"
            "- Singapore retains the mandatory death penalty for certain drug trafficking offences "
            "(e.g., trafficking more than 15g of heroin or 500g of cannabis).\n"
            "- Murder also carries the death penalty, though judicial discretion was introduced in 2012.\n"
            "- Between 2010-2023, Singapore executed approximately 15-20 people, mostly for drug offences.\n"
            "- In 2022-2023, several high-profile executions drew international attention and protests.\n"
            "- The government's position: death penalty is a strong deterrent that has kept Singapore "
            "one of the safest countries in the world, with very low drug abuse rates.\n"
            "- Anti-death penalty activists argue it disproportionately affects lower-income drug mules "
            "rather than drug kingpins.\n"
            "- Singapore's drug policy is among the strictest in the world.\n"
            "- Neighboring countries (Malaysia, Thailand) have moved away from mandatory death penalty for drugs.\n\n"
            "NOTE: Consider the respondent's age, education, personality (risk-averse vs. empathetic), "
            "and exposure to international perspectives. Singapore has strong societal consensus on law and order."
        ),
    },
    {
        "id": "BT-006", "name": "Racial & Religious Harmony", "seed": 52,
        "questions": [{
            "label": "Racial Harmony",
            "question": "How would this respondent rate the current level of racial and religious harmony in Singapore?",
            "options": [
                "Very high",
                "High",
                "Moderate",
                "Low",
                "Very low",
            ],
        }],
        "ground_truth": {"High/Very high": 66.7, "Moderate": 25, "Low/Very low": 8.3},
        "source": "IPS Working Paper No.59, 2024 (n=4000)",
        "context": (
            "RACIAL & RELIGIOUS HARMONY IN SINGAPORE — KEY FACTS:\n\n"
            "- Singapore is a multi-racial society: Chinese (~74%), Malay (~13.5%), Indian (~9%), Others (~3.5%).\n"
            "- Multi-religious: Buddhism, Christianity, Islam, Taoism, Hinduism, and ~20% no religion.\n"
            "- Racial Harmony Day (July 21) commemorates the 1964 racial riots.\n"
            "- HDB ethnic integration policy (EIP) maintains racial quotas in public housing blocks.\n"
            "- Group Representation Constituencies (GRCs) ensure minority representation in Parliament.\n"
            "- Maintenance of Religious Harmony Act (MRHA) gives government power to restrain religious leaders "
            "who cause disharmony.\n"
            "- Recent incidents: 'brownface' advertising controversy (2019), online racism cases prosecuted under POHA.\n"
            "- Government introduced Racial Harmony Commission recommendations (2022).\n"
            "- Inter-racial and inter-religious marriages have increased over the past decade.\n"
            "- Social media has surfaced more discussions about casual racism and microaggressions.\n\n"
            "NOTE: Consider the respondent's ethnicity (minorities may perceive harmony differently from majority), "
            "age (older generations experienced actual racial tensions), housing type, and education level."
        ),
    },
    {
        "id": "BT-007", "name": "Net Zero 2050 Support", "seed": 53,
        "questions": [{
            "label": "Net Zero 2050",
            "question": "Does this respondent support Singapore's target to achieve Net Zero carbon emissions by 2050?",
            "options": [
                "Strongly support",
                "Support",
                "Neutral",
                "Oppose",
                "Strongly oppose",
            ],
        }],
        "ground_truth": {"Support Net Zero 2050": 65, "Want more ambitious timeline": 17, "Other": 18},
        "source": "MSE/NUS/SUTD Survey 2023 (n=2000+)",
        "context": (
            "NET ZERO 2050 — SINGAPORE CONTEXT:\n\n"
            "- In 2022, Singapore raised its climate ambition to achieve Net Zero emissions by 2050.\n"
            "- Singapore is a small island city-state highly vulnerable to sea level rise.\n"
            "- Carbon tax: $5/tonne (2019-2023), $25/tonne (2024-2025), planned $45/tonne (2026-2027), $50-80/tonne (2030).\n"
            "- Singapore's total emissions: ~50 million tonnes CO2 per year (0.1% of global emissions).\n"
            "- Key challenges: limited renewable energy potential (no wind/hydro, limited land for solar).\n"
            "- Singapore is investing in hydrogen, carbon capture, and regional green energy imports.\n"
            "- EV adoption growing: COE for EVs, charging infrastructure expansion.\n"
            "- Green buildings: 80% of buildings to be green-certified by 2030.\n"
            "- International hub: Singapore hosts carbon credit markets and green finance initiatives.\n\n"
            "NOTE: Consider the respondent's age (younger tend to support), education level, "
            "income (carbon tax impacts lower-income more), and personality (openness to change)."
        ),
    },
    {
        "id": "BT-009", "name": "Plastic Bag Charge Behavior", "seed": 54,
        "questions": [{
            "label": "Plastic Bag Charge",
            "question": "If supermarkets charge $0.05 per disposable plastic bag, would this respondent bring their own reusable bag?",
            "options": [
                "Always bring own bag",
                "Usually bring own bag",
                "Sometimes",
                "Rarely",
                "Never, will pay for bags",
            ],
        }],
        "ground_truth": {"Bring own bag (observed)": 70, "Still use disposable": 30},
        "source": "NEA / FairPrice data, 2024",
        "context": (
            "PLASTIC BAG CHARGE — SINGAPORE CONTEXT:\n\n"
            "- From 3 July 2023, large supermarket operators in Singapore must charge at least $0.05 per disposable bag.\n"
            "- This applies to supermarkets with annual turnover >$100 million (NTUC FairPrice, Cold Storage, Sheng Siong, etc.).\n"
            "- Smaller shops, wet markets, and hawker centres are NOT covered.\n"
            "- The charge applies to all disposable bags — plastic, paper, and biodegradable.\n"
            "- Revenue from bag charges goes to the retailers (not the government).\n"
            "- Singapore previously consumed ~820 million plastic bags per year from supermarkets alone.\n"
            "- The policy is part of Singapore's Zero Waste Masterplan and Green Plan 2030.\n"
            "- Similar policies in other countries: Ireland (2002), UK (2015), Taiwan, Hong Kong (2022).\n"
            "- International data shows bag charges typically reduce usage by 50-90%.\n\n"
            "NOTE: Consider the respondent's age (older may have existing habits), income (wealthier may not care "
            "about $0.05), housing type (car owners find it easier to carry reusable bags), "
            "and personality (conscientiousness, environmental awareness)."
        ),
    },
    {
        "id": "BT-010", "name": "Cost of Living Concerns", "seed": 55,
        "questions": [{
            "label": "Top Concern",
            "question": "What is this respondent's MOST important concern for Singapore right now?",
            "options": [
                "Cost of living",
                "Housing affordability",
                "Healthcare",
                "Jobs & economy",
                "Immigration",
                "Education",
            ],
        }],
        "ground_truth": {"Cost of living": 74, "Housing affordability": 61, "Healthcare": 41},
        "source": "IPS Post-GE2025 (n=2056)",
        "context": (
            "SINGAPORE PUBLIC CONCERNS — 2025/2026 CONTEXT:\n\n"
            "- GE2025 was held on 3 May 2025. PAP won 65.6% of popular vote.\n"
            "- Pre-election polls showed cost of living as the #1 concern.\n"
            "- GST increased from 8% to 9% in January 2024 (second phase of the 7%→9% increase).\n"
            "- HDB resale prices hit record highs in 2024, with million-dollar flats becoming common.\n"
            "- Healthcare costs rising: IP premiums up 10-25% annually over 2022-2025.\n"
            "- Unemployment rate low at 2.0% (Q4 2025), but concerns about AI displacement growing.\n"
            "- Immigration: non-resident population ~1.86 million (vs 4.15 million residents).\n"
            "- Budget 2026: focused on economic resilience and support for lower/middle income.\n"
            "- US tariff uncertainties affecting export-dependent Singapore economy.\n\n"
            "NOTE: Consider the respondent's income (lower income more affected by cost of living), "
            "age (younger more concerned about housing), housing type (renters vs owners), "
            "and employment status."
        ),
    },
    # --- SURVEYS (insurance vertical) ---
    {
        "id": "SV-003", "name": "IP Switching & Channel Preference", "seed": 60,
        "questions": [
            {
                "label": "Q1: IP Switching Intent",
                "question": "Has this respondent seriously considered switching their Integrated Shield Plan (IP) to a different insurer in the past 12 months?",
                "options": [
                    "Yes, actively comparing plans from other insurers",
                    "Yes, thought about it but haven't acted",
                    "No, satisfied with current insurer",
                    "No, too much hassle to switch",
                    "Not applicable (no IP currently)",
                ],
            },
            {
                "label": "Q2: Switching Trigger",
                "question": "What would most likely trigger this respondent to switch their IP to a different insurer?",
                "options": [
                    "Finding 15%+ lower premium elsewhere",
                    "Better coverage at the same price",
                    "Bad claims experience with current insurer",
                    "Agent or friend recommendation",
                    "Would not switch regardless of circumstances",
                ],
            },
            {
                "label": "Q3: Purchase Channel",
                "question": "If this respondent were buying or switching IP today, which channel would they prefer?",
                "options": [
                    "Insurance agent (face-to-face advice)",
                    "Online comparison then agent for purchase",
                    "Fully online / app (no agent needed)",
                    "Bank channel (bancassurance)",
                    "Through employer group scheme",
                ],
            },
        ],
        "context": (
            "INTEGRATED SHIELD PLAN (IP) SWITCHING — SINGAPORE 2025/2026:\n\n"
            "- MAS introduced IP portability reforms in 2024, allowing policyholders to switch insurers "
            "without losing coverage continuity for pre-existing conditions.\n"
            "- 7 IP insurers: AIA, Great Eastern, NTUC Income, Prudential, Singlife, AXA, Raffles Health.\n"
            "- IP premiums have increased 10-25% annually over 2022-2025.\n"
            "- As of 2024, approximately 2.9 million Singapore residents (69%) have an IP.\n"
            "- MAS Comparefirst.sg allows consumers to compare IP plans side-by-side.\n"
            "- Historically, IP switching was rare (<5% per year) due to pre-existing condition clauses.\n"
            "- Post-reform, early data suggests switching interest has increased but actual switches remain limited.\n"
            "- Agent channel still dominates IP sales (~70% of new policies).\n"
            "- Digital-first insurers (Singlife, FWD) have grown market share in simple products but less so in IP.\n\n"
            "NOTE: Consider age (older policyholders more reluctant to switch), income, "
            "existing health conditions (affect switching calculus), and personality."
        ),
    },
    {
        "id": "SV-004", "name": "IP Product Innovation Acceptance", "seed": 61,
        "questions": [
            {
                "label": "Q1: Panel Doctor Acceptance",
                "question": "If this respondent's IP offered a 'panel doctor' option — using insurer-approved doctors/hospitals for 20% lower premium — would they accept it?",
                "options": [
                    "Yes, definitely — 20% savings is significant",
                    "Probably yes, if panel includes reputable hospitals",
                    "Neutral — need to see the panel list first",
                    "Probably no — freedom to choose doctor is important",
                    "Definitely no — will not accept any restriction on doctor choice",
                ],
            },
            {
                "label": "Q2: Basic Private IP Interest",
                "question": "If a new 'Basic Private IP' existed at $400/year (covers private hospitals but with higher co-payment and panel restrictions), would this respondent be interested?",
                "options": [
                    "Yes — would buy as new customer (currently no private IP)",
                    "Yes — would downgrade from current full-coverage IP to save money",
                    "Maybe — interested but need more details",
                    "No — prefer full coverage even at higher price",
                    "No — would stick with MediShield Life only",
                ],
            },
            {
                "label": "Q3: Coverage Trade-off",
                "question": "Which coverage feature would this respondent most willingly give up to reduce their IP premium by 15%?",
                "options": [
                    "Single-bed room (accept shared room instead)",
                    "Choice of any doctor (accept panel doctors only)",
                    "Outpatient specialist coverage",
                    "Traditional/alternative medicine coverage",
                    "None — would not give up any coverage",
                ],
            },
        ],
        "context": (
            "IP PRODUCT INNOVATION — SINGAPORE CONTEXT:\n\n"
            "- MAS has encouraged insurers to implement panel doctor arrangements to control costs.\n"
            "- Panel arrangements: insurer negotiates fixed fees with selected doctors/hospitals, "
            "passing savings to policyholders as lower premiums or co-payments.\n"
            "- Currently, most IPs offer 'as-charged' basis with freedom to choose any doctor.\n"
            "- Co-payment: most IPs now require 5-10% co-payment (increased from 0% historically).\n"
            "- Private hospital IP premiums: $300-500/year (age 35), $1,500-3,000/year (age 65).\n"
            "- Restructured hospital IP premiums: significantly lower ($100-200/year for age 35).\n"
            "- International comparison: US managed care (HMO/PPO), Australia medibank panels — "
            "panel models are standard globally but new to Singapore.\n"
            "- Singapore consumers historically value freedom of choice highly.\n\n"
            "NOTE: Consider income (lower income more price-sensitive), age (older have higher premiums, "
            "more to gain from savings), health status (chronic conditions value doctor choice), "
            "and personality (risk-averse vs. pragmatic)."
        ),
    },
    {
        "id": "SV-005", "name": "Young Adults IP Awareness", "seed": 62,
        "age_filter": (25, 35), "sample_size": 500,
        "questions": [
            {
                "label": "Q1: IP Awareness Level",
                "question": "How well does this respondent (age 25-35) understand what an Integrated Shield Plan (IP) covers?",
                "options": [
                    "Very well — can explain difference between IP and MediShield Life",
                    "Somewhat — knows IP exists but vague on details",
                    "Heard of it but don't really understand what it covers",
                    "Never heard of Integrated Shield Plan",
                    "Confused it with other insurance (e.g. life insurance, critical illness)",
                ],
            },
            {
                "label": "Q2: Primary Barrier",
                "question": "What is the primary reason this respondent does NOT have a private hospital IP?",
                "options": [
                    "Too expensive / not worth the premium at my age",
                    "Feel healthy, don't need it yet",
                    "MediShield Life is enough for now",
                    "Don't understand the product well enough to decide",
                    "Haven't gotten around to it / procrastination",
                    "Already have one — employer or parents arranged it",
                ],
            },
            {
                "label": "Q3: Purchase Trigger",
                "question": "What life event would most likely trigger this respondent to buy or upgrade their IP?",
                "options": [
                    "Getting married",
                    "Having a child",
                    "Turning 40",
                    "A health scare (self or family member)",
                    "Seeing friends/family make large hospital claims",
                    "Would not buy regardless of life events",
                ],
            },
        ],
        "context": (
            "YOUNG ADULTS & IP — SINGAPORE CONTEXT:\n\n"
            "- MediShield Life covers all Singapore citizens/PRs automatically (basic public hospital coverage).\n"
            "- Integrated Shield Plans (IPs) provide additional coverage above MediShield Life.\n"
            "- Overall IP penetration: ~69% of residents. But penetration is lower among 25-35 year olds.\n"
            "- IP premiums for age 25-35: ~$200-400/year for private hospital coverage.\n"
            "- Many young adults rely on employer group insurance or parents' family plans.\n"
            "- Young adults face competing financial priorities: housing (BTO), student loans, saving for marriage.\n"
            "- CPF MediSave can be used to pay IP premiums (reduces out-of-pocket cost).\n"
            "- Digital comparison platforms (MoneySmart, SingSaver) have increased awareness.\n"
            "- Social media influencers and financial bloggers (Seedly, Investment Moats) discuss IP frequently.\n\n"
            "NOTE: Consider education level (university-educated more aware), income, "
            "marital/family status, personality (risk-averse vs. carefree), and housing situation."
        ),
    },
    {
        "id": "SV-006", "name": "Savings Insurance vs Alternatives", "seed": 63,
        "questions": [
            {
                "label": "Q1: Where to Put $10K",
                "question": "T-bill rates have dropped from 4% to ~2.8%. Where would this respondent most likely put their next $10,000 in savings?",
                "options": [
                    "Bank fixed deposit (safe, liquid)",
                    "Singapore Savings Bonds (SSB)",
                    "CPF SA/MA voluntary top-up (4% guaranteed)",
                    "Endowment / savings insurance plan",
                    "Stocks / ETFs / robo-advisor",
                    "Keep as cash — waiting for better options",
                ],
            },
            {
                "label": "Q2: Savings Insurance Appeal",
                "question": "What would most attract this respondent to a savings insurance plan over bank deposits?",
                "options": [
                    "Guaranteed returns higher than bank fixed deposit",
                    "Forced savings discipline (cannot withdraw easily)",
                    "Death/TPD benefit included",
                    "Estate planning (nominated beneficiary, bypasses probate)",
                    "Nothing — would not consider savings insurance",
                    "Already have one — would consider adding more",
                ],
            },
            {
                "label": "Q3: $50K for 10 Years",
                "question": "If this respondent has $50,000 to save for 10 years, which option is most appealing?",
                "options": [
                    "Bank FD: 2.5% guaranteed, fully liquid",
                    "CPF SA top-up: 4% guaranteed, locked until 55",
                    "Savings plan: 3.2% guaranteed + 0.5% bonus, locked 10 years",
                    "Balanced fund: ~5% expected but not guaranteed, liquid",
                    "Mix: half CPF top-up + half savings plan",
                ],
            },
            {
                "label": "Q4: Life Stage Trigger",
                "question": "At what life stage is this respondent most likely to buy a savings/endowment insurance plan?",
                "options": [
                    "Upon starting first job (forced savings habit)",
                    "Getting married / buying home",
                    "After having children (education fund)",
                    "Age 40-50 (retirement planning acceleration)",
                    "After receiving a windfall (bonus, inheritance)",
                    "Would not buy at any stage",
                ],
            },
        ],
        "context": (
            "SAVINGS & INVESTMENT IN SINGAPORE — 2025/2026 CONTEXT:\n\n"
            "- T-bill (6-month) rates: peaked at ~4% (2023), now ~2.8% (2026).\n"
            "- Singapore Savings Bonds (SSB): ~2.5-3.0% average yield, 10-year, fully liquid.\n"
            "- CPF SA interest: 4.0% (guaranteed, but locked until age 55).\n"
            "- CPF OA interest: 2.5%. CPF MA interest: 4.0%.\n"
            "- Bank fixed deposits: ~2.0-2.5% for 12-month.\n"
            "- Endowment/savings insurance plans: typically 3.0-3.5% guaranteed + 0.5-1.0% non-guaranteed bonus.\n"
            "- Lock-in period for savings plans: typically 5-25 years. Early surrender penalty significant.\n"
            "- Robo-advisors (Syfe, StashAway, Endowus): growing AUM, ~$5B combined in Singapore.\n"
            "- STI Index ETF: ~7% average annual return (long-term), volatile short-term.\n"
            "- Singaporeans are known for high savings rate (~50% of household income).\n"
            "- CPF voluntary top-up has tax relief (up to $8,000/year for SA, $8,000 for MA).\n\n"
            "NOTE: Consider age (younger may prefer growth, older prefer safety), income (affects risk capacity), "
            "financial literacy (education level), personality (risk appetite), and life stage."
        ),
    },
    {
        "id": "SV-007", "name": "ILP Trust & Bundling Preference", "seed": 64,
        "questions": [
            {
                "label": "Q1: ILP Trust Level",
                "question": "How much does this respondent trust Investment-Linked Plans (ILPs) as a financial product?",
                "options": [
                    "High trust — good way to combine insurance and investment",
                    "Moderate trust — useful but fees are a concern",
                    "Neutral — don't know enough to judge",
                    "Low trust — heard mostly negative things about ILPs",
                    "No trust at all — ILPs are a bad deal for consumers",
                ],
            },
            {
                "label": "Q2: Bundled vs Unbundled",
                "question": "If this respondent wanted both life insurance protection AND investment growth, which approach would they prefer?",
                "options": [
                    "All-in-one ILP (insurance + investment in one product)",
                    "Term life insurance + separate robo-advisor or ETF",
                    "Term life insurance + separate unit trust via bank",
                    "Whole life policy (with cash value) + no separate investment",
                    "Don't want investment component — pure protection only",
                ],
            },
            {
                "label": "Q3: What Would Increase ILP Willingness",
                "question": "What would most increase this respondent's willingness to buy an ILP?",
                "options": [
                    "Clear fee breakdown showing total cost vs direct investing",
                    "Guaranteed minimum return (e.g. capital protection after 10 years)",
                    "Ability to switch sub-funds freely without charges",
                    "Lower management fees (below 1% per annum)",
                    "Independent comparison showing ILP outperforming alternatives",
                    "Nothing — would not consider ILP regardless",
                ],
            },
        ],
        "context": (
            "INVESTMENT-LINKED PLANS (ILPs) — SINGAPORE CONTEXT:\n\n"
            "- ILPs combine life insurance with unit trust investments. Premiums are split between "
            "insurance charges and investment in sub-funds chosen by the policyholder.\n"
            "- ILP sales in Singapore: ~$2.1 billion new premiums (2024), representing ~36% of new individual business.\n"
            "- Total ILP AUM: ~$45 billion.\n"
            "- MAS has tightened ILP regulation: enhanced disclosure requirements, ban on ILP sales via cold calling (2023).\n"
            "- Common criticism: high fees (2-4% total expense ratio vs 0.2-0.5% for ETFs), surrender charges, "
            "poor transparency, and underperformance vs passive index funds.\n"
            "- 'Buy term invest the rest' (BTIR) philosophy has gained popularity, especially among younger investors.\n"
            "- Financial bloggers and forums (HardwareZone, Reddit r/singaporefi) are generally anti-ILP.\n"
            "- ILPs remain popular among older, less financially literate consumers who prefer agent-guided solutions.\n"
            "- Robo-advisors (Syfe, StashAway, Endowus) and DIY investing via brokerages (moomoo, Tiger) "
            "are direct competitors to ILPs for the investment component.\n\n"
            "NOTE: Consider age (younger more skeptical), education/financial literacy, income, "
            "personality (self-directed vs. delegation-preferring), and risk appetite."
        ),
    },
    # --- PREDICTIONS ---
    {
        "id": "PR-001", "name": "Consumer Confidence March 2026", "seed": 70,
        "questions": [{
            "label": "Consumer Confidence",
            "question": "How confident is this respondent about their household's financial situation over the next 6 months?",
            "options": [
                "Very optimistic",
                "Somewhat optimistic",
                "Neutral",
                "Somewhat pessimistic",
                "Very pessimistic",
            ],
        }],
        "context": (
            "SINGAPORE ECONOMIC OUTLOOK — MARCH 2026:\n\n"
            "- GDP growth 2025: 4.4% (better than expected). 2026 forecast: 1-3% (slowing due to global uncertainty).\n"
            "- Unemployment rate: 2.0% (Q4 2025), historically low.\n"
            "- Inflation: core CPI 1.6% (Jan 2026), down from 3.7% peak in 2023.\n"
            "- GST: 9% since Jan 2024 (final phase of 7%→9% increase).\n"
            "- HDB resale prices: continued to rise but pace slowing.\n"
            "- US tariff uncertainty: potential 10-25% tariffs on Asian exports. Singapore trade-dependent.\n"
            "- MAS monetary policy: slight easing in Jan 2025, Singapore dollar appreciation band narrowed.\n"
            "- Budget 2026: S&CC rebates, CDC vouchers, but also carbon tax increase scheduled.\n"
            "- Ipsos Consumer Confidence Index Feb 2026: 56.3 (significant gains from Jan 52.4).\n"
            "- Regional context: China slowdown, US policy uncertainty, ASEAN resilience.\n\n"
            "NOTE: Consider income (lower income more pessimistic), employment status, age, "
            "housing type (property owners benefiting from price gains), and personality."
        ),
    },
    {
        "id": "PR-002", "name": "What Worries Singapore March 2026", "seed": 71,
        "questions": [{
            "label": "Top Worry",
            "question": "What is this respondent's TOP concern for Singapore right now?",
            "options": [
                "Inflation / Cost of living",
                "Unemployment / Job security",
                "Healthcare",
                "Housing",
                "Crime / Safety",
                "Immigration",
                "Climate change",
            ],
        }],
        "context": (
            "SINGAPORE PUBLIC CONCERNS — MARCH 2026:\n\n"
            "- Ipsos 'What Worries the World' Feb 2026: inflation 56%, unemployment 56% (tied for first time).\n"
            "- Cost of living remains top concern despite inflation cooling (core CPI 1.6%).\n"
            "- Unemployment concerns rising due to US tariff threats and tech layoffs.\n"
            "- Healthcare costs: IP premiums up 10-25% annually; aging population pressure.\n"
            "- Housing: HDB resale prices at record highs. BTO wait times 4-5 years.\n"
            "- Crime rate remains very low but scam cases increased 46% in 2024.\n"
            "- Immigration: foreign workforce ~1.46 million, public discourse on integration.\n"
            "- Climate: Singapore committed to Net Zero by 2050; recent extreme weather events.\n"
            "- Budget 2026 provided cost-of-living support measures.\n"
            "- GE2025 exit polls showed cost of living as #1 voter concern.\n\n"
            "NOTE: Consider income level (lower income: cost of living; higher: investment/jobs), "
            "age (younger: housing, jobs; older: healthcare), employment status, and housing type."
        ),
    },
]


def run_case(case_def, batch, agent_dicts):
    """Run all questions for a single case."""
    case_id = case_def["id"]
    case_name = case_def["name"]
    results = []

    for q_def in case_def["questions"]:
        label = q_def["label"]
        question = q_def["question"]
        options = q_def["options"]
        context = case_def["context"]

        print(f"\n{'='*70}")
        print(f"[{case_id}] {label}")
        print(f"{'='*70}")

        start_time = time.time()

        def on_progress(done, total, _st=start_time):
            elapsed = time.time() - _st
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total - done) / rate if rate > 0 else 0
            print(f"  Progress: {done}/{total} ({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")

        print(f"Running {len(batch)} LLM calls (20 concurrent)...")
        raw_results = ask_agents_batch(batch, question, options, context, on_progress=on_progress)

        responses = []
        api_errors = 0
        for i, result in enumerate(raw_results):
            if result is None:
                result = {"choice": options[0], "reasoning": "error", "probabilities": {}}
            if result.get("reasoning") == "API error":
                api_errors += 1
            result.update(agent_response_meta(agent_dicts[i]))
            responses.append(result)

        elapsed = time.time() - start_time
        print(f"\nCompleted {len(responses)} in {elapsed:.0f}s (API errors: {api_errors})")

        dist = compute_distribution(responses, options)

        # Print results
        print(f"\n--- Results (N={len(responses)}) ---")
        for opt in options:
            short = opt[:60]
            print(f"  {short}: {dist[opt]['count']} ({dist[opt]['pct']:.1f}%) "
                  f"[CI: {dist[opt]['ci_low']}-{dist[opt]['ci_high']}%]")

        # Compare with ground truth if backtest
        gt = case_def.get("ground_truth")
        if gt:
            print(f"\n  Ground Truth ({case_def.get('source', 'N/A')}):")
            for k, v in gt.items():
                print(f"    {k}: {v}%")

        results.append({
            "question": question,
            "label": label,
            "options": options,
            "n": len(responses),
            "elapsed_seconds": round(elapsed),
            "api_errors": api_errors,
            "distribution": {opt: dist[opt] for opt in options},
            "percentages": {opt: dist[opt]["pct"] for opt in options},
            "responses": responses,
        })

    return results


def main():
    print(f"Run All Pending Cases — N={SAMPLE_SIZE}, VS+RP v2.0")
    print(f"Total cases: {len(CASES)}")
    print(f"Started: {datetime.now()}")
    global_start = time.time()

    all_outputs = {}

    for ci, case_def in enumerate(CASES):
        case_id = case_def["id"]
        case_name = case_def["name"]
        print(f"\n\n{'#'*70}")
        print(f"# CASE {ci+1}/{len(CASES)}: {case_id} — {case_name}")
        print(f"{'#'*70}")

        # Determine sample parameters
        age_filter = case_def.get("age_filter")
        case_sample_size = case_def.get("sample_size", SAMPLE_SIZE)
        seed = case_def.get("seed", 42)

        # Sample
        sample, meta = stratified_sample(n=case_sample_size, strata=ADULT_STRATA, seed=seed)

        # Apply age filter if specified
        if age_filter:
            lo, hi = age_filter
            sample = sample[(sample["age"] >= lo) & (sample["age"] <= hi)].head(case_sample_size)
            print(f"Filtered to age {lo}-{hi}: {len(sample)} agents")

        # Prepare batch
        batch = []
        agent_dicts = []
        for i in range(len(sample)):
            agent = sample.iloc[i].to_dict()
            persona = agent_to_persona(agent)
            batch.append((i, agent, persona))
            agent_dicts.append(agent)

        # Run
        results = run_case(case_def, batch, agent_dicts)

        # Save individual output
        output = {
            "timestamp": str(datetime.now()),
            "test": case_id,
            "name": case_name,
            "type": "backtest" if case_def.get("ground_truth") else "survey",
            "method": "VS+RP v2.0",
            "sample_size": len(sample),
            "context": case_def["context"],
            "questions": results,
        }
        if case_def.get("ground_truth"):
            output["ground_truth"] = case_def["ground_truth"]
            output["source"] = case_def.get("source")

        filename = case_id.lower().replace("-", "_")
        outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               "data", "output", f"{filename}.json")
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nSaved: {outpath}")

        all_outputs[case_id] = {
            "name": case_name,
            "n": len(sample),
            "questions": len(results),
            "api_errors": sum(r["api_errors"] for r in results),
        }

    # Final summary
    total_elapsed = time.time() - global_start
    print(f"\n\n{'='*70}")
    print(f"ALL CASES COMPLETE")
    print(f"{'='*70}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print(f"Cases run: {len(all_outputs)}")
    for cid, info in all_outputs.items():
        print(f"  {cid}: {info['name']} — n={info['n']}, {info['questions']}Q, errors={info['api_errors']}")
    print(f"\nFinished: {datetime.now()}")


if __name__ == "__main__":
    main()
