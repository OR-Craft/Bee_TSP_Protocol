#!/usr/bin/env python3
"""
Compare large instances (1000-5915 cities).
Correct solutions.txt path and robust parsing.
"""

from pathlib import Path
from bee_tsp.integrators.edge_rand import EdgeRandIntegrator
from bee_tsp.integrators.lkh_integrator import LKHIntegrator
from bee_tsp.core.solver_config import RepairConfig
from bee_tsp.core.utils import parse_tsplib_coords
import time
import sys

# Force unbuffered output
print = lambda *args, **kwargs: __builtins__.print(*args, **kwargs, flush=True)


def load_optimal_lengths():
    """Load optimal lengths from CORRECT solutions.txt location."""
    solutions = {}
    # FIXED PATH:
    sol_file = Path("/home/leo/Python/BEE_TSP/data/solutions.txt")
    
    if not sol_file.exists():
        print(f"⚠️  solutions.txt not found at {sol_file}")
        return solutions
    
    print(f"✅ Found solutions.txt at {sol_file}")
    
    try:
        content = sol_file.read_text()
        lines_parsed = 0
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            if ":" in line:
                # FIXED PARSING: Handles "dsj1000 : 18660188 (CEIL_2D)"
                try:
                    name, value = line.split(":", 1)
                    name = name.strip()
                    
                    # Extract number before any parentheses/spaces
                    value_part = value.strip().split()[0]  # Gets "18660188" from "18660188 (CEIL_2D)"
                    num_str = "".join(filter(str.isdigit, value_part))
                    
                    if num_str:
                        solutions[name] = int(num_str)
                        lines_parsed += 1
                except Exception as e:
                    print(f"⚠️  Could not parse line: '{line}' - {e}")
        
        print(f"✅ Successfully parsed {lines_parsed} optimal values")
        if "dsj1000" in solutions:
            print(f"✅ dsj1000 optimal: {solutions['dsj1000']}")
        
    except Exception as e:
        print(f"❌ Error reading solutions.txt: {e}")
    
    return solutions


def compare(instance_name: str, seeds: int = 5, lkh_seeds: int = 1):
    """Compare integrators on a single large instance."""
    path = Path(f"data/tsplib/{instance_name}.tsp")
    
    if not path.exists():
        print(f"❌ File not found: {path}")
        return None
    
    # FIXED: Parse coords and store n for later use
    try:
        coords = parse_tsplib_coords(path)
        n = len(coords)
        print(f"✅ {path.name}: {n} cities parsed")
    except Exception as e:
        print(f"❌ Failed to parse {path.name}: {e}")
        return None
    
    # Get optimal length
    opt_lengths = load_optimal_lengths()
    optimal = opt_lengths.get(instance_name, "N/A")
    if optimal == "N/A":
        print(f"⚠️  No optimal value found for '{instance_name}'")
    else:
        print(f"✅ Optimal value loaded: {optimal}")
    
    print(f"\n🔍 Running {instance_name} (optimal: {optimal}, {n}c)")
    print("=" * 70)
    
    rc = RepairConfig(time_ms=50)
    
    # EdgeRand
    print("EdgeRand (5 seeds, 1s max each)...")
    er = EdgeRandIntegrator(rc)
    er_lengths = []
    er_start = time.time()
    for seed in range(seeds):
        try:
            _, trace = er.solve(path, max_time_s=1.0, seed=seed+1, candidate_k=10)
            length = trace[0][1] if trace else float('inf')
            er_lengths.append(length)
        except Exception as e:
            print(f"  ❌ ER seed {seed+1} failed: {e}")
            return None
    er_time = time.time() - er_start
    
    # LKH
    print(f"LKH ({lkh_seeds} seeds, 30s max each)...")
    lkh = LKHIntegrator(rc)
    lkh_lengths = []
    lkh_start = time.time()
    for seed in range(lkh_seeds):
        try:
            print(f"  Seed {seed+1}/{lkh_seeds}...")
            _, trace = lkh.solve(path, max_time_s=30.0, seed=seed+1, candidate_k=10)
            length = trace[0][1] if trace else float('inf')
            lkh_lengths.append(length)
        except Exception as e:
            print(f"  ❌ LKH seed {seed+1} failed: {e}")
            return None
    lkh_time = time.time() - lkh_start
    
    # Results
    er_mean = sum(er_lengths) / len(er_lengths)
    lkh_mean = sum(lkh_lengths) / len(lkh_lengths) if lkh_lengths else 0
    
    print(f"✅ EdgeRand: {er_mean:.0f} | Total: {er_time:.2f}s")
    print(f"✅ LKH: {lkh_mean:.0f} | Total: {lkh_time:.2f}s")
    
    if isinstance(optimal, int):
        er_gap = er_mean / optimal
        quality_gap = er_mean / lkh_mean if lkh_mean > 0 else float('inf')
        print(f"📊 Gaps: ER vs Optimal {er_gap:.1f}x | Quality {quality_gap:.1f}x")
    
    return {
        "instance": instance_name,
        "cities": n,  # FIXED: Now uses n from coords
        "optimal": optimal,
        "edge_rand": f"{er_mean:.0f} ({er_time:.2f}s)",
        "lkh": f"{lkh_mean:.0f} ({lkh_time:.2f}s)",
    }


def main():
    """Run on selected large instances."""
    
    benchmarks = [
        ("dsj1000", 3),    # 1000c, 3 LKH seeds
        ("pr2392", 2),     # 2392c, 2 LKH seeds
        ("pcb3038", 1),    # 3038c, 1 LKH seed
        ("rl5915", 1),     # 5915c, 1 LKH seed
    ]
    
    print("BEE_TSP Large Instance Scaling Test")
    print("STARTED: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    results = []
    for instance, lkh_seeds in benchmarks:
        result = compare(instance, seeds=5, lkh_seeds=lkh_seeds)
        results.append(result if result else {"instance": instance, "error": "failed"})
        print()
    
    # Final summary
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"{'Instance':<12} {'Cities':>8} {'Optimal':>12} {'EdgeRand':>25} {'LKH':>25}")
    print("-" * 70)
    for r in results:
        if "error" in r:
            print(f"  {r['instance']:<12} {'FAILED':>58}")
        else:
            print(f"  {r['instance']:<12} {r['cities']:>8} {str(r['optimal']):>12} {r['edge_rand']:>25} {r['lkh']:>25}")
    
    print("\nEND: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)


if __name__ == "__main__":
    main()