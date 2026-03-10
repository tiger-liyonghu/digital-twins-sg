"""
Information injector: determine which agents see what information each day.

Pure rule engine — zero LLM calls. Fast and cheap.

Channels are inferred from agent demographics:
  - Young (18-34): Instagram, TikTok, Xiaohongshu, YouTube
  - Middle (35-54): Facebook, WhatsApp, Straits Times, CNA
  - Senior (55+): Straits Times, TV, WhatsApp, print media
"""

import random
import logging

logger = logging.getLogger(__name__)

# Channel affinity by age group
CHANNEL_AFFINITY = {
    "young": {"instagram", "tiktok", "xiaohongshu", "youtube", "telegram"},
    "middle": {"facebook", "whatsapp", "straits_times", "cna", "linkedin"},
    "senior": {"straits_times", "tv", "whatsapp", "print", "radio"},
}


def inject_info(
    agents: list[dict],
    campaign: dict,
    day: int = 1,
    decay_rate: float = 0.15,
) -> dict:
    """
    Determine ad/info exposure for each agent on a given day.

    Args:
        agents: list of agent dicts
        campaign: {
            "message": str,          # The ad/news content
            "brand": str,            # Brand name
            "channels": ["instagram", "facebook", ...],
            "target_filter": {"age_min": 18, "gender": "Female", ...},
            "base_exposure_rate": 0.3,  # Day 1 base probability
            "type": "ad" | "news" | "policy"
        }
        day: current simulation day (1-indexed)
        decay_rate: how much exposure drops each day (ad fatigue)

    Returns:
        {agent_id: [info_item, ...]}  — empty list = no exposure
    """
    exposures = {}
    base_rate = campaign.get("base_exposure_rate", 0.3)
    # Exposure decays as campaign ages (ad fatigue)
    day_rate = base_rate * (1 - decay_rate) ** (day - 1)
    campaign_channels = set(campaign.get("channels", []))
    target_filter = campaign.get("target_filter", {})
    exposed_count = 0

    for agent in agents:
        a_id = agent["agent_id"]
        exposures[a_id] = []

        # Check target filter
        if not _matches_target(agent, target_filter):
            continue

        # Determine agent's channels
        age = agent.get("age", 30)
        if age < 35:
            agent_channels = CHANNEL_AFFINITY["young"]
        elif age < 55:
            agent_channels = CHANNEL_AFFINITY["middle"]
        else:
            agent_channels = CHANNEL_AFFINITY["senior"]

        # Channel overlap = higher exposure probability
        overlap = campaign_channels & agent_channels
        if not overlap:
            continue

        # More channel overlap = higher chance
        channel_boost = len(overlap) / max(len(campaign_channels), 1)
        final_rate = day_rate * (0.5 + 0.5 * channel_boost)

        # Income/education can affect media consumption
        if agent.get("education_level", "") in ("university", "postgraduate"):
            final_rate *= 1.1  # Higher media consumption

        if random.random() < final_rate:
            exposures[a_id].append({
                "type": campaign.get("type", "ad"),
                "content": campaign["message"],
                "brand": campaign.get("brand", ""),
                "channel": random.choice(list(overlap)),
                "day": day,
            })
            exposed_count += 1

    logger.info(f"Day {day}: {exposed_count}/{len(agents)} agents exposed "
                f"(rate={day_rate:.1%})")
    return exposures


def _matches_target(agent: dict, target_filter: dict) -> bool:
    """Check if agent matches campaign targeting criteria."""
    if not target_filter:
        return True

    age = agent.get("age", 30)
    if target_filter.get("age_min") and age < target_filter["age_min"]:
        return False
    if target_filter.get("age_max") and age > target_filter["age_max"]:
        return False
    if target_filter.get("gender"):
        if agent.get("gender", "").upper()[0:1] != target_filter["gender"].upper()[0:1]:
            return False
    if target_filter.get("ethnicity"):
        if agent.get("ethnicity", "").lower() != target_filter["ethnicity"].lower():
            return False
    if target_filter.get("planning_area"):
        if agent.get("planning_area", "").lower() != target_filter["planning_area"].lower():
            return False
    if target_filter.get("income_min"):
        if (agent.get("monthly_income") or 0) < target_filter["income_min"]:
            return False

    return True
