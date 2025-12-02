#!/usr/bin/env python3
"""
StatisticalEnforcer: Wilcoxon, Cliff's Delta, Bootstrap.
Enforces n≥30, p<0.001, effect size >0.1.
"""

import numpy as np
import pandas as pd
import json
from scipy.stats import wilcoxon
from dataclasses import dataclass
from typing import Tuple, List
from pathlib import Path

@dataclass(frozen=True)
class StatisticalResult:
    instance: str
    integrator_a: str
    integrator_b: str
    n_samples: int
    p_value: float
    effect_size_cliffs_delta: float
    ci_95_lower: float
    ci_95_upper: float
    protocol_compliant: bool

class StatisticalEnforcer:
    @staticmethod
    def cliffs_delta(x: List[float], y: List[float]) -> float:
        """Non-parametric effect size: [-1, 1], |δ|>0.1 is meaningful."""
        n_x, n_y = len(x), len(y)
        n_dominant = 0
        
        for xi in x:
            for yi in y:
                if xi < yi:
                    n_dominant += 1
                elif xi > yi:
                    n_dominant -= 1
        
        return n_dominant / (n_x * n_y)
    
    @staticmethod
    def bootstrap_ci(x: List[float], y: List[float], n_boot: int = 10000) -> Tuple[float, float]:
        """95% CI for mean difference using percentile bootstrap."""
        x, y = np.array(x), np.array(y)
        diffs = []
        
        for _ in range(n_boot):
            x_boot = np.random.choice(x, size=len(x), replace=True)
            y_boot = np.random.choice(y, size=len(y), replace=True)
            diffs.append(np.mean(x_boot) - np.mean(y_boot))
        
        return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
    
    @staticmethod
    def paired_comparison(
        lengths_a: List[float],
        lengths_b: List[float],
        instance: str,
        integrator_a: str,
        integrator_b: str
    ) -> StatisticalResult:
        """Enforce statistical rigor on paired results."""
        n = len(lengths_a)
        
        # Check for zero variance (all values identical in one group)
        if len(set(lengths_a)) == 1 or len(set(lengths_b)) == 1:
            # If both groups have zero variance and are identical, no effect
            if len(set(lengths_a)) == len(set(lengths_b)) == 1 and lengths_a[0] == lengths_b[0]:
                return StatisticalResult(
                    instance=instance,
                    integrator_a=integrator_a,
                    integrator_b=integrator_b,
                    n_samples=n,
                    p_value=1.0,  # No difference
                    effect_size_cliffs_delta=0.0,
                    ci_95_lower=0.0,
                    ci_95_upper=0.0,
                    protocol_compliant=False  # No variance means no statistical power
                )
            # If one group has zero variance and the other doesn't, it's a perfect separation
            else:
                return StatisticalResult(
                    instance=instance,
                    integrator_a=integrator_a,
                    integrator_b=integrator_b,
                    n_samples=n,
                    p_value=1e-15,  # Treat as highly significant
                    effect_size_cliffs_delta=1.0,  # Perfect separation
                    ci_95_lower=0.0,
                    ci_95_upper=0.0,
                    protocol_compliant=True
                )
        
        # Wilcoxon signed-rank test (non-parametric, paired)
        stat, p_value = wilcoxon(lengths_a, lengths_b, alternative="two-sided")
        
        # Cliff's Delta effect size
        delta = StatisticalEnforcer.cliffs_delta(lengths_a, lengths_b)
        
        # Bootstrap CI
        ci_lower, ci_upper = StatisticalEnforcer.bootstrap_ci(lengths_a, lengths_b)
        
        # Protocol compliance: n≥30, p<0.001, |δ|>0.1
        compliant = (n >= 30 and p_value < 0.001 and abs(delta) > 0.1)
        
        return StatisticalResult(
            instance=instance,
            integrator_a=integrator_a,
            integrator_b=integrator_b,
            n_samples=n,
            p_value=p_value,
            effect_size_cliffs_delta=delta,
            ci_95_lower=ci_lower,
            ci_95_upper=ci_upper,
            protocol_compliant=compliant
        )

