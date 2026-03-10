"""
Validation & Audit Framework — Mathematical verification modules.

This file defines ALL testable modules in the Digital Twin system,
categorized by:
  A. Internal automated tests (CI/CD)
  B. Mathematical proofs / formal verification
  C. External audit required (academic / regulatory)
  D. Ongoing monitoring (runtime)

Each module specifies:
  - What it validates
  - How to test it
  - What constitutes a PASS
  - Who should audit it (internal / external)
"""

from typing import Dict, List
from datetime import datetime


# ============================================================
# COMPLETE MODULE REGISTRY
# ============================================================

VALIDATION_MODULES = {

    # ==========================================================
    # CATEGORY A: Population Synthesis Accuracy
    # (Internal automated + External academic validation)
    # ==========================================================

    "A1_IPF_Convergence": {
        "description": "Deming-Stephan IPF converges to Census marginals",
        "method": "Compare fitted 4D table marginals vs Census targets",
        "metric": "Max relative deviation across all marginal cells",
        "pass_criterion": "Max deviation < 0.5%",
        "current_result": "Max deviation = 0.05% (PASS)",
        "test_type": "automated",
        "audit_level": "internal",
        "file": "engine/synthesis/math_core.py:DemingStephanIPF",
    },

    "A2_Marginal_Distributions": {
        "description": "Each demographic variable matches GHS 2025",
        "method": "Chi-square GoF + SRMSE for each marginal",
        "metric": "SRMSE (Standardized Root Mean Square Error)",
        "pass_criterion": "SRMSE < 0.10 (GOOD) for all variables",
        "current_result": {
            "age": "0.005 EXCELLENT",
            "gender": "0.002 EXCELLENT",
            "ethnicity": "0.003 EXCELLENT",
            "area": "0.008 EXCELLENT",
            "housing": "0.186 ACCEPTABLE",
            "education": "0.104 ACCEPTABLE",
        },
        "test_type": "automated",
        "audit_level": "external_academic",
        "external_auditor": "Statistics department or Census authority",
        "file": "scripts/04_validate_population.py",
    },

    "A3_Joint_Distributions": {
        "description": "Cross-tabulations match known Census patterns",
        "method": "Cramer's V + chi-square independence test",
        "metric": "Cramer's V direction and magnitude",
        "pass_criterion": "V direction matches Census (e.g., age×education: V>0.3)",
        "test_type": "automated",
        "audit_level": "external_academic",
        "external_auditor": "Social science / demography department",
        "file": "scripts/04_validate_population.py:test_joint_distribution",
    },

    "A4_Correlation_Structure": {
        "description": "Continuous variable correlations match literature",
        "method": "Pearson r + Spearman rho, sign and magnitude",
        "metric": "Correlation coefficient sign + |r| > 0.01",
        "pass_criterion": "All correlation signs match expected direction",
        "test_type": "automated",
        "audit_level": "internal",
        "file": "scripts/04_validate_population.py:test_correlation",
    },

    "A5_Household_Structure": {
        "description": "Household size distribution matches GHS 2025",
        "method": "Compare size dist vs Census target (1-8+ person)",
        "metric": "Mean household size + size distribution SRMSE",
        "pass_criterion": "Mean size within 0.5 of 3.16",
        "current_result": "Mean = 2.67, gap = 0.49 (PASS, borderline)",
        "improvement_needed": "Reduce single-person from 35% to ~15%",
        "test_type": "automated",
        "audit_level": "external_academic",
        "external_auditor": "DOS or housing research institute",
        "file": "engine/synthesis/household_builder.py",
    },

    "A6_Personality_Traits": {
        "description": "Big Five means match SE Asian norms (Schmitt 2007)",
        "method": "Mean comparison + inter-trait correlation matrix",
        "metric": "Absolute deviation from reference means",
        "pass_criterion": "Each trait mean within 0.15 of SE Asian baseline",
        "test_type": "automated",
        "audit_level": "external_academic",
        "external_auditor": "Psychology department (NUS/NTU/SMU)",
        "file": "engine/synthesis/personality_init.py",
    },

    "A7_Controlled_Rounding": {
        "description": "TRS integerization preserves marginal totals exactly",
        "method": "Verify sum(rounded) == sum(expected) for each marginal",
        "metric": "Marginal total deviation (must be 0)",
        "pass_criterion": "All marginal totals exactly match",
        "test_type": "automated + formal_proof",
        "audit_level": "internal",
        "file": "engine/synthesis/math_core.py:controlled_rounding",
    },

    # ==========================================================
    # CATEGORY B: Transition & Event Model Accuracy
    # (External actuarial / demographic validation)
    # ==========================================================

    "B1_Mortality_Model": {
        "description": "Gompertz mortality matches Singapore Life Tables",
        "method": "Compare q(x) curves with DOS/MOM life tables",
        "metric": "Max absolute deviation of age-specific mortality rates",
        "pass_criterion": "Within 20% of official rates at all ages",
        "current_result": "Age 30: 0.035% (actual ~0.03%), Age 85: 3.64% (actual ~4%)",
        "test_type": "automated",
        "audit_level": "external_actuarial",
        "external_auditor": "Singapore Actuarial Society / Life Insurance Association",
        "file": "engine/models/probability_models.py",
    },

    "B2_Markov_Transition_Matrices": {
        "description": "Job/marital/health transitions produce realistic steady states",
        "method": "Compute stationary distribution, compare with Census",
        "metric": "Stationary dist vs Census marginals",
        "pass_criterion": "KL divergence < 0.05 from Census distribution",
        "test_type": "automated",
        "audit_level": "external_academic",
        "external_auditor": "Econometrics / labor economics department",
        "file": "engine/models/probability_models.py:MarkovTransitionModel",
    },

    "B3_Fertility_Model": {
        "description": "Birth rates reproduce Singapore TFR (~1.1)",
        "method": "Run 10-year simulation, measure births per woman",
        "metric": "Simulated TFR vs official TFR",
        "pass_criterion": "Simulated TFR within 0.2 of official 1.1",
        "test_type": "simulation",
        "audit_level": "external_academic",
        "external_auditor": "Demography unit (IPS/NUS)",
        "file": "engine/models/probability_models.py",
    },

    "B4_CPF_Model": {
        "description": "CPF accumulation matches official rates and rules",
        "method": "Simulate lifetime CPF for reference profiles",
        "metric": "OA/SA/MA balances vs CPF Board calculators",
        "pass_criterion": "Within 5% of official calculator at age 55",
        "test_type": "automated",
        "audit_level": "external_regulatory",
        "external_auditor": "CPF Board / MOM",
        "file": "engine/models/cpf_model.py",
    },

    "B5_Marriage_Model": {
        "description": "Age-specific marriage rates match GHS 2025",
        "method": "Compare married% at age 30-34 after 5-year simulation",
        "metric": "Married proportion at 30-34",
        "pass_criterion": "Within 10% of Census 60%",
        "current_result": "59.7% (PASS)",
        "test_type": "automated",
        "audit_level": "internal",
        "file": "engine/models/probability_models.py",
    },

    "B6_Income_Distribution": {
        "description": "Income distribution matches MOM/DOS statistics",
        "method": "Compare median, Gini coefficient, percentile ratios",
        "metric": "Median income + Gini coefficient",
        "pass_criterion": "Median within 30% of $4,534; Gini within 0.05 of 0.458",
        "current_result": "Median $4,851 (PASS)",
        "test_type": "automated",
        "audit_level": "external_academic",
        "external_auditor": "Economics department / MOM",
        "file": "scripts/03_synthesize_v2_mathematical.py",
    },

    # ==========================================================
    # CATEGORY C: Privacy & Data Protection
    # (External regulatory / legal audit required)
    # ==========================================================

    "C1_PDPA_Compliance": {
        "description": "No direct identifiers, purpose limitation enforced",
        "method": "Column audit + purpose schema validation",
        "metric": "Zero direct identifiers in output",
        "pass_criterion": "No NRIC, name, address, DOB in any output",
        "test_type": "automated",
        "audit_level": "external_legal",
        "external_auditor": "PDPC-certified Data Protection Officer",
        "file": "engine/compliance/privacy_engine.py:PDPAComplianceChecker",
    },

    "C2_k_Anonymity": {
        "description": "Every quasi-identifier combination appears k+ times",
        "method": "Group by QIs, check min group size",
        "metric": "Minimum equivalence class size",
        "pass_criterion": "k >= 5",
        "test_type": "automated",
        "audit_level": "external_technical",
        "external_auditor": "Privacy engineering firm / PDPC sandbox",
        "file": "engine/compliance/privacy_engine.py:PrivacyMetrics.k_anonymity",
    },

    "C3_l_Diversity": {
        "description": "Each equivalence class has diverse sensitive values",
        "method": "Check distinct values of sensitive attrs per QI group",
        "metric": "Minimum distinct values per equivalence class",
        "pass_criterion": "l >= 3 for income, health_status",
        "test_type": "automated",
        "audit_level": "external_technical",
        "external_auditor": "Privacy engineering firm",
        "file": "engine/compliance/privacy_engine.py:PrivacyMetrics.l_diversity",
    },

    "C4_Reidentification_Risk": {
        "description": "Prosecutor & journalist attack risk below thresholds",
        "method": "PDPC 5-step risk evaluation framework",
        "metric": "Max prosecutor risk; journalist risk",
        "pass_criterion": "Prosecutor < 0.20, Journalist < 0.05",
        "test_type": "automated + manual_review",
        "audit_level": "external_regulatory",
        "external_auditor": "PDPC / certified privacy assessor",
        "file": "engine/compliance/privacy_engine.py:ReIdentificationRiskAssessor",
    },

    "C5_Synthetic_Data_Guide": {
        "description": "Compliance with PDPC Synthetic Data Generation Guide",
        "method": "5-step checklist (Know Data → Prep → Generate → Evaluate → Manage)",
        "metric": "All 5 steps documented and evidenced",
        "pass_criterion": "Full compliance with all 5 steps",
        "test_type": "documentation_review",
        "audit_level": "external_regulatory",
        "external_auditor": "PDPC / legal counsel",
        "file": "engine/compliance/privacy_engine.py",
    },

    "C6_Cross_Border_Transfer": {
        "description": "Data transfer controls if API serves overseas clients",
        "method": "PDPA Section 26 Transfer Limitation Obligation",
        "metric": "Contractual safeguards in place",
        "pass_criterion": "Legally enforceable obligations for all recipients",
        "test_type": "legal_review",
        "audit_level": "external_legal",
        "external_auditor": "Legal counsel (data protection specialist)",
        "file": "N/A — contractual, not code",
    },

    # ==========================================================
    # CATEGORY D: AI Governance & Fairness
    # (External AI governance audit)
    # ==========================================================

    "D1_AI_Verify_Compliance": {
        "description": "Compliance with 11 AI Verify principles",
        "method": "Self-assessment + evidence collection per principle",
        "metric": "Principles passed / total principles",
        "pass_criterion": "All 11 principles addressed (8+ passed)",
        "test_type": "self_assessment + external_verification",
        "audit_level": "external_ai_governance",
        "external_auditor": "AI Verify Foundation / IMDA",
        "file": "engine/compliance/ai_governance.py:AIVerifyAssessment",
    },

    "D2_Agentic_AI_Risk_Registry": {
        "description": "All agentic AI risks identified and mitigated",
        "method": "IMDA 2026 Agentic AI Framework 4-dimension assessment",
        "metric": "Zero CRITICAL unmitigated risks",
        "pass_criterion": "All CRITICAL risks have mitigation plans",
        "test_type": "manual_review",
        "audit_level": "external_ai_governance",
        "external_auditor": "IMDA / AI governance consultancy",
        "file": "engine/compliance/ai_governance.py:AgenticAIGovernance",
    },

    "D3_Fairness_Audit": {
        "description": "No discriminatory bias in agent outcomes",
        "method": "Disparate impact ratio (80% rule) across protected attrs",
        "metric": "Min disparate impact ratio",
        "pass_criterion": "All protected groups >= 0.80 of max group",
        "test_type": "automated + expert_review",
        "audit_level": "external_academic",
        "external_auditor": "Fairness/ethics research group (NUS AISG / SMU)",
        "file": "engine/compliance/ai_governance.py:AIVerifyAssessment.assess_fairness",
    },

    "D4_Explainability": {
        "description": "95%+ of agent decisions are explainable",
        "method": "Trace each decision to rules/coefficients/LLM reasoning",
        "metric": "Explainability ratio",
        "pass_criterion": ">= 95% decisions have traceable reasoning",
        "test_type": "automated",
        "audit_level": "internal + external_spot_check",
        "external_auditor": "AI Verify assessment partner",
        "file": "engine/compliance/ai_governance.py:AIVerifyAssessment.assess_explainability",
    },

    "D5_Reproducibility": {
        "description": "Same seed produces identical synthetic population",
        "method": "SHA-256 hash comparison of two runs with same seed",
        "metric": "Hash match (boolean)",
        "pass_criterion": "100% identical output",
        "test_type": "automated",
        "audit_level": "internal",
        "file": "engine/compliance/ai_governance.py:AIVerifyAssessment.assess_reproducibility",
    },

    "D6_MAS_FEAT": {
        "description": "Financial services fairness (if insurance vertical used)",
        "method": "MAS FEAT 4-principle assessment",
        "metric": "Compliance with Fairness, Ethics, Accountability, Transparency",
        "pass_criterion": "Full compliance when used for insurance/finance",
        "test_type": "conditional — only if financial vertical",
        "audit_level": "external_regulatory",
        "external_auditor": "MAS / compliance officer",
        "file": "engine/compliance/ai_governance.py:MASFEATCompliance",
    },

    # ==========================================================
    # CATEGORY E: LLM Decision Engine Safety
    # (External AI safety audit)
    # ==========================================================

    "E1_LLM_Prompt_Safety": {
        "description": "LLM prompts do not leak private agent data",
        "method": "Prompt template audit + output scanning",
        "metric": "Zero data leakage incidents in test runs",
        "pass_criterion": "No real-world-identifiable info in prompts/responses",
        "test_type": "automated + red_team",
        "audit_level": "external_ai_safety",
        "external_auditor": "AI safety firm / red team service",
        "file": "engine/llm/decision_engine.py",
    },

    "E2_LLM_Decision_Bounds": {
        "description": "LLM cannot produce actions outside defined action space",
        "method": "Structured JSON output validation + action whitelist",
        "metric": "Percentage of valid actions",
        "pass_criterion": "100% actions within defined action space",
        "test_type": "automated",
        "audit_level": "internal",
        "file": "engine/llm/decision_engine.py",
    },

    "E3_LLM_Bias_Testing": {
        "description": "LLM decisions don't show demographic bias",
        "method": "Counterfactual testing (same scenario, different demographics)",
        "metric": "Decision variance across demographic counterfactuals",
        "pass_criterion": "No statistically significant bias (p > 0.05)",
        "test_type": "automated + expert_review",
        "audit_level": "external_academic",
        "external_auditor": "AI fairness research lab",
        "file": "engine/llm/decision_engine.py",
    },

    # ==========================================================
    # CATEGORY F: System Integrity
    # ==========================================================

    "F1_Data_Lineage": {
        "description": "Full traceability from Census → IPF → Agent → Decision",
        "method": "Audit trail review",
        "metric": "Every output traceable to input + transformation",
        "pass_criterion": "Complete lineage for 100% of outputs",
        "test_type": "documentation + automated_logging",
        "audit_level": "external_regulatory",
        "external_auditor": "Auditing firm / PDPC",
        "file": "engine/compliance/privacy_engine.py:AuditLogger",
    },

    "F2_Model_Card": {
        "description": "Complete model documentation per Mitchell et al. (2019)",
        "method": "Model card completeness check",
        "metric": "All required sections present",
        "pass_criterion": "Data sources, methodology, limitations, intended use documented",
        "test_type": "documentation_review",
        "audit_level": "external_ai_governance",
        "external_auditor": "AI Verify assessment partner",
        "file": "engine/compliance/ai_governance.py:generate_model_card",
    },
}


