"""
Script 20: Seed 172K agents into Supabase (V3 architecture).

Population composition:
  - 148,000 adults (18+) from NVIDIA Nemotron-Personas-Singapore
  - ~24,173 children (0-17) synthetically generated to match Census proportions

Phase 0 of the V3 roadmap:
  1. Read NVIDIA parquet (148K adults)
  2. Map fields to V3 schema
  3. Generate ~24K children based on Census age structure
  4. CPT-augment missing dimensions (ethnicity, residency, income, housing, health)
  5. Generate Big Five personality + attitudes via Cholesky
  6. Assign life phase from life_ontology.yaml
  7. Batch upsert to Supabase

Usage:
    python3 scripts/20_seed_148k_v3.py [--dry-run] [--limit N]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import hashlib
import math
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
PARQUET_PATH = DATA_DIR / "nvidia_personas_singapore.parquet"

# Supabase config (same project as V2)
SUPABASE_URL = "https://rndfpyuuredtqncegygi.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzA4Nzk0NiwiZXhwIjoyMDg4NjYzOTQ2fQ.EMjLfr3N8RDpBPkVftYKCg1Pf6h4rOj8xfCXSuJIxQI"


# ============================================================
# FIELD MAPPINGS
# ============================================================

GENDER_MAP = {"Male": "M", "Female": "F"}

# NVIDIA education -> our 7 categories
EDU_MAP = {
    "No Qualification": "No_Formal",
    "Primary": "Primary",
    "Lower Secondary": "Secondary",
    "Secondary": "Secondary",
    "Post Secondary (Non-Tertiary)": "Post_Secondary",
    "Other Diploma": "Post_Secondary",
    "Polytechnic": "Polytechnic",
    "University": "University",
}

# NVIDIA marital -> our 4 categories
MARITAL_MAP = {
    "Single": "Single",
    "Married": "Married",
    "Divorced/Separated": "Divorced",
    "Widowed": "Widowed",
}

# NVIDIA planning areas -> our 28 (extras go to "Others")
KNOWN_AREAS = {
    "Bedok", "Tampines", "Jurong West", "Sengkang", "Woodlands",
    "Hougang", "Yishun", "Choa Chu Kang", "Punggol", "Bukit Merah",
    "Bukit Batok", "Toa Payoh", "Ang Mo Kio", "Queenstown", "Clementi",
    "Kallang", "Pasir Ris", "Bishan", "Geylang", "Serangoon",
    "Bukit Panjang", "Sembawang", "Marine Parade", "Bukit Timah",
    "Novena", "Central Area", "Tanglin",
}

# Areas that map to "Central Area" or "Others"
AREA_MAP = {
    "Outram": "Central Area",
    "Rochor": "Central Area",
    "River Valley": "Central Area",
    "Downtown Core": "Central Area",
    "Museum": "Central Area",
    "Singapore River": "Central Area",
}

# Age group boundaries
AGE_BINS = list(range(0, 101, 5)) + [120]
AGE_LABELS = [
    "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
    "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79",
    "80-84", "85-89", "90-94", "95-99", "100",
]

# Life phase assignment by age (aligned with life_ontology.yaml)
def assign_life_phase(age: int, gender: str = "M") -> str:
    if age < 7: return "dependence"
    if age < 13: return "growth"
    if age < 17: return "adolescence"
    if age < 19 and gender == "M": return "ns_service"
    if age < 25: return "establishment"
    if age < 36: return "establishment"
    if age < 51: return "bearing"
    if age < 63: return "release"
    if age < 75: return "retirement_early"
    if age < 85: return "decline"
    return "end_of_life"


# ============================================================
# CHILDREN GENERATION
# ============================================================

# Census 2025 age proportions for children (0-17)
# Source: Population Trends 2025 (SingStat)
CHILD_AGE_PROPORTIONS = {
    # age_group: (proportion_of_total_population, age_range_in_years)
    "0-4":  (0.038, 5),   # 0,1,2,3,4
    "5-9":  (0.038, 5),   # 5,6,7,8,9
    "10-14": (0.038, 5),  # 10,11,12,13,14
    "15-17": (0.044 * 3/5, 3),  # 15,16,17 (3/5 of the 15-19 group)
}
# Total child proportion: 14.04%
# Adult (18+) proportion: 85.96%

# Children education is deterministic by age
# (from life_ontology.yaml: PSLE at ~12, O-Level at ~16, streaming at ~13)
CHILD_EDUCATION = {
    range(0, 4):  "No_Formal",      # pre-school
    range(4, 7):  "No_Formal",      # kindergarten (no formal qualification yet)
    range(7, 13): "Primary",        # primary school (P1-P6, PSLE at 12)
    range(13, 17): "Secondary",     # secondary school (Sec 1-4)
    range(17, 18): "Post_Secondary", # JC/Poly/ITE year 1
}

# Children occupation by age
CHILD_OCCUPATION = {
    range(0, 4):   "Infant/Toddler",
    range(4, 7):   "Pre-school Student",
    range(7, 13):  "Primary School Student",
    range(13, 17): "Secondary School Student",
    range(17, 18): "Post-Secondary Student",
}

# Children are overwhelmingly Citizens born in Singapore
# PR children: ~8% (from PR population share among young)
# Non-resident children: rare (<3%, mostly DP dependents)
CHILD_RESIDENCY_PROBS = {
    "Citizen": 0.89,
    "PR": 0.08,
    "DP": 0.03,  # dependent pass (parent is EP/SP holder)
}


def generate_children(adult_df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate synthetic children (0-17) to complement NVIDIA's 18+ adults.

    Method:
      1. Calculate exact count from Census proportions
      2. Distribute across age groups proportionally
      3. Assign demographics: gender (birth sex ratio 1.07 M:F),
         planning area (follows adult distribution = families live together),
         ethnicity (follows national marginal)
      4. Education/occupation deterministic by age
      5. All children: income=0, single, no industry

    Returns DataFrame with same columns as the adult mapping.
    """
    n_adults = len(adult_df)
    adult_prop = 1.0 - sum(p for p, _ in CHILD_AGE_PROPORTIONS.values())
    total_pop = n_adults / adult_prop
    n_children = round(total_pop - n_adults)

    logger.info(f"Generating {n_children:,} children (0-17) to complement {n_adults:,} adults")
    logger.info(f"Target total population: {round(total_pop):,}")

    # Calculate per-age-group counts
    age_group_counts = {}
    allocated = 0
    groups = list(CHILD_AGE_PROPORTIONS.items())
    for i, (ag, (prop, n_years)) in enumerate(groups):
        if i == len(groups) - 1:
            count = n_children - allocated  # last group gets remainder
        else:
            count = round(total_pop * prop)
        age_group_counts[ag] = count
        allocated += count

    for ag, count in age_group_counts.items():
        logger.info(f"  {ag}: {count:,} children")

    # Build child records
    children = []
    # Planning area distribution from adults (children live where adults live)
    area_dist = adult_df["planning_area"].value_counts(normalize=True)
    area_labels = area_dist.index.tolist()
    area_probs = area_dist.values

    # Ethnicity: national marginal (same as adults)
    eth_labels = ["Chinese", "Malay", "Indian", "Others"]
    eth_probs = [0.739, 0.135, 0.090, 0.036]

    # Gender: birth sex ratio in Singapore ~1.07 M:F (SingStat Vital Statistics)
    # i.e., 51.7% male at birth
    gender_probs = [0.517, 0.483]
    gender_labels = ["M", "F"]

    child_seq = 0  # global sequence for deterministic UUID
    for age_group, (prop, n_years) in CHILD_AGE_PROPORTIONS.items():
        count = age_group_counts[age_group]
        # Parse age range
        parts = age_group.split("-")
        age_lo = int(parts[0])
        age_hi = int(parts[1]) if len(parts) > 1 else age_lo

        for _ in range(count):
            age = rng.integers(age_lo, age_hi + 1)
            gender = rng.choice(gender_labels, p=gender_probs)

            # Education by age (deterministic)
            edu = "No_Formal"
            for age_range, edu_level in CHILD_EDUCATION.items():
                if age in age_range:
                    edu = edu_level
                    break

            # Occupation by age
            occ = ""
            for age_range, occ_label in CHILD_OCCUPATION.items():
                if age in age_range:
                    occ = occ_label
                    break

            # Residency
            res_labels = list(CHILD_RESIDENCY_PROBS.keys())
            res_probs = list(CHILD_RESIDENCY_PROBS.values())
            residency = rng.choice(res_labels, p=res_probs)

            child = {
                "agent_id": hashlib.md5(f"child_v3_{child_seq}".encode()).hexdigest(),  # deterministic UUID
                "age": int(age),
                "gender": gender,
                "marital_status": "Single",
                "education_level": edu,
                "occupation": occ,
                "industry": "",
                "planning_area": rng.choice(area_labels, p=area_probs),
                "ethnicity": rng.choice(eth_labels, p=eth_probs),
                "residency_status": residency,
                "monthly_income": 0,
                "income_band": "0",
                "health_status": rng.choice(
                    ["Healthy", "Chronic_Mild", "Chronic_Severe", "Disabled"],
                    p=[0.95, 0.04, 0.008, 0.002]
                ),
                # No NVIDIA narratives for synthetic children
                "persona": "",
                "professional_persona": "",
                "cultural_background": "",
                "sports_persona": "",
                "arts_persona": "",
                "travel_persona": "",
                "culinary_persona": "",
                "hobbies_and_interests": "",
                "career_goals_and_ambitions": "",
                "skills_and_expertise": "",
                "data_source": "synthetic",
            }
            children.append(child)
            child_seq += 1

    child_df = pd.DataFrame(children)
    logger.info(f"Generated {len(child_df):,} children. "
                f"Gender: M={sum(child_df.gender=='M'):,} F={sum(child_df.gender=='F'):,}")
    return child_df


