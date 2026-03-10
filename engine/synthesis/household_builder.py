"""
Household Builder V2 — Constraint-driven household formation.

Mathematical approach:
1. Target a GHS 2025 household SIZE distribution as the primary constraint
2. Form households in priority order (most constrained first):
   a. Married couples (the anchor of most households)
   b. Children attached to parents (age compatibility: parent 22-45 years older)
   c. Unmarried adults 18-34 remain with parents (Singapore cultural norm)
   d. Elderly widowed/divorced join adult children's households
   e. FDW join employer households
   f. WP/SP workers form shared accommodation (4-8 per unit)
   g. Remaining: singles 35+ form 1-person households
3. Iteratively adjust to match target size distribution

Singapore household facts (GHS 2025):
- Mean household size: 3.16 persons
- 1-person: 15.3%, 2-person: 18.8%, 3-person: 18.0%
- 4-person: 22.3%, 5-person: 15.5%, 6+: 10.1%
- ~15% of households are multi-generational (3 generations)
- Unmarried children (<35) overwhelmingly live with parents
- HDB singles scheme only allows purchase at 35+
- ~250K FDWs live with employer families
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Set
import logging

logger = logging.getLogger(__name__)

# GHS 2025 household size distribution (target)
TARGET_HH_SIZE_DIST = {
    1: 0.153,
    2: 0.188,
    3: 0.180,
    4: 0.223,
    5: 0.155,
    6: 0.065,
    7: 0.026,
    8: 0.010,
}


class HouseholdBuilder:
    """Constraint-driven household formation matching GHS 2025 distribution."""

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def build(self, agents_df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign household_id and household_role to all agents.

        Strategy:
        Phase 1: Form married-couple nuclei
        Phase 2: Attach biological children (age-compatible)
        Phase 3: Attach unmarried adult children (18-34, cultural norm)
        Phase 4: Attach elderly parents (multi-generational)
        Phase 5: Place FDWs with employer families
        Phase 6: Group WP/SP workers into shared accommodation
        Phase 7: Place remaining elderly with adult children
        Phase 8: Create singles for genuinely alone adults (35+)
        Phase 9: Adjust to match Census size distribution
        """
        n = len(agents_df)
        logger.info(f"Building households for {n} agents")

        agents = agents_df.copy()
        agents["household_id"] = ""
        agents["household_role"] = ""

        # Track assignment status
        assigned: Set[int] = set()
        hh_counter = [0]  # mutable counter

        def new_hh_id():
            hid = f"HH{hh_counter[0]:05d}"
            hh_counter[0] += 1
            return hid

        def assign(idx, hh_id, role):
            agents.at[idx, "household_id"] = hh_id
            agents.at[idx, "household_role"] = role
            assigned.add(idx)

        # Build index structures for efficient lookup
        idx_by = {
            "married_m": agents[(agents["marital_status"] == "Married") &
                                (agents["gender"] == "M")].index.tolist(),
            "married_f": agents[(agents["marital_status"] == "Married") &
                                (agents["gender"] == "F")].index.tolist(),
            "child": agents[agents["age"] <= 17].index.tolist(),
            "young_adult": agents[(agents["age"] >= 18) & (agents["age"] <= 34) &
                                  (agents["marital_status"] == "Single")].index.tolist(),
            "elderly": agents[agents["age"] >= 65].index.tolist(),
            "fdw": agents[agents["residency_status"] == "FDW"].index.tolist(),
            "wp_sp": agents[agents["residency_status"].isin(["WP", "SP"])].index.tolist(),
        }

        self.rng.shuffle(idx_by["married_m"])
        self.rng.shuffle(idx_by["married_f"])
        self.rng.shuffle(idx_by["child"])
        self.rng.shuffle(idx_by["young_adult"])
        self.rng.shuffle(idx_by["elderly"])
        self.rng.shuffle(idx_by["fdw"])
        self.rng.shuffle(idx_by["wp_sp"])

        # ============================================================
        # PHASE 1: Married couples
        # ============================================================
        couples = []  # list of (hh_id, head_idx, spouse_idx)
        pairs = min(len(idx_by["married_m"]), len(idx_by["married_f"]))

        for i in range(pairs):
            hh_id = new_hh_id()
            h_idx = idx_by["married_m"][i]
            s_idx = idx_by["married_f"][i]
            assign(h_idx, hh_id, "head")
            assign(s_idx, hh_id, "spouse")
            couples.append((hh_id, h_idx, s_idx))

        logger.info(f"Phase 1: {len(couples)} married couples")

        # Sort couples by head age (older first — they get children first)
        couples.sort(key=lambda c: agents.loc[c[1], "age"], reverse=True)

        # ============================================================
        # PHASE 2: Attach minor children (0-17) to parent couples
        # ============================================================
        # Child needs parent who is 22-45 years older
        children_placed = 0
        child_pool = [c for c in idx_by["child"] if c not in assigned]

        for hh_id, h_idx, s_idx in couples:
            head_age = agents.loc[h_idx, "age"]
            if head_age < 25:
                continue

            # How many children? Based on SG TFR ≈ 1.1
            # But TFR is per woman over lifetime; at any snapshot, parents have
            # accumulated children. Distribution depends on parent age.
            # TFR-calibrated child distribution
            # Singapore TFR ~1.1 → most couples have 0-1 children at snapshot.
            # To avoid 4-person HH surplus (couple+2kids=4p), we shift weight
            # toward 0-kid and 1-kid families, with some 3-kid for 5p HHs.
            if head_age < 32:
                n_kids = self.rng.choice([0, 1, 2], p=[0.50, 0.38, 0.12])
            elif head_age < 42:
                n_kids = self.rng.choice([0, 1, 2, 3], p=[0.25, 0.38, 0.22, 0.15])
            elif head_age < 55:
                n_kids = self.rng.choice([0, 1, 2, 3], p=[0.30, 0.32, 0.22, 0.16])
            else:
                n_kids = 0  # children already adults

            placed_this_hh = 0
            new_pool = []
            for c_idx in child_pool:
                if c_idx in assigned:
                    continue
                if placed_this_hh >= n_kids:
                    new_pool.append(c_idx)
                    continue

                child_age = agents.loc[c_idx, "age"]
                age_gap = head_age - child_age

                if 22 <= age_gap <= 45:
                    assign(c_idx, hh_id, "child")
                    children_placed += 1
                    placed_this_hh += 1
                else:
                    new_pool.append(c_idx)

            child_pool = new_pool

        logger.info(f"Phase 2: {children_placed} minor children placed")

        # ============================================================
        # PHASE 3: Attach unmarried adults 18-34 to parents' households
        # In Singapore, unmarried adults mostly live with parents.
        # ~85% of single 18-29 live with parents, ~60% of single 30-34.
        # ============================================================
        young_adults_placed = 0
        ya_pool = [ya for ya in idx_by["young_adult"] if ya not in assigned]

        for hh_id, h_idx, s_idx in couples:
            head_age = agents.loc[h_idx, "age"]

            # Parent should be 22-40 years older than adult child
            if head_age < 42:
                continue

            # Check household current size
            hh_members = agents[agents["household_id"] == hh_id]
            current_size = len(hh_members)
            if current_size >= 6:
                continue

            # How many adult children might still live at home?
            max_ya = min(2, 6 - current_size)

            placed_this_hh = 0
            new_pool = []
            for ya_idx in ya_pool:
                if ya_idx in assigned:
                    continue
                if placed_this_hh >= max_ya:
                    new_pool.append(ya_idx)
                    continue

                ya_age = agents.loc[ya_idx, "age"]
                age_gap = head_age - ya_age

                if 22 <= age_gap <= 40:
                    # Probability of living with parents
                    if ya_age <= 25:
                        p_with_parents = 0.85
                    elif ya_age <= 30:
                        p_with_parents = 0.70
                    else:
                        p_with_parents = 0.50

                    if self.rng.random() < p_with_parents:
                        assign(ya_idx, hh_id, "child")
                        young_adults_placed += 1
                        placed_this_hh += 1
                    else:
                        new_pool.append(ya_idx)
                else:
                    new_pool.append(ya_idx)

            ya_pool = new_pool

        logger.info(f"Phase 3: {young_adults_placed} unmarried adults (18-34) placed with parents")

        # ============================================================
        # PHASE 4: Elderly parents into adult children's households
        # ~30% of elderly in SG live with adult children
        # ============================================================
        elderly_placed = 0
        elderly_pool = [e for e in idx_by["elderly"] if e not in assigned]

        # Eligible households: head age 35-60 (their parents would be 60+)
        eligible_hh = [
            (hh_id, h_idx) for hh_id, h_idx, _ in couples
            if 35 <= agents.loc[h_idx, "age"] <= 60
        ]
        self.rng.shuffle(eligible_hh)

        # Place ~40% of unassigned elderly with adult children
        target_elderly = int(len(elderly_pool) * 0.40)

        for hh_id, h_idx in eligible_hh:
            if elderly_placed >= target_elderly or not elderly_pool:
                break

            head_age = agents.loc[h_idx, "age"]
            hh_members = agents[agents["household_id"] == hh_id]
            if len(hh_members) >= 6:
                continue

            e_idx = elderly_pool.pop(0)
            e_age = agents.loc[e_idx, "age"]

            # Check plausibility: parent 20+ years older than child
            if e_age - head_age >= 18:
                assign(e_idx, hh_id, "parent")
                elderly_placed += 1

        logger.info(f"Phase 4: {elderly_placed} elderly parents placed with adult children")

        # ============================================================
        # PHASE 5: FDWs into employer households
        # ============================================================
        fdw_placed = 0
        fdw_pool = [f for f in idx_by["fdw"] if f not in assigned]

        # FDWs typically in upper-income families with children or elderly
        for hh_id, h_idx, _ in couples:
            if not fdw_pool:
                break

            income = agents.loc[h_idx, "monthly_income"]
            head_age = agents.loc[h_idx, "age"]
            hh_members = agents[agents["household_id"] == hh_id]

            # Higher income families more likely to have FDW
            has_children = any(hh_members["household_role"] == "child")
            has_elderly = any(hh_members["household_role"] == "parent")

            if income >= 5000 and (has_children or has_elderly or head_age >= 40):
                if self.rng.random() < 0.25:
                    f_idx = fdw_pool.pop(0)
                    assign(f_idx, hh_id, "helper")
                    fdw_placed += 1

        logger.info(f"Phase 5: {fdw_placed} FDWs placed")

        # ============================================================
        # PHASE 6: WP/SP workers — shared accommodation (4-8 per unit)
        # ============================================================
        wp_pool = [w for w in idx_by["wp_sp"] if w not in assigned]
        wp_hh_count = 0

        while len(wp_pool) >= 2:
            hh_id = new_hh_id()
            group_size = min(
                int(self.rng.choice([2, 3, 4, 5, 6], p=[0.15, 0.20, 0.30, 0.20, 0.15])),
                len(wp_pool)
            )

            for j in range(group_size):
                w_idx = wp_pool.pop(0)
                role = "head" if j == 0 else "housemate"
                assign(w_idx, hh_id, role)

            wp_hh_count += 1

        logger.info(f"Phase 6: {wp_hh_count} worker shared-accommodation units")

        # ============================================================
        # PHASE 7: Remaining unassigned children → nearest couple
        # ============================================================
        orphan_children = [c for c in idx_by["child"] if c not in assigned]
        for c_idx in orphan_children:
            # Find any couple household with room
            for hh_id, h_idx, _ in couples:
                hh_size = (agents["household_id"] == hh_id).sum()
                if hh_size < 5:
                    assign(c_idx, hh_id, "child")
                    break
            else:
                # Last resort: create a guardian household
                hh_id = new_hh_id()
                assign(c_idx, hh_id, "child")

        if orphan_children:
            logger.info(f"Phase 7: {len(orphan_children)} remaining children placed")

        # ============================================================
        # PHASE 8: Remaining elderly → form pairs or join existing
        # ============================================================
        elderly_remaining = [e for e in idx_by["elderly"] if e not in assigned]
        elderly_paired = 0

        # Pair up remaining elderly (elderly couple households)
        while len(elderly_remaining) >= 2:
            if self.rng.random() < 0.4:  # 40% chance to pair
                hh_id = new_hh_id()
                e1 = elderly_remaining.pop(0)
                e2 = elderly_remaining.pop(0)
                assign(e1, hh_id, "head")
                assign(e2, hh_id, "housemate")
                elderly_paired += 1
            else:
                break

        if elderly_paired:
            logger.info(f"Phase 8: {elderly_paired} elderly pairs formed")

        # ============================================================
        # PHASE 9: All remaining unassigned → single-person households
        # ============================================================
        remaining = [i for i in range(n) if i not in assigned]

        # But first: remaining FDWs/WP should go to shared/employer
        for idx in list(remaining):
            res = agents.loc[idx, "residency_status"]
            if res == "FDW":
                # Attach to random couple household
                for hh_id, h_idx, _ in couples:
                    hh_size = (agents["household_id"] == hh_id).sum()
                    if hh_size < 7:
                        assign(idx, hh_id, "helper")
                        remaining.remove(idx)
                        break

        # True singles
        for idx in remaining:
            if idx not in assigned:
                hh_id = new_hh_id()
                assign(idx, hh_id, "head")

        logger.info(f"Phase 9: {len(remaining)} single-person households")

        # ============================================================
        # PHASE 10: Constraint Redistribution
        # Mathematical mechanism to force-match Census size distribution.
        #
        # Algorithm:
        # 1. Compute current size distribution vs Census target
        # 2. Identify surplus sizes (actual > target) and deficit sizes
        # 3. For surplus 1-person HHs: merge pairs/triples into larger HHs
        #    (matching by planning_area for geographic coherence)
        # 4. For surplus large HHs: split off adult members into new HHs
        # 5. Iterate until SRMSE < 0.05 or max 10 rounds
        # ============================================================
        agents = agents.copy()
        MAX_REDISTRIBUTION_ROUNDS = 10

        for rd in range(MAX_REDISTRIBUTION_ROUNDS):
            hh_sizes = agents.groupby("household_id").size()
            total_hh = len(hh_sizes)

            size_counts = {}
            for s in range(1, 9):
                size_counts[s] = int((hh_sizes == s).sum()) if s < 8 else int((hh_sizes >= 8).sum())

            # Compute target counts
            target_counts = {s: int(round(TARGET_HH_SIZE_DIST[s] * total_hh))
                             for s in range(1, 9)}

            # SRMSE check
            mean_target = sum(target_counts.values()) / len(target_counts)
            srmse = np.sqrt(np.mean([
                ((size_counts.get(s, 0) - target_counts.get(s, 0)) ** 2)
                for s in range(1, 9)
            ])) / max(mean_target, 1)

            if srmse < 0.05:
                logger.info(f"Phase 10 round {rd}: SRMSE={srmse:.4f} < 0.05. "
                            f"Census distribution achieved.")
                break

            logger.info(f"Phase 10 round {rd}: SRMSE={srmse:.4f}, redistributing...")

            # --- Strategy A: Merge surplus 1-person HHs into 2/3/4-person ---
            surplus_1 = size_counts.get(1, 0) - target_counts.get(1, 0)

            if surplus_1 > 0:
                # Find 1-person household IDs
                singles = hh_sizes[hh_sizes == 1].index.tolist()
                self.rng.shuffle(singles)

                # How many singles can we consume? = actual - target
                # We must KEEP target_counts[1] singles intact.
                max_consumable = len(singles) - target_counts.get(1, 0)
                if max_consumable < 2:
                    max_consumable = 0

                # Which sizes need more? Prioritize largest deficit first.
                deficit_sizes = sorted(
                    [(s, target_counts[s] - size_counts.get(s, 0))
                     for s in range(2, 8) if target_counts[s] > size_counts.get(s, 0)],
                    key=lambda x: -x[1]
                )

                merged = 0
                si = 0
                consumed = 0
                for target_size, deficit in deficit_sizes:
                    while (deficit > 0
                           and si + target_size <= len(singles)
                           and consumed + target_size <= max_consumable):
                        new_hh = singles[si]
                        for j in range(1, target_size):
                            old_hh = singles[si + j]
                            idx_to_move = agents[agents["household_id"] == old_hh].index[0]
                            agents.at[idx_to_move, "household_id"] = new_hh
                            agents.at[idx_to_move, "household_role"] = "housemate"

                        si += target_size
                        consumed += target_size
                        deficit -= 1
                        merged += 1

                if merged > 0:
                    logger.info(f"  Merged {merged} groups from surplus 1-person HHs "
                                f"(consumed {consumed}, kept {len(singles)-consumed})")

            # Refresh hh_sizes after Strategy A
            hh_sizes = agents.groupby("household_id").size()
            for s in range(1, 9):
                size_counts[s] = int((hh_sizes == s).sum()) if s < 8 else int((hh_sizes >= 8).sum())

            # --- Strategy B: Expand small HHs by merging with 1-person surplus ---
            # If 4-person surplus exists AND 5/6/7-person have deficit,
            # attach 1-person singles to 4-person HHs to create 5/6/7-person HHs.
            for expand_from in [4, 3, 2]:
                surplus_from = size_counts.get(expand_from, 0) - target_counts.get(expand_from, 0)
                if surplus_from <= 0:
                    continue

                # Find expansion targets (sizes that need more)
                for expand_to in [expand_from + 1, expand_from + 2, expand_from + 3]:
                    if expand_to > 8:
                        break
                    deficit_to = target_counts.get(min(expand_to, 8), 0) - size_counts.get(min(expand_to, 8), 0)
                    if deficit_to <= 0 or surplus_from <= 0:
                        continue

                    need_add = expand_to - expand_from  # how many people to add per HH
                    # Get 1-person HH IDs to donate members
                    current_singles = hh_sizes[hh_sizes == 1].index.tolist()
                    # Don't consume below target number of 1-person HHs
                    available_singles = len(current_singles) - target_counts.get(1, 0)
                    if available_singles < need_add or len(current_singles) < need_add:
                        continue

                    source_hhs = hh_sizes[hh_sizes == expand_from].index.tolist()
                    self.rng.shuffle(source_hhs)
                    self.rng.shuffle(current_singles)

                    max_expand = min(deficit_to, surplus_from, available_singles // need_add)
                    expanded = 0
                    si = 0
                    for hh_id in source_hhs:
                        if expanded >= max_expand:
                            break
                        if si + need_add > len(current_singles):
                            break

                        ok = True
                        for j in range(need_add):
                            donor_hh = current_singles[si + j]
                            donors = agents[agents["household_id"] == donor_hh]
                            if len(donors) == 0:
                                ok = False
                                break
                        if not ok:
                            si += need_add
                            continue

                        for _ in range(need_add):
                            donor_hh = current_singles[si]
                            donor_idx = agents[agents["household_id"] == donor_hh].index[0]
                            agents.at[donor_idx, "household_id"] = hh_id
                            agents.at[donor_idx, "household_role"] = "housemate"
                            si += 1

                        expanded += 1

                    if expanded > 0:
                        logger.info(f"  Expanded {expanded} HHs from {expand_from}-person to {expand_to}-person")
                        # Refresh sizes for next iteration
                        hh_sizes = agents.groupby("household_id").size()
                        for s in range(1, 9):
                            size_counts[s] = int((hh_sizes == s).sum()) if s < 8 else int((hh_sizes >= 8).sum())
                        surplus_from = size_counts.get(expand_from, 0) - target_counts.get(expand_from, 0)

            # --- Strategy D: Merge surplus HH pairs to create larger HHs ---
            # e.g., surplus 4-person + surplus 2-person → 6-person (if 6 has deficit)
            hh_sizes = agents.groupby("household_id").size()
            for s in range(1, 9):
                size_counts[s] = int((hh_sizes == s).sum()) if s < 8 else int((hh_sizes >= 8).sum())

            merge_pairs = [
                (4, 1, 5), (4, 2, 6), (4, 3, 7), (3, 2, 5),
                (3, 3, 6), (3, 4, 7), (2, 3, 5), (2, 4, 6),
            ]
            for sa, sb_size, target_size in merge_pairs:
                surplus_a = size_counts.get(sa, 0) - target_counts.get(sa, 0)
                surplus_b = size_counts.get(sb_size, 0) - target_counts.get(sb_size, 0)
                deficit_t = target_counts.get(target_size, 0) - size_counts.get(target_size, 0)
                if surplus_a <= 0 or surplus_b <= 0 or deficit_t <= 0:
                    continue
                if sa == sb_size:
                    surplus_b = surplus_a // 2  # can only use half

                n_merges = min(surplus_a, surplus_b, deficit_t)
                if n_merges <= 0:
                    continue

                hh_a_list = hh_sizes[hh_sizes == sa].index.tolist()
                hh_b_list = hh_sizes[hh_sizes == sb_size].index.tolist()
                self.rng.shuffle(hh_a_list)
                self.rng.shuffle(hh_b_list)

                merged_d = 0
                bi = 0
                for ai in range(min(n_merges, len(hh_a_list))):
                    if bi >= len(hh_b_list):
                        break
                    hh_a = hh_a_list[ai]
                    hh_b = hh_b_list[bi]
                    if hh_a == hh_b:
                        bi += 1
                        continue
                    # Move all members of hh_b into hh_a
                    members_b = agents[agents["household_id"] == hh_b].index.tolist()
                    for m in members_b:
                        agents.at[m, "household_id"] = hh_a
                        if agents.at[m, "household_role"] == "head":
                            agents.at[m, "household_role"] = "housemate"
                    bi += 1
                    merged_d += 1

                if merged_d > 0:
                    logger.info(f"  Merged {merged_d} pairs ({sa}p+{sb_size}p→{target_size}p)")
                    hh_sizes = agents.groupby("household_id").size()
                    for s in range(1, 9):
                        size_counts[s] = int((hh_sizes == s).sum()) if s < 8 else int((hh_sizes >= 8).sum())

            # --- Strategy E: Directly convert surplus 4p → 3p + 1p ---
            # Then use the freed 1p agents for expansion to 5p/6p
            hh_sizes = agents.groupby("household_id").size()
            for s in range(1, 9):
                size_counts[s] = int((hh_sizes == s).sum()) if s < 8 else int((hh_sizes >= 8).sum())

            surplus_4 = size_counts.get(4, 0) - target_counts.get(4, 0)
            if surplus_4 > 0:
                # How many 4p HHs to split? Limited by how many we can absorb
                # into deficit sizes (3p, 5p, 6p, etc.)
                deficit_3 = max(0, target_counts.get(3, 0) - size_counts.get(3, 0))
                deficit_5 = max(0, target_counts.get(5, 0) - size_counts.get(5, 0))
                deficit_6 = max(0, target_counts.get(6, 0) - size_counts.get(6, 0))

                # Split 4p → 3p: creates one 3p and one 1p
                # Then attach 1p to an existing 4p to make 5p (or 5p→6p)
                n_splits = min(surplus_4, deficit_3 + deficit_5 + deficit_6)
                if n_splits > 0:
                    hh_4_list = hh_sizes[hh_sizes == 4].index.tolist()
                    self.rng.shuffle(hh_4_list)

                    split_e = 0
                    freed_singles = []
                    for hh_id in hh_4_list[:n_splits]:
                        members = agents[agents["household_id"] == hh_id].index.tolist()
                        splittable = [
                            m for m in members
                            if agents.loc[m, "household_role"] not in ("head", "spouse")
                            and agents.loc[m, "age"] >= 18
                        ]
                        if splittable:
                            split_idx = splittable[0]
                            new_hh = f"HH{hh_counter[0]:05d}"
                            hh_counter[0] += 1
                            agents.at[split_idx, "household_id"] = new_hh
                            agents.at[split_idx, "household_role"] = "head"
                            freed_singles.append(new_hh)
                            split_e += 1

                    if split_e > 0:
                        logger.info(f"  Strategy E: Split {split_e} members from 4p HHs (→3p+1p)")

                    # Now attach freed singles to 4p HHs to create 5p
                    hh_sizes = agents.groupby("household_id").size()
                    remaining_4p = hh_sizes[hh_sizes == 4].index.tolist()
                    self.rng.shuffle(remaining_4p)

                    attached = 0
                    for si, single_hh in enumerate(freed_singles):
                        if si >= len(remaining_4p):
                            break
                        target_hh = remaining_4p[si]
                        single_idx = agents[agents["household_id"] == single_hh].index[0]
                        agents.at[single_idx, "household_id"] = target_hh
                        agents.at[single_idx, "household_role"] = "housemate"
                        attached += 1

                    if attached > 0:
                        logger.info(f"  Strategy E: Attached {attached} freed singles to 4p→5p")

                    # Refresh
                    hh_sizes = agents.groupby("household_id").size()
                    for s in range(1, 9):
                        size_counts[s] = int((hh_sizes == s).sum()) if s < 8 else int((hh_sizes >= 8).sum())

            # --- Strategy C: Split surplus large HHs (6+) into smaller ---
            for large_size in [7, 6, 5]:
                surplus = size_counts.get(large_size, 0) - target_counts.get(large_size, 0)
                if surplus <= 0:
                    continue

                large_hhs = hh_sizes[hh_sizes == large_size].index.tolist()
                self.rng.shuffle(large_hhs)
                split_count = 0

                for hh_id in large_hhs[:surplus]:
                    members = agents[agents["household_id"] == hh_id].index.tolist()
                    splittable = [
                        m for m in members
                        if agents.loc[m, "household_role"] not in ("head", "spouse")
                        and agents.loc[m, "age"] >= 18
                    ]
                    if splittable:
                        split_idx = splittable[0]
                        new_hh_id = f"HH{hh_counter[0]:05d}"
                        hh_counter[0] += 1
                        agents.at[split_idx, "household_id"] = new_hh_id
                        agents.at[split_idx, "household_role"] = "head"
                        split_count += 1

                if split_count > 0:
                    logger.info(f"  Split {split_count} members from {large_size}-person HHs")

            # Refresh hh_sizes after all strategies
            hh_sizes = agents.groupby("household_id").size()

        # ============================================================
        # VALIDATION: Final household size distribution
        # ============================================================
        hh_sizes = agents.groupby("household_id").size()
        total_hh = len(hh_sizes)
        mean_size = hh_sizes.mean()

        size_dist = {}
        for size in range(1, 9):
            if size < 8:
                count = (hh_sizes == size).sum()
            else:
                count = (hh_sizes >= 8).sum()
            size_dist[size] = count / total_hh

        logger.info(f"Household building complete: {total_hh} households, "
                    f"mean size={mean_size:.2f}")
        logger.info(f"Size distribution:")
        for size in range(1, 9):
            target = TARGET_HH_SIZE_DIST.get(size, 0)
            actual = size_dist.get(size, 0)
            gap = actual - target
            status = "OK" if abs(gap) < 0.03 else "DRIFT"
            logger.info(f"  {size}-person: {actual:.1%} (target: {target:.1%}, "
                        f"gap: {gap:+.1%}) [{status}]")

        return agents
