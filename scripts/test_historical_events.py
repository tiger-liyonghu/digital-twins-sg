"""
Historical Event Test Suite for Singapore Digital Twin
=====================================================

Uses real Singapore events (2020-2025) to validate the simulation engine.
Each test injects a specific historical event, runs the simulation, and
measures how agents respond across all three decision layers.

Test Categories:
  A. Policy / Government  — GST hike, CPF changes, BTO launches
  B. Economic / Market    — Interest rate moves, recession, tech layoffs
  C. Infrastructure       — MRT line openings, ERP changes
  D. Health / Crisis      — COVID lockdown, dengue outbreak
  E. Social / Demographic — Retirement age raise, NS policy change

Usage:
  python scripts/test_historical_events.py
"""

import sys, os, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import date
from collections import Counter

from engine.pipeline.tick_manager import SimulationRunner
from engine.pipeline.collectors.base import ExternalEvent


# ============================================================
# TEST POPULATION: 500 representative agents
# ============================================================
def build_test_population(n=500, seed=42):
    """Build a diverse test population reflecting Singapore demographics."""
    rng = np.random.default_rng(seed)

    ages = rng.choice(range(0, 90), n, p=_sg_age_dist())
    genders = rng.choice(["M", "F"], n, p=[0.51, 0.49])
    ethnicities = rng.choice(
        ["Chinese", "Malay", "Indian", "Others"], n,
        p=[0.742, 0.134, 0.092, 0.032])

    # Life phase from age
    def age_to_phase(age):
        if age <= 6: return "dependence"
        if age <= 12: return "growth"
        if age <= 16: return "adolescence"
        if age <= 20: return "ns_service"  # simplified
        if age <= 35: return "establishment"
        if age <= 50: return "bearing"
        if age <= 62: return "release"
        if age <= 74: return "retirement_early"
        if age <= 84: return "decline"
        return "end_of_life"

    # Housing type by age/income correlation
    def pick_housing(age, income):
        if age < 25 or income < 2000:
            return rng.choice(["HDB_3", "HDB_4"], p=[0.6, 0.4])
        if income > 8000:
            return rng.choice(["HDB_5_EC", "Condo", "Landed"], p=[0.4, 0.45, 0.15])
        return rng.choice(["HDB_3", "HDB_4", "HDB_5_EC", "Condo"],
                          p=[0.15, 0.40, 0.30, 0.15])

    incomes = []
    for age in ages:
        if age < 18:
            incomes.append(0)
        elif age > 65:
            incomes.append(int(rng.choice([0, 1500, 2500, 4000], p=[0.3, 0.3, 0.25, 0.15])))
        else:
            incomes.append(int(rng.lognormal(8.2, 0.6)))  # median ~3600

    df = pd.DataFrame({
        "agent_id": [f"T{i:04d}" for i in range(n)],
        "age": ages,
        "gender": genders,
        "ethnicity": ethnicities,
        "residency_status": rng.choice(["Citizen", "PR", "EP"], n, p=[0.65, 0.20, 0.15]),
        "planning_area": rng.choice(
            ["Bedok", "Tampines", "Jurong West", "Woodlands", "Ang Mo Kio",
             "Toa Payoh", "Bukit Merah", "Hougang", "Sengkang", "Punggol",
             "Clementi", "Bishan", "Marine Parade", "Orchard"],
            n),
        "housing_type": [pick_housing(a, i) for a, i in zip(ages, incomes)],
        "education_level": rng.choice(
            ["Primary", "Secondary", "Post_Secondary", "Polytechnic", "University", "Postgraduate"],
            n, p=[0.05, 0.15, 0.15, 0.20, 0.35, 0.10]),
        "monthly_income": incomes,
        "marital_status": [
            "Single" if a < 22 else rng.choice(["Single", "Married", "Divorced"], p=[0.35, 0.55, 0.10])
            for a in ages
        ],
        "num_children": [
            0 if a < 25 else int(rng.choice([0,1,2,3], p=[0.30, 0.35, 0.25, 0.10]))
            for a in ages
        ],
        "life_phase": [age_to_phase(a) for a in ages],
        "health_status": rng.choice(
            ["Healthy", "Chronic_Mild", "Chronic_Severe", "Disabled"],
            n, p=[0.75, 0.15, 0.07, 0.03]),
        "ns_status": [
            "Serving_NSF" if (g == "M" and 18 <= a <= 20) else
            "Active_NSmen" if (g == "M" and 20 < a < 40) else
            "Completed" if (g == "M" and a >= 40) else
            "Not_Applicable"
            for g, a in zip(genders, ages)
        ],
        "is_alive": True,
        "cpf_oa": [max(0, int(a * rng.integers(500, 4000))) if a >= 18 else 0 for a in ages],
        "cpf_sa": [max(0, int(a * rng.integers(200, 1500))) if a >= 18 else 0 for a in ages],
        "cpf_ma": [max(0, int(a * rng.integers(100, 800))) if a >= 18 else 0 for a in ages],
        "smoking": rng.choice([True, False], n, p=[0.12, 0.88]),
        "job_status": [
            "student" if a < 18 else
            "ns" if (g == "M" and 18 <= a <= 20) else
            "retired" if a > 65 else
            rng.choice(["employed", "unemployed", "self_employed"], p=[0.88, 0.05, 0.07])
            for g, a in zip(genders, ages)
        ],
        "has_vehicle": rng.choice([True, False], n, p=[0.12, 0.88]),
        "commute_mode": rng.choice(["MRT", "Bus", "Car", "Walk"], n, p=[0.45, 0.30, 0.15, 0.10]),
        "industry": rng.choice(
            ["Finance", "ICT", "Manufacturing", "Healthcare", "Education",
             "Retail", "F&B", "Construction", "Public_Admin", "Transport"],
            n),
    })
    return df


