"""
Layer 2: Probability Models — Singapore-calibrated life event models.

Each model is either:
1. A logistic regression: P(event) = sigmoid(Xβ)
2. A Markov transition matrix: P(next_state | current_state, covariates)
3. A survival model: hazard function h(t) for time-to-event

All coefficients are calibrated to Singapore administrative data:
- MOM Labour Force Survey 2020 (job transitions)
- GHS 2025 (marriage/divorce/fertility rates by age)
- MOH National Health Survey (chronic disease incidence)
- MAS Financial Stability Report (default/lapse rates)

Cost: ~zero per evaluation (matrix lookup + RNG draw)
"""

import numpy as np
from typing import Dict, Optional
from engine.synthesis.math_core import MarkovTransitionModel, LogisticEventModel
import logging

logger = logging.getLogger(__name__)


def build_all_models(seed: int = 42) -> Dict[str, object]:
    """Build all Layer 2 probability models."""
    models = {}

    # ============================================================
    # 1. JOB TRANSITION (Markov chain)
    # ============================================================
    # States: employed, unemployed, self_employed, retired, student, ns
    job_model = MarkovTransitionModel(
        "job_status",
        ["employed", "unemployed", "self_employed", "retired", "student", "ns"],
        seed=seed,
    )

    # Annual transition matrix (Singapore 2020)
    # Unemployment rate ~3%, self-employment ~15%
    T_job = np.array([
        # emp    unemp   self    ret    stud    ns
        [0.920, 0.025, 0.015, 0.030, 0.005, 0.005],  # employed
        [0.450, 0.400, 0.080, 0.050, 0.015, 0.005],  # unemployed
        [0.050, 0.030, 0.880, 0.035, 0.005, 0.000],  # self-employed
        [0.020, 0.005, 0.010, 0.960, 0.005, 0.000],  # retired
        [0.150, 0.020, 0.010, 0.000, 0.810, 0.010],  # student
        [0.200, 0.010, 0.005, 0.000, 0.100, 0.685],  # ns
    ])
    job_model.set_base_matrix(T_job)

    # Age adjustment: older workers have lower mobility
    def age_adjust_job(T, agent):
        age = agent.get("age", 30)
        if age > 55:
            # Higher retirement probability
            T[:, 3] *= 1 + 0.05 * (age - 55)
            # Lower employment retention
            T[0, 0] *= 0.98
        elif age < 25:
            # Higher student ↔ employment
            T[4, 0] *= 1.3
        # Re-normalize
        row_sums = T.sum(axis=1, keepdims=True)
        return T / np.maximum(row_sums, 1e-10)

    job_model.add_covariate_adjustment(age_adjust_job)
    models["job_transition"] = job_model

    # ============================================================
    # 2. MARITAL STATUS TRANSITION (Markov chain)
    # ============================================================
    marital_model = MarkovTransitionModel(
        "marital_status",
        ["Single", "Married", "Divorced", "Widowed"],
        seed=seed,
    )

    # Annual transition matrix
    # Singapore: median age at first marriage ~30 (M), ~28 (F)
    # Crude marriage rate ~6.5 per 1000, divorce ~1.8 per 1000 married
    T_marital = np.array([
        # Single  Married  Divorced  Widowed
        [0.950,  0.050,   0.000,    0.000],  # Single
        [0.000,  0.990,   0.007,    0.003],  # Married
        [0.000,  0.020,   0.975,    0.005],  # Divorced
        [0.000,  0.005,   0.000,    0.995],  # Widowed
    ])
    marital_model.set_base_matrix(T_marital)

    def age_adjust_marital(T, agent):
        age = agent.get("age", 30)
        gender = agent.get("gender", "M")

        # Marriage rate peaks at 28-32
        if 25 <= age <= 35:
            T[0, 1] *= 1.5  # higher single→married
        elif age < 22:
            T[0, 1] *= 0.1  # very low for youth
        elif age > 50:
            T[0, 1] *= 0.3  # lower for older singles

        # Widowhood increases with age
        if age > 65:
            T[1, 3] *= 1 + 0.02 * (age - 65)
        # Women more likely to be widowed (life expectancy gap)
        if gender == "F" and age > 60:
            T[1, 3] *= 1.5

        row_sums = T.sum(axis=1, keepdims=True)
        return T / np.maximum(row_sums, 1e-10)

    marital_model.add_covariate_adjustment(age_adjust_marital)
    models["marital_transition"] = marital_model

    # ============================================================
    # 3. HEALTH STATUS TRANSITION (Markov chain)
    # ============================================================
    health_model = MarkovTransitionModel(
        "health_status",
        ["Healthy", "Chronic_Mild", "Chronic_Severe", "Disabled"],
        seed=seed,
    )

    # Annual transition matrix
    # Based on MOH chronic disease progression data
    T_health = np.array([
        # Healthy  Mild    Severe  Disabled
        [0.970,   0.025,  0.004,  0.001],   # Healthy
        [0.020,   0.940,  0.035,  0.005],   # Chronic_Mild
        [0.005,   0.020,  0.940,  0.035],   # Chronic_Severe
        [0.001,   0.004,  0.015,  0.980],   # Disabled
    ])
    health_model.set_base_matrix(T_health)

    def age_adjust_health(T, agent):
        age = agent.get("age", 30)
        # Disease progression accelerates with age
        if age > 40:
            factor = 1 + 0.02 * (age - 40)
            T[0, 1] *= factor  # healthy → mild
            T[1, 2] *= factor  # mild → severe
            T[2, 3] *= factor  # severe → disabled
        # Smoking increases risk
        if agent.get("smoking", False):
            T[0, 1] *= 1.5
            T[1, 2] *= 1.3
        row_sums = T.sum(axis=1, keepdims=True)
        return T / np.maximum(row_sums, 1e-10)

    health_model.add_covariate_adjustment(age_adjust_health)
    models["health_transition"] = health_model

    # ============================================================
    # 4. LOGISTIC EVENT MODELS
    # ============================================================

    # First child (annual probability for married, no children)
    # Singapore TFR = 1.1 (2020), one of the lowest in the world
    models["first_child"] = LogisticEventModel(
        "first_child",
        coefficients={
            "age": -0.08,          # sharp decline after 30
            "monthly_income": 0.000015,  # slight positive effect
        },
        intercept=-1.5,
        annual=True,
    )

    # Additional child (annual probability for married with children)
    models["additional_child"] = LogisticEventModel(
        "additional_child",
        coefficients={
            "age": -0.10,
            "num_children": -0.60,  # strong negative: each child reduces probability
            "monthly_income": 0.000010,
        },
        intercept=-1.8,
        annual=True,
    )

    # BTO application (annual probability for eligible singles/couples)
    models["bto_application"] = LogisticEventModel(
        "bto_application",
        coefficients={
            "age": 0.05,
            "monthly_income": 0.00003,
        },
        intercept=-4.0,
        annual=True,
    )

    # Insurance purchase (annual probability for uninsured)
    models["insurance_purchase"] = LogisticEventModel(
        "insurance_purchase",
        coefficients={
            "age": 0.02,
            "monthly_income": 0.00005,
        },
        intercept=-3.0,
        annual=True,
    )

    # Voluntary savings increase (annual)
    models["savings_increase"] = LogisticEventModel(
        "savings_increase",
        coefficients={
            "monthly_income": 0.00004,
            "age": 0.01,
        },
        intercept=-2.5,
        annual=True,
    )

    # Death (annual probability)
    # Singapore life expectancy: M=81.0, F=85.4 (2020)
    # Gompertz mortality: log(h(t)) = alpha + beta * t
    models["death"] = LogisticEventModel(
        "death",
        coefficients={
            "age": 0.085,  # Gompertz beta (doubles every ~8 years)
        },
        intercept=-10.5,  # Gompertz alpha (very low baseline)
        annual=True,
    )

    logger.info(f"Built {len(models)} probability models")
    return models


