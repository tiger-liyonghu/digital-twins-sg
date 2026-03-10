"""
Response aggregator: analyze simulation results with demographic breakdowns.
"""

from collections import Counter, defaultdict
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def aggregate_responses(
    agents: list[dict],
    responses: list[dict],
    breakdowns: Optional[list[str]] = None,
) -> dict:
    """
    Aggregate simulation responses with demographic breakdowns.

    Args:
        agents: list of agent dicts (from sampler)
        responses: list of response dicts with agent_id + choice
        breakdowns: demographic fields to cross-tabulate

    Returns:
        {
            "total": int,
            "distribution": {"option1": count, ...},
            "percentages": {"option1": pct, ...},
            "breakdowns": {
                "age_group": {"20-24": {"option1": count, ...}, ...},
                ...
            }
        }
    """
    if breakdowns is None:
        breakdowns = ["age_group", "gender", "ethnicity", "income_band", "housing_type", "education_level"]

    # Build agent lookup
    agent_map = {a["agent_id"]: a for a in agents}

    # Overall distribution
    choices = [r["choice"] for r in responses]
    total = len(choices)
    dist = dict(Counter(choices))

    if total == 0:
        return {"total": 0, "distribution": {}, "percentages": {}, "breakdowns": {}}

    pcts = {k: round(v / total * 100, 1) for k, v in dist.items()}

    # Breakdowns
    bd = {}
    for field in breakdowns:
        groups = defaultdict(lambda: Counter())
        for r in responses:
            agent = agent_map.get(r["agent_id"], {})
            group_val = agent.get(field, "Unknown")
            groups[group_val][r["choice"]] += 1

        # Convert to regular dicts and add percentages
        bd[field] = {}
        for group_val, counter in sorted(groups.items()):
            group_total = sum(counter.values())
            bd[field][group_val] = {
                "counts": dict(counter),
                "total": group_total,
                "percentages": {
                    k: round(v / group_total * 100, 1)
                    for k, v in counter.items()
                },
            }

    result = {
        "total": total,
        "distribution": dist,
        "percentages": pcts,
        "breakdowns": bd,
    }

    # Redistribute non-candidate options (e.g. "不投票", "Would not vote", "Undecided")
    adjusted = redistribute_non_candidate(pcts)
    if adjusted:
        result["adjusted_percentages"] = adjusted

    return result


# Keywords that identify non-candidate / abstention options
_ABSTAIN_KEYWORDS = [
    "不投票", "弃权", "不参与", "未决定", "不确定",
    "would not vote", "spoil vote", "undecided", "abstain",
    "not vote", "not sure", "no opinion",
]


def redistribute_non_candidate(pcts: dict) -> dict | None:
    """
    Redistribute abstention/undecided votes proportionally among real candidates.
    Returns adjusted percentages dict, or None if no redistribution needed.
    """
    abstain_keys = []
    candidate_keys = []

    for k in pcts:
        k_lower = k.lower().strip()
        if any(kw in k_lower for kw in _ABSTAIN_KEYWORDS):
            abstain_keys.append(k)
        else:
            candidate_keys.append(k)

    if not abstain_keys or not candidate_keys:
        return None

    abstain_total = sum(pcts[k] for k in abstain_keys)
    if abstain_total < 0.1:
        return None

    candidate_total = sum(pcts[k] for k in candidate_keys)
    if candidate_total <= 0:
        return None

    adjusted = {}
    for k in candidate_keys:
        share = pcts[k] / candidate_total
        adjusted[k] = round(pcts[k] + abstain_total * share, 1)

    return adjusted
