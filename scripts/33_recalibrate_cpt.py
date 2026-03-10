"""
Script 33: Incremental CPT Recalibration

Resamples marital_status, housing_type, education_level for all 172K agents
using the corrected CPT v2 from sg_distributions.py.

Strategy to minimize Supabase CPU:
1. Fetch agents in paginated batches (1000 at a time)
2. Resample locally using new CPTs (no LLM calls)
3. Group by (new_value) and batch update via .in_() — one DB call per unique value
4. Sleep between update batches to avoid CPU spikes
5. Skip agents whose values don't change

Usage:
    python scripts/33_recalibrate_cpt.py --dry-run     # Preview changes
    python scripts/33_recalibrate_cpt.py               # Execute updates
"""

import argparse
import logging
import random
import time
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

SUPABASE_URL = "https://rndfpyuuredtqncegygi.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzA4Nzk0NiwiZXhwIjoyMDg4NjYzOTQ2fQ.EMjLfr3N8RDpBPkVftYKCg1Pf6h4rOj8xfCXSuJIxQI"

# ════════════════════════════════════════════════════════════
# CORRECTED CPTs (v2) — matching GHS 2025 marginals
# ════════════════════════════════════════════════════════════

# P(marital_status | age_group, gender)
# Scaled from v1: S×1.228, M×1.125, D×1.421, W×0.430
MARITAL_CPT = {}
for age in ["0-4", "5-9", "10-14", "15-19"]:
    for g in ["M", "F"]:
        MARITAL_CPT[(age, g)] = {"Single": 1.0, "Married": 0.0, "Divorced": 0.0, "Widowed": 0.0}
MARITAL_CPT[("20-24", "M")] = {"Single": 0.96, "Married": 0.04, "Divorced": 0.0, "Widowed": 0.0}
MARITAL_CPT[("20-24", "F")] = {"Single": 0.92, "Married": 0.08, "Divorced": 0.0, "Widowed": 0.0}
MARITAL_CPT[("25-29", "M")] = {"Single": 0.793, "Married": 0.195, "Divorced": 0.012, "Widowed": 0.0}
MARITAL_CPT[("25-29", "F")] = {"Single": 0.639, "Married": 0.349, "Divorced": 0.012, "Widowed": 0.0}
MARITAL_CPT[("30-34", "M")] = {"Single": 0.438, "Married": 0.526, "Divorced": 0.036, "Widowed": 0.0}
MARITAL_CPT[("30-34", "F")] = {"Single": 0.315, "Married": 0.636, "Divorced": 0.049, "Widowed": 0.0}
MARITAL_CPT[("35-39", "M")] = {"Single": 0.255, "Married": 0.680, "Divorced": 0.061, "Widowed": 0.004}
MARITAL_CPT[("35-39", "F")] = {"Single": 0.193, "Married": 0.726, "Divorced": 0.074, "Widowed": 0.007}
MARITAL_CPT[("40-44", "M")] = {"Single": 0.183, "Married": 0.719, "Divorced": 0.087, "Widowed": 0.011}
MARITAL_CPT[("40-44", "F")] = {"Single": 0.152, "Married": 0.728, "Divorced": 0.101, "Widowed": 0.019}
MARITAL_CPT[("45-49", "M")] = {"Single": 0.162, "Married": 0.723, "Divorced": 0.100, "Widowed": 0.015}
MARITAL_CPT[("45-49", "F")] = {"Single": 0.133, "Married": 0.733, "Divorced": 0.103, "Widowed": 0.031}
MARITAL_CPT[("50-54", "M")] = {"Single": 0.143, "Married": 0.745, "Divorced": 0.089, "Widowed": 0.023}
MARITAL_CPT[("50-54", "F")] = {"Single": 0.115, "Married": 0.740, "Divorced": 0.093, "Widowed": 0.052}
MARITAL_CPT[("55-59", "M")] = {"Single": 0.123, "Married": 0.768, "Divorced": 0.078, "Widowed": 0.031}
MARITAL_CPT[("55-59", "F")] = {"Single": 0.108, "Married": 0.728, "Divorced": 0.084, "Widowed": 0.080}
MARITAL_CPT[("60-64", "M")] = {"Single": 0.102, "Married": 0.792, "Divorced": 0.066, "Widowed": 0.040}
MARITAL_CPT[("60-64", "F")] = {"Single": 0.102, "Married": 0.703, "Divorced": 0.074, "Widowed": 0.121}
MARITAL_CPT[("65-69", "M")] = {"Single": 0.082, "Married": 0.811, "Divorced": 0.054, "Widowed": 0.053}
MARITAL_CPT[("65-69", "F")] = {"Single": 0.097, "Married": 0.660, "Divorced": 0.064, "Widowed": 0.179}
MARITAL_CPT[("70-74", "M")] = {"Single": 0.060, "Married": 0.826, "Divorced": 0.042, "Widowed": 0.072}
MARITAL_CPT[("70-74", "F")] = {"Single": 0.092, "Married": 0.591, "Divorced": 0.053, "Widowed": 0.264}
for age in ["75-79", "80-84", "85-89", "90-94", "95-99", "100"]:
    MARITAL_CPT[(age, "M")] = {"Single": 0.051, "Married": 0.802, "Divorced": 0.030, "Widowed": 0.117}
    MARITAL_CPT[(age, "F")] = {"Single": 0.093, "Married": 0.423, "Divorced": 0.043, "Widowed": 0.441}

