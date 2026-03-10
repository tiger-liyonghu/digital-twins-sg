"""
Script 02: Synthesize 20,000 agents for Singapore Digital Twin.

Pipeline:
1. Load Census cross-tabulation data (or use built-in SG distributions)
2. Run IPF to generate base demographic records
3. Enrich with education, income, housing correlations
4. Initialize Big Five personality profiles
5. Derive attitudes from personality + demographics
6. Build household structures
7. Assign life phases and agent types
8. Verify k-anonymity (k>=5)
9. Export to CSV / Supabase

Usage:
    python scripts/02_synthesize_population.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import logging
import json
from pathlib import Path

from engine.synthesis.ipf import IPFEngine, TARGET_AGENTS
from engine.synthesis.personality_init import PersonalityInitializer, AttitudeInitializer
from engine.synthesis.household_builder import HouseholdBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# Singapore Census 2020 Distributions (built-in fallback)
# Used when CSV files from data.gov.sg are not available
# ============================================================

# Age distribution (5-year bands, Census 2020 resident population)
AGE_DIST = {
    "0-4": 0.042, "5-9": 0.046, "10-14": 0.049, "15-19": 0.053,
    "20-24": 0.067, "25-29": 0.075, "30-34": 0.082, "35-39": 0.083,
    "40-44": 0.078, "45-49": 0.076, "50-54": 0.072, "55-59": 0.069,
    "60-64": 0.063, "65-69": 0.051, "70-74": 0.039, "75-79": 0.024,
    "80-84": 0.016, "85-89": 0.009, "90-94": 0.004, "95-99": 0.001,
    "100": 0.0005,
}

# Gender split
GENDER_DIST = {"M": 0.49, "F": 0.51}

# Ethnicity (resident population)
ETHNICITY_DIST = {
    "Chinese": 0.742, "Malay": 0.134, "Indian": 0.090, "Others": 0.034,
}

# Residency status (total population 5.8M)
RESIDENCY_DIST = {
    "Citizen": 0.591,   # 3.43M
    "PR": 0.092,        # 0.53M
    "EP": 0.030,        # 0.17M
    "SP": 0.031,        # 0.18M
    "WP": 0.170,        # 0.99M (includes construction, marine, process)
    "FDW": 0.044,       # 0.25M
    "DP": 0.021,        # 0.12M (Dependant's Pass)
    "STP": 0.021,       # 0.12M (Student, LTVP, etc.)
}

# Education (residents 25+)
EDUCATION_DIST = {
    "No_Formal": 0.08,
    "Primary": 0.12,
    "Secondary": 0.16,
    "Post_Secondary": 0.12,
    "Polytechnic": 0.12,
    "University": 0.32,
    "Postgraduate": 0.08,
}

# Housing type (resident households)
HOUSING_DIST = {
    "HDB_1_2": 0.058,
    "HDB_3": 0.188,
    "HDB_4": 0.310,
    "HDB_5_EC": 0.186,
    "Condo": 0.161,
    "Landed": 0.097,
}

# Marital status (residents 15+)
MARITAL_DIST = {
    "Single": 0.35,
    "Married": 0.52,
    "Divorced": 0.06,
    "Widowed": 0.07,
}

# Monthly income distribution (employed residents, SGD)
INCOME_BANDS = [
    (0, 0, 0.05),        # No income (students, etc.)
    (1, 1999, 0.12),
    (2000, 3499, 0.18),
    (3500, 4999, 0.16),
    (5000, 6999, 0.15),
    (7000, 9999, 0.14),
    (10000, 14999, 0.10),
    (15000, 24999, 0.06),
    (25000, 50000, 0.04),
]

# Planning areas (top 20 by population, simplified)
PLANNING_AREAS = {
    "Bedok": 0.053, "Tampines": 0.052, "Jurong West": 0.051,
    "Sengkang": 0.050, "Woodlands": 0.049, "Hougang": 0.045,
    "Yishun": 0.043, "Choa Chu Kang": 0.037, "Punggol": 0.036,
    "Bukit Merah": 0.032, "Bukit Batok": 0.031, "Toa Payoh": 0.030,
    "Ang Mo Kio": 0.029, "Queenstown": 0.028, "Clementi": 0.027,
    "Kallang": 0.026, "Pasir Ris": 0.025, "Bishan": 0.024,
    "Geylang": 0.023, "Serangoon": 0.022, "Bukit Panjang": 0.021,
    "Sembawang": 0.020, "Marine Parade": 0.019, "Bukit Timah": 0.018,
    "Novena": 0.017, "Central Area": 0.016, "Tanglin": 0.015,
    "Others": 0.161,
}

# Commute mode (resident workers)
COMMUTE_DIST = {
    "MRT": 0.32, "Bus": 0.22, "Drive": 0.20, "Walk": 0.08,
    "Taxi/PHV": 0.06, "Cycle": 0.02, "WFH": 0.08, "Other": 0.02,
}


def _age_from_band(band: str, rng: np.random.Generator) -> int:
    """Convert age band string to specific age."""
    if band == "100":
        return 100
    parts = band.split("-")
    lo, hi = int(parts[0]), int(parts[1])
    return int(rng.integers(lo, hi + 1))


def _sample_income(age: int, education: str, rng: np.random.Generator) -> int:
    """Sample monthly income based on age and education."""
    if age < 15:
        return 0
    if age < 22 and education in ("No_Formal", "Primary", "Secondary"):
        return 0

    # Education premium
    edu_multiplier = {
        "No_Formal": 0.5, "Primary": 0.6, "Secondary": 0.7,
        "Post_Secondary": 0.85, "Polytechnic": 1.0,
        "University": 1.4, "Postgraduate": 1.8,
    }.get(education, 1.0)

    # Age premium (peak at 45-54)
    if age < 25:
        age_mult = 0.5
    elif age < 35:
        age_mult = 0.85
    elif age < 45:
        age_mult = 1.0
    elif age < 55:
        age_mult = 1.05
    elif age < 63:
        age_mult = 0.90
    elif age < 70:
        age_mult = 0.50  # re-employment
    else:
        age_mult = 0.0   # retired

    if age_mult == 0.0:
        return 0

    # Sample from income bands with education/age weighting
    weights = []
    for lo, hi, base_prob in INCOME_BANDS:
        mid = (lo + hi) / 2
        # Shift distribution based on education/age
        adjusted = base_prob * np.exp(-0.0001 * (mid - 5000 * edu_multiplier * age_mult) ** 2 / 10000)
        weights.append(max(adjusted, 0.001))

    weights = np.array(weights)
    weights /= weights.sum()
    band_idx = rng.choice(len(INCOME_BANDS), p=weights)
    lo, hi, _ = INCOME_BANDS[band_idx]
    if hi == 0:
        return 0
    return int(rng.integers(lo, hi + 1))


def build_cross_tab_age_sex() -> pd.DataFrame:
    """Build age × sex cross-tabulation from distributions."""
    records = []
    for age_band, age_prob in AGE_DIST.items():
        for gender, gender_prob in GENDER_DIST.items():
            count = age_prob * gender_prob * 1_000_000  # arbitrary scale
            records.append({
                "age_group": age_band,
                "gender": gender,
                "count": count,
            })
    return pd.DataFrame(records)


def build_cross_tab_ethnicity_area() -> pd.DataFrame:
    """Build ethnicity × planning_area cross-tabulation."""
    records = []
    for eth, eth_prob in ETHNICITY_DIST.items():
        for area, area_prob in PLANNING_AREAS.items():
            count = eth_prob * area_prob * 1_000_000
            records.append({
                "ethnicity": eth,
                "planning_area": area,
                "count": count,
            })
    return pd.DataFrame(records)


def build_cross_tab_planning_area() -> pd.DataFrame:
    """Build 1D planning_area marginal constraint.

    The 3D age×sex×area constraint spreads 20K agents across 1,176 cells,
    making the per-area totals noisy.  This explicit 1D marginal forces IPF
    to match the area distribution directly (SRMSE target < 0.20).
    """
    records = []
    for area, area_prob in PLANNING_AREAS.items():
        records.append({
            "planning_area": area,
            "count": area_prob * 1_000_000,
        })
    return pd.DataFrame(records)


def build_cross_tab_age_sex_area() -> pd.DataFrame:
    """Build age × sex × planning_area (primary constraint)."""
    records = []
    for age_band, age_prob in AGE_DIST.items():
        for gender, gender_prob in GENDER_DIST.items():
            for area, area_prob in PLANNING_AREAS.items():
                count = age_prob * gender_prob * area_prob * 1_000_000
                records.append({
                    "age_group": age_band,
                    "gender": gender,
                    "planning_area": area,
                    "count": count,
                })
    return pd.DataFrame(records)


def enrich_agents(agents: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Add education, income, housing, residency, marital status, and other attributes."""
    n = len(agents)

    # Residency status
    res_choices = list(RESIDENCY_DIST.keys())
    res_probs = np.array(list(RESIDENCY_DIST.values()))
    res_probs /= res_probs.sum()
    agents["residency_status"] = rng.choice(res_choices, size=n, p=res_probs)

    # Ethnicity (if not already present from IPF)
    if "ethnicity" not in agents.columns:
        eth_choices = list(ETHNICITY_DIST.keys())
        eth_probs = np.array(list(ETHNICITY_DIST.values()))
        eth_probs /= eth_probs.sum()
        agents["ethnicity"] = rng.choice(eth_choices, size=n, p=eth_probs)

    # Convert age_group to specific age
    if "age_group" in agents.columns and "age" not in agents.columns:
        agents["age"] = agents["age_group"].apply(lambda x: _age_from_band(x, rng))

    # Education (age-dependent)
    edu_choices = list(EDUCATION_DIST.keys())
    edu_base_probs = np.array(list(EDUCATION_DIST.values()))

    education = []
    for _, row in agents.iterrows():
        age = row["age"]
        if age < 7:
            education.append("No_Formal")
        elif age < 13:
            education.append("Primary")
        elif age < 17:
            education.append("Secondary")
        elif age < 21:
            probs = edu_base_probs.copy()
            probs[5] *= 0.3  # less likely to have university yet
            probs[6] *= 0.0  # no postgrad yet
            probs /= probs.sum()
            education.append(rng.choice(edu_choices, p=probs))
        else:
            education.append(rng.choice(edu_choices, p=edu_base_probs))
    agents["education_level"] = education

    # Income
    agents["monthly_income"] = [
        _sample_income(int(row["age"]), row["education_level"], rng)
        for _, row in agents.iterrows()
    ]

    # Marital status (age-dependent)
    marital = []
    for _, row in agents.iterrows():
        age = row["age"]
        if age < 18:
            marital.append("Single")
        elif age < 25:
            marital.append(rng.choice(
                ["Single", "Married"], p=[0.90, 0.10]))
        elif age < 30:
            marital.append(rng.choice(
                ["Single", "Married", "Divorced"], p=[0.55, 0.42, 0.03]))
        elif age < 40:
            marital.append(rng.choice(
                list(MARITAL_DIST.keys()),
                p=[0.25, 0.65, 0.06, 0.04]))
        elif age < 60:
            marital.append(rng.choice(
                list(MARITAL_DIST.keys()),
                p=[0.15, 0.70, 0.07, 0.08]))
        else:
            marital.append(rng.choice(
                list(MARITAL_DIST.keys()),
                p=[0.10, 0.55, 0.05, 0.30]))
    agents["marital_status"] = marital

    # Housing type (correlated with income)
    housing = []
    for _, row in agents.iterrows():
        income = row["monthly_income"]
        if income < 2000:
            probs = [0.15, 0.30, 0.30, 0.15, 0.07, 0.03]
        elif income < 5000:
            probs = [0.05, 0.20, 0.35, 0.25, 0.10, 0.05]
        elif income < 10000:
            probs = [0.02, 0.10, 0.25, 0.30, 0.22, 0.11]
        elif income < 20000:
            probs = [0.01, 0.05, 0.10, 0.25, 0.35, 0.24]
        else:
            probs = [0.01, 0.02, 0.05, 0.12, 0.40, 0.40]
        housing.append(rng.choice(
            list(HOUSING_DIST.keys()), p=probs))
    agents["housing_type"] = housing

    # Planning area (if not from IPF)
    if "planning_area" not in agents.columns:
        area_choices = list(PLANNING_AREAS.keys())
        area_probs = np.array(list(PLANNING_AREAS.values()))
        area_probs /= area_probs.sum()
        agents["planning_area"] = rng.choice(area_choices, size=n, p=area_probs)

    # Commute mode
    comm_choices = list(COMMUTE_DIST.keys())
    comm_probs = np.array(list(COMMUTE_DIST.values()))
    comm_probs /= comm_probs.sum()
    agents["commute_mode"] = rng.choice(comm_choices, size=n, p=comm_probs)

    # Vehicle ownership (correlated with income and housing)
    agents["has_vehicle"] = [
        bool(rng.random() < (0.05 + 0.4 * min(row["monthly_income"] / 15000, 1.0)))
        for _, row in agents.iterrows()
    ]

    # NS status for male citizens/PRs
    ns_status = []
    for _, row in agents.iterrows():
        if row["gender"] != "M" or row["residency_status"] not in ("Citizen", "PR"):
            ns_status.append("Not_Applicable")
        elif row["age"] < 16:
            ns_status.append("Pre_Enlistment")
        elif row["age"] < 20:
            ns_status.append("Serving_NSF")
        elif row["age"] < 40:
            ns_status.append("Active_NSmen")
        else:
            ns_status.append("Completed")
    agents["ns_status"] = ns_status

    # Health status (age-dependent)
    health = []
    for _, row in agents.iterrows():
        age = row["age"]
        if age < 40:
            health.append(rng.choice(
                ["Healthy", "Chronic_Mild"],
                p=[0.92, 0.08]))
        elif age < 60:
            health.append(rng.choice(
                ["Healthy", "Chronic_Mild", "Chronic_Severe"],
                p=[0.70, 0.22, 0.08]))
        elif age < 75:
            health.append(rng.choice(
                ["Healthy", "Chronic_Mild", "Chronic_Severe", "Disabled"],
                p=[0.40, 0.35, 0.18, 0.07]))
        else:
            health.append(rng.choice(
                ["Healthy", "Chronic_Mild", "Chronic_Severe", "Disabled"],
                p=[0.20, 0.30, 0.30, 0.20]))
    agents["health_status"] = health

    return agents


