"""
Personality Initializer — Big Five + Attitudes + Risk Appetite

Generates psychologically plausible personality profiles for synthetic agents.

Data sources:
- Schmitt et al. (2007): SE Asian Big Five baseline means & SDs
- Soto et al. (2011): Age trajectories for Big Five traits
- McCrae & Costa (2003): Gender differences in Big Five
- Inter-trait correlation matrix from meta-analyses

Method:
1. Start with SE Asian cultural baseline (Schmitt 2007)
2. Apply age trajectory adjustments (Soto 2011)
3. Apply gender adjustments (McCrae & Costa 2003)
4. Sample from multivariate normal with inter-trait correlations
5. Derive attitudes (risk appetite, social trust, etc.) from Big Five + demographics
"""

import numpy as np
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ============================================================
# SE Asian Big Five Baseline (Schmitt et al. 2007, Table 3)
# Scale: 1-5 (BFI-44 items)
# Region: Southeast Asia (Malaysia, Philippines, Indonesia proxied)
# ============================================================
SE_ASIAN_BASELINE = {
    "O": {"mean": 3.45, "sd": 0.55},  # Openness
    "C": {"mean": 3.30, "sd": 0.58},  # Conscientiousness
    "E": {"mean": 3.20, "sd": 0.60},  # Extraversion
    "A": {"mean": 3.55, "sd": 0.52},  # Agreeableness (higher in Asian cultures)
    "N": {"mean": 2.85, "sd": 0.62},  # Neuroticism
}

# ============================================================
# Age Trajectory Adjustments (Soto et al. 2011)
# Delta from young-adult baseline per decade
# Positive = trait increases with age
# ============================================================
AGE_TRAJECTORIES = {
    # age_decade: {trait: delta}
    0: {"O": 0.0, "C": -0.20, "E": 0.10, "A": -0.15, "N": 0.05},   # 0-9 (child)
    1: {"O": 0.05, "C": -0.10, "E": 0.05, "A": -0.10, "N": 0.10},  # 10-19
    2: {"O": 0.0, "C": 0.0, "E": 0.0, "A": 0.0, "N": 0.0},         # 20-29 (baseline)
    3: {"O": -0.05, "C": 0.10, "E": -0.05, "A": 0.08, "N": -0.08},  # 30-39
    4: {"O": -0.08, "C": 0.15, "E": -0.08, "A": 0.12, "N": -0.12},  # 40-49
    5: {"O": -0.10, "C": 0.18, "E": -0.12, "A": 0.15, "N": -0.15},  # 50-59
    6: {"O": -0.12, "C": 0.20, "E": -0.15, "A": 0.18, "N": -0.18},  # 60-69
    7: {"O": -0.15, "C": 0.18, "E": -0.18, "A": 0.20, "N": -0.20},  # 70-79
    8: {"O": -0.18, "C": 0.15, "E": -0.20, "A": 0.22, "N": -0.22},  # 80-89
    9: {"O": -0.20, "C": 0.12, "E": -0.22, "A": 0.25, "N": -0.25},  # 90-99
    10: {"O": -0.20, "C": 0.12, "E": -0.22, "A": 0.25, "N": -0.25}, # 100
}

# ============================================================
# Gender Adjustments (McCrae & Costa 2003)
# Women tend: higher N, higher A, higher E (warmth facet)
# Men tend: slightly higher O (ideas facet)
# ============================================================
GENDER_ADJUSTMENTS = {
    "M": {"O": 0.05, "C": 0.0, "E": -0.05, "A": -0.10, "N": -0.15},
    "F": {"O": -0.05, "C": 0.0, "E": 0.05, "A": 0.10, "N": 0.15},
}

# ============================================================
# Inter-trait Correlation Matrix (meta-analytic estimates)
# Order: O, C, E, A, N
# ============================================================
TRAIT_CORRELATIONS = np.array([
    [1.00,  0.10,  0.25,  0.10, -0.15],  # O
    [0.10,  1.00,  0.15,  0.20, -0.30],  # C
    [0.25,  0.15,  1.00,  0.15, -0.25],  # E
    [0.10,  0.20,  0.15,  1.00, -0.35],  # A
    [-0.15, -0.30, -0.25, -0.35, 1.00],  # N
])

TRAIT_ORDER = ["O", "C", "E", "A", "N"]


