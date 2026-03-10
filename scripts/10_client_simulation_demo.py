"""
Client Simulation Demo — Digital Twin Singapore

Demonstrates the core product flow:
1. Client submits a research question / scenario
2. System selects a representative sample of agents (stratified by demographics)
3. Each agent "responds" via LLM persona reasoning (Layer 3)
4. System aggregates and analyzes responses
5. Client receives structured insights

Two demo clients:
- Client A: Insurance company — "Would you buy CI insurance at $200/month?"
- Client B: Government (HDB) — "Would you apply for a BTO in Punggol?"

Usage:
    python3 scripts/10_client_simulation_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import logging
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# CONFIG — loaded from .env via lib.config
# ============================================================
from lib.config import SUPABASE_URL, SUPABASE_KEY, DEEPSEEK_API_KEY, DEEPSEEK_URL

N_AGENTS = 50  # agents per client scenario
SEED = 42


# ============================================================
# AGENT SAMPLING (stratified)
# ============================================================
def load_agents_from_supabase(n: int = 50, seed: int = 42) -> pd.DataFrame:
    """Load a stratified sample of agents from Supabase."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    # Load all agents (paginated)
    all_agents = []
    offset = 0
    page_size = 1000
    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/agents",
            headers={**headers, "Range": f"{offset}-{offset + page_size - 1}"},
            params={"select": "*"},
        )
        if resp.status_code != 200:
            logger.error(f"Supabase error: {resp.status_code} {resp.text[:200]}")
            break
        data = resp.json()
        all_agents.extend(data)
        if len(data) < page_size:
            break
        offset += page_size

    logger.info(f"Loaded {len(all_agents)} agents from Supabase")
    df = pd.DataFrame(all_agents)

    # Stratified sampling: match Census proportions
    rng = np.random.default_rng(seed)
    sample_indices = []

    # Stratify by age group and gender
    age_bins = [(0, 17, "youth"), (18, 34, "young_adult"),
                (35, 54, "middle"), (55, 74, "senior"), (75, 100, "elderly")]

    for lo, hi, label in age_bins:
        for gender in ["M", "F"]:
            mask = (df["age"] >= lo) & (df["age"] <= hi) & (df["gender"] == gender)
            group = df[mask]
            if len(group) == 0:
                continue
            # Proportional allocation
            target_n = max(1, int(round(len(group) / len(df) * n)))
            chosen = rng.choice(group.index, size=min(target_n, len(group)), replace=False)
            sample_indices.extend(chosen.tolist())

    # Trim or pad to exact n
    rng.shuffle(sample_indices)
    if len(sample_indices) > n:
        sample_indices = sample_indices[:n]
    elif len(sample_indices) < n:
        remaining = [i for i in df.index if i not in sample_indices]
        extra = rng.choice(remaining, size=n - len(sample_indices), replace=False)
        sample_indices.extend(extra.tolist())

    return df.loc[sample_indices].reset_index(drop=True)


def agent_to_persona(agent: dict) -> str:
    """Convert agent record to a persona prompt string."""
    income = agent.get("monthly_income", 0)
    income_desc = "unemployed" if income == 0 else f"earning ${income:,.0f}/month"

    persona = f"""You are a {agent['age']}-year-old {agent['gender']} {agent['ethnicity']} resident of Singapore.
You live in {agent.get('planning_area', 'Singapore')}, in a {agent.get('housing_type', 'HDB')} flat.
Your education level is {agent.get('education_level', 'Secondary')}, currently {income_desc}.
Marital status: {agent.get('marital_status', 'Single')}.
Health: {agent.get('health_status', 'Healthy')}.
Life phase: {agent.get('life_phase', 'establishment')}.
Personality: Openness={agent.get('big5_o', 3):.1f}, Conscientiousness={agent.get('big5_c', 3):.1f}, Extraversion={agent.get('big5_e', 3):.1f}, Agreeableness={agent.get('big5_a', 3):.1f}, Neuroticism={agent.get('big5_n', 3):.1f}.
Risk appetite: {agent.get('risk_appetite', 3):.1f}/5, Social trust: {agent.get('social_trust', 3):.1f}/5."""

    return persona


