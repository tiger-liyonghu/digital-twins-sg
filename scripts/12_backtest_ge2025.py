"""
Script 12: Backtest GE2025 — General Election 2025
Actual results (ELD): PAP 65.57%, WP 14.99%, PSP 3.50%, Others 15.94%

Uses VS+RP method + Survey Design Protocol v2.0 (V-ELEC vertical)
Key protocol additions:
  - Context injection: seat coverage math, contested-vs-national warning
  - Question design: constituency-aware framing
  - Historical anchoring: GE2020 base rates, national share bounds

N=1000, stratified by age x gender (Census proportions for citizens 21+)

Usage:
    python3 -u scripts/12_backtest_ge2025.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from datetime import datetime

from lib.sampling import stratified_sample, CITIZEN_VOTER_STRATA
from lib.persona import agent_to_persona, agent_response_meta
from lib.llm import ask_agent, ask_agents_batch, redistribute_non_candidate
from lib.analysis import compute_distribution, compute_mae, print_breakdown

SAMPLE_SIZE = 1000

ACTUAL = {
    "People's Action Party (PAP)": 65.57,
    "Workers' Party (WP)": 14.99,
    "Progress Singapore Party (PSP)": 3.50,
    "Other opposition parties": 15.94,
}

QUESTION = "Which political party would this respondent most likely vote for in the 2025 Singapore General Election?"

OPTIONS = [
    "People's Action Party (PAP)",
    "Workers' Party (WP)",
    "Progress Singapore Party (PSP)",
    "Other opposition parties",
    "Would not vote / Spoil vote",
]

# === V-ELEC Protocol v2.0: Context Injection ===
# Key insight: coverage math belongs in POST-PROCESSING (aggregation),
# not in the individual-level prompt. Individual agents vote based on
# their personal preferences. We apply coverage weighting AFTER collection.
#
# What DOES belong in the prompt: historical anchoring, party descriptions,
# and calibration cues that prevent LLM's media-bias from inflating opposition.

CONTEXT = (
    # Section A: Election context
    "May 2025 Singapore General Election. PM Lawrence Wong calls the election after "
    "taking over from PM Lee Hsien Loong in May 2024. Key issues: cost of living, "
    "housing affordability, healthcare costs, jobs and immigration policy.\n\n"

    "PAP: Ruling party since 1965, led by PM Lawrence Wong. Platform emphasizes "
    "stability, economic growth, Forward Singapore plan. PAP has governed Singapore "
    "continuously and has deep grassroots networks in every constituency.\n"
    "Workers' Party (WP): Main opposition, led by Pritam Singh. Holds Aljunied GRC "
    "and Sengkang GRC. Advocates for stronger social safety net and checks on government.\n"
    "Progress Singapore Party (PSP): Founded by Tan Cheng Bock in 2019. A newer, smaller "
    "party. Focuses on cost of living and government accountability.\n"
    "Other opposition parties: SDP, NSP, RDU, SPP, and smaller parties. These are small "
    "parties with limited name recognition outside their contested areas.\n\n"

    # Section B: Historical anchoring (V-ELEC Phase 5 — calibration)
    "HISTORICAL CONTEXT FOR CALIBRATION:\n"
    "- In GE2020, PAP won 61.2% of all valid votes nationally.\n"
    "- In GE2020, WP won about 11% of all valid votes nationally.\n"
    "- In GE2020, all other opposition combined won about 28% nationally.\n"
    "- PAP has won every general election since 1965 with national vote share "
    "between 60-70% in recent elections (2011: 60.1%, 2015: 69.9%, 2020: 61.2%).\n"
    "- Most Singaporeans have a pragmatic, stability-oriented political outlook.\n"
    "- Opposition supporters exist but are a MINORITY of the electorate.\n\n"

    # Section C: Anti-bias calibration (V-ELEC E5 — Shy Tory correction)
    "IMPORTANT CALIBRATION NOTE:\n"
    "- Online discourse and media coverage OVERREPRESENT opposition voices. "
    "The silent majority of Singaporean voters consistently support PAP.\n"
    "- Do NOT assume that vocal online criticism of the government reflects "
    "the views of the average voter.\n"
    "- Older voters, heartland HDB residents, and lower-income voters tend to "
    "be more pro-PAP than what online discourse suggests.\n\n"

    "Voting is compulsory for all citizens aged 21+."
)


def main():
    print(f"GE2025 Backtest — N={SAMPLE_SIZE}, VS+RP method")
    print(f"Started: {datetime.now()}")
    print()

    sample, meta = stratified_sample(
        n=SAMPLE_SIZE,
        strata=CITIZEN_VOTER_STRATA,
        residency="Citizen",
    )
    print(f"Sampled: {len(sample)}")
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
    for i, result in enumerate(raw_results):
        if result is None:
            result = {"choice": OPTIONS[0], "reasoning": "error", "probabilities": {}}
        result.update(agent_response_meta(agent_dicts[i]))
        responses.append(result)

    elapsed = time.time() - start_time
    print(f"\nCompleted {len(responses)} agents in {elapsed:.0f}s")

    # Aggregate
    dist = compute_distribution(responses, OPTIONS)
    raw_pcts = {opt: d["pct"] for opt, d in dist.items()}

    print(f"\n{'='*70}")
    print(f"RAW RESULTS (N={len(responses)})")
    print(f"{'='*70}")
    for opt in OPTIONS:
        print(f"  {opt}: {dist[opt]['count']} ({dist[opt]['pct']:.1f}%)")

    # Redistribute abstention
    adjusted = redistribute_non_candidate(raw_pcts)
    mae = None
    if adjusted:
        print(f"\n{'='*70}")
        print(f"ADJUSTED (abstention redistributed)")
        print(f"{'='*70}")
        for k, v in adjusted.items():
            actual_v = ACTUAL.get(k, 0)
            diff = v - actual_v
            print(f"  {k}: {v:.1f}% (actual: {actual_v:.1f}%, diff: {diff:+.1f}pp)")

        mae = compute_mae(adjusted, ACTUAL)
        print(f"\n  MAE: {mae:.1f}pp")

    # Breakdowns
    print(f"\n{'='*70}")
    print("BREAKDOWNS")
    print(f"{'='*70}")

    age_bins = {"21-29": (21, 29), "30-39": (30, 39), "40-49": (40, 49),
                "50-59": (50, 59), "60-69": (60, 69), "70+": (70, 100)}
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
        "test": "GE2025",
        "method": "VS+RP",
        "sample_size": len(responses),
        "sampling_meta": meta,
        "elapsed_seconds": round(elapsed),
        "raw_percentages": raw_pcts,
        "adjusted_percentages": adjusted,
        "actual": ACTUAL,
        "mae_pp": mae,
        "options": OPTIONS,
        "question": QUESTION,
        "context": CONTEXT,
        "responses": responses,
    }
    outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output", "backtest_ge2025.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to: {outpath}")
    print(f"Finished: {datetime.now()}")


if __name__ == "__main__":
    main()
