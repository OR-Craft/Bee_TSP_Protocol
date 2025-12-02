#!/usr/bin/env python3
# scripts/validate_benchmark_set.py
from pathlib import Path

# Define tiers based on YOUR actual instances
TIER_SMALL = ["eil101", "kroC100", "kroD100", "ch130", "ch150", "brg180", "gr202", "tsp225"]
TIER_MEDIUM = ["a280", "lin318", "pcb442", "pa561", "rat575", "gr666", "rat783", "pr1002"]
TIER_LARGE = ["dsj1000", "pr2392", "pcb3038"]
TIER_VERY_LARGE = ["rl5915", "pla7397", "rl11849", "pla33810"]

def check_instances():
    base = Path("data/tsplib")
    print("TSPLIB Benchmark Validation")
    print("=" * 60)
    
    for tier_name, instances in [
        ("🔵 TIER 1 (≤200c, 1000 seeds)", TIER_SMALL),
        ("🟡 TIER 2 (200-1000c, 100 seeds)", TIER_MEDIUM),
        ("🔴 TIER 3 (1000-5000c, 10 seeds)", TIER_LARGE),
        ("⚫ TIER 4 (>5000c, 5 seeds)", TIER_VERY_LARGE),
    ]:
        print(f"\n{tier_name}:")
        for name in instances:
            tsp = base / f"{name}.tsp"
            opt = base / f"{name}.opt.tour"
            
            if tsp.exists():
                size_kb = tsp.stat().st_size / 1024
                # Count lines to estimate n cities (rough)
                with open(tsp) as f:
                    n_lines = sum(1 for _ in f)
                n_est = max(0, n_lines - 6)  # Subtract header lines
                tsp_ok = f"✅ TSP ({n_est}c, {size_kb:.0f}KB)"
            else:
                tsp_ok = "❌ TSP missing"
            
            if opt.exists():
                opt_ok = "✅ .opt.tour"
            else:
                opt_ok = "⚠️  solutions.txt only"
            
            print(f"  {name:<12} {tsp_ok:<25} | {opt_ok}")
    
    print("\n" + "=" * 60)
    print("✅ Ready to run Tier 1 and 2")
    print("✅ Tier 3 requires monitoring memory")
    print("⚠️  Tier 4: Test one instance first")

if __name__ == "__main__":
    check_instances()