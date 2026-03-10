"""
Sampling engine: draw N agents from 172K population.

Three modes:
  - random: simple random sample
  - stratified: proportional stratified by age_group + gender + ethnicity
  - targeted: filtered subset (e.g., all Bedok residents aged 25-34)

Sampling is done SQL-side to avoid loading 172K rows into Python.
"""

import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def sample_agents(
    n: int = 200,
    mode: str = "stratified",
    filter_: Optional[dict] = None,
    strata: Optional[list] = None,
) -> list[dict]:
    """
    Sample N agents from Supabase.

    Args:
        n: number of agents to sample
        mode: "random", "stratified", or "targeted"
        filter_: optional filter dict, e.g. {"age_min": 18, "age_max": 65, "planning_area": "Bedok"}
        strata: stratification columns (default: age_group, gender, ethnicity)

    Returns:
        List of agent dicts with all fields needed for persona building.
    """
    from engine.v3.db import get_client
    sb = get_client()

    PERSONA_COLS = (
        "agent_id, age, age_group, gender, ethnicity, education_level, "
        "occupation, industry, planning_area, marital_status, "
        "monthly_income, income_band, housing_type, health_status, "
        "life_phase, residency_status, "
        "big5_o, big5_c, big5_e, big5_a, big5_n, "
        "risk_appetite, social_trust, religious_devotion, "
        "persona, professional_persona, cultural_background, "
        "hobbies_and_interests, career_goals_and_ambitions, "
        "data_source"
    )

    query = sb.table("agents").select(PERSONA_COLS)
    if filter_:
        query = _apply_filters(query, filter_)

    # Get total count for random offset calculation
    # Use try/except to handle Supabase free-tier statement timeout
    total_population = 172000  # fallback default
    try:
        count_query = sb.table("agents").select("agent_id", count="exact")
        if filter_:
            count_query = _apply_filters(count_query, filter_)
        count_result = count_query.limit(1).execute()
        total_population = count_result.count or total_population
    except Exception as e:
        logger.warning(f"Count query failed (using fallback {total_population}): {e}")

    if mode == "random":
        fetch_n = min(n * 3, 5000)
        offset = random.randint(0, max(0, total_population - fetch_n))
        result = query.range(offset, offset + fetch_n - 1).execute()
        agents = result.data

        if len(agents) > n:
            agents = random.sample(agents, n)

    elif mode == "targeted":
        result = query.limit(n).execute()
        agents = result.data

    else:
        # stratified: fetch a larger pool from random offset, then stratify client-side
        fetch_n = min(n * 5, 10000)
        offset = random.randint(0, max(0, total_population - fetch_n))
        result = query.range(offset, offset + fetch_n - 1).execute()
        pool = result.data

        if len(pool) <= n:
            agents = pool
        else:
            agents = _stratified_sample(pool, n, strata or ["age_group", "gender", "ethnicity"])

    logger.info(f"Sampled {len(agents)} agents (mode={mode}, requested={n})")
    return agents


def _apply_filters(query, filter_: dict):
    """Apply filter dict to a Supabase query. Ignore 'all' values."""
    def _val(key):
        v = filter_.get(key)
        if v is None or (isinstance(v, str) and v.lower() in ("all", "")):
            return None
        return v

    if _val("age_min"):
        query = query.gte("age", filter_["age_min"])
    if _val("age_max"):
        query = query.lte("age", filter_["age_max"])
    if _val("planning_area"):
        query = query.eq("planning_area", filter_["planning_area"])
    if _val("gender"):
        query = query.eq("gender", filter_["gender"])
    if _val("ethnicity"):
        query = query.eq("ethnicity", filter_["ethnicity"])
    if _val("education_level"):
        query = query.eq("education_level", filter_["education_level"])
    if _val("income_min"):
        query = query.gte("monthly_income", filter_["income_min"])
    if _val("income_max"):
        query = query.lte("monthly_income", filter_["income_max"])
    if _val("housing_type"):
        query = query.eq("housing_type", filter_["housing_type"])
    if _val("life_phase"):
        query = query.eq("life_phase", filter_["life_phase"])
    if _val("data_source"):
        query = query.eq("data_source", filter_["data_source"])
    return query


def _stratified_sample(pool: list[dict], n: int, strata: list[str]) -> list[dict]:
    """
    Proportional stratified sampling from a pool.
    Each stratum gets n * (stratum_size / pool_size) agents.
    """
    from collections import defaultdict

    # Group by strata key
    groups = defaultdict(list)
    for agent in pool:
        key = tuple(agent.get(s, "") for s in strata)
        groups[key].append(agent)

    total = len(pool)
    result = []

    for key, members in groups.items():
        # Proportional allocation
        k = max(1, round(n * len(members) / total))
        k = min(k, len(members))
        result.extend(random.sample(members, k))

    # Trim or pad to exactly n
    if len(result) > n:
        result = random.sample(result, n)
    elif len(result) < n:
        remaining = [a for a in pool if a not in result]
        extra = min(n - len(result), len(remaining))
        result.extend(random.sample(remaining, extra))

    return result
