"""
Server-side stratified sampling from Supabase agents table.

Works for all simulation scenarios: backtest, client simulation, policy analysis.
Avoids loading all 172K+ agents — fetches only needed strata directly from DB.

REQUIRES database indexes (see docs/ENGINEERING_BRIEF_AGENT_INDEXES.md):
  CREATE INDEX idx_agents_strata ON agents (age_group, gender, residency_status);
  CREATE INDEX idx_agents_age_group ON agents (age_group);
  CREATE INDEX idx_agents_gender ON agents (gender);
"""

import random
import requests
import pandas as pd
import concurrent.futures
from lib.config import SUPABASE_URL, SUPABASE_KEY, AGENT_FIELDS

# Singapore age_group values in the agents table (5-year bins)
AGE_GROUPS_ALL = [
    "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
    "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79",
    "80-84", "85-89", "90-94", "95-99",
]

# Singapore Census citizen proportions by age-gender (21+ voters)
# Used for election backtests
CITIZEN_VOTER_STRATA = [
    (["20-24", "25-29"], "M", 0.08),
    (["20-24", "25-29"], "F", 0.08),
    (["30-34", "35-39"], "M", 0.10),
    (["30-34", "35-39"], "F", 0.11),
    (["40-44", "45-49"], "M", 0.10),
    (["40-44", "45-49"], "F", 0.10),
    (["50-54", "55-59"], "M", 0.09),
    (["50-54", "55-59"], "F", 0.09),
    (["60-64", "65-69"], "M", 0.07),
    (["60-64", "65-69"], "F", 0.08),
    (["70-74", "75-79", "80-84", "85-89", "90-94", "95-99"], "M", 0.04),
    (["70-74", "75-79", "80-84", "85-89", "90-94", "95-99"], "F", 0.06),
]

# General adult population strata (18+, all residency)
ADULT_STRATA = [
    (["15-19", "20-24"], "M", 0.08),
    (["15-19", "20-24"], "F", 0.08),
    (["25-29", "30-34"], "M", 0.11),
    (["25-29", "30-34"], "F", 0.11),
    (["35-39", "40-44"], "M", 0.10),
    (["35-39", "40-44"], "F", 0.10),
    (["45-49", "50-54"], "M", 0.09),
    (["45-49", "50-54"], "F", 0.09),
    (["55-59", "60-64"], "M", 0.07),
    (["55-59", "60-64"], "F", 0.07),
    (["65-69", "70-74", "75-79", "80-84", "85-89"], "M", 0.05),
    (["65-69", "70-74", "75-79", "80-84", "85-89"], "F", 0.05),
]


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def _fetch_stratum(age_groups, gender, n, residency=None, select=AGENT_FIELDS, seed=None):
    """
    Fetch n agents from a single stratum using server-side filtering.
    Retries up to 3 times with exponential backoff on failure.
    """
    import time as _time

    params = {
        "select": select,
        "gender": f"eq.{gender}",
        "order": "agent_id",
    }

    if len(age_groups) == 1:
        params["age_group"] = f"eq.{age_groups[0]}"
    else:
        params["age_group"] = f"in.({','.join(age_groups)})"

    if residency:
        params["residency_status"] = f"eq.{residency}"

    fetch_n = min(n * 5, 2000)
    headers = {**_headers(), "Range": f"0-{fetch_n - 1}"}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/agents",
                headers=headers,
                params=params,
                timeout=45,
            )
            if resp.status_code in (200, 206):
                data = resp.json()
                break
            elif resp.status_code == 500 and residency:
                # Fall back: drop residency filter, filter client-side
                params_fb = {k: v for k, v in params.items() if k != "residency_status"}
                resp2 = requests.get(
                    f"{SUPABASE_URL}/rest/v1/agents",
                    headers=headers,
                    params=params_fb,
                    timeout=45,
                )
                if resp2.status_code in (200, 206):
                    data = [a for a in resp2.json() if a.get("residency_status") == residency]
                    break
            # Retry on failure
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Retry {attempt+1}/{max_retries} for {gender} {age_groups} (status {resp.status_code}, wait {wait}s)")
                _time.sleep(wait)
            else:
                print(f"  WARNING: stratum {gender} {age_groups} fetch failed after {max_retries} attempts: {resp.status_code}")
                return []
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Retry {attempt+1}/{max_retries} for {gender} {age_groups} (timeout, wait {wait}s)")
                _time.sleep(wait)
            else:
                print(f"  WARNING: stratum {gender} {age_groups} timed out after {max_retries} attempts")
                return []

    if not data:
        return []

    rng = random.Random(seed)
    if len(data) > n:
        data = rng.sample(data, n)

    return data


