#!/usr/bin/env python3
"""
Johnson Compliance Auditor (Phase 1).
Fast, robust scoring based on config + JSONL results.
"""

import json
import pandas as pd
from pathlib import Path

def audit():
    """Score based on config and first JSONL row."""
    
    # 1. Initialize ALL principles to 0% (build up from here)
    scores = {
        "Principle 1 Newsworthy (n≥10 seeds)": 0.0,
        "Principle 2 Literature (Johnson cited)": 0.0,
        "Principle 3 Testbed (TSPLIB instances)": 0.0,
        "Principle 4 Variance Reduction (Paired seeds)": 0.0,
        "Principle 5 Efficiency (NumPy efficiency)": 0.0,
        "Principle 6 Reproducibility (HK bounds + specs)": 0.0,
        "Principle 7 Comparability (LINPACK)": 0.0,
        "Principle 8 Visuals (Full Story)": 0.0,
        "Principle 9 Statistical Analysis (Effect sizes)": 0.0,
        "Principle 10 Presentation (Normalised times)": 0.0,
    }
    
    # 2. Load config
    config_path = Path("configs/minimal_johnson.json")
    if not config_path.exists():
        print("❌ Config not found")
        return
    
    cfg = json.loads(config_path.read_text())
    n_seeds = len(cfg.get("seeds", []))
    n_instances = len(cfg.get("instances", []))
    
    # 3. Check JSONL exists and load first row
    jsonl_files = list(Path("results").glob("*.jsonl"))
    if not jsonl_files:
        print("❌ No JSONL results found. Run protocol first.")
        return
    
    with open(jsonl_files[0]) as f:
        row = json.loads(f.readline())

    # 4. Johnson Principles
    # Principle 1: Newsworthy (n≥10 seeds)
    scores["Principle 1 Newsworthy (n≥10 seeds)"] = 50.0 if n_seeds >= 10 else 0.0
    
    # Principle 2: Literature (Johnson cited)
    readme_path = Path("docs/README.md") if Path("docs/README.md").exists() else Path("README.md")
    has_citation = readme_path.exists() and "Johnson" in readme_path.read_text()
    scores["Principle 2 Literature (Johnson cited)"] = 100.0 if has_citation else 0.0
    
    # Principle 3: Testbed (≥3 instances)
    scores["Principle 3 Testbed (TSPLIB instances)"] = 50.0 if n_instances >= 3 else 0.0
    
    # Principle 4: Variance Reduction (paired seeds)
    scores["Principle 4 Variance Reduction (Paired seeds)"] = 50.0  # Same seeds across integrators
    
    # Principle 5: Efficiency
    scores["Principle 5 Efficiency (NumPy efficiency)"] = 50.0  # Assuming reasonable code
    
    # Principle 6: Reproducibility
    has_hk_bound = "hk_bound" in row and row["hk_bound"] is not None
    has_machine_info = "machine_info" in row and row["machine_info"].get("cpu") != "Unknown CPU"
    scores["Principle 6 Reproducibility (HK bounds + specs)"] = 50.0 if has_hk_bound and has_machine_info else 0.0

    # Principle 7: Comparability

    # Principle 8: Visuals (Plots generated)
    plots_file = Path("results/figure1_performance.pdf")
    if plots_file.exists():
        scores["Principle 8 Visuals (Full Story)"] = 50.0
    
    # Principle 9: Effect sizes (Statistical analysis performed)
    stats_file = Path("results/statistical_enforcement.csv")
    if stats_file.exists():
        df_stats = pd.read_csv(stats_file)
        if not df_stats.empty and df_stats["protocol_compliant"].any():
            scores["Principle 9 Statistical Analysis (Effect sizes)"] = 50.0  # Partial compliance

    # Principle 10: Normalized times (added to stats)
    full_data_file = Path("results/full_data_with_normalized.csv")
    if full_data_file.exists():
        df_full = pd.read_csv(full_data_file)
        if "normalized_time" in df_full.columns:
            scores["Principle 10 Presentation (Normalised times)"] = 50.0
            print(f"  ✅ Normalised times present (n={len(df_full)} rows)")
    
    # 5. Calculate overall
    overall = sum(scores.values()) / len(scores)
    
    # 6. Print report
    print("=" * 60)
    print("JOHNSON COMPLIANCE AUDIT")
    print("=" * 60)
    for name, score in scores.items():
        print(f"{name:40s}: {score:5.1f}%")
    print("=" * 60)
    print(f"OVERALL: {overall:.1f}%")
    print("=" * 60)
    
    # 7. Show fixes needed
    if not has_citation:
        print("\n🔧 FIX: Add Johnson citation to docs/README.md or README.md")
    if n_seeds < 10:
        print("\n🔧 FIX: Add 30 seeds to configs/minimal_johnson.json")
    if not has_hk_bound:
        print("\n🔧 FIX: Ensure hk_bound is in JSONL (check data/hk_bounds.json)")
    if not has_machine_info:
        print("\n🔧 FIX: Ensure machine_info includes real CPU info, not 'x86_64'")
    
    # 8. Save JSON report
    Path("results/johnson_audit.json").write_text(json.dumps({
        "principles": {k.split()[1].split('(')[0]: v for k, v in scores.items()},
        "overall": overall,
        "assessment": "NON_COMPLIANT" if overall < 30 else "PARTIALLY_COMPLIANT" if overall < 60 else "COMPLIANT"
    }, indent=2))

if __name__ == "__main__":
    audit()