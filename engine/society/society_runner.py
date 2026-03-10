"""
Society Mode runner: 7-day simulation with social propagation.

Flow per day:
  1. Info injection (rule engine, 0 LLM)
  2. Merge social inbox from previous day
  3. Propagation: reaction evaluation + social spread (async LLM)
  4. Decision: exposed agents make choices (async LLM)
  5. Memory update (write to DB)

Typical 200-agent, 7-day run:
  - LLM calls: ~600-1200 (only exposed/stimulated agents)
  - Time: ~5-10 min with concurrency=30
  - Cost: ~$0.5-1.5
"""

import json
import random
import asyncio
import logging
from datetime import datetime, timezone

from engine.v3.db import get_client
from engine.v3.sampler import sample_agents
from engine.v3.persona_builder import build_persona
from engine.v3.llm_client import LLMClient
from engine.v3.aggregator import aggregate_responses
from engine.society.social_graph import build_social_graph, get_graph_stats
from engine.society.info_injector import inject_info
from engine.society.propagation import propagate

logger = logging.getLogger(__name__)

NUM_DAYS = 7

DECISION_SYSTEM = """You are a survey research analyst estimating how a specific respondent would answer a question after exposure to social information. You do NOT know the outcome of any real-world event.

Respond in JSON:
{
    "probabilities": {"option_text": 0.XX, ...},
    "reasoning": "1-2 sentence explanation based on respondent profile and social exposure"
}

Rules:
- Assign a probability (0.00 to 1.00) to EVERY option. Probabilities must sum to 1.00.
- Consider the respondent's persona, what information they've been exposed to, and their social circle's views.
- Different profiles and exposure histories SHOULD produce different distributions.
- Do NOT default to the most popular or socially desirable answer."""


def run_society_job(job: dict, llm: LLMClient) -> dict:
    """Execute a Society Mode simulation (7-day cycle)."""
    return asyncio.run(_run_society_async(job, llm))


