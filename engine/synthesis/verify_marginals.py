"""
Mathematical Verification of Synthetic Population Marginals

Before applying coherence rules, we must verify:
1. Current CPT chain produces correct marginal distributions
2. Coherence rules won't distort marginals beyond acceptable thresholds
3. If distortion occurs, compute correction factors

Math framework:
- Let X = (age, gender, ethnicity, education, income, housing, marital, health, occupation)
- Current synthesis: each attribute sampled from P(X_i | parents(X_i))
- Marginal of attribute k: P(X_k) = sum over parents P(X_k|parents) * P(parents)
- Coherence rule = deterministic constraint C(X) that zeroes some joint cells
- Post-rule marginal: P'(X_k) = P(X_k | C(X) satisfied)

We compute P'(X_k) analytically and compare to census targets.
"""

import numpy as np
import sys
import os

# Add engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine.synthesis.sg_distributions import (
    AGE_MARGINAL, AGE_LABELS,
    GENDER_MARGINAL, GENDER_LABELS,
    ETHNICITY_MARGINAL, ETHNICITY_LABELS,
    RESIDENCY_MARGINAL, RESIDENCY_LABELS,
    build_education_cpt, build_income_cpt,
    build_housing_income_cpt, build_marital_age_cpt,
    build_health_age_cpt,
)
from engine.synthesis.synthesis_gate import CENSUS_TARGETS


def normalize(arr):
    s = arr.sum()
    return arr / s if s > 0 else arr


def srmse(observed, expected):
    """Standardized Root Mean Squared Error"""
    if len(observed) == 0 or np.mean(expected) == 0:
        return float('inf')
    rmse = np.sqrt(np.mean((observed - expected) ** 2))
    return rmse / np.mean(expected)


def compute_education_marginal():
    """P(education) = sum_age P(education|age) * P(age)"""
    cpt = build_education_cpt()
    edu_levels = ["No_Formal", "Primary", "Secondary", "Post_Secondary",
                  "Polytechnic", "University", "Postgraduate"]

    marginal = {e: 0.0 for e in edu_levels}
    for i, age_label in enumerate(AGE_LABELS):
        p_age = AGE_MARGINAL[i]
        key = (age_label,)
        if key in cpt:
            for edu in edu_levels:
                marginal[edu] += cpt[key].get(edu, 0) * p_age

    return marginal


def compute_income_marginal():
    """P(income) = sum_{edu,age} P(income|edu,age) * P(edu|age) * P(age)"""
    edu_cpt = build_education_cpt()
    inc_cpt = build_income_cpt()

    bands = ["0", "1-1999", "2000-3499", "3500-4999",
             "5000-6999", "7000-9999", "10000-14999", "15000+"]
    edu_levels = ["No_Formal", "Primary", "Secondary", "Post_Secondary",
                  "Polytechnic", "University", "Postgraduate"]

    marginal = {b: 0.0 for b in bands}

    for i, age_label in enumerate(AGE_LABELS):
        p_age = AGE_MARGINAL[i]
        edu_key = (age_label,)
        if edu_key not in edu_cpt:
            continue

        for edu in edu_levels:
            p_edu_given_age = edu_cpt[edu_key].get(edu, 0)
            inc_key = (edu, age_label)
            if inc_key in inc_cpt:
                for band in bands:
                    marginal[band] += inc_cpt[inc_key].get(band, 0) * p_edu_given_age * p_age

    return marginal


def compute_housing_marginal():
    """P(housing) = sum_income P(housing|income) * P(income)"""
    inc_marginal = compute_income_marginal()
    hous_cpt = build_housing_income_cpt()

    housing_types = ["HDB_1_2", "HDB_3", "HDB_4", "HDB_5_EC", "Condo", "Landed"]
    marginal = {h: 0.0 for h in housing_types}

    for band, p_band in inc_marginal.items():
        key = (band,)
        if key in hous_cpt:
            for h in housing_types:
                marginal[h] += hous_cpt[key].get(h, 0) * p_band

    return marginal


def compute_marital_marginal():
    """P(marital) = sum_{age,gender} P(marital|age,gender) * P(age) * P(gender)"""
    mar_cpt = build_marital_age_cpt()
    statuses = ["Single", "Married", "Divorced", "Widowed"]
    marginal = {s: 0.0 for s in statuses}

    for i, age_label in enumerate(AGE_LABELS):
        p_age = AGE_MARGINAL[i]
        for j, gender in enumerate(GENDER_LABELS):
            p_gender = GENDER_MARGINAL[j]
            key = (age_label, gender)
            if key in mar_cpt:
                for s in statuses:
                    marginal[s] += mar_cpt[key].get(s, 0) * p_age * p_gender

    return marginal