class ProbabilityEngine:
    """
    Layer 2 decision engine: evaluates all probability models for an agent.

    For each active agent per tick:
    1. Check all applicable Markov models for state transitions
    2. Check all applicable logistic models for event triggering
    3. Return list of triggered events with probabilities
    """

    def __init__(self, seed: int = 42):
        self.models = build_all_models(seed)
        self.rng = np.random.default_rng(seed)

    def evaluate(self, agent: dict) -> list:
        """
        Evaluate all models for one agent.

        Returns list of triggered events:
        [{"event": "marriage", "probability": 0.003, "details": {...}}, ...]
        """
        triggered = []
        age = agent.get("age", 0)

        # Markov transitions (daily probability = 1 - (1-annual)^(1/365))
        # Job transition (only for working-age)
        if 15 <= age <= 70:
            current_job = agent.get("job_status", "employed")
            if current_job in self.models["job_transition"].states:
                T = self.models["job_transition"].get_transition_matrix(agent)
                i = self.models["job_transition"].state_to_idx[current_job]
                # Convert annual to daily
                T_daily = self._annual_to_daily_matrix(T)
                new_state = self.rng.choice(
                    self.models["job_transition"].states,
                    p=T_daily[i])
                if new_state != current_job:
                    triggered.append({
                        "event": "job_transition",
                        "from": current_job,
                        "to": new_state,
                        "probability": float(T_daily[i, self.models["job_transition"].state_to_idx[new_state]]),
                    })

        # Marital transition (15+)
        if age >= 15:
            current_marital = agent.get("marital_status", "Single")
            if current_marital in self.models["marital_transition"].states:
                T = self.models["marital_transition"].get_transition_matrix(agent)
                i = self.models["marital_transition"].state_to_idx[current_marital]
                T_daily = self._annual_to_daily_matrix(T)
                new_state = self.rng.choice(
                    self.models["marital_transition"].states,
                    p=T_daily[i])
                if new_state != current_marital:
                    triggered.append({
                        "event": "marital_transition",
                        "from": current_marital,
                        "to": new_state,
                        "probability": float(T_daily[i, self.models["marital_transition"].state_to_idx[new_state]]),
                    })

        # Health transition (all ages)
        current_health = agent.get("health_status", "Healthy")
        if current_health in self.models["health_transition"].states:
            T = self.models["health_transition"].get_transition_matrix(agent)
            i = self.models["health_transition"].state_to_idx[current_health]
            T_daily = self._annual_to_daily_matrix(T)
            new_state = self.rng.choice(
                self.models["health_transition"].states,
                p=T_daily[i])
            if new_state != current_health:
                triggered.append({
                    "event": "health_transition",
                    "from": current_health,
                    "to": new_state,
                    "probability": float(T_daily[i, self.models["health_transition"].state_to_idx[new_state]]),
                })

        # Logistic event models
        # First child
        if (agent.get("marital_status") == "Married"
                and agent.get("num_children", 0) == 0
                and 22 <= age <= 45):
            if self.models["first_child"].should_trigger(agent, self.rng):
                triggered.append({
                    "event": "first_child",
                    "probability": self.models["first_child"].predict_probability(agent),
                })

        # Additional child
        if (agent.get("marital_status") == "Married"
                and agent.get("num_children", 0) > 0
                and age <= 45):
            if self.models["additional_child"].should_trigger(agent, self.rng):
                triggered.append({
                    "event": "additional_child",
                    "probability": self.models["additional_child"].predict_probability(agent),
                })

        # Death (Gompertz model)
        if self.models["death"].should_trigger(agent, self.rng):
            triggered.append({
                "event": "death",
                "probability": self.models["death"].predict_probability(agent),
            })

        return triggered

    @staticmethod
    def _annual_to_daily_matrix(T_annual: np.ndarray) -> np.ndarray:
        """
        Convert annual transition matrix to daily.

        Using matrix power: T_daily = T_annual^(1/365)

        For computational stability, use eigendecomposition:
        T = V * diag(lambda) * V^-1
        T^(1/n) = V * diag(lambda^(1/n)) * V^-1
        """
        n = T_annual.shape[0]
        try:
            eigenvalues, V = np.linalg.eig(T_annual)
            # Take 1/365 power of eigenvalues
            eigenvalues_daily = np.power(np.abs(eigenvalues), 1/365)
            T_daily = np.real(V @ np.diag(eigenvalues_daily) @ np.linalg.inv(V))
            # Ensure valid probabilities
            T_daily = np.maximum(T_daily, 0)
            row_sums = T_daily.sum(axis=1, keepdims=True)
            T_daily = T_daily / np.maximum(row_sums, 1e-10)
            return T_daily
        except np.linalg.LinAlgError:
            # Fallback: approximate as I + (T-I)/365
            return np.eye(n) + (T_annual - np.eye(n)) / 365
