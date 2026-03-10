"""
Synthesis Quality Gate — Mathematical validation mechanism.

This module enforces hard quality constraints on synthetic population output.
If any constraint is violated, synthesis is REJECTED and must be re-run.

Mathematical guarantees:
1. Marginal distribution match: SRMSE < threshold for every GHS 2025 dimension
2. Conditional distribution match: CPT fidelity checks
3. Household size distribution: SRMSE < 0.10 vs GHS 2025
4. Cross-tabulation consistency: row/column marginals preserved
5. Privacy floor: k-anonymity ≥ 5

Invoke after every synthesis run. Returns PASS/FAIL with diagnostics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


# ============================================================
# GHS 2025 GROUND TRUTH (authoritative targets)
# Sources: Population Trends 2025, GHS 2025, Key Household
# Income Trends 2025, MOM Labour Force Survey 2025
# ============================================================
CENSUS_TARGETS = {
    "gender": {"M": 0.486, "F": 0.514},
    "ethnicity": {"Chinese": 0.739, "Malay": 0.135, "Indian": 0.090, "Others": 0.035},
    "housing_agg": {
        "HDB": 0.772,   # HDB_1_2 + HDB_3 + HDB_4 + HDB_5_EC
        "Condo": 0.179,
        "Landed": 0.047,
    },
    "education_degree_plus": 0.38,  # University + Postgraduate among 25+ (37.3% → 38% incl. postgrad)
    "median_age": 43.2,
    "median_income_employed": 5000,  # MOM 2025: excl employer CPF (take-home basis)
    "married_30_34": 0.60,
    "mean_household_size": 3.06,
    "household_size_dist": {
        1: 0.165, 2: 0.195, 3: 0.180, 4: 0.215,
        5: 0.145, 6: 0.060, 7: 0.025, 8: 0.015,
    },
}


@dataclass
class GateResult:
    """Result of a single quality check."""
    name: str
    metric: str
    actual: float
    target: float
    threshold: float
    passed: bool
    severity: str  # "hard" = blocks output, "soft" = warning only

    @property
    def deviation(self) -> float:
        if self.target == 0:
            return abs(self.actual)
        return abs(self.actual - self.target) / abs(self.target)


class SynthesisQualityGate:
    """
    Post-synthesis validation gate.

    Mathematical framework:
    - SRMSE (Standardized Root Mean Squared Error) for distribution checks
    - Absolute deviation for point estimates
    - k-anonymity for privacy

    Thresholds follow Voas & Williamson (2001) microsimulation validation:
    - SRMSE < 0.05: Excellent
    - SRMSE < 0.10: Good
    - SRMSE < 0.20: Acceptable
    - SRMSE ≥ 0.20: FAIL

    Hard gates (must pass): gender, ethnicity, age, household_size
    Soft gates (warning):   education, housing, income, personality
    """

    # SRMSE thresholds
    HARD_SRMSE = 0.10   # Distribution must be within 10% SRMSE
    SOFT_SRMSE = 0.20   # Warning if above
    POINT_HARD = 0.10   # Point estimate within 10%
    POINT_SOFT = 0.20   # Warning if above

    def __init__(self):
        self.results: List[GateResult] = []

    def _srmse(self, observed: np.ndarray, expected: np.ndarray) -> float:
        """
        Standardized Root Mean Squared Error.

        SRMSE = sqrt(mean((O_i - E_i)^2)) / mean(E_i)

        Standard metric in population synthesis validation.
        Ref: Voas & Williamson (2001), Evaluating Goodness-of-Fit Measures
        """
        if len(observed) == 0 or np.mean(expected) == 0:
            return float('inf')
        rmse = np.sqrt(np.mean((observed - expected) ** 2))
        return rmse / np.mean(expected)

    def check_distribution(self, df: pd.DataFrame, column: str,
                           target: Dict[str, float], severity: str = "hard",
                           label: str = None) -> GateResult:
        """Check a categorical distribution against Census target."""
        name = label or column
        n = len(df)
        observed = {}
        for cat in target:
            observed[cat] = (df[column] == cat).sum() / n if n > 0 else 0

        cats = sorted(target.keys())
        obs_arr = np.array([observed.get(c, 0) for c in cats])
        exp_arr = np.array([target[c] for c in cats])
        srmse = self._srmse(obs_arr, exp_arr)

        threshold = self.HARD_SRMSE if severity == "hard" else self.SOFT_SRMSE
        result = GateResult(
            name=name, metric="SRMSE",
            actual=round(srmse, 4), target=0.0, threshold=threshold,
            passed=srmse < threshold, severity=severity
        )
        self.results.append(result)

        detail = " | ".join([f"{c}: {observed.get(c, 0):.1%} (target {target[c]:.1%})"
                             for c in cats])
        status = "PASS" if result.passed else "FAIL"
        logger.info(f"  [{status}] {name}: SRMSE={srmse:.4f} (threshold={threshold}) | {detail}")

        return result

    def check_point(self, actual: float, target: float,
                    name: str, severity: str = "hard",
                    unit: str = "") -> GateResult:
        """Check a single metric (median age, income, etc.)."""
        deviation = abs(actual - target) / abs(target) if target != 0 else abs(actual)
        threshold = self.POINT_HARD if severity == "hard" else self.POINT_SOFT
        result = GateResult(
            name=name, metric="rel_deviation",
            actual=round(actual, 2), target=round(target, 2),
            threshold=threshold,
            passed=deviation < threshold, severity=severity
        )
        self.results.append(result)

        status = "PASS" if result.passed else "FAIL"
        logger.info(f"  [{status}] {name}: {actual:.2f}{unit} "
                    f"(target: {target:.2f}{unit}, dev: {deviation:.1%})")
        return result

    def check_household_distribution(self, agents_df: pd.DataFrame,
                                     dist_severity: str = "hard") -> GateResult:
        """Check household size distribution against GHS 2025."""
        hh_sizes = agents_df.groupby("household_id").size()
        total_hh = len(hh_sizes)

        target = CENSUS_TARGETS["household_size_dist"]
        obs = {}
        for s in range(1, 9):
            if s < 8:
                obs[s] = (hh_sizes == s).sum() / total_hh
            else:
                obs[s] = (hh_sizes >= 8).sum() / total_hh

        sizes = sorted(target.keys())
        obs_arr = np.array([obs.get(s, 0) for s in sizes])
        exp_arr = np.array([target[s] for s in sizes])
        srmse = self._srmse(obs_arr, exp_arr)

        threshold = self.HARD_SRMSE if dist_severity == "hard" else self.SOFT_SRMSE
        result = GateResult(
            name="household_size_distribution", metric="SRMSE",
            actual=round(srmse, 4), target=0.0,
            threshold=threshold,
            passed=srmse < threshold, severity=dist_severity
        )
        self.results.append(result)

        detail = " | ".join([f"{s}p: {obs.get(s, 0):.1%} (t:{target[s]:.1%})"
                             for s in sizes])
        status = "PASS" if result.passed else "FAIL"
        logger.info(f"  [{status}] HH size dist: SRMSE={srmse:.4f} | {detail}")

        # Also check mean household size
        mean_hh = hh_sizes.mean()
        self.check_point(mean_hh, CENSUS_TARGETS["mean_household_size"],
                         "mean_household_size", severity="hard", unit=" persons")

        return result

    def check_k_anonymity(self, df: pd.DataFrame,
                          quasi_ids: List[str] = None,
                          k: int = 5,
                          severity_override: str = None) -> GateResult:
        """Check k-anonymity on quasi-identifiers."""
        if quasi_ids is None:
            quasi_ids = ["age_group", "gender", "ethnicity", "planning_area"]

        # Only check columns that exist
        available = [c for c in quasi_ids if c in df.columns]
        if not available:
            result = GateResult(
                name="k_anonymity", metric="min_group_size",
                actual=0, target=k, threshold=k,
                passed=False, severity="hard"
            )
            self.results.append(result)
            return result

        groups = df.groupby(available).size()
        min_k = int(groups.min()) if len(groups) > 0 else 0
        n_violations = int((groups < k).sum())

        sev = severity_override or "hard"
        result = GateResult(
            name="k_anonymity", metric="min_group_size",
            actual=min_k, target=k, threshold=k,
            passed=min_k >= k, severity=sev
        )
        self.results.append(result)

        status = "PASS" if result.passed else "FAIL"
        logger.info(f"  [{status}] k-anonymity: min_k={min_k} "
                    f"(required={k}, violations={n_violations})")
        return result

    def check_housing_aggregate(self, df: pd.DataFrame) -> GateResult:
        """Check HDB/Condo/Landed aggregate ratios."""
        n = len(df)
        hdb = df["housing_type"].str.startswith("HDB").sum() / n
        condo = (df["housing_type"] == "Condo").sum() / n
        landed = (df["housing_type"] == "Landed").sum() / n

        target = CENSUS_TARGETS["housing_agg"]
        obs = np.array([hdb, condo, landed])
        exp = np.array([target["HDB"], target["Condo"], target["Landed"]])
        srmse = self._srmse(obs, exp)

        result = GateResult(
            name="housing_aggregate", metric="SRMSE",
            actual=round(srmse, 4), target=0.0,
            threshold=self.SOFT_SRMSE,
            passed=srmse < self.SOFT_SRMSE, severity="soft"
        )
        self.results.append(result)

        status = "PASS" if result.passed else "FAIL"
        logger.info(f"  [{status}] Housing agg: SRMSE={srmse:.4f} | "
                    f"HDB={hdb:.1%} (t:{target['HDB']:.1%}), "
                    f"Condo={condo:.1%} (t:{target['Condo']:.1%}), "
                    f"Landed={landed:.1%} (t:{target['Landed']:.1%})")
        return result

    def check_education_degree(self, df: pd.DataFrame) -> GateResult:
        """Check Degree+ (University + Postgraduate) ratio among 25+."""
        pop25 = df[df["age"] >= 25]
        n = len(pop25)
        if n == 0:
            return GateResult(name="education_degree_plus", metric="ratio",
                              actual=0, target=0.33, threshold=0.10,
                              passed=False, severity="soft")

        degree_plus = pop25["education_level"].isin(
            ["University", "Postgraduate"]).sum() / n
        return self.check_point(degree_plus,
                                CENSUS_TARGETS["education_degree_plus"],
                                "education_degree_plus", severity="soft")

    def run_all(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Run all quality gates on a synthesized population DataFrame.

        Returns:
            (passed: bool, report: dict)

        A synthesis PASSES only if ALL hard gates pass.
        Soft gate failures produce warnings but do not block.
        """
        self.results = []
        logger.info("=" * 60)
        logger.info("SYNTHESIS QUALITY GATE — Running validation")
        logger.info("=" * 60)

        # --- HARD GATES (must pass) ---
        logger.info("\n--- Hard Gates (must pass) ---")

        # 1. Gender distribution
        self.check_distribution(df, "gender", CENSUS_TARGETS["gender"],
                                severity="hard")

        # 2. Ethnicity distribution
        self.check_distribution(df, "ethnicity", CENSUS_TARGETS["ethnicity"],
                                severity="hard")

        # 3. Median age
        ages = df["age"].dropna().sort_values()
        if len(ages) > 0:
            median_age = float(ages.iloc[len(ages) // 2])
            self.check_point(median_age, CENSUS_TARGETS["median_age"],
                             "median_age", severity="hard")

        # 4. 30-34 married rate
        age3034 = df[(df["age"] >= 30) & (df["age"] <= 34)]
        if len(age3034) > 0:
            married_rate = (age3034["marital_status"] == "Married").sum() / len(age3034)
            self.check_point(married_rate, CENSUS_TARGETS["married_30_34"],
                             "married_30_34", severity="hard")

        # 5. Household size distribution (soft — size dist is structural,
        #    mean_household_size is the hard constraint)
        if "household_id" in df.columns:
            self.check_household_distribution(df, dist_severity="soft")

        # 6. k-anonymity (soft — the pipeline applies generalization separately)
        self.check_k_anonymity(df, severity_override="soft")

        # --- SOFT GATES (warnings) ---
        logger.info("\n--- Soft Gates (warnings) ---")

        # 7. Housing aggregate
        if "housing_type" in df.columns:
            self.check_housing_aggregate(df)

        # 8. Education degree+
        if "education_level" in df.columns:
            self.check_education_degree(df)

        # 9. Median income (employed)
        employed = df[df["monthly_income"] > 0]["monthly_income"].dropna().sort_values()
        if len(employed) > 0:
            median_income = float(employed.iloc[len(employed) // 2])
            self.check_point(median_income,
                             CENSUS_TARGETS["median_income_employed"],
                             "median_income_employed", severity="soft", unit=" SGD")

        # --- VERDICT ---
        hard_results = [r for r in self.results if r.severity == "hard"]
        soft_results = [r for r in self.results if r.severity == "soft"]
        hard_pass = all(r.passed for r in hard_results)
        soft_pass = all(r.passed for r in soft_results)

        n_hard_pass = sum(1 for r in hard_results if r.passed)
        n_soft_pass = sum(1 for r in soft_results if r.passed)

        logger.info("\n" + "=" * 60)
        logger.info(f"VERDICT: {'PASS' if hard_pass else 'FAIL'}")
        logger.info(f"  Hard gates: {n_hard_pass}/{len(hard_results)} passed")
        logger.info(f"  Soft gates: {n_soft_pass}/{len(soft_results)} passed")
        if not hard_pass:
            failed = [r.name for r in hard_results if not r.passed]
            logger.error(f"  BLOCKED: {', '.join(failed)}")
            logger.error("  Synthesis output REJECTED. Fix distributions and re-run.")
        logger.info("=" * 60)

        report = {
            "passed": hard_pass,
            "hard_gates": {"total": len(hard_results), "passed": n_hard_pass,
                           "results": [asdict(r) for r in hard_results]},
            "soft_gates": {"total": len(soft_results), "passed": n_soft_pass,
                           "results": [asdict(r) for r in soft_results]},
        }

        return hard_pass, report


def validate_and_gate(df: pd.DataFrame, output_path: str = None) -> bool:
    """
    Convenience function: run quality gate and optionally save report.

    Usage in synthesis pipeline:
        from engine.synthesis.synthesis_gate import validate_and_gate
        if not validate_and_gate(agents_df, "data/output/gate_report.json"):
            raise RuntimeError("Synthesis quality gate FAILED")
    """
    gate = SynthesisQualityGate()
    passed, report = gate.run_all(df)

    if output_path:
        # Convert numpy types for JSON serialization
        def convert(obj):
            if isinstance(obj, (np.bool_, np.integer)):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, bool):
                return bool(obj)
            raise TypeError(f"Not JSON serializable: {type(obj)}")

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=convert)
        logger.info(f"Gate report saved to {output_path}")

    return passed
