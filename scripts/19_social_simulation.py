"""
Script 19: 7-Day Social Simulation — CPF Withdrawal Age (55 → 60)

Multi-round agent-based model with information propagation.

Round 1 (Day 1): Cold reaction — agents see raw news, no peer influence
Round 2 (Day 4): Peer influence — cluster majority opinion injected
Round 3 (Day 7): Echo chamber — strong social pressure + national trend

Captures: word-of-mouth, echo chambers, opinion shifts

Usage:
    python3 -u scripts/19_social_simulation.py [--n 200]
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import random
import argparse
from datetime import datetime
from collections import Counter, defaultdict

from lib.sampling import stratified_sample, ADULT_STRATA
from lib.persona import agent_to_persona, agent_response_meta
from lib.llm import ask_agents_batch
from lib.analysis import compute_distribution

# === Event ===
EVENT_NAME = "CPF Withdrawal Age: 55 → 60"
EVENT_NAME_ZH = "CPF提取年龄从55提至60"

QUESTION = (
    "What is this respondent's position on the government's proposal "
    "to raise the CPF Ordinary Account withdrawal age from 55 to 60?"
)

OPTIONS = [
    "Strongly support — longer accumulation ensures better retirement",
    "Somewhat support — makes sense given longer life expectancy",
    "Neutral / Need more information",
    "Somewhat oppose — unfair to those planning around age 55",
    "Strongly oppose — government should not move the goalposts on our CPF",
]

# === Round 1 Context: Just objective facts ===
CONTEXT_DAY1 = (
    "CPF WITHDRAWAL AGE PROPOSAL — SINGAPORE, MARCH 2026:\n\n"

    "WHAT IS PROPOSED:\n"
    "- The government has announced it is studying raising the CPF Ordinary Account "
    "withdrawal age from 55 to 60, with a 3-year transition period starting 2028.\n"
    "- Currently, CPF members can withdraw OA savings at 55 (after setting aside the "
    "Full Retirement Sum or Basic Retirement Sum).\n"
    "- CPF LIFE monthly payouts would continue to start at age 65.\n\n"

    "GOVERNMENT'S RATIONALE:\n"
    "- Life expectancy in Singapore: 84.8 years (up from 78.0 in 2000).\n"
    "- Many Singaporeans outlive their retirement savings.\n"
    "- Longer accumulation period → higher CPF LIFE payouts.\n"
    "- Aligns with trend of Singaporeans working longer (re-employment age raised to 68).\n"
    "- About 20% of CPF members withdraw significant OA savings at age 55.\n\n"

    "CONCERNS RAISED:\n"
    "- 'CPF is our money' — frustration that government controls withdrawal timing.\n"
    "- Workers in physically demanding jobs may not be able to work until 60.\n"
    "- Some planned to use CPF OA at 55 to pay off HDB loan or fund children's education.\n"
    "- Previous CPF changes (Minimum Sum increases) eroded public trust.\n"
    "- Lower-income workers may need the cash more urgently.\n\n"

    "CPF FACTS:\n"
    "- Contribution rate: 37% of wages (20% employee + 17% employer) for age <55.\n"
    "- Average OA balance at 55: ~$180,000.\n"
    "- CPF can be used for housing (OA), healthcare (MediSave), retirement (SA/RA).\n"
    "- Full Retirement Sum (2025): $213,000.\n\n"

    "NOTE: Consider the respondent's age (directly affects when they can access CPF), "
    "income level (higher income = larger CPF balance), housing status (HDB owners may "
    "rely on CPF for retirement), and personality (risk-averse may support, skeptical "
    "may oppose government control)."
)

# Peer quotes by sentiment
PEER_QUOTES = {
    "support": [
        "We're living longer — if we withdraw at 55 and live to 90, that's 35 years of retirement to fund.",
        "I'd rather have a bigger CPF LIFE payout at 65. Five more years of compounding makes a big difference.",
        "Look at Japan and Korea — their elderly poverty rates are terrible. This protects us.",
    ],
    "oppose": [
        "They keep moving the goalposts. First Minimum Sum, now this. When will it end?",
        "My father was a hawker — you think he could work until 60? Not everyone sits in aircon office.",
        "It's OUR money. If I want to take it out at 55 to help my kids with their BTO, that's my right.",
    ],
    "mixed": [
        "I can see the logic, but they need to exempt people in physically demanding jobs.",
        "Maybe 58 as a compromise? 60 feels too much too fast.",
        "I'm okay with it IF they increase CPF returns from 2.5% to at least 4%.",
    ],
}


def assign_cluster(agent):
    """Assign agent to a demographic cluster based on housing × age tier."""
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


def choice_to_score(choice):
    """Map option text to opinion score: +2 to -2."""
    for i, opt in enumerate(OPTIONS):
        if choice == opt:
            return [2, 1, 0, -1, -2][i]
    return 0


def score_to_label(score):
    if score > 0:
        return "support"
    elif score < 0:
        return "oppose"
    return "neutral"


def compute_cluster_stats(agents, score_key):
    """Compute opinion stats per cluster."""
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
            "n": n,
            "avg": round(avg, 2),
            "support_pct": round(support / n * 100),
            "oppose_pct": round(oppose / n * 100),
            "neutral_pct": round(neutral / n * 100),
            "majority": "support" if support > oppose else "oppose" if oppose > support else "mixed",
        }
    return stats


def build_social_context(cluster_stats, cluster_id, day):
    """Build per-agent social context string for Day 4 or Day 7."""
    s = cluster_stats[cluster_id]
    rng = random.Random(hash(cluster_id) + day)

    if day == 4:
        # Day 4: heard from peers in your circle
        majority = s["majority"]
        quote = rng.choice(PEER_QUOTES.get(majority, PEER_QUOTES["mixed"]))
        peer_type = rng.choice(["neighbour", "colleague", "relative", "old classmate"])

        return (
            f"\n\nSOCIAL CONTEXT (Day 4 — you have heard people discussing this):\n"
            f"In your social circle, about {s['support_pct']}% support the change, "
            f"{s['oppose_pct']}% oppose it, and {s['neutral_pct']}% are undecided.\n"
            f"A {peer_type} you often talk to said: \"{quote}\"\n"
            f"Several WhatsApp groups and coffee shop conversations have been about this topic."
        )

    elif day == 7:
        # Day 7: strong echo chamber + national trend
        majority = s["majority"]
        quotes = PEER_QUOTES.get(majority, PEER_QUOTES["mixed"])
        q1 = rng.choice(quotes)
        # Add a counter-opinion for mixed clusters
        if s["support_pct"] > 70:
            echo = "Almost everyone you know supports this change."
            counter = ""
        elif s["oppose_pct"] > 70:
            echo = "Almost everyone you know is against this change."
            counter = ""
        else:
            echo = f"Opinions are divided — about {s['support_pct']}% support, {s['oppose_pct']}% oppose."
            minority = "support" if s["majority"] == "oppose" else "oppose"
            counter_quote = rng.choice(PEER_QUOTES.get(minority, PEER_QUOTES["mixed"]))
            counter = f'\nBut you also heard someone say: "{counter_quote}"'

        return (
            f"\n\nSOCIAL CONTEXT (Day 7 — after a full week of public debate):\n"
            f"{echo}\n"
            f"The dominant view around you: \"{q1}\"{counter}\n"
            f"Social media has been intense — #CPF55 trending on TikTok/Reddit.\n"
            f"Government held a press conference reaffirming the proposal with 'flexibility provisions'.\n"
            f"Some people have changed their minds. Others feel even more strongly than before.\n"
            f"What is this respondent's position NOW, after a week of discussion and social pressure?"
        )

    return ""


def print_round_results(agents, score_key, round_name):
    """Print distribution for a round."""
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


def print_cluster_evolution(agents, clusters_stats_d1, clusters_stats_d4, clusters_stats_d7):
    """Show how each cluster's opinion evolved."""
    print(f"\n{'='*70}")
    print("ECHO CHAMBER ANALYSIS — Cluster Opinion Evolution")
    print(f"{'='*70}")
    print(f"  {'Cluster':<25} {'Day 1':>12} {'Day 4':>12} {'Day 7':>12} {'Shift':>8}")
    print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*12} {'-'*8}")

    for c in sorted(clusters_stats_d1.keys()):
        d1 = clusters_stats_d1[c]
        d4 = clusters_stats_d4[c]
        d7 = clusters_stats_d7[c]
        shift = d7["avg"] - d1["avg"]
        direction = "→support" if shift > 0.3 else "→oppose" if shift < -0.3 else "stable"
        print(f"  {c:<25} {d1['avg']:>+6.2f} (n={d1['n']:<3}) {d4['avg']:>+6.2f}       {d7['avg']:>+6.2f}       {direction}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200, help="Sample size")
    args = parser.parse_args()
    N = args.n

    print(f"7-Day Social Simulation: {EVENT_NAME}")
    print(f"N={N}, 3 rounds × {N} = {3*N} LLM calls")
    print(f"Started: {datetime.now()}")
    print()

    # === SAMPLE ===
    print("Sampling agents (stratified)...")
    sample, meta = stratified_sample(n=N, strata=ADULT_STRATA, seed=50)
    sample = sample.head(N)
    print(f"Sampled: {len(sample)} agents")

    # === ASSIGN CLUSTERS ===
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

    # ================================================================
    # ROUND 1 — Day 1: Cold Reaction (no peer influence)
    # ================================================================
    print(f"\n{'='*70}")
    print("ROUND 1 — Day 1: Media Exposure (Cold Reaction)")
    print(f"{'='*70}")

    start = time.time()

    def on_progress(done, total):
        elapsed = time.time() - start
        eta = (total - done) / (done / elapsed) if done > 0 else 0
        print(f"  Progress: {done}/{total} ({elapsed:.0f}s, ETA {eta:.0f}s)")

    batch_r1 = [(i, agents[i], agents[i]["persona_base"]) for i in range(len(agents))]
    results_r1 = ask_agents_batch(batch_r1, QUESTION, OPTIONS, CONTEXT_DAY1, on_progress=on_progress)

    for i, r in enumerate(results_r1):
        if r is None:
            r = {"choice": OPTIONS[2], "reasoning": "error"}
        agents[i]["day1_choice"] = r["choice"]
        agents[i]["day1_score"] = choice_to_score(r["choice"])
        agents[i]["day1_reasoning"] = r.get("reasoning", "")

    elapsed_r1 = time.time() - start
    print(f"Round 1 completed in {elapsed_r1:.0f}s")
    print_round_results(agents, "day1_score", "Day 1 — Cold Reaction")

    # Compute cluster stats after Day 1
    cluster_stats_d1 = compute_cluster_stats(agents, "day1_score")

    print("\nCluster opinions after Day 1:")
    for c in sorted(cluster_stats_d1.keys()):
        s = cluster_stats_d1[c]
        print(f"  {c:<25} avg={s['avg']:>+.2f}  support={s['support_pct']}%  oppose={s['oppose_pct']}%  [{s['majority']}]")

    # ================================================================
    # ROUND 2 — Day 4: Peer Influence (word of mouth)
    # ================================================================
    print(f"\n{'='*70}")
    print("ROUND 2 — Day 4: Peer Influence (Word of Mouth)")
    print(f"{'='*70}")

    start = time.time()

    # Build per-agent persona with social context
    batch_r2 = []
    for i, a in enumerate(agents):
        social_ctx = build_social_context(cluster_stats_d1, a["cluster"], day=4)
        persona_r2 = a["persona_base"] + social_ctx
        batch_r2.append((i, a, persona_r2))

    results_r2 = ask_agents_batch(batch_r2, QUESTION, OPTIONS, CONTEXT_DAY1, on_progress=on_progress)

    for i, r in enumerate(results_r2):
        if r is None:
            r = {"choice": OPTIONS[2], "reasoning": "error"}
        agents[i]["day4_choice"] = r["choice"]
        agents[i]["day4_score"] = choice_to_score(r["choice"])
        agents[i]["day4_reasoning"] = r.get("reasoning", "")

    elapsed_r2 = time.time() - start
    print(f"Round 2 completed in {elapsed_r2:.0f}s")
    print_round_results(agents, "day4_score", "Day 4 — After Peer Influence")

    cluster_stats_d4 = compute_cluster_stats(agents, "day4_score")

    # Show shifts from Day 1 → Day 4
    d1_scores = [a["day1_score"] for a in agents]
    d4_scores = [a["day4_score"] for a in agents]
    changed_d4 = sum(1 for i in range(len(agents)) if d1_scores[i] != d4_scores[i])
    print(f"\n  Opinion changed Day1→Day4: {changed_d4}/{len(agents)} ({changed_d4/len(agents)*100:.1f}%)")

    moved_support = sum(1 for i in range(len(agents)) if d4_scores[i] > d1_scores[i])
    moved_oppose = sum(1 for i in range(len(agents)) if d4_scores[i] < d1_scores[i])
    print(f"  Moved toward support: {moved_support} | Moved toward oppose: {moved_oppose}")

    # ================================================================
    # ROUND 3 — Day 7: Echo Chamber + Final Decision
    # ================================================================
    print(f"\n{'='*70}")
    print("ROUND 3 — Day 7: Echo Chamber + Final Decision")
    print(f"{'='*70}")

    start = time.time()

    batch_r3 = []
    for i, a in enumerate(agents):
        social_ctx = build_social_context(cluster_stats_d4, a["cluster"], day=7)
        persona_r3 = a["persona_base"] + social_ctx
        batch_r3.append((i, a, persona_r3))

    results_r3 = ask_agents_batch(batch_r3, QUESTION, OPTIONS, CONTEXT_DAY1, on_progress=on_progress)

    for i, r in enumerate(results_r3):
        if r is None:
            r = {"choice": OPTIONS[2], "reasoning": "error"}
        agents[i]["day7_choice"] = r["choice"]
        agents[i]["day7_score"] = choice_to_score(r["choice"])
        agents[i]["day7_reasoning"] = r.get("reasoning", "")

    elapsed_r3 = time.time() - start
    print(f"Round 3 completed in {elapsed_r3:.0f}s")
    print_round_results(agents, "day7_score", "Day 7 — Final Position (Echo Chamber)")

    cluster_stats_d7 = compute_cluster_stats(agents, "day7_score")

    # ================================================================
    # ANALYSIS — Opinion Dynamics
    # ================================================================
    print(f"\n{'='*70}")
    print("OPINION DYNAMICS ANALYSIS")
    print(f"{'='*70}")

    # 1. Overall shift
    d7_scores = [a["day7_score"] for a in agents]
    changed_total = sum(1 for i in range(len(agents)) if d1_scores[i] != d7_scores[i])
    print(f"\n  Total opinion changed Day1→Day7: {changed_total}/{len(agents)} ({changed_total/len(agents)*100:.1f}%)")

    moved_support_total = sum(1 for i in range(len(agents)) if d7_scores[i] > d1_scores[i])
    moved_oppose_total = sum(1 for i in range(len(agents)) if d7_scores[i] < d1_scores[i])
    print(f"  Net movement: {moved_support_total} toward support, {moved_oppose_total} toward oppose")

    # 2. Polarization index (std dev of scores)
    import statistics
    pol_d1 = statistics.stdev(d1_scores) if len(d1_scores) > 1 else 0
    pol_d7 = statistics.stdev(d7_scores) if len(d7_scores) > 1 else 0
    print(f"\n  Polarization (σ): Day 1 = {pol_d1:.3f} → Day 7 = {pol_d7:.3f} ({'↑ increased' if pol_d7 > pol_d1 else '↓ decreased'})")

    # 3. Echo chamber strength (average within-cluster std dev)
    def echo_strength(agents, score_key):
        clusters = defaultdict(list)
        for a in agents:
            clusters[a["cluster"]].append(a[score_key])
        stds = [statistics.stdev(v) for v in clusters.values() if len(v) > 1]
        return statistics.mean(stds) if stds else 0

    echo_d1 = echo_strength(agents, "day1_score")
    echo_d7 = echo_strength(agents, "day7_score")
    print(f"  Echo chamber (within-cluster σ): Day 1 = {echo_d1:.3f} → Day 7 = {echo_d7:.3f} ({'↓ stronger echo' if echo_d7 < echo_d1 else '↑ weaker echo'})")

    # 4. Cluster evolution
    print_cluster_evolution(agents, cluster_stats_d1, cluster_stats_d4, cluster_stats_d7)

    # 5. Demographic breakdown of shifts
    print(f"\n{'='*70}")
    print("OPINION SHIFT BY DEMOGRAPHICS")
    print(f"{'='*70}")

    # By age group
    age_bins = {"18-34": (18, 34), "35-54": (35, 54), "55+": (55, 100)}
    for label, (lo, hi) in age_bins.items():
        group = [a for a in agents if lo <= a.get("age", 30) <= hi]
        if not group:
            continue
        d1_sup = sum(1 for a in group if a["day1_score"] > 0) / len(group) * 100
        d7_sup = sum(1 for a in group if a["day7_score"] > 0) / len(group) * 100
        d1_opp = sum(1 for a in group if a["day1_score"] < 0) / len(group) * 100
        d7_opp = sum(1 for a in group if a["day7_score"] < 0) / len(group) * 100
        shift = d7_sup - d1_sup
        print(f"  Age {label} (n={len(group)}): Support {d1_sup:.0f}%→{d7_sup:.0f}% ({shift:+.0f}pp) | Oppose {d1_opp:.0f}%→{d7_opp:.0f}%")

    # By housing
    for ht in ["private", "hdb_large", "hdb_mid", "hdb_small"]:
        group = [a for a in agents if a["cluster"].startswith(ht)]
        if not group:
            continue
        d1_sup = sum(1 for a in group if a["day1_score"] > 0) / len(group) * 100
        d7_sup = sum(1 for a in group if a["day7_score"] > 0) / len(group) * 100
        shift = d7_sup - d1_sup
        d1_opp = sum(1 for a in group if a["day1_score"] < 0) / len(group) * 100
        d7_opp = sum(1 for a in group if a["day7_score"] < 0) / len(group) * 100
        print(f"  {ht:<12} (n={len(group)}): Support {d1_sup:.0f}%→{d7_sup:.0f}% ({shift:+.0f}pp) | Oppose {d1_opp:.0f}%→{d7_opp:.0f}%")

    # 6. Sample opinion journeys
    print(f"\n{'='*70}")
    print("SAMPLE OPINION JOURNEYS (first 10)")
    print(f"{'='*70}")
    for a in agents[:10]:
        d1 = a["day1_score"]
        d4 = a["day4_score"]
        d7 = a["day7_score"]
        journey = f"{d1:+d} → {d4:+d} → {d7:+d}"
        changed = "CHANGED" if d1 != d7 else "stable"
        age = a.get("age", "?")
        eth = a.get("ethnicity", "?")
        housing = a.get("housing_type", "?")
        print(f"  [{age}{a.get('gender','?')} {eth} {housing}] {journey} ({changed})")
        print(f"    Day1: {a.get('day1_reasoning', '')[:80]}")
        if d1 != d7:
            print(f"    Day7: {a.get('day7_reasoning', '')[:80]}")

    # === Summary ===
    total_elapsed = time.time() - total_start
    support_d1 = sum(1 for a in agents if a["day1_score"] > 0) / len(agents) * 100
    oppose_d1 = sum(1 for a in agents if a["day1_score"] < 0) / len(agents) * 100
    support_d7 = sum(1 for a in agents if a["day7_score"] > 0) / len(agents) * 100
    oppose_d7 = sum(1 for a in agents if a["day7_score"] < 0) / len(agents) * 100

    print(f"\n{'='*70}")
    print(f"SUMMARY — 7-Day Social Simulation: {EVENT_NAME}")
    print(f"{'='*70}")
    print(f"  N = {len(agents)}, 3 rounds × {len(agents)} = {3*len(agents)} LLM calls")
    print(f"  Total runtime: {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")
    print(f"")
    print(f"  Day 1 (cold):  Support {support_d1:.1f}% | Oppose {oppose_d1:.1f}%")
    print(f"  Day 7 (echo):  Support {support_d7:.1f}% | Oppose {oppose_d7:.1f}%")
    print(f"  Net shift:     Support {support_d7-support_d1:+.1f}pp | Oppose {oppose_d7-oppose_d1:+.1f}pp")
    print(f"")
    print(f"  Opinion changed: {changed_total}/{len(agents)} ({changed_total/len(agents)*100:.1f}%)")
    print(f"  Polarization:    {pol_d1:.3f} → {pol_d7:.3f}")
    print(f"  Echo chamber:    {echo_d1:.3f} → {echo_d7:.3f}")

    # Save
    output = {
        "timestamp": str(datetime.now()),
        "test": "SIM-001",
        "name": EVENT_NAME,
        "type": "social_simulation",
        "method": "VS+RP v2.0 + Multi-Round ABM",
        "sample_size": len(agents),
        "rounds": 3,
        "total_llm_calls": 3 * len(agents),
        "elapsed_seconds": round(total_elapsed),
        "event": EVENT_NAME,
        "question": QUESTION,
        "options": OPTIONS,
        "context_day1": CONTEXT_DAY1,
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
                "age": a.get("age"),
                "gender": a.get("gender"),
                "ethnicity": a.get("ethnicity"),
                "housing": a.get("housing_type"),
                "income": a.get("monthly_income"),
                "cluster": a["cluster"],
                "day1_score": a["day1_score"],
                "day4_score": a["day4_score"],
                "day7_score": a["day7_score"],
                "day1_choice": a["day1_choice"],
                "day7_choice": a["day7_choice"],
                "day1_reasoning": a.get("day1_reasoning", ""),
                "day7_reasoning": a.get("day7_reasoning", ""),
                "changed": a["day1_score"] != a["day7_score"],
            }
            for a in agents
        ],
    }

    outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output", "sim_cpf_age.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to: {outpath}")
    print(f"Finished: {datetime.now()}")


if __name__ == "__main__":
    main()
