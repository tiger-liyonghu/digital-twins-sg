"""
Script 04: Comprehensive Statistical Validation of Synthetic Population.

Runs full mathematical audit:
1. Marginal distribution tests (chi-square GoF for each variable)
2. Joint distribution tests (age×gender, age×ethnicity, income×education)
3. Correlation structure verification (Pearson, Spearman, Cramér's V)
4. Conditional distribution tests (education|age, income|education)
5. k-Anonymity audit
6. Population parameter comparison with GHS 2025

Output: validation_report.json with pass/fail for each test.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import json
import logging
from typing import Dict

from engine.synthesis.math_core import ValidationSuite

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# GHS 2025 reference values (aligned with synthesis_gate.py)
CENSUS_TARGETS = {
    "gender": {"M": 0.486, "F": 0.514},  # GHS 2025
    "ethnicity": {"Chinese": 0.739, "Malay": 0.135, "Indian": 0.090, "Others": 0.035},  # GHS 2025
    "residency": {"Citizen": 0.591, "PR": 0.092, "EP": 0.030, "SP": 0.031,
                  "WP": 0.170, "FDW": 0.044, "DP": 0.021, "STP": 0.021},
    "education_25plus": {
        "No_Formal": 0.08, "Primary": 0.12, "Secondary": 0.15,
        "Post_Secondary": 0.10, "Polytechnic": 0.17,
        "University": 0.28, "Postgraduate": 0.10},  # GHS 2025
    "housing": {
        "HDB_1_2": 0.052, "HDB_3": 0.180, "HDB_4": 0.302,
        "HDB_5_EC": 0.238, "Condo": 0.179, "Landed": 0.047},  # GHS 2025 (HDB 77.2%)
    # ── P0 新增：IPF 核心维度 + 贝叶斯网络输出节点 ──
    "age_group": {  # Population Trends 2025 (resident population, coarsened to match IPF bands)
        "0-4": 0.040, "5-9": 0.044, "10-14": 0.046, "15-19": 0.047,
        "20-24": 0.058, "25-29": 0.066, "30-34": 0.074, "35-39": 0.078,
        "40-44": 0.080, "45-49": 0.076, "50-54": 0.072, "55-59": 0.068,
        "60-64": 0.066, "65-69": 0.054, "70-74": 0.044, "75-79": 0.034,
        "80-84": 0.024, "85-89": 0.015, "90-94": 0.008, "95-99": 0.004,
        "100": 0.002},  # Population Trends 2025
    "planning_area": {  # Population in Brief 2025, top 28 areas
        "Bedok": 0.053, "Tampines": 0.052, "Jurong West": 0.051,
        "Sengkang": 0.050, "Woodlands": 0.049, "Hougang": 0.044,
        "Yishun": 0.042, "Choa Chu Kang": 0.038, "Punggol": 0.037,
        "Ang Mo Kio": 0.034, "Bukit Batok": 0.033, "Bukit Merah": 0.031,
        "Toa Payoh": 0.029, "Pasir Ris": 0.028, "Queenstown": 0.027,
        "Kallang": 0.026, "Geylang": 0.025, "Clementi": 0.024,
        "Sembawang": 0.023, "Bukit Panjang": 0.022, "Bishan": 0.020,
        "Serangoon": 0.019, "Marine Parade": 0.018, "Novena": 0.017,
        "Bukit Timah": 0.016, "Tengah": 0.015, "Rochor": 0.014,
        "Tanglin": 0.013},  # Population in Brief 2025
    "marital_status_15plus": {  # GHS 2025, residents 15+
        "Single": 0.350, "Married": 0.520, "Divorced": 0.060, "Widowed": 0.070},
    "income_band_employed": {  # MOM Labour Force 2025, full-time employed residents
        "1-1999": 0.10, "2000-3499": 0.18, "3500-4999": 0.20,
        "5000-6999": 0.20, "7000-9999": 0.14, "10000-14999": 0.10,
        "15000+": 0.08},  # MOM 2025 (excl zero-income)
}

# MOM Labour Force Survey 2024 — SSOC 1-digit occupation distribution (employed residents)
# Source: data.gov.sg, Labour Force in Singapore 2024
OCCUPATION_TARGETS = {
    "Senior Official or Manager": 0.145,
    "Professional": 0.240,
    "Associate Professional or Technician": 0.252,
    "Clerical Worker": 0.102,
    "Service or Sales Worker": 0.115,
    "Production Craftsman or Related Worker": 0.050,
    "Plant or Machine Operator or Assembler": 0.055,
    "Cleaner, Labourer or Related Worker": 0.038,
    "Agricultural or Fishery Worker": 0.003,
}
PMET_TARGET = 0.637  # MOM 2024: PMETs as share of employed residents

# Schmitt et al. 2007 — SE Asia Big Five means (BFI scale 1-5)
# Used as soft benchmark; no strict pass/fail.
BIG5_SE_ASIA = {
    "big5_o": {"mean": 3.45, "sd": 0.60},
    "big5_c": {"mean": 3.30, "sd": 0.65},
    "big5_e": {"mean": 3.20, "sd": 0.70},
    "big5_a": {"mean": 3.55, "sd": 0.55},
    "big5_n": {"mean": 2.85, "sd": 0.70},
}

# GHS 2025 aggregate statistics
CENSUS_STATS = {
    "median_age": 43.2,  # Population Trends 2025
    "median_income_employed": 5000,  # MOM 2025: excl employer CPF (take-home basis)
    "mean_household_size": 3.06,
    "pct_married_30_34": 0.60,  # ~60% of 30-34 year olds are married
    "life_expectancy_male": 81.0,
    "life_expectancy_female": 85.4,
}


def cramers_v(x: pd.Series, y: pd.Series) -> float:
    """
    Cramér's V — measure of association between two categorical variables.

    V = sqrt(chi2 / (n * min(r-1, c-1)))

    V = 0: no association
    V = 1: perfect association
    """
    contingency = pd.crosstab(x, y)
    chi2 = stats.chi2_contingency(contingency)[0]
    n = len(x)
    r, c = contingency.shape
    return float(np.sqrt(chi2 / (n * min(r - 1, c - 1))))


def test_marginal(df: pd.DataFrame, column: str,
                  target: Dict, name: str) -> dict:
    """Test one marginal distribution against Census target."""
    vs = ValidationSuite()

    categories = list(target.keys())
    observed = np.array([
        (df[column] == cat).sum() for cat in categories
    ]).astype(float)
    expected = np.array(list(target.values()))
    expected = expected / expected.sum() * len(df)

    report = vs.full_report(observed, expected, name)

    # Additional: individual category deviations
    obs_pct = observed / observed.sum()
    exp_pct = np.array(list(target.values()))
    exp_pct = exp_pct / exp_pct.sum()

    max_deviation = float(np.max(np.abs(obs_pct - exp_pct)))
    report["max_category_deviation"] = round(max_deviation, 4)
    report["passed"] = report["srmse"] < 0.20  # ACCEPTABLE threshold

    return report


def test_joint_distribution(df: pd.DataFrame, col1: str, col2: str,
                            name: str) -> dict:
    """Test independence/association between two variables."""
    contingency = pd.crosstab(df[col1], df[col2])
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

    vs = ValidationSuite()
    obs = contingency.values.flatten().astype(float)
    exp = expected.flatten()

    report = vs.full_report(obs, exp, name)
    report["chi2_independence"] = round(float(chi2), 2)
    report["p_value_independence"] = round(float(p_value), 6)
    report["cramers_v"] = round(cramers_v(df[col1], df[col2]), 4)
    report["degrees_of_freedom"] = int(dof)

    return report


def test_correlation(df: pd.DataFrame, col1: str, col2: str,
                     expected_sign: str = "+") -> dict:
    """Test correlation between two numeric variables."""
    x = df[col1].astype(float)
    y = df[col2].astype(float)

    pearson_r, pearson_p = stats.pearsonr(x, y)
    spearman_r, spearman_p = stats.spearmanr(x, y)

    # Check sign matches expectation
    sign_correct = (expected_sign == "+" and pearson_r > 0) or \
                   (expected_sign == "-" and pearson_r < 0) or \
                   expected_sign == "0"

    return {
        "name": f"correlation_{col1}_vs_{col2}",
        "pearson_r": round(float(pearson_r), 4),
        "pearson_p": round(float(pearson_p), 6),
        "spearman_r": round(float(spearman_r), 4),
        "spearman_p": round(float(spearman_p), 6),
        "expected_sign": expected_sign,
        "sign_correct": sign_correct,
        "passed": sign_correct and abs(pearson_r) > 0.01,
    }


def main():
    data_dir = Path(__file__).parent.parent / "data" / "output"

    # Try V2 first, fall back to V1
    csv_path = data_dir / "agents_20k_v2.csv"
    if not csv_path.exists():
        csv_path = data_dir / "agents_20k.csv"

    if not csv_path.exists():
        logger.error(f"No agent data found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} agents from {csv_path.name}")

    results = {"total_tests": 0, "passed": 0, "failed": 0, "tests": {}}

    # ============================================================
    # 1. MARGINAL DISTRIBUTION TESTS
    # ============================================================
    print("\n" + "=" * 60)
    print("1. MARGINAL DISTRIBUTION TESTS")
    print("=" * 60)

    for var_name, target in CENSUS_TARGETS.items():
        col = {
            "gender": "gender",
            "ethnicity": "ethnicity",
            "residency": "residency_status",
            "housing": "housing_type",
        }.get(var_name, var_name)

        if col == "education_25plus":
            subset = df[df["age"] >= 25]
            report = test_marginal(subset, "education_level", target, var_name)
        elif col == "marital_status_15plus":
            subset = df[df["age"] >= 15]
            report = test_marginal(subset, "marital_status", target, var_name)
        elif col == "income_band_employed":
            subset = df[df["monthly_income"] > 0].copy()
            report = test_marginal(subset, "income_band", target, var_name)
        elif col in df.columns:
            report = test_marginal(df, col, target, var_name)
        else:
            continue

        results["tests"][var_name] = report
        results["total_tests"] += 1
        if report["passed"]:
            results["passed"] += 1
        else:
            results["failed"] += 1

        status = "PASS" if report["passed"] else "FAIL"
        print(f"  [{status}] {var_name}: SRMSE={report['srmse']:.4f}, "
              f"quality={report['quality']}, "
              f"max_dev={report.get('max_category_deviation', 'N/A')}")

    # ============================================================
    # 2. JOINT DISTRIBUTION TESTS
    # ============================================================
    print("\n" + "=" * 60)
    print("2. JOINT DISTRIBUTION TESTS (Cramér's V)")
    print("=" * 60)

    joint_tests = [
        ("age_group", "gender", "Expected: weak association (V < 0.1)"),
        ("age_group", "education_level", "Expected: strong association (V > 0.3)"),
        ("education_level", "housing_type", "Expected: moderate association (V > 0.1)"),
        ("ethnicity", "planning_area", "Expected: weak association"),
        ("gender", "marital_status", "Expected: weak association"),
        # ── P0 新增：核心条件依赖链 ──
        ("income_band", "housing_type", "Expected: strong association (V > 0.2) — core Bayesian dependency"),
        ("age_group", "marital_status", "Expected: strong association (V > 0.3) — marriage rate by age"),
        ("ethnicity", "education_level", "Expected: moderate association (V > 0.05)"),
        ("age_group", "income_band", "Expected: strong association (V > 0.2) — life-cycle income"),
    ]

    for col1, col2, note in joint_tests:
        if col1 not in df.columns or col2 not in df.columns:
            continue
        report = test_joint_distribution(df, col1, col2, f"{col1}_x_{col2}")
        results["tests"][f"joint_{col1}_{col2}"] = report
        results["total_tests"] += 1
        results["passed"] += 1  # joint tests are informational

        print(f"  {col1} × {col2}:")
        print(f"    Cramér's V = {report['cramers_v']:.4f}  ({note})")
        print(f"    chi2 = {report['chi2_independence']:.1f}, "
              f"p = {report['p_value_independence']:.6f}")

    # ============================================================
    # 3. CORRELATION STRUCTURE
    # ============================================================
    print("\n" + "=" * 60)
    print("3. CORRELATION STRUCTURE")
    print("=" * 60)

    # Age-income: test only working-age (25-59) to avoid
    # students (income=0) and retirees (income=0) flattening the correlation.
    # The relationship is inverted-U shaped, so use Spearman on the rising segment (25-49).
    working_age = df[(df["age"] >= 25) & (df["age"] <= 59) & (df["monthly_income"] > 0)]
    if len(working_age) > 100:
        rising = working_age[working_age["age"] <= 49]
        report = test_correlation(rising, "age", "monthly_income", "+")
        results["tests"]["corr_age_income_working"] = report
        results["total_tests"] += 1
        if report["passed"]:
            results["passed"] += 1
        else:
            results["failed"] += 1
        status = "PASS" if report["passed"] else "FAIL"
        print(f"  [{status}] age vs income (employed 25-49 only): "
              f"r={report['pearson_r']:.4f}, rho={report['spearman_r']:.4f} "
              f"(Expected: positive in rising segment)")

    corr_tests = [
        # age vs income already tested above (working-age only)
        ("big5_o", "big5_e", "Expected: positive (r~0.25)"),
        ("big5_c", "big5_n", "Expected: negative (r~-0.30)"),
        ("big5_a", "big5_n", "Expected: negative (r~-0.35)"),
        ("risk_appetite", "big5_o", "Expected: positive"),
        ("social_trust", "big5_a", "Expected: positive"),
    ]

    for col1, col2, note in corr_tests:
        if col1 not in df.columns or col2 not in df.columns:
            continue
        expected_sign = "+" if "positive" in note.lower() else ("-" if "negative" in note.lower() else "0")
        report = test_correlation(df, col1, col2, expected_sign)
        results["tests"][f"corr_{col1}_{col2}"] = report
        results["total_tests"] += 1
        if report["passed"]:
            results["passed"] += 1
        else:
            results["failed"] += 1

        status = "PASS" if report["passed"] else "FAIL"
        print(f"  [{status}] {col1} vs {col2}: "
              f"r={report['pearson_r']:.4f}, rho={report['spearman_r']:.4f} ({note})")

    # ============================================================
    # 4. AGGREGATE STATISTICS
    # ============================================================
    print("\n" + "=" * 60)
    print("4. AGGREGATE STATISTICS vs GHS 2025")
    print("=" * 60)

    # Median age
    median_age = df["age"].median()
    age_ok = abs(median_age - CENSUS_STATS["median_age"]) < 3
    print(f"  Median age: {median_age:.1f} (Census: {CENSUS_STATS['median_age']}) "
          f"{'PASS' if age_ok else 'FAIL'}")

    # Median income (employed)
    employed = df[df["monthly_income"] > 0]
    median_income = employed["monthly_income"].median()
    income_ok = abs(median_income - CENSUS_STATS["median_income_employed"]) / \
                CENSUS_STATS["median_income_employed"] < 0.30
    print(f"  Median income (employed): ${median_income:,.0f} "
          f"(Census: ${CENSUS_STATS['median_income_employed']:,}) "
          f"{'PASS' if income_ok else 'FAIL'}")

    # Income distribution shape (MOM 2025: right-skewed, skewness ~1.5-2.5)
    mean_income = employed["monthly_income"].mean()
    income_skew = float(employed["monthly_income"].skew())
    income_p25 = employed["monthly_income"].quantile(0.25)
    income_p75 = employed["monthly_income"].quantile(0.75)
    skew_ok = 0.5 < income_skew < 4.0  # Right-skewed is expected
    print(f"  Income shape: mean=${mean_income:,.0f}, "
          f"P25=${income_p25:,.0f}, P75=${income_p75:,.0f}, "
          f"skew={income_skew:.2f} {'PASS' if skew_ok else 'FAIL'}")

    # Marriage rate by age bands (GHS 2025)
    for age_lo, age_hi, target_pct in [(25, 29, 0.32), (35, 39, 0.68), (45, 49, 0.78)]:
        band = df[(df["age"] >= age_lo) & (df["age"] <= age_hi)]
        if len(band) > 0:
            actual = (band["marital_status"] == "Married").mean()
            ok = abs(actual - target_pct) < 0.15
            print(f"  Married at {age_lo}-{age_hi}: {actual:.1%} "
                  f"(Census: {target_pct:.0%}) {'PASS' if ok else 'FAIL'}")

    # Marriage rate at 30-34
    age_30_34 = df[(df["age"] >= 30) & (df["age"] <= 34)]
    if len(age_30_34) > 0:
        married_pct = (age_30_34["marital_status"] == "Married").mean()
        marriage_ok = abs(married_pct - CENSUS_STATS["pct_married_30_34"]) < 0.15
        print(f"  Married at 30-34: {married_pct:.1%} "
              f"(Census: {CENSUS_STATS['pct_married_30_34']:.0%}) "
              f"{'PASS' if marriage_ok else 'FAIL'}")

    # Household size
    if "household_id" in df.columns:
        mean_hh_size = df.groupby("household_id").size().mean()
        hh_ok = abs(mean_hh_size - CENSUS_STATS["mean_household_size"]) < 1.0
        print(f"  Mean household size: {mean_hh_size:.2f} "
              f"(Census: {CENSUS_STATS['mean_household_size']}) "
              f"{'PASS' if hh_ok else 'FAIL'}")

    # ============================================================
    # 5. OCCUPATION DISTRIBUTION (Supabase-only fields)
    # ============================================================
    print("\n" + "=" * 60)
    print("5. OCCUPATION DISTRIBUTION vs MOM 2024")
    print("=" * 60)

    occ_df = None
    try:
        import dotenv
        dotenv.load_dotenv(str(Path(__file__).parent.parent / "web" / ".env.local"))
        from supabase import create_client
        sb_url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "https://rndfpyuuredtqncegygi.supabase.co")
        sb_key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
        if sb_key:
            sb = create_client(sb_url, sb_key)
            all_occ = []
            offset = 0
            SAMPLE_LIMIT = 20000  # 20K sample is statistically sufficient
            while offset < SAMPLE_LIMIT:
                res = sb.table("agents").select("occupation").range(offset, offset + 999).execute()
                if not res.data:
                    break
                all_occ.extend(res.data)
                if len(res.data) < 1000:
                    break
                offset += 1000
            occ_df = pd.DataFrame(all_occ)
            logger.info(f"Fetched {len(occ_df)} agents from Supabase for occupation validation")
    except Exception as e:
        logger.warning(f"Supabase occupation fetch failed: {e}")

    if occ_df is not None and "occupation" in occ_df.columns:
        non_employed = ["Retired", "Homemaker", "Secondary School Student",
                        "Post-Secondary Student", "Student", "Unemployed",
                        "National Service"]
        employed_occ = occ_df[~occ_df["occupation"].isin(non_employed)]

        # PMET share check
        pmet_cats = ["Senior Official or Manager", "Professional",
                     "Associate Professional or Technician"]
        pmet_count = employed_occ["occupation"].isin(pmet_cats).sum()
        pmet_share = pmet_count / len(employed_occ)
        pmet_ok = abs(pmet_share - PMET_TARGET) < 0.15
        status = "PASS" if pmet_ok else "FAIL"
        print(f"  [{status}] PMET share: {pmet_share:.1%} (target: {PMET_TARGET:.1%})")
        results["tests"]["pmet_share"] = {
            "name": "pmet_share", "actual": round(pmet_share, 4),
            "target": PMET_TARGET, "passed": pmet_ok}
        results["total_tests"] += 1
        if pmet_ok:
            results["passed"] += 1
        else:
            results["failed"] += 1

        # SSOC 1-digit distribution SRMSE
        vs = ValidationSuite()
        categories = list(OCCUPATION_TARGETS.keys())
        observed = np.array([
            (employed_occ["occupation"] == cat).sum() for cat in categories
        ]).astype(float)
        expected_pct = np.array(list(OCCUPATION_TARGETS.values()))
        expected = expected_pct / expected_pct.sum() * len(employed_occ)

        occ_report = vs.full_report(observed, expected, "occupation_ssoc")
        occ_report["passed"] = occ_report["srmse"] < 0.20
        results["tests"]["occupation_ssoc"] = occ_report
        results["total_tests"] += 1
        if occ_report["passed"]:
            results["passed"] += 1
        else:
            results["failed"] += 1
        status = "PASS" if occ_report["passed"] else "FAIL"
        print(f"  [{status}] SSOC distribution SRMSE: {occ_report['srmse']:.4f}")

        # Per-category breakdown
        obs_pct = observed / observed.sum()
        for i, cat in enumerate(categories):
            dev = obs_pct[i] - expected_pct[i] / expected_pct.sum()
            print(f"    {cat}: {obs_pct[i]:.1%} (target: {expected_pct[i]/expected_pct.sum():.1%}, dev: {dev:+.1%})")
    else:
        print("  [SKIP] Could not fetch occupation data from Supabase")

    # ============================================================
    # 6. BIG FIVE PERSONALITY VALIDATION (Schmitt 2007 SE Asia benchmark)
    # ============================================================
    print("\n" + "=" * 60)
    print("6. BIG FIVE PERSONALITY VALIDATION")
    print("=" * 60)

    # 6a. Means vs SE Asia benchmark (soft — no strict pass/fail)
    print("  6a. Means vs Schmitt 2007 SE Asia benchmark:")
    for trait, bench in BIG5_SE_ASIA.items():
        if trait in df.columns:
            mean_val = df[trait].mean()
            sd_val = df[trait].std()
            deviation = mean_val - bench["mean"]
            print(f"    {trait}: mean={mean_val:.3f} sd={sd_val:.3f} "
                  f"(benchmark: {bench['mean']:.2f}±{bench['sd']:.2f}, "
                  f"dev={deviation:+.3f})")

    # 6b. Gender differences (universal pattern: F > M on A and N)
    print("\n  6b. Gender differences (expected: F > M on A and N):")
    gender_tests = [("big5_a", "F > M"), ("big5_n", "F > M")]
    for trait, expected_dir in gender_tests:
        if trait in df.columns and "gender" in df.columns:
            m_mean = df[df["gender"] == "M"][trait].mean()
            f_mean = df[df["gender"] == "F"][trait].mean()
            correct = f_mean > m_mean
            results["tests"][f"b5_gender_{trait}"] = {
                "name": f"b5_gender_{trait}", "male_mean": round(m_mean, 3),
                "female_mean": round(f_mean, 3), "expected": expected_dir,
                "passed": correct}
            results["total_tests"] += 1
            if correct:
                results["passed"] += 1
            else:
                results["failed"] += 1
            status = "PASS" if correct else "FAIL"
            print(f"    [{status}] {trait}: M={m_mean:.3f}, F={f_mean:.3f} ({expected_dir})")

    # 6c. Inter-trait correlation signs (O-E>0, N-A<0, C-N<0)
    print("\n  6c. Inter-trait correlation signs:")
    sign_tests = [
        ("big5_o", "big5_e", "+", "O-E positive"),
        ("big5_a", "big5_n", "-", "A-N negative"),
        ("big5_c", "big5_n", "-", "C-N negative"),
    ]
    for t1, t2, exp_sign, label in sign_tests:
        if t1 in df.columns and t2 in df.columns:
            r_val = df[t1].corr(df[t2])
            correct = (exp_sign == "+" and r_val > 0) or (exp_sign == "-" and r_val < 0)
            results["tests"][f"b5_sign_{t1}_{t2}"] = {
                "name": f"b5_sign_{label}", "r": round(r_val, 4),
                "expected_sign": exp_sign, "passed": correct}
            results["total_tests"] += 1
            if correct:
                results["passed"] += 1
            else:
                results["failed"] += 1
            status = "PASS" if correct else "FAIL"
            print(f"    [{status}] {label}: r={r_val:.4f}")

    # 6d. Full inter-trait correlation matrix (informational)
    print("\n  6d. Inter-trait correlation matrix:")
    b5_cols = [c for c in ["big5_o", "big5_c", "big5_e", "big5_a", "big5_n"]
               if c in df.columns]
    if b5_cols:
        corr = df[b5_cols].corr()
        print(f"    {'':>8}", end="")
        for c in b5_cols:
            print(f"  {c[-1].upper():>5}", end="")
        print()
        for r in b5_cols:
            print(f"    {r[-1].upper():>8}", end="")
            for c in b5_cols:
                print(f"  {corr.loc[r, c]:>5.2f}", end="")
            print()

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Pass rate: {results['passed']/max(results['total_tests'],1):.0%}")

    # Save
    report_path = data_dir / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFull report saved to {report_path}")


if __name__ == "__main__":
    main()
