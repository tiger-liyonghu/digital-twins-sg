"""
CPF (Central Provident Fund) Mathematical Model.

Singapore's CPF is a mandatory savings scheme with 4 accounts:
- OA (Ordinary Account): housing, education, investment
- SA (Special Account): retirement, investment
- MA (MediSave Account): medical expenses
- RA (Retirement Account): created at 55, from SA + OA

Contribution rates depend on age bracket and residency status.
Interest rates: OA = 2.5%, SA = 4%, MA = 4%, RA = 4%
(with extra 1% on first $60K, extra 1% on first $30K for 55+)

Mathematical model:
- Monthly contributions: C(age, wage) = wage × rate(age)
- Annual interest: I(balance, account) = balance × r(account) + extras
- OA withdrawal for housing: W_housing(age, flat_type)
- RA formation at 55: min(SA + OA, FRS)
- CPF LIFE payout at 65: annuity formula

References:
- CPF Board Contribution Rates Table (2024)
- CPF Interest Rate Policy
"""

import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


# ============================================================
# CPF Contribution Rates (2024, Total = Employee + Employer)
# ============================================================

# Rates as fraction of ordinary wages (capped at OW ceiling)
# Format: (age_lower, age_upper, oa_rate, sa_rate, ma_rate)
CONTRIBUTION_RATES_CITIZEN = [
    (0,   15,  0.000, 0.000, 0.000),  # No CPF for <16
    (16,  55,  0.230, 0.060, 0.080),  # Total: 37%
    (55,  60,  0.150, 0.045, 0.075),  # Total: 27%
    (60,  65,  0.085, 0.030, 0.065),  # Total: 18%
    (65,  70,  0.060, 0.020, 0.050),  # Total: 13%
    (70, 200,  0.050, 0.010, 0.040),  # Total: 10%
]

# PR rates (graduated over 3 years)
PR_RATE_MULTIPLIER = {
    0: 0.60,  # Year 1-2: 60% of citizen rate
    1: 0.60,
    2: 0.80,  # Year 3: 80%
    3: 1.00,  # Year 4+: full rate
}

# Wage ceiling (2024)
OW_CEILING = 6800  # Ordinary Wage ceiling per month
AW_CEILING = 102000  # Additional Wage ceiling per year

# Interest rates
INTEREST_RATES = {
    "OA": 0.025,   # 2.5% per annum
    "SA": 0.040,   # 4.0% per annum
    "MA": 0.040,   # 4.0% per annum
    "RA": 0.040,   # 4.0% per annum
}

# Extra interest (on combined balances)
EXTRA_INTEREST_FIRST_60K = 0.01    # 1% extra on first $60K
EXTRA_INTEREST_FIRST_30K_55 = 0.01  # additional 1% for 55+ on first $30K

# CPF minimums (2024)
FRS = 205800    # Full Retirement Sum
BRS = 102900    # Basic Retirement Sum
ERS = 308700    # Enhanced Retirement Sum
BHS = 71500     # Basic Healthcare Sum (MediSave)


