"""
Social propagation: simulate word-of-mouth spreading through the social graph.

Flow:
  1. Agents who received info → LLM evaluates reaction intensity (batch async)
  2. High-intensity agents spread to their connections (probability-weighted)
  3. Spread messages are "retold" — slightly transformed by the spreader's persona

LLM is only called for agents who actually received stimuli.
"""

import random
import logging

from engine.v3.persona_builder import build_persona
from engine.v3.llm_client import LLMClient

logger = logging.getLogger(__name__)

REACTION_SYSTEM = """You are a behavioral analyst estimating how a specific respondent would react to information they just received.

Respond in JSON:
{
    "intensity": 1-10 (how strongly this respondent reacts, 10=extremely strong),
    "sentiment": "positive" | "negative" | "neutral",
    "would_share": true | false (would this respondent tell friends/family?),
    "one_line_reaction": "this respondent's likely gut reaction in one sentence"
}

Base your estimate on the respondent's demographic profile, personality traits, and life circumstances. Different profiles should produce different reactions."""


async def propagate(
    graph: dict,
    agents_dict: dict,
    exposures: dict,
    llm: LLMClient,
    day: int,
) -> tuple[dict, dict]:
    """
    Evaluate reactions and propagate through social graph.

    Args:
        graph: social graph {agent_id: [connections]}
        agents_dict: {agent_id: agent_dict}
        exposures: {agent_id: [info_items]} from info_injector
        llm: LLMClient instance
        day: current day number

    Returns:
        (social_inbox, reactions)
        social_inbox: {agent_id: [social_messages]} — what friends told them
        reactions: {agent_id: reaction_dict} — how exposed agents reacted
    """
    # Step 1: Identify agents who received stimuli
    stimulated = {a_id: items for a_id, items in exposures.items() if items}
    if not stimulated:
        logger.info(f"  Day {day} propagation: no stimulated agents")
        return {}, {}

    # Step 2: Batch LLM call for reactions
    prompts = []
    agent_ids = []
    for a_id, items in stimulated.items():
        agent = agents_dict.get(a_id)
        if not agent:
            continue
        persona = build_persona(agent)
        info_text = items[0]["content"]
        channel = items[0].get("channel", "social media")
        source = items[0].get("type", "ad")
        if source == "social":
            # Heard from a friend, not direct ad
            rel = items[0].get("relationship", "friend")
            user_prompt = f"PERSONA:\n{persona}\n\nYour {rel} told you:\n\"{info_text}\"\n\nHow do you react?"
        else:
            user_prompt = f"PERSONA:\n{persona}\n\nYou just saw this on {channel}:\n\"{info_text}\"\n\nHow do you react?"
        prompts.append((REACTION_SYSTEM, user_prompt))
        agent_ids.append(a_id)

    logger.info(f"  Day {day} propagation: evaluating {len(prompts)} reactions...")
    results = await llm.batch_async(prompts)

    # Step 3: Parse reactions
    reactions = {}
    for a_id, result in zip(agent_ids, results):
        reactions[a_id] = {
            "intensity": min(10, max(1, int(result.get("intensity", 3)))),
            "sentiment": result.get("sentiment", "neutral"),
            "would_share": result.get("would_share", False),
            "one_line": result.get("one_line_reaction", ""),
            "tokens_used": result.get("tokens_used", 0),
            "cost_usd": result.get("cost_usd", 0),
        }

    # Step 4: Spread through social graph
    social_inbox = {}
    spread_count = 0

    for a_id, reaction in reactions.items():
        if not reaction["would_share"] or reaction["intensity"] < 4:
            continue

        connections = graph.get(a_id, [])
        for conn in connections:
            target_id = conn["target"]
            # Spread probability = connection strength x intensity / 10
            spread_prob = conn["strength"] * reaction["intensity"] / 10
            if conn["type"] == "family":
                spread_prob = min(1.0, spread_prob * 1.5)

            if random.random() < spread_prob:
                if target_id not in social_inbox:
                    social_inbox[target_id] = []
                social_inbox[target_id].append({
                    "type": "social",
                    "from_agent": a_id,
                    "relationship": conn["type"],
                    "content": reaction["one_line"],
                    "sender_sentiment": reaction["sentiment"],
                    "day": day,
                })
                spread_count += 1

    logger.info(f"  Day {day} propagation: {len([r for r in reactions.values() if r['would_share']])} "
                f"sharers -> {spread_count} messages to {len(social_inbox)} agents")

    return social_inbox, reactions