async def _run_society_async(job: dict, llm: LLMClient) -> dict:
    job_id = job["id"]
    question = job["question"]
    options = job.get("options", [])
    sample_size = job.get("sample_size", 200)
    filter_ = job.get("filter", {})
    campaign = job.get("campaign", {})
    num_days = job.get("num_days") or NUM_DAYS

    sb = get_client()

    # Update status
    sb.table("simulation_jobs").update({
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", job_id).execute()

    logger.info(f"Society job {job_id}: '{question}' (n={sample_size}, days={num_days})")

    # Step 1: Sample agents
    agents = sample_agents(n=sample_size, mode="stratified", filter_=filter_)
    agents_dict = {a["agent_id"]: a for a in agents}
    logger.info(f"  Sampled {len(agents)} agents")

    if not agents:
        sb.table("simulation_jobs").update({"status": "failed"}).eq("id", job_id).execute()
        return {"total": 0, "distribution": {}}

    # Step 2: Build social graph
    graph = build_social_graph(agents)
    graph_stats = get_graph_stats(graph)
    logger.info(f"  Graph: {graph_stats['total_edges']} edges, avg degree {graph_stats['avg_degree']}")

    # Step 3: 7-day simulation loop
    daily_results = []
    cumulative_exposed = set()
    cumulative_reactions = {}  # agent_id -> list of reactions over days
    social_inbox = {}  # Carries over between days
    total_tokens = 0
    total_cost = 0.0
    cancelled = False

    for day in range(1, num_days + 1):
        # Check cancellation
        try:
            check = sb.table("simulation_jobs").select("status").eq("id", job_id).execute()
            if check.data and check.data[0]["status"] == "cancelled":
                logger.info(f"  Job {job_id} cancelled at day {day}")
                cancelled = True
                break
        except Exception:
            pass

        logger.info(f"  === Day {day}/{num_days} ===")

        # Phase 1: Info injection (0 LLM)
        exposures = inject_info(agents, campaign, day=day)

        # Phase 2: Merge social inbox from previous day's propagation
        for a_id, msgs in social_inbox.items():
            if a_id in exposures:
                exposures[a_id].extend(msgs)
            else:
                exposures[a_id] = msgs

        # Track cumulative exposure
        day_exposed = {a_id for a_id, items in exposures.items() if items}
        new_exposed = day_exposed - cumulative_exposed
        cumulative_exposed.update(day_exposed)

        # Phase 3: Propagation — reaction + social spread (LLM)
        social_inbox, reactions = await propagate(graph, agents_dict, exposures, llm, day)

        # Track reactions
        for a_id, reaction in reactions.items():
            if a_id not in cumulative_reactions:
                cumulative_reactions[a_id] = []
            cumulative_reactions[a_id].append({"day": day, **reaction})

        # Accumulate costs
        day_tokens = sum(r.get("tokens_used", 0) for r in reactions.values())
        day_cost = sum(r.get("cost_usd", 0) for r in reactions.values())
        total_tokens += day_tokens
        total_cost += day_cost

        # Daily summary
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for r in reactions.values():
            sentiment_counts[r.get("sentiment", "neutral")] += 1

        daily_results.append({
            "day": day,
            "exposed_today": len(day_exposed),
            "new_exposed": len(new_exposed),
            "cumulative_exposed": len(cumulative_exposed),
            "reactions": len(reactions),
            "social_spread": len(social_inbox),
            "sentiment": sentiment_counts,
            "avg_intensity": round(sum(r["intensity"] for r in reactions.values()) / max(len(reactions), 1), 1),
            "tokens": day_tokens,
            "cost": round(day_cost, 4),
        })

        # Update progress
        progress = round(day / num_days * 100, 1)
        try:
            sb.table("simulation_jobs").update({"progress": progress}).eq("id", job_id).execute()
        except Exception:
            pass

    if cancelled:
        return {"total": 0, "distribution": {}, "cancelled": True}

    # Step 4: Final decision round — all exposed agents answer the question
    logger.info(f"  Final decision round: {len(cumulative_exposed)} exposed agents...")
    options_str = "\n".join(f"- {opt}" for opt in options)
    prompts = []
    decision_agent_ids = []

    for a_id in cumulative_exposed:
        agent = agents_dict.get(a_id)
        if not agent:
            continue
        persona = build_persona(agent)

        # Build context from their experience
        agent_reactions = cumulative_reactions.get(a_id, [])
        experience = ""
        if agent_reactions:
            experience = "Your recent experiences:\n"
            for r in agent_reactions[-3:]:  # Last 3 reactions
                experience += f"- Day {r['day']}: {r['one_line']} (felt {r['sentiment']})\n"

        user_prompt = f"PERSONA:\n{persona}\n\n{experience}\nQUESTION: {question}\n\nOPTIONS:\n{options_str}\n\nChoose one option and explain why."
        prompts.append((DECISION_SYSTEM, user_prompt))
        decision_agent_ids.append(a_id)

    # Also get decisions from unexposed agents (control group)
    unexposed = [a for a in agents if a["agent_id"] not in cumulative_exposed]
    for agent in unexposed:
        persona = build_persona(agent)
        options_json = json.dumps(options, ensure_ascii=False)
        user_prompt = (
            f"RESPONDENT PROFILE:\n{persona}\n\n"
            f"SURVEY QUESTION:\n{question}\n\n"
            f"OPTIONS:\n{options_json}\n\n"
            f"Estimate the probability distribution over these options for this specific respondent."
        )
        prompts.append((DECISION_SYSTEM, user_prompt))
        decision_agent_ids.append(agent["agent_id"])

    results = await llm.batch_async(prompts)
    total_tokens += sum(r.get("tokens_used", 0) for r in results)
    total_cost += sum(r.get("cost_usd", 0) for r in results)

    # Build responses — Verbalized Sampling
    responses = []
    for a_id, result in zip(decision_agent_ids, results):
        choice, confidence = _sample_from_distribution(result, options)
        responses.append({
            "job_id": job_id,
            "agent_id": a_id,
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

    # Step 6: Aggregate — standard + exposed vs unexposed comparison
    all_result = aggregate_responses(agents, responses)

    # Exposed group aggregate
    exposed_responses = [r for r in responses if r["agent_id"] in cumulative_exposed]
    exposed_agents = [a for a in agents if a["agent_id"] in cumulative_exposed]
    exposed_result = aggregate_responses(exposed_agents, exposed_responses) if exposed_responses else {"total": 0, "distribution": {}, "percentages": {}}

    # Unexposed (control) group aggregate
    unexposed_responses = [r for r in responses if r["agent_id"] not in cumulative_exposed]
    unexposed_agents = [a for a in agents if a["agent_id"] not in cumulative_exposed]
    control_result = aggregate_responses(unexposed_agents, unexposed_responses) if unexposed_responses else {"total": 0, "distribution": {}, "percentages": {}}

    # Build final result
    final_result = {
        **all_result,
        "mode": "society",
        "num_days": num_days,
        "graph_stats": graph_stats,
        "daily": daily_results,
        "exposed_group": {
            "total": exposed_result["total"],
            "percentages": exposed_result.get("percentages", {}),
        },
        "control_group": {
            "total": control_result["total"],
            "percentages": control_result.get("percentages", {}),
        },
        "campaign_reach": {
            "total_agents": len(agents),
            "total_exposed": len(cumulative_exposed),
            "reach_rate": round(len(cumulative_exposed) / max(len(agents), 1) * 100, 1),
        },
    }

    # Step 7: Update job
    sb.table("simulation_jobs").update({
        "status": "completed",
        "progress": 100.0,
        "result": json.dumps(final_result),
        "total_agents": len(agents),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", job_id).execute()

    logger.info(f"  Society job {job_id} completed: {final_result['total']} responses, "
                f"{len(cumulative_exposed)} exposed, {total_tokens} tokens, ${total_cost:.4f}")

    return final_result


def _sample_from_distribution(result: dict, options: list[str]) -> tuple[str, float]:
    """Verbalized Sampling: sample from LLM's probability distribution."""
    probs = result.get("probabilities", {})
    if probs and isinstance(probs, dict):
        matched = {}
        for opt in options:
            opt_l = opt.lower().strip()
            best_p = 0.0
            for k, v in probs.items():
                k_l = k.lower().strip()
                try:
                    p = float(v)
                except (ValueError, TypeError):
                    p = 0.0
                if k_l == opt_l or k_l in opt_l or opt_l in k_l:
                    best_p = max(best_p, p)
            matched[opt] = best_p
        total_p = sum(matched.values())
        if total_p > 0:
            weights = [matched[o] / total_p for o in options]
        else:
            weights = [1.0 / len(options)] * len(options)
        chosen = random.choices(options, weights=weights, k=1)[0]
        return chosen, round(matched.get(chosen, 0.0), 3)
    # Fallback
    choice = result.get("choice", "SKIPPED")
    choice = _match_option(choice, options)
    return choice, result.get("confidence", 0.5)


def _match_option(choice: str, options: list[str]) -> str:
    if not options:
        return choice
    choice_lower = choice.lower().strip()
    for opt in options:
        if opt.lower().strip() == choice_lower:
            return opt
    for opt in options:
        if opt.lower() in choice_lower or choice_lower in opt.lower():
            return opt
    return options[0] if options else choice


def _batch_insert_responses(sb, responses: list[dict], batch_size: int = 100):
    for i in range(0, len(responses), batch_size):
        batch = responses[i:i + batch_size]
        try:
            sb.table("agent_responses").insert(batch).execute()
        except Exception as e:
            logger.error(f"  Batch insert failed: {e}")
            for r in batch:
                try:
                    sb.table("agent_responses").insert(r).execute()
                except Exception as e2:
                    logger.error(f"  Single insert failed: {e2}")