# P(housing_type | income_band)
# Calibrated to match GHS 2025: HDB_1_2 7.3%, HDB_3 16.6%, HDB_4 31.2%, HDB_5_EC 22.1%, Condo 17.9%, Landed 4.7%
HOUSING_CPT = {
    "0":           {"HDB_1_2": 0.164, "HDB_3": 0.280, "HDB_4": 0.341, "HDB_5_EC": 0.147, "Condo": 0.058, "Landed": 0.010},
    "1-1999":      {"HDB_1_2": 0.117, "HDB_3": 0.257, "HDB_4": 0.334, "HDB_5_EC": 0.178, "Condo": 0.095, "Landed": 0.019},
    "2000-3499":   {"HDB_1_2": 0.056, "HDB_3": 0.194, "HDB_4": 0.367, "HDB_5_EC": 0.236, "Condo": 0.119, "Landed": 0.028},
    "3500-4999":   {"HDB_1_2": 0.028, "HDB_3": 0.121, "HDB_4": 0.361, "HDB_5_EC": 0.274, "Condo": 0.179, "Landed": 0.037},
    "5000-6999":   {"HDB_1_2": 0.014, "HDB_3": 0.078, "HDB_4": 0.316, "HDB_5_EC": 0.295, "Condo": 0.242, "Landed": 0.055},
    "7000-9999":   {"HDB_1_2": 0.007, "HDB_3": 0.044, "HDB_4": 0.230, "HDB_5_EC": 0.278, "Condo": 0.347, "Landed": 0.094},
    "10000-14999": {"HDB_1_2": 0.004, "HDB_3": 0.027, "HDB_4": 0.141, "HDB_5_EC": 0.241, "Condo": 0.438, "Landed": 0.149},
    "15000+":      {"HDB_1_2": 0.004, "HDB_3": 0.018, "HDB_4": 0.096, "HDB_5_EC": 0.167, "Condo": 0.494, "Landed": 0.221},
}

