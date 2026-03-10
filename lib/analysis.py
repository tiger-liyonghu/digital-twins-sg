"""
Shared analysis and reporting utilities for simulation results.

Provides standardized breakdowns by demographics, accuracy metrics, etc.
"""

import math
from collections import Counter


def compute_distribution(responses, options, confidence=0.95):
    """Compute choice distribution with confidence intervals from responses."""
    choices = [r["choice"] for r in responses]
    counts = Counter(choices)
    total = len(choices)

    # z-score for confidence level
    z = 1.96 if confidence == 0.95 else 1.645 if confidence == 0.90 else 2.576

    result = {}
    for opt in options:
        count = counts.get(opt, 0)
        pct = round(count / total * 100, 1) if total > 0 else 0
        # Wilson score interval for binomial proportion
        p_hat = count / total if total > 0 else 0
        if total > 0:
            margin = z * math.sqrt(p_hat * (1 - p_hat) / total) * 100
        else:
            margin = 0
        result[opt] = {
            "count": count,
            "pct": pct,
            "ci_low": round(max(0, pct - margin), 1),
            "ci_high": round(min(100, pct + margin), 1),
        }
    return result


def compute_mae(predicted_pcts, actual_pcts):
    """Mean Absolute Error in percentage points."""
    deviations = []
    for k in predicted_pcts:
        if k in actual_pcts:
            deviations.append(abs(predicted_pcts[k] - actual_pcts[k]))
    return round(sum(deviations) / len(deviations), 1) if deviations else 0


def breakdown_by_field(responses, field, options, bins=None):
    """
    Break down responses by a demographic field.

    Args:
        responses: List of response dicts
        field: e.g., "agent_age", "agent_ethnicity", "agent_income"
        options: List of option strings
        bins: Dict of {label: (lo, hi)} for numeric fields, or None for categorical

    Returns:
        Dict of {label: {option: pct, ...}}
    """
    result = {}

    if bins:
        for label, (lo, hi) in bins.items():
            group = [r for r in responses if lo <= (r.get(field, 0) or 0) <= hi]
            if not group:
                continue
            gc = Counter(r["choice"] for r in group)
            result[label] = {
                "_n": len(group),
                **{opt: round(gc.get(opt, 0) / len(group) * 100, 1) for opt in options},
            }
    else:
        values = sorted(set(r.get(field, "") for r in responses))
        for v in values:
            if not v:
                continue
            group = [r for r in responses if r.get(field) == v]
            if not group:
                continue
            gc = Counter(r["choice"] for r in group)
            result[v] = {
                "_n": len(group),
                **{opt: round(gc.get(opt, 0) / len(group) * 100, 1) for opt in options},
            }

    return result


def print_breakdown(responses, field, options, title, bins=None, highlight_options=None):
    """Print a formatted breakdown table."""
    print(f"\n--- {title} ---")
    bd = breakdown_by_field(responses, field, options, bins=bins)
    show = highlight_options or options[:2]
    for label, data in bd.items():
        parts = [f"{opt.split('(')[1].rstrip(')') if '(' in opt else opt[:15]} {data.get(opt, 0):.0f}%"
                 for opt in show]
        print(f"  {label} (n={data['_n']}): {', '.join(parts)}")
