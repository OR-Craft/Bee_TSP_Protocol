#!/usr/bin/env python3
"""
Minimal titration runner for laptop experiments.
Runs one instance × one integrator × one budget × all seeds.
"""

from pathlib import Path
import sys
import time
from bee_tsp.titration.protocol import TitrationProtocol
from bee_tsp.titration.config import TitrationConfig

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.run_titration configs/experiment_v1.json")
        sys.exit(1)
    
    config_path = Path(sys.argv[1])
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        sys.exit(1)
    
    # Load config
    cfg = TitrationConfig.from_json(config_path)
    
    # Run protocol
    protocol = TitrationProtocol(cfg)
    df = protocol.run()
    
    # Save results
    results_path = Path("results/v1_lkh_baseline.csv")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(results_path, index=False)
    
    print(f"\n✓ Results saved to {results_path}")
    print(f"  Total runs: {len(df)}")
    print(f"  Average time: {df['time_to_best_s'].mean():.2f}s")
    print(f"  Median gap: {df['final_gap_pct'].median():.2f}%")

if __name__ == "__main__":
    main()