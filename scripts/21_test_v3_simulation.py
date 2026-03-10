"""
Script 21: End-to-end test of V3 simulation pipeline.

Creates a job, runs it with 20 agents, displays results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    from engine.v3.db import get_client
    from engine.v3.job_runner import run_one_job
    from engine.v3.llm_client import LLMClient

    sb = get_client()
    llm = LLMClient()

    # Create a test job
    job_data = {
        "question": "新加坡政府宣布GST将从9%涨到10%，你会怎么调整消费？",
        "options": json.dumps([
            "大幅减少消费",
            "适当减少非必要开支",
            "不会改变消费习惯",
            "会趁涨价前多买一些"
        ]),
        "sample_size": 20,
        "filter": json.dumps({"age_min": 18}),
        "strata": json.dumps(["age_group", "gender", "ethnicity"]),
    }

    result = sb.table("simulation_jobs").insert(job_data).execute()
    job = result.data[0]
    job_id = job["id"]
    logger.info(f"Created test job: {job_id}")

    # Deserialize JSON fields for the runner
    job["options"] = json.loads(job["options"])
    job["filter"] = json.loads(job["filter"])
    job["strata"] = json.loads(job["strata"])

    # Run the job
    result = run_one_job(job, llm)

    # Display results
    print("\n" + "=" * 60)
    print("SIMULATION RESULT")
    print("=" * 60)
    print(f"Question: {job_data['question']}")
    print(f"Sample size: {result['total']}")
    print()

    print("Overall distribution:")
    for option, pct in sorted(result["percentages"].items(), key=lambda x: -x[1]):
        count = result["distribution"].get(option, 0)
        bar = "█" * int(pct / 2)
        print(f"  {option}: {count} ({pct}%) {bar}")

    print()

    # Age breakdown
    if "age_group" in result.get("breakdowns", {}):
        print("By age group:")
        for age_group, data in sorted(result["breakdowns"]["age_group"].items()):
            top_choice = max(data["percentages"].items(), key=lambda x: x[1])
            print(f"  {age_group} (n={data['total']}): {top_choice[0]} ({top_choice[1]}%)")

    # Income breakdown
    if "income_band" in result.get("breakdowns", {}):
        print("\nBy income band:")
        for band, data in sorted(result["breakdowns"]["income_band"].items()):
            top_choice = max(data["percentages"].items(), key=lambda x: x[1])
            print(f"  ${band} (n={data['total']}): {top_choice[0]} ({top_choice[1]}%)")

    print(f"\nLLM stats: {llm.total_calls} calls, {llm.total_tokens} tokens, ${llm.total_cost:.4f}")


if __name__ == "__main__":
    main()
