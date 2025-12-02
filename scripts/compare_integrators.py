#!/usr/bin/env python3
"""
Head-to-head comparison of EdgeRand vs LKH.
Demonstrates the performance gap that BEETSP aims to close.
"""

from pathlib import Path
from bee_tsp.integrators.edge_rand import EdgeRandIntegrator
from bee_tsp.integrators.lkh_integrator import LKHIntegrator
from bee_tsp.core.solver_config import RepairConfig
from bee_tsp.core.utils import parse_tsplib_coords
import time
from tabulate import tabulate  # pip install tabulate if needed

def compare(instance_name: str, optimal: int, seeds: int = 10):
    """Compare integrators on a single instance."""
    path = Path(f"data/tsplib/{instance_name}.tsp")
    repair_cfg = RepairConfig(time_ms=50)
    
    # Verify file exists
    if not path.exists():
        return None
    
    # Load coordinates once (for reference)
    coords = parse_tsplib_coords(path)
    n = len(coords)
    
    # EdgeRand
    er = EdgeRandIntegrator(repair_cfg)
    er_times = []
    er_lengths = []
    
    start = time.time()
    for seed in range(seeds):
        _, trace = er.solve(path, max_time_s=1.0, seed=seed+1, candidate_k=10)
        er_times.append(trace[0][0])
        er_lengths.append(trace[0][1])
    er_total = time.time() - start
    
    # LKH
    lkh = LKHIntegrator(repair_cfg)
    lkh_times = []
    lkh_lengths = []
    
    start = time.time()
    for seed in range(seeds):
        _, trace = lkh.solve(path, max_time_s=5.0, seed=seed+1, candidate_k=10)
        lkh_times.append(trace[0][0])
        lkh_lengths.append(trace[0][1])
    lkh_total = time.time() - start
    
    # Calculate statistics
    er_mean = sum(er_lengths) / len(er_lengths)
    er_std = (sum((x - er_mean) ** 2 for x in er_lengths) / len(er_lengths)) ** 0.5
    
    lkh_mean = sum(lkh_lengths) / len(lkh_lengths)
    lkh_std = (sum((x - lkh_mean) ** 2 for x in lkh_lengths) / len(lkh_lengths)) ** 0.5
    
    quality_gap = er_mean / lkh_mean
    
    return {
        "Instance": f"{instance_name} ({n}c)",
        "Optimal": optimal,
        "Edge_Rand": f"{er_mean:.0f} ± {er_std:.0f}",
        "LKH": f"{lkh_mean:.0f} ± {lkh_std:.0f}",
        "Gap": f"{quality_gap:.1f}x",
        "ER_time": f"{er_total:.2f}s",
        "LKH_time": f"{lkh_total:.2f}s",
    }

def main():
    """Run comparison on benchmark set."""
    
    # Small instances with known optima
    benchmarks = [
        ("eil51", 426),
        ("eil101", 629),
        ("berlin52", 7542),
        ("ch130", 6110),
        ("pcb442", 50778),
    ]
    
    results = []
    for instance, optimal in benchmarks:
        print(f"Running {instance}...")
        result = compare(instance, optimal, seeds=10)
        if result:
            results.append(result)
    
    # Print table
    print("\n" + "="*80)
    print("BEE_TSP: Edge_Rand vs LKH Comparison")
    print("="*80)
    
    headers = ["Instance", "Optimal", "Edge_Rand", "LKH", "Gap", "ER_time", "LKH_time"]
    rows = [[r[h] for h in headers] for r in results]
    
    print(tabulate(rows, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    main()