def _sg_age_dist():
    """Approximate Singapore 2020 age distribution (0-89)."""
    # Simplified: working-age bulge, low birth rate, aging population
    raw = []
    for a in range(90):
        if a < 5: w = 0.8
        elif a < 15: w = 1.0
        elif a < 25: w = 1.3
        elif a < 35: w = 1.5
        elif a < 45: w = 1.4
        elif a < 55: w = 1.5
        elif a < 65: w = 1.2
        elif a < 75: w = 0.8
        elif a < 85: w = 0.4
        else: w = 0.15
        raw.append(w)
    total = sum(raw)
    return [r / total for r in raw]


# ============================================================
# HISTORICAL EVENTS LIBRARY
# ============================================================
HISTORICAL_EVENTS = {

    # ---- A. POLICY / GOVERNMENT ----

    "A1_GST_9pct_2024": {
        "name": "GST Hike 8% → 9% (Jan 2024)",
        "date": "2024-01-01",
        "description": "Singapore raised GST from 8% to 9%, completing the planned two-step increase from 7%.",
        "events": [
            ExternalEvent("gov", "policy_tax",
                {"title": "GST increased from 8% to 9%",
                 "detail": "Second and final phase of GST hike takes effect. Government provides GST vouchers and Assurance Package for lower-income households.",
                 "gst_rate": 0.09, "prev_rate": 0.08},
                relevance_tags=[]),  # affects everyone
        ],
        "expected": {
            "affected_groups": "All agents, especially lower-income (< $3000/month)",
            "expected_reactions": "reduce_spending, save_more for low-income; minimal impact on high-income",
        },
    },

    "A2_BTO_Tengah_2023": {
        "name": "BTO Launch: Tengah 4,000 Units (Aug 2023)",
        "date": "2023-08-15",
        "description": "HDB launched ~4,000 BTO flats in Tengah, Singapore's newest town with car-free features.",
        "events": [
            ExternalEvent("gov", "policy_housing",
                {"title": "HDB BTO launch: 4,000 units in Tengah town",
                 "detail": "New town with car-lite features, smart home systems. 2-room to 5-room flats. Priority for first-timers.",
                 "location": "Tengah", "units": 4000},
                relevance_tags=["housing:HDB_3", "housing:HDB_4", "housing:HDB_5_EC",
                                "age:young", "age:working"]),
        ],
        "expected": {
            "affected_groups": "Young singles (25-35), married couples in HDB, first-time buyers",
            "expected_reactions": "apply_bto for eligible young adults; housing upgrade consideration",
        },
    },

    "A3_CPF_Ceiling_2024": {
        "name": "CPF Monthly Salary Ceiling: $6,800 → $8,000 (Sep 2023 phased)",
        "date": "2023-09-01",
        "description": "Gradual increase in CPF ordinary wage ceiling from $6,000 to $8,000 by 2026.",
        "events": [
            ExternalEvent("gov", "policy_cpf",
                {"title": "CPF salary ceiling raised to $6,800, heading to $8,000 by 2026",
                 "detail": "Higher-income workers contribute more to CPF. Improves retirement adequacy but reduces take-home pay.",
                 "new_ceiling": 6800, "target_ceiling": 8000},
                relevance_tags=["age:working"]),
        ],
        "expected": {
            "affected_groups": "Workers earning above $6,000/month",
            "expected_reactions": "save_more (forced savings); some may reduce_spending due to lower take-home",
        },
    },

    "A4_Retirement_Age_63_2022": {
        "name": "Retirement Age Raised to 63 (Jul 2022)",
        "date": "2022-07-01",
        "description": "Minimum retirement age raised from 62 to 63; re-employment age from 67 to 68.",
        "events": [
            ExternalEvent("gov", "policy_employment",
                {"title": "Retirement age raised to 63, re-employment to 68",
                 "detail": "Part of planned increases to 65/70 by 2030. Employers must offer re-employment.",
                 "retirement_age": 63, "reemployment_age": 68},
                relevance_tags=["age:senior", "age:working"]),
        ],
        "expected": {
            "affected_groups": "Workers aged 55-68",
            "expected_reactions": "plan_retirement adjustments; part_time_work for 63-68 age group",
        },
    },

    # ---- B. ECONOMIC / MARKET ----

    "B1_Fed_Rate_Hike_2022": {
        "name": "Aggressive Rate Hikes — Mortgage Shock (2022-2023)",
        "date": "2022-06-15",
        "description": "US Fed raised rates aggressively, Singapore SORA/SIBOR followed. Home loan rates jumped from ~1.5% to 3.5-4%.",
        "events": [
            ExternalEvent("market", "market_interest_rate",
                {"title": "Singapore mortgage rates surge to 3.5-4% as Fed hikes aggressively",
                 "detail": "SORA-based home loans now at 3.5-4%, up from 1.5% in 2021. Monthly payments for $500K loan increase by ~$500.",
                 "sora_3m": 3.65, "prev_rate": 1.50, "mortgage_impact_pct": 40},
                relevance_tags=["housing:Condo", "housing:Landed", "housing:HDB_5_EC",
                                "age:working"]),
        ],
        "expected": {
            "affected_groups": "Private property owners, condo buyers, HDB upgraders",
            "expected_reactions": "reduce_spending for mortgage holders; save_more; defer housing upgrade",
        },
    },

    "B2_Tech_Layoffs_2023": {
        "name": "Tech Sector Layoffs — Meta/Google/Shopee (2023)",
        "date": "2023-01-20",
        "description": "Global tech layoffs hit Singapore. Shopee, Sea Group, Meta, Google cut headcount.",
        "events": [
            ExternalEvent("market", "news_employment",
                {"title": "Tech layoffs hit Singapore: Shopee, Meta, Google cut thousands of jobs",
                 "detail": "Over 10,000 tech jobs cut in Singapore. EP holders face 6-month window to find new employment.",
                 "sector": "ICT", "layoffs_sg": 10000},
                relevance_tags=["age:working", "industry:ICT"]),
        ],
        "expected": {
            "affected_groups": "ICT workers, EP holders, young professionals",
            "expected_reactions": "change_job, save_more, reduce_spending; EP holders face visa risk",
        },
    },

    "B3_Property_Cooling_2023": {
        "name": "Property Cooling Measures — ABSD 60% (Apr 2023)",
        "date": "2023-04-27",
        "description": "ABSD for foreigners doubled to 60%. Designed to cool red-hot property market.",
        "events": [
            ExternalEvent("gov", "policy_housing",
                {"title": "ABSD for foreigners raised to 60%, highest in history",
                 "detail": "Additional Buyer's Stamp Duty: foreigners 60%, PRs 30% (2nd property), citizens 20% (2nd property).",
                 "absd_foreigner": 60, "absd_pr_2nd": 30, "absd_citizen_2nd": 20},
                relevance_tags=["housing:Condo", "housing:Landed", "age:working"]),
        ],
        "expected": {
            "affected_groups": "EP/SP holders wanting property; investors; PR second-home buyers",
            "expected_reactions": "defer housing upgrade; invest elsewhere; foreign workers may reconsider SG",
        },
    },

    # ---- C. INFRASTRUCTURE ----

    "C1_TEL_Stage4_2024": {
        "name": "Thomson-East Coast Line Stage 4 Opens (Jun 2024)",
        "date": "2024-06-23",
        "description": "TEL Stage 4: 7 new stations from Tanjong Rhu to Bayshore, serving Marine Parade, Katong, Bedok South.",
        "events": [
            ExternalEvent("gov", "infrastructure_transport",
                {"title": "Thomson-East Coast Line Stage 4 opens with 7 new stations",
                 "detail": "Marine Parade, Katong, Bedok South now have MRT access. Commute time to CBD cut by 15-20 min for eastern residents.",
                 "line": "TEL", "stage": 4, "stations": 7,
                 "areas_served": ["Marine Parade", "Bedok", "Katong"]},
                relevance_tags=["transport:mrt", "transport:bus",
                                "area:Marine Parade", "area:Bedok"]),
        ],
        "expected": {
            "affected_groups": "Residents of Marine Parade, Bedok, eastern areas; commuters",
            "expected_reactions": "Switch to MRT commute; property values in area may rise",
        },
    },

    "C2_ERP2_2024": {
        "name": "ERP 2.0 Satellite-Based Pricing Announced (2024)",
        "date": "2024-08-01",
        "description": "Transition from gantry-based ERP to satellite-based distance charging. On-Board Units mandatory.",
        "events": [
            ExternalEvent("gov", "policy_transport",
                {"title": "ERP 2.0: Distance-based road pricing to replace gantry system",
                 "detail": "New OBU devices mandatory for all vehicles by 2025. Charges based on distance, time, and route.",
                 "system": "ERP_2.0", "launch_year": 2025},
                relevance_tags=["transport:vehicle", "transport:car"]),
        ],
        "expected": {
            "affected_groups": "Vehicle owners (12% of population), daily car commuters",
            "expected_reactions": "Consider switching to public transport; reduce_spending on commute",
        },
    },

    # ---- D. HEALTH / CRISIS ----

    "D1_COVID_CB_2020": {
        "name": "COVID-19 Circuit Breaker (Apr-Jun 2020)",
        "date": "2020-04-07",
        "description": "Singapore imposed a nationwide Circuit Breaker — schools closed, WFH mandatory, only essential services open.",
        "events": [
            ExternalEvent("gov", "crisis_pandemic",
                {"title": "COVID-19 Circuit Breaker: Nationwide partial lockdown for 8 weeks",
                 "detail": "All non-essential workplaces closed. Schools shift to home-based learning. Gatherings banned. Government provides $600/month Jobs Support Scheme.",
                 "duration_weeks": 8, "wfh_mandatory": True, "school_closed": True,
                 "job_support_pct": 75},
                relevance_tags=[]),  # affects everyone
        ],
        "expected": {
            "affected_groups": "All agents — F&B/Retail hardest hit, WFH for office workers",
            "expected_reactions": "reduce_spending universally; job_loss for F&B/Retail; save_more for WFH workers with maintained income",
        },
    },

    "D2_Dengue_Record_2022": {
        "name": "Record Dengue Outbreak — 32,000 Cases (2022)",
        "date": "2022-07-15",
        "description": "Singapore saw record dengue cases. NEA ramped up fogging. Several deaths reported.",
        "events": [
            ExternalEvent("health", "health_dengue",
                {"title": "Singapore sees record 32,000 dengue cases in 2022",
                 "detail": "Dengue hotspots across Bedok, Tampines, Woodlands. 20 deaths reported. NEA intensive fogging in residential areas.",
                 "cases": 32000, "deaths": 20,
                 "hotspots": ["Bedok", "Tampines", "Woodlands"]},
                relevance_tags=["area:Bedok", "area:Tampines", "area:Woodlands"]),
        ],
        "expected": {
            "affected_groups": "Residents of Bedok, Tampines, Woodlands; seniors; outdoor workers",
            "expected_reactions": "medical_checkup for affected areas; health anxiety increase",
        },
    },

    # ---- E. SOCIAL / DEMOGRAPHIC ----

    "E1_CDAC_Malay_Support_2023": {
        "name": "Enhanced CDC Vouchers — $300/Household (2023)",
        "date": "2023-01-03",
        "description": "Government distributed $300 CDC vouchers per household to offset cost of living.",
        "events": [
            ExternalEvent("gov", "policy_social",
                {"title": "Every Singaporean household receives $300 CDC vouchers",
                 "detail": "Split: $150 for heartland merchants, $150 for hawkers/transport. Valid 6 months. ~1.3M households eligible.",
                 "amount": 300, "eligible": "all_citizen_households"},
                relevance_tags=[]),  # all citizen households
        ],
        "expected": {
            "affected_groups": "All citizen households, lower-income benefit more proportionally",
            "expected_reactions": "Slight spending increase; benefit perception highest for low-income",
        },
    },

    "E2_NS_Women_Discussion_2024": {
        "name": "National Service for Women Discussion (2024)",
        "date": "2024-03-08",
        "description": "PM Lee raised discussion about expanding NS obligations. No policy change, but public debate intensified.",
        "events": [
            ExternalEvent("news", "news_ns",
                {"title": "PM raises possibility of NS for women in future review",
                 "detail": "Public discourse on gender equality in national defense. No immediate policy change but triggered debate across demographics.",
                 "policy_change": False, "discussion_only": True},
                relevance_tags=["age:young"]),
        ],
        "expected": {
            "affected_groups": "Young women (18-25), NS-serving males, parents",
            "expected_reactions": "Discussion/opinion formation only; no behavioral change expected",
        },
    },
}