# ============================================================
# LLM SURVEY ENGINE
# ============================================================
def ask_agent(persona: str, question: str, options: list,
              context: str = "") -> dict:
    """Ask a single agent a survey question via LLM."""

    system_prompt = """You are simulating a real person living in Singapore. Based on your persona, answer the survey question honestly and realistically.

Respond in JSON format:
{
    "choice": "one of the provided options (exact string)",
    "reasoning": "1-2 sentence explanation from your persona's perspective",
    "willingness_score": 1-10 (1=definitely no, 10=definitely yes),
    "key_concern": "your biggest concern or factor"
}

Be realistic. Consider your income, life stage, personality, and Singapore's social context."""

    user_prompt = f"""PERSONA:
{persona}

{f'CONTEXT: {context}' if context else ''}

SURVEY QUESTION:
{question}

OPTIONS:
{json.dumps(options, ensure_ascii=False)}

Answer as this person would. Be authentic to the persona."""

    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 200,
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )

        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)
            result = json.loads(content)
            result["tokens_used"] = tokens
            result["cost_usd"] = tokens * 0.001 / 1000
            return result
        else:
            logger.warning(f"API error {resp.status_code}: {resp.text[:100]}")
            return {"choice": options[0], "reasoning": "API error fallback",
                    "willingness_score": 5, "key_concern": "N/A",
                    "tokens_used": 0, "cost_usd": 0}

    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        return {"choice": options[0], "reasoning": f"Error: {e}",
                "willingness_score": 5, "key_concern": "N/A",
                "tokens_used": 0, "cost_usd": 0}


# ============================================================
# CLIENT SCENARIOS
# ============================================================

CLIENT_A = {
    "name": "AIA Singapore (Insurance)",
    "name_zh": "友邦保险新加坡",
    "description": "AIA wants to assess demand for a new Critical Illness insurance product",
    "description_zh": "友邦保险想评估一款新重疾险产品的市场需求",
    "question": "A major insurance company is offering a new Critical Illness (CI) insurance plan that covers 37 critical illnesses including cancer, heart attack, and stroke. The premium is $200/month for $200,000 coverage. Would you consider purchasing this?",
    "question_zh": "一家保险公司推出了新的重疾险计划，覆盖37种重大疾病（含癌症、心脏病、中风等），月保费$200，保额$200,000。你会考虑购买吗？",
    "options": [
        "Definitely yes — I need CI coverage",
        "Probably yes — but need to compare prices",
        "Maybe — depends on my budget",
        "Probably no — too expensive",
        "Definitely no — not interested in insurance"
    ],
    "context": "Singapore healthcare costs are rising. MediShield Life covers basic hospitalization but not income loss from critical illness. The average CI treatment cost is $100,000-$300,000.",
}

CLIENT_B = {
    "name": "HDB (Government Housing)",
    "name_zh": "建屋发展局（HDB）",
    "description": "HDB wants to gauge demand for new BTO flats in Punggol",
    "description_zh": "HDB 想评估榜鹅新BTO的需求",
    "question": "HDB is launching a new Build-To-Order (BTO) project in Punggol with 3-room ($250K), 4-room ($380K), and 5-room ($520K) flats. The estimated completion is 2030. Would you consider applying?",
    "question_zh": "HDB在榜鹅推出新BTO项目，3房式（$250K）、4房式（$380K）、5房式（$520K），预计2030年交付。你会考虑申请吗？",
    "options": [
        "Definitely yes — I need a new flat",
        "Probably yes — good location and price",
        "Maybe — but prefer other areas",
        "Probably no — already have a home",
        "Definitely no — not eligible or interested"
    ],
    "context": "Punggol is a mature estate with MRT connectivity (Punggol MRT, Cross Island Line coming in 2032). New BTO flats have 4-5 year waiting time. First-timers get priority allocation.",
}


