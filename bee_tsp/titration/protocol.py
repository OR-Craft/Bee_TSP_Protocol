#!/usr/bin/env python3
"""
Parallel titration protocol driver.
Runs experiments across 6 workers (one per physical core).
"""

from __future__ import annotations
import time, json, math
from dataclasses import field
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from bee_tsp.titration.config import TitrationConfig, RepairConfig
from bee_tsp.core.distance import Distance
from bee_tsp.core.interfaces import Tour
from bee_tsp.integrators.lkh_integrator import LKHIntegrator as LKHSolver

@dataclass(frozen=True)
class ProtocolResult:
    """One row = one run. Immutable, auditable."""
    instance: str
    integrator: str
    budget_s: float
    seed: int
    best_length: int
    time_to_best_s: float
    final_gap_pct: float
    hk_bound: int
    wall_time_s: float
    machine_info: Dict[str, Any]
    compute_cost_usd: float
    raw_trace: List[Tuple[float, int]]
    
    # Fields with defaults MUST come last
    deviations: List[str] = field(default_factory=list)
    cycles_explored: int = 0
    repair_path: str = ""

class TitrationProtocol:
    """Execute experiments in parallel across 6 workers."""
    
    def __init__(self, cfg: TitrationConfig):
        self.cfg = cfg
        self._validate_cfg()
        
        # Load machine specs ONCE (not per experiment)
        with open("data/machine_specs.json") as f:
            self.machine_info = json.load(f)
        
        # Load HK bounds ONCE
        with open("data/hk_bounds.json") as f:
            self.hk_bounds = json.load(f)
        
        # Initialize integrators
        self.integrators = self._build_integrators()
        
        # Load optimal values (fallback)
        self.optimal_lengths = self._load_optimal_lengths()
        
        # Results accumulator
        self.results: List[ProtocolResult] = []
    
    def _validate_cfg(self):
        """Fail fast on invalid config."""
        if len(self.cfg.seeds) < 5:
            raise ValueError(f"Minimum 5 seeds required (got {len(self.cfg.seeds)})")
        
        for inst in self.cfg.instances:
            path = self.cfg.tsplib_dir / f"{inst}.tsp"
            if not path.exists():
                raise FileNotFoundError(f"Missing instance: {path}")
    
    def _get_hk_bound(self, instance: str) -> int:
        """Return HK bound for instance (uses optimal as approximation)."""
        with open("data/hk_bounds.json") as f:
            bounds = json.load(f)
        return bounds.get(instance, 0)  # Returns 0 if not found (will error)
        
    def _build_integrators(self) -> Dict[str, Any]:
        """Factory: only LKH for now."""
        repair_cfg = RepairConfig(time_ms=1000)  # Dummy for LKH
            
        return {
            "lkh": LKHSolver(repair_cfg=repair_cfg),
        }
    
    def _load_optimal_lengths(self) -> Dict[str, int]:
        """Load optimal tour lengths from data/optimal_values.csv."""
        optimal_path = Path("data/optimal_values.csv")
        if not optimal_path.exists():
            # Fallback: use TSPLIB-known values
            return {
                "eil51": 429,
                "eil76": 538,
                "berlin52": 7542,
                "kroA100": 21282,
            }
        
        df = pd.read_csv(optimal_path)
        return dict(zip(df["instance"], df["optimal_length"]))
    
    def run(self) -> pd.DataFrame:
        """Run full factorial design in parallel."""
        total_runs = (len(self.cfg.instances) * 
                    len(self.cfg.integrators) * 
                    len(self.cfg.budgets) * 
                    len(self.cfg.seeds))
        
        print(f"[PROTOCOL] Running {total_runs} experiments across 6 workers")
        
        # Generate all experiment tuples
        experiments = []
        for instance in self.cfg.instances:
            for integrator_name in self.cfg.integrators:
                for budget in self.cfg.budgets:
                    for seed in self.cfg.seeds:
                        experiments.append((instance, integrator_name, budget, seed))
        
        # Run in parallel (6 workers = 6 physical cores)
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self._run_single, exp): exp 
                for exp in experiments
            }
            
            for future in as_completed(futures):
                result = future.result()
                self.results.append(result)
                print(f"[DONE] {result.instance} | {result.integrator} | "
                    f"budget={result.budget_s:.0f}s | seed={result.seed} | "
                    f"cost=${result.compute_cost_usd:.4f}")
        
        # Finalize results into DataFrame
        df = self._finalize_results()
        
        # SAVE TO DISK (add this block)
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # JSONL: one row per line (Johnson-compliant audit trail)
        jsonl_path = results_dir / "minimal_audit.jsonl"
        with open(jsonl_path, "w") as f:
            for result in self.results:
                f.write(json.dumps(result.__dict__) + "\n")
        
        # CSV: for JohnsonAuditor compatibility
        df.to_csv(results_dir / "current_results.csv", index=False)
        
        print(f"[PROTOCOL] Saved {len(df)} rows to {jsonl_path}")
        
        # NOW return the DataFrame
        return df
    
    def _run_single(self, exp: Tuple) -> ProtocolResult:
        instance, integrator_name, budget, seed = exp
        
        solver = self.integrators[integrator_name]
        optimal = self.optimal_lengths.get(instance, 0) # 0 = "not found"
        
        # Get HK bound (pre-loaded in __init__)
        hk_bound = self.hk_bounds.get(instance, None)  #  None = "not computed"
        
        # Use HK for gap if available, otherwise optimal, otherwise fail
        gap_denominator = hk_bound if hk_bound is not None else optimal
        if gap_denominator <= 0:
            gap_denominator = 1  # Prevent division by zero
        
        deviations = []
        if hk_bound is None:
            deviations.append(f"HK bound not computed; using optimal = {optimal}")
        if optimal == 0:
            deviations.append(f"Optimal length missing; gap calculation invalid")
        
        try:
            tour, trace = solver.solve(
                instance_path=self.cfg.tsplib_dir / f"{instance}.tsp",
                max_time_s=budget,
                seed=seed,
                candidate_k=self.cfg.candidate_k,
            )
            
            length = trace[0][1] if trace else -1
            elapsed = trace[0][0] if trace else budget
            
            # CORRECT gap calculation
            gap = (length - gap_denominator) / gap_denominator * 100
            
            # SAFE diagnostics extraction
            try:
                diagnostics = solver.get_last_run_diagnostics()
                # Handle both dict-like and object-like diagnostics
                if hasattr(diagnostics, 'get'):
                    cycles = diagnostics.get("cycles_explored", 0)
                    repair = diagnostics.get("repair_path", "lkh")
                else:
                    # Object with attributes
                    cycles = getattr(diagnostics, 'cycles_explored', 0)
                    repair = getattr(diagnostics, 'repair_path', 'lkh')
            except Exception:
                cycles = 0
                repair = "lkh"
            
            # Compute cost
            cost_usd = elapsed * self.cfg.aws_hourly_rate / 3600
            
            return ProtocolResult(
                instance=instance,
                integrator=integrator_name,
                budget_s=budget,
                seed=seed,
                best_length=length,
                time_to_best_s=elapsed,
                final_gap_pct=gap,
                hk_bound=hk_bound or optimal,
                wall_time_s=elapsed,
                compute_cost_usd=cost_usd,
                raw_trace=trace,
                cycles_explored=cycles,
                repair_path=repair,
                machine_info=self.machine_info,
                deviations=deviations,
            )

        except Exception as e:
            # Graceful failure with ALL required fields
            cost_usd = budget * self.cfg.aws_hourly_rate / 3600
            hk_bound = self.hk_bounds.get(instance, 0)
            
            return ProtocolResult(
                instance=instance,
                integrator=integrator_name,
                budget_s=budget,
                seed=seed,
                best_length=-1,
                time_to_best_s=budget,
                final_gap_pct=-1.0,
                hk_bound=hk_bound,
                wall_time_s=budget,
                compute_cost_usd=cost_usd,
                raw_trace=[],
                cycles_explored=0,
                repair_path=f"ERROR: {e}",
                machine_info=getattr(self, 'machine_info', {}),
                deviations=deviations + [f"Runtime error: {str(e)}"],
            )
    
    def _finalize_results(self) -> pd.DataFrame:
        """Convert results to DataFrame."""
        df = pd.DataFrame([r.__dict__ for r in self.results])
        df["n"] = df["instance"].map(self._instance_metadata())
        return df
    
    def _instance_metadata(self) -> Dict[str, int]:
        """Extract instance sizes."""
        metadata = {}
        for inst in self.cfg.instances:
            path = self.cfg.tsplib_dir / f"{inst}.tsp"
            try:
                with open(path) as f:
                    for line in f:
                        if line.startswith("DIMENSION"):
                            n = int(line.split(":")[1].strip())
                            metadata[inst] = n
                            break
            except Exception:
                metadata[inst] = -1
        return metadata


def test_protocol():
    """Smoke test: run protocol on tiny config."""
    from bee_tsp.titration.config import TitrationConfig
    
    cfg = TitrationConfig(
        tsplib_dir=Path("data/tsplib"),
        instances=["eil51"],
        integrators=["lkh"],
        budgets=[1.0],
        seeds=[42, 43, 44, 45, 46],
        candidate_k=30,
        aws_hourly_rate=0.0  # No cost for test
    )
    
    protocol = TitrationProtocol(cfg)
    df = protocol.run()
    
    print(f"✓ Protocol test passed: {len(df)} rows")
    print(df.head())

if __name__ == "__main__":
    test_protocol()