def assign_life_phases(agents: pd.DataFrame) -> pd.DataFrame:
    """Assign life_phase and agent_type based on agent attributes."""
    phases = []
    types = []
    for _, row in agents.iterrows():
        age = row["age"]
        gender = row["gender"]
        ns = row["ns_status"]
        health = row["health_status"]

        # Life phase
        if age <= 6:
            phase = "dependence"
        elif age <= 12:
            phase = "growth"
        elif age <= 16:
            phase = "adolescence"
        elif gender == "M" and ns == "Serving_NSF":
            phase = "ns_service"
        elif age >= 85 or health == "Disabled":
            phase = "end_of_life"
        elif age >= 75 or health == "Chronic_Severe":
            phase = "decline"
        elif age >= 63:
            phase = "retirement_early"
        elif age >= 51:
            phase = "release"
        elif age >= 36:
            phase = "bearing"
        else:
            phase = "establishment"
        phases.append(phase)

        # Agent type
        if age < 13:
            types.append("passive")
        elif age < 15:
            types.append("semi_active")
        else:
            types.append("active")

    agents["life_phase"] = phases
    agents["agent_type"] = types
    return agents


def check_k_anonymity(agents: pd.DataFrame, quasi_ids: list, k: int = 5) -> dict:
    """Check k-anonymity for given quasi-identifiers."""
    grouped = agents.groupby(quasi_ids).size()
    violations = grouped[grouped < k]
    return {
        "k": k,
        "quasi_identifiers": quasi_ids,
        "total_groups": len(grouped),
        "violations": len(violations),
        "min_group_size": int(grouped.min()),
        "passed": len(violations) == 0,
    }


