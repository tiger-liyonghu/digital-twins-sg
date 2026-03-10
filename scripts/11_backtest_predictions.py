"""
Script 11: Backtest Predictions — Validate Digital Twin against real events.

Two past events with known outcomes:
1. 2023 Presidential Election: Tharman 70.4%, Ng Kok Song 15.7%, Tan Kin Lian 13.9%
2. 2024 GST 9% Impact: ~60% consumers planned to reduce non-essential spending

Usage:
    python3 -u scripts/11_backtest_predictions.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from datetime import datetime
from collections import Counter

from lib.sampling import stratified_sample, simple_sample, CITIZEN_VOTER_STRATA, ADULT_STRATA
from lib.persona import agent_to_persona, agent_response_meta
from lib.llm import ask_agents_batch
from lib.analysis import compute_distribution, compute_mae, print_breakdown

SAMPLE_SIZE = 100


def run_survey(title, question, options, context, sample_df, actual_result):
    """Run a survey on a pre-sampled set of agents using batch LLM calls."""
    print(f"\n{'='*70}")
    print(f"BACKTEST: {title}")
    print(f"{'='*70}")
    print(f"Question: {question}")
    print(f"Actual result: {actual_result}")
    print(f"Sample size: {len(sample_df)}")
    print()

    # Prepare batch
    batch = []
    agent_dicts = []
    for i in range(len(sample_df)):
        agent = sample_df.iloc[i].to_dict()
        persona = agent_to_persona(agent)
        batch.append((i, agent, persona))
        agent_dicts.append(agent)

    start_time = time.time()

    def on_progress(done, total):
        elapsed = time.time() - start_time
        print(f"  Progress: {done}/{total} ({elapsed:.0f}s elapsed)")

    print(f"Running {len(batch)} LLM calls (batch mode)...")
    raw_results = ask_agents_batch(batch, question, options, context, on_progress=on_progress)

    # Merge agent metadata
    responses = []
    for i, result in enumerate(raw_results):
        if result is None:
            result = {"choice": options[0], "reasoning": "error", "probabilities": {}}
        result.update(agent_response_meta(agent_dicts[i]))
        responses.append(result)

    elapsed = time.time() - start_time
    print(f"Completed {len(responses)} agents in {elapsed:.0f}s")

    # Analyze
    dist = compute_distribution(responses, options)

    print(f"\n--- Results ({len(responses)} agents) ---")
    for opt in options:
        print(f"  {opt}: {dist[opt]['count']} ({dist[opt]['pct']:.1f}%)")

    # Breakdowns
    age_bins = {"21-29": (21, 29), "30-44": (30, 44), "45-59": (45, 59), "60+": (60, 100)}
    print_breakdown(responses, "agent_age", options, "By Age Group",
                    bins=age_bins, highlight_options=options[:2])
    print_breakdown(responses, "agent_ethnicity", options, "By Ethnicity",
                    highlight_options=options[:2])
    inc_bins = {"<$3K": (0, 2999), "$3K-$7K": (3000, 6999), "$7K+": (7000, 999999)}
    print_breakdown(responses, "agent_income", options, "By Income",
                    bins=inc_bins, highlight_options=options[:2])

    # Sample reasoning
    print("\n--- Sample Reasoning ---")
    for r in responses[:5]:
        print(f"  [{r['agent_age']}{r['agent_gender']} {r['agent_ethnicity']} ${int(r['agent_income']):,}] "
              f"{r['choice']} — {r.get('reasoning', 'N/A')}")

    return {
        "title": title,
        "question": question,
        "options": options,
        "actual_result": actual_result,
        "n_respondents": len(responses),
        "elapsed_seconds": round(elapsed),
        "choice_distribution": dist,
        "responses": responses,
    }


def main():
    print(f"Backtest Predictions — N={SAMPLE_SIZE} per survey (batch mode)")
    print(f"Started: {datetime.now()}")

    results = []

    # EVENT 1: 2023 Presidential Election
    print("\nSampling for Presidential Election (citizens 21+)...")
    pe_sample, _ = stratified_sample(
        n=SAMPLE_SIZE,
        strata=CITIZEN_VOTER_STRATA,
        residency="Citizen",
        seed=42,
    )

    r1 = run_survey(
        title="2023 Singapore Presidential Election",
        question=(
            "The 2023 Singapore Presidential Election has three candidates.\n"
            "Who would this respondent most likely vote for as President of Singapore?"
        ),
        options=[
            "Tharman Shanmugaratnam",
            "Ng Kok Song",
            "Tan Kin Lian",
            "Would not vote / Spoil vote",
        ],
        context=(
            "September 2023 Presidential Election. The President of Singapore is a ceremonial role "
            "with custodial powers over national reserves. Voting is compulsory for citizens.\n"
            "Candidate A: Tharman Shanmugaratnam, 66, Indian Tamil descent, former Senior Minister, "
            "resigned from PAP to run as independent.\n"
            "Candidate B: Ng Kok Song, 75, Chinese, former GIC Chief Investment Officer, "
            "independent candidate, first-time politician.\n"
            "Candidate C: Tan Kin Lian, 75, Chinese, former NTUC Income CEO, "
            "second-time presidential candidate (also ran in 2011)."
        ),
        sample_df=pe_sample,
        actual_result="Tharman 70.4%, Ng Kok Song 15.7%, Tan Kin Lian 13.9%",
    )
    results.append(r1)

    # EVENT 2: GST increase
    print("\nSampling for GST Impact (adults 18+ with income)...")
    gst_sample = simple_sample(
        n=SAMPLE_SIZE,
        age_min=18,
        seed=43,
    )
    # Filter to those with income client-side
    gst_sample = gst_sample[gst_sample["monthly_income"] > 0].head(SAMPLE_SIZE)

    r2 = run_survey(
        title="2024 GST Increase to 9% — Consumer Impact",
        question=(
            "The Singapore government has raised GST from 8% to 9%, effective January 2024. "
            "How would this respondent's spending habits be affected?"
        ),
        options=[
            "Will significantly cut non-essential spending",
            "Will moderately reduce some spending",
            "Minor impact, will mostly spend the same",
            "No impact at all on my spending",
        ],
        context=(
            "January 2024. Singapore's GST rose from 8% to 9% (second stage, after 7%->8% in 2023). "
            "The government provided an Assurance Package including CDC vouchers, cash payouts, "
            "and U-Save rebates. Lower-income households receive more support. "
            "Prices of food, transport, and daily essentials have been elevated due to global inflation."
        ),
        sample_df=gst_sample,
        actual_result="~60% planned to reduce non-essential spending (CASE survey)",
    )
    results.append(r2)

    # SUMMARY
    print("\n" + "=" * 70)
    print("BACKTEST COMPARISON SUMMARY")
    print("=" * 70)
    for r in results:
        print(f"\n--- {r['title']} ---")
        print(f"Actual: {r['actual_result']}")
        print(f"Predicted ({r['n_respondents']} agents, {r['elapsed_seconds']}s):")
        for opt, data in r["choice_distribution"].items():
            print(f"  {opt}: {data['pct']}%")

    # Save results
    output = {
        "timestamp": str(datetime.now()),
        "sample_size_per_survey": SAMPLE_SIZE,
        "results": results,
    }
    outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output", "backtest_results.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nFull results saved to: {outpath}")
    print(f"Finished: {datetime.now()}")


if __name__ == "__main__":
    main()