# ============================================================
# TEST RUNNER
# ============================================================
def run_test(test_id: str, test_data: dict, population: pd.DataFrame,
             n_ticks: int = 30):
    """
    Run a single historical event test.

    Simulates n_ticks (days) with the event injected at tick 0.
    Returns detailed results.
    """
    snap_dir = tempfile.mkdtemp()
    runner = SimulationRunner(
        population.copy(), date(2026, 1, 1), seed=42,
        snapshot_dir=snap_dir, enable_collectors=False,  # disable random collectors
    )

    # Take baseline snapshot
    baseline = population.copy()

    # Inject historical events at tick 0
    for event in test_data["events"]:
        runner.tick_manager.queue_event_for_relevant(
            event, runner.tick_manager.agents)

    # Count how many agents received the event
    agents_with_events = sum(
        1 for v in runner.tick_manager.pending_events.values() if v)

    # Run simulation
    tick_results = []
    for _ in range(n_ticks):
        result = runner.run_tick()
        tick_results.append(result)

    # Analyze results
    final = runner.tick_manager.agents
    analysis = {
        "test_id": test_id,
        "test_name": test_data["name"],
        "event_date": test_data["date"],
        "description": test_data["description"],
        "agents_received_event": agents_with_events,
        "agents_total": len(population),
        "ticks_simulated": n_ticks,
        "total_rule_decisions": sum(t["rule_decisions"] for t in tick_results),
        "total_prob_decisions": sum(t["prob_decisions"] for t in tick_results),
        "total_llm_decisions": sum(t["llm_decisions"] for t in tick_results),
        "tick_0_detail": tick_results[0] if tick_results else {},
    }

    # State changes analysis
    changes = {}

    # Job status changes
    if "job_status" in baseline.columns and "job_status" in final.columns:
        job_before = Counter(baseline["job_status"])
        job_after = Counter(final["job_status"])
        job_delta = {k: job_after.get(k, 0) - job_before.get(k, 0)
                     for k in set(list(job_before.keys()) + list(job_after.keys()))
                     if job_after.get(k, 0) != job_before.get(k, 0)}
        if job_delta:
            changes["job_status"] = job_delta

    # Marital status changes
    if "marital_status" in baseline.columns:
        mar_before = Counter(baseline["marital_status"])
        mar_after = Counter(final["marital_status"])
        mar_delta = {k: mar_after.get(k, 0) - mar_before.get(k, 0)
                     for k in set(list(mar_before.keys()) + list(mar_after.keys()))
                     if mar_after.get(k, 0) != mar_before.get(k, 0)}
        if mar_delta:
            changes["marital_status"] = mar_delta

    # Health changes
    if "health_status" in baseline.columns:
        health_before = Counter(baseline["health_status"])
        health_after = Counter(final["health_status"])
        health_delta = {k: health_after.get(k, 0) - health_before.get(k, 0)
                        for k in set(list(health_before.keys()) + list(health_after.keys()))
                        if health_after.get(k, 0) != health_before.get(k, 0)}
        if health_delta:
            changes["health_status"] = health_delta

    # Deaths
    if "is_alive" in baseline.columns:
        deaths = int(baseline["is_alive"].sum() - final["is_alive"].sum())
        if deaths:
            changes["deaths"] = deaths

    # Children born
    if "num_children" in baseline.columns:
        births = int(final["num_children"].sum() - baseline["num_children"].sum())
        if births:
            changes["births"] = births

    # CPF changes
    if "cpf_oa" in baseline.columns:
        cpf_before = baseline[["cpf_oa", "cpf_sa", "cpf_ma"]].sum()
        cpf_after = final[["cpf_oa", "cpf_sa", "cpf_ma"]].sum()
        changes["cpf_total_delta"] = int(cpf_after.sum() - cpf_before.sum())
        changes["cpf_oa_delta"] = int(cpf_after["cpf_oa"] - cpf_before["cpf_oa"])
        changes["cpf_sa_delta"] = int(cpf_after["cpf_sa"] - cpf_before["cpf_sa"])
        changes["cpf_ma_delta"] = int(cpf_after["cpf_ma"] - cpf_before["cpf_ma"])

    # LLM decisions breakdown (what actions were chosen)
    llm_actions = Counter()
    for d in runner.decision_log:
        action = d.get("decision", {}).get("action", "unknown")
        llm_actions[action] += 1
    if llm_actions:
        changes["llm_action_distribution"] = dict(llm_actions)

    analysis["state_changes"] = changes
    analysis["expected"] = test_data["expected"]

    return analysis


