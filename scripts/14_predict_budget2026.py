"""
Script 14: Predict Budget 2026 Public Satisfaction (PR-003)
Predict public satisfaction with Singapore Budget 2026 (announced Feb 13, 2026).

Uses VS+RP method + Protocol v2.0 (V-POLI + V-CONS vertical)
N=1000, 20 concurrent, adults 21+

PROTOCOL v2.0 PRINCIPLE: Context contains ONLY objective facts about Budget 2026.
No survey results, no satisfaction polls, no public opinion data referenced.
The model must predict independently from agent demographics + policy facts.

Usage:
    python3 -u scripts/14_predict_budget2026.py
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

QUESTION = "How satisfied is this respondent with Singapore's Budget 2026?"

OPTIONS = [
    "Very satisfied",
    "Somewhat satisfied",
    "Neutral",
    "Somewhat dissatisfied",
    "Very dissatisfied",
]

# === V-POLI + V-CONS Protocol v2.0: Context Injection ===
# PRINCIPLE: Objective facts only. No survey results. No satisfaction data.
# Present both "reduced" and "increased" measures for balanced framing.
CONTEXT = (
    # Section A: What happened
    "February 13, 2026. Prime Minister Lawrence Wong delivered Singapore's Budget 2026, "
    "themed 'Securing Our Future Together in a Changed World.' This is the first full Budget "
    "after the May 2025 General Election where PAP won 65.6% of votes.\n\n"

    # Section B: Key measures — what households receive
    "KEY MEASURES FOR HOUSEHOLDS:\n"
    "- CDC Vouchers: $500 per household (Jan 2027) — usable at supermarkets and hawkers\n"
    "- Cost-of-Living Special Payment: $200-$400 one-off cash (Sep 2026), tiered by income\n"
    "- U-Save rebates: up to $570 for HDB households (to cushion carbon tax increase to $45/tonne)\n"
    "- Child LifeSG Credits: $500 per child for families\n"
    "- CPF top-up: up to $1,500 for those aged 50+ with retirement savings below Basic Retirement Sum\n"
    "- Corporate income tax rebate: 40% for companies (capped at $30,000)\n\n"

    # Section C: Changes from previous budget (factual comparison)
    "COMPARED TO BUDGET 2025:\n"
    "- CDC vouchers reduced from $800 to $500 per household (-$300)\n"
    "- U-Save rebates reduced by approximately 25%\n"
    "- EdSave top-ups for teenagers removed (was $500 per student in Budget 2025)\n"
    "- SG60 one-off bonuses from 2025 not repeated (those were tied to Singapore's 60th birthday)\n"
    "- A median household with two children receives approximately $300-$500 less in direct transfers\n"
    "- However, ComCare long-term assistance rates INCREASED (single person: $640 to $760/month)\n"
    "- Higher CPF contributions for older workers (new)\n\n"

    # Section D: Economic context (objective facts)
    "ECONOMIC CONTEXT:\n"
    "- Carbon tax rises from $25 to $45 per tonne in 2026 (will increase electricity bills)\n"
    "- US tariff uncertainty (10-15% tariffs on trading partners) creates economic headwinds\n"
    "- Singapore GDP growth forecast for 2026: 1-3%\n"
    "- Inflation has moderated from 2023 peaks but cost of living remains a top public concern\n"
    "- Unemployment rate remains low at around 2%\n\n"

    "NOTE: This question asks about the respondent's PERSONAL satisfaction with Budget 2026 "
    "as a whole — not whether individual measures are good or bad. Consider their income level, "
    "life stage, housing type, and how much they personally benefit or are affected."
)


def main():
    print(f"Budget 2026 Satisfaction Prediction (PR-003) — N={SAMPLE_SIZE}, VS+RP v2.0")
    print(f"Started: {datetime.now()}")
    print()

    # Sample adults 21+ (voting age, all residency)
    print("Sampling adults 21+ (stratified by age x gender)...")
    sample, meta = stratified_sample(
        n=SAMPLE_SIZE,
        strata=ADULT_STRATA,
        seed=44,
    )
    print(f"Sampled: {len(sample)} agents")
    print()

    # Prepare batch
    batch = []
    agent_dicts = []
    for i in range(len(sample)):
        agent = sample.iloc[i].to_dict()
        persona = agent_to_persona(agent)
        batch.append((i, agent, persona))
        agent_dicts.append(agent)

    start_time = time.time()

    def on_progress(done, total):
        elapsed = time.time() - start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0
        print(f"  Progress: {done}/{total} ({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")

    print(f"Running {len(batch)} LLM calls (20 concurrent)...")
    raw_results = ask_agents_batch(batch, QUESTION, OPTIONS, CONTEXT, on_progress=on_progress)

    # Merge agent metadata
    responses = []
    api_errors = 0
    for i, result in enumerate(raw_results):
        if result is None:
            result = {"choice": OPTIONS[2], "reasoning": "error", "probabilities": {}}
        if result.get("reasoning") == "API error":
            api_errors += 1
        result.update(agent_response_meta(agent_dicts[i]))
        responses.append(result)

    elapsed = time.time() - start_time
    print(f"\nCompleted {len(responses)} agents in {elapsed:.0f}s")
    print(f"API errors: {api_errors}")

    # Aggregate
    dist = compute_distribution(responses, OPTIONS)
    pcts = {opt: d["pct"] for opt, d in dist.items()}

    print(f"\n{'='*70}")
    print(f"PREDICTION RESULTS (N={len(responses)})")
    print(f"{'='*70}")
    for opt in OPTIONS:
        print(f"  {opt}: {dist[opt]['count']} ({dist[opt]['pct']:.1f}%)")

    # Key metrics
    satisfied_pct = pcts.get("Very satisfied", 0) + pcts.get("Somewhat satisfied", 0)
    dissatisfied_pct = pcts.get("Somewhat dissatisfied", 0) + pcts.get("Very dissatisfied", 0)
    print(f"\n  Satisfied (very+somewhat): {satisfied_pct:.1f}%")
    print(f"  Dissatisfied (somewhat+very): {dissatisfied_pct:.1f}%")
    print(f"  Net satisfaction: {satisfied_pct - dissatisfied_pct:+.1f}pp")

    # Breakdowns
    print(f"\n{'='*70}")
    print("BREAKDOWNS")
    print(f"{'='*70}")

    age_bins = {"21-29": (21, 29), "30-39": (30, 39), "40-49": (40, 49),
                "50-59": (50, 59), "60+": (60, 100)}
    print_breakdown(responses, "agent_age", OPTIONS, "By Age Group",
                    bins=age_bins, highlight_options=OPTIONS[:2])

    print_breakdown(responses, "agent_ethnicity", OPTIONS, "By Ethnicity",
                    highlight_options=OPTIONS[:2])

    inc_bins = {"<$3K": (0, 2999), "$3K-$5K": (3000, 4999),
                "$5K-$8K": (5000, 7999), "$8K+": (8000, 999999)}
    print_breakdown(responses, "agent_income", OPTIONS, "By Income",
                    bins=inc_bins, highlight_options=OPTIONS[:2])

    print_breakdown(responses, "agent_housing", OPTIONS, "By Housing",
                    highlight_options=OPTIONS[:2])

    # Sample reasoning
    print("\n--- Sample Reasoning (first 10) ---")
    for r in responses[:10]:
        print(f"  [{r['agent_age']}{r['agent_gender']} {r['agent_ethnicity']} ${int(r['agent_income']):,} {r['agent_housing']}]")
        print(f"    -> {r['choice']}")
        print(f"    Reason: {r.get('reasoning', 'N/A')}")

    # Save results
    output = {
        "timestamp": str(datetime.now()),
        "test": "Budget_2026_Satisfaction",
        "type": "prediction",
        "method": "VS+RP v2.0",
        "sample_size": len(responses),
        "elapsed_seconds": round(elapsed),
        "api_errors": api_errors,
        "percentages": pcts,
        "satisfied_pct": satisfied_pct,
        "dissatisfied_pct": dissatisfied_pct,
        "net_satisfaction": round(satisfied_pct - dissatisfied_pct, 1),
        "options": OPTIONS,
        "question": QUESTION,
        "context": CONTEXT,
        "responses": responses,
    }
    outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output", "predict_budget2026.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to: {outpath}")
    print(f"Finished: {datetime.now()}")


if __name__ == "__main__":
    main()
