"""
Script 17: Insurance Purchase Channel Preference Backtest (BT-INS-001)
Backtest against Capco Singapore Insurance Survey 2023 (n=1,000).

Ground truth (Capco 2023, single-select):
  - Agent/representative: 64%
  - Third party (non-tied agent): 23%
  - Self (online/direct): 13%

Uses VS+RP method + Protocol v2.0
N=1000, 20 concurrent, adults 18-65 (matching Capco survey demographics)

PROTOCOL v2.0: Context contains ONLY objective facts about insurance distribution
in Singapore. No reference to Capco survey results or any channel preference data.

Usage:
    python3 -u scripts/17_backtest_insurance_channel.py
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

# Ground truth — Capco Singapore Insurance Survey 2023
GROUND_TRUTH = {
    "Insurance agent or representative (face-to-face)": 64.0,
    "Third-party intermediary (non-tied agent, bank, broker)": 23.0,
    "By myself online (insurer website, app, comparison site)": 13.0,
}

# === Survey question ===
QUESTION = (
    "If this respondent were buying a new life or health insurance policy today, "
    "which purchase channel would they most likely use?"
)

OPTIONS = [
    "Insurance agent or representative (face-to-face)",
    "Third-party intermediary (non-tied agent, bank, broker)",
    "By myself online (insurer website, app, comparison site)",
]

# === Context: objective facts only — NO survey results ===
CONTEXT = (
    "INSURANCE DISTRIBUTION IN SINGAPORE — KEY FACTS:\n\n"

    "MARKET STRUCTURE:\n"
    "- Singapore has ~30,000 licensed insurance representatives (tied agents) "
    "as of 2024, down from ~35,000 in 2018.\n"
    "- 7 major life insurers: AIA, Prudential, Great Eastern, NTUC Income, "
    "Manulife, Singlife, FWD.\n"
    "- Financial Advisory (FA) firms employ non-tied advisors who can recommend "
    "products from multiple insurers.\n"
    "- Banks offer bancassurance (insurance sold through bank branches and relationship managers).\n\n"

    "DIGITAL CHANNELS:\n"
    "- All major insurers now offer online purchase for simple products "
    "(term life, travel insurance, basic health plans).\n"
    "- Comparison platforms exist: MoneySmart, SingSaver, GoBear (closed 2023), Comparefirst.sg (MAS-mandated).\n"
    "- MAS introduced the Direct Purchase Insurance (DPI) scheme allowing consumers "
    "to buy basic life insurance directly from insurers without an agent.\n"
    "- Digital insurers: Singlife (originally digital-first), FWD (strong digital presence).\n\n"

    "REGULATORY ENVIRONMENT:\n"
    "- MAS Financial Advisers Act governs insurance distribution.\n"
    "- Agents must pass CMFAS (Capital Markets and Financial Advisory Services) exams.\n"
    "- MAS has encouraged digitalization and direct purchase to improve access and reduce costs.\n"
    "- Balanced Scorecard framework (2022) shifts agent compensation toward quality metrics.\n\n"

    "PRODUCT COMPLEXITY:\n"
    "- Simple products (term life, travel): easier to buy online.\n"
    "- Complex products (whole life, ILP, CI riders, IP): typically require agent explanation.\n"
    "- Integrated Shield Plans (IP): can be purchased directly but riders often sold via agents.\n"
    "- Endowment/savings plans: commonly sold through agents and banks.\n\n"

    "NOTE: Consider the respondent's age (younger may prefer digital, older may prefer "
    "face-to-face), income level (higher income may have bank RM relationships), "
    "education (affects comfort with self-research), and personality (introverts may "
    "prefer online, extroverts may value agent relationships)."
)


def main():
    print(f"Insurance Purchase Channel Backtest (BT-INS-001) — N={SAMPLE_SIZE}, VS+RP v2.0")
    print(f"Ground truth: Capco Singapore Insurance Survey 2023 (n=1,000)")
    print(f"Started: {datetime.now()}")
    print()

    # Sample adults 18-65 (matching Capco demographics)
    print("Sampling adults 18-65 (stratified by age x gender)...")
    sample, meta = stratified_sample(
        n=SAMPLE_SIZE,
        strata=ADULT_STRATA,
        seed=47,
    )
    # Filter to 18-65
    sample = sample[(sample["age"] >= 18) & (sample["age"] <= 65)].head(SAMPLE_SIZE)
    print(f"Sampled (age 18-65): {len(sample)} agents")

    # Prepare batch
    batch = []
    agent_dicts = []
    for i in range(len(sample)):
        agent = sample.iloc[i].to_dict()
        persona = agent_to_persona(agent)
        batch.append((i, agent, persona))
        agent_dicts.append(agent)

    # Run
    print(f"\n{'='*70}")
    print(f"QUESTION: Insurance Purchase Channel Preference")
    print(f"{'='*70}")

    start_time = time.time()

    def on_progress(done, total):
        elapsed = time.time() - start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0
        print(f"  Progress: {done}/{total} ({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")

    print(f"Running {len(batch)} LLM calls (20 concurrent)...")
    raw_results = ask_agents_batch(batch, QUESTION, OPTIONS, CONTEXT, on_progress=on_progress)

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
    print(f"\nCompleted {len(responses)} agents in {elapsed:.0f}s (API errors: {api_errors})")

    # Distribution
    dist = compute_distribution(responses, OPTIONS)

    print(f"\n--- Results (N={len(responses)}) ---")
    print(f"{'Option':<60} {'Predicted':>10} {'Actual':>10} {'Dev':>8}")
    print("-" * 90)
    total_abs_dev = 0
    for opt in OPTIONS:
        pred = dist[opt]["pct"]
        actual = GROUND_TRUTH.get(opt, 0)
        dev = pred - actual
        total_abs_dev += abs(dev)
        short = opt[:55]
        print(f"  {short:<58} {pred:>8.1f}% {actual:>8.1f}% {dev:>+7.1f}pp")

    mae = total_abs_dev / len(OPTIONS)
    print(f"\n  MAE: {mae:.1f}pp")

    # Breakdowns
    age_bins = {"18-29": (18, 29), "30-39": (30, 39), "40-49": (40, 49), "50-65": (50, 65)}
    print_breakdown(responses, "agent_age", OPTIONS, "By Age Group",
                    bins=age_bins, highlight_options=OPTIONS[:2])

    print_breakdown(responses, "agent_gender", OPTIONS, "By Gender",
                    highlight_options=OPTIONS[:2])

    inc_bins = {"<$3K": (0, 2999), "$3K-$5K": (3000, 4999),
                "$5K-$8K": (5000, 7999), "$8K+": (8000, 999999)}
    print_breakdown(responses, "agent_income", OPTIONS, "By Income",
                    bins=inc_bins, highlight_options=OPTIONS[:2])

    print_breakdown(responses, "agent_housing", OPTIONS, "By Housing",
                    highlight_options=OPTIONS[:2])

    # Sample reasoning
    print("\n--- Sample Reasoning (first 5) ---")
    for r in responses[:5]:
        short_choice = r['choice'][:50]
        print(f"  [{r['agent_age']}{r['agent_gender']} {r['agent_ethnicity']} ${int(r['agent_income']):,} {r['agent_housing']}]")
        print(f"    -> {short_choice}")
        print(f"    Reason: {r.get('reasoning', 'N/A')}")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY — Insurance Purchase Channel Backtest")
    print(f"{'='*70}")
    print(f"  Sample: N={len(responses)} (age 18-65)")
    print(f"  API errors: {api_errors}")
    print(f"  MAE: {mae:.1f}pp")
    for opt in OPTIONS:
        pred = dist[opt]["pct"]
        actual = GROUND_TRUTH.get(opt, 0)
        short = opt.split(" (")[0]
        print(f"  {short}: predicted {pred:.1f}% vs actual {actual:.1f}%")

    verdict = "EXCELLENT" if mae < 3 else "GOOD" if mae < 5 else "ACCEPTABLE" if mae < 8 else "NEEDS REVIEW"
    print(f"\n  *** VERDICT: {verdict} (MAE {mae:.1f}pp) ***")

    # Save
    output = {
        "timestamp": str(datetime.now()),
        "test": "Insurance_Purchase_Channel",
        "type": "backtest",
        "method": "VS+RP v2.0",
        "sample_size": len(responses),
        "ground_truth_source": "Capco Singapore Insurance Survey 2023 (n=1,000)",
        "ground_truth_url": "https://www.capco.com/intelligence/capco-intelligence/singapore-insurance-survey-2023",
        "context": CONTEXT,
        "question": QUESTION,
        "options": OPTIONS,
        "ground_truth": GROUND_TRUTH,
        "predicted": {opt: dist[opt]["pct"] for opt in OPTIONS},
        "mae": round(mae, 1),
        "elapsed_seconds": round(elapsed),
        "api_errors": api_errors,
        "distribution": {opt: dist[opt] for opt in OPTIONS},
        "responses": responses,
    }
    outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output", "backtest_insurance_channel.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to: {outpath}")
    print(f"Finished: {datetime.now()}")


if __name__ == "__main__":
    main()