# P(education | age_group) — 7 levels, merge Uni+PG on write
EDUCATION_CPT = {}
EDUCATION_CPT["0-4"]   = {"No_Formal": 1.0, "Primary": 0.0, "Secondary": 0.0, "Post_Secondary": 0.0, "Polytechnic": 0.0, "University": 0.0, "Postgraduate": 0.0}
EDUCATION_CPT["5-9"]   = {"No_Formal": 0.15, "Primary": 0.85, "Secondary": 0.0, "Post_Secondary": 0.0, "Polytechnic": 0.0, "University": 0.0, "Postgraduate": 0.0}
EDUCATION_CPT["10-14"] = {"No_Formal": 0.0, "Primary": 0.40, "Secondary": 0.60, "Post_Secondary": 0.0, "Polytechnic": 0.0, "University": 0.0, "Postgraduate": 0.0}
EDUCATION_CPT["15-19"] = {"No_Formal": 0.0, "Primary": 0.0, "Secondary": 0.45, "Post_Secondary": 0.35, "Polytechnic": 0.15, "University": 0.05, "Postgraduate": 0.0}
EDUCATION_CPT["20-24"] = {"No_Formal": 0.01, "Primary": 0.02, "Secondary": 0.10, "Post_Secondary": 0.20, "Polytechnic": 0.25, "University": 0.40, "Postgraduate": 0.02}
EDUCATION_CPT["25-29"] = {"No_Formal": 0.011, "Primary": 0.018, "Secondary": 0.073, "Post_Secondary": 0.240, "Polytechnic": 0.186, "University": 0.378, "Postgraduate": 0.094}
EDUCATION_CPT["30-34"] = {"No_Formal": 0.011, "Primary": 0.028, "Secondary": 0.083, "Post_Secondary": 0.241, "Polytechnic": 0.164, "University": 0.355, "Postgraduate": 0.118}
EDUCATION_CPT["35-39"] = {"No_Formal": 0.011, "Primary": 0.037, "Secondary": 0.101, "Post_Secondary": 0.241, "Polytechnic": 0.153, "University": 0.339, "Postgraduate": 0.118}
EDUCATION_CPT["40-44"] = {"No_Formal": 0.022, "Primary": 0.045, "Secondary": 0.144, "Post_Secondary": 0.255, "Polytechnic": 0.150, "University": 0.292, "Postgraduate": 0.092}
EDUCATION_CPT["45-49"] = {"No_Formal": 0.033, "Primary": 0.071, "Secondary": 0.176, "Post_Secondary": 0.270, "Polytechnic": 0.126, "University": 0.249, "Postgraduate": 0.075}
EDUCATION_CPT["50-54"] = {"No_Formal": 0.044, "Primary": 0.089, "Secondary": 0.196, "Post_Secondary": 0.253, "Polytechnic": 0.106, "University": 0.228, "Postgraduate": 0.084}
EDUCATION_CPT["55-59"] = {"No_Formal": 0.055, "Primary": 0.108, "Secondary": 0.206, "Post_Secondary": 0.235, "Polytechnic": 0.096, "University": 0.223, "Postgraduate": 0.077}
EDUCATION_CPT["60-64"] = {"No_Formal": 0.111, "Primary": 0.181, "Secondary": 0.225, "Post_Secondary": 0.196, "Polytechnic": 0.064, "University": 0.169, "Postgraduate": 0.054}
EDUCATION_CPT["65-69"] = {"No_Formal": 0.168, "Primary": 0.228, "Secondary": 0.199, "Post_Secondary": 0.158, "Polytechnic": 0.054, "University": 0.146, "Postgraduate": 0.047}
EDUCATION_CPT["70-74"] = {"No_Formal": 0.223, "Primary": 0.254, "Secondary": 0.180, "Post_Secondary": 0.138, "Polytechnic": 0.043, "University": 0.123, "Postgraduate": 0.039}
EDUCATION_CPT["75-79"] = {"No_Formal": 0.311, "Primary": 0.272, "Secondary": 0.162, "Post_Secondary": 0.099, "Polytechnic": 0.032, "University": 0.093, "Postgraduate": 0.031}
for age in ["80-84", "85-89", "90-94", "95-99", "100"]:
    EDUCATION_CPT[age] = {"No_Formal": 0.383, "Primary": 0.267, "Secondary": 0.133, "Post_Secondary": 0.097, "Polytechnic": 0.021, "University": 0.076, "Postgraduate": 0.023}


def sample_from_cpt(dist: dict, rng: random.Random) -> str:
    """Sample a category from a probability distribution."""
    cats = list(dist.keys())
    probs = list(dist.values())
    r = rng.random()
    cumsum = 0
    for cat, p in zip(cats, probs):
        cumsum += p
        if r < cumsum:
            return cat
    return cats[-1]


def resample_agent(agent: dict, rng: random.Random) -> dict:
    """Resample marital_status, housing_type, education_level for one agent."""
    age_group = agent["age_group"]
    gender = agent["gender"]
    income_band = agent["income_band"]

    updates = {}

    # 1. Marital status
    key = (age_group, gender)
    if key in MARITAL_CPT:
        new_marital = sample_from_cpt(MARITAL_CPT[key], rng)
        if new_marital != agent["marital_status"]:
            updates["marital_status"] = new_marital

    # 2. Housing type
    if income_band in HOUSING_CPT:
        new_housing = sample_from_cpt(HOUSING_CPT[income_band], rng)
        if new_housing != agent["housing_type"]:
            updates["housing_type"] = new_housing

    # 3. Education level (merge Uni+PG → University in DB)
    if age_group in EDUCATION_CPT:
        new_edu = sample_from_cpt(EDUCATION_CPT[age_group], rng)
        if new_edu == "Postgraduate":
            new_edu = "University"
        if new_edu != agent["education_level"]:
            updates["education_level"] = new_edu

    return updates


