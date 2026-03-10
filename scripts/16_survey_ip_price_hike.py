"""
Script 16: IP Price Hike Response Survey (SV-002)
Survey Singaporean residents' likely response to Integrated Shield Plan premium increases.

Uses VS+RP method + Protocol v2.0
N=1000, 20 concurrent, adults 25+ (IP-relevant age group)

PROTOCOL v2.0 PRINCIPLE: Context contains ONLY objective facts about IP market.
No opinion polls, no satisfaction surveys, no public sentiment data referenced.

Usage:
    python3 -u scripts/16_survey_ip_price_hike.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from datetime import datetime

from lib.sampling import stratified_sample, ADULT_STRATA
from lib.persona import agent_to_persona, agent_response_meta
from lib.llm import ask_agents_batch
from lib.analysis import compute_distribution, print_breakdown

SAMPLE_SIZE = 1000

# === Four survey questions ===

# Q1: Current IP status
Q1 = "Does this respondent currently have an Integrated Shield Plan (IP) on top of MediShield Life?"
Q1_OPTIONS = [
    "Yes — private hospital IP (e.g. Prudential PRUShield, AIA HealthShield Gold Max)",
    "Yes — restructured/government hospital IP",
    "No — only MediShield Life (basic government coverage)",
    "No — not sure / don't know what IP is",
]

# Q2: Response to 15% premium increase
Q2 = "If this respondent's Integrated Shield Plan premium increases by 15% next year, what would they most likely do?"
Q2_OPTIONS = [
    "Accept the increase and keep current plan",
    "Downgrade to a lower-tier plan (e.g. private → restructured hospital)",
    "Switch to a different insurer's plan at a better rate",
    "Drop IP entirely, keep only MediShield Life",
    "Not sure / need more information before deciding",
]

# Q3: Maximum acceptable annual premium (for private hospital IP)
Q3 = "What is the maximum annual premium this respondent would be willing to pay for a private hospital Integrated Shield Plan?"
Q3_OPTIONS = [
    "Up to $300/year — only basic coverage is worth it",
    "$300-$600/year — moderate premium is acceptable",
    "$600-$1,200/year — willing to pay more for comprehensive coverage",
    "$1,200-$2,000/year — premium coverage is important to me",
    "Over $2,000/year — comprehensive private hospital coverage is essential",
    "Would not pay for IP at all — MediShield Life is sufficient",
]

# Q4: Most important factor when choosing IP
Q4 = "What is the MOST important factor for this respondent when choosing an Integrated Shield Plan?"
Q4_OPTIONS = [
    "Monthly/annual premium cost",
    "Coverage scope (what is covered, panel of hospitals)",
    "Insurer's brand reputation and financial strength",
    "Ease and speed of claims process",
    "Recommendation from insurance agent or family",
    "Whether it covers pre-existing conditions",
]

# === Context: objective facts only ===
CONTEXT = (
    "INTEGRATED SHIELD PLAN (IP) — SINGAPORE MARKET FACTS:\n\n"

    "WHAT IS IP:\n"
    "- MediShield Life is Singapore's compulsory basic health insurance (covers public hospital Class B2/C wards).\n"
    "- Integrated Shield Plans (IPs) are optional private insurance plans that provide additional coverage "
    "above MediShield Life — typically covering private hospitals and Class A/B1 wards.\n"
    "- IPs are offered by 7 insurers: AIA, Great Eastern, NTUC Income, Prudential, Singlife, AXA, Raffles Health.\n"
    "- CPF MediSave can be used to pay IP premiums (up to withdrawal limits).\n"
    "- As of 2024, approximately 2.9 million Singapore residents (about 69%) have an IP.\n\n"

    "RECENT PREMIUM INCREASES:\n"
    "- IP premiums have increased significantly over 2022-2025:\n"
    "  * 2023: average increase 10-20% across insurers\n"
    "  * 2024: average increase 12-18%\n"
    "  * 2025: some plans increased 15-25%\n"
    "- Key drivers: medical cost inflation (5-10% annually), over-utilisation of private healthcare, "
    "rising reinsurance costs, aging population.\n"
    "- A 35-year-old male pays approximately $300-500/year for a private hospital IP.\n"
    "- A 65-year-old male pays approximately $1,500-3,000/year for a private hospital IP.\n"
    "- Premiums increase sharply with age, especially after 60.\n\n"

    "MAS REFORMS (2024-2025):\n"
    "- MAS introduced IP reforms to address rising premiums:\n"
    "  * Portability: policyholders can now switch insurers without losing coverage continuity.\n"
    "  * Upgrade/Downgrade: policyholders can move between plan tiers more easily.\n"
    "  * Panel doctors: insurers can implement panel arrangements to control costs.\n"
    "  * Co-payment: MAS encouraged higher co-payment to reduce over-utilisation.\n"
    "- Government message: IP premiums must remain affordable and sustainable.\n\n"

    "PUBLIC CONCERNS:\n"
    "- IP affordability is consistently among the top healthcare concerns in Singapore.\n"
    "- Many seniors face 'premium shock' as premiums spike after age 60-65.\n"
    "- Some policyholders feel 'trapped' — having paid premiums for years, they are reluctant to downgrade "
    "but struggle with increasing costs.\n"
    "- Younger Singaporeans (25-35) question whether private hospital coverage is worth the cost.\n\n"

    "NOTE: Consider the respondent's age (premiums vary dramatically by age), income level "
    "(affects affordability), housing type (proxy for wealth), and health status "
    "(those with chronic conditions value coverage more). Risk appetite and personality "
    "also affect insurance purchasing decisions."
)


def run_question(question, options, batch, agent_dicts, label):
    """Run one survey question across all agents."""
    print(f"\n{'='*70}")
    print(f"QUESTION: {label}")
    print(f"{'='*70}")

    start_time = time.time()

    def on_progress(done, total):
        elapsed = time.time() - start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0
        print(f"  Progress: {done}/{total} ({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")

    print(f"Running {len(batch)} LLM calls (20 concurrent)...")
    raw_results = ask_agents_batch(batch, question, options, CONTEXT, on_progress=on_progress)

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
    print(f"\nCompleted {len(responses)} agents in {elapsed:.0f}s (API errors: {api_errors})")

    dist = compute_distribution(responses, options)

    print(f"\n--- Results (N={len(responses)}) ---")
    for opt in options:
        short = opt.split(" — ")[0] if " — " in opt else opt[:60]
        print(f"  {short}: {dist[opt]['count']} ({dist[opt]['pct']:.1f}%) "
              f"[CI: {dist[opt]['ci_low']}-{dist[opt]['ci_high']}%]")

    # Breakdowns
    age_bins = {"25-34": (25, 34), "35-44": (35, 44), "45-54": (45, 54),
                "55-64": (55, 64), "65+": (65, 100)}
    print_breakdown(responses, "agent_age", options, "By Age Group",
                    bins=age_bins, highlight_options=options[:2])

    print_breakdown(responses, "agent_gender", options, "By Gender",
                    highlight_options=options[:2])

    inc_bins = {"<$3K": (0, 2999), "$3K-$5K": (3000, 4999),
                "$5K-$8K": (5000, 7999), "$8K+": (8000, 999999)}
    print_breakdown(responses, "agent_income", options, "By Income",
                    bins=inc_bins, highlight_options=options[:2])

    print_breakdown(responses, "agent_housing", options, "By Housing",
                    highlight_options=options[:2])

    # Sample reasoning
    print("\n--- Sample Reasoning (first 5) ---")
    for r in responses[:5]:
        short_choice = r['choice'].split(" — ")[0] if " — " in r['choice'] else r['choice'][:50]
        print(f"  [{r['agent_age']}{r['agent_gender']} {r['agent_ethnicity']} ${int(r['agent_income']):,} {r['agent_housing']}]")
        print(f"    -> {short_choice}")
        print(f"    Reason: {r.get('reasoning', 'N/A')}")

    return {
        "question": question,
        "label": label,
        "options": options,
        "n": len(responses),
        "elapsed_seconds": round(elapsed),
        "api_errors": api_errors,
        "distribution": {opt: dist[opt] for opt in options},
        "percentages": {opt: dist[opt]["pct"] for opt in options},
        "responses": responses,
    }


def main():
    print(f"IP Price Hike Response Survey (SV-002) — N={SAMPLE_SIZE}, VS+RP v2.0")
    print(f"Started: {datetime.now()}")
    print()

    # Sample adults 25+ (IP-relevant age)
    print("Sampling adults 25+ (stratified by age x gender)...")
    sample, meta = stratified_sample(
        n=SAMPLE_SIZE,
        strata=ADULT_STRATA,
        seed=46,
    )
    # Filter to 25+ (ADULT_STRATA includes 15-19 and 20-24)
    sample = sample[sample["age"] >= 25].head(SAMPLE_SIZE)
    print(f"Sampled (age 25+): {len(sample)} agents")

    # Prepare batch
    batch = []
    agent_dicts = []
    for i in range(len(sample)):
        agent = sample.iloc[i].to_dict()
        persona = agent_to_persona(agent)
        batch.append((i, agent, persona))
        agent_dicts.append(agent)

    # Run 4 questions
    r1 = run_question(Q1, Q1_OPTIONS, batch, agent_dicts, "Q1: Current IP Status")
    r2 = run_question(Q2, Q2_OPTIONS, batch, agent_dicts, "Q2: Response to 15% Premium Increase")
    r3 = run_question(Q3, Q3_OPTIONS, batch, agent_dicts, "Q3: Maximum Acceptable Premium")
    r4 = run_question(Q4, Q4_OPTIONS, batch, agent_dicts, "Q4: Most Important Factor")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY — IP Price Hike Response")
    print(f"{'='*70}")

    # Q1
    q1_private = r1["percentages"].get(Q1_OPTIONS[0], 0)
    q1_govt = r1["percentages"].get(Q1_OPTIONS[1], 0)
    q1_none = r1["percentages"].get(Q1_OPTIONS[2], 0)
    print(f"\nQ1 IP Status: {q1_private:.1f}% private IP, {q1_govt:.1f}% govt IP, {q1_none:.1f}% MediShield only")

    # Q2
    q2_accept = r2["percentages"].get(Q2_OPTIONS[0], 0)
    q2_downgrade = r2["percentages"].get(Q2_OPTIONS[1], 0)
    q2_switch = r2["percentages"].get(Q2_OPTIONS[2], 0)
    q2_drop = r2["percentages"].get(Q2_OPTIONS[3], 0)
    print(f"Q2 Price Hike: {q2_accept:.1f}% accept, {q2_downgrade:.1f}% downgrade, {q2_switch:.1f}% switch, {q2_drop:.1f}% drop")

    # Q3
    print(f"Q3 Max Premium: see distribution above")

    # Q4
    top_factor = max(r4["percentages"], key=r4["percentages"].get)
    top_factor_short = top_factor.split(" (")[0] if " (" in top_factor else top_factor[:40]
    print(f"Q4 Top Factor: {top_factor_short} ({r4['percentages'][top_factor]:.1f}%)")

    # Key insight
    churn_risk = q2_downgrade + q2_switch + q2_drop
    print(f"\n*** KEY INSIGHT: {churn_risk:.1f}% of policyholders at risk of leaving/downgrading with 15% hike ***")

    # Save
    output = {
        "timestamp": str(datetime.now()),
        "test": "IP_Price_Hike_Response",
        "type": "survey",
        "method": "VS+RP v2.0",
        "sample_size": len(sample),
        "context": CONTEXT,
        "questions": [r1, r2, r3, r4],
    }
    outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output", "survey_ip_price_hike.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to: {outpath}")
    print(f"Finished: {datetime.now()}")


if __name__ == "__main__":
    main()