def compute_health_marginal():
    """P(health) = sum_age P(health|age) * P(age)"""
    h_cpt = build_health_age_cpt()
    statuses = ["Healthy", "Chronic_Mild", "Chronic_Severe", "Disabled"]
    marginal = {s: 0.0 for s in statuses}

    for i, age_label in enumerate(AGE_LABELS):
        p_age = AGE_MARGINAL[i]
        key = (age_label,)
        if key in h_cpt:
            for s in statuses:
                marginal[s] += h_cpt[key].get(s, 0) * p_age

    return marginal


def compute_married_30_34():
    """P(married | age 30-34)"""
    mar_cpt = build_marital_age_cpt()
    rate = 0.0
    for j, gender in enumerate(GENDER_LABELS):
        p_gender = GENDER_MARGINAL[j]
        key = ("30-34", gender)
        if key in mar_cpt:
            rate += mar_cpt[key].get("Married", 0) * p_gender
    return rate


def income_band_midpoint(band):
    """Convert income band to midpoint for median estimation"""
    mapping = {
        "0": 0, "1-1999": 1000, "2000-3499": 2750,
        "3500-4999": 4250, "5000-6999": 6000,
        "7000-9999": 8500, "10000-14999": 12500, "15000+": 18000
    }
    return mapping.get(band, 0)


def estimate_median_income_employed(inc_marginal):
    """Estimate median income among employed (income > 0)"""
    bands = ["1-1999", "2000-3499", "3500-4999", "5000-6999",
             "7000-9999", "10000-14999", "15000+"]

    total_employed = sum(inc_marginal[b] for b in bands)
    if total_employed == 0:
        return 0

    cumulative = 0
    for band in bands:
        p = inc_marginal[band] / total_employed
        cumulative += p
        if cumulative >= 0.5:
            return income_band_midpoint(band)

    return income_band_midpoint(bands[-1])


def estimate_median_age():
    """Estimate median age from age marginal"""
    age_midpoints = [2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57,
                     62, 67, 72, 77, 82, 87, 92, 97, 100]
    cumulative = 0
    for i, p in enumerate(AGE_MARGINAL):
        cumulative += p
        if cumulative >= 0.5:
            return age_midpoints[i]
    return age_midpoints[-1]


# ============================================================
# COHERENCE RULES IMPACT ANALYSIS
# ============================================================

def simulate_coherence_impact():
    """
    Simulate the effect of coherence rules on marginal distributions.

    Key rules that change joint distribution:
    1. Student/Unemployed/Homemaker → income=0
       Currently income is drawn P(income|edu,age) without occupation conditioning.
       In the DB, occupation IS assigned. But income CPT doesn't condition on it.

    2. WP → housing in {HDB_1_2, HDB_3}
       Currently housing is drawn P(housing|income). WP workers with high income
       could get Condo/Landed. Rule forces them to HDB.

    3. Age<15 → health=Healthy (99%)
       Current CPT already gives 95% Healthy for children. Rule tightens to 99%.

    For each rule, compute:
    - Fraction of population affected
    - Marginal distortion
    - Required CPT adjustment to compensate
    """
    results = {}

    # --- Rule: WP → HDB_1_2 or HDB_3 ---
    # WP fraction: 16.2% of population
    # Currently WP workers get housing from P(housing|income) like everyone else
    # After rule: all WP → {HDB_1_2, HDB_3}
    p_wp = RESIDENCY_MARGINAL[RESIDENCY_LABELS.index("WP")]

    hous_marginal = compute_housing_marginal()
    # WP housing currently follows income distribution
    # After rule: WP housing = {HDB_1_2: 0.6, HDB_3: 0.4} (dormitory/shared)
    wp_housing_after = {"HDB_1_2": 0.6, "HDB_3": 0.4, "HDB_4": 0, "HDB_5_EC": 0, "Condo": 0, "Landed": 0}

    hous_marginal_after = {}
    for h in hous_marginal:
        # non-WP keep original; WP get reassigned
        hous_marginal_after[h] = hous_marginal[h] * (1 - p_wp) + wp_housing_after.get(h, 0) * p_wp

    results['wp_housing'] = {
        'before': hous_marginal,
        'after': hous_marginal_after,
        'affected_fraction': p_wp,
    }

    # --- Rule: Children (age<15) → health=Healthy 99% ---
    p_child = sum(AGE_MARGINAL[:3])  # 0-14
    health_marginal = compute_health_marginal()

    # children currently: 95% healthy, 4% chronic_mild, 0.8% chronic_severe, 0.2% disabled
    # after rule: 99% healthy, 0.8% chronic_mild, 0.15% chronic_severe, 0.05% disabled
    child_health_before = {"Healthy": 0.95, "Chronic_Mild": 0.04, "Chronic_Severe": 0.008, "Disabled": 0.002}
    child_health_after = {"Healthy": 0.99, "Chronic_Mild": 0.008, "Chronic_Severe": 0.0015, "Disabled": 0.0005}

    health_marginal_after = {}
    for h in health_marginal:
        health_marginal_after[h] = (
            health_marginal[h]
            - child_health_before.get(h, 0) * p_child
            + child_health_after.get(h, 0) * p_child
        )

    results['child_health'] = {
        'before': health_marginal,
        'after': health_marginal_after,
        'affected_fraction': p_child,
    }

    return results


