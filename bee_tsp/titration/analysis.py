#!/usr/bin/env python3
"""
Statistical analysis: bootstrap CIs and pairwise tests.
"""

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


def compute_summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-instance integrator summary with 95% bootstrap CIs.
    Returns: DataFrame with median_gap, gap_ci_95, median_cost, cost_ci_95
    """
    results = []
    
    for instance in df["instance"].unique():
        inst_data = df[df["instance"] == instance]
        
        for integrator in inst_data["integrator"].unique():
            int_data = inst_data[inst_data["integrator"] == integrator]
            
            gaps = int_data["final_gap_pct"].values
            costs = int_data["compute_cost_usd"].values
            
            # Bootstrap 95% CI (1000 resamples)
            gap_ci = bootstrap_ci(gaps, n_resamples=1000, confidence=0.95)
            cost_ci = bootstrap_ci(costs, n_resamples=1000, confidence=0.95)
            
            results.append({
                "instance": instance,
                "integrator": integrator,
                "median_gap": np.median(gaps),
                "gap_ci_95": gap_ci,
                "median_cost": np.median(costs),
                "cost_ci_95": cost_ci,
                "n_runs": len(gaps),
            })
    
    return pd.DataFrame(results)


def bootstrap_ci(data: np.ndarray, n_resamples: int = 1000, confidence: float = 0.95) -> tuple[float, float]:
    """Compute bootstrap percentile CI."""
    if len(data) < 2:
        return (float(data[0]), float(data[0])) if len(data) == 1 else (0.0, 0.0)
    
    rng = np.random.default_rng(42)
    estimates = []
    
    for _ in range(n_resamples):
        sample = rng.choice(data, size=len(data), replace=True)
        estimates.append(np.median(sample))
    
    alpha = 1 - confidence
    lower = np.percentile(estimates, 100 * alpha / 2)
    upper = np.percentile(estimates, 100 * (1 - alpha / 2))
    
    return (float(lower), float(upper))


def pairwise_mann_whitney(df: pd.DataFrame, integrator_a: str, integrator_b: str) -> dict[str, float]:
    """
    Mann-Whitney U test between two integrators (non-parametric).
    Returns p-value and effect size (common language effect size).
    """
    a_data = df[df["integrator"] == integrator_a]["final_gap_pct"].values
    b_data = df[df["integrator"] == integrator_b]["final_gap_pct"].values
    
    if len(a_data) < 5 or len(b_data) < 5:
        return {"p_value": 1.0, "effect_size": 0.0, "significant": False}
    
    statistic, p_value = mannwhitneyu(a_data, b_data, alternative="two-sided")
    
    # Common language effect size: P(X > Y)
    effect_size = np.mean([np.mean(a > b) for a in a_data for b in b_data])
    
    return {
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "significant": p_value < 0.05,
    }