def get_modules_by_audit_level() -> Dict[str, List[str]]:
    """Group modules by who needs to audit them."""
    by_level = {}
    for mod_id, mod in VALIDATION_MODULES.items():
        level = mod["audit_level"]
        # Handle compound levels like "internal + external_spot_check"
        for sub_level in level.split(" + "):
            sub_level = sub_level.strip()
            by_level.setdefault(sub_level, []).append(mod_id)
    return by_level


def get_modules_needing_external_audit() -> List[Dict]:
    """Return all modules requiring external validation."""
    external = []
    for mod_id, mod in VALIDATION_MODULES.items():
        if "external" in mod["audit_level"]:
            external.append({
                "module": mod_id,
                "description": mod["description"],
                "auditor": mod.get("external_auditor", "TBD"),
                "test_type": mod["test_type"],
            })
    return external


def get_engineering_tasks() -> List[Dict]:
    """Return engineering work needed to complete all validation modules."""
    tasks = [
        {
            "id": "ENG-01",
            "module": "C2_k_Anonymity",
            "task": "Integrate k-anonymity check into synthesis pipeline (post-generation)",
            "status": "DONE",
            "file": "engine/synthesis/math_core.py",
        },
        {
            "id": "ENG-02",
            "module": "C3_l_Diversity",
            "task": "Add l-diversity enforcement after household assignment",
            "status": "TODO",
            "file": "engine/compliance/privacy_engine.py",
        },
        {
            "id": "ENG-03",
            "module": "C4_Reidentification_Risk",
            "task": "Build automated re-identification attack simulator",
            "status": "DONE",
            "file": "engine/compliance/privacy_engine.py",
        },
        {
            "id": "ENG-04",
            "module": "D4_Explainability",
            "task": "Add decision logging to tick_manager (layer, reason, coefficients)",
            "status": "TODO",
            "file": "engine/pipeline/tick_manager.py",
        },
        {
            "id": "ENG-05",
            "module": "D5_Reproducibility",
            "task": "Add SHA-256 hash of output CSV to validation report",
            "status": "TODO",
            "file": "scripts/04_validate_population.py",
        },
        {
            "id": "ENG-06",
            "module": "E1_LLM_Prompt_Safety",
            "task": "Add prompt sanitization — strip sensitive attributes before LLM call",
            "status": "TODO",
            "file": "engine/llm/decision_engine.py",
        },
        {
            "id": "ENG-07",
            "module": "E2_LLM_Decision_Bounds",
            "task": "Add JSON schema validation on LLM response + action whitelist",
            "status": "TODO",
            "file": "engine/llm/decision_engine.py",
        },
        {
            "id": "ENG-08",
            "module": "E3_LLM_Bias_Testing",
            "task": "Build counterfactual test harness (same scenario, swap demographics)",
            "status": "TODO",
            "file": "engine/compliance/ai_governance.py",
        },
        {
            "id": "ENG-09",
            "module": "F1_Data_Lineage",
            "task": "Integrate AuditLogger into synthesis pipeline + tick engine",
            "status": "TODO",
            "file": "engine/compliance/privacy_engine.py",
        },
        {
            "id": "ENG-10",
            "module": "A5_Household_Structure",
            "task": "Improve household builder: reduce 1-person from 35% to 15%",
            "status": "TODO",
            "file": "engine/synthesis/household_builder.py",
        },
        {
            "id": "ENG-11",
            "module": "A2_Marginal_Distributions",
            "task": "Improve housing SRMSE from 0.186 to <0.10",
            "status": "TODO",
            "file": "scripts/03_synthesize_v2_mathematical.py",
        },
        {
            "id": "ENG-12",
            "module": "B3_Fertility_Model",
            "task": "Build TFR validation: run 10-year sim, measure births/woman",
            "status": "TODO",
            "file": "engine/models/probability_models.py",
        },
        {
            "id": "ENG-13",
            "module": "D1_AI_Verify_Compliance",
            "task": "Run full AI Verify self-assessment and generate evidence pack",
            "status": "TODO",
            "file": "engine/compliance/ai_governance.py",
        },
        {
            "id": "ENG-14",
            "module": "C5_Synthetic_Data_Guide",
            "task": "Write PDPC 5-step compliance documentation",
            "status": "TODO",
            "file": "docs/pdpc_synthetic_data_compliance.md",
        },
        {
            "id": "ENG-15",
            "module": "D2_Agentic_AI_Risk_Registry",
            "task": "Populate risk registry with all identified agentic AI risks",
            "status": "TODO",
            "file": "engine/compliance/ai_governance.py",
        },
    ]
    return tasks


def print_summary():
    """Print human-readable summary of all validation modules."""
    modules = VALIDATION_MODULES
    external = get_modules_needing_external_audit()
    tasks = get_engineering_tasks()

    print("=" * 70)
    print("SINGAPORE DIGITAL TWIN — VALIDATION & AUDIT FRAMEWORK")
    print("=" * 70)

    print(f"\nTotal validation modules: {len(modules)}")

    by_level = get_modules_by_audit_level()
    print("\n--- By Audit Level ---")
    for level, mods in sorted(by_level.items()):
        print(f"  {level}: {len(mods)} modules")

    print(f"\n--- External Audit Required: {len(external)} modules ---")
    for ext in external:
        print(f"  [{ext['module']}] {ext['description']}")
        print(f"    Auditor: {ext['auditor']}")

    print(f"\n--- Engineering Tasks: {len(tasks)} ---")
    done = sum(1 for t in tasks if t["status"] == "DONE")
    todo = sum(1 for t in tasks if t["status"] == "TODO")
    print(f"  Done: {done}, TODO: {todo}")
    for t in tasks:
        status = "DONE" if t["status"] == "DONE" else "TODO"
        print(f"  [{status}] {t['id']}: {t['task']}")


if __name__ == "__main__":
    print_summary()