def fetch_all_agents(supabase):
    """Fetch all agents with pagination, selecting only needed columns."""
    columns = "agent_id,age_group,gender,income_band,marital_status,housing_type,education_level"
    agents = []
    offset = 0
    limit = 1000
    while True:
        r = supabase.table("agents").select(columns).range(offset, offset + limit - 1).execute()
        if not r.data:
            break
        agents.extend(r.data)
        if len(r.data) < limit:
            break
        offset += limit
        if offset % 10000 == 0:
            logger.info(f"  Fetched {offset:,} agents...")
    return agents


def batch_update_grouped(supabase, table, updates_list, batch_size=500, sleep_sec=0.3):
    """
    Group updates by field+value, then batch update via .in_().
    E.g., all agents getting marital_status='Divorced' → one DB call.
    Sleep between batches to limit CPU usage.
    """
    # Group: (field, value) → [agent_id, ...]
    groups = defaultdict(list)
    for agent_id, updates in updates_list:
        for field, value in updates.items():
            groups[(field, value)].append(agent_id)

    logger.info(f"  {len(groups)} unique (field, value) groups to update")

    success = 0
    errors = 0
    group_count = 0

    for (field, value), agent_ids in groups.items():
        for chunk_start in range(0, len(agent_ids), batch_size):
            chunk = agent_ids[chunk_start:chunk_start + batch_size]
            for attempt in range(3):
                try:
                    supabase.table(table).update({field: value}).in_("agent_id", chunk).execute()
                    success += len(chunk)
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    errors += len(chunk)
                    if errors <= 10:
                        logger.error(f"  Batch failed ({field}={value}): {e}")
            # Sleep to avoid CPU spike
            time.sleep(sleep_sec)

        group_count += 1
        if group_count % 50 == 0:
            logger.info(f"  Groups: {group_count}/{len(groups)}, updated: {success:,}")

    return success, errors


def main():
    parser = argparse.ArgumentParser(description="Recalibrate CPT fields for 172K agents")
    parser.add_argument("--dry-run", action="store_true", help="Preview without updating DB")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--sleep", type=float, default=0.3, help="Sleep seconds between batches")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    logger.info("=" * 60)
    logger.info("SCRIPT 33: CPT RECALIBRATION")
    logger.info("=" * 60)

    # Connect
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Fetch all agents
    logger.info("Fetching agents from Supabase...")
    agents = fetch_all_agents(supabase)
    logger.info(f"Fetched {len(agents):,} agents")

    # Resample
    logger.info("Resampling with corrected CPTs...")
    updates_list = []  # [(agent_id, {field: new_value}), ...]
    change_counts = Counter()

    for agent in agents:
        updates = resample_agent(agent, rng)
        if updates:
            updates_list.append((agent["agent_id"], updates))
            for field in updates:
                change_counts[field] += 1

    logger.info(f"\nChanges needed:")
    logger.info(f"  Agents changed:   {len(updates_list):,} / {len(agents):,} ({len(updates_list)/len(agents)*100:.1f}%)")
    for field, cnt in sorted(change_counts.items()):
        logger.info(f"  {field}: {cnt:,} changes")

    # Verify new distributions
    logger.info("\nVerifying new distributions...")
    new_marital = Counter()
    new_housing = Counter()
    new_education = Counter()
    for agent in agents:
        aid = agent["agent_id"]
        # Find if this agent has updates
        agent_updates = {}
        for a_id, u in updates_list:
            if a_id == aid:
                agent_updates = u
                break
        new_marital[agent_updates.get("marital_status", agent["marital_status"])] += 1
        new_housing[agent_updates.get("housing_type", agent["housing_type"])] += 1
        new_education[agent_updates.get("education_level", agent["education_level"])] += 1

    n = len(agents)
    logger.info(f"  Marital: {dict(sorted({k: round(v/n, 3) for k, v in new_marital.items()}.items()))}")
    logger.info(f"  Housing: {dict(sorted({k: round(v/n, 3) for k, v in new_housing.items()}.items()))}")
    logger.info(f"  Education: {dict(sorted({k: round(v/n, 3) for k, v in new_education.items()}.items()))}")

    if args.dry_run:
        logger.info("\nDRY RUN — no DB changes made")
        return

    # Upload
    logger.info(f"\nUploading {len(updates_list):,} agent updates (sleep={args.sleep}s between batches)...")
    s, e = batch_update_grouped(supabase, "agents", updates_list,
                                 batch_size=500, sleep_sec=args.sleep)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"RECALIBRATION COMPLETE")
    logger.info(f"{'=' * 60}")
    logger.info(f"Updated: {s:,} field-updates")
    logger.info(f"Errors:  {e:,}")
    logger.info(f"Fields recalibrated: marital_status, housing_type, education_level")


if __name__ == "__main__":
    main()
