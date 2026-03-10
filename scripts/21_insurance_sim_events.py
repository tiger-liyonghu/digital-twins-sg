"""
Script 21: Insurance Vertical Social Simulation — 4 Industry Events

SIM-INS-001: IP Portability Reform (penalty-free switching)
SIM-INS-002: CareShield Life Premium Doubling (enhanced long-term care)
SIM-INS-003: Gig Worker Insurance Mandate (platform companies must insure)
SIM-INS-004: Digital-Only Insurer License (no agent channel)

Each runs 3 rounds (Day 1 cold → Day 4 peer influence → Day 7 echo chamber).
Reuses ABM engine from script 20.

Usage:
    python3 -u scripts/21_insurance_sim_events.py --event ip_portability
    python3 -u scripts/21_insurance_sim_events.py --event careshield_hike
    python3 -u scripts/21_insurance_sim_events.py --event gig_insurance
    python3 -u scripts/21_insurance_sim_events.py --event digital_insurer
    python3 -u scripts/21_insurance_sim_events.py --all
    python3 -u scripts/21_insurance_sim_events.py --all --n 500
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import random
import argparse
import statistics
from datetime import datetime
from collections import Counter, defaultdict

from lib.sampling import stratified_sample, ADULT_STRATA
from lib.persona import agent_to_persona, agent_response_meta
from lib.llm import ask_agents_batch
from lib.analysis import compute_distribution

# ============================================================
# INSURANCE VERTICAL EVENT DEFINITIONS
# ============================================================

EVENTS = {
    "ip_portability": {
        "id": "SIM-INS-001",
        "name": "IP Portability Reform — Penalty-Free Switching",
        "name_zh": "综合健保计划无惩罚转保改革",
        "output_file": "sim_ip_portability.json",
        "question": (
            "What is this respondent's position on a proposed MAS regulation that would "
            "allow Integrated Shield Plan (IP) policyholders to switch insurers freely "
            "without any underwriting penalty or waiting period for pre-existing conditions?"
        ),
        "options": [
            "Strongly support — consumers deserve full freedom to switch without penalty",
            "Somewhat support — good idea but needs safeguards against anti-selection",
            "Neutral / Need more information",
            "Somewhat oppose — will destabilize the IP market and raise premiums for everyone",
            "Strongly oppose — current system works, switching without underwriting is unfair",
        ],
        "context": (
            "INTEGRATED SHIELD PLAN (IP) PORTABILITY — SINGAPORE POLICY PROPOSAL:\n\n"

            "CURRENT SITUATION:\n"
            "- Every Singapore citizen/PR has MediShield Life (basic national health insurance).\n"
            "- 7 private insurers offer IP upgrades: AIA, Prudential, Great Eastern, NTUC Income, "
            "Singlife, AXA, Raffles Health Insurance.\n"
            "- ~2.9 million Singaporeans hold IPs (68% of residents).\n"
            "- Current portability rules (since 2018): switching to a new insurer resets "
            "pre-existing condition exclusions. New insurer can impose underwriting penalties.\n"
            "- MAS implemented IP portability framework in 2018, but practical barriers remain.\n"
            "- Average IP premiums rose 8-15% annually from 2020-2025.\n\n"

            "THE PROPOSAL:\n"
            "- Full portability: switch insurers with zero underwriting penalty.\n"
            "- Pre-existing conditions must be covered by the new insurer immediately.\n"
            "- Continuous coverage credit: years of claims-free history transfer.\n"
            "- 30-day free-look period after switching.\n\n"

            "ARGUMENTS FOR:\n"
            "- Consumers currently 'locked in' to expensive IPs due to pre-existing condition risk.\n"
            "- Forces insurers to compete on price and service quality.\n"
            "- Aligned with MAS principle of consumer empowerment.\n"
            "- Similar to mobile number portability — consumers should not be penalized for switching.\n"
            "- Older policyholders most disadvantaged: more pre-existing conditions, highest premiums.\n\n"

            "ARGUMENTS AGAINST:\n"
            "- Anti-selection risk: people may buy cheap IPs when young, switch to premium IPs when sick.\n"
            "- Insurers cannot price risk accurately without underwriting.\n"
            "- May cause 'death spiral': healthy lives cluster in cheap plans, sick lives in premium plans.\n"
            "- Smaller insurers may exit the market, reducing competition.\n"
            "- Administrative complexity: claims history standardization across insurers.\n\n"

            "SINGAPORE CONTEXT:\n"
            "- IP is deeply connected to CPF Medisave (premiums payable from Medisave).\n"
            "- Rider restructuring in 2019 already caused consumer anxiety.\n"
            "- 2024: MAS consulting on further IP reforms.\n"
            "- Strong agent relationships: many consumers trust their agent more than the insurer.\n"
            "- Cultural factor: Singaporeans are generally risk-averse and value stability.\n\n"

            "NOTE: Consider the respondent's age (older = more pre-existing conditions, higher stakes), "
            "income (higher = more options), housing type (proxy for wealth), and gender."
        ),
        "peer_quotes": {
            "support": [
                "I've been paying NTUC Income for 15 years. Their premiums went up 40% but I can't switch because of my knee surgery. How is that fair?",
                "It's like being stuck with a bad phone plan because you're afraid of losing your number. MAS should just make it portable.",
                "My mother is 68, paying $800/month for her IP rider. She would switch tomorrow if she could. This is consumer protection, not anti-selection.",
            ],
            "oppose": [
                "If everyone can switch freely, healthy people will always chase the cheapest plan. Then premiums for the rest of us go through the roof.",
                "Insurance is not like a phone plan — underwriting exists for a reason. You can't just pretend risk doesn't exist.",
                "Small insurers like Raffles Health will die. Then we'll have 3 insurers instead of 7, and prices will be even worse.",
            ],
            "mixed": [
                "I understand the frustration, but maybe partial portability is better — cover pre-existing conditions after 2 years, not immediately.",
                "The real problem is premium transparency, not portability. If insurers had to justify their price increases, we wouldn't need to switch.",
                "Support in principle, but worried about the implementation. Look at what happened when they restructured riders in 2019.",
            ],
        },
    },

    "careshield_hike": {
        "id": "SIM-INS-002",
        "name": "CareShield Life Premium Doubling for Enhanced Coverage",
        "name_zh": "终身护保保费翻倍以提升保障",
        "output_file": "sim_careshield_hike.json",
        "question": (
            "What is this respondent's position on a proposal to double CareShield Life premiums "
            "(from ~$200-600/year to ~$400-1,200/year) in exchange for significantly enhanced "
            "long-term care coverage — including home care, dementia support, and higher monthly payouts?"
        ),
        "options": [
            "Strongly support — long-term care is a crisis, doubling premiums is worth it for proper coverage",
            "Somewhat support — better coverage is needed, but doubling is steep; maybe a smaller increase",
            "Neutral / Need more information",
            "Somewhat oppose — premiums already burden the sandwich generation; find other funding sources",
            "Strongly oppose — government should fund long-term care from reserves, not raise premiums on citizens",
        ],
        "context": (
            "CARESHIELD LIFE ENHANCEMENT — SINGAPORE LONG-TERM CARE PROPOSAL:\n\n"

            "CURRENT SITUATION:\n"
            "- CareShield Life: mandatory national long-term care insurance since 2020.\n"
            "- Replaced ElderShield (2002). All Singaporeans born 1980+ auto-enrolled.\n"
            "- Current payout: $600/month (from 2020, increasing annually) for severe disability.\n"
            "- Premiums: $200-600/year depending on age at entry, payable from Medisave.\n"
            "- Coverage gap: only pays for the most severe disabilities (cannot perform 3+ ADLs).\n"
            "- No coverage for: moderate disability, dementia (unless severely disabling), home care.\n\n"

            "SINGAPORE'S AGING CHALLENGE:\n"
            "- 2025: 1 in 5 Singaporeans aged 65+. By 2030: 1 in 4.\n"
            "- Nursing home costs: $2,000-4,500/month. Home care: $800-2,500/month.\n"
            "- CareShield Life payout ($600/month) covers only 13-30% of actual nursing home costs.\n"
            "- Sandwich generation squeeze: supporting aging parents while raising children.\n"
            "- Domestic helper (for eldercare): ~$800-1,200/month including levy.\n"
            "- Average Medisave balance: $30,000-50,000 (must also cover IP premiums, hospitalization).\n\n"

            "THE PROPOSAL:\n"
            "- Double premiums to provide comprehensive long-term care coverage.\n"
            "- New benefits: home care coverage, dementia support, caregiver respite.\n"
            "- Higher payouts: $1,500/month (vs current $600) for severe disability.\n"
            "- New tier: $800/month for moderate disability (currently not covered).\n"
            "- Still payable from Medisave (but would consume a larger share).\n\n"

            "ARGUMENTS FOR:\n"
            "- $600/month is grossly inadequate for actual care costs.\n"
            "- Preventive home care can delay or prevent nursing home admission.\n"
            "- Dementia affects 1 in 10 seniors; current exclusion is a major gap.\n"
            "- Spreading cost across the population is more efficient than individual savings.\n"
            "- Japan, South Korea, and Germany all have more comprehensive public LTC insurance.\n\n"

            "ARGUMENTS AGAINST:\n"
            "- Doubling premiums strains Medisave accounts already pressured by IP premiums.\n"
            "- Young workers subsidizing elderly care they may not need for 40 years.\n"
            "- Government has $900B+ in reserves — should fund from reserves, not premiums.\n"
            "- Private LTC supplements exist for those who want enhanced coverage.\n"
            "- Moral hazard: comprehensive coverage may reduce family caregiving incentives.\n\n"

            "NOTE: Consider age (older = more immediate relevance), income (affordability), "
            "housing (wealth proxy), ethnicity (cultural attitudes toward family vs institutional care), "
            "and gender (women are disproportionate caregivers)."
        ),
        "peer_quotes": {
            "support": [
                "My father has dementia. $600/month is a joke — his nursing home costs $3,800. I'm draining my savings while CareShield pays for nothing.",
                "Double the premium is fine if it actually covers something useful. We pay more for our car insurance than our parents' long-term care — something is wrong.",
                "Japan spends 2% of GDP on long-term care insurance. We spend 0.3%. This is the richest country in ASEAN — we can afford to do better.",
            ],
            "oppose": [
                "I'm 35, paying IP premiums, mortgage, childcare. Now you want to double my CareShield too? The government has $900 billion in reserves — use that.",
                "My parents took care of their parents at home. That's the Chinese way. I don't need the government to turn everyone into a nursing home case.",
                "Every few years, premiums go up and benefits stay the same. I don't trust that doubling premiums will actually improve anything.",
            ],
            "mixed": [
                "I'd support a 50% increase, not doubling. Phase it in over 5 years so people can adjust.",
                "The coverage gaps are real, but the solution should be means-tested. Why should a condo owner pay the same as an HDB 2-room renter?",
                "Home care coverage is essential — that part I support. But dementia coverage will blow up costs and premiums will keep rising forever.",
            ],
        },
    },

    "gig_insurance": {
        "id": "SIM-INS-003",
        "name": "Mandatory Insurance for Gig Workers",
        "name_zh": "强制为零工工人提供保险",
        "output_file": "sim_gig_insurance.json",
        "question": (
            "What is this respondent's position on a proposed law requiring platform companies "
            "(Grab, foodpanda, Deliveroo, GoJek) to provide basic health insurance and workplace "
            "injury coverage for all gig workers, funded by a 3-5% commission surcharge?"
        ),
        "options": [
            "Strongly support — gig workers deserve the same protection as regular employees",
            "Somewhat support — reasonable safety net, but keep the surcharge small to avoid raising consumer prices",
            "Neutral / Need more information",
            "Somewhat oppose — will raise food delivery costs and reduce gig worker flexibility",
            "Strongly oppose — gig workers chose independence; mandatory insurance undermines the gig model",
        ],
        "context": (
            "GIG WORKER INSURANCE MANDATE — SINGAPORE POLICY PROPOSAL:\n\n"

            "CURRENT SITUATION:\n"
            "- ~80,000 platform workers in Singapore (2024 MOM estimate).\n"
            "- Major platforms: Grab, foodpanda, Deliveroo, GoJek, Lalamove, Ninja Van.\n"
            "- Gig workers classified as 'independent contractors' — no employment benefits.\n"
            "- No employer CPF contribution, no workplace injury insurance, no health coverage.\n"
            "- MAS Advisory Panel on Platform Workers (2023) recommended phased-in protections.\n"
            "- Platform Workers Bill expected 2025-2026.\n\n"

            "GIG WORKER DEMOGRAPHICS:\n"
            "- 60% aged 30-50, 25% aged 50+. 85% male.\n"
            "- 40% do gig work as primary income, 60% as supplementary.\n"
            "- Median gig income: $1,500-2,500/month (full-time riders).\n"
            "- Many have no personal insurance — young riders especially.\n"
            "- Injury rate: ~5x higher than office workers (road accidents, heatstroke).\n\n"

            "THE PROPOSAL:\n"
            "- Platform companies must provide: basic health insurance (outpatient + hospitalization), "
            "workplace injury coverage (including road accidents), and disability income protection.\n"
            "- Funded by 3-5% surcharge on commissions (passed to consumers via higher delivery fees).\n"
            "- Coverage automatic — no opt-out for platforms or workers.\n"
            "- Estimated cost: $80-120/month per active worker.\n\n"

            "ARGUMENTS FOR:\n"
            "- Gig workers face real risks: road accidents, heatstroke, no sick leave.\n"
            "- Platforms profit from worker risk without bearing any cost.\n"
            "- Singapore's social compact: everyone deserves basic protection.\n"
            "- Consumer price impact is small: ~$0.30-0.50 per delivery order.\n"
            "- Other countries (UK, Spain, EU) have moved toward gig worker protections.\n\n"

            "ARGUMENTS AGAINST:\n"
            "- Raises consumer costs, reducing demand and gig worker earnings.\n"
            "- Gig workers value flexibility — mandatory benefits move toward employment relationship.\n"
            "- Platforms may reduce worker rosters to control costs.\n"
            "- Some gig workers already have insurance through other channels.\n"
            "- Administrative burden on small platform companies.\n\n"

            "SINGAPORE CONTEXT:\n"
            "- Strong tripartite (government-employer-union) tradition, but gig workers don't fit neatly.\n"
            "- NTUC trying to organize platform workers through new associations.\n"
            "- Food delivery is a major part of daily life — 4 in 5 Singaporeans order at least weekly.\n"
            "- Cost of living sensitivity: delivery fee increases are politically visible.\n"
            "- Many gig workers are PR/EP holders, not citizens — complicates public sympathy.\n\n"

            "NOTE: Consider age (younger = more likely to use delivery services), income (price sensitivity), "
            "housing (affordability), and whether the respondent might be or know a gig worker."
        ),
        "peer_quotes": {
            "support": [
                "A Grab rider died in an accident last month. No insurance, no CPF, wife and 2 kids left with nothing. This is unacceptable in Singapore.",
                "I order food delivery every day. I'd happily pay $0.50 more per order if it means the uncle delivering my lunch has medical coverage.",
                "Grab made $1.5 billion in revenue last year. They can afford $100/month per worker. Don't tell me that's 'too expensive'.",
            ],
            "oppose": [
                "I'm a Grab driver because I want flexibility. If they start adding mandatory insurance and CPF, they'll treat us like employees — fixed schedules, performance reviews, all that nonsense.",
                "My food delivery already costs $12 with fees. Add another surcharge and I'll just cook at home. Then the riders lose income entirely.",
                "Most riders are doing this part-time for extra cash. They already have insurance from their main job. Why force double coverage?",
            ],
            "mixed": [
                "Support for full-time gig workers, but part-timers should be optional. Don't force insurance on the uncle doing 5 deliveries a week for pocket money.",
                "The principle is right, but 3-5% surcharge will hit lower-income consumers hardest. Make the platforms absorb it from their margins.",
                "Start with workplace injury only — that's the most urgent gap. Health insurance can come later when we see the cost impact.",
            ],
        },
    },

    "digital_insurer": {
        "id": "SIM-INS-004",
        "name": "Digital-Only Insurer License (No Agent Channel)",
        "name_zh": "纯数字保险牌照（无代理人渠道）",
        "output_file": "sim_digital_insurer.json",
        "question": (
            "What is this respondent's position on MAS granting a new category of 'digital-only' "
            "insurance license — where insurers can sell all products online without agents, "
            "promising 30-40% lower premiums by eliminating agent commissions?"
        ),
        "options": [
            "Strongly support — lower premiums benefit everyone; agents are an outdated middleman",
            "Somewhat support — good for simple products, but complex products still need human advice",
            "Neutral / Need more information",
            "Somewhat oppose — most people need guidance to buy insurance; digital-only will lead to poor decisions",
            "Strongly oppose — agents provide essential service; this will destroy 30,000 livelihoods",
        ],
        "context": (
            "DIGITAL-ONLY INSURER LICENSE — SINGAPORE REGULATORY PROPOSAL:\n\n"

            "CURRENT SITUATION:\n"
            "- MAS licenses life insurers under one category — all must maintain agent distribution.\n"
            "- ~30,000 licensed insurance agents in Singapore (down from 35,000 in 2018).\n"
            "- Agent commission: 30-50% of first-year premium (life), 20-30% (health/IP).\n"
            "- MAS Direct Purchase Insurance (DPI) scheme allows buying basic products without agents, "
            "but only 3 product types qualify and take-up is very low (~5% of market).\n"
            "- Digital-first insurers exist (Singlife, FWD) but still use agents for complex products.\n"
            "- Online comparison platforms: MoneyS, SingSaver, Comparefirst.sg.\n\n"

            "THE PROPOSAL:\n"
            "- New license category: 'Digital Insurer' — sell ALL products online.\n"
            "- No agent network required. May use salaried advisors for complex queries.\n"
            "- Must offer 30-40% lower premiums than traditional insurers.\n"
            "- AI chatbots and robo-advisors for needs analysis and product recommendation.\n"
            "- All products available: term life, whole life, CI, IP riders, ILP, endowment.\n"
            "- Claims processed digitally with guaranteed turnaround times.\n\n"

            "ARGUMENTS FOR:\n"
            "- Agent commissions are the largest cost component of insurance — elimination benefits consumers.\n"
            "- Young, digitally savvy generation prefers self-service.\n"
            "- AI advisors can provide objective recommendations (no commission bias).\n"
            "- Banks already sell insurance digitally through bancassurance — why not extend?\n"
            "- Competition will force traditional insurers to reduce commissions too.\n"
            "- Singapore is a digital-first society (98% smartphone penetration, 90%+ digital banking).\n\n"

            "ARGUMENTS AGAINST:\n"
            "- Insurance is complex — most consumers cannot evaluate their own needs accurately.\n"
            "- Agent mis-selling is a problem, but the solution is better regulation, not elimination.\n"
            "- 30,000 agents and their families lose livelihoods — massive social impact.\n"
            "- Digital-only works for simple products, but whole life, ILP, CI need human explanation.\n"
            "- Underinsurance risk: consumers buy cheapest option without understanding coverage gaps.\n"
            "- Elderly and less tech-savvy populations will be left behind.\n"
            "- Claims disputes need human advocacy — chatbots cannot fight for policyholders.\n\n"

            "SINGAPORE CONTEXT:\n"
            "- Insurance agents are a significant employment sector, especially for career changers.\n"
            "- Cultural value of personal relationships in financial decisions.\n"
            "- MAS Balanced Scorecard (2022) already pushing agents toward advisory role.\n"
            "- Singapore's digital banking licenses (2020) showed appetite for disruption.\n"
            "- High insurance penetration: 60%+ of adults have life insurance.\n"
            "- Agent reputation is mixed: trusted advisors vs aggressive sales.\n\n"

            "NOTE: Consider age (younger = more digital-comfortable), income (higher = more self-directed), "
            "education (affects ability to self-research), housing type, and whether respondent might "
            "know or be an insurance agent."
        ),
        "peer_quotes": {
            "support": [
                "My agent keeps pushing me whole life plans because the commission is 50%. A digital insurer would recommend term life at 1/5 the price. The math is clear.",
                "I bought my IP, travel insurance, and term life all online. The only time I talked to an agent was when he cold-called me. I don't need him.",
                "Singapore has digital banks now. Digital insurance is the natural next step. If agents add value, they'll survive. If they don't, why protect them?",
            ],
            "oppose": [
                "My agent helped me restructure my portfolio after my divorce. She understood my situation — no chatbot could do that.",
                "30,000 families depend on this industry. You can't just 'disrupt' people's livelihoods for a 30% discount on a $200/month premium.",
                "My parents are 70. They don't understand insurance jargon in English. Who's going to explain to them in Hokkien through a chatbot?",
            ],
            "mixed": [
                "Digital for term life and travel insurance — sure. But whole life, CI, ILP? I'd still want to talk to a human before committing $500/month for 25 years.",
                "Lower the commission, don't eliminate the agent. Pay agents a flat fee instead of commission. That removes the bias without destroying jobs.",
                "The real question is whether MAS will hold digital insurers to the same claims standards. Selling cheap is easy. Paying claims fairly is what matters.",
            ],
        },
    },
}


# ============================================================
# ABM ENGINE (same as script 20)
# ============================================================

def assign_cluster(agent):
    age = agent.get("age", 30)
    housing = str(agent.get("housing_type", "HDB 4-room"))
    if age < 35:
        age_tier = "young"
    elif age < 55:
        age_tier = "mid"
    else:
        age_tier = "senior"
    h = housing.lower()
    if any(x in h for x in ["condo", "private", "landed", "semi-d", "bungalow", "terrace"]):
        housing_tier = "private"
    elif "5" in h or "executive" in h:
        housing_tier = "hdb_large"
    elif "4" in h:
        housing_tier = "hdb_mid"
    else:
        housing_tier = "hdb_small"
    return f"{housing_tier}_{age_tier}"


def choice_to_score(choice, options):
    for i, opt in enumerate(options):
        if choice == opt:
            return [2, 1, 0, -1, -2][i]
    return 0


def compute_cluster_stats(agents, score_key):
    clusters = defaultdict(list)
    for a in agents:
        clusters[a["cluster"]].append(a[score_key])
    stats = {}
    for c, scores in clusters.items():
        n = len(scores)
        support = sum(1 for s in scores if s > 0)
        oppose = sum(1 for s in scores if s < 0)
        neutral = sum(1 for s in scores if s == 0)
        avg = sum(scores) / n
        stats[c] = {
            "n": n, "avg": round(avg, 2),
            "support_pct": round(support / n * 100),
            "oppose_pct": round(oppose / n * 100),
            "neutral_pct": round(neutral / n * 100),
            "majority": "support" if support > oppose else "oppose" if oppose > support else "mixed",
        }
    return stats


def build_social_context(cluster_stats, cluster_id, day, peer_quotes, event_tag="this proposal"):
    s = cluster_stats[cluster_id]
    rng = random.Random(hash(cluster_id) + day)

    if day == 4:
        majority = s["majority"]
        quote = rng.choice(peer_quotes.get(majority, peer_quotes["mixed"]))
        peer_type = rng.choice(["neighbour", "colleague", "relative", "old classmate"])
        return (
            f"\n\nSOCIAL CONTEXT (Day 4 — you have heard people discussing {event_tag}):\n"
            f"In your social circle, about {s['support_pct']}% support the change, "
            f"{s['oppose_pct']}% oppose it, and {s['neutral_pct']}% are undecided.\n"
            f"A {peer_type} you often talk to said: \"{quote}\"\n"
            f"Several WhatsApp groups and coffee shop conversations have been about this topic."
        )
    elif day == 7:
        majority = s["majority"]
        quotes = peer_quotes.get(majority, peer_quotes["mixed"])
        q1 = rng.choice(quotes)
        if s["support_pct"] > 70:
            echo = "Almost everyone you know supports this proposal."
            counter = ""
        elif s["oppose_pct"] > 70:
            echo = "Almost everyone you know opposes this proposal."
            counter = ""
        else:
            echo = f"Opinions are divided — about {s['support_pct']}% support, {s['oppose_pct']}% oppose."
            minority = "support" if s["majority"] == "oppose" else "oppose"
            counter_quote = rng.choice(peer_quotes.get(minority, peer_quotes["mixed"]))
            counter = f'\nBut you also heard someone say: "{counter_quote}"'
        return (
            f"\n\nSOCIAL CONTEXT (Day 7 — after a full week of public debate):\n"
            f"{echo}\n"
            f"The dominant view around you: \"{q1}\"{counter}\n"
            f"Social media has been intense — trending on TikTok/Reddit/HWZ.\n"
            f"Insurance industry associations and consumer groups have both issued statements.\n"
            f"Some people have changed their minds. Others feel even more strongly.\n"
            f"What is this respondent's position NOW, after a week of discussion and social pressure?"
        )
    return ""


def print_round_results(agents, score_key, round_name):
    scores = [a[score_key] for a in agents]
    total = len(scores)
    dist = Counter(scores)
    print(f"\n--- {round_name} (N={total}) ---")
    labels = [(2, "Strongly support"), (1, "Somewhat support"), (0, "Neutral"),
              (-1, "Somewhat oppose"), (-2, "Strongly oppose")]
    for val, label in labels:
        count = dist.get(val, 0)
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"  {label:<22} {count:>4} ({pct:>5.1f}%) {bar}")
    support = sum(1 for s in scores if s > 0)
    oppose = sum(1 for s in scores if s < 0)
    neutral = sum(1 for s in scores if s == 0)
    print(f"\n  Support: {support/total*100:.1f}% | Neutral: {neutral/total*100:.1f}% | Oppose: {oppose/total*100:.1f}%")


def echo_strength(agents, score_key):
    clusters = defaultdict(list)
    for a in agents:
        clusters[a["cluster"]].append(a[score_key])
    stds = [statistics.stdev(v) for v in clusters.values() if len(v) > 1]
    return statistics.mean(stds) if stds else 0


# ============================================================
# INSURANCE-SPECIFIC ANALYSIS
# ============================================================

def print_insurance_demographics(agents, event_id):
    """Additional demographic breakdowns relevant to insurance vertical."""
    print(f"\nBy Housing × Age (Insurance Relevance):")
    for housing in ["private", "hdb_large", "hdb_mid", "hdb_small"]:
        for age_tier in ["young", "mid", "senior"]:
            cluster = f"{housing}_{age_tier}"
            group = [a for a in agents if a["cluster"] == cluster]
            if len(group) < 3:
                continue
            s1 = sum(1 for a in group if a["day1_score"] > 0) / len(group) * 100
            s7 = sum(1 for a in group if a["day7_score"] > 0) / len(group) * 100
            shift = s7 - s1
            sign = "+" if shift >= 0 else ""
            print(f"  {cluster:<20} (n={len(group):>3}): Support {s1:>5.1f}%→{s7:>5.1f}% ({sign}{shift:.1f}pp)")

    # Income-based analysis (insurance is highly income-correlated)
    print(f"\nBy Income Band:")
    inc_bins = {"<$3K": (0, 2999), "$3K-$5K": (3000, 4999),
                "$5K-$8K": (5000, 7999), "$8K+": (8000, 999999)}
    for label, (lo, hi) in inc_bins.items():
        group = [a for a in agents if lo <= (a.get("monthly_income") or a.get("income", 0) or 0) <= hi]
        if len(group) < 3:
            continue
        s1 = sum(1 for a in group if a["day1_score"] > 0) / len(group) * 100
        s7 = sum(1 for a in group if a["day7_score"] > 0) / len(group) * 100
        o7 = sum(1 for a in group if a["day7_score"] < 0) / len(group) * 100
        print(f"  {label:<10} (n={len(group):>3}): Support {s1:.0f}%→{s7:.0f}% | Oppose {o7:.0f}%")

    # Ethnicity (insurance purchase patterns differ by ethnic group)
    print(f"\nBy Ethnicity:")
    for eth in ["Chinese", "Malay", "Indian"]:
        group = [a for a in agents if a.get("ethnicity") == eth]
        if len(group) < 3:
            continue
        s1 = sum(1 for a in group if a["day1_score"] > 0) / len(group) * 100
        s7 = sum(1 for a in group if a["day7_score"] > 0) / len(group) * 100
        print(f"  {eth:<10} (n={len(group):>3}): Support {s1:.0f}%→{s7:.0f}%")


# ============================================================
# RUN ONE SIMULATION
# ============================================================

def run_simulation(event_key, N=200):
    ev = EVENTS[event_key]
    print(f"\n{'#'*70}")
    print(f"# {ev['id']}: {ev['name']}")
    print(f"# N={N}, 3 rounds × {N} = {3*N} LLM calls")
    print(f"{'#'*70}")
    print(f"Started: {datetime.now()}\n")

    # Sample
    print("Sampling agents (stratified)...")
    sample, meta = stratified_sample(n=N, strata=ADULT_STRATA, seed=100 + hash(event_key) % 100)
    sample = sample.head(N)
    print(f"Sampled: {len(sample)} agents")

    # Assign clusters
    agents = []
    for i in range(len(sample)):
        a = sample.iloc[i].to_dict()
        a["cluster"] = assign_cluster(a)
        a["persona_base"] = agent_to_persona(a)
        agents.append(a)

    cluster_counts = Counter(a["cluster"] for a in agents)
    print(f"\nClusters ({len(cluster_counts)}):")
    for c, n in sorted(cluster_counts.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")

    total_start = time.time()
    OPTIONS = ev["options"]
    CONTEXT = ev["context"]
    QUESTION = ev["question"]

    def on_progress(done, total):
        elapsed = time.time() - start
        eta = (total - done) / (done / elapsed) if done > 0 else 0
        print(f"  Progress: {done}/{total} ({elapsed:.0f}s, ETA {eta:.0f}s)")

    # === ROUND 1 — Day 1 ===
    print(f"\n{'='*70}")
    print(f"ROUND 1 — Day 1: Cold Reaction")
    print(f"{'='*70}")
    start = time.time()

    batch_r1 = [(i, agents[i], agents[i]["persona_base"]) for i in range(len(agents))]
    results_r1 = ask_agents_batch(batch_r1, QUESTION, OPTIONS, CONTEXT, on_progress=on_progress)

    for i, r in enumerate(results_r1):
        if r is None:
            r = {"choice": OPTIONS[2], "reasoning": "error"}
        agents[i]["day1_choice"] = r["choice"]
        agents[i]["day1_score"] = choice_to_score(r["choice"], OPTIONS)
        agents[i]["day1_reasoning"] = r.get("reasoning", "")

    print(f"Round 1 completed in {time.time() - start:.0f}s")
    print_round_results(agents, "day1_score", "Day 1")
    cluster_stats_d1 = compute_cluster_stats(agents, "day1_score")

    # === ROUND 2 — Day 4 ===
    print(f"\n{'='*70}")
    print(f"ROUND 2 — Day 4: Peer Influence")
    print(f"{'='*70}")
    start = time.time()

    batch_r2 = []
    for i, a in enumerate(agents):
        social_ctx = build_social_context(cluster_stats_d1, a["cluster"], 4, ev["peer_quotes"], ev["name"])
        batch_r2.append((i, a, a["persona_base"] + social_ctx))

    results_r2 = ask_agents_batch(batch_r2, QUESTION, OPTIONS, CONTEXT, on_progress=on_progress)

    for i, r in enumerate(results_r2):
        if r is None:
            r = {"choice": OPTIONS[2], "reasoning": "error"}
        agents[i]["day4_choice"] = r["choice"]
        agents[i]["day4_score"] = choice_to_score(r["choice"], OPTIONS)
        agents[i]["day4_reasoning"] = r.get("reasoning", "")

    print(f"Round 2 completed in {time.time() - start:.0f}s")
    print_round_results(agents, "day4_score", "Day 4")
    cluster_stats_d4 = compute_cluster_stats(agents, "day4_score")

    # === ROUND 3 — Day 7 ===
    print(f"\n{'='*70}")
    print(f"ROUND 3 — Day 7: Echo Chamber")
    print(f"{'='*70}")
    start = time.time()

    batch_r3 = []
    for i, a in enumerate(agents):
        social_ctx = build_social_context(cluster_stats_d4, a["cluster"], 7, ev["peer_quotes"], ev["name"])
        batch_r3.append((i, a, a["persona_base"] + social_ctx))

    results_r3 = ask_agents_batch(batch_r3, QUESTION, OPTIONS, CONTEXT, on_progress=on_progress)

    for i, r in enumerate(results_r3):
        if r is None:
            r = {"choice": OPTIONS[2], "reasoning": "error"}
        agents[i]["day7_choice"] = r["choice"]
        agents[i]["day7_score"] = choice_to_score(r["choice"], OPTIONS)
        agents[i]["day7_reasoning"] = r.get("reasoning", "")

    print(f"Round 3 completed in {time.time() - start:.0f}s")
    print_round_results(agents, "day7_score", "Day 7")
    cluster_stats_d7 = compute_cluster_stats(agents, "day7_score")

    # === ANALYSIS ===
    total_elapsed = time.time() - total_start
    d1_scores = [a["day1_score"] for a in agents]
    d7_scores = [a["day7_score"] for a in agents]
    changed_total = sum(1 for i in range(len(agents)) if d1_scores[i] != d7_scores[i])

    support_d1 = sum(1 for s in d1_scores if s > 0) / len(agents) * 100
    oppose_d1 = sum(1 for s in d1_scores if s < 0) / len(agents) * 100
    support_d7 = sum(1 for s in d7_scores if s > 0) / len(agents) * 100
    oppose_d7 = sum(1 for s in d7_scores if s < 0) / len(agents) * 100

    pol_d1 = statistics.stdev(d1_scores) if len(d1_scores) > 1 else 0
    pol_d7 = statistics.stdev(d7_scores) if len(d7_scores) > 1 else 0
    echo_d1 = echo_strength(agents, "day1_score")
    echo_d7 = echo_strength(agents, "day7_score")

    print(f"\n{'='*70}")
    print(f"SUMMARY — {ev['name']}")
    print(f"{'='*70}")
    print(f"  N = {len(agents)}, {3*len(agents)} LLM calls, {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")
    print(f"  Day 1: Support {support_d1:.1f}% | Oppose {oppose_d1:.1f}%")
    print(f"  Day 7: Support {support_d7:.1f}% | Oppose {oppose_d7:.1f}%")
    print(f"  Changed: {changed_total}/{len(agents)} ({changed_total/len(agents)*100:.1f}%)")
    print(f"  Polarization: {pol_d1:.3f} → {pol_d7:.3f}")

    # Standard demographic breakdowns
    print(f"\nBy Gender:")
    for g in ["M", "F"]:
        group = [a for a in agents if a.get("gender") == g]
        if group:
            s1 = sum(1 for a in group if a["day1_score"] > 0) / len(group) * 100
            s7 = sum(1 for a in group if a["day7_score"] > 0) / len(group) * 100
            o7 = sum(1 for a in group if a["day7_score"] < 0) / len(group) * 100
            print(f"  {g} (n={len(group)}): Support {s1:.0f}%→{s7:.0f}% | Day7 Oppose {o7:.0f}%")

    print(f"\nBy Age:")
    for label, (lo, hi) in {"18-34": (18, 34), "35-54": (35, 54), "55+": (55, 100)}.items():
        group = [a for a in agents if lo <= a.get("age", 30) <= hi]
        if group:
            s1 = sum(1 for a in group if a["day1_score"] > 0) / len(group) * 100
            s7 = sum(1 for a in group if a["day7_score"] > 0) / len(group) * 100
            print(f"  {label} (n={len(group)}): Support {s1:.0f}%→{s7:.0f}%")

    # Insurance-specific demographics
    print_insurance_demographics(agents, ev["id"])

    # Sample journeys
    print(f"\nSample Journeys (first 5):")
    for a in agents[:5]:
        d1, d4, d7 = a["day1_score"], a["day4_score"], a["day7_score"]
        tag = "CHANGED" if d1 != d7 else "stable"
        print(f"  [{a.get('age','?')}{a.get('gender','?')} {str(a.get('housing_type','?'))[:15]}] {d1:+d}→{d4:+d}→{d7:+d} ({tag})")

    # === SAVE ===
    d1_counter = Counter(a["day1_choice"] for a in agents)
    d7_counter = Counter(a["day7_choice"] for a in agents)

    output = {
        "timestamp": str(datetime.now()),
        "test": ev["id"],
        "name": ev["name"],
        "name_zh": ev["name_zh"],
        "type": "insurance_simulation",
        "method": "VS+RP v2.0 + Multi-Round ABM",
        "sample_size": len(agents),
        "rounds": 3,
        "total_llm_calls": 3 * len(agents),
        "elapsed_seconds": round(total_elapsed),
        "event": ev["name"],
        "question": QUESTION,
        "options": OPTIONS,
        "context_day1": CONTEXT,
        "day1_distribution": {opt: round(d1_counter.get(opt, 0) / len(agents) * 100, 1) for opt in OPTIONS},
        "day7_distribution": {opt: round(d7_counter.get(opt, 0) / len(agents) * 100, 1) for opt in OPTIONS},
        "summary": {
            "day1_support_pct": round(support_d1, 1),
            "day1_oppose_pct": round(oppose_d1, 1),
            "day7_support_pct": round(support_d7, 1),
            "day7_oppose_pct": round(oppose_d7, 1),
            "opinion_changed_pct": round(changed_total / len(agents) * 100, 1),
            "polarization_d1": round(pol_d1, 3),
            "polarization_d7": round(pol_d7, 3),
            "echo_chamber_d1": round(echo_d1, 3),
            "echo_chamber_d7": round(echo_d7, 3),
            "mean_score_d1": round(statistics.mean(d1_scores), 3),
            "mean_score_d7": round(statistics.mean(d7_scores), 3),
        },
        "cluster_evolution": {
            c: {
                "n": cluster_stats_d1[c]["n"],
                "day1_avg": cluster_stats_d1[c]["avg"],
                "day4_avg": cluster_stats_d4[c]["avg"],
                "day7_avg": cluster_stats_d7[c]["avg"],
            }
            for c in sorted(cluster_stats_d1.keys())
        },
        "agents": [
            {
                "age": a.get("age"), "gender": a.get("gender"),
                "ethnicity": a.get("ethnicity"), "housing": a.get("housing_type"),
                "income": a.get("monthly_income"), "cluster": a["cluster"],
                "day1_score": a["day1_score"], "day4_score": a["day4_score"], "day7_score": a["day7_score"],
                "day1_choice": a["day1_choice"], "day7_choice": a["day7_choice"],
                "day1_reasoning": a.get("day1_reasoning", ""),
                "day7_reasoning": a.get("day7_reasoning", ""),
                "changed": a["day1_score"] != a["day7_score"],
            }
            for a in agents
        ],
    }

    outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output", ev["output_file"])
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved: {outpath}")
    print(f"Finished: {datetime.now()}")
    return output


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Insurance Vertical Social Simulation")
    parser.add_argument("--event", type=str, choices=list(EVENTS.keys()), help="Event to simulate")
    parser.add_argument("--all", action="store_true", help="Run all 4 insurance events")
    parser.add_argument("--n", type=int, default=200, help="Sample size per event")
    args = parser.parse_args()

    if args.all:
        events_to_run = list(EVENTS.keys())
    elif args.event:
        events_to_run = [args.event]
    else:
        print("Insurance Vertical Social Simulation Runner")
        print("Usage: --event <name> or --all")
        print(f"Available events: {', '.join(EVENTS.keys())}")
        for k, v in EVENTS.items():
            print(f"  {k:<20} {v['id']}: {v['name']}")
        return

    print(f"Insurance Vertical Simulation — {len(events_to_run)} events × N={args.n}")
    print(f"Total LLM calls: {len(events_to_run) * 3 * args.n}")
    print(f"Started: {datetime.now()}\n")

    grand_start = time.time()
    for event_key in events_to_run:
        run_simulation(event_key, N=args.n)

    grand_elapsed = time.time() - grand_start
    print(f"\n{'='*70}")
    print(f"ALL INSURANCE SIMULATIONS COMPLETE — {grand_elapsed:.0f}s ({grand_elapsed/60:.1f} min)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
