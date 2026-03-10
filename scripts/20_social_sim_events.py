"""
Script 20: Social Simulation — Multi-Event Runner

4 classic social simulation events:
  SIM-002: Mandatory NS for Women
  SIM-003: Wealth Tax on Ultra-Rich ($10M+)
  SIM-004: Abolish PSLE
  SIM-005: Mandatory 4-Day Work Week

Each runs 3 rounds (Day 1 cold → Day 4 peer influence → Day 7 echo chamber).
Reuses the same ABM engine as script 19.

Usage:
    python3 -u scripts/20_social_sim_events.py --event ns_women
    python3 -u scripts/20_social_sim_events.py --event wealth_tax
    python3 -u scripts/20_social_sim_events.py --event abolish_psle
    python3 -u scripts/20_social_sim_events.py --event four_day_week
    python3 -u scripts/20_social_sim_events.py --all
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
# EVENT DEFINITIONS
# ============================================================

EVENTS = {
    "ns_women": {
        "id": "SIM-002",
        "name": "Mandatory National Service for Women",
        "name_zh": "女性强制服兵役",
        "output_file": "sim_ns_women.json",
        "question": (
            "What is this respondent's position on the proposal to extend "
            "mandatory National Service (NS) to women in Singapore?"
        ),
        "options": [
            "Strongly support — gender equality means equal responsibilities",
            "Somewhat support — in principle fair, but needs careful implementation",
            "Neutral / Need more information",
            "Somewhat oppose — women already contribute in other ways, NS is too disruptive",
            "Strongly oppose — NS for women is unnecessary and impractical",
        ],
        "context": (
            "NATIONAL SERVICE FOR WOMEN — SINGAPORE POLICY PROPOSAL:\n\n"

            "CURRENT SITUATION:\n"
            "- All male Singapore Citizens and 2nd-generation PRs must serve 2-year NS (age 18-20).\n"
            "- Women are exempt from NS but can volunteer for SAF/SPF/SCDF careers.\n"
            "- NS obligation includes 10 years of reservist (ICT) duties after full-time service.\n"
            "- About 25,000 males enlist annually. SAF active strength: ~72,000.\n"
            "- Male NS personnel receive $630-$1,200/month allowance (well below civilian wages).\n\n"

            "PROPOSAL UNDER DISCUSSION:\n"
            "- Extend mandatory NS to women, with a 1.5-year service period (vs 2 years for men).\n"
            "- Women would serve in non-combat roles: logistics, medical, communications, cyber, intelligence.\n"
            "- Phased implementation starting 2029.\n"
            "- Option for community/civil defence service as alternative.\n\n"

            "ARGUMENTS FOR:\n"
            "- Gender equality: if men sacrifice 2 years, women should contribute too.\n"
            "- Shrinking population: birth rate 0.97 TFR — need larger defence pool.\n"
            "- Other countries: Israel, Norway, Sweden have women in NS.\n"
            "- Skills training: women gain leadership, technical skills.\n"
            "- National cohesion: shared experience across genders.\n\n"

            "ARGUMENTS AGAINST:\n"
            "- Women already face career penalties (maternity, caregiving) — NS adds another 1.5 years.\n"
            "- May delay marriage and childbirth further in an already low-fertility society.\n"
            "- Physical differences make some roles challenging.\n"
            "- Cost: expanding NS infrastructure for women is expensive.\n"
            "- Disrupts workforce pipeline — Singapore's tight labour market.\n"
            "- Cultural resistance: traditional gender roles still prevalent, especially among older generation.\n\n"

            "SINGAPORE CONTEXT:\n"
            "- NS is deeply personal — every family with sons has experienced the sacrifice.\n"
            "- Common male sentiment: 'Why should women be exempt when we gave 2 years?'\n"
            "- Common female sentiment: 'We already face enough gender-based challenges.'\n"
            "- Government has been cautious, acknowledging this is 'under study.'\n\n"

            "NOTE: Consider the respondent's gender (most directly affected), age (older may be more "
            "conservative), whether they have sons/daughters in NS age range, and personality "
            "(egalitarian vs traditional values). Income and education may also influence views."
        ),
        "peer_quotes": {
            "support": [
                "My son just finished NS. Why should my daughter get a free pass? Equal rights means equal duties.",
                "Norway and Israel do it. Singapore is too small to exclude 50% of the population from defence.",
                "I'm a woman and I support this. We shouldn't hide behind our gender. 1.5 years is manageable.",
            ],
            "oppose": [
                "Women already lose years to pregnancy and childcare. Adding NS will make our birth rate drop to zero.",
                "The SAF can't even properly handle the male NS intake. How will they accommodate 25,000 more women?",
                "This is just vote-buying from angry NS men. Fix NS pay and conditions instead of dragging women in.",
            ],
            "mixed": [
                "I support it in principle, but the timing is terrible with our birth rate crisis.",
                "Maybe voluntary with incentives? Force doesn't work well for social change.",
                "If it's cyber and medical roles with proper career benefits, I could accept it. But not infantry.",
            ],
        },
    },

    "wealth_tax": {
        "id": "SIM-003",
        "name": "Wealth Tax on Ultra-Rich ($10M+)",
        "name_zh": "超高净值富人税（净资产>$1000万）",
        "output_file": "sim_wealth_tax.json",
        "question": (
            "What is this respondent's position on the proposal to introduce "
            "an annual 2% wealth tax on individuals with net assets exceeding $10 million?"
        ),
        "options": [
            "Strongly support — the ultra-rich should pay their fair share",
            "Somewhat support — reasonable if implemented properly with safeguards",
            "Neutral / Need more information",
            "Somewhat oppose — risks driving wealth and talent out of Singapore",
            "Strongly oppose — punishes success and harms Singapore's competitiveness",
        ],
        "context": (
            "WEALTH TAX PROPOSAL — SINGAPORE:\n\n"

            "PROPOSAL:\n"
            "- Annual 2% tax on net assets exceeding $10 million SGD.\n"
            "- Only ~3,500 individuals affected (top 0.06% of residents).\n"
            "- Estimated revenue: $4-6 billion/year.\n"
            "- Applies to all asset classes: property, investments, cash, crypto, art.\n"
            "- Proposed exemptions: primary residence (first $5M), CPF balances.\n\n"

            "CURRENT TAX LANDSCAPE:\n"
            "- Singapore has NO capital gains tax, NO inheritance/estate tax (abolished 2008).\n"
            "- Income tax top rate: 24% (on income above $1M, raised from 22% in 2024).\n"
            "- Property tax: progressive rates up to 36% on non-owner-occupied properties.\n"
            "- Singapore's low-tax regime is a key competitive advantage for attracting wealth.\n"
            "- Family offices: 1,400+ single-family offices managing ~$500B+ in assets.\n\n"

            "ARGUMENTS FOR:\n"
            "- Growing inequality: Gini coefficient 0.433 (after transfers).\n"
            "- Ultra-rich benefit disproportionately from Singapore's stability, infrastructure, and rule of law.\n"
            "- Revenue can fund healthcare for aging population, education, climate adaptation.\n"
            "- Global trend: OECD countries discussing minimum wealth taxes.\n"
            "- Many ultra-rich pay effective tax rates below middle-class workers.\n\n"

            "ARGUMENTS AGAINST:\n"
            "- Capital flight: ultra-rich can relocate to Dubai, Monaco, Hong Kong.\n"
            "- Wealth valuation is complex and gameable (illiquid assets, trusts, offshore structures).\n"
            "- May deter foreign investment and family offices from basing in Singapore.\n"
            "- 'Slippery slope': threshold may lower over time, eventually hitting upper-middle-class.\n"
            "- Singapore's success is built on low taxes — changing the model risks everything.\n"
            "- Administrative cost of valuing and collecting wealth tax is high.\n\n"

            "SINGAPORE CONTEXT:\n"
            "- Housing wealth dominates for most: 70% of HDB owners have majority of net worth in their flat.\n"
            "- Visible inequality: condos next to HDB, luxury cars, Good Class Bungalows.\n"
            "- Public sentiment on inequality has grown — 'cost of living' is top concern.\n"
            "- Government has been cautious, preferring targeted measures (ABSD, property cooling).\n\n"

            "NOTE: Consider the respondent's income and housing type (proxy for wealth), "
            "age (younger may support redistribution, older may fear scope creep), education level "
            "(may understand economic arguments), and personality (egalitarian vs competitive)."
        ),
        "peer_quotes": {
            "support": [
                "3,500 people own more wealth than the bottom million combined. 2% is nothing to them but means hospitals for us.",
                "They abolished estate tax and now wonder why inequality is exploding. Time to fix the mistake.",
                "I'm not jealous — I just want my kids to have a fair shot. Dynastic wealth kills meritocracy.",
            ],
            "oppose": [
                "The rich will just move to Dubai. Then who pays? The rest of us, with higher GST.",
                "Today it's $10M. Next election it's $5M. Then $2M. Then your HDB is 'wealth' too.",
                "Singapore is successful BECAUSE of low taxes. You want to become France?",
            ],
            "mixed": [
                "I'd support it if they ring-fence it for healthcare and education, not general spending.",
                "Make it 1% instead of 2%, and apply it only to financial assets, not property.",
                "The concept is fair but execution in Singapore's open economy is nearly impossible.",
            ],
        },
    },

    "abolish_psle": {
        "id": "SIM-004",
        "name": "Abolish PSLE",
        "name_zh": "废除小六会考（PSLE）",
        "output_file": "sim_abolish_psle.json",
        "question": (
            "What is this respondent's position on the proposal to abolish "
            "the Primary School Leaving Examination (PSLE) and replace it with "
            "school-based assessment?"
        ),
        "options": [
            "Strongly support — PSLE causes excessive stress and should be removed",
            "Somewhat support — needs reform, but school-based assessment is a step forward",
            "Neutral / Need more information",
            "Somewhat oppose — standards will drop without a national exam, inequality may increase",
            "Strongly oppose — PSLE is meritocratic and should be kept as is",
        ],
        "context": (
            "PSLE ABOLITION PROPOSAL — SINGAPORE:\n\n"

            "CURRENT SYSTEM:\n"
            "- PSLE is taken by all students at age 12 (Primary 6).\n"
            "- Results determine secondary school placement (Express, Normal Academic, Normal Technical).\n"
            "- Scoring reformed in 2021: from aggregate T-score to Achievement Level (AL) system (AL1-8).\n"
            "- ~40,000 students sit PSLE annually.\n"
            "- Top schools (RI, Hwa Chong, Nanyang Girls) require AL scores of 6-8.\n\n"

            "PROPOSAL:\n"
            "- Replace PSLE with continuous school-based assessment over Primary 5-6.\n"
            "- Secondary school placement based on portfolio: grades, CCA, teacher assessment.\n"
            "- All students proceed to secondary school without streaming at 12.\n"
            "- Subject-based banding (already introduced) continues.\n\n"

            "ARGUMENTS FOR ABOLISHING:\n"
            "- Extreme stress: tuition industry worth $1.4 billion, children study 7 days/week.\n"
            "- Mental health crisis: increased anxiety and depression among primary school children.\n"
            "- Labelling at 12: 'Express vs Normal' creates lifelong stigma.\n"
            "- Tuition widens inequality: rich families spend $500-2,000/month on tuition.\n"
            "- International trend: Finland (no exams until 16), many countries use continuous assessment.\n"
            "- AL scoring reform in 2021 was a half-measure — the fundamental problem remains.\n\n"

            "ARGUMENTS FOR KEEPING:\n"
            "- Meritocracy: PSLE ensures placement by ability, not connections or wealth.\n"
            "- Standards: without national exam, schools may inflate grades (no accountability).\n"
            "- School-based assessment favours rich kids (better portfolios, better CCAs).\n"
            "- Motivation: some students need exam pressure to perform.\n"
            "- Singapore's education is world-class BECAUSE of rigorous standards.\n"
            "- PSLE is already reformed (AL scoring) — give it time.\n\n"

            "SINGAPORE CONTEXT:\n"
            "- Education is deeply emotional — PSLE stress affects the entire family.\n"
            "- 'Kiasu' culture (fear of losing out) drives intense preparation.\n"
            "- Many parents were shaped by their own PSLE experience.\n"
            "- Government has been gradually reforming (DSA, subject-based banding, AL scores).\n"
            "- Tuition centres are a visible industry — some areas have more tuition centres than shops.\n\n"

            "NOTE: Consider whether the respondent has school-age children or grandchildren, "
            "their education level (university-educated may value meritocracy differently), income "
            "(tuition affordability), age (own PSLE experience), and personality (competitive vs nurturing)."
        ),
        "peer_quotes": {
            "support": [
                "My daughter cries every night doing assessment books. She's TEN. This is child abuse disguised as education.",
                "Finland doesn't have PSLE and they're ranked higher than us. The exam proves nothing.",
                "We spend $2,000/month on tuition. It's an arms race. Remove PSLE and the madness stops.",
            ],
            "oppose": [
                "Without PSLE, rich kids will get into RI through connections and expensive portfolios. How is that fair?",
                "I came from a kampong, scored well in PSLE, and got into a good school. That exam gave me a chance. Don't take it away.",
                "School-based assessment means teacher bias. At least PSLE is blind and objective.",
            ],
            "mixed": [
                "The stress is real, but abolishing PSLE without a good replacement is dangerous.",
                "Maybe make PSLE count for less — 50% PSLE, 50% school-based? Best of both worlds.",
                "Reform the scoring further, reduce the stakes, but keep some national benchmark.",
            ],
        },
    },

    "four_day_week": {
        "id": "SIM-005",
        "name": "Mandatory 4-Day Work Week",
        "name_zh": "强制四天工作制",
        "output_file": "sim_four_day_week.json",
        "question": (
            "What is this respondent's position on the proposal to mandate "
            "a 4-day work week (32 hours) for all companies in Singapore, with no pay reduction?"
        ),
        "options": [
            "Strongly support — better work-life balance and productivity",
            "Somewhat support — good idea for most industries, some exceptions needed",
            "Neutral / Need more information",
            "Somewhat oppose — not practical for Singapore's competitive economy",
            "Strongly oppose — will harm businesses, especially SMEs, and Singapore's edge",
        ],
        "context": (
            "MANDATORY 4-DAY WORK WEEK — SINGAPORE PROPOSAL:\n\n"

            "PROPOSAL:\n"
            "- All companies must offer 4-day work week (32 hours) with no pay reduction by 2028.\n"
            "- Exceptions: essential services (healthcare, transport, security) can offer compressed hours.\n"
            "- Companies can choose which day is off (flexibility).\n"
            "- Overtime rules tightened: >32 hours requires time-and-a-half pay.\n"
            "- 2-year grace period for SMEs (< 50 employees).\n\n"

            "CURRENT SITUATION:\n"
            "- Singapore average work hours: 44.4 hours/week (one of highest in developed world).\n"
            "- Standard work week: 44 hours (Employment Act) or 5.5 days.\n"
            "- Many PMETs work 50+ hours regularly.\n"
            "- MOM Flexible Work Arrangements (FWA) guidelines took effect Dec 2024.\n"
            "- Only ~8% of SG companies currently offer compressed 4-day options.\n\n"

            "ARGUMENTS FOR:\n"
            "- Productivity: UK 4-day week trial (2022) — 92% of companies continued after trial.\n"
            "- Mental health: burnout is severe — 1 in 4 SG workers reported burnout in 2024.\n"
            "- Talent retention: 4-day week is top attraction for young workers.\n"
            "- Birth rate: more time may encourage family formation (TFR 0.97).\n"
            "- Japan, Belgium, Iceland have trialled or legislated 4-day options.\n"
            "- AI and automation reduce the need for long hours.\n\n"

            "ARGUMENTS AGAINST:\n"
            "- Cost: same pay for 20% less hours = significant cost increase for employers.\n"
            "- SME impact: small businesses operate on thin margins, cannot absorb cost.\n"
            "- Competitiveness: Singapore competes with HK, Dubai, Shanghai — all work 5+ day weeks.\n"
            "- Service industries: F&B, retail, logistics need continuous coverage.\n"
            "- Not all jobs can compress: meetings, client-facing roles, manufacturing.\n"
            "- May increase outsourcing and automation, replacing workers entirely.\n"
            "- Global headquarters may relocate if SG mandates shorter hours.\n\n"

            "SINGAPORE CONTEXT:\n"
            "- Work culture is deeply entrenched — 'hardworking' is a national identity.\n"
            "- Many see long hours as necessary for Singapore's success.\n"
            "- Young workers increasingly prioritise work-life balance over career advancement.\n"
            "- Government has been cautious: FWA guidelines are advisory, not mandatory.\n"
            "- MOM view: 'productivity, not hours worked, should determine output.'\n\n"

            "NOTE: Consider the respondent's age (younger strongly favour), income level "
            "(higher income = more flexibility already), job type (PMETs vs hourly workers), "
            "housing (proxy for financial pressure), and personality (work-oriented vs lifestyle-oriented)."
        ),
        "peer_quotes": {
            "support": [
                "I work 50 hours a week and haven't seen my kids awake on a weekday in months. This has to stop.",
                "The UK trial proved it: same output in 4 days, happier workers, companies kept it. What are we afraid of?",
                "No wonder our birth rate is 0.97. People are too exhausted to even go on dates, let alone have kids.",
            ],
            "oppose": [
                "My hawker stall needs to open 6 days. How does a 4-day week work for me? I'll lose customers.",
                "MNCs will just move their Asia HQ to Hong Kong. Then we all lose our jobs.",
                "Same pay for less work? That's not how economics works. Costs go up, prices go up, everyone suffers.",
            ],
            "mixed": [
                "Love the concept, but mandate is too strong. Let companies choose — those who offer it will attract talent.",
                "Maybe 4.5 days as a compromise? Or make it optional with tax incentives?",
                "For office workers, yes. For healthcare, F&B, logistics — it's just not realistic without more hiring.",
            ],
        },
    },
}


# ============================================================
# ABM ENGINE (same as script 19)
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
            f"Government held a press conference responding to public feedback.\n"
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
    sample, meta = stratified_sample(n=N, strata=ADULT_STRATA, seed=50 + hash(event_key) % 100)
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

    # Demographic breakdown
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

    # Sample journeys
    print(f"\nSample Journeys (first 5):")
    for a in agents[:5]:
        d1, d4, d7 = a["day1_score"], a["day4_score"], a["day7_score"]
        tag = "CHANGED" if d1 != d7 else "stable"
        print(f"  [{a.get('age','?')}{a.get('gender','?')} {a.get('housing_type','?')[:15]}] {d1:+d}→{d4:+d}→{d7:+d} ({tag})")

    # === SAVE ===
    # Day 1 and Day 7 distributions
    d1_counter = Counter(a["day1_choice"] for a in agents)
    d7_counter = Counter(a["day7_choice"] for a in agents)

    output = {
        "timestamp": str(datetime.now()),
        "test": ev["id"],
        "name": ev["name"],
        "name_zh": ev["name_zh"],
        "type": "social_simulation",
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=str, choices=list(EVENTS.keys()), help="Event to simulate")
    parser.add_argument("--all", action="store_true", help="Run all 4 events")
    parser.add_argument("--n", type=int, default=200, help="Sample size per event")
    args = parser.parse_args()

    if args.all:
        events_to_run = list(EVENTS.keys())
    elif args.event:
        events_to_run = [args.event]
    else:
        print("Usage: --event <name> or --all")
        print(f"Available events: {', '.join(EVENTS.keys())}")
        return

    print(f"Social Simulation Runner — {len(events_to_run)} events × N={args.n}")
    print(f"Total LLM calls: {len(events_to_run) * 3 * args.n}")
    print(f"Started: {datetime.now()}\n")

    grand_start = time.time()
    for event_key in events_to_run:
        run_simulation(event_key, N=args.n)

    grand_elapsed = time.time() - grand_start
    print(f"\n{'='*70}")
    print(f"ALL SIMULATIONS COMPLETE — {grand_elapsed:.0f}s ({grand_elapsed/60:.1f} min)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
