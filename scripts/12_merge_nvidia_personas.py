"""
Script 12: Merge NVIDIA Nemotron-Personas-Singapore with our 20K agents.

Strategy:
  Our 20K agents have precise demographics (income, housing, Big Five, household)
  but dry persona prompts. NVIDIA's 148K personas have rich narrative text
  (cultural_background, professional_persona, hobbies, etc.) but lack income/housing.

  We match each of our agents to the BEST-FIT NVIDIA persona by:
    1. Exact match: planning_area + gender + education_level
    2. Nearest age (within ±3 years)
    3. Same marital_status (soft)

  Then graft NVIDIA's narrative fields onto our agent record.

  Result: 20K agents with BOTH precise demographics AND rich personas.

Usage:
    python3 scripts/12_merge_nvidia_personas.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "output"


# Education level mapping: our labels -> NVIDIA labels
EDU_MAP = {
    "No_Formal": "No Qualification",
    "Primary": "Primary",
    "Secondary": "Secondary",
    "Post_Secondary": "Post Secondary (Non-Tertiary)",
    "Polytechnic": "Polytechnic",
    "University": "University",
    "Postgraduate": "University",  # NVIDIA has no Postgraduate, map to University
}

# Gender mapping
GENDER_MAP = {"M": "Male", "F": "Female"}

# Planning area normalization: our names -> NVIDIA names
# Both use similar names but we have "Others" bucket
AREA_MAP = {
    "Others": None,  # will use fallback matching
}


def main():
    # Load datasets
    agents = pd.read_csv(OUTPUT_DIR / "agents_20k_v2.csv")
    nvidia = pd.read_parquet(DATA_DIR / "nvidia_personas_singapore.parquet")

    logger.info(f"Our agents: {len(agents):,}")
    logger.info(f"NVIDIA personas: {len(nvidia):,}")

    # Normalize fields for matching
    agents["_gender_nv"] = agents["gender"].map(GENDER_MAP)
    agents["_edu_nv"] = agents["education_level"].map(EDU_MAP)
    agents["_area_nv"] = agents["planning_area"].replace(AREA_MAP)

    # NVIDIA narrative fields to graft
    NARRATIVE_FIELDS = [
        "persona", "professional_persona", "cultural_background",
        "sports_persona", "arts_persona", "travel_persona",
        "culinary_persona", "hobbies_and_interests", "career_goals_and_ambitions",
        "occupation", "industry",
    ]

    # Build NVIDIA index for fast lookup
    # Group by (planning_area, sex, education_level)
    nvidia_groups = {}
    for idx, row in nvidia.iterrows():
        key = (row["planning_area"], row["sex"], row["education_level"])
        if key not in nvidia_groups:
            nvidia_groups[key] = []
        nvidia_groups[key].append(idx)

    logger.info(f"NVIDIA groups: {len(nvidia_groups)} unique (area, sex, edu) combos")

    # Match each agent
    matched = 0
    unmatched = 0
    match_distances = []

    rng = np.random.default_rng(42)
    used_nvidia_ids = set()  # track used personas to maximize diversity

    for i in range(len(agents)):
        agent = agents.iloc[i]
        area = agent["_area_nv"]
        gender = agent["_gender_nv"]
        edu = agent["_edu_nv"]
        age = agent["age"]
        marital = agent["marital_status"]

        # Try exact key match
        key = (area, gender, edu)
        candidates = nvidia_groups.get(key)

        # Fallback 1: relax area (any area, same gender + edu)
        if not candidates:
            fallback_keys = [k for k in nvidia_groups if k[1] == gender and k[2] == edu]
            candidates = []
            for fk in fallback_keys:
                candidates.extend(nvidia_groups[fk])

        # Fallback 2: relax edu too (same gender only)
        if not candidates:
            fallback_keys = [k for k in nvidia_groups if k[1] == gender]
            candidates = []
            for fk in fallback_keys:
                candidates.extend(nvidia_groups[fk])

        if not candidates:
            # Last resort: any persona
            candidates = list(range(len(nvidia)))

        # Score candidates by age proximity + marital match
        cand_ages = nvidia.iloc[candidates]["age"].values
        cand_marital = nvidia.iloc[candidates]["marital_status"].values

        age_diff = np.abs(cand_ages - age)
        marital_bonus = (cand_marital == marital).astype(float) * 2  # bonus for marital match
        # Prefer unused personas
        unused_bonus = np.array([3.0 if c not in used_nvidia_ids else 0.0 for c in candidates])

        # Combined score (lower = better, but bonuses are subtracted)
        scores = age_diff - marital_bonus - unused_bonus

        # Pick from top-5 best matches randomly (for diversity)
        top_k = min(5, len(scores))
        top_indices = np.argpartition(scores, top_k)[:top_k]
        chosen_local = rng.choice(top_indices)
        chosen_nvidia_idx = candidates[chosen_local]
        used_nvidia_ids.add(chosen_nvidia_idx)

        # Graft narrative fields
        nv_row = nvidia.iloc[chosen_nvidia_idx]
        for field in NARRATIVE_FIELDS:
            agents.at[agents.index[i], field] = nv_row[field]

        match_distances.append(abs(nv_row["age"] - age))
        matched += 1

    logger.info(f"Matched: {matched:,}, Unmatched: {unmatched}")
    logger.info(f"Age distance: mean={np.mean(match_distances):.1f}, "
                f"median={np.median(match_distances):.1f}, "
                f"max={np.max(match_distances)}")

    # Drop temporary columns
    agents.drop(columns=["_gender_nv", "_edu_nv", "_area_nv"], inplace=True)

    # Save merged dataset
    outpath = OUTPUT_DIR / "agents_20k_enriched.csv"
    agents.to_csv(outpath, index=False)
    logger.info(f"Saved enriched agents to {outpath}")

    # Stats
    print("\n" + "=" * 60)
    print("MERGE COMPLETE")
    print("=" * 60)
    print(f"Agents: {len(agents):,}")
    print(f"New fields: {NARRATIVE_FIELDS}")
    print(f"Occupation distribution:")
    for k, v in agents["occupation"].value_counts().head(10).items():
        print(f"  {k}: {v:,} ({v/len(agents):.1%})")
    print(f"\nIndustry distribution:")
    for k, v in agents["industry"].value_counts().head(10).items():
        print(f"  {k}: {v:,} ({v/len(agents):.1%})")

    # Show sample enriched agent
    sample = agents.iloc[100]
    print(f"\n--- SAMPLE ENRICHED AGENT ---")
    print(f"  Age: {sample['age']}, Gender: {sample['gender']}, "
          f"Ethnicity: {sample['ethnicity']}")
    print(f"  Income: ${sample['monthly_income']:,.0f}, "
          f"Housing: {sample['housing_type']}, Area: {sample['planning_area']}")
    print(f"  Big5: O={sample['big5_o']:.1f} C={sample['big5_c']:.1f} "
          f"E={sample['big5_e']:.1f} A={sample['big5_a']:.1f} N={sample['big5_n']:.1f}")
    print(f"  Occupation: {sample['occupation']}")
    print(f"  Industry: {sample['industry']}")
    print(f"  Persona: {str(sample['persona'])[:200]}...")
    print(f"  Cultural: {str(sample['cultural_background'])[:200]}...")


if __name__ == "__main__":
    main()
