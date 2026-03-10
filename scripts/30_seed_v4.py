"""
Script 30: Seed 172K agents into NEW Supabase (V4 architecture).

V4 changes vs V3:
  - agents table: demographics only (no narrative text)
  - agent_profiles table: narrative text (persona, cultural_background, etc.)
  - New database: rndfpyuuredtqncegygi

Usage:
    python3 scripts/30_seed_v4.py [--dry-run] [--limit N] [--skip-profiles]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import hashlib
import math
import logging
import time
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
PARQUET_PATH = DATA_DIR / "nvidia_personas_singapore.parquet"

# NEW Supabase (V4)
SUPABASE_URL = "https://rndfpyuuredtqncegygi.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzA4Nzk0NiwiZXhwIjoyMDg4NjYzOTQ2fQ.EMjLfr3N8RDpBPkVftYKCg1Pf6h4rOj8xfCXSuJIxQI"


# ============================================================
# FIELD MAPPINGS (same as V3)
# ============================================================

GENDER_MAP = {"Male": "M", "Female": "F"}

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

MARITAL_MAP = {
    "Single": "Single",
    "Married": "Married",
    "Divorced/Separated": "Divorced",
    "Widowed": "Widowed",
}

KNOWN_AREAS = {
    "Bedok", "Tampines", "Jurong West", "Sengkang", "Woodlands",
    "Hougang", "Yishun", "Choa Chu Kang", "Punggol", "Bukit Merah",
    "Bukit Batok", "Toa Payoh", "Ang Mo Kio", "Queenstown", "Clementi",
    "Kallang", "Pasir Ris", "Bishan", "Geylang", "Serangoon",
    "Bukit Panjang", "Sembawang", "Marine Parade", "Bukit Timah",
    "Novena", "Central Area", "Tanglin",
}

AREA_MAP = {
    "Outram": "Central Area",
    "Rochor": "Central Area",
    "River Valley": "Central Area",
    "Downtown Core": "Central Area",
    "Museum": "Central Area",
    "Singapore River": "Central Area",
}

AGE_BINS = list(range(0, 101, 5)) + [120]
AGE_LABELS = [
    "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
    "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79",
    "80-84", "85-89", "90-94", "95-99", "100",
]


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
# CHILDREN GENERATION (same as V3)
# ============================================================

CHILD_AGE_PROPORTIONS = {
    "0-4":  (0.038, 5),
    "5-9":  (0.038, 5),
    "10-14": (0.038, 5),
    "15-17": (0.044 * 3/5, 3),
}

CHILD_EDUCATION = {
    range(0, 4):  "No_Formal",
    range(4, 7):  "No_Formal",
    range(7, 13): "Primary",
    range(13, 17): "Secondary",
    range(17, 18): "Post_Secondary",
}

CHILD_OCCUPATION = {
    range(0, 4):   "Infant/Toddler",
    range(4, 7):   "Pre-school Student",
    range(7, 13):  "Primary School Student",
    range(13, 17): "Secondary School Student",
    range(17, 18): "Post-Secondary Student",
}

CHILD_RESIDENCY_PROBS = {
    "Citizen": 0.89,
    "PR": 0.08,
    "DP": 0.03,
}


def generate_children(adult_df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    n_adults = len(adult_df)
    adult_prop = 1.0 - sum(p for p, _ in CHILD_AGE_PROPORTIONS.values())
    total_pop = n_adults / adult_prop
    n_children = round(total_pop - n_adults)

    logger.info(f"Generating {n_children:,} children (0-17) to complement {n_adults:,} adults")

    age_group_counts = {}
    allocated = 0
    groups = list(CHILD_AGE_PROPORTIONS.items())
    for i, (ag, (prop, n_years)) in enumerate(groups):
        if i == len(groups) - 1:
            count = n_children - allocated
        else:
            count = round(total_pop * prop)
        age_group_counts[ag] = count
        allocated += count

    area_dist = adult_df["planning_area"].value_counts(normalize=True)
    area_labels = area_dist.index.tolist()
    area_probs = area_dist.values

    eth_labels = ["Chinese", "Malay", "Indian", "Others"]
    eth_probs = [0.739, 0.135, 0.090, 0.036]
    gender_probs = [0.517, 0.483]
    gender_labels = ["M", "F"]

    children = []
    child_seq = 0
    for age_group, (prop, n_years) in CHILD_AGE_PROPORTIONS.items():
        count = age_group_counts[age_group]
        parts = age_group.split("-")
        age_lo = int(parts[0])
        age_hi = int(parts[1]) if len(parts) > 1 else age_lo

        for _ in range(count):
            age = rng.integers(age_lo, age_hi + 1)
            gender = rng.choice(gender_labels, p=gender_probs)

            edu = "No_Formal"
            for age_range, edu_level in CHILD_EDUCATION.items():
                if age in age_range:
                    edu = edu_level
                    break

            occ = ""
            for age_range, occ_label in CHILD_OCCUPATION.items():
                if age in age_range:
                    occ = occ_label
                    break

            res_labels = list(CHILD_RESIDENCY_PROBS.keys())
            res_probs = list(CHILD_RESIDENCY_PROBS.values())
            residency = rng.choice(res_labels, p=res_probs)

            child = {
                "agent_id": hashlib.md5(f"child_v3_{child_seq}".encode()).hexdigest(),
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
    logger.info(f"Generated {len(child_df):,} children")
    return child_df


# ============================================================
# CPT AUGMENTATION (same as V3 — imported inline)
# ============================================================

def augment_residency(df, rng):
    n = len(df)
    df["residency_status"] = "Citizen"
    for i in range(n):
        age = df.iat[i, df.columns.get_loc("age")]
        if age < 18:
            r = rng.random()
            if r < 0.92: df.iat[i, df.columns.get_loc("residency_status")] = "Citizen"
            elif r < 0.97: df.iat[i, df.columns.get_loc("residency_status")] = "PR"
            else: df.iat[i, df.columns.get_loc("residency_status")] = "DP"
        elif age < 30:
            r = rng.random()
            if r < 0.65: df.iat[i, df.columns.get_loc("residency_status")] = "Citizen"
            elif r < 0.78: df.iat[i, df.columns.get_loc("residency_status")] = "PR"
            elif r < 0.88: df.iat[i, df.columns.get_loc("residency_status")] = "EP"
            elif r < 0.94: df.iat[i, df.columns.get_loc("residency_status")] = "SP"
            else: df.iat[i, df.columns.get_loc("residency_status")] = "WP"
        elif age < 65:
            r = rng.random()
            if r < 0.70: df.iat[i, df.columns.get_loc("residency_status")] = "Citizen"
            elif r < 0.85: df.iat[i, df.columns.get_loc("residency_status")] = "PR"
            elif r < 0.92: df.iat[i, df.columns.get_loc("residency_status")] = "EP"
            elif r < 0.96: df.iat[i, df.columns.get_loc("residency_status")] = "SP"
            else: df.iat[i, df.columns.get_loc("residency_status")] = "WP"
        else:
            r = rng.random()
            if r < 0.88: df.iat[i, df.columns.get_loc("residency_status")] = "Citizen"
            else: df.iat[i, df.columns.get_loc("residency_status")] = "PR"
    return df


def augment_income(df, rng):
    bands = ["0", "1-1999", "2000-3499", "3500-4999", "5000-6999", "7000-9999", "10000-14999", "15000+"]
    band_midpoints = [0, 1000, 2750, 4250, 6000, 8500, 12500, 20000]
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
        if age >= 70: probs = [0.70, 0.12, 0.08, 0.04, 0.03, 0.02, 0.005, 0.005]
        elif age >= 65: probs = [0.50, 0.18, 0.12, 0.08, 0.05, 0.03, 0.02, 0.02]
        elif age >= 60:
            probs = [p * 0.6 + (0.3 if j == 0 else 0.1 / 7) for j, p in enumerate(probs)]
        total = sum(probs)
        probs = [p / total for p in probs]
        band_idx = rng.choice(len(bands), p=probs)
        income_bands.append(bands[band_idx])
        if band_idx == 0: incomes.append(0)
        elif band_idx == len(bands) - 1: incomes.append(int(rng.triangular(15000, 18000, 50000)))
        else:
            boundaries = [0, 1, 2000, 3500, 5000, 7000, 10000, 15000, 50000]
            lo = boundaries[band_idx]
            hi = boundaries[band_idx + 1]
            mode = lo + (hi - lo) * 0.4
            incomes.append(int(rng.triangular(lo, mode, hi)))
    df["income_band"] = income_bands
    df["monthly_income"] = incomes
    return df


def augment_housing(df, rng):
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


def augment_health(df, rng):
    health_levels = ["Healthy", "Chronic_Mild", "Chronic_Severe", "Disabled"]
    n = len(df)
    health = []
    for i in range(n):
        age = df.iat[i, df.columns.get_loc("age")]
        if age < 30: probs = [0.92, 0.06, 0.015, 0.005]
        elif age < 40: probs = [0.86, 0.09, 0.035, 0.015]
        elif age < 50: probs = [0.75, 0.155, 0.06, 0.035]
        elif age < 60: probs = [0.60, 0.225, 0.115, 0.06]
        elif age < 70: probs = [0.42, 0.29, 0.185, 0.105]
        elif age < 80: probs = [0.26, 0.29, 0.265, 0.185]
        else: probs = [0.15, 0.25, 0.30, 0.30]
        health.append(rng.choice(health_levels, p=probs))
    df["health_status"] = health
    return df


def augment_occupation(df, rng):
    occ_labels = [
        "Manager", "Professional", "Associate Professional",
        "Clerical", "Service and Sales",
        "Production", "Plant and Machine Operator",
        "Cleaner and Labourer", "Agriculture",
    ]
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
    edu_occ = {
        ("University","young"):[0.10,0.50,0.32,0.04,0.02,0.005,0.003,0.001,0.001],
        ("University","mid"):[0.25,0.40,0.27,0.04,0.02,0.008,0.005,0.004,0.003],
        ("University","senior"):[0.30,0.35,0.26,0.04,0.03,0.008,0.005,0.004,0.003],
        ("Postgraduate","young"):[0.12,0.52,0.30,0.03,0.02,0.003,0.003,0.001,0.003],
        ("Postgraduate","mid"):[0.26,0.42,0.26,0.03,0.02,0.005,0.003,0.003,0.002],
        ("Postgraduate","senior"):[0.32,0.36,0.25,0.03,0.02,0.007,0.005,0.005,0.003],
        ("Polytechnic","young"):[0.07,0.20,0.38,0.12,0.12,0.04,0.03,0.015,0.005],
        ("Polytechnic","mid"):[0.15,0.17,0.33,0.12,0.11,0.04,0.03,0.015,0.005],
        ("Polytechnic","senior"):[0.18,0.15,0.30,0.12,0.12,0.05,0.04,0.02,0.005],
        ("Post_Secondary","young"):[0.05,0.10,0.26,0.15,0.20,0.08,0.08,0.04,0.005],
        ("Post_Secondary","mid"):[0.10,0.08,0.23,0.15,0.19,0.09,0.08,0.05,0.005],
        ("Post_Secondary","senior"):[0.12,0.07,0.20,0.14,0.18,0.10,0.09,0.06,0.005],
        ("Secondary","young"):[0.04,0.06,0.21,0.14,0.24,0.11,0.11,0.06,0.005],
        ("Secondary","mid"):[0.08,0.05,0.18,0.13,0.23,0.11,0.11,0.08,0.005],
        ("Secondary","senior"):[0.09,0.04,0.15,0.12,0.22,0.12,0.12,0.11,0.005],
        ("Primary","young"):[0.03,0.03,0.12,0.09,0.25,0.12,0.15,0.15,0.005],
        ("Primary","mid"):[0.04,0.03,0.11,0.08,0.24,0.12,0.15,0.17,0.005],
        ("Primary","senior"):[0.05,0.02,0.08,0.07,0.21,0.12,0.15,0.24,0.005],
        ("No_Formal","young"):[0.03,0.02,0.10,0.08,0.25,0.12,0.16,0.18,0.005],
        ("No_Formal","mid"):[0.03,0.02,0.10,0.08,0.25,0.12,0.16,0.18,0.005],
        ("No_Formal","senior"):[0.04,0.02,0.07,0.06,0.21,0.12,0.16,0.26,0.005],
    }
    skip_occupations = {
        "Retired","Homemaker","Infant/Toddler","Pre-school Student",
        "Primary School Student","Secondary School Student",
        "Post-Secondary Student","Student","University Student",
        "Polytechnic Student","Unemployed","National Service",
        "Full-time National Serviceman",
    }
    def should_skip(occ_str):
        if not occ_str: return True
        if occ_str in skip_occupations: return True
        if "Student" in occ_str or "student" in occ_str: return True
        if "Retired" in occ_str or "retired" in occ_str: return True
        if "Homemaker" in occ_str or "homemaker" in occ_str: return True
        if "National Service" in occ_str: return True
        return False

    def age_bucket(age):
        if age < 35: return "young"
        elif age < 50: return "mid"
        else: return "senior"

    n = len(df)
    occ_col = df.columns.get_loc("occupation")
    age_col = df.columns.get_loc("age")
    edu_col = df.columns.get_loc("education_level")
    resampled = 0
    for i in range(n):
        current_occ = str(df.iat[i, occ_col])
        if should_skip(current_occ): continue
        age = int(df.iat[i, age_col])
        edu = str(df.iat[i, edu_col])
        key = (edu, age_bucket(age))
        probs = edu_occ.get(key, edu_occ[("Secondary", "mid")])
        total = sum(probs)
        probs_norm = [p / total for p in probs]
        new_occ = rng.choice(occ_labels, p=probs_norm)
        df.iat[i, occ_col] = occ_to_db[new_occ]
        resampled += 1
    logger.info(f"Occupation resampled: {resampled:,} employed adults")
    return df


# ============================================================
# PERSONALITY (Big Five + Attitudes) — same as V3
# ============================================================

BIG5_MEANS = np.array([3.45, 3.30, 3.20, 3.55, 2.85])
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
    0:[0.0,-0.20,0.10,-0.15,0.05],1:[0.05,-0.10,0.05,-0.10,0.10],
    2:[0.0,0.0,0.0,0.0,0.0],3:[-0.05,0.10,-0.05,0.08,-0.08],
    4:[-0.08,0.15,-0.08,0.12,-0.12],5:[-0.10,0.18,-0.12,0.15,-0.15],
    6:[-0.12,0.20,-0.15,0.18,-0.18],7:[-0.15,0.18,-0.18,0.20,-0.20],
    8:[-0.18,0.15,-0.20,0.22,-0.22],9:[-0.20,0.12,-0.22,0.25,-0.25],
    10:[-0.20,0.12,-0.22,0.25,-0.25],
}
GENDER_ADJ = {
    "M": np.array([0.05, 0.0, -0.05, -0.10, -0.15]),
    "F": np.array([-0.05, 0.0, 0.05, 0.10, 0.15]),
}


def augment_personality(df, rng):
    n = len(df)
    logger.info(f"Generating Big Five + attitudes for {n:,} agents...")
    ages = df["age"].values
    genders = df["gender"].values
    Z = rng.standard_normal((n, 5))
    correlated = Z @ CHOLESKY.T
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

    age_factor = -0.01 * (ages - 30)
    risk = 0.3*results[:,0] - 0.2*results[:,4] - 0.15*results[:,1] + 0.15*age_factor + 2.5 + rng.normal(0, 0.3, n)
    df["risk_appetite"] = np.clip(np.round(risk, 2), 1.0, 5.0)
    age_conserv = 0.008 * (ages - 25)
    political = 0.35*results[:,0] - 0.15*results[:,1] - age_conserv + 1.8 + rng.normal(0, 0.35, n)
    df["political_leaning"] = np.clip(np.round(political, 2), 1.0, 5.0)
    trust = 0.25*results[:,3] + 0.15*results[:,2] - 0.15*results[:,4] + 2.2 + rng.normal(0, 0.3, n)
    df["social_trust"] = np.clip(np.round(trust, 2), 1.0, 5.0)
    eth_boost = df["ethnicity"].map({"Chinese":0.0,"Malay":0.5,"Indian":0.3,"Others":0.1}).fillna(0).values
    age_rel = 0.005 * (ages - 25)
    devotion = 0.15*results[:,1] + 0.10*results[:,3] + eth_boost + age_rel + 2.0 + rng.normal(0, 0.4, n)
    df["religious_devotion"] = np.clip(np.round(devotion, 2), 1.0, 5.0)

    logger.info(f"Big Five means: O={results[:,0].mean():.2f} C={results[:,1].mean():.2f} "
                f"E={results[:,2].mean():.2f} A={results[:,3].mean():.2f} N={results[:,4].mean():.2f}")
    return df


# ============================================================
# SUPABASE UPLOAD
# ============================================================

def batch_upsert(supabase, table, records, batch_size=500):
    total = len(records)
    batches = math.ceil(total / batch_size)
    logger.info(f"Upserting {total:,} records to '{table}' in {batches} batches")

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
                if (i + 1) % 100 == 0 or i == batches - 1:
                    logger.info(f"  {table} batch {i+1}/{batches}: {success:,}/{total:,}")
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                logger.error(f"  Batch {i+1} failed: {e}")
                for j in range(0, len(batch), 20):
                    mini = batch[j:j+20]
                    try:
                        supabase.table(table).upsert(mini).execute()
                        success += len(mini)
                    except Exception as e2:
                        errors += len(mini)
                        logger.error(f"  Mini-batch failed: {e2}")
                    time.sleep(0.5)

    logger.info(f"  {table} done: {success:,} success, {errors:,} errors")
    return success, errors


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Seed 172K agents (V4 — split tables)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-profiles", action="store_true", help="Skip uploading agent_profiles")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    # STEP 1: Load NVIDIA parquet
    logger.info(f"Loading NVIDIA parquet from {PARQUET_PATH}")
    df = pd.read_parquet(PARQUET_PATH)
    logger.info(f"Loaded {len(df):,} adults, {len(df.columns)} columns")

    if args.limit > 0:
        df = df.head(args.limit)
        logger.info(f"Limited to {len(df):,} rows")

    # STEP 2: Map fields
    logger.info("Mapping fields...")
    df["agent_id"] = df["uuid"]
    df["gender"] = df["sex"].map(GENDER_MAP)
    df["education_level"] = df["education_level"].map(EDU_MAP).fillna("Secondary")
    df["marital_status"] = df["marital_status"].map(MARITAL_MAP).fillna("Single")
    df["planning_area"] = df["planning_area"].map(
        lambda x: AREA_MAP.get(x, x) if x not in KNOWN_AREAS else x
    )
    df.loc[~df["planning_area"].isin(KNOWN_AREAS | {"Central Area"}), "planning_area"] = "Others"

    # STEP 3: Generate children
    child_df = generate_children(df, rng)

    # STEP 4: Merge
    df["data_source"] = "nvidia_nemotron"
    df = pd.concat([df, child_df], ignore_index=True)
    logger.info(f"Total population: {len(df):,}")

    # STEP 5: Common fields
    df["age_group"] = pd.cut(df["age"], bins=AGE_BINS, labels=AGE_LABELS, right=False, include_lowest=True).astype(str)
    df["life_phase"] = df.apply(lambda r: assign_life_phase(r["age"], r["gender"]), axis=1)

    # STEP 6: CPT augmentation
    is_adult = df["data_source"] == "nvidia_nemotron"
    adult_idx = df[is_adult].index

    logger.info("Augmenting ethnicity...")
    eth_vals = rng.choice(["Chinese","Malay","Indian","Others"], size=len(adult_idx), p=[0.739,0.135,0.090,0.036])
    df.loc[adult_idx, "ethnicity"] = eth_vals

    logger.info("Augmenting residency...")
    df_a = df.loc[is_adult].copy()
    df_a = augment_residency(df_a, rng)
    df.loc[is_adult, "residency_status"] = df_a["residency_status"]

    logger.info("Augmenting income...")
    df_a = df.loc[is_adult].copy()
    df_a = augment_income(df_a, rng)
    df.loc[is_adult, "income_band"] = df_a["income_band"]
    df.loc[is_adult, "monthly_income"] = df_a["monthly_income"]

    logger.info("Augmenting housing...")
    df = augment_housing(df, rng)

    logger.info("Augmenting health...")
    df_a = df.loc[is_adult].copy()
    df_a = augment_health(df_a, rng)
    df.loc[is_adult, "health_status"] = df_a["health_status"]

    logger.info("Augmenting occupation...")
    df_a = df.loc[is_adult].copy()
    df_a = augment_occupation(df_a, rng)
    df.loc[is_adult, "occupation"] = df_a["occupation"]

    # STEP 7: Personality
    df = augment_personality(df, rng)
    df["is_alive"] = True

    # STEP 8: Validation
    n_adults = (df["data_source"] == "nvidia_nemotron").sum()
    n_children = (df["data_source"] == "synthetic").sum()
    logger.info(f"\n=== VALIDATION ===")
    logger.info(f"Total: {len(df):,} (adults: {n_adults:,}, children: {n_children:,})")
    logger.info(f"Gender: {df['gender'].value_counts().to_dict()}")
    logger.info(f"Ethnicity: {df['ethnicity'].value_counts().to_dict()}")

    if args.dry_run:
        logger.info("DRY RUN — skipping upload")
        return

    # STEP 9: Upload to NEW Supabase (V4 split tables)
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # V4: agents table (demographics only)
    AGENT_COLUMNS = [
        "agent_id", "age", "age_group", "gender", "marital_status",
        "education_level", "occupation", "industry", "planning_area",
        "ethnicity", "residency_status", "monthly_income", "income_band",
        "housing_type", "health_status",
        "big5_o", "big5_c", "big5_e", "big5_a", "big5_n",
        "risk_appetite", "political_leaning", "social_trust", "religious_devotion",
        "life_phase", "is_alive", "data_source",
    ]

    # V4: agent_profiles table (narrative text)
    PROFILE_COLUMNS = [
        "agent_id", "persona", "professional_persona", "cultural_background",
        "sports_persona", "arts_persona", "travel_persona",
        "culinary_persona", "hobbies_and_interests",
        "career_goals_and_ambitions", "skills_and_expertise",
    ]

    INT_COLS = ["age", "monthly_income"]
    for col in INT_COLS:
        df[col] = df[col].fillna(0).astype(int)

    def make_records(columns):
        records = []
        for _, row in df.iterrows():
            rec = {}
            for col in columns:
                val = row.get(col, None)
                if pd.isna(val): val = None
                elif isinstance(val, (np.integer, np.int64)): val = int(val)
                elif isinstance(val, (np.floating, np.float64)):
                    val = int(val) if col in INT_COLS else float(val)
                elif isinstance(val, np.bool_): val = bool(val)
                rec[col] = val
            records.append(rec)
        return records

    # Upload agents (demographics)
    logger.info("Preparing agent records...")
    agent_records = make_records(AGENT_COLUMNS)
    logger.info(f"Uploading {len(agent_records):,} agents...")
    s1, e1 = batch_upsert(supabase, "agents", agent_records, batch_size=500)

    # Upload profiles (narratives) — only for adults with NVIDIA data
    if not args.skip_profiles:
        logger.info("Preparing profile records (adults with narratives)...")
        # Only upload profiles for agents that have narrative data
        has_persona = df["persona"].fillna("").str.len() > 0
        profile_df = df[has_persona]
        profile_records = []
        for _, row in profile_df.iterrows():
            rec = {}
            for col in PROFILE_COLUMNS:
                val = row.get(col, None)
                if pd.isna(val): val = None
                rec[col] = val
            profile_records.append(rec)
        logger.info(f"Uploading {len(profile_records):,} profiles...")
        s2, e2 = batch_upsert(supabase, "agent_profiles", profile_records, batch_size=200)
    else:
        s2, e2 = 0, 0
        logger.info("Skipping profiles upload (--skip-profiles)")

    print("\n" + "=" * 60)
    print("V4 SEED COMPLETE")
    print("=" * 60)
    print(f"Agents:   {s1:,} in agents table")
    print(f"Profiles: {s2:,} in agent_profiles table")
    print(f"Database: {SUPABASE_URL}")


if __name__ == "__main__":
    main()