# ============================================================
# CPT AUGMENTATION
# ============================================================

def augment_residency(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Assign residency status. NVIDIA personas are Singapore-based, so
    heavily weighted toward Citizen/PR. Age-conditioned: younger working
    adults more likely non-resident.
    """
    n = len(df)
    df["residency_status"] = "Citizen"  # default

    for i in range(n):
        age = df.iat[i, df.columns.get_loc("age")]
        if age < 18:
            # Children: almost all citizens
            r = rng.random()
            if r < 0.92:
                df.iat[i, df.columns.get_loc("residency_status")] = "Citizen"
            elif r < 0.97:
                df.iat[i, df.columns.get_loc("residency_status")] = "PR"
            else:
                df.iat[i, df.columns.get_loc("residency_status")] = "DP"
        elif age < 30:
            r = rng.random()
            if r < 0.65:
                df.iat[i, df.columns.get_loc("residency_status")] = "Citizen"
            elif r < 0.78:
                df.iat[i, df.columns.get_loc("residency_status")] = "PR"
            elif r < 0.88:
                df.iat[i, df.columns.get_loc("residency_status")] = "EP"
            elif r < 0.94:
                df.iat[i, df.columns.get_loc("residency_status")] = "SP"
            else:
                df.iat[i, df.columns.get_loc("residency_status")] = "WP"
        elif age < 65:
            r = rng.random()
            if r < 0.70:
                df.iat[i, df.columns.get_loc("residency_status")] = "Citizen"
            elif r < 0.85:
                df.iat[i, df.columns.get_loc("residency_status")] = "PR"
            elif r < 0.92:
                df.iat[i, df.columns.get_loc("residency_status")] = "EP"
            elif r < 0.96:
                df.iat[i, df.columns.get_loc("residency_status")] = "SP"
            else:
                df.iat[i, df.columns.get_loc("residency_status")] = "WP"
        else:
            # 65+: mostly citizens/PR
            r = rng.random()
            if r < 0.88:
                df.iat[i, df.columns.get_loc("residency_status")] = "Citizen"
            else:
                df.iat[i, df.columns.get_loc("residency_status")] = "PR"

    return df


def augment_income(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Assign income band and continuous income via P(income | education, age_group).
    Uses simplified CPT from sg_distributions.py.
    """
    bands = ["0", "1-1999", "2000-3499", "3500-4999",
             "5000-6999", "7000-9999", "10000-14999", "15000+"]
    band_midpoints = [0, 1000, 2750, 4250, 6000, 8500, 12500, 20000]

    # Simplified CPT: P(income_band | education_level)
    # Averaged across age groups for speed. Full CPT is in sg_distributions.py.
    edu_income = {
        "No_Formal":      [0.20, 0.25, 0.25, 0.15, 0.08, 0.04, 0.02, 0.01],
        "Primary":        [0.15, 0.22, 0.28, 0.18, 0.09, 0.04, 0.03, 0.01],
        "Secondary":      [0.08, 0.14, 0.26, 0.24, 0.14, 0.08, 0.04, 0.02],
        "Post_Secondary": [0.07, 0.10, 0.22, 0.26, 0.18, 0.09, 0.05, 0.03],
        "Polytechnic":    [0.05, 0.07, 0.18, 0.26, 0.24, 0.12, 0.05, 0.03],
        "University":     [0.04, 0.04, 0.08, 0.16, 0.26, 0.22, 0.13, 0.07],
    }

    n = len(df)
    income_bands = []
    incomes = []

    for i in range(n):
        edu = df.iat[i, df.columns.get_loc("education_level")]
        age = df.iat[i, df.columns.get_loc("age")]

        probs = edu_income.get(edu, edu_income["Secondary"])

        # Age adjustment: retired people (65+) shift toward zero income
        if age >= 70:
            probs = [0.70, 0.12, 0.08, 0.04, 0.03, 0.02, 0.005, 0.005]
        elif age >= 65:
            probs = [0.50, 0.18, 0.12, 0.08, 0.05, 0.03, 0.02, 0.02]
        elif age >= 60:
            # Partial retirement
            probs = [p * 0.6 + (0.3 if j == 0 else 0.1 / 7)
                     for j, p in enumerate(probs)]

        # Normalize
        total = sum(probs)
        probs = [p / total for p in probs]

        band_idx = rng.choice(len(bands), p=probs)
        income_bands.append(bands[band_idx])

        # Continuous income within band (triangular distribution)
        mid = band_midpoints[band_idx]
        if band_idx == 0:
            incomes.append(0)
        elif band_idx == len(bands) - 1:
            incomes.append(int(rng.triangular(15000, 18000, 50000)))
        else:
            lo = band_midpoints[band_idx] - 500
            hi = band_midpoints[band_idx] + 500
            # Use band boundaries
            boundaries = [0, 1, 2000, 3500, 5000, 7000, 10000, 15000, 50000]
            lo = boundaries[band_idx]
            hi = boundaries[band_idx + 1]
            mode = lo + (hi - lo) * 0.4
            incomes.append(int(rng.triangular(lo, mode, hi)))

    df["income_band"] = income_bands
    df["monthly_income"] = incomes
    return df


def augment_housing(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Assign housing type via P(housing | income_band).
    From sg_distributions.py build_housing_income_cpt().
    """
    housing_types = ["HDB_1_2", "HDB_3", "HDB_4", "HDB_5_EC", "Condo", "Landed"]

    income_housing = {
        "0":          [0.22, 0.30, 0.28, 0.13, 0.06, 0.01],
        "1-1999":     [0.16, 0.28, 0.28, 0.16, 0.10, 0.02],
        "2000-3499":  [0.08, 0.22, 0.32, 0.22, 0.13, 0.03],
        "3500-4999":  [0.04, 0.14, 0.32, 0.26, 0.20, 0.04],
        "5000-6999":  [0.02, 0.09, 0.28, 0.28, 0.27, 0.06],
        "7000-9999":  [0.01, 0.05, 0.20, 0.26, 0.38, 0.10],
        "10000-14999":[0.005, 0.03, 0.12, 0.22, 0.47, 0.155],
        "15000+":     [0.005, 0.02, 0.08, 0.15, 0.52, 0.225],
    }

    n = len(df)
    housing = []
    for i in range(n):
        band = df.iat[i, df.columns.get_loc("income_band")]
        probs = income_housing.get(band, income_housing["0"])
        housing.append(rng.choice(housing_types, p=probs))

    df["housing_type"] = housing
    return df


def augment_health(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Assign health status via P(health | age_group).
    From sg_distributions.py build_health_age_cpt().
    """
    health_levels = ["Healthy", "Chronic_Mild", "Chronic_Severe", "Disabled"]

    n = len(df)
    health = []
    for i in range(n):
        age = df.iat[i, df.columns.get_loc("age")]
        if age < 30:
            probs = [0.92, 0.06, 0.015, 0.005]
        elif age < 40:
            probs = [0.86, 0.09, 0.035, 0.015]
        elif age < 50:
            probs = [0.75, 0.155, 0.06, 0.035]
        elif age < 60:
            probs = [0.60, 0.225, 0.115, 0.06]
        elif age < 70:
            probs = [0.42, 0.29, 0.185, 0.105]
        elif age < 80:
            probs = [0.26, 0.29, 0.265, 0.185]
        else:
            probs = [0.15, 0.25, 0.30, 0.30]
        health.append(rng.choice(health_levels, p=probs))

    df["health_status"] = health
    return df


def augment_occupation(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Resample SSOC occupation for employed adults via P(occupation | education, age_group).

    Skips non-employed statuses (children, students, retirees, homemakers,
    unemployed, national service) — their occupation is kept as-is.
    """
    # SSOC major groups — short keys for CPT, mapped to DB names below
    occ_labels = [
        "Manager", "Professional", "Associate Professional",
        "Clerical", "Service and Sales",
        "Production", "Plant and Machine Operator",
        "Cleaner and Labourer", "Agriculture",
    ]
    # Map short CPT labels → full SSOC names used in Supabase DB
    occ_to_db = {
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

    # Simplified CPT inline (mirrors build_occupation_cpt in sg_distributions.py)
    # Keys: (education_level, age_bucket) where age_bucket is coarse
    # Values: probability list aligned with occ_labels
    # Calibrated to MOM 2024 SSOC targets: Mgr 14.5%, Prof 24.0%, AssocProf 25.2%,
    # Clerical 10.2%, Svc/Sales 11.5%, Prod 5.0%, Plant 5.5%, Cleaner 3.8%, Agri 0.3%
    # Calibrated to MOM 2024 SSOC targets given actual employed education distribution:
    # Uni/PG 44%, Poly 18%, PostSec 10%, Sec 14%, Pri/NoFormal 13%
    # Target marginal: Mgr 14.5%, Prof 24.0%, AssocProf 25.2%,
    #   Clerical 10.2%, Svc/Sales 11.5%, Prod 5.0%, Plant 5.5%, Cleaner 3.8%, Agri 0.3%
    edu_occ = {
        # University / Postgraduate — high PMET (~92%)
        ("University",   "young"):  [0.10, 0.50, 0.32, 0.04, 0.02, 0.005, 0.003, 0.001, 0.001],
        ("University",   "mid"):    [0.25, 0.40, 0.27, 0.04, 0.02, 0.008, 0.005, 0.004, 0.003],
        ("University",   "senior"): [0.30, 0.35, 0.26, 0.04, 0.03, 0.008, 0.005, 0.004, 0.003],
        ("Postgraduate", "young"):  [0.12, 0.52, 0.30, 0.03, 0.02, 0.003, 0.003, 0.001, 0.003],
        ("Postgraduate", "mid"):    [0.26, 0.42, 0.26, 0.03, 0.02, 0.005, 0.003, 0.003, 0.002],
        ("Postgraduate", "senior"): [0.32, 0.36, 0.25, 0.03, 0.02, 0.007, 0.005, 0.005, 0.003],
        # Polytechnic — moderate PMET (~65%)
        ("Polytechnic",  "young"):  [0.07, 0.20, 0.38, 0.12, 0.12, 0.04, 0.03,  0.015, 0.005],
        ("Polytechnic",  "mid"):    [0.15, 0.17, 0.33, 0.12, 0.11, 0.04, 0.03,  0.015, 0.005],
        ("Polytechnic",  "senior"): [0.18, 0.15, 0.30, 0.12, 0.12, 0.05, 0.04,  0.02,  0.005],
        # Post_Secondary (ITE/A-Level) — moderate-low PMET (~40%)
        ("Post_Secondary","young"): [0.05, 0.10, 0.26, 0.15, 0.20, 0.08, 0.08,  0.04,  0.005],
        ("Post_Secondary","mid"):   [0.10, 0.08, 0.23, 0.15, 0.19, 0.09, 0.08,  0.05,  0.005],
        ("Post_Secondary","senior"):[0.12, 0.07, 0.20, 0.14, 0.18, 0.10, 0.09,  0.06,  0.005],
        # Secondary — low PMET (~30%)
        ("Secondary",    "young"):  [0.04, 0.06, 0.21, 0.14, 0.24, 0.11, 0.11,  0.06,  0.005],
        ("Secondary",    "mid"):    [0.08, 0.05, 0.18, 0.13, 0.23, 0.11, 0.11,  0.08,  0.005],
        ("Secondary",    "senior"): [0.09, 0.04, 0.15, 0.12, 0.22, 0.12, 0.12,  0.11,  0.005],
        # Primary / No_Formal — very low PMET (~18%)
        ("Primary",      "young"):  [0.03, 0.03, 0.12, 0.09, 0.25, 0.12, 0.15,  0.15,  0.005],
        ("Primary",      "mid"):    [0.04, 0.03, 0.11, 0.08, 0.24, 0.12, 0.15,  0.17,  0.005],
        ("Primary",      "senior"): [0.05, 0.02, 0.08, 0.07, 0.21, 0.12, 0.15,  0.24,  0.005],
        ("No_Formal",    "young"):  [0.03, 0.02, 0.10, 0.08, 0.25, 0.12, 0.16,  0.18,  0.005],
        ("No_Formal",    "mid"):    [0.03, 0.02, 0.10, 0.08, 0.25, 0.12, 0.16,  0.18,  0.005],
        ("No_Formal",    "senior"): [0.04, 0.02, 0.07, 0.06, 0.21, 0.12, 0.16,  0.26,  0.005],
    }

    # Occupation strings that should NOT be resampled (non-employed)
    skip_occupations = {
        "Retired", "Homemaker",
        "Infant/Toddler", "Pre-school Student",
        "Primary School Student", "Secondary School Student",
        "Post-Secondary Student", "Student",
        "University Student", "Polytechnic Student",
        "Unemployed", "National Service",
        "Full-time National Serviceman",
    }
    # Also skip any occupation containing "Student" (catches variants)
    def should_skip(occ_str: str) -> bool:
        if not occ_str:
            return True  # empty → probably a child, skip
        if occ_str in skip_occupations:
            return True
        if "Student" in occ_str or "student" in occ_str:
            return True
        if "Retired" in occ_str or "retired" in occ_str:
            return True
        if "Homemaker" in occ_str or "homemaker" in occ_str:
            return True
        if "National Service" in occ_str:
            return True
        return False

    def age_bucket(age: int) -> str:
        if age < 35:
            return "young"
        elif age < 50:
            return "mid"
        else:
            return "senior"

    n = len(df)
    occ_col = df.columns.get_loc("occupation")
    age_col = df.columns.get_loc("age")
    edu_col = df.columns.get_loc("education_level")

    resampled = 0
    skipped = 0

    for i in range(n):
        current_occ = str(df.iat[i, occ_col])
        if should_skip(current_occ):
            skipped += 1
            continue

        age = int(df.iat[i, age_col])
        edu = str(df.iat[i, edu_col])
        bucket = age_bucket(age)

        key = (edu, bucket)
        probs = edu_occ.get(key, edu_occ[("Secondary", "mid")])  # fallback

        # Normalize (safety)
        total = sum(probs)
        probs_norm = [p / total for p in probs]

        new_occ = rng.choice(occ_labels, p=probs_norm)
        df.iat[i, occ_col] = occ_to_db[new_occ]
        resampled += 1

    logger.info(f"Occupation resampled: {resampled:,} employed adults, "
                f"{skipped:,} skipped (non-employed)")
    return df


# ============================================================
# PERSONALITY (Big Five + Attitudes)
# ============================================================

# SE Asian baseline (Schmitt 2007)
BIG5_MEANS = np.array([3.45, 3.30, 3.20, 3.55, 2.85])  # O, C, E, A, N
BIG5_SDS = np.array([0.55, 0.58, 0.60, 0.52, 0.62])
TRAIT_CORR = np.array([
    [1.00,  0.10,  0.25,  0.10, -0.15],
    [0.10,  1.00,  0.15,  0.20, -0.30],
    [0.25,  0.15,  1.00,  0.15, -0.25],
    [0.10,  0.20,  0.15,  1.00, -0.35],
    [-0.15, -0.30, -0.25, -0.35, 1.00],
])
CHOLESKY = np.linalg.cholesky(TRAIT_CORR)

AGE_TRAJ = {
    0: [0.0, -0.20, 0.10, -0.15, 0.05],
    1: [0.05, -0.10, 0.05, -0.10, 0.10],
    2: [0.0, 0.0, 0.0, 0.0, 0.0],
    3: [-0.05, 0.10, -0.05, 0.08, -0.08],
    4: [-0.08, 0.15, -0.08, 0.12, -0.12],
    5: [-0.10, 0.18, -0.12, 0.15, -0.15],
    6: [-0.12, 0.20, -0.15, 0.18, -0.18],
    7: [-0.15, 0.18, -0.18, 0.20, -0.20],
    8: [-0.18, 0.15, -0.20, 0.22, -0.22],
    9: [-0.20, 0.12, -0.22, 0.25, -0.25],
    10: [-0.20, 0.12, -0.22, 0.25, -0.25],
}
GENDER_ADJ = {
    "M": np.array([0.05, 0.0, -0.05, -0.10, -0.15]),
    "F": np.array([-0.05, 0.0, 0.05, 0.10, 0.15]),
}


def augment_personality(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Generate Big Five + attitudes for all agents via batch Cholesky sampling."""
    n = len(df)
    logger.info(f"Generating Big Five + attitudes for {n:,} agents...")

    ages = df["age"].values
    genders = df["gender"].values

    # Vectorized Big Five generation
    Z = rng.standard_normal((n, 5))
    correlated = Z @ CHOLESKY.T  # apply correlation structure

    results = np.zeros((n, 5))
    for i in range(n):
        decade = min(ages[i] // 10, 10)
        age_adj = np.array(AGE_TRAJ[decade])
        g_adj = GENDER_ADJ.get(genders[i], np.zeros(5))
        means = BIG5_MEANS + age_adj + g_adj
        results[i] = np.clip(means + BIG5_SDS * correlated[i], 1.0, 5.0)

    df["big5_o"] = np.round(results[:, 0], 2)
    df["big5_c"] = np.round(results[:, 1], 2)
    df["big5_e"] = np.round(results[:, 2], 2)
    df["big5_a"] = np.round(results[:, 3], 2)
    df["big5_n"] = np.round(results[:, 4], 2)

    # Attitudes derived from Big Five + demographics
    age_factor = -0.01 * (ages - 30)
    risk = 0.3 * results[:, 0] - 0.2 * results[:, 4] - 0.15 * results[:, 1] + 0.15 * age_factor + 2.5 + rng.normal(0, 0.3, n)
    df["risk_appetite"] = np.clip(np.round(risk, 2), 1.0, 5.0)

    age_conserv = 0.008 * (ages - 25)
    political = 0.35 * results[:, 0] - 0.15 * results[:, 1] - age_conserv + 1.8 + rng.normal(0, 0.35, n)
    df["political_leaning"] = np.clip(np.round(political, 2), 1.0, 5.0)

    trust = 0.25 * results[:, 3] + 0.15 * results[:, 2] - 0.15 * results[:, 4] + 2.2 + rng.normal(0, 0.3, n)
    df["social_trust"] = np.clip(np.round(trust, 2), 1.0, 5.0)

    eth_boost = df["ethnicity"].map({"Chinese": 0.0, "Malay": 0.5, "Indian": 0.3, "Others": 0.1}).fillna(0).values
    age_rel = 0.005 * (ages - 25)
    devotion = 0.15 * results[:, 1] + 0.10 * results[:, 3] + eth_boost + age_rel + 2.0 + rng.normal(0, 0.4, n)
    df["religious_devotion"] = np.clip(np.round(devotion, 2), 1.0, 5.0)

    logger.info(f"Big Five means: O={results[:,0].mean():.2f} C={results[:,1].mean():.2f} "
                f"E={results[:,2].mean():.2f} A={results[:,3].mean():.2f} N={results[:,4].mean():.2f}")
    return df


# ============================================================
# SUPABASE UPLOAD
# ============================================================

def batch_upsert(supabase, table: str, records: list, batch_size: int = 200):
    """Upsert records in batches with retry."""
    import time
    total = len(records)
    batches = math.ceil(total / batch_size)
    logger.info(f"Upserting {total:,} records to '{table}' in {batches} batches (size={batch_size})")

    success = 0
    errors = 0

    for i in range(batches):
        start = i * batch_size
        end = min(start + batch_size, total)
        batch = records[start:end]

        for attempt in range(3):
            try:
                supabase.table(table).upsert(batch).execute()
                success += len(batch)
                if (i + 1) % 50 == 0 or i == batches - 1:
                    logger.info(f"  Batch {i+1}/{batches}: {success:,}/{total:,} uploaded")
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)  # 1s, 2s backoff
                    continue
                logger.error(f"  Batch {i+1} failed after 3 attempts: {e}")
                # Retry with smaller batches
                for j in range(0, len(batch), 20):
                    mini = batch[j:j+20]
                    try:
                        supabase.table(table).upsert(mini).execute()
                        success += len(mini)
                    except Exception as e2:
                        errors += len(mini)
                        logger.error(f"  Mini-batch failed: {e2}")
                    time.sleep(0.5)

    logger.info(f"Upload complete: {success:,} success, {errors:,} errors")
    return success, errors


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Seed 172K agents (V3)")
    parser.add_argument("--dry-run", action="store_true", help="Process data but don't upload")
    parser.add_argument("--limit", type=int, default=0, help="Limit NVIDIA rows for testing (0=all)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    # ========================================
    # STEP 1: Load NVIDIA parquet (148K adults)
    # ========================================
    logger.info(f"Loading NVIDIA parquet from {PARQUET_PATH}")
    df = pd.read_parquet(PARQUET_PATH)
    logger.info(f"Loaded {len(df):,} adults (18+), {len(df.columns)} columns")

    if args.limit > 0:
        df = df.head(args.limit)
        logger.info(f"Limited to {len(df):,} rows for testing")

    # ========================================
    # STEP 2: Map NVIDIA fields to V3 schema
    # ========================================
    logger.info("Mapping NVIDIA fields to V3 schema...")
    df["agent_id"] = df["uuid"]
    df["gender"] = df["sex"].map(GENDER_MAP)
    df["education_level"] = df["education_level"].map(EDU_MAP).fillna("Secondary")
    df["marital_status"] = df["marital_status"].map(MARITAL_MAP).fillna("Single")

    # Planning area normalization
    df["planning_area"] = df["planning_area"].map(
        lambda x: AREA_MAP.get(x, x) if x not in KNOWN_AREAS else x
    )
    df.loc[~df["planning_area"].isin(KNOWN_AREAS | {"Central Area"}), "planning_area"] = "Others"

    # ========================================
    # STEP 3: Generate children (0-17)
    # ========================================
    child_df = generate_children(df, rng)

    # ========================================
    # STEP 4: Merge adults + children
    # ========================================
    df["data_source"] = "nvidia_nemotron"
    # Ensure narrative columns exist in child_df (already set to "")
    # Concat
    df = pd.concat([df, child_df], ignore_index=True)
    logger.info(f"Merged population: {len(df):,} agents (adults + children)")

    # ========================================
    # STEP 5: Common field assignments
    # ========================================
    # Age group (for all agents)
    df["age_group"] = pd.cut(
        df["age"], bins=AGE_BINS, labels=AGE_LABELS, right=False, include_lowest=True
    ).astype(str)

    # Life phase (uses age + gender for NS assignment)
    df["life_phase"] = df.apply(lambda r: assign_life_phase(r["age"], r["gender"]), axis=1)

    # ========================================
    # STEP 6: CPT augmentation (adults only — children already have these)
    # ========================================
    # Mark which rows need augmentation
    is_adult = df["data_source"] == "nvidia_nemotron"

    logger.info("Augmenting ethnicity (adults)...")
    adult_idx = df[is_adult].index
    eth_vals = rng.choice(
        ["Chinese", "Malay", "Indian", "Others"],
        size=len(adult_idx),
        p=[0.739, 0.135, 0.090, 0.036]
    )
    df.loc[adult_idx, "ethnicity"] = eth_vals

    logger.info("Augmenting residency status (adults)...")
    df_adults_only = df.loc[is_adult].copy()
    df_adults_only = augment_residency(df_adults_only, rng)
    df.loc[is_adult, "residency_status"] = df_adults_only["residency_status"]

    logger.info("Augmenting income (adults)...")
    df_adults_only = df.loc[is_adult].copy()
    df_adults_only = augment_income(df_adults_only, rng)
    df.loc[is_adult, "income_band"] = df_adults_only["income_band"]
    df.loc[is_adult, "monthly_income"] = df_adults_only["monthly_income"]

    logger.info("Augmenting housing...")
    # Housing for ALL (children inherit area-consistent housing)
    df = augment_housing(df, rng)

    logger.info("Augmenting health status (adults)...")
    df_adults_only = df.loc[is_adult].copy()
    df_adults_only = augment_health(df_adults_only, rng)
    df.loc[is_adult, "health_status"] = df_adults_only["health_status"]

    logger.info("Augmenting occupation (employed adults)...")
    df_adults_only = df.loc[is_adult].copy()
    df_adults_only = augment_occupation(df_adults_only, rng)
    df.loc[is_adult, "occupation"] = df_adults_only["occupation"]

    # ========================================
    # STEP 7: Personality (all agents)
    # ========================================
    df = augment_personality(df, rng)

    # ========================================
    # STEP 8: Final flags
    # ========================================
    df["is_alive"] = True

    # ========================================
    # STEP 9: Validation summary
    # ========================================
    n_adults = (df["data_source"] == "nvidia_nemotron").sum()
    n_children = (df["data_source"] == "synthetic").sum()
    logger.info("\n=== VALIDATION SUMMARY ===")
    logger.info(f"Total agents: {len(df):,} (adults: {n_adults:,}, children: {n_children:,})")
    logger.info(f"Child proportion: {n_children/len(df)*100:.2f}% (Census target: 14.04%)")
    logger.info(f"Gender: {df['gender'].value_counts().to_dict()}")
    logger.info(f"Ethnicity: {df['ethnicity'].value_counts().to_dict()}")
    logger.info(f"Residency: {df['residency_status'].value_counts().to_dict()}")
    logger.info(f"Education: {df['education_level'].value_counts().to_dict()}")
    logger.info(f"Housing: {df['housing_type'].value_counts().to_dict()}")
    logger.info(f"Health: {df['health_status'].value_counts().to_dict()}")
    logger.info(f"Income median (adults): ${df[df.data_source=='nvidia_nemotron']['monthly_income'].median():,.0f}")
    logger.info(f"Age range: {df['age'].min()}-{df['age'].max()}")
    logger.info(f"Life phases: {df['life_phase'].value_counts().to_dict()}")
    logger.info(f"Planning areas: {df['planning_area'].nunique()}")

    if args.dry_run:
        logger.info("DRY RUN — skipping upload")
        out_path = DATA_DIR / "output" / "agents_172k_v3_preview.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Save: first 500 adults + first 500 children
        preview = pd.concat([
            df[df.data_source == "nvidia_nemotron"].head(500),
            df[df.data_source == "synthetic"].head(500),
        ])
        preview.to_csv(out_path, index=False)
        logger.info(f"Preview saved to {out_path} ({len(preview)} rows)")
        return

    # 7. Upload to Supabase via REST API (original proven method)
    logger.info("Connecting to Supabase...")
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    V3_COLUMNS = [
        "agent_id", "age", "age_group", "gender", "marital_status",
        "education_level", "occupation", "industry", "planning_area",
        "persona", "professional_persona", "cultural_background",
        "sports_persona", "arts_persona", "travel_persona",
        "culinary_persona", "hobbies_and_interests",
        "career_goals_and_ambitions", "skills_and_expertise",
        "ethnicity", "residency_status", "monthly_income", "income_band",
        "housing_type", "health_status",
        "big5_o", "big5_c", "big5_e", "big5_a", "big5_n",
        "risk_appetite", "political_leaning", "social_trust", "religious_devotion",
        "life_phase", "is_alive", "data_source",
    ]

    INT_COLS = ["age", "monthly_income"]
    for col in INT_COLS:
        df[col] = df[col].fillna(0).astype(int)

    logger.info("Preparing records for upload...")
    records = []
    for _, row in df.iterrows():
        rec = {}
        for col in V3_COLUMNS:
            val = row.get(col, None)
            if pd.isna(val):
                val = None
            elif isinstance(val, (np.integer, np.int64)):
                val = int(val)
            elif isinstance(val, (np.floating, np.float64)):
                if col in INT_COLS:
                    val = int(val)
                else:
                    val = float(val)
            elif isinstance(val, np.bool_):
                val = bool(val)
            rec[col] = val
        records.append(rec)

    logger.info(f"Uploading {len(records):,} agents to Supabase...")
    success, errors = batch_upsert(supabase, "agents", records, batch_size=500)
    final_count = success

    print("\n" + "=" * 60)
    print("V3 SEED COMPLETE")
    print("=" * 60)
    print(f"Agents:     {final_count:,} in database")
    print(f"  Adults:   {n_adults:,} (NVIDIA Nemotron)")
    print(f"  Children: {n_children:,} (synthetic, Census-proportioned)")
    print(f"Database:   {SUPABASE_URL}")


if __name__ == "__main__":
    main()