class CPFModel:
    """Mathematical model of CPF accumulation and drawdown."""

    def __init__(self):
        pass

    def get_contribution_rates(self, age: int, residency: str,
                                years_in_sg: int = 10) -> Tuple[float, float, float]:
        """
        Get monthly CPF contribution rates (OA, SA, MA) as fraction of wage.

        Args:
            age: agent's age
            residency: Citizen, PR, or other
            years_in_sg: years since obtaining PR (for graduated rates)

        Returns:
            (oa_rate, sa_rate, ma_rate) as fractions
        """
        if residency not in ("Citizen", "PR"):
            return (0.0, 0.0, 0.0)

        # Find base rates by age
        oa_rate = sa_rate = ma_rate = 0.0
        for lo, hi, oa, sa, ma in CONTRIBUTION_RATES_CITIZEN:
            if lo <= age < hi:
                oa_rate, sa_rate, ma_rate = oa, sa, ma
                break

        # Apply PR multiplier
        if residency == "PR":
            mult = PR_RATE_MULTIPLIER.get(min(years_in_sg, 3), 1.0)
            oa_rate *= mult
            sa_rate *= mult
            ma_rate *= mult

        return (oa_rate, sa_rate, ma_rate)

    def monthly_contribution(self, age: int, monthly_wage: int,
                              residency: str,
                              years_in_sg: int = 10) -> Dict[str, int]:
        """
        Calculate monthly CPF contribution in dollars.

        Returns:
            {"OA": int, "SA": int, "MA": int, "total": int}
        """
        oa_rate, sa_rate, ma_rate = self.get_contribution_rates(
            age, residency, years_in_sg)

        # Cap at OW ceiling
        capped_wage = min(monthly_wage, OW_CEILING)

        oa = int(capped_wage * oa_rate)
        sa = int(capped_wage * sa_rate)
        ma = int(capped_wage * ma_rate)

        return {"OA": oa, "SA": sa, "MA": ma, "total": oa + sa + ma}

    def annual_interest(self, balances: Dict[str, int],
                        age: int) -> Dict[str, int]:
        """
        Calculate annual CPF interest.

        Rules:
        1. Base interest: OA 2.5%, SA/MA/RA 4%
        2. Extra 1% on first $60K of combined balances
           (up to $20K from OA, rest from SA/MA/RA)
        3. Extra 1% on first $30K for members 55+
           (up to $20K from RA, rest from OA/SA/MA)

        Returns:
            {"OA": int, "SA": int, "MA": int, "RA": int}
        """
        oa = balances.get("OA", 0)
        sa = balances.get("SA", 0)
        ma = balances.get("MA", 0)
        ra = balances.get("RA", 0)

        # Base interest
        interest = {
            "OA": int(oa * INTEREST_RATES["OA"]),
            "SA": int(sa * INTEREST_RATES["SA"]),
            "MA": int(ma * INTEREST_RATES["MA"]),
            "RA": int(ra * INTEREST_RATES["RA"]),
        }

        # Extra 1% on first $60K
        # Applied to: up to $20K from OA, then SA, MA, RA
        extra_60k_remaining = 60000
        oa_extra_eligible = min(oa, 20000, extra_60k_remaining)
        extra_60k_remaining -= oa_extra_eligible
        sa_extra_eligible = min(sa, extra_60k_remaining)
        extra_60k_remaining -= sa_extra_eligible
        ma_extra_eligible = min(ma, extra_60k_remaining)
        extra_60k_remaining -= ma_extra_eligible
        ra_extra_eligible = min(ra, extra_60k_remaining)

        interest["OA"] += int(oa_extra_eligible * EXTRA_INTEREST_FIRST_60K)
        interest["SA"] += int(sa_extra_eligible * EXTRA_INTEREST_FIRST_60K)
        interest["MA"] += int(ma_extra_eligible * EXTRA_INTEREST_FIRST_60K)
        interest["RA"] += int(ra_extra_eligible * EXTRA_INTEREST_FIRST_60K)

        # Extra 1% on first $30K for 55+
        if age >= 55:
            extra_30k_remaining = 30000
            ra_extra_55 = min(ra, 20000, extra_30k_remaining)
            extra_30k_remaining -= ra_extra_55
            oa_extra_55 = min(oa, extra_30k_remaining)
            extra_30k_remaining -= oa_extra_55
            sa_extra_55 = min(sa, extra_30k_remaining)
            extra_30k_remaining -= sa_extra_55
            ma_extra_55 = min(ma, extra_30k_remaining)

            interest["RA"] += int(ra_extra_55 * EXTRA_INTEREST_FIRST_30K_55)
            interest["OA"] += int(oa_extra_55 * EXTRA_INTEREST_FIRST_30K_55)
            interest["SA"] += int(sa_extra_55 * EXTRA_INTEREST_FIRST_30K_55)
            interest["MA"] += int(ma_extra_55 * EXTRA_INTEREST_FIRST_30K_55)

        return interest

    def form_retirement_account(self, balances: Dict[str, int]) -> Dict[str, int]:
        """
        Form RA at age 55.

        Transfer from SA first, then OA, up to FRS.
        Remaining OA/SA balances are kept.

        Returns:
            Updated balances dict
        """
        sa = balances.get("SA", 0)
        oa = balances.get("OA", 0)

        # Transfer SA first
        sa_to_ra = min(sa, FRS)
        remaining_frs = FRS - sa_to_ra

        # Then OA
        oa_to_ra = min(oa, remaining_frs)

        ra = sa_to_ra + oa_to_ra

        return {
            "OA": oa - oa_to_ra,
            "SA": sa - sa_to_ra,
            "MA": balances.get("MA", 0),
            "RA": ra,
        }

    def cpf_life_payout(self, ra_balance: int,
                        scheme: str = "standard") -> int:
        """
        Estimate monthly CPF LIFE payout at age 65.

        Simplified annuity calculation:
        Monthly payout ≈ RA_balance / (expected_remaining_life_months × discount_factor)

        Standard plan: higher monthly, lower bequest
        Basic plan: lower monthly, higher bequest

        Returns:
            Estimated monthly payout in SGD
        """
        # Average remaining life at 65: ~20 years = 240 months
        # Discount for pooling risk: ~0.85
        expected_months = 240

        if scheme == "standard":
            factor = 0.85
        elif scheme == "basic":
            factor = 0.70
        else:
            factor = 0.78  # escalating plan

        monthly = int(ra_balance * factor / expected_months)
        return max(monthly, 0)

    def simulate_lifetime_cpf(self, start_age: int = 22, end_age: int = 90,
                               monthly_wage: int = 4500,
                               wage_growth: float = 0.03,
                               residency: str = "Citizen") -> Dict[str, list]:
        """
        Simulate CPF accumulation over a lifetime.

        Returns:
            Dict with age-indexed lists for each account balance
        """
        balances = {"OA": 0, "SA": 0, "MA": 0, "RA": 0}
        history = {"age": [], "OA": [], "SA": [], "MA": [], "RA": [],
                   "total": [], "monthly_wage": []}

        wage = monthly_wage

        for age in range(start_age, end_age + 1):
            # Monthly contributions × 12
            if age < 63:  # working age
                contrib = self.monthly_contribution(age, int(wage), residency)
                balances["OA"] += contrib["OA"] * 12
                balances["SA"] += contrib["SA"] * 12
                balances["MA"] += contrib["MA"] * 12

            # Annual interest
            interest = self.annual_interest(balances, age)
            balances["OA"] += interest["OA"]
            balances["SA"] += interest["SA"]
            balances["MA"] += interest["MA"]
            balances["RA"] += interest["RA"]

            # Cap MA at BHS
            if balances["MA"] > BHS:
                overflow = balances["MA"] - BHS
                balances["MA"] = BHS
                balances["SA"] += overflow  # overflow to SA

            # Form RA at 55
            if age == 55:
                balances = self.form_retirement_account(balances)

            # CPF LIFE payouts from 65
            if age >= 65 and balances["RA"] > 0:
                payout = self.cpf_life_payout(balances["RA"])
                balances["RA"] -= payout * 12
                balances["RA"] = max(balances["RA"], 0)

            # Record
            history["age"].append(age)
            history["OA"].append(balances["OA"])
            history["SA"].append(balances["SA"])
            history["MA"].append(balances["MA"])
            history["RA"].append(balances["RA"])
            history["total"].append(sum(balances.values()))
            history["monthly_wage"].append(int(wage))

            # Wage growth
            if age < 55:
                wage *= (1 + wage_growth)
            elif age < 63:
                wage *= 0.98  # slight decline in later years

        return history
