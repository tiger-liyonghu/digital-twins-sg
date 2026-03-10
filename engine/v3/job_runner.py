"""
Job Runner: poll pending simulation jobs, execute, write results.

Flow:
  1. Poll simulation_jobs WHERE status = 'pending'
  2. For each job: sample agents -> build persona -> LLM (async batch) -> aggregate
  3. Write agent_responses + update job result + status = 'completed'

Performance:
  - Async concurrent LLM calls (30 parallel) -> 1000 agents in ~2-3 min vs 67 min serial
  - Batched DB inserts (100 per batch)
  - Cancel check during progress callbacks
"""

import json
import time
import asyncio
import logging
import random
from datetime import datetime, timezone

from engine.v3.db import get_client
from engine.v3.sampler import sample_agents
from engine.v3.persona_builder import build_persona
from engine.v3.llm_client import LLMClient
from engine.v3.aggregator import aggregate_responses
from engine.society.society_runner import run_society_job

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a survey research analyst estimating how a specific respondent would answer a question. You do NOT know the outcome of any real-world event. Estimate based ONLY on the respondent's demographic profile, personality, and life circumstances.

Respond in JSON:
{
    "probabilities": {"option_text": 0.XX, ...},
    "reasoning": "1-2 sentence explanation of why this respondent's profile leads to this probability distribution"
}

Rules:
- Assign a probability (0.00 to 1.00) to EVERY option. Probabilities must sum to 1.00.
- Different respondent profiles SHOULD produce different distributions. A 75-year-old low-income Chinese retiree and a 28-year-old Indian professional may have very different views.
- Base your estimate on the respondent's age, ethnicity, income, education, personality traits, and life phase. Do NOT default to the most popular or socially desirable answer.
- There is no correct answer. Real populations show diverse opinions."""


def run_one_job(job: dict, llm: LLMClient) -> dict:
    """Execute a single simulation job with async LLM calls."""
    job_id = job["id"]
    question = job["question"]
    options = job.get("options", [])
    sample_size = job.get("sample_size", 200)
    filter_ = job.get("filter", {})
    topic_tags = job.get("topic_tags", None)

    sb = get_client()

    # Update status to running
    sb.table("simulation_jobs").update({
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", job_id).execute()

    logger.info(f"Job {job_id}: '{question}' (n={sample_size})")

    # Step 1: Sample agents
    agents = sample_agents(n=sample_size, mode="stratified", filter_=filter_)
    logger.info(f"  Sampled {len(agents)} agents")

    if not agents:
        logger.warning(f"  No agents sampled, marking as failed")
        sb.table("simulation_jobs").update({
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", job_id).execute()
        return {"total": 0, "distribution": {}}

    # Step 2: Build prompts for all agents (Verbalized Sampling + Reformulated)
    options_json = json.dumps(options, ensure_ascii=False)
    prompts = []
    for agent in agents:
        persona = build_persona(agent, topic_tags=topic_tags)
        user_prompt = (
            f"RESPONDENT PROFILE:\n{persona}\n\n"
            f"SURVEY QUESTION:\n{question}\n\n"
            f"OPTIONS:\n{options_json}\n\n"
            f"Estimate the probability distribution over these options for this specific respondent."
        )
        prompts.append((SYSTEM_PROMPT, user_prompt))

    # Cancel flag shared with progress callback
    cancelled = False

    def on_progress(done, total):
        nonlocal cancelled
        if cancelled:
            return
        # Update progress every 5% or every 5 agents (whichever is more frequent)
        step = max(1, min(total // 20, 5))
        if done % step == 0 or done == total:
            progress = round(done / total * 100, 1)
            try:
                sb.table("simulation_jobs").update({
                    "progress": progress,
                }).eq("id", job_id).execute()
            except Exception:
                pass
            logger.info(f"  Progress: {done}/{total} ({progress}%)")

        # Check cancel every 10 completions
        if done % 10 == 0:
            try:
                check = sb.table("simulation_jobs").select("status").eq("id", job_id).execute()
                if check.data and check.data[0]["status"] == "cancelled":
                    logger.info(f"  Job {job_id} cancelled at {done}/{total}")
                    cancelled = True
            except Exception:
                pass

    # Step 3: Async batch LLM calls
    if sample_size <= 5:
        # Small jobs: use sync for simplicity
        results = []
        for i, (sp, up) in enumerate(prompts):
            result = llm.ask(sp, up)
            results.append(result)
            on_progress(i + 1, len(prompts))
            if cancelled:
                break
    else:
        # Large jobs: async concurrent
        results = asyncio.run(llm.batch_async(prompts, on_progress=on_progress))

    if cancelled:
        return {"total": 0, "distribution": {}, "cancelled": True}

    # Step 4: Build responses — sample from Verbalized Sampling distributions
    responses = []
    for i, (agent, result) in enumerate(zip(agents, results)):
        choice, confidence = _sample_from_distribution(result, options)

        responses.append({
            "job_id": job_id,
            "agent_id": agent["agent_id"],
            "decision_layer": "llm" if result.get("model") != "fallback" else "rule",
            "choice": choice,
            "reasoning": result.get("reasoning", ""),
            "confidence": confidence,
            "llm_model": result.get("model", ""),
            "tokens_used": result.get("tokens_used", 0),
            "cost_usd": result.get("cost_usd", 0.0),
        })

    # Step 5: Write responses to DB
    logger.info(f"  Writing {len(responses)} responses...")
    _batch_insert_responses(sb, responses)

    # Step 6: Aggregate
    result = aggregate_responses(agents, responses)

    # Step 7: Update job as completed
    total_tokens = sum(r["tokens_used"] for r in responses)
    total_cost = sum(r["cost_usd"] for r in responses)

    sb.table("simulation_jobs").update({
        "status": "completed",
        "progress": 100.0,
        "result": json.dumps(result),
        "total_agents": len(agents),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", job_id).execute()

    logger.info(f"  Job {job_id} completed: {result['total']} responses, "
                f"{total_tokens} tokens, ${total_cost:.4f}")

    return result


def _sample_from_distribution(result: dict, options: list[str]) -> tuple[str, float]:
    """
    Verbalized Sampling: LLM returns probability distribution, we sample from it.

    If the LLM returned {"probabilities": {"Option A": 0.65, "Option B": 0.25, "Option C": 0.10}},
    we sample one choice weighted by these probabilities.

    Falls back to deterministic choice if probabilities are missing.
    """
    probs = result.get("probabilities", {})

    if probs and isinstance(probs, dict):
        # Match LLM's probability keys to actual option strings
        matched_probs = {}
        for opt in options:
            best_p = 0.0
            opt_lower = opt.lower().strip()
            for k, v in probs.items():
                k_lower = k.lower().strip()
                try:
                    p = float(v)
                except (ValueError, TypeError):
                    p = 0.0
                # Exact or substring match
                if k_lower == opt_lower or k_lower in opt_lower or opt_lower in k_lower:
                    best_p = max(best_p, p)
            matched_probs[opt] = best_p

        # Normalize if probabilities don't sum to 1
        total_p = sum(matched_probs.values())
        if total_p > 0:
            weights = [matched_probs[opt] / total_p for opt in options]
        else:
            weights = [1.0 / len(options)] * len(options)

        # Weighted random sample
        chosen = random.choices(options, weights=weights, k=1)[0]
        confidence = matched_probs.get(chosen, 0.0)
        return chosen, round(confidence, 3)

    # Fallback: old-style single choice response
    choice = result.get("choice", "SKIPPED")
    choice = _match_option(choice, options)
    return choice, result.get("confidence", 0.5)


def _match_option(choice: str, options: list[str]) -> str:
    """Match LLM's choice text to the closest option."""
    if not options:
        return choice

    choice_lower = choice.lower().strip()

    # Exact match
    for opt in options:
        if opt.lower().strip() == choice_lower:
            return opt

    # Substring match
    for opt in options:
        if opt.lower() in choice_lower or choice_lower in opt.lower():
            return opt

    # Fallback: return first option
    return options[0] if options else choice


