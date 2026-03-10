"""
Script 21: Update occupation field for all employed agents in Supabase.

Fetches agent_id + education_level + age from Supabase,
resamples occupation via CPT, then updates only the occupation column.
This avoids the timeout issues from full-record upserts.
"""

import os
import sys
import time
import math
import logging
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import dotenv
dotenv.load_dotenv(str(Path(__file__).parent.parent / "web" / ".env.local"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Occupation CPT (same as in 20_seed_148k_v3.py) ──

OCC_LABELS = [
    "Manager", "Professional", "Associate Professional",
    "Clerical", "Service and Sales",
    "Production", "Plant and Machine Operator",
    "Cleaner and Labourer", "Agriculture",
]

OCC_TO_DB = {
    "Manager": "Senior Official or Manager",
    "Professional": "Professional",
    "Associate Professional": "Associate Professional or Technician",
    "Clerical": "Clerical Worker",
    "Service and Sales": "Service or Sales Worker",
    "Production": "Production Craftsman or Related Worker",
    "Plant and Machine Operator": "Plant or Machine Operator or Assembler",
    "Cleaner and Labourer": "Cleaner, Labourer or Related Worker",
    "Agriculture": "Agricultural or Fishery Worker",
}

EDU_OCC = {
    ("University",   "young"):  [0.10, 0.50, 0.32, 0.04, 0.02, 0.005, 0.003, 0.001, 0.001],
    ("University",   "mid"):    [0.25, 0.40, 0.27, 0.04, 0.02, 0.008, 0.005, 0.004, 0.003],
    ("University",   "senior"): [0.30, 0.35, 0.26, 0.04, 0.03, 0.008, 0.005, 0.004, 0.003],
    ("Postgraduate", "young"):  [0.12, 0.52, 0.30, 0.03, 0.02, 0.003, 0.003, 0.001, 0.003],
    ("Postgraduate", "mid"):    [0.26, 0.42, 0.26, 0.03, 0.02, 0.005, 0.003, 0.003, 0.002],
    ("Postgraduate", "senior"): [0.32, 0.36, 0.25, 0.03, 0.02, 0.007, 0.005, 0.005, 0.003],
    ("Polytechnic",  "young"):  [0.07, 0.20, 0.38, 0.12, 0.12, 0.04, 0.03,  0.015, 0.005],
    ("Polytechnic",  "mid"):    [0.15, 0.17, 0.33, 0.12, 0.11, 0.04, 0.03,  0.015, 0.005],
    ("Polytechnic",  "senior"): [0.18, 0.15, 0.30, 0.12, 0.12, 0.05, 0.04,  0.02,  0.005],
    ("Post_Secondary","young"): [0.05, 0.10, 0.26, 0.15, 0.20, 0.08, 0.08,  0.04,  0.005],
    ("Post_Secondary","mid"):   [0.10, 0.08, 0.23, 0.15, 0.19, 0.09, 0.08,  0.05,  0.005],
    ("Post_Secondary","senior"):[0.12, 0.07, 0.20, 0.14, 0.18, 0.10, 0.09,  0.06,  0.005],
    ("Secondary",    "young"):  [0.04, 0.06, 0.21, 0.14, 0.24, 0.11, 0.11,  0.06,  0.005],
    ("Secondary",    "mid"):    [0.08, 0.05, 0.18, 0.13, 0.23, 0.11, 0.11,  0.08,  0.005],
    ("Secondary",    "senior"): [0.09, 0.04, 0.15, 0.12, 0.22, 0.12, 0.12,  0.11,  0.005],
    ("Primary",      "young"):  [0.03, 0.03, 0.12, 0.09, 0.25, 0.12, 0.15,  0.15,  0.005],
    ("Primary",      "mid"):    [0.04, 0.03, 0.12, 0.09, 0.25, 0.12, 0.15,  0.15,  0.005],
    ("Primary",      "senior"): [0.05, 0.02, 0.08, 0.07, 0.21, 0.12, 0.15,  0.24,  0.005],
    ("No_Formal",    "young"):  [0.03, 0.02, 0.10, 0.08, 0.25, 0.12, 0.16,  0.18,  0.005],
    ("No_Formal",    "mid"):    [0.03, 0.02, 0.10, 0.08, 0.25, 0.12, 0.16,  0.18,  0.005],
    ("No_Formal",    "senior"): [0.04, 0.02, 0.07, 0.06, 0.21, 0.12, 0.16,  0.26,  0.005],
}

SKIP_OCCUPATIONS = {
    "Retired", "Homemaker",
    "Infant/Toddler", "Pre-school Student",
    "Primary School Student", "Secondary School Student",
    "Post-Secondary Student", "Student",
    "University Student", "Polytechnic Student",
    "Unemployed", "National Service",
    "Full-time National Serviceman",
}


def age_bucket(age: int) -> str:
    if age < 35:
        return "young"
    elif age < 50:
        return "mid"
    else:
        return "senior"


def should_skip(occ: str) -> bool:
    if not occ:
        return True
    if occ in SKIP_OCCUPATIONS:
        return True
    if "Student" in occ or "student" in occ:
        return True
    if "Retired" in occ or "Homemaker" in occ:
        return True
    if "National Service" in occ:
        return True
    return False


def main():
    from supabase import create_client

    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "https://rndfpyuuredtqncegygi.supabase.co")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not key:
        key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    if not key:
        logger.error("No Supabase key found")
        return

    sb = create_client(url, key)
    rng = np.random.default_rng(42)

    # Step 1: Fetch agent_id, occupation, education_level, age
    # Use cursor-based pagination (gt agent_id) to avoid offset timeout
    logger.info("Fetching agents from Supabase (cursor-based)...")
    all_agents = []
    last_id = ""
    page_size = 200
    while True:
        for attempt in range(5):
            try:
                q = sb.table("agents").select(
                    "agent_id,occupation,education_level,age"
                ).order("agent_id").limit(page_size)
                if last_id:
                    q = q.gt("agent_id", last_id)
                res = q.execute()
                break
            except Exception as e:
                if attempt < 4:
                    wait = 2 ** attempt
                    logger.warning(f"  Fetch after {last_id[:8]}... failed, retry in {wait}s")
                    time.sleep(wait)
                else:
                    logger.error(f"  Fetch failed after 5 attempts, stopping fetch")
                    res = type('R', (), {'data': []})()
        if not res.data:
            break
        all_agents.extend(res.data)
        last_id = res.data[-1]["agent_id"]
        if len(res.data) < page_size:
            break
        if len(all_agents) % 10000 == 0:
            logger.info(f"  Fetched {len(all_agents):,} agents...")

    logger.info(f"Fetched {len(all_agents):,} agents total")

    # Step 2: Resample occupation for employed adults
    updates = []
    skipped = 0
    for agent in all_agents:
        occ = agent.get("occupation", "")
        if should_skip(occ):
            skipped += 1
            continue

        edu = agent.get("education_level", "Secondary")
        age = agent.get("age", 30)
        bucket = age_bucket(age)
        key = (edu, bucket)
        probs = EDU_OCC.get(key, EDU_OCC[("Secondary", "mid")])
        total = sum(probs)
        probs_norm = [p / total for p in probs]

        new_occ = rng.choice(OCC_LABELS, p=probs_norm)
        new_occ_db = OCC_TO_DB[new_occ]

        if new_occ_db != occ:
            updates.append({
                "agent_id": agent["agent_id"],
                "occupation": new_occ_db,
            })

    logger.info(f"Need to update {len(updates):,} agents ({skipped:,} skipped non-employed)")

    # Step 3: Batch update using .update().in_() grouped by occupation
    # Group agent_ids by target occupation to minimize API calls
    from collections import defaultdict
    occ_groups = defaultdict(list)
    for u in updates:
        occ_groups[u["occupation"]].append(u["agent_id"])

    logger.info(f"Grouped into {len(occ_groups)} occupation categories")
    for occ, ids in occ_groups.items():
        logger.info(f"  {occ}: {len(ids):,} agents")

    success = 0
    errors = 0
    batch_size = 15  # Very small to stay within 8s statement timeout

    for occ, ids in occ_groups.items():
        sub_batches = math.ceil(len(ids) / batch_size)
        for j in range(sub_batches):
            chunk = ids[j * batch_size : (j + 1) * batch_size]
            for attempt in range(5):
                try:
                    sb.table("agents").update(
                        {"occupation": occ}
                    ).in_("agent_id", chunk).execute()
                    success += len(chunk)
                    break
                except Exception as e:
                    if attempt < 4:
                        time.sleep(2 ** attempt)
                        continue
                    logger.error(f"  Update {occ} sub-batch {j+1} failed: {e}")
                    errors += len(chunk)
            if success % 500 == 0 and success > 0:
                logger.info(f"  Progress: {success:,}/{len(updates):,} updated")
        logger.info(f"  {occ} done: {success:,} total updated so far")

    logger.info(f"Update complete: {success:,} success, {errors:,} errors")

    # Step 4: Verify
    logger.info("Verifying...")
    sample = sb.table("agents").select("occupation").range(0, 4999).execute()
    df = pd.DataFrame(sample.data)
    non_emp = list(SKIP_OCCUPATIONS)
    employed = df[~df["occupation"].isin(non_emp)]
    pmet_cats = ["Senior Official or Manager", "Professional", "Associate Professional or Technician"]
    pmet = employed["occupation"].isin(pmet_cats).sum()
    logger.info(f"PMET share (sample 5K): {pmet/len(employed):.1%} (target: 63.7%)")
    logger.info(f"Occupation distribution:\n{employed['occupation'].value_counts(normalize=True)}")


if __name__ == "__main__":
    main()
