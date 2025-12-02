#!/usr/bin/env python3
"""
Edge-Rand Integrator: Pure random recombination (baseline).
Generates random tours for comparison with LKH.
"""

from __future__ import annotations
import time
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np

from bee_tsp.core.interfaces import Integrator, Tour
from bee_tsp.core.distance import Distance
from bee_tsp.core.solver_config import RepairConfig
from bee_tsp.core.utils import parse_tsplib_coords, ERDiagnostics

class EdgeRandIntegrator(Integrator):
    """
    Edge-Rand: Simple random tour generator.
    Used as a baseline to show when sophisticated integrators matter.
    """
    
    def __init__(self, repair_cfg: RepairConfig):
        self.repair_cfg = repair_cfg
        self._last_diagnostics: ERDiagnostics | None = None
        print(f"[EdgeRand] Initialised")
    
    def solve(
        self, 
        instance_path: Path,
        max_time_s: float,
        seed: int,
        candidate_k: int,
    ) -> Tuple[Tour, List[Tuple[float, int]]]:
        """
        Generate a random tour.
        """
        start = time.monotonic()
        
        # Load coordinates to get n cities
        coords = parse_tsplib_coords(instance_path)
        n = len(coords)

        print(f"File: {instance_path.name}")
        print(f"Cities: {n}")
        print(f"Coordinate range: X({min(c[0] for c in coords):.0f}-{max(c[0] for c in coords):.0f}) Y({min(c[1] for c in coords):.0f}-{max(c[1] for c in coords):.0f})")
        
        # Generate random tour
        rng = random.Random(seed)
        tour = list(range(n))
        rng.shuffle(tour)
        
        # Validate
        tour_obj = Tour(tour)
        
        # Compute length
        dist = Distance.from_tsplib_file(instance_path)
        length = dist.tour_length(tour_obj)
        
        elapsed = time.monotonic() - start
        
        # Build trace
        trace = [(elapsed, length)]
        
        # Store diagnostics
        self._last_diagnostics = ERDiagnostics(
            runs_completed=1,
            time_limit_reached=False,
            trace=trace,
        )
        # Debug: Verify tours are actually different
        print(f"DEBUG: Seed {seed}, Tour hash: {hash(tuple(tour_obj[:5]))}, Length: {length}")
        return tour_obj, trace
    
    def get_last_run_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostics."""
        if self._last_diagnostics is None:
            return {"error": "No run completed"}
        
        return {
            "cycles_explored": self._last_diagnostics.runs_completed,
            "repair_path": "EdgeRand",
            "backend": self._last_diagnostics.backend,
            "version": self._last_diagnostics.version,
            "time_limit_reached": self._last_diagnostics.time_limit_reached,
        }
    
def test_edge_rand():
    """Smoke test."""
    from bee_tsp.core.solver_config import RepairConfig
    
    solver = EdgeRandIntegrator(repair_cfg=RepairConfig(time_ms=1000))
    tour, trace = solver.solve(
        instance_path=Path("data/tsplib/eil51.tsp"),
        max_time_s=1.0,
        seed=42,
        candidate_k=30,
    )
    
    print(f"✓ EdgeRand generated tour, length: {len(tour)}")
    print(f"  Tour length: {trace[0][1]} (should be ~1600-1700 random)")
    assert len(tour) == 51


if __name__ == "__main__":
    test_edge_rand()