"""
Rule Engine (Layer 1) — Deterministic life rules for Singapore.

Zero-cost, runs for every active agent every tick.
Handles:
- Life phase transitions (age-based)
- CPF contribution calculations
- NS enlistment/ORD
- Birthday aging
- Mandatory insurance transitions (MediShield Life, CareShield Life)
- Education streaming (PSLE → O-Level → JC/Poly/ITE)
- Retirement age triggers
"""

from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class LifeRuleEngine:
    """Deterministic rule engine for Singapore life events."""

    def evaluate(self, agent: dict, tick: int, sim_date: str) -> List[dict]:
        """
        Evaluate all rules for one agent.

        Args:
            agent: Agent attributes dict
            tick: Current simulation tick
            sim_date: Current simulation date (YYYY-MM-DD)

        Returns:
            List of actions to apply (field changes + events)
        """
        actions = []

        actions.extend(self._check_life_phase_transition(agent))
        actions.extend(self._check_cpf_contribution(agent))
        actions.extend(self._check_ns_rules(agent))
        actions.extend(self._check_education_rules(agent))
        actions.extend(self._check_retirement_rules(agent))
        actions.extend(self._check_health_rules(agent))

        return actions

    def _check_life_phase_transition(self, agent: dict) -> List[dict]:
        """Check if agent should transition to a new life phase."""
        actions = []
        age = agent.get("age", 0)
        phase = agent.get("life_phase", "establishment")
        gender = agent.get("gender", "M")
        ns = agent.get("ns_status", "Not_Applicable")
        health = agent.get("health_status", "Healthy")

        new_phase = None

        if phase == "dependence" and age >= 7:
            new_phase = "growth"
        elif phase == "growth" and age >= 13:
            new_phase = "adolescence"
        elif phase == "adolescence":
            if age >= 17 and gender == "M" and ns == "Pre_Enlistment":
                new_phase = "ns_service"
                actions.append({
                    "type": "field_change",
                    "field": "ns_status",
                    "value": "Serving_NSF",
                    "reason": "NS enlistment at 18",
                })
            elif age >= 17 and (gender == "F" or ns in ("Not_Applicable", "Exempt")):
                new_phase = "establishment"
        elif phase == "ns_service" and age >= 20:
            new_phase = "establishment"
            actions.append({
                "type": "field_change",
                "field": "ns_status",
                "value": "Active_NSmen",
                "reason": "ORD — operationally ready",
            })
        elif phase == "establishment" and age >= 36:
            new_phase = "bearing"
        elif phase == "bearing" and age >= 51:
            new_phase = "release"
        elif phase == "release" and age >= 63:
            new_phase = "retirement_early"
        elif phase == "retirement_early" and (age >= 75 or health == "Chronic_Severe"):
            new_phase = "decline"
        elif phase == "decline" and (age >= 85 or health == "Disabled"):
            new_phase = "end_of_life"

        if new_phase:
            actions.append({
                "type": "field_change",
                "field": "life_phase",
                "value": new_phase,
                "reason": f"Life phase transition: {phase} → {new_phase}",
            })
            logger.debug(f"Agent {agent.get('agent_id')}: {phase} → {new_phase}")

        return actions

    def _check_cpf_contribution(self, agent: dict) -> List[dict]:
        """Calculate monthly CPF contributions based on age and income."""
        actions = []
        age = agent.get("age", 0)
        income = agent.get("monthly_income", 0)
        residency = agent.get("residency_status", "Citizen")

        if income <= 0 or age < 16 or age > 70:
            return actions
        if residency not in ("Citizen", "PR"):
            return actions

        # CPF contribution rates (2024, simplified)
        # Employee + Employer total allocation
        if age <= 55:
            oa_rate = 0.23   # OA
            sa_rate = 0.06   # SA
            ma_rate = 0.08   # MA
        elif age <= 60:
            oa_rate = 0.15
            sa_rate = 0.045
            ma_rate = 0.075
        elif age <= 65:
            oa_rate = 0.085
            sa_rate = 0.03
            ma_rate = 0.065
        else:
            oa_rate = 0.06
            sa_rate = 0.02
            ma_rate = 0.05

        # PR gets graduated rates (simplified: 80% of citizen rates for first 2 years)
        if residency == "PR":
            years = agent.get("years_in_sg", 0)
            if years < 2:
                oa_rate *= 0.6
                sa_rate *= 0.6
                ma_rate *= 0.6
            elif years < 3:
                oa_rate *= 0.8
                sa_rate *= 0.8
                ma_rate *= 0.8

        # Cap at ordinary wage ceiling ($6,800/month as of 2024)
        capped_income = min(income, 6800)

        cpf_oa_add = int(capped_income * oa_rate)
        cpf_sa_add = int(capped_income * sa_rate)
        cpf_ma_add = int(capped_income * ma_rate)

        actions.append({
            "type": "cpf_contribution",
            "cpf_oa_add": cpf_oa_add,
            "cpf_sa_add": cpf_sa_add,
            "cpf_ma_add": cpf_ma_add,
            "reason": f"Monthly CPF on ${income} (age {age})",
        })

        return actions

    def _check_ns_rules(self, agent: dict) -> List[dict]:
        """NS-related rules for male citizens/PRs."""
        actions = []
        gender = agent.get("gender")
        residency = agent.get("residency_status")
        age = agent.get("age", 0)
        ns = agent.get("ns_status")

        if gender != "M" or residency not in ("Citizen", "PR"):
            return actions

        # Pre-enlistment → Serving at 18
        if ns == "Pre_Enlistment" and age >= 18:
            actions.append({
                "type": "field_change",
                "field": "ns_status",
                "value": "Serving_NSF",
                "reason": "NS enlistment",
            })

        # Active NSmen → Completed at 40 (or 50 for officers, simplified)
        if ns == "Active_NSmen" and age >= 40:
            actions.append({
                "type": "field_change",
                "field": "ns_status",
                "value": "Completed",
                "reason": "NSmen obligation completed",
            })

        return actions

    def _check_education_rules(self, agent: dict) -> List[dict]:
        """Education streaming rules."""
        actions = []
        age = agent.get("age", 0)
        education = agent.get("education_level", "")

        # PSLE at 12 → secondary
        if age == 12 and education == "Primary":
            actions.append({
                "type": "event",
                "event_type": "psle_exam",
                "reason": "PSLE examination year",
            })

        # O-Level at 16 → streaming
        if age == 16 and education == "Secondary":
            actions.append({
                "type": "event",
                "event_type": "o_level_exam",
                "reason": "O-Level examination year",
            })

        return actions

    def _check_retirement_rules(self, agent: dict) -> List[dict]:
        """Retirement-related rules."""
        actions = []
        age = agent.get("age", 0)
        income = agent.get("monthly_income", 0)

        # Retirement age 63 (2024)
        if age == 63 and income > 0:
            actions.append({
                "type": "event",
                "event_type": "retirement_eligibility",
                "reason": "Reached minimum retirement age (63)",
            })

        # Re-employment age 68
        if age == 68 and income > 0:
            actions.append({
                "type": "event",
                "event_type": "re_employment_end",
                "reason": "Reached re-employment age limit (68)",
            })

        # CPF Life payout at 65
        if age == 65:
            actions.append({
                "type": "event",
                "event_type": "cpf_life_start",
                "reason": "CPF LIFE payout begins at 65",
            })

        return actions

    def _check_health_rules(self, agent: dict) -> List[dict]:
        """Health-related deterministic rules."""
        actions = []
        age = agent.get("age", 0)

        # CareShield Life enrollment at 30 (born 1980+)
        if age == 30:
            actions.append({
                "type": "event",
                "event_type": "careshield_life_enrollment",
                "reason": "Automatic CareShield Life enrollment at 30",
            })

        return actions
