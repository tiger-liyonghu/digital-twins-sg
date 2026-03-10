"""
Script 32: Fill media_diet, social_media_usage, household_id, num_children.

Mathematical foundations:
  1. media_diet — Multinomial draw from P(channel | age, ethnicity, education)
     Anchored to IMDA 2024 + Reuters Digital News Report Singapore
  2. social_media_usage — Ordinal from P(intensity | age, education)
     Anchored to DataReportal 2024 Singapore
  3. household_id — Combinatorial household formation:
     - Assortative mating: pair married M+F by age proximity
     - Census 2020 household size distribution
     - Children assigned to married households by mother's planning_area
  4. num_children — Derived from household assignment + Census TFR

Usage:
    python3 -u scripts/32_fill_media_household.py [--dry-run]
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import time
import math
import hashlib
import numpy as np
import pandas as pd
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = "https://rndfpyuuredtqncegygi.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzA4Nzk0NiwiZXhwIjoyMDg4NjYzOTQ2fQ.EMjLfr3N8RDpBPkVftYKCg1Pf6h4rOj8xfCXSuJIxQI"


# ============================================================
# 1. MEDIA DIET — P(channels | age, ethnicity, education)
# ============================================================
# Each agent draws 1-3 media channels. Probabilities from IMDA 2024
# + Reuters Digital News Report Singapore 2024.
#
# Channels: straits_times, social_media, whatsapp, tv, chinese_media,
#           cna, reddit, tiktok, radio, print_newspaper
#
# Model: For each channel, P(consume | age_bucket, ethnicity, education)
# Agent draws Bernoulli for each channel independently, then we keep
# channels where draw=1. Minimum 1 channel guaranteed.

MEDIA_CHANNELS = [
    'straits_times', 'social_media', 'whatsapp', 'tv',
    'chinese_media', 'cna', 'reddit', 'tiktok', 'radio',
]

# P(channel | age_bucket) — base rates from IMDA/Reuters
# Rows: [18-29, 30-44, 45-59, 60+, 0-17]
# Each row sums > 1 because agents consume multiple channels
MEDIA_BASE = {
    #                     ST    social  WA    TV    zh_media CNA   reddit tiktok radio
    'young':   np.array([0.25, 0.85,  0.60, 0.15, 0.05,   0.20, 0.30, 0.55, 0.05]),  # 18-29
    'mid':     np.array([0.45, 0.70,  0.75, 0.35, 0.10,   0.35, 0.15, 0.25, 0.15]),  # 30-44
    'mature':  np.array([0.55, 0.45,  0.80, 0.60, 0.20,   0.40, 0.05, 0.10, 0.25]),  # 45-59
    'senior':  np.array([0.40, 0.20,  0.65, 0.80, 0.35,   0.30, 0.02, 0.03, 0.35]),  # 60+
    'child':   np.array([0.02, 0.40,  0.10, 0.30, 0.02,   0.05, 0.05, 0.35, 0.02]),  # 0-17
}

def get_age_bucket(age):
    if age < 18: return 'child'
    if age < 30: return 'young'
    if age < 45: return 'mid'
    if age < 60: return 'mature'
    return 'senior'

# Ethnicity modifiers (multiplicative)
# Chinese speakers consume more chinese_media
# Malay/Indian less likely to read ST (English-centric), more TV
ETH_MOD = {
    'Chinese': np.array([1.0, 1.0, 1.0, 1.0, 3.5, 1.0, 1.0, 1.0, 1.0]),
    'Malay':   np.array([0.7, 1.1, 1.2, 1.3, 0.1, 0.8, 0.8, 1.2, 1.2]),
    'Indian':  np.array([0.9, 1.1, 1.1, 1.1, 0.05,1.0, 1.0, 1.0, 1.1]),
    'Others':  np.array([1.0, 1.0, 1.0, 0.8, 0.1, 1.0, 1.2, 1.0, 0.8]),
}

# Education modifiers: higher edu → more ST/reddit, less TV
EDU_MOD = {
    'University':     np.array([1.3, 1.0, 1.0, 0.8, 0.8, 1.2, 1.5, 0.8, 0.9]),
    'Postgraduate':   np.array([1.4, 0.9, 1.0, 0.7, 0.7, 1.3, 1.6, 0.6, 0.8]),
    'Polytechnic':    np.array([1.1, 1.1, 1.0, 0.9, 0.9, 1.1, 1.2, 1.1, 1.0]),
    'Post_Secondary': np.array([1.0, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.0]),
    'Secondary':      np.array([0.8, 1.0, 1.0, 1.2, 1.2, 0.9, 0.7, 1.1, 1.1]),
    'Primary':        np.array([0.5, 0.7, 1.0, 1.4, 1.5, 0.7, 0.3, 0.8, 1.2]),
    'No_Formal':      np.array([0.3, 0.5, 0.8, 1.5, 1.8, 0.5, 0.1, 0.5, 1.3]),
}


def sample_media_diet(age, ethnicity, education, rng):
    """Sample media channels via independent Bernoulli draws."""
    bucket = get_age_bucket(age)
    base = MEDIA_BASE[bucket].copy()

    # Apply modifiers
    eth_mod = ETH_MOD.get(ethnicity, ETH_MOD['Others'])
    edu_mod = EDU_MOD.get(education, EDU_MOD['Secondary'])
    probs = np.clip(base * eth_mod * edu_mod, 0.01, 0.95)

    # Bernoulli draw for each channel
    draws = rng.random(len(MEDIA_CHANNELS)) < probs
    selected = [ch for ch, d in zip(MEDIA_CHANNELS, draws) if d]

    # Guarantee at least 1 channel
    if not selected:
        # Pick the highest-probability channel
        selected = [MEDIA_CHANNELS[np.argmax(probs)]]

    return ','.join(selected)


# ============================================================
# 2. SOCIAL MEDIA USAGE — P(intensity | age, education)
# ============================================================
# Ordinal: heavy / moderate / light / none
# Anchored to DataReportal 2024:
#   SG daily social media time: 2h 14m average
#   18-24: ~3h (heavy), 25-34: ~2.5h, 35-49: ~2h,
#   50-64: ~1.5h, 65+: ~0.5h
#
# Model: Categorical draw from P(intensity | age_bucket)

SOCIAL_MEDIA_CPT = {
    #              heavy  moderate  light   none
    'child':     [0.15,  0.30,    0.35,   0.20],
    'young':     [0.45,  0.35,    0.15,   0.05],
    'mid':       [0.20,  0.45,    0.25,   0.10],
    'mature':    [0.08,  0.30,    0.40,   0.22],
    'senior':    [0.03,  0.12,    0.35,   0.50],
}

SM_LABELS = ['heavy', 'moderate', 'light', 'none']

# Education modifier: higher edu → slightly more usage (work-related social)
SM_EDU_SHIFT = {
    'University': np.array([0.05, 0.03, -0.05, -0.03]),
    'Postgraduate': np.array([0.03, 0.05, -0.05, -0.03]),
    'Polytechnic': np.array([0.03, 0.02, -0.03, -0.02]),
    'Post_Secondary': np.array([0.0, 0.0, 0.0, 0.0]),
    'Secondary': np.array([-0.02, 0.0, 0.02, 0.0]),
    'Primary': np.array([-0.05, -0.03, 0.03, 0.05]),
    'No_Formal': np.array([-0.08, -0.05, 0.05, 0.08]),
}


def sample_social_media_usage(age, education, rng):
    """Sample social media usage intensity."""
    bucket = get_age_bucket(age)
    probs = np.array(SOCIAL_MEDIA_CPT[bucket], dtype=float)

    # Apply education shift
    shift = SM_EDU_SHIFT.get(education, np.zeros(4))
    probs = np.clip(probs + shift, 0.01, 0.99)
    probs /= probs.sum()  # re-normalize

    return rng.choice(SM_LABELS, p=probs)


# ============================================================
# 3 & 4. HOUSEHOLD FORMATION + NUM_CHILDREN
# ============================================================
# Mathematical model:
#
# Step 1: Assortative mating
#   - Take all married adults, separate by gender
#   - Sort by (planning_area, age)
#   - Greedy match: within same planning_area, pair M+F with
#     smallest |age_M - age_F| (empirical SG mean gap: M 2-3 yrs older)
#   - Unmatched married → single-person household
#
# Step 2: Assign children to households
#   - Children (0-17) assigned to married couples in same planning_area
#   - Priority: youngest mothers (25-45) get children first
#   - Max children per household: Poisson(λ) where λ from Census TFR
#
# Step 3: Remaining adults
#   - Single/Divorced/Widowed adults → own household
#   - Young singles (18-30) → 20% chance of shared household (flatmates)
#
# Step 4: num_children
#   - Derived from household assignment: count children per household
#   - Written to both parents
#
# Census 2020 anchoring:
#   - Average household size: 3.22
#   - 1-person: 15.3%, 2-person: 18.7%, 3-person: 17.5%,
#     4-person: 21.9%, 5+: 26.6%
#   - TFR 2024: 0.97 (one of world's lowest)
#   - Mean children per married couple: ~1.5 (includes childless)

SG_TFR = 0.97  # 2024
# Poisson lambda for children per married couple
# Mean children among couples WITH children ≈ 1.8
# But ~35% couples are childless → effective λ ≈ 1.5
CHILDREN_LAMBDA = 1.5


def form_households(agents_df, rng):
    """
    Form households using assortative mating + child assignment.

    Returns dict: agent_id -> (household_id, num_children)
    """
    logger.info("Forming households...")
    n = len(agents_df)

    # Separate by marital status
    married_m = agents_df[(agents_df.marital_status == 'Married') & (agents_df.gender == 'M')].copy()
    married_f = agents_df[(agents_df.marital_status == 'Married') & (agents_df.gender == 'F')].copy()
    children = agents_df[agents_df.data_source == 'synthetic'].copy()
    others = agents_df[
        ~agents_df.agent_id.isin(married_m.agent_id) &
        ~agents_df.agent_id.isin(married_f.agent_id) &
        ~agents_df.agent_id.isin(children.agent_id)
    ].copy()

    logger.info(f"  Married M: {len(married_m):,}, F: {len(married_f):,}")
    logger.info(f"  Children: {len(children):,}")
    logger.info(f"  Others (single/divorced/widowed): {len(others):,}")

    # Result mapping
    hh_map = {}  # agent_id -> household_id
    hh_children_count = defaultdict(int)  # household_id -> num_children
    hh_seq = 0

    # === STEP 1: Assortative mating ===
    # Sort married by planning_area, then age
    married_m = married_m.sort_values(['planning_area', 'age']).reset_index(drop=True)
    married_f = married_f.sort_values(['planning_area', 'age']).reset_index(drop=True)

    # Group by planning_area for within-area matching
    m_by_area = defaultdict(list)
    f_by_area = defaultdict(list)
    for _, row in married_m.iterrows():
        m_by_area[row.planning_area].append((row.agent_id, row.age))
    for _, row in married_f.iterrows():
        f_by_area[row.planning_area].append((row.agent_id, row.age))

    couples = []  # (m_id, f_id, area, avg_age)
    unmatched_ids = []

    for area in set(list(m_by_area.keys()) + list(f_by_area.keys())):
        males = sorted(m_by_area.get(area, []), key=lambda x: x[1])
        females = sorted(f_by_area.get(area, []), key=lambda x: x[1])

        # Greedy matching by age proximity
        used_f = set()
        for m_id, m_age in males:
            best_f = None
            best_diff = 999
            for j, (f_id, f_age) in enumerate(females):
                if j in used_f:
                    continue
                # SG empirical: husband typically 2-3 years older
                # Prefer |m_age - f_age - 2.5| minimized
                diff = abs((m_age - f_age) - 2.5)
                if diff < best_diff:
                    best_diff = diff
                    best_f = (j, f_id, f_age)
            if best_f and best_diff < 15:  # max 15 year gap
                j, f_id, f_age = best_f
                used_f.add(j)
                hh_id = f"HH-{hh_seq:06d}"
                hh_seq += 1
                hh_map[m_id] = hh_id
                hh_map[f_id] = hh_id
                couples.append((m_id, f_id, area, (m_age + f_age) / 2))
            else:
                hh_id = f"HH-{hh_seq:06d}"
                hh_seq += 1
                hh_map[m_id] = hh_id
                unmatched_ids.append(m_id)

        # Unmatched females
        for j, (f_id, f_age) in enumerate(females):
            if j not in used_f:
                hh_id = f"HH-{hh_seq:06d}"
                hh_seq += 1
                hh_map[f_id] = hh_id
                unmatched_ids.append(f_id)

    logger.info(f"  Couples formed: {len(couples):,}")
    logger.info(f"  Unmatched married: {len(unmatched_ids):,}")

    # === STEP 2: Assign children to couples ===
    # Group couples by planning_area
    couples_by_area = defaultdict(list)
    for m_id, f_id, area, avg_age in couples:
        couples_by_area[area].append((m_id, f_id, avg_age))

    # Sort children by planning_area
    children_by_area = defaultdict(list)
    for _, row in children.iterrows():
        children_by_area[row.planning_area].append(row.agent_id)

    # For each area, assign children to couples
    # Younger couples (25-45) more likely to have young children
    # Use Poisson(λ=1.5) truncated at 4 for max children per couple
    children_assigned = 0
    for area in children_by_area:
        area_children = children_by_area[area].copy()
        rng.shuffle(area_children)

        area_couples = couples_by_area.get(area, [])
        if not area_couples:
            # No couples in this area — assign children to single-parent households
            for c_id in area_children:
                hh_id = f"HH-{hh_seq:06d}"
                hh_seq += 1
                hh_map[c_id] = hh_id
            continue

        # Sort couples: prioritize age 28-42 (peak child-rearing)
        # Weight: higher for couples aged 28-42
        couple_weights = []
        for m_id, f_id, avg_age in area_couples:
            if 28 <= avg_age <= 42:
                w = 3.0
            elif 25 <= avg_age <= 50:
                w = 1.5
            else:
                w = 0.3
            couple_weights.append(w)
        couple_weights = np.array(couple_weights)
        couple_weights /= couple_weights.sum()

        # Assign children: draw couple index, assign to that household
        # Cap at 4 children per couple
        couple_child_count = defaultdict(int)
        for c_id in area_children:
            # Draw a couple (weighted by child-rearing age)
            attempts = 0
            while attempts < 20:
                idx = rng.choice(len(area_couples), p=couple_weights)
                m_id, f_id, avg_age = area_couples[idx]
                couple_hh = hh_map[m_id]
                if couple_child_count[couple_hh] < 4:
                    hh_map[c_id] = couple_hh
                    couple_child_count[couple_hh] += 1
                    hh_children_count[couple_hh] += 1
                    children_assigned += 1
                    break
                attempts += 1
            else:
                # All couples full — new household
                hh_id = f"HH-{hh_seq:06d}"
                hh_seq += 1
                hh_map[c_id] = hh_id

    logger.info(f"  Children assigned to couples: {children_assigned:,}")

    # === STEP 3: Remaining adults (single/divorced/widowed) ===
    # In Singapore, many single adults live with parents.
    # Census 2020: only 15.3% of households are 1-person.
    # Model:
    #   - Single adults 18-34: 75% live with a couple (parents)
    #   - Single adults 35-49: 40% live with a couple
    #   - Single adults 50+: 20% live with a couple (elderly parents passed)
    #   - Divorced/Widowed: 30% live with a couple (return to parents)
    #   - Rest: own household

    # Build pool of couple households by area for co-residence
    couple_hh_by_area = defaultdict(list)
    for m_id, f_id, area, avg_age in couples:
        couple_hh_by_area[area].append(hh_map[m_id])

    for _, row in others.iterrows():
        age = row['age']
        ms = row['marital_status']
        area = row['planning_area']

        # Determine probability of co-residence with a couple household
        # Census 2020: 84.7% of Singaporeans live in multi-person households
        # HDB rules: single citizens can only buy BTO at 35+
        # Cultural norm: children stay with parents until marriage
        if ms == 'Single':
            if age < 18:
                p_coresidence = 0.0  # children handled in step 2
            elif age < 28:
                p_coresidence = 0.92  # almost all live with parents
            elif age < 35:
                p_coresidence = 0.80  # HDB BTO only at 35 for singles
            elif age < 50:
                p_coresidence = 0.55  # some bought own flat
            else:
                p_coresidence = 0.35  # older singles, many own flat
        elif ms == 'Widowed':
            if age >= 65:
                p_coresidence = 0.65  # elderly widowed often live with adult children
            else:
                p_coresidence = 0.40
        else:  # Divorced
            p_coresidence = 0.45

        area_hhs = couple_hh_by_area.get(area, [])
        if area_hhs and rng.random() < p_coresidence:
            # Join a random couple household in same area
            chosen_hh = rng.choice(area_hhs)
            hh_map[row.agent_id] = chosen_hh
        else:
            hh_id = f"HH-{hh_seq:06d}"
            hh_seq += 1
            hh_map[row.agent_id] = hh_id

    # === STEP 3b: Redistribute 1-person HHs to match Census distribution ===
    # Census 2020 target (% of households):
    #   1-person: 15.3%, 2-person: 18.7%, 3-person: 17.5%, 4-person: 21.9%, 5+: 26.6%
    #
    # Strategy: merge 1-person HHs into existing 2-3 person households
    # (to build up 3/4/5+ person households) rather than just pairing into 2s.

    hh_members = defaultdict(list)
    for aid, hid in hh_map.items():
        hh_members[hid].append(aid)

    # Get current distribution
    hh_size_map = {hid: len(members) for hid, members in hh_members.items()}
    total_hh_pre = len(hh_size_map)

    one_person_hhs = [hid for hid, s in hh_size_map.items() if s == 1]
    logger.info(f"  1-person HHs before merge: {len(one_person_hhs):,} / {total_hh_pre:,} total")

    # Target: keep ~15% as 1-person → keep this many
    target_1p_count = int(total_hh_pre * 0.153)
    to_relocate = len(one_person_hhs) - target_1p_count
    if to_relocate < 0:
        to_relocate = 0
    logger.info(f"  Target 1-person: {target_1p_count:,}, need to relocate: {to_relocate:,}")

    # Get agent info for 1-person HH members
    # Drop duplicates to ensure unique index (prevents Series/DataFrame confusion)
    agent_lookup = agents_df.drop_duplicates(subset='agent_id').set_index('agent_id')
    one_p_agents = []
    for hid in one_person_hhs:
        aid = hh_members[hid][0]
        if aid in agent_lookup.index:
            row = agent_lookup.loc[aid]
            one_p_agents.append((aid, hid, row['planning_area'], row['age']))

    rng.shuffle(one_p_agents)
    # Only relocate the amount needed
    agents_to_move = one_p_agents[:to_relocate]

    # Build pool of target households (size 2-4) by area — adding to these builds 3/4/5+
    target_hhs_by_area = defaultdict(list)
    for hid, size in hh_size_map.items():
        if 2 <= size <= 4:
            # Find area of first member
            first_member = hh_members[hid][0]
            if first_member in agent_lookup.index:
                area = agent_lookup.loc[first_member, 'planning_area']
                target_hhs_by_area[area].append((hid, size))

    merged_to_existing = 0
    merged_to_pairs = 0
    remaining_to_move = []

    for aid, old_hid, area, age in agents_to_move:
        targets = target_hhs_by_area.get(area, [])
        if targets:
            # Pick a random target household (prefer smaller ones → grow them)
            idx = rng.integers(0, len(targets))
            target_hid, target_size = targets[idx]
            hh_map[aid] = target_hid
            # Update size tracking
            new_size = target_size + 1
            targets[idx] = (target_hid, new_size)
            # Remove from pool if now too large (5+)
            if new_size >= 5:
                targets.pop(idx)
            merged_to_existing += 1
        else:
            remaining_to_move.append((aid, old_hid, area, age))

    # For remaining (no target HH in area), pair them with each other
    remaining_by_area = defaultdict(list)
    for aid, old_hid, area, age in remaining_to_move:
        remaining_by_area[area].append((aid, old_hid))
    for area, agents_list in remaining_by_area.items():
        i = 0
        while i + 1 < len(agents_list):
            aid1, hid1 = agents_list[i]
            aid2, hid2 = agents_list[i + 1]
            hh_map[aid2] = hid1
            merged_to_pairs += 1
            i += 2

    logger.info(f"  Merged into existing HHs: {merged_to_existing:,}")
    logger.info(f"  Paired remaining: {merged_to_pairs:,}")

    # === STEP 4: Compute num_children per parent ===
    # For each household with children, write num_children to parents
    num_children_map = {}
    for agent_id, hh_id in hh_map.items():
        nc = hh_children_count.get(hh_id, 0)
        num_children_map[agent_id] = nc

    # Validation
    total_hh = len(set(hh_map.values()))
    avg_size = len(hh_map) / total_hh if total_hh > 0 else 0
    hh_sizes = defaultdict(int)
    for hh_id in hh_map.values():
        hh_sizes[hh_id] += 1
    size_dist = defaultdict(int)
    for s in hh_sizes.values():
        size_dist[min(s, 5)] += 1

    logger.info(f"\n  === HOUSEHOLD VALIDATION ===")
    logger.info(f"  Total households: {total_hh:,}")
    logger.info(f"  Average size: {avg_size:.2f} (Census target: 3.22)")
    logger.info(f"  Size distribution:")
    for s in sorted(size_dist.keys()):
        label = f"{s}+" if s == 5 else str(s)
        pct = size_dist[s] / total_hh * 100
        logger.info(f"    {label}-person: {size_dist[s]:,} ({pct:.1f}%)")
    logger.info(f"  Households with children: {len(hh_children_count):,}")

    return hh_map, num_children_map


# ============================================================
# BATCH UPDATE (grouped)
# ============================================================

def batch_update_grouped(supabase, table, records, fields, batch_size=500):
    """Group by update values, batch update by agent_id IN (...)."""
    groups = defaultdict(list)
    for rec in records:
        key = tuple(rec[f] for f in fields)
        groups[key].append(rec['agent_id'])

    logger.info(f"Grouped into {len(groups)} unique combinations for {len(records):,} agents")

    success = 0
    errors = 0
    g_count = 0

    for key, agent_ids in groups.items():
        update_data = {f: v for f, v in zip(fields, key)}
        for chunk_start in range(0, len(agent_ids), batch_size):
            chunk = agent_ids[chunk_start:chunk_start + batch_size]
            for attempt in range(3):
                try:
                    supabase.table(table).update(update_data).in_('agent_id', chunk).execute()
                    success += len(chunk)
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    errors += len(chunk)
                    if errors <= 10:
                        logger.error(f"  Failed: {e}")

        g_count += 1
        if g_count % 500 == 0:
            logger.info(f"  Groups: {g_count}/{len(groups)}, updated: {success:,}")

    logger.info(f"  Done: {success:,} success, {errors:,} errors")
    return success, errors


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rng = np.random.default_rng(42)

    # Load all agents from Supabase
    logger.info("Loading all agents from Supabase...")
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    all_agents = []
    offset = 0
    page_size = 1000
    while True:
        resp = supabase.table('agents').select(
            'agent_id,age,gender,ethnicity,education_level,marital_status,'
            'planning_area,data_source,monthly_income'
        ).range(offset, offset + page_size - 1).execute()
        if not resp.data:
            break
        all_agents.extend(resp.data)
        offset += page_size
        if len(resp.data) < page_size:
            break
        if offset % 50000 == 0:
            logger.info(f"  Loaded {offset:,} agents...")

    df = pd.DataFrame(all_agents)
    logger.info(f"Loaded {len(df):,} agents total")

    # === 1. Media diet ===
    logger.info("\n=== MEDIA DIET ===")
    df['media_diet'] = df.apply(
        lambda r: sample_media_diet(r['age'], r['ethnicity'], r['education_level'], rng),
        axis=1
    )
    # Stats
    all_channels = ','.join(df['media_diet']).split(',')
    from collections import Counter
    ch_counts = Counter(all_channels)
    logger.info("Channel penetration:")
    for ch, count in ch_counts.most_common():
        logger.info(f"  {ch}: {count:,} ({count/len(df)*100:.1f}%)")

    # === 2. Social media usage ===
    logger.info("\n=== SOCIAL MEDIA USAGE ===")
    df['social_media_usage'] = df.apply(
        lambda r: sample_social_media_usage(r['age'], r['education_level'], rng),
        axis=1
    )
    sm_dist = df['social_media_usage'].value_counts()
    logger.info(f"Distribution: {dict(sm_dist)}")

    # === 3 & 4. Households ===
    logger.info("\n=== HOUSEHOLDS ===")
    hh_map, nc_map = form_households(df, rng)
    df['household_id'] = df['agent_id'].map(hh_map)
    df['num_children'] = df['agent_id'].map(nc_map)

    if args.dry_run:
        logger.info("\nDRY RUN — sample records:")
        sample = df.sample(10, random_state=42)
        for _, r in sample.iterrows():
            logger.info(f"  {r.agent_id[:8]}... age={r.age} {r.gender} {r.ethnicity} "
                        f"media={r.media_diet} sm={r.social_media_usage} "
                        f"hh={r.household_id} children={r.num_children}")
        return

    # === Upload ===
    # All 4 fields have high cardinality (media_diet ~170K unique, household_id ~53K).
    # Strategy: 20-thread concurrent per-agent update, all 4 fields at once.
    # 20 threads × ~150ms = ~133 req/s → 172K / 133 ≈ 21 minutes.

    logger.info("\n=== UPLOADING (20-thread concurrent) ===")

    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    lock = threading.Lock()
    counters = {'success': 0, 'errors': 0}
    total = len(df)

    # Build update list
    update_items = []
    for _, r in df.iterrows():
        update_items.append({
            'agent_id': r['agent_id'],
            'data': {
                'media_diet': r['media_diet'],
                'social_media_usage': r['social_media_usage'],
                'household_id': r['household_id'],
                'num_children': int(r['num_children']),
            }
        })

    def update_agent(item):
        for attempt in range(3):
            try:
                supabase.table('agents').update(
                    item['data']
                ).eq('agent_id', item['agent_id']).execute()
                with lock:
                    counters['success'] += 1
                    if counters['success'] % 10000 == 0:
                        logger.info(f"  Progress: {counters['success']:,}/{total:,} "
                                    f"({counters['success']/total*100:.1f}%)")
                return
            except Exception as ex:
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                with lock:
                    counters['errors'] += 1
                    if counters['errors'] <= 10:
                        logger.error(f"  Failed {item['agent_id'][:8]}: {ex}")

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(update_agent, item) for item in update_items]
        for f in as_completed(futures):
            pass

    s = counters['success']
    e = counters['errors']
    print(f"\n{'='*60}")
    print(f"FILL COMPLETE")
    print(f"{'='*60}")
    print(f"Updated: {s:,} agents, {e:,} errors")
    print(f"Fields: media_diet, social_media_usage, household_id, num_children")


if __name__ == "__main__":
    main()