def stratified_sample(n=1000, strata=None, residency=None, seed=42):
    """
    Draw a stratified random sample of n agents from Supabase.

    Args:
        n: Total sample size
        strata: List of (age_groups, gender, weight) tuples.
                Defaults to CITIZEN_VOTER_STRATA for election scenarios.
        residency: Filter by residency_status (e.g., "Citizen"). None = all.
        seed: Random seed for reproducibility.

    Returns:
        (pd.DataFrame, dict) — sampled agents and metadata
    """
    if strata is None:
        strata = CITIZEN_VOTER_STRATA

    all_agents = []
    meta = {"strata_counts": {}, "total_fetched": 0}

    # Parallel stratum fetching
    stratum_tasks = []
    for age_groups, gender, weight in strata:
        stratum_n = max(2, int(round(n * weight)))
        label = f"{gender} {'+'.join(age_groups)}"
        stratum_tasks.append((age_groups, gender, stratum_n, label))

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        future_map = {
            ex.submit(_fetch_stratum, ag, g, sn, residency=residency, seed=seed): (sn, label)
            for ag, g, sn, label in stratum_tasks
        }
        for future in concurrent.futures.as_completed(future_map):
            stratum_n, label = future_map[future]
            data = future.result()
            all_agents.extend(data)
            meta["strata_counts"][label] = len(data)
            print(f"  Stratum {label}: {len(data)}/{stratum_n}")

    random.Random(seed).shuffle(all_agents)
    meta["total_fetched"] = len(all_agents)

    if not all_agents:
        raise RuntimeError("No agents fetched. Check database indexes and filters.")

    df = pd.DataFrame(all_agents)
    print(f"Total sampled: {len(df)} agents")
    return df, meta


def simple_sample(n=100, age_min=None, age_max=None, gender=None,
                  residency=None, seed=42):
    """
    Simple random sample without census-weighted strata.
    Good for quick tests, client simulations, and non-election scenarios.

    Filters by age_group bins that overlap the requested age range.
    """
    # Map age range to age_group values
    if age_min is not None or age_max is not None:
        lo = age_min or 0
        hi = age_max or 99
        matching_groups = []
        for g in AGE_GROUPS_ALL:
            parts = g.split("-")
            g_lo, g_hi = int(parts[0]), int(parts[1])
            if g_hi >= lo and g_lo <= hi:
                matching_groups.append(g)
    else:
        matching_groups = AGE_GROUPS_ALL

    params = {
        "select": AGENT_FIELDS,
        "order": "agent_id",
    }
    if matching_groups and len(matching_groups) < len(AGE_GROUPS_ALL):
        if len(matching_groups) == 1:
            params["age_group"] = f"eq.{matching_groups[0]}"
        else:
            params["age_group"] = f"in.({','.join(matching_groups)})"
    if gender:
        params["gender"] = f"eq.{gender}"
    if residency:
        params["residency_status"] = f"eq.{residency}"

    # Fetch in pages (Supabase max 1000 per page)
    page_size = 1000
    fetch_n = min(n * 5, 10000)
    data = []
    offset = 0
    while offset < fetch_n:
        end = min(offset + page_size - 1, fetch_n - 1)
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/agents",
            headers={**_headers(), "Range": f"{offset}-{end}"},
            params=params,
            timeout=30,
        )
        if resp.status_code not in (200, 206):
            break
        page = resp.json()
        if not page:
            break
        data.extend(page)
        if len(page) < page_size:
            break  # last page
        offset += page_size
    if not data:
        # Fallback: remove residency filter if it causes timeout
        if residency:
            params_fb = {k: v for k, v in params.items() if k != "residency_status"}
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/agents",
                headers={**_headers(), "Range": f"0-{min(n * 5, 5000) - 1}"},
                params=params_fb,
                timeout=30,
            )
            if resp.status_code in (200, 206):
                data = [a for a in resp.json() if a.get("residency_status") == residency]
            else:
                raise RuntimeError(f"Agent query failed: {resp.status_code}")
        else:
            raise RuntimeError("Agent query returned no data")

    # Apply age_min/age_max precisely (age_group is 5-year bins, may overshoot)
    if age_min is not None:
        data = [a for a in data if a.get("age", 0) >= age_min]
    if age_max is not None:
        data = [a for a in data if a.get("age", 999) <= age_max]

    rng = random.Random(seed)
    if len(data) > n:
        data = rng.sample(data, n)

    print(f"Sampled {len(data)} agents (filters: age={age_min}-{age_max}, gender={gender}, residency={residency})")
    return pd.DataFrame(data)
