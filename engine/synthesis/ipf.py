"""
Iterative Proportional Fitting (IPF) Engine
Generates 20,000 synthetic agents from Census cross-tabulation data.

Method: Given marginal distributions and cross-tabulations from Singapore GHS 2025,
synthesize individual-level records that jointly satisfy all constraints.

References:
- Beckman et al. (1996) "Creating synthetic baseline populations"
- Müller & Axhausen (2011) "Population synthesis for microsimulation"
- GenSynthPop (sample-free approach from aggregated tables)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Target population
TARGET_AGENTS = 20_000
SG_POPULATION = 5_800_000
SCALE_FACTOR = SG_POPULATION / TARGET_AGENTS  # ~290


class IPFEngine:
    """Iterative Proportional Fitting for synthetic population generation."""

    def __init__(self, target_n: int = TARGET_AGENTS, seed: int = 42):
        self.target_n = target_n
        self.rng = np.random.default_rng(seed)
        self.constraints: List[Dict] = []
        self.population: Optional[pd.DataFrame] = None

    def add_constraint(self, name: str, dimensions: List[str],
                       table: pd.DataFrame, weight: float = 1.0):
        """
        Add a cross-tabulation constraint.

        Args:
            name: Descriptive name (e.g., "age_sex_area")
            dimensions: Column names in the table (e.g., ["age_group", "sex", "planning_area"])
            table: DataFrame with columns = dimensions + "count"
            weight: Importance weight for this constraint
        """
        self.constraints.append({
            "name": name,
            "dimensions": dimensions,
            "table": table,
            "weight": weight,
        })
        logger.info(f"Added constraint '{name}' with {len(table)} cells, "
                     f"dimensions: {dimensions}")

    def _initialize_seed_matrix(self) -> pd.DataFrame:
        """
        Create initial seed population using the most detailed constraint.
        Start with the constraint that has the most dimensions.
        """
        if not self.constraints:
            raise ValueError("No constraints added. Call add_constraint() first.")

        # Use the constraint with most dimensions as seed
        primary = max(self.constraints, key=lambda c: len(c["dimensions"]))
        logger.info(f"Using '{primary['name']}' as primary constraint "
                     f"(dimensions: {primary['dimensions']})")

        table = primary["table"].copy()
        total = table["count"].sum()

        # Scale counts to target population
        table["scaled_count"] = (table["count"] / total * self.target_n)

        # Integerize using TRS (Truncation, Residuals, Sampling)
        table["int_count"] = table["scaled_count"].astype(int)
        residuals = table["scaled_count"] - table["int_count"]
        deficit = self.target_n - table["int_count"].sum()

        if deficit > 0:
            # Probabilistic rounding for residuals
            probs = residuals / residuals.sum()
            extra_indices = self.rng.choice(
                len(table), size=int(deficit), replace=False, p=probs.values
            )
            table.iloc[extra_indices, table.columns.get_loc("int_count")] += 1

        # Expand to individual records
        records = []
        for _, row in table.iterrows():
            n = int(row["int_count"])
            if n > 0:
                record = {dim: row[dim] for dim in primary["dimensions"]}
                records.extend([record.copy() for _ in range(n)])

        population = pd.DataFrame(records)
        logger.info(f"Seed population: {len(population)} agents from "
                     f"{len(table)} cells")
        return population

    def _fit_constraint(self, population: pd.DataFrame,
                        constraint: Dict) -> pd.DataFrame:
        """
        Adjust population to better fit a single constraint.
        Uses reweighting and resampling.
        """
        dims = constraint["dimensions"]
        target_table = constraint["table"].copy()
        target_total = target_table["count"].sum()

        # Check which dimensions exist in population
        available_dims = [d for d in dims if d in population.columns]
        if not available_dims:
            logger.warning(f"Skipping constraint '{constraint['name']}': "
                           f"no matching dimensions in population")
            return population

        missing_dims = [d for d in dims if d not in population.columns]
        if missing_dims:
            logger.info(f"Constraint '{constraint['name']}': "
                        f"missing dims {missing_dims}, using available: {available_dims}")
            # Marginalize target table over missing dimensions
            target_table = (target_table.groupby(available_dims)["count"]
                            .sum().reset_index())

        # Compute current distribution in population
        current = (population.groupby(available_dims)
                   .size().reset_index(name="current_count"))

        # Merge with target
        merged = target_table.merge(current, on=available_dims, how="outer").fillna(0)
        merged["target_scaled"] = merged["count"] / target_total * self.target_n
        merged["ratio"] = np.where(
            merged["current_count"] > 0,
            merged["target_scaled"] / merged["current_count"],
            1.0
        )

        # Cap extreme ratios to avoid instability
        merged["ratio"] = merged["ratio"].clip(0.2, 5.0)

        # Apply weights to population via resampling
        # Assign ratio to each agent based on their cell
        pop_with_ratio = population.merge(
            merged[available_dims + ["ratio"]],
            on=available_dims,
            how="left"
        )
        pop_with_ratio["ratio"] = pop_with_ratio["ratio"].fillna(1.0)

        # Resample with weights
        weights = pop_with_ratio["ratio"].values
        weights = weights / weights.sum()

        indices = self.rng.choice(
            len(population),
            size=self.target_n,
            replace=True,
            p=weights
        )
        resampled = population.iloc[indices].reset_index(drop=True)

        return resampled

    def fit(self, max_iterations: int = 20, tolerance: float = 0.01) -> pd.DataFrame:
        """
        Run IPF: iteratively fit all constraints until convergence.

        Args:
            max_iterations: Maximum number of full iterations
            tolerance: Convergence threshold (max relative deviation)

        Returns:
            DataFrame with synthetic population (one row per agent)
        """
        logger.info(f"Starting IPF with {len(self.constraints)} constraints, "
                     f"target {self.target_n} agents")

        # Step 1: Initialize seed population
        population = self._initialize_seed_matrix()

        # Step 2: Iteratively fit constraints
        for iteration in range(max_iterations):
            max_deviation = 0.0

            for constraint in self.constraints:
                prev_pop = population.copy()
                population = self._fit_constraint(population, constraint)

                # Measure deviation
                dims = [d for d in constraint["dimensions"]
                        if d in population.columns]
                if dims:
                    target = constraint["table"].copy()
                    target_total = target["count"].sum()

                    current = (population.groupby(dims)
                               .size().reset_index(name="current"))
                    target_scaled = (target.groupby(dims)["count"]
                                     .sum().reset_index())
                    target_scaled["target"] = (
                        target_scaled["count"] / target_total * self.target_n
                    )

                    merged = target_scaled.merge(current, on=dims, how="outer").fillna(0)
                    deviations = np.abs(
                        merged["current"] - merged["target"]
                    ) / (merged["target"] + 1)
                    max_dev = deviations.max()
                    max_deviation = max(max_deviation, max_dev)

            logger.info(f"Iteration {iteration + 1}: max deviation = {max_deviation:.4f}")

            if max_deviation < tolerance:
                logger.info(f"Converged after {iteration + 1} iterations")
                break

        # Step 3: Assign unique IDs
        population["agent_id"] = [f"A{i:05d}" for i in range(len(population))]
        population = population.reset_index(drop=True)

        self.population = population
        logger.info(f"IPF complete: {len(population)} agents generated")
        return population

    def verify(self) -> Dict[str, float]:
        """
        Verify how well the synthetic population matches all constraints.
        Returns a dictionary of constraint_name -> max_relative_deviation.
        """
        if self.population is None:
            raise ValueError("No population generated. Call fit() first.")

        results = {}
        for constraint in self.constraints:
            dims = [d for d in constraint["dimensions"]
                    if d in self.population.columns]
            if not dims:
                continue

            target = constraint["table"].copy()
            target_total = target["count"].sum()

            current = (self.population.groupby(dims)
                       .size().reset_index(name="current"))
            target_scaled = (target.groupby(dims)["count"]
                             .sum().reset_index())
            target_scaled["target"] = (
                target_scaled["count"] / target_total * self.target_n
            )

            merged = target_scaled.merge(current, on=dims, how="outer").fillna(0)
            deviations = np.abs(
                merged["current"] - merged["target"]
            ) / (merged["target"] + 1)

            results[constraint["name"]] = {
                "max_deviation": float(deviations.max()),
                "mean_deviation": float(deviations.mean()),
                "cells_checked": len(merged),
            }

        return results

    def summary(self) -> str:
        """Print summary statistics of the synthetic population."""
        if self.population is None:
            return "No population generated."

        lines = []
        lines.append(f"Synthetic Population Summary")
        lines.append(f"{'=' * 40}")
        lines.append(f"Total agents: {len(self.population)}")
        lines.append(f"Scale factor: 1:{SCALE_FACTOR:.0f}")
        lines.append(f"")

        for col in self.population.columns:
            if col in ("agent_id",):
                continue
            n_unique = self.population[col].nunique()
            if n_unique <= 20:
                lines.append(f"{col} ({n_unique} values):")
                dist = self.population[col].value_counts(normalize=True)
                for val, pct in dist.head(10).items():
                    lines.append(f"  {val}: {pct:.1%}")
                lines.append("")

        return "\n".join(lines)
