"""
Singapore-specific joint distributions and conditional probability tables.

All distributions are derived from GHS 2025 (General Household Survey),
Population Trends 2025, and Department of Statistics Singapore (SingStat)
publications. Where exact cross-tabulations are unavailable, we estimate
conditional probabilities from published marginals + known correlations.

Data sources:
- Population Trends 2025 (SingStat, released Sep 2025)
- General Household Survey 2025 (SingStat, released Feb 2026)
- Key Household Income Trends 2025 (SingStat, released Feb 2026)
- MOM Labour Force Survey 2025 (median income $5,775/month)
- HDB Key Statistics 2024/2025
- Population in Brief 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from engine.synthesis.math_core import (
    DemingStephanIPF,
    ConditionalProbabilityEngine,
    GaussianCopula,
    controlled_rounding,
)
import logging

logger = logging.getLogger(__name__)

# ============================================================
# MARGINAL DISTRIBUTIONS (GHS 2025 / Population Trends 2025)
# ============================================================

# 21 age groups × proportion
# Source: Population Trends 2025 (SingStat), adjusted for RESIDENT population
# (~4.20M). Total pop (6.11M) includes ~1.91M non-residents who skew younger
# (work permit holders 20-40). Resident median age = 43.2 years.
# Key shift vs Census 2020: 65+ rose from ~15.2% to 18.8%
AGE_MARGINAL = np.array([
    0.038, 0.038, 0.038, 0.044,  # 0-19  (children shrinking)
    0.056, 0.067, 0.077, 0.071,  # 20-39 (resident: less dominant than total pop)
    0.076, 0.073, 0.069, 0.065,  # 40-59 (larger share in resident pop)
    0.064, 0.058, 0.046, 0.033,  # 60-79 (elderly growing significantly)
    0.019, 0.011, 0.005, 0.002, 0.001,  # 80-100
])
AGE_LABELS = [
    "0-4", "5-9", "10-14", "15-19",
    "20-24", "25-29", "30-34", "35-39",
    "40-44", "45-49", "50-54", "55-59",
    "60-64", "65-69", "70-74", "75-79",
    "80-84", "85-89", "90-94", "95-99", "100",
]

# 2 genders × proportion
# Source: Population Trends 2025 — sex ratio 947 males per 1000 females
GENDER_MARGINAL = np.array([0.486, 0.514])
GENDER_LABELS = ["M", "F"]

# 4 ethnicities × proportion (resident population)
# Source: Population Trends 2025 — Chinese 73.9%, Malay 13.5%, Indian 9.0%, Others 3.5%
ETHNICITY_MARGINAL = np.array([0.739, 0.135, 0.090, 0.035])
ETHNICITY_LABELS = ["Chinese", "Malay", "Indian", "Others"]

# 8 residency statuses × proportion (total 6.11M, residents 4.20M, non-res 1.91M)
# Source: Population in Brief 2025 — citizens 3.66M, PR 0.54M, non-res 1.91M
RESIDENCY_MARGINAL = np.array([0.599, 0.088, 0.032, 0.033, 0.162, 0.042, 0.022, 0.022])
RESIDENCY_LABELS = ["Citizen", "PR", "EP", "SP", "WP", "FDW", "DP", "STP"]

# 28 planning areas × proportion
AREA_MARGINAL = np.array([
    0.053, 0.052, 0.051, 0.050, 0.049, 0.045, 0.043, 0.037,
    0.036, 0.032, 0.031, 0.030, 0.029, 0.028, 0.027, 0.026,
    0.025, 0.024, 0.023, 0.022, 0.021, 0.020, 0.019, 0.018,
    0.017, 0.016, 0.015, 0.161,
])
AREA_LABELS = [
    "Bedok", "Tampines", "Jurong West", "Sengkang", "Woodlands",
    "Hougang", "Yishun", "Choa Chu Kang", "Punggol", "Bukit Merah",
    "Bukit Batok", "Toa Payoh", "Ang Mo Kio", "Queenstown", "Clementi",
    "Kallang", "Pasir Ris", "Bishan", "Geylang", "Serangoon",
    "Bukit Panjang", "Sembawang", "Marine Parade", "Bukit Timah",
    "Novena", "Central Area", "Tanglin", "Others",
]


# ============================================================
# CONDITIONAL PROBABILITY TABLES
# ============================================================

def build_education_cpt() -> Dict[tuple, Dict[str, float]]:
    """
    P(education | age_group)

    Age strongly determines education distribution:
    - Children: deterministic (No_Formal, Primary, Secondary by age)
    - Adults: GHS 2025 education attainment by age group
    - Key shift: Degree+ among 25+ rose from 33% (2020) to 37.3% (2025)
    """
    edu_levels = [
        "No_Formal", "Primary", "Secondary", "Post_Secondary",
        "Polytechnic", "University", "Postgraduate",
    ]

    cpt = {}

    # Children: deterministic by age
    cpt[("0-4",)]   = {"No_Formal": 1.0, "Primary": 0.0, "Secondary": 0.0,
                        "Post_Secondary": 0.0, "Polytechnic": 0.0,
                        "University": 0.0, "Postgraduate": 0.0}
    cpt[("5-9",)]   = {"No_Formal": 0.15, "Primary": 0.85, "Secondary": 0.0,
                        "Post_Secondary": 0.0, "Polytechnic": 0.0,
                        "University": 0.0, "Postgraduate": 0.0}
    cpt[("10-14",)] = {"No_Formal": 0.0, "Primary": 0.40, "Secondary": 0.60,
                        "Post_Secondary": 0.0, "Polytechnic": 0.0,
                        "University": 0.0, "Postgraduate": 0.0}
    cpt[("15-19",)] = {"No_Formal": 0.0, "Primary": 0.0, "Secondary": 0.45,
                        "Post_Secondary": 0.35, "Polytechnic": 0.15,
                        "University": 0.05, "Postgraduate": 0.0}

    # ── Calibrated 25+ education CPT (v2) ───────────────────────────
    # Scaled from v1 CPT using multiplicative factors to match
    # GHS 2025 25+ marginals when weighted by age distribution.
    # Key fix: Post_Secondary was severely underrepresented (-45%),
    # University+PG overrepresented (+19%). Scale factors:
    # NF×1.188, Pri×0.968, Sec×0.962, PS×2.105, Poly×1.146, Uni+PG×0.825
    cpt[("20-24",)] = {"No_Formal": 0.01, "Primary": 0.02, "Secondary": 0.10,
                        "Post_Secondary": 0.20, "Polytechnic": 0.25,
                        "University": 0.40, "Postgraduate": 0.02}
    cpt[("25-29",)] = {"No_Formal": 0.011, "Primary": 0.018, "Secondary": 0.073,
                        "Post_Secondary": 0.240, "Polytechnic": 0.186,
                        "University": 0.378, "Postgraduate": 0.094}
    cpt[("30-34",)] = {"No_Formal": 0.011, "Primary": 0.028, "Secondary": 0.083,
                        "Post_Secondary": 0.241, "Polytechnic": 0.164,
                        "University": 0.355, "Postgraduate": 0.118}
    cpt[("35-39",)] = {"No_Formal": 0.011, "Primary": 0.037, "Secondary": 0.101,
                        "Post_Secondary": 0.241, "Polytechnic": 0.153,
                        "University": 0.339, "Postgraduate": 0.118}

    # Middle-aged
    cpt[("40-44",)] = {"No_Formal": 0.022, "Primary": 0.045, "Secondary": 0.144,
                        "Post_Secondary": 0.255, "Polytechnic": 0.150,
                        "University": 0.292, "Postgraduate": 0.092}
    cpt[("45-49",)] = {"No_Formal": 0.033, "Primary": 0.071, "Secondary": 0.176,
                        "Post_Secondary": 0.270, "Polytechnic": 0.126,
                        "University": 0.249, "Postgraduate": 0.075}
    cpt[("50-54",)] = {"No_Formal": 0.044, "Primary": 0.089, "Secondary": 0.196,
                        "Post_Secondary": 0.253, "Polytechnic": 0.106,
                        "University": 0.228, "Postgraduate": 0.084}
    cpt[("55-59",)] = {"No_Formal": 0.055, "Primary": 0.108, "Secondary": 0.206,
                        "Post_Secondary": 0.235, "Polytechnic": 0.096,
                        "University": 0.223, "Postgraduate": 0.077}

    # Older adults
    cpt[("60-64",)] = {"No_Formal": 0.111, "Primary": 0.181, "Secondary": 0.225,
                        "Post_Secondary": 0.196, "Polytechnic": 0.064,
                        "University": 0.169, "Postgraduate": 0.054}
    cpt[("65-69",)] = {"No_Formal": 0.168, "Primary": 0.228, "Secondary": 0.199,
                        "Post_Secondary": 0.158, "Polytechnic": 0.054,
                        "University": 0.146, "Postgraduate": 0.047}
    cpt[("70-74",)] = {"No_Formal": 0.223, "Primary": 0.254, "Secondary": 0.180,
                        "Post_Secondary": 0.138, "Polytechnic": 0.043,
                        "University": 0.123, "Postgraduate": 0.039}
    cpt[("75-79",)] = {"No_Formal": 0.311, "Primary": 0.272, "Secondary": 0.162,
                        "Post_Secondary": 0.099, "Polytechnic": 0.032,
                        "University": 0.093, "Postgraduate": 0.031}

    # Elderly
    for age_group in ["80-84", "85-89", "90-94", "95-99", "100"]:
        cpt[(age_group,)] = {
            "No_Formal": 0.383, "Primary": 0.267, "Secondary": 0.133,
            "Post_Secondary": 0.097, "Polytechnic": 0.021,
            "University": 0.076, "Postgraduate": 0.023}

    return cpt


def build_income_cpt() -> Dict[tuple, Dict[str, float]]:
    """
    P(income_band | education, age_group)

    Income strongly depends on education and age.
    Derived from MOM Labour Force Survey 2025 + Key Household Income Trends 2025.
    Target: Median monthly income $5,000 (excl employer CPF, take-home basis).
    Ref: MOM 2025 full-time employed residents median = $5,000 excl CPF.

    Income bands (monthly, SGD):
    0, 1-1999, 2000-3499, 3500-4999, 5000-6999,
    7000-9999, 10000-14999, 15000+
    """
    bands = ["0", "1-1999", "2000-3499", "3500-4999",
             "5000-6999", "7000-9999", "10000-14999", "15000+"]

    cpt = {}

    # Education × broad age → income distribution
    # Calibrated to $5,000 median (excl CPF). Growth ~7% vs Census 2020 ($4,680).
    # University 20-24 (fresh grads, NSmen, part-time)
    cpt[("University", "20-24")] = {
        "0": 0.30, "1-1999": 0.15, "2000-3499": 0.20,
        "3500-4999": 0.18, "5000-6999": 0.10,
        "7000-9999": 0.04, "10000-14999": 0.02, "15000+": 0.01}

    # University graduates, working age (young)
    for age in ["25-29", "30-34", "35-39"]:
        cpt[("University", age)] = {
            "0": 0.02, "1-1999": 0.03, "2000-3499": 0.10,
            "3500-4999": 0.22, "5000-6999": 0.28,
            "7000-9999": 0.18, "10000-14999": 0.11, "15000+": 0.06}

    # University graduates, peak earning (40-54)
    # Calibrated down: MOM 2025 median $5,000 incl all education levels
    for age in ["40-44", "45-49", "50-54"]:
        cpt[("University", age)] = {
            "0": 0.03, "1-1999": 0.03, "2000-3499": 0.07,
            "3500-4999": 0.15, "5000-6999": 0.24,
            "7000-9999": 0.22, "10000-14999": 0.15, "15000+": 0.11}

    # Postgrad 20-24 (rare — masters students, part-time)
    cpt[("Postgraduate", "20-24")] = {
        "0": 0.40, "1-1999": 0.15, "2000-3499": 0.15,
        "3500-4999": 0.15, "5000-6999": 0.08,
        "7000-9999": 0.04, "10000-14999": 0.02, "15000+": 0.01}

    # Postgrad: premium over university
    for age in ["25-29", "30-34", "35-39"]:
        cpt[("Postgraduate", age)] = {
            "0": 0.02, "1-1999": 0.01, "2000-3499": 0.05,
            "3500-4999": 0.12, "5000-6999": 0.22,
            "7000-9999": 0.24, "10000-14999": 0.18, "15000+": 0.16}

    for age in ["40-44", "45-49", "50-54"]:
        cpt[("Postgraduate", age)] = {
            "0": 0.03, "1-1999": 0.02, "2000-3499": 0.04,
            "3500-4999": 0.08, "5000-6999": 0.17,
            "7000-9999": 0.22, "10000-14999": 0.22, "15000+": 0.22}

    # Polytechnic graduates
    for age in ["20-24", "25-29", "30-34", "35-39"]:
        cpt[("Polytechnic", age)] = {
            "0": 0.04, "1-1999": 0.06, "2000-3499": 0.20,
            "3500-4999": 0.28, "5000-6999": 0.24,
            "7000-9999": 0.10, "10000-14999": 0.05, "15000+": 0.03}

    for age in ["40-44", "45-49", "50-54"]:
        cpt[("Polytechnic", age)] = {
            "0": 0.03, "1-1999": 0.04, "2000-3499": 0.12,
            "3500-4999": 0.22, "5000-6999": 0.26,
            "7000-9999": 0.17, "10000-14999": 0.10, "15000+": 0.06}

    # Secondary education
    for age in ["20-24", "25-29", "30-34", "35-39"]:
        cpt[("Secondary", age)] = {
            "0": 0.06, "1-1999": 0.14, "2000-3499": 0.28,
            "3500-4999": 0.24, "5000-6999": 0.14,
            "7000-9999": 0.08, "10000-14999": 0.04, "15000+": 0.02}

    for age in ["40-44", "45-49", "50-54"]:
        cpt[("Secondary", age)] = {
            "0": 0.05, "1-1999": 0.12, "2000-3499": 0.22,
            "3500-4999": 0.24, "5000-6999": 0.18,
            "7000-9999": 0.10, "10000-14999": 0.05, "15000+": 0.04}

    # Primary / No formal: lower income range
    for edu in ["Primary", "No_Formal"]:
        for age in ["20-24", "25-29", "30-34", "35-39",
                     "40-44", "45-49", "50-54", "55-59"]:
            cpt[(edu, age)] = {
                "0": 0.10, "1-1999": 0.28, "2000-3499": 0.30,
                "3500-4999": 0.16, "5000-6999": 0.08,
                "7000-9999": 0.04, "10000-14999": 0.03, "15000+": 0.01}

    # Post-secondary (ITE, A-Level)
    for age in ["20-24", "25-29", "30-34", "35-39"]:
        cpt[("Post_Secondary", age)] = {
            "0": 0.05, "1-1999": 0.10, "2000-3499": 0.26,
            "3500-4999": 0.26, "5000-6999": 0.18,
            "7000-9999": 0.08, "10000-14999": 0.04, "15000+": 0.03}

    # Post-secondary, middle-aged (40-54): experienced ITE/A-Level workers
    for age in ["40-44", "45-49", "50-54"]:
        cpt[("Post_Secondary", age)] = {
            "0": 0.04, "1-1999": 0.08, "2000-3499": 0.20,
            "3500-4999": 0.26, "5000-6999": 0.22,
            "7000-9999": 0.10, "10000-14999": 0.06, "15000+": 0.04}

    # Retired (60+): mostly zero income
    for edu in ["No_Formal", "Primary", "Secondary", "Post_Secondary",
                "Polytechnic", "University", "Postgraduate"]:
        for age in ["60-64", "65-69", "70-74", "75-79",
                     "80-84", "85-89", "90-94", "95-99", "100"]:
            if age == "60-64":
                cpt[(edu, age)] = {
                    "0": 0.30, "1-1999": 0.20, "2000-3499": 0.18,
                    "3500-4999": 0.12, "5000-6999": 0.08,
                    "7000-9999": 0.05, "10000-14999": 0.04, "15000+": 0.03}
            elif age == "65-69":
                cpt[(edu, age)] = {
                    "0": 0.50, "1-1999": 0.20, "2000-3499": 0.12,
                    "3500-4999": 0.07, "5000-6999": 0.04,
                    "7000-9999": 0.03, "10000-14999": 0.02, "15000+": 0.02}
            else:
                cpt[(edu, age)] = {
                    "0": 0.75, "1-1999": 0.12, "2000-3499": 0.06,
                    "3500-4999": 0.03, "5000-6999": 0.02,
                    "7000-9999": 0.01, "10000-14999": 0.005, "15000+": 0.005}

    # Youth: mostly zero (students)
    for edu in ["No_Formal", "Primary", "Secondary", "Post_Secondary",
                "Polytechnic", "University", "Postgraduate"]:
        for age in ["0-4", "5-9", "10-14", "15-19"]:
            cpt[(edu, age)] = {
                "0": 0.95, "1-1999": 0.04, "2000-3499": 0.01,
                "3500-4999": 0.0, "5000-6999": 0.0,
                "7000-9999": 0.0, "10000-14999": 0.0, "15000+": 0.0}

    # Fill missing combinations with default
    for age in ["55-59"]:
        for edu in ["University", "Postgraduate", "Polytechnic",
                     "Post_Secondary", "Secondary"]:
            if (edu, age) not in cpt:
                cpt[(edu, age)] = {
                    "0": 0.15, "1-1999": 0.10, "2000-3499": 0.15,
                    "3500-4999": 0.15, "5000-6999": 0.15,
                    "7000-9999": 0.12, "10000-14999": 0.10, "15000+": 0.08}

    return cpt


def build_housing_income_cpt() -> Dict[tuple, Dict[str, float]]:
    """
    P(housing_type | income_band)

    Housing type strongly correlates with income.
    From HDB Key Statistics 2025 + GHS 2025 housing data.
    """
    # GHS 2025 overall: HDB ~77.2%, Condo ~17.9%, Landed ~4.7%
    # (shift from Census 2020: HDB 78.7→77.2%, Condo 16→17.9%, Landed 5.3→4.7%)
    # Calibrated so the income-weighted marginal yields ~4.7% Landed, ~77% HDB.
    cpt = {}

    # ── Calibrated housing CPT (v2) ────────────────────────────────
    # GHS 2025 housing breakdown: HDB_1_2 7.3%, HDB_3 16.6%, HDB_4 31.2%,
    # HDB_5_EC 22.1%, Condo 17.9%, Landed 4.7%
    # Scaled from v1 CPT using multiplicative optimization to match
    # GHS 2025 marginals when weighted by income distribution.
    # Key fixes: HDB_1_2 reduced (was +66%), HDB_4 increased (was -14%),
    # Landed/Condo adjusted to match aggregate targets.
    cpt[("0",)] = {
        "HDB_1_2": 0.164, "HDB_3": 0.280, "HDB_4": 0.341,
        "HDB_5_EC": 0.147, "Condo": 0.058, "Landed": 0.010}

    cpt[("1-1999",)] = {
        "HDB_1_2": 0.117, "HDB_3": 0.257, "HDB_4": 0.334,
        "HDB_5_EC": 0.178, "Condo": 0.095, "Landed": 0.019}

    cpt[("2000-3499",)] = {
        "HDB_1_2": 0.056, "HDB_3": 0.194, "HDB_4": 0.367,
        "HDB_5_EC": 0.236, "Condo": 0.119, "Landed": 0.028}

    cpt[("3500-4999",)] = {
        "HDB_1_2": 0.028, "HDB_3": 0.121, "HDB_4": 0.361,
        "HDB_5_EC": 0.274, "Condo": 0.179, "Landed": 0.037}

    cpt[("5000-6999",)] = {
        "HDB_1_2": 0.014, "HDB_3": 0.078, "HDB_4": 0.316,
        "HDB_5_EC": 0.295, "Condo": 0.242, "Landed": 0.055}

    cpt[("7000-9999",)] = {
        "HDB_1_2": 0.007, "HDB_3": 0.044, "HDB_4": 0.230,
        "HDB_5_EC": 0.278, "Condo": 0.347, "Landed": 0.094}

    cpt[("10000-14999",)] = {
        "HDB_1_2": 0.004, "HDB_3": 0.027, "HDB_4": 0.141,
        "HDB_5_EC": 0.241, "Condo": 0.438, "Landed": 0.149}

    cpt[("15000+",)] = {
        "HDB_1_2": 0.004, "HDB_3": 0.018, "HDB_4": 0.096,
        "HDB_5_EC": 0.167, "Condo": 0.494, "Landed": 0.221}

    return cpt


def build_marital_age_cpt() -> Dict[tuple, Dict[str, float]]:
    """
    P(marital_status | age_group, gender)

    From Population Trends 2025 (marital status by age and sex).
    Key shift: married 61.6% (up from 59.5% in 2014), single 29.1%.
    """
    cpt = {}

    # Children: always single
    for age in ["0-4", "5-9", "10-14", "15-19"]:
        for g in ["M", "F"]:
            cpt[(age, g)] = {"Single": 1.0, "Married": 0.0,
                             "Divorced": 0.0, "Widowed": 0.0}

    # Young adults
    cpt[("20-24", "M")] = {"Single": 0.96, "Married": 0.04, "Divorced": 0.0, "Widowed": 0.0}
    cpt[("20-24", "F")] = {"Single": 0.92, "Married": 0.08, "Divorced": 0.0, "Widowed": 0.0}

    # ── Calibrated 25+ CPT (v2) ──────────────────────────────────
    # Scaled from original CPT using multiplicative factors to match
    # GHS 2025 15+ marginals: S=30.4%, M=58.9%, D=5.8%, W=4.9%
    # Key fix: original CPT over-estimated widowhood (~11% vs 4.9%)
    # and under-estimated divorce (~4% vs 5.8%).
    # Scale factors: S×1.228, M×1.125, D×1.421, W×0.430, then renorm.
    cpt[("25-29", "M")] = {"Single": 0.793, "Married": 0.195, "Divorced": 0.012, "Widowed": 0.0}
    cpt[("25-29", "F")] = {"Single": 0.639, "Married": 0.349, "Divorced": 0.012, "Widowed": 0.0}
    cpt[("30-34", "M")] = {"Single": 0.438, "Married": 0.526, "Divorced": 0.036, "Widowed": 0.0}
    cpt[("30-34", "F")] = {"Single": 0.315, "Married": 0.636, "Divorced": 0.049, "Widowed": 0.0}
    cpt[("35-39", "M")] = {"Single": 0.255, "Married": 0.680, "Divorced": 0.061, "Widowed": 0.004}
    cpt[("35-39", "F")] = {"Single": 0.193, "Married": 0.726, "Divorced": 0.074, "Widowed": 0.007}

    # Middle-aged
    cpt[("40-44", "M")] = {"Single": 0.183, "Married": 0.719, "Divorced": 0.087, "Widowed": 0.011}
    cpt[("40-44", "F")] = {"Single": 0.152, "Married": 0.728, "Divorced": 0.101, "Widowed": 0.019}
    cpt[("45-49", "M")] = {"Single": 0.162, "Married": 0.723, "Divorced": 0.100, "Widowed": 0.015}
    cpt[("45-49", "F")] = {"Single": 0.133, "Married": 0.733, "Divorced": 0.103, "Widowed": 0.031}
    cpt[("50-54", "M")] = {"Single": 0.143, "Married": 0.745, "Divorced": 0.089, "Widowed": 0.023}
    cpt[("50-54", "F")] = {"Single": 0.115, "Married": 0.740, "Divorced": 0.093, "Widowed": 0.052}
    cpt[("55-59", "M")] = {"Single": 0.123, "Married": 0.768, "Divorced": 0.078, "Widowed": 0.031}
    cpt[("55-59", "F")] = {"Single": 0.108, "Married": 0.728, "Divorced": 0.084, "Widowed": 0.080}

    # Elderly
    cpt[("60-64", "M")] = {"Single": 0.102, "Married": 0.792, "Divorced": 0.066, "Widowed": 0.040}
    cpt[("60-64", "F")] = {"Single": 0.102, "Married": 0.703, "Divorced": 0.074, "Widowed": 0.121}
    cpt[("65-69", "M")] = {"Single": 0.082, "Married": 0.811, "Divorced": 0.054, "Widowed": 0.053}
    cpt[("65-69", "F")] = {"Single": 0.097, "Married": 0.660, "Divorced": 0.064, "Widowed": 0.179}
    cpt[("70-74", "M")] = {"Single": 0.060, "Married": 0.826, "Divorced": 0.042, "Widowed": 0.072}
    cpt[("70-74", "F")] = {"Single": 0.092, "Married": 0.591, "Divorced": 0.053, "Widowed": 0.264}

    for age in ["75-79", "80-84", "85-89", "90-94", "95-99", "100"]:
        cpt[(age, "M")] = {"Single": 0.051, "Married": 0.802, "Divorced": 0.030, "Widowed": 0.117}
        cpt[(age, "F")] = {"Single": 0.093, "Married": 0.423, "Divorced": 0.043, "Widowed": 0.441}

    return cpt


def build_occupation_cpt() -> Dict[tuple, Dict[str, float]]:
    """
    P(occupation | education_level, age_group)

    Resamples SSOC 2020 major occupation groups for employed adults.
    Source: MOM Occupational Employment Statistics 2024 (resident employed).

    Overall SSOC 2024 targets (employed residents):
      Manager           14.5%
      Professional      24.0%
      Associate Prof    25.2%
      Clerical          10.2%
      Service/Sales     11.5%
      Production         5.0%
      Plant/Machine      5.5%
      Cleaner/Labourer   3.8%
      Agriculture        0.3%

    PMET share = Manager + Professional + Associate Prof = 63.7%

    Conditioning logic:
      - University/Postgrad → high PMET (~85%)
      - Polytechnic → moderate PMET (~55%)
      - Post_Secondary / Secondary / below → low PMET (~25%)
      - Younger adults (25-34) slightly more PMET (educational upgrading)
      - Older adults (55-64) slightly more non-PMET (cohort effect)
    """
    occ_labels = [
        "Manager", "Professional", "Associate Professional",
        "Clerical", "Service and Sales",
        "Production", "Plant and Machine Operator",
        "Cleaner and Labourer", "Agriculture",
    ]

    cpt = {}

    # Calibrated to MOM 2024 SSOC targets given actual employed education
    # distribution (Uni 33.5%, PG 10.6%, Poly 18.4%, PostSec 10.1%,
    # Sec 14%, Pri 8.1%, NoFormal 5.2%).  Target PMET = 63.7%.

    # ----- University: high PMET (~92%) -----
    for age in ["20-24", "25-29", "30-34"]:
        cpt[("University", age)] = {
            "Manager": 0.10, "Professional": 0.50, "Associate Professional": 0.32,
            "Clerical": 0.04, "Service and Sales": 0.02, "Production": 0.005,
            "Plant and Machine Operator": 0.003, "Cleaner and Labourer": 0.001,
            "Agriculture": 0.001}
    for age in ["35-39", "40-44", "45-49"]:
        cpt[("University", age)] = {
            "Manager": 0.25, "Professional": 0.40, "Associate Professional": 0.27,
            "Clerical": 0.04, "Service and Sales": 0.02, "Production": 0.008,
            "Plant and Machine Operator": 0.005, "Cleaner and Labourer": 0.004,
            "Agriculture": 0.003}
    for age in ["50-54", "55-59", "60-64"]:
        cpt[("University", age)] = {
            "Manager": 0.30, "Professional": 0.35, "Associate Professional": 0.26,
            "Clerical": 0.04, "Service and Sales": 0.03, "Production": 0.008,
            "Plant and Machine Operator": 0.005, "Cleaner and Labourer": 0.004,
            "Agriculture": 0.003}

    # ----- Postgraduate: high PMET (~94%) -----
    for age in ["20-24", "25-29", "30-34"]:
        cpt[("Postgraduate", age)] = {
            "Manager": 0.12, "Professional": 0.52, "Associate Professional": 0.30,
            "Clerical": 0.03, "Service and Sales": 0.02, "Production": 0.003,
            "Plant and Machine Operator": 0.003, "Cleaner and Labourer": 0.001,
            "Agriculture": 0.003}
    for age in ["35-39", "40-44", "45-49"]:
        cpt[("Postgraduate", age)] = {
            "Manager": 0.26, "Professional": 0.42, "Associate Professional": 0.26,
            "Clerical": 0.03, "Service and Sales": 0.02, "Production": 0.005,
            "Plant and Machine Operator": 0.003, "Cleaner and Labourer": 0.003,
            "Agriculture": 0.002}
    for age in ["50-54", "55-59", "60-64"]:
        cpt[("Postgraduate", age)] = {
            "Manager": 0.32, "Professional": 0.36, "Associate Professional": 0.25,
            "Clerical": 0.03, "Service and Sales": 0.02, "Production": 0.007,
            "Plant and Machine Operator": 0.005, "Cleaner and Labourer": 0.005,
            "Agriculture": 0.003}

    # ----- Polytechnic: moderate PMET (~65%) -----
    for age in ["20-24", "25-29", "30-34"]:
        cpt[("Polytechnic", age)] = {
            "Manager": 0.07, "Professional": 0.20, "Associate Professional": 0.38,
            "Clerical": 0.12, "Service and Sales": 0.12, "Production": 0.04,
            "Plant and Machine Operator": 0.03, "Cleaner and Labourer": 0.015,
            "Agriculture": 0.005}
    for age in ["35-39", "40-44", "45-49"]:
        cpt[("Polytechnic", age)] = {
            "Manager": 0.15, "Professional": 0.17, "Associate Professional": 0.33,
            "Clerical": 0.12, "Service and Sales": 0.11, "Production": 0.04,
            "Plant and Machine Operator": 0.03, "Cleaner and Labourer": 0.015,
            "Agriculture": 0.005}
    for age in ["50-54", "55-59", "60-64"]:
        cpt[("Polytechnic", age)] = {
            "Manager": 0.18, "Professional": 0.15, "Associate Professional": 0.30,
            "Clerical": 0.12, "Service and Sales": 0.12, "Production": 0.05,
            "Plant and Machine Operator": 0.04, "Cleaner and Labourer": 0.02,
            "Agriculture": 0.005}

    # ----- Post_Secondary (ITE/A-Level): moderate-low PMET (~40%) -----
    for age in ["20-24", "25-29", "30-34"]:
        cpt[("Post_Secondary", age)] = {
            "Manager": 0.05, "Professional": 0.10, "Associate Professional": 0.26,
            "Clerical": 0.15, "Service and Sales": 0.20, "Production": 0.08,
            "Plant and Machine Operator": 0.08, "Cleaner and Labourer": 0.04,
            "Agriculture": 0.005}
    for age in ["35-39", "40-44", "45-49"]:
        cpt[("Post_Secondary", age)] = {
            "Manager": 0.10, "Professional": 0.08, "Associate Professional": 0.23,
            "Clerical": 0.15, "Service and Sales": 0.19, "Production": 0.09,
            "Plant and Machine Operator": 0.08, "Cleaner and Labourer": 0.05,
            "Agriculture": 0.005}
    for age in ["50-54", "55-59", "60-64"]:
        cpt[("Post_Secondary", age)] = {
            "Manager": 0.12, "Professional": 0.07, "Associate Professional": 0.20,
            "Clerical": 0.14, "Service and Sales": 0.18, "Production": 0.10,
            "Plant and Machine Operator": 0.09, "Cleaner and Labourer": 0.06,
            "Agriculture": 0.005}

    # ----- Secondary: low PMET (~30%) -----
    for age in ["20-24", "25-29", "30-34"]:
        cpt[("Secondary", age)] = {
            "Manager": 0.04, "Professional": 0.06, "Associate Professional": 0.21,
            "Clerical": 0.14, "Service and Sales": 0.24, "Production": 0.11,
            "Plant and Machine Operator": 0.11, "Cleaner and Labourer": 0.06,
            "Agriculture": 0.005}
    for age in ["35-39", "40-44", "45-49"]:
        cpt[("Secondary", age)] = {
            "Manager": 0.08, "Professional": 0.05, "Associate Professional": 0.18,
            "Clerical": 0.13, "Service and Sales": 0.23, "Production": 0.11,
            "Plant and Machine Operator": 0.11, "Cleaner and Labourer": 0.08,
            "Agriculture": 0.005}
    for age in ["50-54", "55-59", "60-64"]:
        cpt[("Secondary", age)] = {
            "Manager": 0.09, "Professional": 0.04, "Associate Professional": 0.15,
            "Clerical": 0.12, "Service and Sales": 0.22, "Production": 0.12,
            "Plant and Machine Operator": 0.12, "Cleaner and Labourer": 0.11,
            "Agriculture": 0.005}

    # ----- Primary / No_Formal: very low PMET (~18%) -----
    for edu in ["Primary", "No_Formal"]:
        for age in ["20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]:
            cpt[(edu, age)] = {
                "Manager": 0.03, "Professional": 0.03, "Associate Professional": 0.12,
                "Clerical": 0.09, "Service and Sales": 0.25, "Production": 0.12,
                "Plant and Machine Operator": 0.15, "Cleaner and Labourer": 0.15,
                "Agriculture": 0.005}
        for age in ["50-54", "55-59", "60-64"]:
            cpt[(edu, age)] = {
                "Manager": 0.05, "Professional": 0.02, "Associate Professional": 0.08,
                "Clerical": 0.07, "Service and Sales": 0.21, "Production": 0.12,
                "Plant and Machine Operator": 0.15, "Cleaner and Labourer": 0.24,
                "Agriculture": 0.005}

    return cpt


def build_health_age_cpt() -> Dict[tuple, Dict[str, float]]:
    """
    P(health_status | age_group)

    Based on National Health Survey 2020 + MOH disease burden data.
    Chronic disease prevalence increases exponentially with age.
    """
    cpt = {}

    for age in ["0-4", "5-9", "10-14", "15-19"]:
        cpt[(age,)] = {"Healthy": 0.95, "Chronic_Mild": 0.04,
                       "Chronic_Severe": 0.008, "Disabled": 0.002}

    cpt[("20-24",)] = {"Healthy": 0.93, "Chronic_Mild": 0.05,
                       "Chronic_Severe": 0.015, "Disabled": 0.005}
    cpt[("25-29",)] = {"Healthy": 0.91, "Chronic_Mild": 0.06,
                       "Chronic_Severe": 0.02, "Disabled": 0.01}
    cpt[("30-34",)] = {"Healthy": 0.88, "Chronic_Mild": 0.08,
                       "Chronic_Severe": 0.03, "Disabled": 0.01}
    cpt[("35-39",)] = {"Healthy": 0.84, "Chronic_Mild": 0.10,
                       "Chronic_Severe": 0.04, "Disabled": 0.02}
    cpt[("40-44",)] = {"Healthy": 0.78, "Chronic_Mild": 0.14,
                       "Chronic_Severe": 0.05, "Disabled": 0.03}
    cpt[("45-49",)] = {"Healthy": 0.72, "Chronic_Mild": 0.17,
                       "Chronic_Severe": 0.07, "Disabled": 0.04}
    cpt[("50-54",)] = {"Healthy": 0.65, "Chronic_Mild": 0.20,
                       "Chronic_Severe": 0.10, "Disabled": 0.05}
    cpt[("55-59",)] = {"Healthy": 0.55, "Chronic_Mild": 0.25,
                       "Chronic_Severe": 0.13, "Disabled": 0.07}
    cpt[("60-64",)] = {"Healthy": 0.45, "Chronic_Mild": 0.28,
                       "Chronic_Severe": 0.17, "Disabled": 0.10}
    cpt[("65-69",)] = {"Healthy": 0.38, "Chronic_Mild": 0.30,
                       "Chronic_Severe": 0.20, "Disabled": 0.12}
    cpt[("70-74",)] = {"Healthy": 0.30, "Chronic_Mild": 0.30,
                       "Chronic_Severe": 0.25, "Disabled": 0.15}
    cpt[("75-79",)] = {"Healthy": 0.22, "Chronic_Mild": 0.28,
                       "Chronic_Severe": 0.28, "Disabled": 0.22}

    for age in ["80-84", "85-89", "90-94", "95-99", "100"]:
        cpt[(age,)] = {"Healthy": 0.15, "Chronic_Mild": 0.25,
                       "Chronic_Severe": 0.30, "Disabled": 0.30}

    return cpt


# ============================================================
# INCOME COPULA (continuous sampling within band)
# ============================================================

def build_income_copula() -> GaussianCopula:
    """
    Gaussian copula for income × education_years × age.

    Correlation structure (estimated from MOM data):
    - income ~ education: r = 0.55
    - income ~ age: r = 0.30 (inverted-U shape, approximated as linear)
    - education ~ age: r = -0.15 (younger cohorts more educated)
    """
    R = np.array([
        [1.00, 0.55, 0.30],   # income
        [0.55, 1.00, -0.15],  # education_years
        [0.30, -0.15, 1.00],  # age
    ])
    return GaussianCopula(R, ["income", "education_years", "age"])


# ============================================================
# LAYER 2: LOGISTIC EVENT MODELS (Singapore-calibrated)
# ============================================================

def build_sg_event_models() -> Dict[str, dict]:
    """
    Logistic regression models for key life events,
    calibrated to Singapore rates.

    Returns dict of event_name -> {coefficients, intercept, annual_rate}
    """
    models = {}

    # Marriage probability (annual)
    # Base rate ~5% for single 25-34 year olds
    # Higher for women, higher income, higher education
    models["marriage"] = {
        "intercept": -3.5,
        "coefficients": {
            "age": 0.08,       # peaks at 30s
            "monthly_income": 0.00005,  # income effect
        },
        "annual_base_rate": 0.05,
    }

    # Job change probability (annual)
    # ~12% annual turnover rate in SG (MOM 2020)
    models["job_change"] = {
        "intercept": -2.3,
        "coefficients": {
            "age": -0.03,      # decreases with age
            "monthly_income": -0.00002,  # higher income → less likely to change
        },
        "annual_base_rate": 0.12,
    }

    # First child probability (annual, for married couples 25-40)
    # TFR 1.1 in Singapore — very low fertility
    models["first_child"] = {
        "intercept": -3.0,
        "coefficients": {
            "age": -0.05,      # decreases sharply with age
            "monthly_income": 0.00003,
        },
        "annual_base_rate": 0.08,
    }

    # Divorce probability (annual, for married)
    # ~7,600 divorces/year out of ~1.1M married couples = 0.7%
    models["divorce"] = {
        "intercept": -5.0,
        "coefficients": {
            "age": -0.02,
        },
        "annual_base_rate": 0.007,
    }

    # Housing purchase (BTO application, annual)
    models["bto_application"] = {
        "intercept": -3.5,
        "coefficients": {
            "age": 0.05,
            "monthly_income": 0.00004,
        },
        "annual_base_rate": 0.04,
    }

    # Chronic disease onset (annual, age 40+)
    # ~20% prevalence at 40, ~50% at 60
    models["chronic_onset"] = {
        "intercept": -5.0,
        "coefficients": {
            "age": 0.06,
        },
        "annual_base_rate": 0.03,
    }

    return models