class PersonalityInitializer:
    """Generate Big Five personality profiles for synthetic agents."""

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        # Cholesky decomposition for correlated sampling
        self.cholesky = np.linalg.cholesky(TRAIT_CORRELATIONS)

    def _get_adjusted_means(self, age: int, gender: str) -> np.ndarray:
        """Get trait means adjusted for age and gender."""
        decade = min(age // 10, 10)
        means = []
        for trait in TRAIT_ORDER:
            base = SE_ASIAN_BASELINE[trait]["mean"]
            age_adj = AGE_TRAJECTORIES[decade][trait]
            gender_adj = GENDER_ADJUSTMENTS.get(gender, {}).get(trait, 0.0)
            means.append(base + age_adj + gender_adj)
        return np.array(means)

    def _get_sds(self) -> np.ndarray:
        """Get trait standard deviations."""
        return np.array([SE_ASIAN_BASELINE[t]["sd"] for t in TRAIT_ORDER])

    def generate_one(self, age: int, gender: str) -> dict:
        """Generate Big Five profile for a single agent."""
        means = self._get_adjusted_means(age, gender)
        sds = self._get_sds()

        # Sample from multivariate normal using Cholesky
        z = self.rng.standard_normal(5)
        raw = means + sds * (self.cholesky @ z)

        # Clip to valid range [1, 5]
        clipped = np.clip(raw, 1.0, 5.0)

        return {f"big5_{t.lower()}": round(float(clipped[i]), 2)
                for i, t in enumerate(TRAIT_ORDER)}

    def generate_batch(self, agents_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate Big Five profiles for all agents.

        Args:
            agents_df: DataFrame with 'age' and 'gender' columns

        Returns:
            DataFrame with added big5_o, big5_c, big5_e, big5_a, big5_n columns
        """
        n = len(agents_df)
        logger.info(f"Generating Big Five profiles for {n} agents")

        results = np.zeros((n, 5))

        for i, (_, row) in enumerate(agents_df.iterrows()):
            age = int(row["age"])
            gender = str(row["gender"])
            means = self._get_adjusted_means(age, gender)
            sds = self._get_sds()
            z = self.rng.standard_normal(5)
            raw = means + sds * (self.cholesky @ z)
            results[i] = np.clip(raw, 1.0, 5.0)

        for i, trait in enumerate(TRAIT_ORDER):
            agents_df[f"big5_{trait.lower()}"] = np.round(results[:, i], 2)

        logger.info(f"Big Five generation complete. Trait means: "
                    f"{dict(zip(TRAIT_ORDER, results.mean(axis=0).round(2)))}")
        return agents_df


class AttitudeInitializer:
    """
    Derive attitudes and preferences from Big Five + demographics.

    Attitudes (Layer B) are more malleable than personality (Layer A),
    but more stable than emotions (Layer C).
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def generate_batch(self, agents_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate attitude profiles based on Big Five + demographics.

        Derived attitudes:
        - risk_appetite: f(O, C, N, age, income)
        - political_leaning: f(O, A, age, education)
        - social_trust: f(A, E, N, ethnicity)
        - religious_devotion: f(C, A, age, ethnicity)
        """
        n = len(agents_df)
        logger.info(f"Generating attitude profiles for {n} agents")

        # Risk appetite: higher O, lower N, lower C → more risk-taking
        # Also decreases with age (Dohmen et al. 2011)
        age_factor = -0.01 * (agents_df["age"].values - 30)  # decreases from 30
        risk = (
            0.3 * agents_df["big5_o"].values
            - 0.2 * agents_df["big5_n"].values
            - 0.15 * agents_df["big5_c"].values
            + 0.15 * age_factor
            + 2.5  # center at ~3
            + self.rng.normal(0, 0.3, n)
        )
        agents_df["risk_appetite"] = np.clip(np.round(risk, 2), 1.0, 5.0)

        # Political leaning: higher O → more progressive; higher C, A → more conservative
        # Young people tend more progressive (Tilley & Evans 2014)
        age_conserv = 0.008 * (agents_df["age"].values - 25)
        political = (
            0.35 * agents_df["big5_o"].values
            - 0.15 * agents_df["big5_c"].values
            - age_conserv
            + 1.8
            + self.rng.normal(0, 0.35, n)
        )
        agents_df["political_leaning"] = np.clip(np.round(political, 2), 1.0, 5.0)

        # Social trust: higher A, higher E, lower N → more trusting
        # Singapore generally has high institutional trust
        trust = (
            0.25 * agents_df["big5_a"].values
            + 0.15 * agents_df["big5_e"].values
            - 0.15 * agents_df["big5_n"].values
            + 2.2  # SG baseline slightly above neutral
            + self.rng.normal(0, 0.3, n)
        )
        agents_df["social_trust"] = np.clip(np.round(trust, 2), 1.0, 5.0)

        # Religious devotion: varies by ethnicity and age
        # Malay community generally more religiously observant
        ethnicity_boost = agents_df.get("ethnicity", pd.Series(["Chinese"] * n))
        eth_factor = ethnicity_boost.map({
            "Chinese": 0.0,
            "Malay": 0.5,
            "Indian": 0.3,
            "Others": 0.1,
        }).fillna(0.0).values

        age_religious = 0.005 * (agents_df["age"].values - 25)  # increases with age
        devotion = (
            0.15 * agents_df["big5_c"].values
            + 0.10 * agents_df["big5_a"].values
            + eth_factor
            + age_religious
            + 2.0
            + self.rng.normal(0, 0.4, n)
        )
        agents_df["religious_devotion"] = np.clip(np.round(devotion, 2), 1.0, 5.0)

        logger.info("Attitude generation complete")
        return agents_df