def _batch_insert_responses(sb, responses: list[dict], batch_size: int = 100):
    """Insert responses in batches."""
    for i in range(0, len(responses), batch_size):
        batch = responses[i:i+batch_size]
        try:
            sb.table("agent_responses").insert(batch).execute()
        except Exception as e:
            logger.error(f"  Response batch insert failed: {e}")
            for r in batch:
                try:
                    sb.table("agent_responses").insert(r).execute()
                except Exception as e2:
                    logger.error(f"  Single response insert failed: {e2}")


def poll_and_run(interval: int = 5, max_jobs: int = 0):
    """
    Main loop: poll for pending jobs and execute them.

    Args:
        interval: seconds between polls
        max_jobs: stop after N jobs (0 = run forever)
    """
    llm = LLMClient()
    jobs_done = 0

    logger.info(f"Job Runner started (async, concurrency={llm.concurrency}). Polling every {interval}s...")

    while True:
        sb = get_client()

        # Heartbeat
        try:
            sb.table("runner_status").upsert({
                "runner_id": "runner-1",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "active_jobs": 0,
            }).execute()
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

        # Poll for pending jobs
        try:
            result = sb.table("simulation_jobs") \
                .select("*") \
                .eq("status", "pending") \
                .order("created_at") \
                .limit(1) \
                .execute()
        except Exception as e:
            logger.warning(f"Poll failed: {e}")
            time.sleep(interval)
            continue

        if result.data:
            job = result.data[0]
            # Deserialize JSON fields from DB
            for field in ("options", "filter", "strata", "campaign"):
                if isinstance(job.get(field), str):
                    try:
                        job[field] = json.loads(job[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            try:
                mode = job.get("sim_mode", "survey")
                if mode == "society":
                    logger.info(f"Routing job {job['id']} to Society Mode runner")
                    result = run_society_job(job, llm)
                else:
                    result = run_one_job(job, llm)
                if result and result.get("cancelled"):
                    logger.info(f"Job {job['id']} was cancelled, skipping.")
                else:
                    jobs_done += 1
            except Exception as e:
                logger.error(f"Job {job['id']} failed: {e}")
                # Don't overwrite 'cancelled' status
                try:
                    check = sb.table("simulation_jobs").select("status").eq("id", job["id"]).execute()
                    if check.data and check.data[0]["status"] != "cancelled":
                        sb.table("simulation_jobs").update({
                            "status": "failed",
                        }).eq("id", job["id"]).execute()
                except Exception:
                    pass

            if max_jobs > 0 and jobs_done >= max_jobs:
                logger.info(f"Completed {jobs_done} jobs. Stopping.")
                break
        else:
            time.sleep(interval)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    max_jobs = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    poll_and_run(interval=5, max_jobs=max_jobs)
