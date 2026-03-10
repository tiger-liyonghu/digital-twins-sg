"""
AI Governance Engine — IMDA Model AI Governance Framework compliance.

Implements requirements from:
1. Model AI Governance Framework (IMDA 2020, updated 2024)
2. Model AI Governance Framework for Agentic AI (IMDA Jan 2026)
3. AI Verify Testing Framework (11 principles, updated May 2025)
4. MAS FEAT Principles (Fairness, Ethics, Accountability, Transparency)

Four core dimensions (Agentic AI Framework 2026):
D1: Assess and bound risks upfront
D2: Make humans meaningfully accountable
D3: Implement technical controls and processes
D4: Enable end-user responsibility

AI Verify 11 Principles:
P1: Transparency
P2: Explainability
P3: Repeatability / Reproducibility
P4: Safety
P5: Security
P6: Robustness
P7: Fairness
P8: Data Governance
P9: Accountability
P10: Human Agency and Oversight
P11: Inclusive Growth, Societal and Environmental Well-being
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
import json
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================
# AI Verify Principle Assessment
# ============================================================

class AIVerifyAssessment:
    """
    Self-assessment against AI Verify's 11 governance principles.

    For each principle: evidence of compliance, test results,
    and documentation references.
    """

    def __init__(self):
        self.assessments: Dict[str, Dict] = {}

    def assess_transparency(self, model_card: Dict) -> Dict:
        """
        P1: Transparency — responsible disclosure to affected parties.

        For Digital Twin: users must know:
        - What data sources the synthetic population is based on
        - How agent decisions are made (3-layer: rules → probability → LLM)
        - Limitations and known biases
        - That agents are SYNTHETIC, not real individuals
        """
        checks = {
            "data_sources_documented": bool(model_card.get("data_sources")),
            "decision_pipeline_documented": bool(model_card.get("decision_pipeline")),
            "limitations_documented": bool(model_card.get("limitations")),
            "synthetic_nature_disclosed": bool(model_card.get("synthetic_disclosure")),
            "model_methodology_documented": bool(model_card.get("methodology")),
        }
        passed = sum(checks.values())
        total = len(checks)

        result = {
            "principle": "P1_Transparency",
            "checks": checks,
            "score": f"{passed}/{total}",
            "passed": passed == total,
        }
        self.assessments["P1"] = result
        return result

    def assess_explainability(self, decision_logs: List[Dict]) -> Dict:
        """
        P2: Explainability — assess factors leading to decisions.

        For Digital Twin: every agent decision must be traceable:
        - Layer 1 (rules): deterministic, fully explainable
        - Layer 2 (probability): model coefficients visible
        - Layer 3 (LLM): prompt + reasoning chain logged
        """
        if not decision_logs:
            return {
                "principle": "P2_Explainability",
                "passed": False,
                "reason": "No decision logs provided",
            }

        explainable_count = 0
        for log in decision_logs:
            if log.get("layer") == "rules":
                explainable_count += 1  # Always explainable
            elif log.get("layer") == "probability":
                if log.get("model_coefficients"):
                    explainable_count += 1
            elif log.get("layer") == "llm":
                if log.get("reasoning_chain"):
                    explainable_count += 1

        ratio = explainable_count / len(decision_logs) if decision_logs else 0

        result = {
            "principle": "P2_Explainability",
            "total_decisions": len(decision_logs),
            "explainable": explainable_count,
            "explainability_ratio": round(ratio, 4),
            "passed": ratio >= 0.95,  # 95% of decisions must be explainable
        }
        self.assessments["P2"] = result
        return result

    def assess_reproducibility(self, seed: int,
                               run1_hash: str, run2_hash: str) -> Dict:
        """
        P3: Repeatability/Reproducibility.

        Same seed + same code → same synthetic population.
        Verified by comparing SHA-256 hashes of output.
        """
        result = {
            "principle": "P3_Reproducibility",
            "seed": seed,
            "run1_hash": run1_hash,
            "run2_hash": run2_hash,
            "identical": run1_hash == run2_hash,
            "passed": run1_hash == run2_hash,
        }
        self.assessments["P3"] = result
        return result

    def assess_fairness(self, df: pd.DataFrame,
                        outcome_col: str = "monthly_income") -> Dict:
        """
        P7: Fairness — no unintended discrimination.

        Test: income distribution should not show unexplained bias
        across protected attributes (gender, ethnicity).

        Method: Compute disparate impact ratio (80% rule).
        For each protected group: mean(outcome) / max_group_mean(outcome)
        Must be >= 0.80 (four-fifths rule).
        """
        results_by_attr = {}

        for attr in ["gender", "ethnicity"]:
            if attr not in df.columns or outcome_col not in df.columns:
                continue

            group_means = df.groupby(attr)[outcome_col].mean()
            max_mean = group_means.max()

            disparate_impact = {}
            for group, mean_val in group_means.items():
                ratio = mean_val / max_mean if max_mean > 0 else 0
                disparate_impact[group] = round(float(ratio), 4)

            min_ratio = min(disparate_impact.values())
            results_by_attr[attr] = {
                "group_means": {k: round(float(v), 2)
                                for k, v in group_means.items()},
                "disparate_impact_ratios": disparate_impact,
                "min_ratio": round(min_ratio, 4),
                "passed_80pct_rule": min_ratio >= 0.80,
            }

        all_passed = all(r["passed_80pct_rule"]
                         for r in results_by_attr.values())

        result = {
            "principle": "P7_Fairness",
            "outcome": outcome_col,
            "results_by_attribute": results_by_attr,
            "passed": all_passed,
        }
        self.assessments["P7"] = result
        return result

    def assess_data_governance(self, privacy_audit: Dict) -> Dict:
        """
        P8: Data Governance — good practices for data quality,
        lineage, and compliance.
        """
        checks = {
            "data_lineage_tracked": bool(privacy_audit.get("data_sources")),
            "quality_validated": bool(privacy_audit.get("validation_results")),
            "pdpa_compliant": bool(privacy_audit.get("pdpa_audit", {}).get(
                "direct_id_check", {}).get("passed")),
            "k_anonymity_enforced": bool(privacy_audit.get("k_anonymity", {}).get("passed")),
            "retention_policy_defined": bool(privacy_audit.get("retention_policy")),
        }
        passed = sum(checks.values())
        total = len(checks)

        result = {
            "principle": "P8_Data_Governance",
            "checks": checks,
            "score": f"{passed}/{total}",
            "passed": passed >= 4,  # At least 4/5 checks
        }
        self.assessments["P8"] = result
        return result

    def assess_human_oversight(self, config: Dict) -> Dict:
        """
        P10: Human Agency and Oversight.

        For Agentic AI (2026 framework): humans must remain
        meaningfully accountable with clear approval checkpoints.
        """
        checks = {
            "llm_decisions_logged": config.get("llm_logging", False),
            "human_review_threshold": config.get("human_review_threshold", 0) > 0,
            "kill_switch_available": config.get("kill_switch", False),
            "decision_override_possible": config.get("override_enabled", False),
            "approval_checkpoints_defined": bool(config.get("checkpoints")),
        }
        passed = sum(checks.values())

        result = {
            "principle": "P10_Human_Oversight",
            "checks": checks,
            "score": f"{passed}/{len(checks)}",
            "passed": passed >= 3,
        }
        self.assessments["P10"] = result
        return result

    def generate_report(self) -> Dict:
        """Generate full AI Verify compliance report."""
        total = len(self.assessments)
        passed = sum(1 for a in self.assessments.values() if a.get("passed"))

        return {
            "framework": "AI Verify Testing Framework",
            "version": "2025-05 (GenAI Enhanced)",
            "assessment_date": datetime.now().isoformat(),
            "principles_assessed": total,
            "principles_passed": passed,
            "pass_rate": round(passed / total, 2) if total > 0 else 0,
            "details": self.assessments,
        }


# ============================================================
# Agentic AI Governance (IMDA 2026)
# ============================================================

class AgenticAIGovernance:
    """
    Controls for IMDA Model AI Governance Framework
    for Agentic AI (January 2026).

    Dimension 1: Assess & bound risks upfront
    Dimension 2: Make humans meaningfully accountable
    Dimension 3: Technical controls & processes
    Dimension 4: Enable end-user responsibility
    """

    def __init__(self):
        self.risk_registry: List[Dict] = []
        self.checkpoints: List[Dict] = []
        self.agent_permissions: Dict[str, Dict] = {}

    # --- D1: Risk Assessment ---

    def register_risk(self, risk_id: str, description: str,
                      category: str, severity: str,
                      mitigation: str) -> Dict:
        """Register a known risk with its mitigation strategy."""
        risk = {
            "risk_id": risk_id,
            "description": description,
            "category": category,  # unauthorized_action, data_leakage, bias
            "severity": severity,  # LOW, MEDIUM, HIGH, CRITICAL
            "mitigation": mitigation,
            "status": "MITIGATED",
            "registered_at": datetime.now().isoformat(),
        }
        self.risk_registry.append(risk)
        return risk

    def risk_assessment_report(self) -> Dict:
        """D1: Full risk assessment for agentic AI components."""
        by_severity = {}
        for risk in self.risk_registry:
            sev = risk["severity"]
            by_severity.setdefault(sev, []).append(risk)

        return {
            "dimension": "D1_Risk_Assessment",
            "total_risks": len(self.risk_registry),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "critical_unmitigated": sum(
                1 for r in self.risk_registry
                if r["severity"] == "CRITICAL" and r["status"] != "MITIGATED"
            ),
            "risks": self.risk_registry,
        }

    # --- D2: Human Accountability ---

    def define_checkpoint(self, name: str, trigger: str,
                          requires_approval: bool = True) -> Dict:
        """Define a human approval checkpoint."""
        cp = {
            "name": name,
            "trigger": trigger,
            "requires_approval": requires_approval,
        }
        self.checkpoints.append(cp)
        return cp

    # --- D3: Technical Controls ---

    def set_agent_permissions(self, agent_type: str,
                              can_read: List[str],
                              can_write: List[str],
                              max_actions_per_tick: int,
                              requires_human_approval: List[str]) -> Dict:
        """
        Bound agent permissions (sandboxing).

        Limits what data agents can access and what actions
        they can take, per the framework's recommendation to
        "place limits on agents' autonomy and access to tools and data."
        """
        perms = {
            "agent_type": agent_type,
            "can_read": can_read,
            "can_write": can_write,
            "max_actions_per_tick": max_actions_per_tick,
            "requires_human_approval": requires_human_approval,
        }
        self.agent_permissions[agent_type] = perms
        return perms

    def validate_action(self, agent_type: str, action: str,
                        target: str) -> Tuple[bool, str]:
        """Check if an agent action is permitted."""
        perms = self.agent_permissions.get(agent_type)
        if not perms:
            return False, f"No permissions defined for agent type: {agent_type}"

        if action == "read" and target not in perms["can_read"]:
            return False, f"Read access denied for {target}"
        if action == "write" and target not in perms["can_write"]:
            return False, f"Write access denied for {target}"
        if action in perms["requires_human_approval"]:
            return False, f"Action {action} requires human approval"

        return True, "Permitted"


# ============================================================
# MAS FEAT Principles (Financial Services)
# ============================================================

class MASFEATCompliance:
    """
    MAS FEAT Principles for financial services AI.
    Fairness, Ethics, Accountability, Transparency.

    Relevant when Digital Twin is used for:
    - Insurance pricing/underwriting
    - Credit scoring
    - Financial product recommendations
    """

    def fairness_check(self, df: pd.DataFrame,
                       decision_col: str,
                       protected_attrs: List[str] = None) -> Dict:
        """
        FEAT-F: Decisions should not systematically disadvantage
        individuals based on protected characteristics.
        """
        if protected_attrs is None:
            protected_attrs = ["gender", "ethnicity", "age"]

        results = {}
        for attr in protected_attrs:
            if attr not in df.columns or decision_col not in df.columns:
                continue

            if df[decision_col].dtype in ["float64", "int64"]:
                # Continuous: compare means
                group_means = df.groupby(attr)[decision_col].mean()
                max_mean = group_means.max()
                ratios = {str(k): round(float(v / max_mean), 4)
                          for k, v in group_means.items()}
                min_ratio = min(ratios.values()) if ratios else 0
                results[attr] = {
                    "type": "continuous",
                    "ratios": ratios,
                    "min_ratio": min_ratio,
                    "fair": min_ratio >= 0.80,
                }
            else:
                # Categorical: compare rates
                total = len(df)
                positive = df[decision_col].value_counts()
                results[attr] = {
                    "type": "categorical",
                    "distribution": positive.to_dict(),
                }

        return {
            "principle": "FEAT_Fairness",
            "decision": decision_col,
            "results": results,
        }

    def ethics_check(self) -> Dict:
        """
        FEAT-E: AI use should be aligned with firm's ethical standards.
        Returns documentation checklist.
        """
        return {
            "principle": "FEAT_Ethics",
            "checklist": [
                "Synthetic agents do not represent real individuals",
                "No individual-level predictions used for real-world decisions",
                "Population-level insights only for policy planning",
                "Simulation disclaimers prominently displayed",
                "No discriminatory scenario design",
            ],
        }


# ============================================================
# Model Card Generator
# ============================================================

def generate_model_card() -> Dict:
    """
    Generate a Model Card for the Digital Twin system.

    Following Mitchell et al. (2019) "Model Cards for Model Reporting"
    and Singapore's AI Verify transparency requirements.
    """
    return {
        "model_name": "Singapore Digital Twin — Synthetic Population Engine",
        "version": "2.0",
        "type": "Agent-based social simulation",

        "data_sources": [
            "Singapore GHS 2025 (aggregate distributions only)",
            "Department of Statistics Singapore (DOS) public tables",
            "HDB resale price index (public)",
            "CPF Board contribution rate tables (public)",
            "Singapore Life Tables 2020 (public)",
        ],

        "synthetic_disclosure": (
            "This system generates SYNTHETIC agents that do not represent "
            "any real individual. All personal attributes are statistically "
            "sampled from aggregate Census distributions using Iterative "
            "Proportional Fitting (IPF). No individual-level data is used "
            "as input at any stage."
        ),

        "methodology": {
            "population_synthesis": "Deming-Stephan IPF on 4D contingency table "
                                    "(age×gender×ethnicity×area, 4704 cells)",
            "attribute_sampling": "Bayesian Network DAG with conditional probability tables",
            "personality": "Big Five via Gaussian Copula (Cholesky decomposition)",
            "decisions": "3-layer: deterministic rules → logistic/Markov probability → LLM reasoning",
            "privacy": "k-Anonymity (k≥5), l-Diversity, controlled rounding (TRS)",
        },

        "decision_pipeline": {
            "layer_1": "Deterministic rules (CPF, NS, education streaming)",
            "layer_2": "Probability models (Markov chains, logistic regression)",
            "layer_3": "LLM persona reasoning (DeepSeek/Claude, logged)",
        },

        "limitations": [
            "20,000 agents represent 5.8M population (1:290 scale)",
            "GHS 2025 distributions may not reflect 2026 reality",
            "Personality traits based on SE Asian averages (Schmitt 2007), "
            "not Singapore-specific norms",
            "Household formation heuristic, not microsimulation",
            "LLM decisions are stochastic and may not reflect actual "
            "human decision-making patterns",
            "Income distribution is approximate (no individual tax data)",
        ],

        "intended_use": [
            "Policy impact simulation (urban planning, public health)",
            "Insurance product design testing",
            "Transport demand modeling",
            "Academic research on agent-based social simulation",
        ],

        "prohibited_use": [
            "Individual-level predictions about real persons",
            "Credit scoring or financial decisions affecting real individuals",
            "Surveillance or profiling of real populations",
            "Discriminatory policy design",
        ],

        "evaluation_metrics": {
            "SRMSE": "Standardized Root Mean Square Error vs Census marginals",
            "chi_square": "Pearson chi-square goodness-of-fit",
            "KL_divergence": "Kullback-Leibler divergence from target distributions",
            "cramers_v": "Association strength between categorical variables",
            "k_anonymity": "Minimum equivalence class size ≥ 5",
        },

        "regulatory_compliance": [
            "PDPA (Personal Data Protection Act 2012)",
            "PDPC Synthetic Data Generation Guide (July 2024)",
            "IMDA Model AI Governance Framework (2020)",
            "IMDA Agentic AI Governance Framework (Jan 2026)",
            "AI Verify 11 Principles (May 2025 update)",
        ],

        "contact": "Digital Twin Singapore Project Team",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
    }
