#!/usr/bin/env python3
"""
Principle 8: Generate boxplots of performance vs. instance size.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def generate_plots(jsonl_path: Path = None):
    """Generate Figure 1: Performance comparison plot."""
    
    # Find the most recent JSONL if none specified
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
    
    # Load with proper StringIO wrapper to avoid FutureWarning
    import io
    with open(jsonl_path) as f:
        content = f.read()
    
    if not content.strip():
        raise ValueError("JSONL file has no content")
    
    df = pd.read_json(io.StringIO(content), lines=True)
    
    # Verify expected columns exist
    required_cols = ["instance", "integrator", "budget_s", "best_length", "hk_bound"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    print(f"✅ Loaded {len(df)} rows from {jsonl_path.name}")
    
    # Plot 1: Tour length vs. instance size (by integrator)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # LKH vs EdgeRand across instances
    for integrator, color in [("lkh", "blue"), ("EdgeRand", "red")]:
        data = df[df["integrator"] == integrator]
        axes[0].scatter(data["hk_bound"], data["best_length"], 
                       alpha=0.6, label=integrator, color=color)
    
    axes[0].set_xlabel("Reference bound (HK/optimal)")
    axes[0].set_ylabel("Best tour length")
    axes[0].set_title("Figure 1a: Integrator Performance")
    axes[0].legend()
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    
    # Plot 2: Cliff's Delta by instance size
    stats_df = pd.read_csv("results/statistical_enforcement.csv")
    instances = stats_df["instance"].str.replace("_lkh_vs_EdgeRand", "")
    deltas = stats_df["effect_size_cliffs_delta"]
    
    axes[1].bar(range(len(instances)), deltas)
    axes[1].set_xticks(range(len(instances)))
    axes[1].set_xticklabels(instances, rotation=45)
    axes[1].set_ylabel("Cliff's Delta")
    axes[1].set_title("Figure 1b: Effect Sizes (δ)")
    axes[1].axhline(y=0.1, color='red', linestyle='--', label='Meaningful threshold')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig("results/figure1_performance.pdf")
    print("✅ Saved Figure 1 to results/figure1_performance.pdf")

if __name__ == "__main__":
    generate_plots()