def print_result(result: dict):
    """Pretty-print a test result."""
    print()
    print("=" * 72)
    print(f"  {result['test_id']}: {result['test_name']}")
    print(f"  Date: {result['event_date']}")
    print(f"  {result['description']}")
    print("=" * 72)
    print()
    print(f"  Population:          {result['agents_total']} agents")
    print(f"  Received event:      {result['agents_received_event']} agents "
          f"({result['agents_received_event']/result['agents_total']*100:.1f}%)")
    print(f"  Ticks simulated:     {result['ticks_simulated']} days")
    print()
    print(f"  --- Decision Counts (total over {result['ticks_simulated']} days) ---")
    print(f"  Layer 1 (Rules):     {result['total_rule_decisions']:,}")
    print(f"  Layer 2 (Prob):      {result['total_prob_decisions']:,}")
    print(f"  Layer 3 (LLM):       {result['total_llm_decisions']:,}")
    print()

    # Tick 0 detail
    t0 = result.get("tick_0_detail", {})
    if t0:
        print(f"  --- Tick 0 (Event Injection Day) ---")
        print(f"  Active agents:       {t0.get('active_agents', 0)}")
        print(f"  Events routed:       {t0.get('events_routed', 0)}")
        print(f"  Rule decisions:      {t0.get('rule_decisions', 0)}")
        print(f"  Prob decisions:      {t0.get('prob_decisions', 0)}")
        print(f"  LLM decisions:       {t0.get('llm_decisions', 0)}")
        print()

    # State changes
    ch = result.get("state_changes", {})
    if ch:
        print(f"  --- State Changes After {result['ticks_simulated']} Days ---")
        if ch.get("job_status"):
            print(f"  Job status:          {ch['job_status']}")
        if ch.get("marital_status"):
            print(f"  Marital status:      {ch['marital_status']}")
        if ch.get("health_status"):
            print(f"  Health status:       {ch['health_status']}")
        if ch.get("deaths"):
            print(f"  Deaths:              {ch['deaths']}")
        if ch.get("births"):
            print(f"  Births:              {ch['births']}")
        if ch.get("cpf_total_delta"):
            print(f"  CPF total change:    ${ch['cpf_total_delta']:,}")
            print(f"    OA: +${ch['cpf_oa_delta']:,}  SA: +${ch['cpf_sa_delta']:,}  MA: +${ch['cpf_ma_delta']:,}")
        if ch.get("llm_action_distribution"):
            print(f"  LLM action choices:  {ch['llm_action_distribution']}")
        print()

    # Expected
    exp = result.get("expected", {})
    if exp:
        print(f"  --- Expected Behavior ---")
        print(f"  Affected groups:     {exp.get('affected_groups', 'N/A')}")
        print(f"  Expected reactions:  {exp.get('expected_reactions', 'N/A')}")
    print()


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 72)
    print("  SINGAPORE DIGITAL TWIN — HISTORICAL EVENT TEST SUITE")
    print("  Testing with real events from 2020-2024")
    print("=" * 72)

    # Build population
    print("\nBuilding test population (500 agents)...")
    pop = build_test_population(500, seed=42)
    print(f"  Age range: {pop['age'].min()}-{pop['age'].max()}")
    print(f"  Gender: {dict(Counter(pop['gender']))}")
    print(f"  Ethnicity: {dict(Counter(pop['ethnicity']))}")
    print(f"  Housing: {dict(Counter(pop['housing_type']))}")
    print(f"  Working (income > 0): {(pop['monthly_income'] > 0).sum()}")
    print(f"  Median income (workers): ${pop.loc[pop['monthly_income']>0, 'monthly_income'].median():,.0f}")

    # Select which tests to run
    test_ids = sys.argv[1:] if len(sys.argv) > 1 else list(HISTORICAL_EVENTS.keys())

    all_results = []
    for tid in test_ids:
        if tid not in HISTORICAL_EVENTS:
            print(f"\n  WARNING: Unknown test ID '{tid}', skipping.")
            continue
        print(f"\nRunning {tid}...", end=" ", flush=True)
        result = run_test(tid, HISTORICAL_EVENTS[tid], pop, n_ticks=30)
        print("done.")
        print_result(result)
        all_results.append(result)

    # Summary table
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print(f"  {'Test':<30} {'Rcvd':>5} {'Rule':>6} {'Prob':>5} {'LLM':>5} {'Jobs':>6} {'Deaths':>6} {'CPF':>10}")
    print(f"  {'-'*30} {'-'*5} {'-'*6} {'-'*5} {'-'*5} {'-'*6} {'-'*6} {'-'*10}")
    for r in all_results:
        ch = r.get("state_changes", {})
        job_ch = sum(abs(v) for v in ch.get("job_status", {}).values()) // 2
        deaths = ch.get("deaths", 0)
        cpf = ch.get("cpf_total_delta", 0)
        print(f"  {r['test_name'][:30]:<30} {r['agents_received_event']:>5} "
              f"{r['total_rule_decisions']:>6} {r['total_prob_decisions']:>5} "
              f"{r['total_llm_decisions']:>5} {job_ch:>6} {deaths:>6} "
              f"${cpf:>9,}")
    print()
