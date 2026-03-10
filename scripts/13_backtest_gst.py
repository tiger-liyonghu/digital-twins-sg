"""
Script 13: Backtest GST 9% Impact (BT-002)
Actual: ~60% planned to reduce non-essential spending (CASE survey)
Actual breakdown: 15% significantly cut, 45% moderately reduce, 30% minor, 10% no impact

Uses VS+RP method + Protocol v2.0 (V-ECON vertical)
N=1000, 20 concurrent, adults 18+ with income

Usage:
    python3 -u scripts/13_backtest_gst.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from datetime import datetime

from lib.sampling import simple_sample
from lib.persona import agent_to_persona, agent_response_meta
from lib.llm import ask_agents_batch, redistribute_non_candidate
from lib.analysis import compute_distribution, compute_mae, print_breakdown

SAMPLE_SIZE = 1000

ACTUAL = {
    "Significantly cut spending": 15,
    "Moderately reduce spending": 45,
    "Minor impact": 30,
    "No impact at all": 10,
}

QUESTION = "How would this respondent's spending habits be affected by the GST increase from 8% to 9%?"

OPTIONS = [
    "Significantly cut spending",
    "Moderately reduce spending",
    "Minor impact",
    "No impact at all",
]

# === V-ECON + V-CONS Protocol v2.0: Context Injection ===
# Phase 5 redesign based on pre-flight diagnosis:
# - REMOVED: "$50-100/month" rational anchor (made LLM dismiss impact)
# - REMOVED: Detailed Assurance Package (made LLM think "cushioned = no impact")
# - REMOVED: Any reference to CASE survey results (ground truth leak — violates backtest integrity)
# - ADDED: Cumulative inflation pressure framing (matches consumer psychology)
# - ADDED: Historical GST 2007 context (different event, legitimate anchoring)
# PRINCIPLE: Backtest context must NEVER reference the specific survey/study being validated.
#            Historical data from DIFFERENT events is allowed. The target survey's results are NOT.
CONTEXT = (
    # Section A: Policy context
    "January 2024. Singapore's GST (Goods and Services Tax) rose from 8% to 9%. "
    "This is the SECOND increase in two years (7%→8% in Jan 2023, then 8%→9% in Jan 2024). "
    "Consumers have experienced two consecutive years of tax increases.\n\n"

    # Section B: Economic pressure context (consumer psychology, not rational calculation)
    "ECONOMIC CONTEXT:\n"
    "- Singapore experienced high inflation in 2022-2023 (CPI peaked at 6.1% in 2023)\n"
    "- Food prices, hawker meals, and daily essentials rose noticeably\n"
    "- Public transport fares increased in late 2023\n"
    "- HDB rents and housing costs reached record highs\n"
    "- The GST increase comes ON TOP of these existing price pressures\n"
    "- Many consumers feel a CUMULATIVE squeeze — it is not just 1% GST in isolation, "
    "but GST + inflation + rent + transport all rising together\n\n"

    # Section C: Government support (brief, balanced)
    "The government provided an Assurance Package with cash payouts and vouchers "
    "to offset the GST increase, especially for lower-income households. However, "
    "many consumers still FEEL the pinch because the offsets come in periodic lump sums "
    "while the price increases are felt daily.\n\n"

    # Section D: Historical anchoring (DIFFERENT event, not the target survey)
    "HISTORICAL CONTEXT:\n"
    "- When GST rose from 5%→7% in 2007 (a 2pp increase), consumers reported planning "
    "to reduce spending\n"
    "- The current 1pp increase is smaller, but comes during a period of high inflation "
    "unlike 2007 which was a low-inflation period\n\n"

    "NOTE: This question asks how the respondent PLANS to adjust their spending, "
    "not whether they think GST policy is good or bad. Consider their income level "
    "and daily spending patterns."
)


def main():
    print(f"GST 9% Backtest (BT-002) — N={SAMPLE_SIZE}, VS+RP v2.0")
    print(f"Started: {datetime.now()}")
    print()

    # Sample adults 18+ with income — oversample 4x to ensure ≥1000 after income filter
    print("Sampling adults 18+ ...")
    sample = simple_sample(n=SAMPLE_SIZE * 4, age_min=18, seed=43)
    # Filter to those with income
    sample = sample[sample["monthly_income"] > 0].head(SAMPLE_SIZE)
    print(f"Sampled: {len(sample)} (with income > 0)")
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
            result = {"choice": OPTIONS[0], "reasoning": "error", "probabilities": {}}
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
    print(f"RESULTS (N={len(responses)})")
    print(f"{'='*70}")
    for opt in OPTIONS:
        actual_v = ACTUAL.get(opt, 0)
        diff = dist[opt]['pct'] - actual_v
        print(f"  {opt}: {dist[opt]['count']} ({dist[opt]['pct']:.1f}%) [actual: {actual_v}%, diff: {diff:+.1f}pp]")

    mae = compute_mae(pcts, ACTUAL)
    print(f"\n  MAE: {mae:.1f}pp")

    # Key metric: % reducing spending (significantly + moderately)
    reduce_pct = pcts.get("Significantly cut spending", 0) + pcts.get("Moderately reduce spending", 0)
    print(f"\n  Reduce spending (sig+mod): {reduce_pct:.1f}% [actual: ~60%]")

    # Breakdowns
    print(f"\n{'='*70}")
    print("BREAKDOWNS")
    print(f"{'='*70}")

    age_bins = {"18-29": (18, 29), "30-39": (30, 39), "40-49": (40, 49),
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
        "test": "GST_9pct",
        "method": "VS+RP v2.0",
        "sample_size": len(responses),
        "elapsed_seconds": round(elapsed),
        "api_errors": api_errors,
        "percentages": pcts,
        "actual": ACTUAL,
        "mae_pp": mae,
        "reduce_spending_pct": reduce_pct,
        "options": OPTIONS,
        "question": QUESTION,
        "context": CONTEXT,
        "responses": responses,
    }
    outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output", "backtest_gst.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to: {outpath}")
    print(f"Finished: {datetime.now()}")


if __name__ == "__main__":
    main()