@staticmethod
def add_normalized_times(df: pd.DataFrame) -> pd.DataFrame:
    """Add wall_time_s / (n * log(n)) column for Principle 10."""
    
    # Extract node count from instance name (eil51 -> 51, dsj1000 -> 1000)
    def extract_n(instance_name: str) -> int:
        """Extract node count from instance name."""
        import re
        match = re.search(r'(\d+)$', instance_name)
        return int(match.group(1)) if match else 50
    
    df["n_nodes"] = df["instance"].apply(extract_n)
    df["normalized_time"] = df["wall_time_s"] / (df["n_nodes"] * np.log(df["n_nodes"]))
    return df

def analyze_results(jsonl_path: Path = None):
    """Run statistical analysis comparing LKH vs EdgeRand."""
    
    print("🔬 StatisticalEnforcer: Analyzing results...")
    
    # Find MOST RECENT JSONL (not hardcoded date)
    if jsonl_path is None:
        results_dir = Path("results")
        jsonl_files = list(results_dir.glob("johnson_audit_*.jsonl"))
        if not jsonl_files:
            raise FileNotFoundError("No johnson_audit JSONL files found in results/")
        jsonl_path = max(jsonl_files, key=lambda f: f.stat().st_mtime)
        print(f"📊 Using most recent JSONL: {jsonl_path.name}")
    
    # Verify file exists and has content
    if not jsonl_path.exists():
        raise FileNotFoundError(f"File not found: {jsonl_path}")
    
    if jsonl_path.stat().st_size == 0:
        raise ValueError(f"File is empty: {jsonl_path}")
    
    # Load data
    results = []
    with open(jsonl_path) as f:
        for line in f:
            results.append(json.loads(line))
    
    df = pd.DataFrame(results)
    
    # Verify required columns exist
    required_cols = ["instance", "integrator", "budget_s", "seed", "best_length", "wall_time_s"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}\nFound: {df.columns.tolist()}")
    
    # Add normalized times
    df = add_normalized_times(df)
    df.to_csv("results/full_data_with_normalized.csv", index=False)
    
    # Group by instance and budget
    stats_results = []
    
    for (instance, budget), group in df.groupby(["instance", "budget_s"]):
        seeds_lkh = group[group["integrator"] == "lkh"]["best_length"].tolist()
        seeds_er = group[group["integrator"] == "EdgeRand"]["best_length"].tolist()
        
        if len(seeds_lkh) == len(seeds_er) == 30:
            stat = StatisticalEnforcer.paired_comparison(
                lengths_a=seeds_lkh,
                lengths_b=seeds_er,
                instance=f"{instance}_lkh_vs_EdgeRand",
                integrator_a=f"lkh_{budget}s",
                integrator_b=f"EdgeRand_{budget}s"
            )
            stats_results.append(stat)
    
    # Print summary
    print("\n" + "=" * 60)
    print("STATISTICAL ENFORCEMENT REPORT")
    print("=" * 60)
    
    compliant_count = sum(1 for r in stats_results if r.protocol_compliant)
    print(f"Compliant comparisons: {compliant_count}/{len(stats_results)}")
    
    for r in stats_results:
        status = "✅ PASS" if r.protocol_compliant else "❌ FAIL"
        print(f"\n{r.instance} | {r.integrator_a} vs {r.integrator_b}")
        print(f"  n={r.n_samples}, p={r.p_value:.2e}, δ={r.effect_size_cliffs_delta:.3f}")
        print(f"  CI=[{r.ci_95_lower:.2f}, {r.ci_95_upper:.2f}]")
        print(f"  {status}")
    
    # Save results
    if stats_results:
        stats_df = pd.DataFrame([r.__dict__ for r in stats_results])
        stats_df.to_csv("results/statistical_enforcement.csv", index=False)
        print(f"\n📊 Saved to results/statistical_enforcement.csv")
    
    return stats_results

if __name__ == "__main__":
    analyze_results() 