"""
Script 41: Generate insurance profiles for all agents.

Reads CPT from data/cpt/insurance_v1.yaml, generates 17 insurance fields
for each of the 172,173 agents, writes to agent_insurance table.

Usage:
    python3 scripts/41_generate_insurance.py [--version v1.0] [--dry-run] [--limit N]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import math
import logging
import time
import json
import yaml
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CPT_PATH = PROJECT_ROOT / "data" / "cpt" / "insurance_v1.yaml"

SUPABASE_URL = "https://rndfpyuuredtqncegygi.supabase.co"
SUPABASE_SERVICE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIs"
    "ImlhdCI6MTc3MzA4Nzk0NiwiZXhwIjoyMDg4NjYzOTQ2fQ."
    "EMjLfr3N8RDpBPkVftYKCg1Pf6h4rOj8xfCXSuJIxQI"
)


# ============================================================
# CPT LOADER
# ============================================================

def load_cpt(path: Path) -> dict:
    """Load CPT yaml file."""
    with open(path) as f:
        cpt = yaml.safe_load(f)
    logger.info(f"Loaded CPT from {path} (version {cpt['meta']['version']})")
    return cpt


# ============================================================
# AGE GROUP MAPPING
# ============================================================

def age_to_5yr(age: int) -> str:
    """Map age to 5-year band string used in CPT."""
    if age < 5: return "0-4"
    if age < 10: return "5-9"
    if age < 15: return "10-14"
    if age < 20: return "15-19"
    if age < 25: return "20-24"
    if age < 30: return "25-29"
    if age < 35: return "30-34"
    if age < 40: return "35-39"
    if age < 45: return "40-44"
    if age < 50: return "45-49"
    if age < 55: return "50-54"
    if age < 60: return "55-59"
    if age < 65: return "60-64"
    if age < 70: return "65-69"
    return "70+"


def age_to_broad(age: int) -> str:
    """Map age to broad band for CPTs that use coarser grouping."""
    if age < 20: return "0-19"
    if age < 25: return "20-24"
    if age < 30: return "25-29"
    if age < 35: return "30-34"
    if age < 40: return "35-39"
    if age < 45: return "40-44"
    if age < 50: return "45-49"
    if age < 55: return "50-54"
    if age < 60: return "55-59"
    if age < 65: return "60-64"
    if age < 70: return "65-69"
    return "70+"


def age_to_rider_band(age: int) -> str:
    if age < 20: return "0-19"
    if age < 35: return "20-34"
    if age < 50: return "35-49"
    if age < 60: return "50-59"
    if age < 70: return "60-69"
    return "70+"


def age_to_channel_band(age: int) -> str:
    if age < 25: return "0-24"
    if age < 35: return "25-34"
    if age < 50: return "35-49"
    if age < 65: return "50-64"
    return "65+"


def age_to_attitude_band(age: int) -> str:
    if age < 20: return "0-19"
    if age < 30: return "20-29"
    if age < 45: return "30-44"
    if age < 60: return "45-59"
    return "60+"


def age_to_cpf_band(age: int) -> str:
    if age <= 20: return "0-20"
    if age <= 25: return "20-25"
    if age <= 30: return "25-30"
    if age <= 35: return "30-35"
    if age <= 40: return "35-40"
    if age <= 45: return "40-45"
    if age <= 50: return "45-50"
    if age <= 55: return "50-55"
    if age <= 60: return "55-60"
    return "60+"


def age_to_hosp_band(age: int) -> str:
    if age < 5: return "0-4"
    if age < 15: return "5-14"
    if age < 25: return "15-24"
    if age < 35: return "25-34"
    if age < 45: return "35-44"
    if age < 55: return "45-54"
    if age < 65: return "55-64"
    if age < 75: return "65-74"
    return "75+"


def income_tier(income: int) -> str:
    """Map monthly income to tier for CPT lookup."""
    if income < 1500: return "low"
    if income < 3000: return "low_mid"
    if income < 5000: return "mid"
    if income < 8000: return "mid_high"
    return "high"


def income_tier_3(income: int) -> str:
    """3-level income tier for attitude CPT."""
    if income < 3000: return "low"
    if income < 8000: return "mid"
    return "high"


def ip_tier_income_housing_key(income: int, housing: str) -> str:
    """Map income+housing to ip_tier CPT key."""
    tier = income_tier(income)
    if tier == "high" and housing in ("Condo", "Landed"):
        return "high_private"
    if tier == "high":
        return "high_hdb"
    if tier == "mid_high":
        return "mid_high"
    if tier == "mid":
        return "mid"
    if tier == "low_mid":
        return "low_mid"
    return "low"


# ============================================================
# SAMPLING HELPERS
# ============================================================

def sample_categorical(probs: dict, rng: np.random.Generator) -> str:
    """Sample from a categorical distribution {label: prob}."""
    labels = list(probs.keys())
    p = np.array([probs[k] for k in labels], dtype=float)
    p = p / p.sum()  # renormalize
    return labels[rng.choice(len(labels), p=p)]


def sample_lognormal(mean: float, cv: float, rng: np.random.Generator) -> int:
    """Sample from lognormal with given mean and coefficient of variation."""
    if mean <= 0:
        return 0
    sigma2 = np.log(1 + cv ** 2)
    mu = np.log(mean) - sigma2 / 2
    val = rng.lognormal(mu, np.sqrt(sigma2))
    return max(0, int(round(val)))


# ============================================================
# CORE GENERATION: per-agent insurance profile
# ============================================================

def calibrate_cpt(cpt: dict, agents: list[dict]) -> dict:
    """Auto-calibrate by_age rates so weighted marginal hits target.

    Computes population-weighted marginal for each field, then applies
    a uniform scale factor to all by_age rates.
    """
    import copy
    cpt = copy.deepcopy(cpt)
    targets = cpt["marginal_targets"]

    # Count agents per age band
    age_counts_5yr = {}
    for a in agents:
        band = age_to_5yr(a["age"])
        age_counts_5yr[band] = age_counts_5yr.get(band, 0) + 1
    n = len(agents)

    # Calibrate boolean fields with by_age rates
    for field, target_key in [
        ("has_whole_life", "has_whole_life"),
        ("has_ci", "has_ci"),
        ("has_term_life", "has_term_life"),
    ]:
        target = targets[target_key]
        rates = cpt[field]["conditions"]["by_age"]
        # Compute current weighted marginal
        weighted = sum(rates.get(band, 0) * count for band, count in age_counts_5yr.items()) / n
        if weighted > 0:
            scale = target / weighted
            for band in rates:
                rates[band] = min(0.95, rates[band] * scale)
            logger.info(f"  Calibrated {field}: weighted {weighted:.4f} → target {target}, scale={scale:.4f}")

    # Calibrate has_ip (has income modifier — compute effective rate per agent)
    ip_rates = cpt["has_ip"]["conditions"]["by_age"]
    ip_inc_mod = cpt["has_ip"]["conditions"]["income_modifier"]

    # Compute actual weighted marginal including income modifier
    weighted_ip_sum = 0
    for a in agents:
        age5 = age_to_5yr(a["age"])
        base = ip_rates.get(age5, 0.71)
        inc = a.get("monthly_income", 0) or 0
        inc3 = income_tier_3(inc)
        mod = ip_inc_mod.get(inc3, 1.0)
        weighted_ip_sum += min(0.98, base * mod)
    weighted_ip = weighted_ip_sum / n
    if weighted_ip > 0:
        ip_target = targets["has_ip"]
        scale = ip_target / weighted_ip
        for band in ip_rates:
            ip_rates[band] = min(0.98, ip_rates[band] * scale)
        logger.info(f"  Calibrated has_ip: weighted {weighted_ip:.4f} → target {ip_target}, scale={scale:.4f}")

    # Calibrate ip_tier: compute weighted tier distribution from agents with IP
    # Count agents by income_tier_housing_key
    income_housing_counts = {}
    for a in agents:
        inc = a.get("monthly_income", 0) or 0
        housing = a.get("housing_type", "HDB_4")
        key = ip_tier_income_housing_key(inc, housing)
        income_housing_counts[key] = income_housing_counts.get(key, 0) + 1

    tier_targets = targets["ip_tier_given_ip"]
    tier_conds = cpt["ip_tier"]["conditions"]["by_income_housing"]

    # Compute current weighted tier marginal
    total_w = sum(income_housing_counts.values())
    weighted_tier = {}
    for tier in ["private", "A", "B1", "standard"]:
        weighted_tier[tier] = sum(
            tier_conds.get(key, {"private": 0.56, "A": 0.28, "B1": 0.14, "standard": 0.02}).get(tier, 0) * count
            for key, count in income_housing_counts.items()
        ) / total_w

    logger.info(f"  IP tier before calibration: {weighted_tier}")

    # Simple adjustment: shift mass toward/away from each tier
    for key in tier_conds:
        probs = tier_conds[key]
        # Scale each tier probability to reduce gap to target
        for tier in ["private", "A", "B1", "standard"]:
            if weighted_tier[tier] > 0:
                adj = tier_targets[tier] / weighted_tier[tier]
                probs[tier] = probs.get(tier, 0) * adj
        # Renormalize
        total = sum(probs.values())
        if total > 0:
            for tier in probs:
                probs[tier] /= total

    logger.info(f"  Calibrated ip_tier conditional probabilities")

    # Calibrate insurance_attitude: compute weighted marginal from income distribution
    inc3_counts = {}
    for a in agents:
        inc = a.get("monthly_income", 0) or 0
        inc3 = income_tier_3(inc)
        inc3_counts[inc3] = inc3_counts.get(inc3, 0) + 1

    att_targets = targets["insurance_attitude"]
    att_by_income = cpt["insurance_attitude"]["conditions"]["by_income"]

    # Compute current weighted attitude marginal (before age modifier)
    weighted_att = {}
    for att in att_targets:
        weighted_att[att] = sum(
            att_by_income.get(inc3, cpt["insurance_attitude"]["marginal"]).get(att, 0) * count
            for inc3, count in inc3_counts.items()
        ) / n

    logger.info(f"  Attitude before calibration: {weighted_att}")

    # Adjust the by_income tables to better match targets
    for inc3 in att_by_income:
        probs = att_by_income[inc3]
        for att in att_targets:
            if weighted_att.get(att, 0) > 0:
                adj = att_targets[att] / weighted_att[att]
                # Dampen adjustment (don't fully correct, age modifier adds noise)
                adj = 1.0 + (adj - 1.0) * 0.7
                probs[att] = probs.get(att, 0) * adj
        total = sum(probs.values())
        if total > 0:
            for att in probs:
                probs[att] /= total

    logger.info(f"  Calibrated insurance_attitude by_income tables")

    return cpt


def generate_insurance_profile(agent: dict, cpt: dict, rng: np.random.Generator) -> dict:
    """Generate all 17 insurance fields for one agent."""
    age = agent["age"]
    gender = agent.get("gender", "M")
    income = agent.get("monthly_income", 0) or 0
    housing = agent.get("housing_type", "HDB_4")
    marital = agent.get("marital_status", "Single")
    health = agent.get("health_status", "Healthy")
    life_phase = agent.get("life_phase", "establishment")
    age5 = age_to_5yr(age)

    profile = {}

    # ----- 1. has_medishield_life -----
    profile["has_medishield_life"] = True

    # ----- 2. has_ip -----
    ip_cpt = cpt["has_ip"]["conditions"]
    base_ip_rate = ip_cpt["by_age"].get(age5, 0.71)
    inc_mod = ip_cpt["income_modifier"]
    inc3 = income_tier_3(income)
    modifier = inc_mod.get(inc3, 1.0)
    ip_prob = min(0.98, base_ip_rate * modifier)
    has_ip = rng.random() < ip_prob
    profile["has_ip"] = has_ip

    # ----- 3. ip_tier -----
    if has_ip:
        tier_key = ip_tier_income_housing_key(income, housing)
        tier_probs = cpt["ip_tier"]["conditions"]["by_income_housing"].get(
            tier_key, {"private": 0.56, "A": 0.28, "B1": 0.14, "standard": 0.02}
        )
        profile["ip_tier"] = sample_categorical(tier_probs, rng)
    else:
        profile["ip_tier"] = None

    # ----- 4. has_rider -----
    if has_ip:
        rider_band = age_to_rider_band(age)
        rider_rate = cpt["has_rider"]["conditions"]["by_age"].get(rider_band, 0.67)
        profile["has_rider"] = rng.random() < rider_rate
    else:
        profile["has_rider"] = False

    # ----- 5. ip_insurer -----
    if has_ip:
        profile["ip_insurer"] = sample_categorical(cpt["ip_insurer"]["distribution"], rng)
    else:
        profile["ip_insurer"] = None

    # ----- 6. has_whole_life -----
    wol_rate = cpt["has_whole_life"]["conditions"]["by_age"].get(age5, 0.336)
    profile["has_whole_life"] = rng.random() < wol_rate

    # ----- 7. has_term_life -----
    term_cpt = cpt["has_term_life"]["conditions"]
    base_term = term_cpt["by_age"].get(age5, 0.17)
    marital_mod = term_cpt["marital_modifier"].get(marital, 1.0)
    term_prob = min(0.95, base_term * marital_mod)
    profile["has_term_life"] = rng.random() < term_prob

    # ----- 8. has_ci -----
    ci_rate = cpt["has_ci"]["conditions"]["by_age"].get(age5, 0.306)
    profile["has_ci"] = rng.random() < ci_rate

    # ----- 9. term_life_coverage -----
    if profile["has_term_life"]:
        mean_cov = cpt["term_life_coverage"]["mean_by_age"].get(age5, 300000)
        cv = cpt["term_life_coverage"]["cv"]
        elasticity = cpt["term_life_coverage"]["income_elasticity"]
        # Income adjustment: scale by (income / median)^elasticity
        median_income = 4500  # approximate SG median
        if income > 0:
            inc_factor = (income / median_income) ** elasticity
        else:
            inc_factor = 0.5
        adjusted_mean = mean_cov * inc_factor
        profile["term_life_coverage"] = sample_lognormal(adjusted_mean, cv, rng)
    else:
        profile["term_life_coverage"] = 0

    # ----- 10. ci_coverage -----
    if profile["has_ci"]:
        ci_means = cpt["ci_coverage"]["mean_by_age_gender"]
        age_key = age5
        if age_key not in ci_means:
            # Fall back to closest
            age_key = "30-34"
        gender_means = ci_means.get(age_key, {"M": 200000, "F": 180000})
        mean_ci = gender_means.get(gender, gender_means.get("M", 200000))
        cv = cpt["ci_coverage"]["cv"]
        elasticity = cpt["ci_coverage"]["income_elasticity"]
        median_income = 4500
        if income > 0:
            inc_factor = (income / median_income) ** elasticity
        else:
            inc_factor = 0.5
        adjusted_mean = mean_ci * inc_factor
        profile["ci_coverage"] = sample_lognormal(adjusted_mean, cv, rng)
    else:
        profile["ci_coverage"] = 0

    # ----- 11. insurance_attitude -----
    att_cpt = cpt["insurance_attitude"]["conditions"]
    inc3 = income_tier_3(income)
    base_probs = dict(att_cpt["by_income"].get(inc3, cpt["insurance_attitude"]["marginal"]))
    # Apply age modifier
    age_band = age_to_attitude_band(age)
    age_mod = att_cpt["age_modifier"].get(age_band, {})
    for k, v in age_mod.items():
        if k in base_probs:
            base_probs[k] *= v
    profile["insurance_attitude"] = sample_categorical(base_probs, rng)

    # ----- 12. protection_gap_awareness -----
    att = profile["insurance_attitude"]
    gap_probs = cpt["protection_gap_awareness"]["conditions"]["by_attitude"].get(
        att, cpt["protection_gap_awareness"]["marginal"]
    )
    profile["protection_gap_awareness"] = sample_categorical(gap_probs, rng)

    # ----- 13. preferred_channel -----
    ch_band = age_to_channel_band(age)
    ch_probs = cpt["preferred_channel"]["conditions"]["by_age"].get(
        ch_band, cpt["preferred_channel"]["marginal"]
    )
    profile["preferred_channel"] = sample_categorical(ch_probs, rng)

    # ----- 14. last_life_event_trigger -----
    trigger_probs = cpt["last_life_event_trigger"]["conditions"]["by_life_phase"].get(
        life_phase, {"none_recent": 1.0}
    )
    profile["last_life_event_trigger"] = sample_categorical(trigger_probs, rng)

    # ----- 15. medisave_balance -----
    ms_cpt = cpt["medisave_balance"]
    cpf_band = age_to_cpf_band(age)
    avg_cpf = ms_cpt["avg_total_cpf_by_age"].get(cpf_band, 100000)
    ms_pct = ms_cpt["medisave_pct_by_age"].get(cpf_band, 0.23)
    mean_ms = avg_cpf * ms_pct
    bhs_cap = ms_cpt["bhs_cap"]
    ms_val = sample_lognormal(mean_ms, ms_cpt["cv"], rng)
    profile["medisave_balance"] = min(ms_val, bhs_cap)

    # ----- 16. annual_hospitalization_freq -----
    hosp_cpt = cpt["annual_hospitalization_freq"]
    hosp_band = age_to_hosp_band(age)
    base_rate = hosp_cpt["by_age"].get(hosp_band, 0.08)
    h_mod = hosp_cpt["health_modifier"].get(health, 1.0)
    # Sample from Poisson-like (use rate directly for expected freq)
    profile["annual_hospitalization_freq"] = round(base_rate * h_mod, 3)

    # ----- 17. monthly_insurance_spend -----
    # Derived from product holdings
    spend = 0
    if profile["has_ip"]:
        # IP premium varies hugely by age and tier
        tier = profile["ip_tier"] or "B1"
        tier_mult = {"private": 1.8, "A": 1.2, "B1": 0.8, "standard": 0.5}
        # Base IP premium by age (very rough annual → monthly)
        if age < 30:
            base_ip_monthly = 25
        elif age < 40:
            base_ip_monthly = 35
        elif age < 50:
            base_ip_monthly = 60
        elif age < 60:
            base_ip_monthly = 110
        elif age < 70:
            base_ip_monthly = 200
        else:
            base_ip_monthly = 350
        ip_premium = base_ip_monthly * tier_mult.get(tier, 1.0)
        if profile["has_rider"]:
            ip_premium *= 1.5
        spend += ip_premium

    if profile["has_term_life"]:
        # Term: ~$2-4 per $100K coverage per month for young, more for old
        cov_100k = profile["term_life_coverage"] / 100000
        if age < 40:
            rate = 2.5
        elif age < 50:
            rate = 4.0
        elif age < 60:
            rate = 8.0
        else:
            rate = 15.0
        spend += cov_100k * rate

    if profile["has_whole_life"]:
        # WoL: $150-400/month typical (saving + protection)
        if age < 30:
            spend += 120
        elif age < 50:
            spend += 200
        else:
            spend += 250

    if profile["has_ci"] and not profile["has_whole_life"]:
        # Standalone CI: ~$3-8 per $100K per month
        ci_100k = profile["ci_coverage"] / 100000
        if age < 40:
            rate = 3.0
        elif age < 50:
            rate = 5.0
        else:
            rate = 10.0
        spend += ci_100k * rate

    # Add some noise (±20%)
    if spend > 0:
        spend *= rng.uniform(0.8, 1.2)
    profile["monthly_insurance_spend"] = max(0, int(round(spend)))

    return profile


# ============================================================
# MARGINAL VALIDATION
# ============================================================

def validate_marginals(df: pd.DataFrame, cpt: dict) -> dict:
    """Check generated distribution against marginal targets."""
    targets = cpt["marginal_targets"]
    results = {}
    n = len(df)

    def check(name, actual, target, tol=0.02):
        diff = abs(actual - target)
        ok = diff <= tol
        results[name] = {"actual": round(actual, 4), "target": target, "diff": round(diff, 4), "pass": ok}
        status = "PASS" if ok else "FAIL"
        logger.info(f"  {status} {name}: actual={actual:.4f} target={target} diff={diff:.4f}")
        return ok

    logger.info("=" * 60)
    logger.info("MARGINAL VALIDATION")
    logger.info("=" * 60)

    all_pass = True
    all_pass &= check("has_ip", df["has_ip"].mean(), targets["has_ip"])
    all_pass &= check("has_term_life", df["has_term_life"].mean(), targets["has_term_life"], tol=0.015)
    all_pass &= check("has_whole_life", df["has_whole_life"].mean(), targets["has_whole_life"], tol=0.015)
    all_pass &= check("has_ci", df["has_ci"].mean(), targets["has_ci"], tol=0.015)

    # IP tier distribution (among IP holders)
    ip_holders = df[df["has_ip"]]
    if len(ip_holders) > 0:
        for tier, target in targets["ip_tier_given_ip"].items():
            actual = (ip_holders["ip_tier"] == tier).mean()
            all_pass &= check(f"ip_tier_{tier}", actual, target, tol=0.03)

    # Rider rate among IP holders
    if len(ip_holders) > 0:
        rider_rate = ip_holders["has_rider"].mean()
        all_pass &= check("has_rider_given_ip", rider_rate, targets["has_rider_given_ip"])

    # Attitude distribution
    for att, target in targets["insurance_attitude"].items():
        actual = (df["insurance_attitude"] == att).mean()
        all_pass &= check(f"attitude_{att}", actual, target, tol=0.03)

    results["all_pass"] = all_pass
    logger.info(f"Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    return results


# ============================================================
# SUPABASE UPLOAD
# ============================================================

def upload_to_supabase(records: list[dict], version_id: str, dry_run: bool = False):
    """Batch upsert insurance records to Supabase."""
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Add version_id to each record
    for r in records:
        r["version_id"] = version_id

    total = len(records)
    batch_size = 500
    batches = math.ceil(total / batch_size)
    success = 0
    errors = 0

    logger.info(f"Uploading {total:,} records in {batches} batches")

    for i in range(batches):
        start = i * batch_size
        end = min(start + batch_size, total)
        batch = records[start:end]

        if dry_run:
            success += len(batch)
            continue

        try:
            sb.table("agent_insurance").upsert(batch).execute()
            success += len(batch)
            if (i + 1) % 50 == 0 or i == batches - 1:
                logger.info(f"  Batch {i+1}/{batches}: {success:,}/{total:,}")
        except Exception as e:
            logger.error(f"  Batch {i+1} failed: {e}")
            # Retry with smaller batches
            for j in range(0, len(batch), 50):
                mini = batch[j:j+50]
                try:
                    sb.table("agent_insurance").upsert(mini).execute()
                    success += len(mini)
                except Exception as e2:
                    errors += len(mini)
                    logger.error(f"  Mini-batch failed: {e2}")

    logger.info(f"Upload complete: {success:,} success, {errors:,} errors")
    return success, errors


def create_version_record(cpt: dict, version: str, description: str, dry_run: bool = False) -> str:
    """Create domain_versions record, return version_id."""
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    record = {
        "domain": "insurance",
        "version": version,
        "is_active": False,
        "status": "generating",
        "description": description,
        "research_doc": "insurance_profile_research_v1.md",
        "data_sources": {
            "PGS_2022": ["Table 58", "Table 60", "Table 61", "Table 64", "Table 66", "Table 67", "Table 68", "Table 69", "Section 16"],
            "MOH_2025": ["IP coverage 71%", "IP rider 67%", "IP tier distribution"],
            "CPF_AR_2021": ["Section 15.4.5 CPF savings by age"],
            "CPF_Board_2025Q3": ["MediSave total S$148.7bn"],
        },
        "generation_params": {
            "cpt_file": "data/cpt/insurance_v1.yaml",
            "marginal_targets": cpt["marginal_targets"],
            "seed": 42,
        },
        "cpt_file": "data/cpt/insurance_v1.yaml",
    }

    if dry_run:
        import uuid
        vid = str(uuid.uuid4())
        logger.info(f"[DRY RUN] Would create version record: {version} → {vid}")
        return vid

    # Try insert first, if conflict (already exists), fetch existing
    try:
        result = sb.table("domain_versions").insert(record).execute()
        vid = result.data[0]["id"]
        logger.info(f"Created domain_versions record: {version} → {vid}")
    except Exception:
        # Already exists — fetch and update
        existing = sb.table("domain_versions").select("id").eq("domain", "insurance").eq("version", version).execute()
        vid = existing.data[0]["id"]
        sb.table("domain_versions").update({
            "status": "generating",
            "generation_params": record["generation_params"],
            "data_sources": record["data_sources"],
        }).eq("id", vid).execute()
        logger.info(f"Reusing existing domain_versions record: {version} → {vid}")
    return vid


def update_version_status(version_id: str, status: str, agent_count: int = 0,
                          validation: dict = None, dry_run: bool = False):
    """Update version record status."""
    if dry_run:
        logger.info(f"[DRY RUN] Would update version {version_id}: status={status}")
        return

    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    update = {"status": status}
    if agent_count:
        update["agent_count"] = agent_count
    if validation:
        # Convert numpy types to native Python for JSON serialization
        def to_native(obj):
            if isinstance(obj, dict):
                return {k: to_native(v) for k, v in obj.items()}
            if isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            if isinstance(obj, (np.integer, int)):
                return int(obj)
            if isinstance(obj, (np.floating, float)):
                return float(obj)
            return obj
        update["validation_result"] = to_native(validation)

    sb.table("domain_versions").update(update).eq("id", version_id).execute()
    logger.info(f"Updated version {version_id}: status={status}")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Generate insurance profiles for agents")
    parser.add_argument("--version", default="v1.0", help="Version label (default: v1.0)")
    parser.add_argument("--description", default="Initial insurance profiles based on PGS 2022 + MOH 2025",
                        help="Version description")
    parser.add_argument("--dry-run", action="store_true", help="Generate but don't upload")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of agents (0=all)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    t0 = time.time()

    # 1. Load CPT
    cpt = load_cpt(CPT_PATH)

    # 2. Load all agents from Supabase
    logger.info("Loading agents from Supabase...")
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Paginated fetch (Supabase limit = 1000 per request)
    all_agents = []
    page_size = 1000
    offset = 0
    fields = "agent_id,age,gender,ethnicity,monthly_income,housing_type,marital_status,health_status,life_phase,education_level"

    while True:
        result = sb.table("agents").select(fields).range(offset, offset + page_size - 1).execute()
        batch = result.data
        if not batch:
            break
        all_agents.extend(batch)
        offset += page_size
        if len(all_agents) % 50000 == 0:
            logger.info(f"  Loaded {len(all_agents):,} agents...")

    logger.info(f"Loaded {len(all_agents):,} agents in {time.time()-t0:.1f}s")

    if args.limit > 0:
        all_agents = all_agents[:args.limit]
        logger.info(f"Limited to {len(all_agents):,} agents")

    # 2b. Calibrate CPT rates against actual population age distribution
    logger.info("Calibrating CPT rates against population distribution...")
    cpt = calibrate_cpt(cpt, all_agents)

    # 3. Create version record
    version_id = create_version_record(cpt, args.version, args.description, dry_run=args.dry_run)

    # 4. Generate insurance profiles
    logger.info(f"Generating insurance profiles (seed={args.seed})...")
    rng = np.random.default_rng(args.seed)
    t1 = time.time()

    records = []
    for i, agent in enumerate(all_agents):
        profile = generate_insurance_profile(agent, cpt, rng)
        profile["agent_id"] = agent["agent_id"]
        records.append(profile)

        if (i + 1) % 50000 == 0:
            logger.info(f"  Generated {i+1:,}/{len(all_agents):,}")

    gen_time = time.time() - t1
    logger.info(f"Generated {len(records):,} profiles in {gen_time:.1f}s ({len(records)/gen_time:.0f} agents/sec)")

    # 5. Validate marginals
    df = pd.DataFrame(records)
    validation = validate_marginals(df, cpt)

    # 6. Upload
    update_version_status(version_id, "validating", agent_count=len(records),
                          validation=validation, dry_run=args.dry_run)

    if not args.dry_run:
        logger.info("Uploading to Supabase...")
        t2 = time.time()
        success, errors = upload_to_supabase(records, version_id)
        logger.info(f"Upload done in {time.time()-t2:.1f}s")

        final_status = "active" if validation.get("all_pass") else "validating"
        update_version_status(version_id, final_status)
    else:
        logger.info("[DRY RUN] Skipping upload")
        # Print sample records
        logger.info("Sample records:")
        for r in records[:3]:
            logger.info(f"  {json.dumps({k: v for k, v in r.items() if k != 'agent_id'}, indent=2)}")

    # 7. Summary statistics
    logger.info("=" * 60)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total agents: {len(df):,}")
    logger.info(f"has_ip: {df['has_ip'].mean():.1%}")
    logger.info(f"has_term_life: {df['has_term_life'].mean():.1%}")
    logger.info(f"has_whole_life: {df['has_whole_life'].mean():.1%}")
    logger.info(f"has_ci: {df['has_ci'].mean():.1%}")
    logger.info(f"has_rider (of IP): {df[df['has_ip']]['has_rider'].mean():.1%}")

    ip_holders = df[df["has_ip"]]
    if len(ip_holders) > 0:
        logger.info(f"IP tier distribution:")
        for tier in ["private", "A", "B1", "standard"]:
            pct = (ip_holders["ip_tier"] == tier).mean()
            logger.info(f"  {tier}: {pct:.1%}")

    logger.info(f"Avg term_life_coverage (holders): ${df[df['has_term_life']]['term_life_coverage'].mean():,.0f}")
    logger.info(f"Avg ci_coverage (holders): ${df[df['has_ci']]['ci_coverage'].mean():,.0f}")
    logger.info(f"Avg monthly_spend (all): ${df['monthly_insurance_spend'].mean():,.0f}")
    logger.info(f"Avg medisave_balance: ${df['medisave_balance'].mean():,.0f}")

    logger.info(f"Attitude distribution:")
    for att in ["proactive", "adequate", "passive", "resistant", "unaware"]:
        pct = (df["insurance_attitude"] == att).mean()
        logger.info(f"  {att}: {pct:.1%}")

    total_time = time.time() - t0
    logger.info(f"\nTotal time: {total_time:.1f}s")
    logger.info(f"Version: {args.version} → {version_id}")


if __name__ == "__main__":
    main()
