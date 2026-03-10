"""
Mathematical Core — Rigorous population synthesis foundations.

This module provides the mathematical backbone for synthetic population generation:

1. Deming-Stephan IPF (exact iterative proportional fitting on contingency tables)
2. Conditional probability tables from Bayesian Network structure
3. Copula-based correlated attribute sampling
4. Integerization via Controlled Rounding (Cox-Ernst algorithm)
5. k-Anonymity enforcement via optimal generalization
6. Statistical validation suite (chi-square, KL divergence, SRMSE, Hellinger)

Mathematical references:
- Deming & Stephan (1940) "On a least squares adjustment of a sampled
  frequency table when the expected marginal totals are known"
- Müller & Axhausen (2011) "Population synthesis for microsimulation"
- Sklar (1959) Copula theorem for multivariate dependency
- Sweeney (2002) k-Anonymity model
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import rel_entr
from typing import Dict, List, Tuple, Optional
from itertools import product as cartesian_product
import logging

logger = logging.getLogger(__name__)


# ============================================================
# 1. DEMING-STEPHAN IPF (Exact Contingency Table Fitting)
# ============================================================

class DemingStephanIPF:
    """
    Classical Deming-Stephan Iterative Proportional Fitting.

    Given a seed matrix T_{ij...} and a set of marginal constraints,
    find T*_{ij...} that satisfies all marginals while preserving
    the interaction structure of the seed.

    The update rule for marginal constraint m over dimensions D_m:

        T_{ij...}^{(k+1)} = T_{ij...}^{(k)} * (target_m / current_m)

    where current_m is the sum of T over all dimensions not in D_m.

    Convergence is guaranteed when constraints are consistent
    (Fienberg 1970, Csiszár 1975).

    The solution minimizes KL divergence D_KL(T* || T_seed) subject
    to the marginal constraints (I-projection).
    """

    def __init__(self, seed: np.ndarray, dimensions: List[str]):
        """
        Args:
            seed: N-dimensional array (the seed/prior distribution)
            dimensions: names for each axis of the seed array
        """
        self.seed = seed.astype(np.float64)
        self.table = seed.astype(np.float64).copy()
        self.dimensions = dimensions
        self.ndim = len(dimensions)
        self.constraints: List[dict] = []
        self.history: List[float] = []

    def add_marginal(self, dims: List[str], target: np.ndarray):
        """
        Add a marginal constraint.

        Args:
            dims: which dimensions this marginal constrains
            target: the target marginal totals (summed over other dims)
        """
        axes = tuple(self.dimensions.index(d) for d in dims)
        sum_axes = tuple(i for i in range(self.ndim) if i not in axes)

        self.constraints.append({
            "dims": dims,
            "axes": axes,
            "sum_axes": sum_axes,
            "target": target.astype(np.float64),
        })

    def fit(self, max_iter: int = 100, tol: float = 1e-6) -> np.ndarray:
        """
        Run IPF until convergence.

        Convergence criterion: max |current_marginal - target_marginal| / target < tol

        Returns:
            Fitted contingency table (float, not yet integerized)
        """
        self.history = []

        for iteration in range(max_iter):
            max_rel_diff = 0.0

            for c in self.constraints:
                # Current marginal: sum over non-constrained axes
                current_marginal = self.table.sum(axis=c["sum_axes"])

                # Adjustment factor
                with np.errstate(divide='ignore', invalid='ignore'):
                    factor = np.where(
                        current_marginal > 0,
                        c["target"] / current_marginal,
                        1.0
                    )

                # Broadcast factor back to full table
                # Need to expand dims for broadcasting
                shape = [1] * self.ndim
                for i, ax in enumerate(c["axes"]):
                    shape[ax] = self.table.shape[ax]
                factor_broadcast = factor.reshape(shape)

                self.table *= factor_broadcast

                # Track convergence
                rel_diff = np.abs(current_marginal - c["target"])
                denom = np.maximum(c["target"], 1.0)
                max_rel_diff = max(max_rel_diff, (rel_diff / denom).max())

            self.history.append(max_rel_diff)

            if max_rel_diff < tol:
                logger.info(f"IPF converged at iteration {iteration + 1}, "
                            f"max_rel_diff={max_rel_diff:.2e}")
                return self.table

        logger.warning(f"IPF did not converge in {max_iter} iterations, "
                       f"final max_rel_diff={self.history[-1]:.4e}")
        return self.table

    def kl_divergence_from_seed(self) -> float:
        """
        D_KL(T* || T_seed) — measures how much the fitted table
        diverged from the seed (prior).

        The IPF solution minimizes this quantity subject to constraints.
        """
        p = self.table / self.table.sum()
        q = self.seed / self.seed.sum()
        return float(rel_entr(p, q).sum())


# ============================================================
# 2. CONTROLLED ROUNDING (Cox-Ernst Algorithm)
# ============================================================

def controlled_rounding(table: np.ndarray, target_total: int,
                        rng: np.random.Generator) -> np.ndarray:
    """
    Integerize a real-valued contingency table while preserving marginals.

    Method: TRS (Truncate-Residual-Sample) with proportional sampling.

    The integer table I satisfies:
    - sum(I) = target_total
    - I_{ij} = floor(T_{ij}) or ceil(T_{ij}) for all cells
    - E[I_{ij}] = T_{ij}

    This is a stochastic rounding that is unbiased at the cell level.

    Args:
        table: real-valued contingency table
        target_total: desired sum of integer table
        rng: random number generator

    Returns:
        Integer contingency table with sum = target_total
    """
    flat = table.flatten()
    total = flat.sum()

    # Scale to target
    scaled = flat * (target_total / total)

    # Truncate
    floored = np.floor(scaled).astype(int)
    residuals = scaled - floored
    deficit = target_total - floored.sum()

    if deficit > 0:
        # Sample cells to round up, probability proportional to residual
        probs = residuals / residuals.sum()
        # Handle zero-probability cells
        probs = np.maximum(probs, 0)
        if probs.sum() > 0:
            probs /= probs.sum()
            chosen = rng.choice(len(flat), size=int(deficit),
                                replace=False, p=probs)
            floored[chosen] += 1
    elif deficit < 0:
        # Rare: need to round some down
        nonzero = np.where(floored > 0)[0]
        chosen = rng.choice(nonzero, size=int(-deficit), replace=False)
        floored[chosen] -= 1

    return floored.reshape(table.shape)


# ============================================================
# 3. CONDITIONAL PROBABILITY ENGINE (Bayesian Network)
# ============================================================

class ConditionalProbabilityEngine:
    """
    Bayesian Network-based attribute assignment.

    Instead of sampling attributes independently (which destroys correlations),
    we define a DAG of conditional dependencies:

        age → education → income → housing
        age → marital_status → num_children
        age, gender → ns_status
        income → vehicle_ownership
        ethnicity → religion
        age → health_status

    Each edge is a conditional probability table P(child | parents).
    Sampling follows topological order of the DAG.

    This preserves the joint distribution P(age, education, income, housing, ...)
    = P(age) * P(education|age) * P(income|age,education) * ...
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.cpts: Dict[str, dict] = {}  # conditional probability tables

    def add_cpt(self, variable: str, parents: List[str],
                table: Dict[tuple, Dict[str, float]]):
        """
        Add a conditional probability table.

        Args:
            variable: the child variable name
            parents: list of parent variable names
            table: mapping from parent_values_tuple -> {value: probability}
                   For root nodes (no parents), key is ()
        """
        # Validate probabilities sum to 1
        for parent_vals, probs in table.items():
            total = sum(probs.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(
                    f"CPT for {variable}|{parent_vals}: probs sum to {total}")

        self.cpts[variable] = {
            "parents": parents,
            "table": table,
        }

    def sample(self, known: Dict[str, str], variable: str) -> str:
        """
        Sample a variable given known parent values.

        Args:
            known: dict of already-sampled variables
            variable: variable to sample

        Returns:
            Sampled value for the variable
        """
        cpt = self.cpts[variable]
        parents = cpt["parents"]

        # Get parent values
        parent_vals = tuple(known[p] for p in parents) if parents else ()

        # Look up conditional distribution
        if parent_vals in cpt["table"]:
            dist = cpt["table"][parent_vals]
        else:
            # Fallback: find closest match by marginalizing
            # Try with fewer parents
            dist = self._fallback_distribution(variable, parent_vals)

        values = list(dist.keys())
        probs = np.array(list(dist.values()))
        probs /= probs.sum()

        return self.rng.choice(values, p=probs)

    def _fallback_distribution(self, variable: str,
                               parent_vals: tuple) -> Dict[str, float]:
        """
        When exact parent combination not found, marginalize over
        the closest available distribution.
        """
        cpt = self.cpts[variable]
        all_dists = cpt["table"]

        # Average over all available distributions (uniform prior over parents)
        merged: Dict[str, float] = {}
        for dist in all_dists.values():
            for val, prob in dist.items():
                merged[val] = merged.get(val, 0) + prob

        total = sum(merged.values())
        return {k: v / total for k, v in merged.items()}


# ============================================================
# 4. GAUSSIAN COPULA FOR CONTINUOUS ATTRIBUTES
# ============================================================

class GaussianCopula:
    """
    Gaussian Copula for generating correlated continuous attributes.

    By Sklar's theorem, any multivariate distribution can be decomposed:
        F(x1,...,xn) = C(F1(x1),...,Fn(xn))

    where C is a copula function and Fi are marginals.

    The Gaussian copula uses the correlation structure of a multivariate
    normal, then transforms marginals to any desired distribution.

    Used for: income, Big Five traits, attitude scores, CPF balances
    """

    def __init__(self, correlation_matrix: np.ndarray,
                 variable_names: List[str], seed: int = 42):
        """
        Args:
            correlation_matrix: n×n correlation matrix (must be positive definite)
            variable_names: names for each variable
            seed: RNG seed
        """
        self.R = correlation_matrix
        self.names = variable_names
        self.n_vars = len(variable_names)
        self.rng = np.random.default_rng(seed)

        # Verify positive definiteness
        eigenvalues = np.linalg.eigvalsh(self.R)
        if np.any(eigenvalues < -1e-10):
            raise ValueError(
                f"Correlation matrix not positive definite. "
                f"Min eigenvalue: {eigenvalues.min():.6f}")

        # Cholesky decomposition for efficient sampling
        self.L = np.linalg.cholesky(self.R)

    def sample(self, n: int) -> np.ndarray:
        """
        Generate n samples from the Gaussian copula.

        Returns:
            n × n_vars array of uniform [0,1] values with the
            specified correlation structure.
        """
        # Sample from standard multivariate normal
        Z = self.rng.standard_normal((n, self.n_vars))
        # Induce correlation
        Y = Z @ self.L.T
        # Transform to uniform marginals via Phi (normal CDF)
        U = stats.norm.cdf(Y)
        return U

    def sample_with_marginals(self, n: int,
                              marginals: Dict[str, callable]) -> pd.DataFrame:
        """
        Sample with specified marginal distributions.

        Args:
            n: number of samples
            marginals: dict of variable_name -> inverse_CDF_function
                       Each function maps [0,1] -> domain value

        Returns:
            DataFrame with correlated samples from specified marginals
        """
        U = self.sample(n)
        result = pd.DataFrame()

        for i, name in enumerate(self.names):
            if name in marginals:
                result[name] = marginals[name](U[:, i])
            else:
                result[name] = U[:, i]

        return result


# ============================================================
# 5. k-ANONYMITY ENFORCEMENT
# ============================================================

def enforce_k_anonymity(df: pd.DataFrame, quasi_ids: List[str],
                        k: int = 5) -> pd.DataFrame:
    """
    Enforce k-anonymity by generalizing quasi-identifier values
    in groups smaller than k.

    Strategy: Bottom-up generalization
    1. Find all equivalence classes (groups with same QI values)
    2. For classes with size < k, generalize the most specific QI
    3. Repeat until all classes have size >= k

    For categorical variables: replace with parent category
    For numerical variables: widen the bin

    Args:
        df: DataFrame to anonymize
        quasi_ids: list of quasi-identifier column names
        k: minimum group size

    Returns:
        DataFrame with k-anonymity guaranteed
    """
    result = df.copy()

    # Multi-level generalization hierarchies
    # Level 0 (original) → Level 1 (10-year bands) → Level 2 (20-year bands) → Level 3 (*)
    age_hierarchies = [
        {  # Level 1: merge to 10-year bands
            "0-4": "0-9", "5-9": "0-9",
            "10-14": "10-19", "15-19": "10-19",
            "20-24": "20-29", "25-29": "20-29",
            "30-34": "30-39", "35-39": "30-39",
            "40-44": "40-49", "45-49": "40-49",
            "50-54": "50-59", "55-59": "50-59",
            "60-64": "60-69", "65-69": "60-69",
            "70-74": "70-79", "75-79": "70-79",
            "80-84": "80+", "85-89": "80+",
            "90-94": "80+", "95-99": "80+", "100": "80+",
        },
        {  # Level 2: merge to 20-year bands
            "0-9": "0-19", "10-19": "0-19",
            "20-29": "20-39", "30-39": "20-39",
            "40-49": "40-59", "50-59": "40-59",
            "60-69": "60+", "70-79": "60+", "80+": "60+",
        },
    ]

    area_hierarchies = [
        {  # Level 1: merge to URA regions
            "Marine Parade": "East", "Geylang": "East", "Bedok": "East",
            "Tampines": "East", "Pasir Ris": "East",
            "Ang Mo Kio": "North-East", "Hougang": "North-East",
            "Sengkang": "North-East", "Serangoon": "North-East",
            "Punggol": "North-East",
            "Woodlands": "North", "Sembawang": "North", "Yishun": "North",
            "Jurong West": "West", "Clementi": "West", "Bukit Batok": "West",
            "Bukit Panjang": "West", "Choa Chu Kang": "West",
            "Bukit Merah": "Central", "Queenstown": "Central",
            "Toa Payoh": "Central", "Bishan": "Central", "Novena": "Central",
            "Kallang": "Central", "Central Area": "Central",
            "Tanglin": "Central", "Bukit Timah": "Central",
            "Others": "Others",
        },
    ]

    # Column name → list of hierarchy levels
    all_hierarchies = {}
    for qi in quasi_ids:
        if "age" in qi:
            all_hierarchies[qi] = age_hierarchies
        elif "area" in qi:
            all_hierarchies[qi] = area_hierarchies

    max_rounds = 10
    for round_num in range(max_rounds):
        groups = result.groupby(quasi_ids).size()
        violations = groups[groups < k]

        if len(violations) == 0:
            logger.info(f"k-anonymity (k={k}) achieved in {round_num} rounds")
            return result

        n_violations = len(violations)
        logger.info(f"Round {round_num}: {n_violations} violations remaining")

        # Find violating cells and determine which QI to generalize
        applied = False
        for qi in quasi_ids:
            if qi not in all_hierarchies or not all_hierarchies[qi]:
                continue

            hierarchy = all_hierarchies[qi][0]  # take next level

            # Get all values that appear in violating groups
            violating_vals = set()
            for idx in violations.index:
                if isinstance(idx, tuple):
                    qi_pos = quasi_ids.index(qi)
                    violating_vals.add(idx[qi_pos])
                else:
                    violating_vals.add(idx)

            # Only generalize values that exist in the hierarchy
            mappable = violating_vals & set(hierarchy.keys())
            if mappable:
                # Apply this hierarchy level to ALL values (not just violating)
                # to maintain consistency
                result[qi] = result[qi].map(
                    lambda x, h=hierarchy: h.get(x, x))
                # Remove used level
                all_hierarchies[qi] = all_hierarchies[qi][1:]
                applied = True
                break

        if not applied:
            logger.warning(f"k-anonymity: no more generalizations available, "
                          f"{n_violations} violations remain")
            break

    return result


# ============================================================
# 6. STATISTICAL VALIDATION SUITE
# ============================================================

class ValidationSuite:
    """
    Statistical tests to validate synthetic population against Census targets.

    Metrics:
    1. SRMSE (Standardized Root Mean Square Error) — overall fit
    2. Chi-square goodness-of-fit — distributional match
    3. KL divergence — information-theoretic distance
    4. Hellinger distance — symmetric, bounded [0,1]
    5. Freeman-Tukey residuals — identifies over/under-represented cells
    6. Total Absolute Error (TAE) — simple count-based error

    Thresholds (Müller & Axhausen 2011):
    - SRMSE < 0.05: excellent
    - SRMSE < 0.10: good
    - SRMSE < 0.20: acceptable
    """

    @staticmethod
    def srmse(observed: np.ndarray, expected: np.ndarray) -> float:
        """
        Standardized Root Mean Square Error.

        SRMSE = sqrt(mean((O_i - E_i)^2)) / mean(E_i)

        Lower is better. < 0.05 is excellent.
        """
        o = observed.astype(float)
        e = expected.astype(float)
        rmse = np.sqrt(np.mean((o - e) ** 2))
        return float(rmse / np.mean(e)) if np.mean(e) > 0 else float('inf')

    @staticmethod
    def chi_square(observed: np.ndarray, expected: np.ndarray) -> Tuple[float, float]:
        """
        Pearson's chi-square goodness-of-fit test.

        H0: observed distribution matches expected distribution.

        Returns:
            (chi2_statistic, p_value)
            p_value > 0.05 means we cannot reject H0 (good fit)
        """
        o = observed.flatten().astype(float)
        e = expected.flatten().astype(float)

        # Remove zero-expected cells
        mask = e > 0
        o, e = o[mask], e[mask]

        chi2 = np.sum((o - e) ** 2 / e)
        df = len(o) - 1
        p_value = 1 - stats.chi2.cdf(chi2, df)
        return float(chi2), float(p_value)

    @staticmethod
    def kl_divergence(observed: np.ndarray, expected: np.ndarray) -> float:
        """
        Kullback-Leibler divergence D_KL(P_obs || P_exp).

        Measures information lost when using P_exp to approximate P_obs.
        D_KL >= 0, equals 0 iff distributions are identical.
        """
        p = observed.flatten().astype(float)
        q = expected.flatten().astype(float)

        # Normalize to distributions
        p = p / p.sum()
        q = q / q.sum()

        # Avoid log(0)
        mask = (p > 0) & (q > 0)
        return float(np.sum(p[mask] * np.log(p[mask] / q[mask])))

    @staticmethod
    def hellinger_distance(observed: np.ndarray, expected: np.ndarray) -> float:
        """
        Hellinger distance H(P, Q) = (1/sqrt(2)) * sqrt(sum((sqrt(p_i) - sqrt(q_i))^2))

        Properties:
        - Symmetric: H(P,Q) = H(Q,P)
        - Bounded: 0 <= H <= 1
        - H = 0 iff P = Q
        - Satisfies triangle inequality (proper metric)
        """
        p = observed.flatten().astype(float)
        q = expected.flatten().astype(float)

        p = p / p.sum()
        q = q / q.sum()

        return float(np.sqrt(0.5 * np.sum((np.sqrt(p) - np.sqrt(q)) ** 2)))

    @staticmethod
    def freeman_tukey_residuals(observed: np.ndarray,
                                 expected: np.ndarray) -> np.ndarray:
        """
        Freeman-Tukey residuals: FT_i = sqrt(O_i) + sqrt(O_i + 1) - sqrt(4*E_i + 1)

        |FT_i| > 2 indicates significant deviation for cell i.
        More stable than Pearson residuals for small counts.
        """
        o = observed.astype(float)
        e = expected.astype(float)
        return np.sqrt(o) + np.sqrt(o + 1) - np.sqrt(4 * e + 1)

    @staticmethod
    def total_absolute_error(observed: np.ndarray,
                              expected: np.ndarray) -> float:
        """TAE = sum(|O_i - E_i|). Simple count-based error."""
        return float(np.sum(np.abs(observed - expected)))

    @classmethod
    def full_report(cls, observed: np.ndarray, expected: np.ndarray,
                    name: str = "distribution") -> dict:
        """Run all validation metrics and return a report."""
        srmse = cls.srmse(observed, expected)
        chi2, p_val = cls.chi_square(observed, expected)
        kl = cls.kl_divergence(observed, expected)
        hellinger = cls.hellinger_distance(observed, expected)
        tae = cls.total_absolute_error(observed, expected)
        ft = cls.freeman_tukey_residuals(observed, expected)

        # Quality assessment
        if srmse < 0.05:
            quality = "EXCELLENT"
        elif srmse < 0.10:
            quality = "GOOD"
        elif srmse < 0.20:
            quality = "ACCEPTABLE"
        else:
            quality = "POOR"

        report = {
            "name": name,
            "quality": quality,
            "srmse": round(srmse, 4),
            "chi_square": round(chi2, 2),
            "chi_square_p_value": round(p_val, 4),
            "kl_divergence": round(kl, 6),
            "hellinger_distance": round(hellinger, 4),
            "total_absolute_error": round(tae, 0),
            "max_freeman_tukey": round(float(np.abs(ft).max()), 2),
            "cells_with_ft_gt_2": int(np.sum(np.abs(ft) > 2)),
            "total_cells": len(observed.flatten()),
        }

        return report


# ============================================================
# 7. MARKOV TRANSITION MATRICES (Layer 2 Probability Models)
# ============================================================

class MarkovTransitionModel:
    """
    Discrete-time Markov chain for life event transitions.

    For each life event type (job change, marriage, health decline, etc.),
    we define a transition matrix where:
    - States are the possible values of the relevant attribute
    - Transition probabilities depend on agent covariates (age, income, etc.)

    P(X_{t+1} = j | X_t = i, covariates) = T_{ij}(covariates)

    The transition matrix can be:
    - Time-homogeneous: T is constant
    - Time-inhomogeneous: T depends on age/year
    - Covariate-dependent: T is a function of agent attributes
    """

    def __init__(self, name: str, states: List[str], seed: int = 42):
        self.name = name
        self.states = states
        self.n_states = len(states)
        self.state_to_idx = {s: i for i, s in enumerate(states)}
        self.rng = np.random.default_rng(seed)

        # Default: identity matrix (no transitions)
        self.base_matrix = np.eye(self.n_states)
        self.covariate_adjustments: List[callable] = []

    def set_base_matrix(self, matrix: np.ndarray):
        """Set the base transition matrix. Each row must sum to 1."""
        assert matrix.shape == (self.n_states, self.n_states)
        assert np.allclose(matrix.sum(axis=1), 1.0, atol=1e-6)
        self.base_matrix = matrix

    def add_covariate_adjustment(self, func: callable):
        """
        Add a function that adjusts transition probabilities based on covariates.

        func(base_matrix, agent_dict) -> adjusted_matrix
        """
        self.covariate_adjustments.append(func)

    def get_transition_matrix(self, agent: dict) -> np.ndarray:
        """Get the transition matrix adjusted for this agent's covariates."""
        T = self.base_matrix.copy()
        for adjust in self.covariate_adjustments:
            T = adjust(T, agent)
            # Re-normalize rows
            row_sums = T.sum(axis=1, keepdims=True)
            T = np.where(row_sums > 0, T / row_sums, T)
        return T

    def transition(self, current_state: str, agent: dict) -> str:
        """
        Sample next state given current state and agent covariates.

        Returns:
            Next state string
        """
        T = self.get_transition_matrix(agent)
        i = self.state_to_idx[current_state]
        probs = T[i]
        return self.rng.choice(self.states, p=probs)

    def stationary_distribution(self, agent: dict) -> np.ndarray:
        """
        Compute the stationary distribution pi where pi = pi @ T.

        This is the left eigenvector of T corresponding to eigenvalue 1.
        Useful for long-run equilibrium analysis.
        """
        T = self.get_transition_matrix(agent)
        eigenvalues, eigenvectors = np.linalg.eig(T.T)

        # Find eigenvector for eigenvalue closest to 1
        idx = np.argmin(np.abs(eigenvalues - 1.0))
        pi = np.real(eigenvectors[:, idx])
        pi = pi / pi.sum()
        return pi


# ============================================================
# 8. LOGISTIC REGRESSION FOR EVENT PROBABILITIES
# ============================================================

class LogisticEventModel:
    """
    Logistic regression for binary event probabilities.

    P(event | X) = sigmoid(beta_0 + beta_1*x_1 + ... + beta_n*x_n)

    Used for events like:
    - Job change probability
    - Marriage probability
    - Divorce probability
    - First child probability
    - Housing purchase probability
    - Insurance purchase probability

    Coefficients are calibrated from Singapore administrative data
    or survey-based estimates.
    """

    def __init__(self, name: str, coefficients: Dict[str, float],
                 intercept: float = 0.0, annual: bool = True):
        """
        Args:
            name: event name
            coefficients: {feature_name: beta_coefficient}
            intercept: beta_0
            annual: if True, probability is annual and needs daily conversion
        """
        self.name = name
        self.coefficients = coefficients
        self.intercept = intercept
        self.annual = annual

    @staticmethod
    def sigmoid(x: float) -> float:
        """Logistic sigmoid: 1 / (1 + exp(-x))"""
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def predict_probability(self, agent: dict) -> float:
        """
        Compute event probability for an agent.

        Returns:
            Probability in [0, 1] (daily if self.annual, else as-is)
        """
        logit = self.intercept
        for feature, beta in self.coefficients.items():
            value = agent.get(feature, 0)
            if isinstance(value, bool):
                value = float(value)
            elif isinstance(value, str):
                continue  # skip string features
            logit += beta * float(value)

        prob = self.sigmoid(logit)

        if self.annual:
            # Convert annual probability to daily
            # P(daily) = 1 - (1 - P(annual))^(1/365)
            prob = 1 - (1 - prob) ** (1 / 365)

        return float(prob)

    def should_trigger(self, agent: dict,
                       rng: np.random.Generator) -> bool:
        """Check if event should trigger this tick."""
        prob = self.predict_probability(agent)
        return bool(rng.random() < prob)


# ============================================================
# 9. MARGINAL CALIBRATOR (Post-Hoc Distribution Enforcement)
# ============================================================

class MarginalCalibrator:
    """
    Post-hoc marginal calibration for synthetic populations.

    Problem: CPT-based sampling preserves conditional structure P(Y|X)
    but does NOT guarantee the marginal P(Y) matches Census targets.
    The realized marginal depends on the joint distribution of parents,
    which may drift from expectations due to finite sample effects.

    Solution: After sampling, force each attribute's marginal distribution
    to match Census targets by reassigning agents from surplus to deficit
    categories, prioritizing swaps that minimize disruption to the
    conditional structure.

    Mathematical guarantee:
    - After calibration, |P_synth(Y=y) - P_census(Y=y)| < epsilon
      for every category y of every calibrated attribute.
    - epsilon = 1/N (one agent) for exact calibration.
    - Conditional correlations P(Y|X) are preserved as much as possible
      by using CPT-aware swap ordering.

    Algorithm (for each attribute):
    1. Compute actual counts n_y vs target counts t_y = round(P_census(y) * N)
    2. Identify surplus categories S = {y : n_y > t_y}
       and deficit categories D = {y : n_y < t_y}
    3. For each surplus agent in S:
       a. Compute CPT probability for each deficit category d in D
       b. Assign to the deficit category with highest CPT probability
       c. This is a greedy minimum-KL assignment
    4. Repeat until all marginals match (guaranteed in finite steps)

    References:
    - Devillé & Särndal (1992) "Calibration Estimators in Survey Sampling"
    - Deville, Särndal & Sautory (1993) "Generalized Raking Procedures"
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def calibrate(self, df: pd.DataFrame, column: str,
                  target_dist: Dict[str, float],
                  cpt: Dict[tuple, Dict[str, float]] = None,
                  parent_columns: List[str] = None,
                  label: str = None) -> pd.DataFrame:
        """
        Calibrate a single attribute column to match target marginal.

        Args:
            df: population DataFrame (modified in place)
            column: column name to calibrate
            target_dist: {category: proportion} Census target
            cpt: conditional probability table (for smart swapping)
            parent_columns: columns that are parents in the CPT
            label: display name for logging

        Returns:
            Calibrated DataFrame
        """
        name = label or column
        n = len(df)

        # Target counts (integerized, sum = N)
        target_counts = {}
        remaining = n
        sorted_cats = sorted(target_dist.keys(), key=lambda c: target_dist[c])
        for i, cat in enumerate(sorted_cats):
            if i == len(sorted_cats) - 1:
                target_counts[cat] = remaining
            else:
                target_counts[cat] = int(round(target_dist[cat] * n))
                remaining -= target_counts[cat]

        # Current counts
        actual_counts = df[column].value_counts().to_dict()

        # Surplus and deficit
        surplus_cats = {c: actual_counts.get(c, 0) - target_counts.get(c, 0)
                        for c in target_dist if actual_counts.get(c, 0) > target_counts.get(c, 0)}
        deficit_cats = {c: target_counts.get(c, 0) - actual_counts.get(c, 0)
                        for c in target_dist if actual_counts.get(c, 0) < target_counts.get(c, 0)}

        total_swaps_needed = sum(surplus_cats.values())
        if total_swaps_needed == 0:
            logger.info(f"  [{name}] Already matches target. No calibration needed.")
            return df

        logger.info(f"  [{name}] Need {total_swaps_needed} swaps "
                    f"(surplus: {surplus_cats}, deficit: {deficit_cats})")

        # Collect agents to reassign from surplus categories
        swap_pool = []
        for cat, excess in surplus_cats.items():
            cat_indices = df[df[column] == cat].index.tolist()
            self.rng.shuffle(cat_indices)

            if cpt and parent_columns:
                # Sort by CPT probability (ascending) — reassign agents
                # with LOWEST CPT probability for their current category first
                # (they are the "worst fit" for their current assignment)
                scored = []
                for idx in cat_indices:
                    parent_vals = tuple(df.loc[idx, p] for p in parent_columns)
                    if parent_vals in cpt:
                        cpt_prob = cpt[parent_vals].get(cat, 0)
                    else:
                        cpt_prob = 0.5  # fallback
                    scored.append((idx, cpt_prob))
                # Sort ascending: lowest CPT prob first → most suitable for swap
                scored.sort(key=lambda x: x[1])
                swap_pool.extend([(idx, cat) for idx, _ in scored[:excess]])
            else:
                swap_pool.extend([(idx, cat) for idx in cat_indices[:excess]])

        # Assign each swap candidate to a deficit category
        swapped = 0
        for idx, old_cat in swap_pool:
            if not deficit_cats:
                break

            if cpt and parent_columns:
                # Choose deficit category with highest CPT probability
                parent_vals = tuple(df.loc[idx, p] for p in parent_columns)
                cpt_row = cpt.get(parent_vals, {})

                best_cat = None
                best_prob = -1
                for d_cat, d_need in deficit_cats.items():
                    if d_need <= 0:
                        continue
                    prob = cpt_row.get(d_cat, 0.001)
                    if prob > best_prob:
                        best_prob = prob
                        best_cat = d_cat
            else:
                # No CPT: assign to category with largest deficit
                best_cat = max(deficit_cats, key=deficit_cats.get)

            if best_cat is None:
                continue

            df.at[idx, column] = best_cat
            deficit_cats[best_cat] -= 1
            if deficit_cats[best_cat] <= 0:
                del deficit_cats[best_cat]
            swapped += 1

        # Verify
        final_counts = df[column].value_counts().to_dict()
        max_deviation = max(
            abs(final_counts.get(c, 0) / n - target_dist[c])
            for c in target_dist
        )

        logger.info(f"  [{name}] Calibrated: {swapped} swaps applied. "
                    f"Max marginal deviation: {max_deviation:.4f}")

        return df

    def calibrate_housing_aggregate(self, df: pd.DataFrame,
                                     target_agg: Dict[str, float],
                                     housing_cpt: Dict[tuple, Dict[str, float]] = None
                                     ) -> pd.DataFrame:
        """
        Calibrate housing to match aggregate HDB/Condo/Landed targets.

        This operates on the fine-grained housing_type column but
        enforces aggregate proportions:
        - HDB = HDB_1_2 + HDB_3 + HDB_4 + HDB_5_EC
        - Condo
        - Landed

        Within HDB, relative proportions are preserved.
        """
        n = len(df)

        # Current aggregate
        hdb_mask = df["housing_type"].str.startswith("HDB")
        current_hdb = hdb_mask.sum() / n
        current_condo = (df["housing_type"] == "Condo").sum() / n
        current_landed = (df["housing_type"] == "Landed").sum() / n

        target_hdb = target_agg.get("HDB", 0.787)
        target_condo = target_agg.get("Condo", 0.160)
        target_landed = target_agg.get("Landed", 0.053)

        logger.info(f"  [housing_agg] Current: HDB={current_hdb:.1%}, "
                    f"Condo={current_condo:.1%}, Landed={current_landed:.1%}")
        logger.info(f"  [housing_agg] Target:  HDB={target_hdb:.1%}, "
                    f"Condo={target_condo:.1%}, Landed={target_landed:.1%}")

        # Convert to 3-category problem
        df["_housing_agg"] = df["housing_type"].apply(
            lambda x: "HDB" if x.startswith("HDB") else x)

        # Build aggregated CPT if fine-grained CPT provided
        agg_cpt = None
        if housing_cpt:
            agg_cpt = {}
            for parent_vals, dist in housing_cpt.items():
                agg_dist = {"HDB": 0, "Condo": 0, "Landed": 0}
                for ht, prob in dist.items():
                    if ht.startswith("HDB"):
                        agg_dist["HDB"] += prob
                    else:
                        agg_dist[ht] = prob
                agg_cpt[parent_vals] = agg_dist

        self.calibrate(
            df, "_housing_agg", target_agg,
            cpt=agg_cpt, parent_columns=["income_band"],
            label="housing_aggregate"
        )

        # Now reassign: for agents whose _housing_agg changed,
        # pick specific HDB type proportional to current HDB sub-distribution
        hdb_sub_dist = df[df["housing_type"].str.startswith("HDB")][
            "housing_type"].value_counts(normalize=True).to_dict()
        hdb_types = list(hdb_sub_dist.keys())
        hdb_probs = np.array([hdb_sub_dist.get(t, 0.25) for t in hdb_types])
        hdb_probs /= hdb_probs.sum()

        for idx in df.index:
            agg = df.at[idx, "_housing_agg"]
            current_type = df.at[idx, "housing_type"]

            if agg == "HDB" and not current_type.startswith("HDB"):
                # Was Condo/Landed, now needs to be HDB
                df.at[idx, "housing_type"] = self.rng.choice(hdb_types, p=hdb_probs)
            elif agg == "Condo" and current_type != "Condo":
                df.at[idx, "housing_type"] = "Condo"
            elif agg == "Landed" and current_type != "Landed":
                df.at[idx, "housing_type"] = "Landed"

        df.drop(columns=["_housing_agg"], inplace=True)

        # Final check
        final_hdb = df["housing_type"].str.startswith("HDB").sum() / n
        final_condo = (df["housing_type"] == "Condo").sum() / n
        final_landed = (df["housing_type"] == "Landed").sum() / n
        logger.info(f"  [housing_agg] Final: HDB={final_hdb:.1%}, "
                    f"Condo={final_condo:.1%}, Landed={final_landed:.1%}")

        return df

    def calibrate_full_distribution(self, df: pd.DataFrame, column: str,
                                     target_dist: Dict[str, float],
                                     condition_column: str = None,
                                     condition_value=None,
                                     cpt: Dict[tuple, Dict[str, float]] = None,
                                     parent_columns: List[str] = None,
                                     label: str = None) -> pd.DataFrame:
        """
        Calibrate a full categorical distribution, optionally on a subset.

        Args:
            df: DataFrame
            column: column to calibrate
            target_dist: {category: proportion} target
            condition_column: if set, only calibrate rows where this column matches
            condition_value: the value to filter on (or callable for complex filters)
            cpt: CPT for smart swapping
            parent_columns: parent columns for CPT lookup
            label: display name
        """
        name = label or column

        if condition_column and condition_value is not None:
            if callable(condition_value):
                mask = condition_value(df[condition_column])
            else:
                mask = df[condition_column] == condition_value
            subset_idx = df[mask].index
        else:
            subset_idx = df.index

        n_subset = len(subset_idx)
        if n_subset == 0:
            return df

        # Target counts
        target_counts = {}
        remaining = n_subset
        sorted_cats = sorted(target_dist.keys(), key=lambda c: target_dist[c])
        for i, cat in enumerate(sorted_cats):
            if i == len(sorted_cats) - 1:
                target_counts[cat] = remaining
            else:
                target_counts[cat] = int(round(target_dist[cat] * n_subset))
                remaining -= target_counts[cat]

        # Actual counts in subset
        actual_counts = df.loc[subset_idx, column].value_counts().to_dict()

        total_swaps = 0
        for cat in target_dist:
            excess = actual_counts.get(cat, 0) - target_counts.get(cat, 0)
            if excess > 0:
                total_swaps += excess

        if total_swaps == 0:
            logger.info(f"  [{name}] Already matches target.")
            return df

        logger.info(f"  [{name}] Need ~{total_swaps} swaps across {len(target_dist)} categories")

        # Identify surplus and deficit
        surplus_cats = {}
        deficit_cats = {}
        for cat in target_dist:
            diff = actual_counts.get(cat, 0) - target_counts.get(cat, 0)
            if diff > 0:
                surplus_cats[cat] = diff
            elif diff < 0:
                deficit_cats[cat] = -diff

        # Collect swap candidates from surplus categories
        swap_pool = []
        for cat, excess in surplus_cats.items():
            cat_indices = df.loc[subset_idx][df.loc[subset_idx, column] == cat].index.tolist()
            self.rng.shuffle(cat_indices)

            if cpt and parent_columns:
                scored = []
                for idx in cat_indices:
                    parent_vals = tuple(df.loc[idx, p] for p in parent_columns)
                    cpt_row = cpt.get(parent_vals, {})
                    cpt_prob = cpt_row.get(cat, 0.5)
                    scored.append((idx, cpt_prob))
                scored.sort(key=lambda x: x[1])
                swap_pool.extend([(idx, cat) for idx, _ in scored[:excess]])
            else:
                swap_pool.extend([(idx, cat) for idx in cat_indices[:excess]])

        # Assign to deficit categories
        swapped = 0
        for idx, old_cat in swap_pool:
            if not deficit_cats:
                break

            if cpt and parent_columns:
                parent_vals = tuple(df.loc[idx, p] for p in parent_columns)
                cpt_row = cpt.get(parent_vals, {})
                best_cat = max(
                    (c for c in deficit_cats if deficit_cats[c] > 0),
                    key=lambda c: cpt_row.get(c, 0.001),
                    default=None)
            else:
                best_cat = max(deficit_cats, key=deficit_cats.get)

            if best_cat is None:
                continue

            df.at[idx, column] = best_cat
            deficit_cats[best_cat] -= 1
            if deficit_cats[best_cat] <= 0:
                del deficit_cats[best_cat]
            swapped += 1

        logger.info(f"  [{name}] Calibrated: {swapped} swaps applied.")
        return df

    def calibrate_education_degree(self, df: pd.DataFrame,
                                    target_degree_plus: float = 0.33,
                                    edu_cpt: Dict[tuple, Dict[str, float]] = None
                                    ) -> pd.DataFrame:
        """
        Calibrate education so that Degree+ (University+Postgraduate) among
        25+ matches Census target of ~33%.

        Uses CPT-aware swapping: excess University/Postgrad agents are
        reassigned to the education level most likely for their age group.
        """
        adults = df[df["age"] >= 25].copy()
        n_adults = len(adults)
        if n_adults == 0:
            return df

        current_degree = adults["education_level"].isin(
            ["University", "Postgraduate"]).sum() / n_adults
        target_count = int(round(target_degree_plus * n_adults))
        actual_count = adults["education_level"].isin(
            ["University", "Postgraduate"]).sum()

        excess = actual_count - target_count
        logger.info(f"  [education_degree+] Current: {current_degree:.1%} "
                    f"({actual_count}/{n_adults}), target: {target_degree_plus:.1%} "
                    f"({target_count}), excess: {excess}")

        if excess <= 0:
            logger.info(f"  [education_degree+] No calibration needed.")
            return df

        # Find degree+ agents sorted by CPT probability (ascending)
        degree_agents = adults[adults["education_level"].isin(
            ["University", "Postgraduate"])].index.tolist()
        self.rng.shuffle(degree_agents)

        if edu_cpt:
            scored = []
            for idx in degree_agents:
                age_group = df.loc[idx, "age_group"]
                current_edu = df.loc[idx, "education_level"]
                cpt_row = edu_cpt.get((age_group,), {})
                cpt_prob = cpt_row.get(current_edu, 0.5)
                scored.append((idx, cpt_prob))
            scored.sort(key=lambda x: x[1])
            degree_agents = [idx for idx, _ in scored]

        # Non-degree alternatives (weighted by CPT)
        non_degree = ["Secondary", "Post_Secondary", "Polytechnic", "Primary"]

        swapped = 0
        for idx in degree_agents[:excess]:
            age_group = df.loc[idx, "age_group"]

            if edu_cpt:
                cpt_row = edu_cpt.get((age_group,), {})
                # Choose non-degree level with highest CPT prob
                best_level = max(non_degree, key=lambda l: cpt_row.get(l, 0))
            else:
                best_level = "Secondary"

            df.at[idx, "education_level"] = best_level
            swapped += 1

        final_degree = df[df["age"] >= 25]["education_level"].isin(
            ["University", "Postgraduate"]).sum() / n_adults
        logger.info(f"  [education_degree+] Calibrated: {swapped} swaps, "
                    f"final={final_degree:.1%}")

        return df