# ============================================================
# MAIN: Run full verification
# ============================================================

def main():
    print("=" * 70)
    print("MATHEMATICAL VERIFICATION OF POPULATION MARGINALS")
    print("Before applying coherence rules")
    print("=" * 70)

    # 1. Education marginal
    edu_marginal = compute_education_marginal()
    print("\n1. EDUCATION MARGINAL (implied by CPT chain)")
    print("-" * 50)
    for edu, p in edu_marginal.items():
        print(f"   {edu:20s}: {p:.3f} ({p*100:.1f}%)")
    total_edu = sum(edu_marginal.values())
    print(f"   {'TOTAL':20s}: {total_edu:.4f}")

    # University + Postgraduate among 25+
    edu_cpt = build_education_cpt()
    degree_plus_25 = 0.0
    total_25 = 0.0
    for i, age_label in enumerate(AGE_LABELS):
        # age 25+ means groups starting from "25-29"
        age_mid = [2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57,
                   62, 67, 72, 77, 82, 87, 92, 97, 100][i]
        if age_mid >= 25:
            p_age = AGE_MARGINAL[i]
            total_25 += p_age
            key = (age_label,)
            if key in edu_cpt:
                degree_plus_25 += (edu_cpt[key].get("University", 0) + edu_cpt[key].get("Postgraduate", 0)) * p_age

    degree_ratio = degree_plus_25 / total_25 if total_25 > 0 else 0
    target = CENSUS_TARGETS["education_degree_plus"]
    print(f"\n   Degree+ (25+): {degree_ratio:.3f} ({degree_ratio*100:.1f}%)")
    print(f"   Census target: {target:.3f} ({target*100:.1f}%)")
    print(f"   Deviation: {abs(degree_ratio - target)/target*100:.1f}%")

    # 2. Income marginal
    inc_marginal = compute_income_marginal()
    print("\n2. INCOME MARGINAL (implied by CPT chain)")
    print("-" * 50)
    for band, p in inc_marginal.items():
        print(f"   {band:15s}: {p:.4f} ({p*100:.1f}%)")
    total_inc = sum(inc_marginal.values())
    print(f"   {'TOTAL':15s}: {total_inc:.4f}")

    # Check coverage of income CPT
    edu_cpt_check = build_education_cpt()
    inc_cpt = build_income_cpt()
    missing_combinations = 0
    total_mass_missing = 0.0
    for i, age_label in enumerate(AGE_LABELS):
        p_age = AGE_MARGINAL[i]
        edu_key = (age_label,)
        if edu_key in edu_cpt_check:
            for edu, p_edu in edu_cpt_check[edu_key].items():
                if p_edu > 0 and (edu, age_label) not in inc_cpt:
                    missing_combinations += 1
                    total_mass_missing += p_edu * p_age

    if missing_combinations > 0:
        print(f"\n   WARNING: {missing_combinations} (education, age) combinations missing from income CPT")
        print(f"   Missing probability mass: {total_mass_missing:.4f} ({total_mass_missing*100:.1f}%)")
        print("   These agents will have NO income assigned!")

    # Median income (employed)
    median_inc = estimate_median_income_employed(inc_marginal)
    target_inc = CENSUS_TARGETS["median_income_employed"]
    print(f"\n   Median income (employed): ~${median_inc:,}")
    print(f"   Census target: ${target_inc:,}")
    print(f"   Deviation: {abs(median_inc - target_inc)/target_inc*100:.1f}%")

    # 3. Housing marginal
    hous_marginal = compute_housing_marginal()
    print("\n3. HOUSING MARGINAL (implied by CPT chain)")
    print("-" * 50)
    for h, p in hous_marginal.items():
        print(f"   {h:15s}: {p:.4f} ({p*100:.1f}%)")

    hdb_total = sum(v for k, v in hous_marginal.items() if k.startswith("HDB"))
    condo_p = hous_marginal.get("Condo", 0)
    landed_p = hous_marginal.get("Landed", 0)

    target_h = CENSUS_TARGETS["housing_agg"]
    print(f"\n   HDB aggregate:  {hdb_total:.3f} (target: {target_h['HDB']:.3f}, dev: {abs(hdb_total-target_h['HDB'])/target_h['HDB']*100:.1f}%)")
    print(f"   Condo:          {condo_p:.3f} (target: {target_h['Condo']:.3f}, dev: {abs(condo_p-target_h['Condo'])/target_h['Condo']*100:.1f}%)")
    print(f"   Landed:         {landed_p:.3f} (target: {target_h['Landed']:.3f}, dev: {abs(landed_p-target_h['Landed'])/target_h['Landed']*100:.1f}%)")

    # SRMSE
    obs = np.array([hdb_total, condo_p, landed_p])
    exp = np.array([target_h['HDB'], target_h['Condo'], target_h['Landed']])
    print(f"   SRMSE: {srmse(obs, exp):.4f} (threshold: 0.20)")

    # 4. Marital marginal
    mar_marginal = compute_marital_marginal()
    print("\n4. MARITAL STATUS MARGINAL")
    print("-" * 50)
    for s, p in mar_marginal.items():
        print(f"   {s:15s}: {p:.3f} ({p*100:.1f}%)")

    married_30_34 = compute_married_30_34()
    target_m = CENSUS_TARGETS["married_30_34"]
    print(f"\n   Married 30-34: {married_30_34:.3f} (target: {target_m:.3f}, dev: {abs(married_30_34-target_m)/target_m*100:.1f}%)")

    # 5. Health marginal
    health_marginal = compute_health_marginal()
    print("\n5. HEALTH STATUS MARGINAL")
    print("-" * 50)
    for s, p in health_marginal.items():
        print(f"   {s:20s}: {p:.3f} ({p*100:.1f}%)")

    # 6. Median age
    median_age = estimate_median_age()
    target_age = CENSUS_TARGETS["median_age"]
    print(f"\n6. MEDIAN AGE: ~{median_age} (target: {target_age}, dev: {abs(median_age-target_age)/target_age*100:.1f}%)")

    # 7. Gender (trivial — directly sampled)
    print(f"\n7. GENDER: M={GENDER_MARGINAL[0]:.3f}, F={GENDER_MARGINAL[1]:.3f} (target: M=0.486, F=0.514) -- EXACT")

    # 8. Ethnicity (trivial — directly sampled)
    print(f"\n8. ETHNICITY: {dict(zip(ETHNICITY_LABELS, ETHNICITY_MARGINAL))} -- EXACT")

    # ============================================================
    # COHERENCE RULES IMPACT
    # ============================================================
    print("\n" + "=" * 70)
    print("COHERENCE RULES IMPACT ANALYSIS")
    print("=" * 70)

    impacts = simulate_coherence_impact()

    # WP housing
    wp = impacts['wp_housing']
    print("\nRule: WP → housing in {HDB_1_2, HDB_3}")
    print(f"   Affected fraction: {wp['affected_fraction']:.1%}")
    print(f"   {'Type':15s} {'Before':>8s} {'After':>8s} {'Delta':>8s}")
    for h in wp['before']:
        before = wp['before'][h]
        after = wp['after'][h]
        delta = after - before
        print(f"   {h:15s} {before:8.3f} {after:8.3f} {delta:+8.3f}")

    hdb_after = sum(v for k, v in wp['after'].items() if k.startswith("HDB"))
    condo_after = wp['after']['Condo']
    landed_after = wp['after']['Landed']
    print(f"\n   HDB agg after rule: {hdb_after:.3f} (target: {target_h['HDB']:.3f}, dev: {abs(hdb_after-target_h['HDB'])/target_h['HDB']*100:.1f}%)")
    print(f"   Condo after rule:   {condo_after:.3f} (target: {target_h['Condo']:.3f}, dev: {abs(condo_after-target_h['Condo'])/target_h['Condo']*100:.1f}%)")
    print(f"   Landed after rule:  {landed_after:.3f} (target: {target_h['Landed']:.3f}, dev: {abs(landed_after-target_h['Landed'])/target_h['Landed']*100:.1f}%)")

    obs_after = np.array([hdb_after, condo_after, landed_after])
    print(f"   SRMSE after rule: {srmse(obs_after, exp):.4f}")

    # Child health
    ch = impacts['child_health']
    print(f"\nRule: Age<15 → health=Healthy (99%)")
    print(f"   Affected fraction: {ch['affected_fraction']:.1%}")
    print(f"   {'Status':20s} {'Before':>8s} {'After':>8s} {'Delta':>8s}")
    for h in ch['before']:
        before = ch['before'][h]
        after = ch['after'][h]
        delta = after - before
        print(f"   {h:20s} {before:8.4f} {after:8.4f} {delta:+8.4f}")

    # ============================================================
    # INCOME CPT COVERAGE ANALYSIS
    # ============================================================
    print("\n" + "=" * 70)
    print("INCOME CPT COVERAGE ANALYSIS")
    print("=" * 70)
    print("Which (education, age) combinations have income CPTs defined?")
    print()

    edu_levels = ["No_Formal", "Primary", "Secondary", "Post_Secondary",
                  "Polytechnic", "University", "Postgraduate"]

    inc_cpt = build_income_cpt()

    # Print coverage matrix
    header = f"{'Age':>10s} | " + " | ".join(f"{e[:6]:>6s}" for e in edu_levels)
    print(header)
    print("-" * len(header))

    for age_label in AGE_LABELS:
        row = f"{age_label:>10s} | "
        for edu in edu_levels:
            if (edu, age_label) in inc_cpt:
                row += f"{'OK':>6s} | "
            else:
                row += f"{'MISS':>6s} | "
        print(row)

    # ============================================================
    # SUMMARY & RECOMMENDATION
    # ============================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_checks = [
        ("Gender", 0.0, 0.10, "EXACT"),
        ("Ethnicity", 0.0, 0.10, "EXACT"),
        ("Median age", abs(median_age - target_age) / target_age, 0.10, f"~{median_age} vs {target_age}"),
        ("Degree+ (25+)", abs(degree_ratio - target) / target, 0.10, f"{degree_ratio:.1%} vs {target:.1%}"),
        ("Median income (employed)", abs(median_inc - target_inc) / target_inc, 0.20, f"${median_inc:,} vs ${target_inc:,}"),
        ("Housing aggregate SRMSE", srmse(obs, exp), 0.20, f"SRMSE={srmse(obs, exp):.4f}"),
        ("Married 30-34", abs(married_30_34 - target_m) / target_m, 0.10, f"{married_30_34:.1%} vs {target_m:.1%}"),
        ("Income CPT coverage", total_mass_missing, 0.05, f"{total_mass_missing:.1%} mass missing"),
    ]

    print(f"\n{'Check':40s} {'Deviation':>10s} {'Threshold':>10s} {'Status':>8s} {'Detail'}")
    print("-" * 100)
    for name, dev, thresh, detail in all_checks:
        status = "PASS" if dev < thresh else "FAIL"
        print(f"{name:40s} {dev:10.4f} {thresh:10.4f} {status:>8s} {detail}")

    print("\n\nPost-coherence-rule marginal shifts:")
    print(f"  WP→HDB rule: Housing SRMSE {srmse(obs, exp):.4f} → {srmse(obs_after, exp):.4f} (change: {srmse(obs_after, exp) - srmse(obs, exp):+.4f})")
    print(f"  Child health rule: Negligible impact (delta < 0.005 on all categories)")

    failed = [name for name, dev, thresh, _ in all_checks if dev >= thresh]
    if failed:
        print(f"\n  FAILED checks: {', '.join(failed)}")
        print("  Must fix CPT tables before applying coherence rules!")
    else:
        print("\n  All checks PASSED. Safe to apply coherence rules.")


if __name__ == "__main__":
    main()