# ============================================================
# ANALYSIS
# ============================================================
def analyze_responses(agents_df: pd.DataFrame, responses: list,
                      client: dict) -> dict:
    """Analyze aggregated responses with demographic breakdowns."""
    n = len(responses)

    # Overall distribution
    choices = [r.get("choice", "Unknown") for r in responses]
    choice_counts = Counter(choices)

    # Willingness scores
    scores = [r.get("willingness_score", 5) for r in responses]
    avg_score = np.mean(scores)

    # Key concerns
    concerns = [r.get("key_concern", "N/A") for r in responses]

    # Demographic breakdowns
    positive_choices = [c for c in client["options"][:2]]  # first 2 = positive

    breakdowns = {}

    # By age group
    age_groups = {"18-29": (18, 29), "30-44": (30, 44),
                  "45-59": (45, 59), "60+": (60, 100)}
    age_breakdown = {}
    for label, (lo, hi) in age_groups.items():
        mask = (agents_df["age"] >= lo) & (agents_df["age"] <= hi)
        group_indices = agents_df[mask].index.tolist()
        if not group_indices:
            continue
        group_choices = [responses[i]["choice"] for i in group_indices if i < len(responses)]
        positive_rate = sum(1 for c in group_choices if c in positive_choices) / max(len(group_choices), 1)
        age_breakdown[label] = {
            "n": len(group_choices),
            "positive_rate": round(positive_rate, 2),
            "avg_willingness": round(np.mean([responses[i].get("willingness_score", 5)
                                               for i in group_indices if i < len(responses)]), 1),
        }
    breakdowns["by_age"] = age_breakdown

    # By income level
    income_groups = {"<$3K": (0, 2999), "$3K-$7K": (3000, 6999),
                     "$7K-$15K": (7000, 14999), "$15K+": (15000, 99999)}
    income_breakdown = {}
    for label, (lo, hi) in income_groups.items():
        mask = (agents_df["monthly_income"] >= lo) & (agents_df["monthly_income"] <= hi)
        group_indices = agents_df[mask].index.tolist()
        if not group_indices:
            continue
        group_choices = [responses[i]["choice"] for i in group_indices if i < len(responses)]
        positive_rate = sum(1 for c in group_choices if c in positive_choices) / max(len(group_choices), 1)
        income_breakdown[label] = {
            "n": len(group_choices),
            "positive_rate": round(positive_rate, 2),
        }
    breakdowns["by_income"] = income_breakdown

    # By housing
    housing_breakdown = {}
    for ht in agents_df["housing_type"].unique():
        mask = agents_df["housing_type"] == ht
        group_indices = agents_df[mask].index.tolist()
        if not group_indices or len(group_indices) < 2:
            continue
        group_choices = [responses[i]["choice"] for i in group_indices if i < len(responses)]
        positive_rate = sum(1 for c in group_choices if c in positive_choices) / max(len(group_choices), 1)
        housing_breakdown[ht] = {
            "n": len(group_choices),
            "positive_rate": round(positive_rate, 2),
        }
    breakdowns["by_housing"] = housing_breakdown

    # Cost
    total_tokens = sum(r.get("tokens_used", 0) for r in responses)
    total_cost = sum(r.get("cost_usd", 0) for r in responses)

    report = {
        "client": client["name"],
        "client_zh": client["name_zh"],
        "question": client["question"],
        "n_respondents": n,
        "timestamp": str(datetime.now()),
        "overall": {
            "choice_distribution": dict(choice_counts),
            "avg_willingness_score": round(avg_score, 1),
            "positive_rate": round(
                sum(1 for c in choices if c in positive_choices) / n, 2),
        },
        "breakdowns": breakdowns,
        "sample_concerns": concerns[:10],
        "sample_reasoning": [r.get("reasoning", "") for r in responses[:5]],
        "cost": {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "cost_per_agent": round(total_cost / max(n, 1), 4),
        },
    }

    return report