def main():
    seed = 42
    rng = np.random.default_rng(seed)
    output_dir = Path(__file__).parent.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # Step 1: IPF — generate base demographics
    # ============================================================
    logger.info("=" * 60)
    logger.info("Step 1: IPF population synthesis")
    logger.info("=" * 60)

    ipf = IPFEngine(target_n=TARGET_AGENTS, seed=seed)

    # Primary constraint: age × sex × planning area
    ipf.add_constraint(
        name="age_sex_area",
        dimensions=["age_group", "gender", "planning_area"],
        table=build_cross_tab_age_sex_area(),
    )

    # Secondary: ethnicity × area
    ipf.add_constraint(
        name="ethnicity_area",
        dimensions=["ethnicity", "planning_area"],
        table=build_cross_tab_ethnicity_area(),
    )

    # Tertiary: 1D planning_area marginal (fixes sparse 3D cell noise)
    ipf.add_constraint(
        name="planning_area",
        dimensions=["planning_area"],
        table=build_cross_tab_planning_area(),
    )

    agents = ipf.fit(max_iterations=15, tolerance=0.02)

    # Verify IPF fit
    verification = ipf.verify()
    for name, stats in verification.items():
        logger.info(f"  {name}: max_dev={stats['max_deviation']:.4f}, "
                    f"mean_dev={stats['mean_deviation']:.4f}")

    # ============================================================
    # Step 2: Enrich with correlated attributes
    # ============================================================
    logger.info("=" * 60)
    logger.info("Step 2: Enriching with education, income, housing...")
    logger.info("=" * 60)

    agents = enrich_agents(agents, rng)

    # ============================================================
    # Step 3: Personality (Big Five)
    # ============================================================
    logger.info("=" * 60)
    logger.info("Step 3: Big Five personality initialization")
    logger.info("=" * 60)

    personality = PersonalityInitializer(seed=seed)
    agents = personality.generate_batch(agents)

    # ============================================================
    # Step 4: Attitudes
    # ============================================================
    logger.info("=" * 60)
    logger.info("Step 4: Attitude derivation")
    logger.info("=" * 60)

    attitudes = AttitudeInitializer(seed=seed)
    agents = attitudes.generate_batch(agents)

    # ============================================================
    # Step 5: Life phases
    # ============================================================
    logger.info("=" * 60)
    logger.info("Step 5: Life phase assignment")
    logger.info("=" * 60)

    agents = assign_life_phases(agents)

    # ============================================================
    # Step 6: Household building
    # ============================================================
    logger.info("=" * 60)
    logger.info("Step 6: Household building")
    logger.info("=" * 60)

    hh_builder = HouseholdBuilder(seed=seed)
    agents = hh_builder.build(agents)

    # ============================================================
    # Step 7: k-Anonymity check
    # ============================================================
    logger.info("=" * 60)
    logger.info("Step 7: k-Anonymity verification")
    logger.info("=" * 60)

    k_checks = [
        check_k_anonymity(agents, ["age_group", "gender", "planning_area"]),
        check_k_anonymity(agents, ["age_group", "gender", "ethnicity"]),
        check_k_anonymity(agents, ["planning_area", "housing_type"]),
    ]
    for check in k_checks:
        status = "PASS" if check["passed"] else "FAIL"
        logger.info(f"  [{status}] {check['quasi_identifiers']}: "
                    f"min_group={check['min_group_size']}, "
                    f"violations={check['violations']}/{check['total_groups']}")

    # ============================================================
    # Step 8: Export
    # ============================================================
    logger.info("=" * 60)
    logger.info("Step 8: Export")
    logger.info("=" * 60)

    # Reorder columns
    col_order = [
        "agent_id", "age", "age_group", "gender", "ethnicity", "residency_status",
        "planning_area", "education_level", "monthly_income", "marital_status",
        "housing_type", "commute_mode", "has_vehicle", "ns_status", "health_status",
        "life_phase", "agent_type", "household_id", "household_role",
        "big5_o", "big5_c", "big5_e", "big5_a", "big5_n",
        "risk_appetite", "political_leaning", "social_trust", "religious_devotion",
    ]
    existing_cols = [c for c in col_order if c in agents.columns]
    extra_cols = [c for c in agents.columns if c not in col_order]
    agents = agents[existing_cols + extra_cols]

    # Save CSV
    csv_path = output_dir / "agents_20k.csv"
    agents.to_csv(csv_path, index=False)
    logger.info(f"Saved {len(agents)} agents to {csv_path}")

    # Save summary stats
    summary = {
        "total_agents": len(agents),
        "age_range": [int(agents["age"].min()), int(agents["age"].max())],
        "gender_dist": agents["gender"].value_counts(normalize=True).to_dict(),
        "ethnicity_dist": agents["ethnicity"].value_counts(normalize=True).round(3).to_dict(),
        "residency_dist": agents["residency_status"].value_counts(normalize=True).round(3).to_dict(),
        "life_phase_dist": agents["life_phase"].value_counts(normalize=True).round(3).to_dict(),
        "housing_dist": agents["housing_type"].value_counts(normalize=True).round(3).to_dict(),
        "mean_income": float(agents["monthly_income"].mean()),
        "median_income": float(agents["monthly_income"].median()),
        "households": int(agents["household_id"].nunique()),
        "k_anonymity": k_checks,
    }
    summary_path = output_dir / "synthesis_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"Saved summary to {summary_path}")

    # Print quick summary
    print("\n" + "=" * 50)
    print("SYNTHESIS COMPLETE")
    print("=" * 50)
    print(f"Agents: {len(agents)}")
    print(f"Households: {agents['household_id'].nunique()}")
    print(f"Age range: {agents['age'].min()} - {agents['age'].max()}")
    print(f"Mean income: ${agents['monthly_income'].mean():,.0f}")
    print(f"Life phases: {agents['life_phase'].value_counts().to_dict()}")
    print(f"\nOutput: {csv_path}")


if __name__ == "__main__":
    main()
