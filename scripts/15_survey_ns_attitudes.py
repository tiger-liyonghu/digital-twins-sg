"""
Script 15: National Service Attitudes Survey (SV-001)
Survey Singaporean residents' attitudes toward National Service (NS).

Uses VS+RP method + Protocol v2.0
N=1000, 20 concurrent, adults 18+ (includes those who served, are serving, or never served)

PROTOCOL v2.0 PRINCIPLE: Context contains ONLY objective facts about NS policy.
No opinion polls, no attitude surveys, no public sentiment data referenced.
The model must predict independently from agent demographics + policy facts.

Usage:
    python3 -u scripts/15_survey_ns_attitudes.py
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

# === Three survey questions covering different dimensions of NS attitudes ===

# Q1: Overall importance
Q1 = "How important does this respondent believe National Service (NS) is to Singapore?"
Q1_OPTIONS = [
    "Very important — essential for Singapore's defence and national identity",
    "Somewhat important — necessary but could be improved",
    "Neutral — can see both sides",
    "Somewhat unimportant — the costs outweigh the benefits",
    "Not important at all — Singapore should move to a professional military",
]

# Q2: Fairness of current system
Q2 = "How fair does this respondent think the current National Service system is?"
Q2_OPTIONS = [
    "Very fair — the current system is well-designed",
    "Somewhat fair — generally fair but has some inequities",
    "Neutral",
    "Somewhat unfair — significant fairness issues exist",
    "Very unfair — the system is fundamentally inequitable",
]

# Q3: Should NS duration be shortened?
Q3 = "Does this respondent think the current 2-year NS duration should be shortened?"
Q3_OPTIONS = [
    "No — 2 years is necessary for proper training",
    "Maybe — open to modest reduction (e.g. to 18 months) if training efficiency improves",
    "Yes — should be reduced to 12-18 months",
    "Yes — should be reduced to under 12 months",
    "NS should be abolished entirely",
]

# === Context: objective facts only ===
CONTEXT = (
    "SINGAPORE NATIONAL SERVICE (NS) — KEY FACTS:\n"
    "- Enacted via the Enlistment Act 1967. All male Singapore Citizens and 2nd-generation "
    "Permanent Residents must serve 2 years of full-time NS upon turning 18.\n"
    "- After full-time NS, men serve Operationally Ready NS (reservist) obligations "
    "until age 40 (enlisted) or 50 (officers), with annual In-Camp Training (ICT).\n"
    "- Women are NOT required to serve NS. Female volunteers may apply.\n"
    "- NS covers three services: Singapore Armed Forces (SAF), Singapore Police Force (SPF), "
    "and Singapore Civil Defence Force (SCDF).\n"
    "- NSFs (full-time servicemen) receive monthly allowances ranging from ~$630 (recruit) "
    "to ~$1,200 (officer), significantly below market wages.\n\n"

    "RECENT DEVELOPMENTS (2024-2026):\n"
    "- The Committee to Strengthen National Service (CSNS) was established in 2023 "
    "to review NS policies and recommend updates.\n"
    "- NS duration has remained at 2 years since 2004 (reduced from 2.5 years).\n"
    "- PM Lawrence Wong has stated NS remains necessary given Singapore's small population "
    "and geopolitical position.\n"
    "- Enhanced NS Recognition: LifeSG credits, tax reliefs, and priority in public housing "
    "for NSmen and their families.\n"
    "- Growing public discussion about whether women should serve some form of national service.\n"
    "- Some NSFs and parents have raised concerns about the opportunity cost — 2 years delay "
    "to university/career compared to peers in countries without conscription.\n\n"

    "SINGAPORE'S SECURITY CONTEXT:\n"
    "- Small city-state (5.9 million population, ~3.6 million citizens) with no strategic depth.\n"
    "- Located in Southeast Asia between Malaysia and Indonesia.\n"
    "- Singapore's total defence doctrine relies on a large trained reserve force.\n"
    "- SAF active strength: ~72,000. Reserve strength: ~300,000+.\n"
    "- Defence budget 2026: ~S$21 billion (~6% of government expenditure).\n\n"

    "NOTE: Consider the respondent's gender (men have direct NS experience; women do not serve), "
    "age (older men have completed reservist; younger men may be serving or recently completed), "
    "ethnicity, income level, and personality when estimating their attitude."
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

    # Merge agent metadata
    responses = []
    api_errors = 0
    for i, result in enumerate(raw_results):
        if result is None:
            result = {"choice": options[2], "reasoning": "error", "probabilities": {}}
        if result.get("reasoning") == "API error":
            api_errors += 1
        result.update(agent_response_meta(agent_dicts[i]))
        responses.append(result)

    elapsed = time.time() - start_time
    print(f"\nCompleted {len(responses)} agents in {elapsed:.0f}s (API errors: {api_errors})")

    # Aggregate
    dist = compute_distribution(responses, options)

    print(f"\n--- Results (N={len(responses)}) ---")
    for opt in options:
        short = opt.split(" — ")[0] if " — " in opt else opt[:50]
        print(f"  {short}: {dist[opt]['count']} ({dist[opt]['pct']:.1f}%) "
              f"[CI: {dist[opt]['ci_low']}-{dist[opt]['ci_high']}%]")

    # Breakdowns
    age_bins = {"18-29": (18, 29), "30-39": (30, 39), "40-49": (40, 49),
                "50-59": (50, 59), "60+": (60, 100)}
    print_breakdown(responses, "agent_age", options, "By Age Group",
                    bins=age_bins, highlight_options=options[:2])

    print_breakdown(responses, "agent_gender", options, "By Gender",
                    highlight_options=options[:2])

    print_breakdown(responses, "agent_ethnicity", options, "By Ethnicity",
                    highlight_options=options[:2])

    inc_bins = {"<$3K": (0, 2999), "$3K-$5K": (3000, 4999),
                "$5K-$8K": (5000, 7999), "$8K+": (8000, 999999)}
    print_breakdown(responses, "agent_income", options, "By Income",
                    bins=inc_bins, highlight_options=options[:2])

    # Sample reasoning
    print("\n--- Sample Reasoning (first 5) ---")
    for r in responses[:5]:
        short_choice = r['choice'].split(" — ")[0] if " — " in r['choice'] else r['choice'][:40]
        print(f"  [{r['agent_age']}{r['agent_gender']} {r['agent_ethnicity']} ${int(r['agent_income']):,}]")
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
    print(f"National Service Attitudes Survey (SV-001) — N={SAMPLE_SIZE}, VS+RP v2.0")
    print(f"Started: {datetime.now()}")
    print()

    # Sample adults 18+ (all residency, both genders)
    print("Sampling adults 18+ (stratified by age x gender)...")
    sample, meta = stratified_sample(
        n=SAMPLE_SIZE,
        strata=ADULT_STRATA,
        seed=45,
    )
    print(f"Sampled: {len(sample)} agents")

    # Prepare batch (shared across all 3 questions)
    batch = []
    agent_dicts = []
    for i in range(len(sample)):
        agent = sample.iloc[i].to_dict()
        persona = agent_to_persona(agent)
        batch.append((i, agent, persona))
        agent_dicts.append(agent)

    # Run 3 questions
    r1 = run_question(Q1, Q1_OPTIONS, batch, agent_dicts, "Q1: Importance of NS")
    r2 = run_question(Q2, Q2_OPTIONS, batch, agent_dicts, "Q2: Fairness of NS")
    r3 = run_question(Q3, Q3_OPTIONS, batch, agent_dicts, "Q3: NS Duration")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY — National Service Attitudes")
    print(f"{'='*70}")

    # Q1 summary
    q1_important = r1["percentages"].get(Q1_OPTIONS[0], 0) + r1["percentages"].get(Q1_OPTIONS[1], 0)
    q1_not = r1["percentages"].get(Q1_OPTIONS[3], 0) + r1["percentages"].get(Q1_OPTIONS[4], 0)
    print(f"\nQ1 Importance: {q1_important:.1f}% think NS is important, {q1_not:.1f}% think it's not")

    # Q2 summary
    q2_fair = r2["percentages"].get(Q2_OPTIONS[0], 0) + r2["percentages"].get(Q2_OPTIONS[1], 0)
    q2_unfair = r2["percentages"].get(Q2_OPTIONS[3], 0) + r2["percentages"].get(Q2_OPTIONS[4], 0)
    print(f"Q2 Fairness: {q2_fair:.1f}% think NS is fair, {q2_unfair:.1f}% think it's unfair")

    # Q3 summary
    q3_keep = r3["percentages"].get(Q3_OPTIONS[0], 0)
    q3_shorten = sum(r3["percentages"].get(Q3_OPTIONS[i], 0) for i in [2, 3])
    q3_abolish = r3["percentages"].get(Q3_OPTIONS[4], 0)
    print(f"Q3 Duration: {q3_keep:.1f}% keep 2 years, {q3_shorten:.1f}% shorten, {q3_abolish:.1f}% abolish")

    # Save results
    output = {
        "timestamp": str(datetime.now()),
        "test": "NS_Attitudes_Survey",
        "type": "survey",
        "method": "VS+RP v2.0",
        "sample_size": len(sample),
        "context": CONTEXT,
        "questions": [r1, r2, r3],
    }
    outpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output", "survey_ns_attitudes.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to: {outpath}")
    print(f"Finished: {datetime.now()}")


if __name__ == "__main__":
    main()