def print_report(report: dict):
    """Print a formatted report."""
    print("\n" + "=" * 70)
    print(f"  CLIENT: {report['client']} / {report['client_zh']}")
    print("=" * 70)
    print(f"  Respondents: {report['n_respondents']}")
    print(f"  Positive rate: {report['overall']['positive_rate']:.0%}")
    print(f"  Avg willingness: {report['overall']['avg_willingness_score']}/10")
    print()

    print("  CHOICE DISTRIBUTION:")
    for choice, count in sorted(report["overall"]["choice_distribution"].items(),
                                 key=lambda x: -x[1]):
        pct = count / report["n_respondents"]
        bar = "█" * int(pct * 30)
        print(f"    {pct:5.0%} {bar} {choice} ({count})")
    print()

    print("  BY AGE GROUP:")
    for age, data in report["breakdowns"].get("by_age", {}).items():
        print(f"    {age}: positive={data['positive_rate']:.0%}, "
              f"willingness={data.get('avg_willingness', 'N/A')}/10 (n={data['n']})")
    print()

    print("  BY INCOME:")
    for inc, data in report["breakdowns"].get("by_income", {}).items():
        print(f"    {inc}: positive={data['positive_rate']:.0%} (n={data['n']})")
    print()

    print("  SAMPLE CONCERNS:")
    for i, concern in enumerate(report.get("sample_concerns", [])[:5]):
        print(f"    {i+1}. {concern}")
    print()

    print(f"  COST: ${report['cost']['total_cost_usd']:.4f} "
          f"({report['cost']['total_tokens']} tokens)")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================
def run_client_scenario(client: dict, agents_df: pd.DataFrame) -> dict:
    """Run one client scenario with all agents."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running scenario: {client['name']}")
    logger.info(f"Question: {client['question'][:80]}...")
    logger.info(f"Agents: {len(agents_df)}")
    logger.info(f"{'='*60}")

    responses = []
    for i in range(len(agents_df)):
        agent = agents_df.iloc[i].to_dict()
        persona = agent_to_persona(agent)

        logger.info(f"  Agent {i+1}/{len(agents_df)}: "
                    f"{agent['age']}y {agent['gender']} {agent['ethnicity']} "
                    f"${agent.get('monthly_income', 0):,.0f}/mo "
                    f"{agent.get('housing_type', '?')}")

        result = ask_agent(
            persona=persona,
            question=client["question"],
            options=client["options"],
            context=client["context"],
        )

        logger.info(f"    → {result.get('choice', '?')[:50]} "
                    f"(willingness={result.get('willingness_score', '?')}/10)")
        responses.append(result)

        # Rate limiting (DeepSeek allows ~10 req/s)
        time.sleep(0.15)

    report = analyze_responses(agents_df, responses, client)
    return report


def main():
    start = datetime.now()

    # Load stratified sample
    logger.info("Loading agents from Supabase...")
    agents_df = load_agents_from_supabase(n=N_AGENTS, seed=SEED)

    logger.info(f"Sample demographics:")
    logger.info(f"  Age: {agents_df['age'].min()}-{agents_df['age'].max()}, "
                f"median={agents_df['age'].median():.0f}")
    logger.info(f"  Gender: {agents_df['gender'].value_counts().to_dict()}")
    logger.info(f"  Ethnicity: {agents_df['ethnicity'].value_counts().to_dict()}")
    logger.info(f"  Income: median=${agents_df['monthly_income'].median():,.0f}")

    output_dir = Path(__file__).parent.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run Client A: Insurance
    report_a = run_client_scenario(CLIENT_A, agents_df)
    print_report(report_a)

    # Run Client B: HDB
    report_b = run_client_scenario(CLIENT_B, agents_df)
    print_report(report_b)

    # Save reports
    combined = {
        "run_timestamp": str(datetime.now()),
        "total_elapsed_seconds": round((datetime.now() - start).total_seconds(), 1),
        "sample_size": N_AGENTS,
        "client_a_insurance": report_a,
        "client_b_hdb": report_b,
    }

    report_path = output_dir / "client_simulation_demo.json"
    with open(report_path, "w") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"\nReports saved to {report_path}")

    total_cost = (report_a["cost"]["total_cost_usd"] +
                  report_b["cost"]["total_cost_usd"])
    print(f"\n{'='*70}")
    print(f"DEMO COMPLETE")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Total time: {(datetime.now() - start).total_seconds():.0f}s")
    print(f"Report: {report_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
