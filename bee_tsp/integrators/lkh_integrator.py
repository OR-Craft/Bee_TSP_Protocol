#!/usr/bin/env python3
"""
LKHIntegrator: Direct LKH binary wrapper.
Handles all edge types and supports full time limits.
"""

from pathlib import Path
from typing import Tuple, List, Optional
import time
import subprocess
import tempfile
import re
from bee_tsp.core.interfaces import Integrator, Tour
from bee_tsp.core.solver_config import RepairConfig
from bee_tsp.core.distance import Distance
from bee_tsp.core.utils import ERDiagnostics

class LKHIntegrator(Integrator):
    """
    Lin-Kernighan Heuristic (LKH) integrator using LKH-3 binary.
    """
    
    def __init__(
        self,
        repair_cfg: RepairConfig,
        lkh_binary: Path = Path("~/bin/LKH").expanduser(),
    ):
        self.repair_cfg = repair_cfg
        self.lkh_binary = lkh_binary
        self._last_diagnostics: Optional[ERDiagnostics] = None
        
        if not self.lkh_binary.exists():
            raise RuntimeError(
                f"LKH binary not found at {self.lkh_binary}\n"
                "Download from: http://webhotel4.ruc.dk/~keld/research/LKH-3/"
            )
        
        print(f"[LKH] Initialised | Binary: {self.lkh_binary}")
    
    def solve(
        self,
        instance_path: Path,
        max_time_s: float,
        seed: int,
        candidate_k: int,
    ) -> Tuple[Tour, List[Tuple[float, int]]]:
        """
        Solve TSP using LKH binary.
        """
        start = time.monotonic()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            par_file = tmpdir / "lkh.par"
            tour_file = tmpdir / "lkh.tour"
            
            # Generate LKH parameter file
            self._write_parameter_file(
                par_file, instance_path, tour_file, max_time_s, seed
            )
            
            # Execute LKH
            try:
                result = subprocess.run(
                    [str(self.lkh_binary), str(par_file)],
                    capture_output=True,
                    text=True,
                    timeout=max_time_s + 10.0  # Grace period
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"LKH failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"LKH timed out after {max_time_s + 10.0}s")
            
            # Parse tour file
            if not tour_file.exists():
                raise RuntimeError("LKH did not produce tour file")
            
            tour_list = self._parse_tour_file(tour_file)
        
        # Validate and compute length
        tour_obj = Tour(tour_list)
        dist = Distance.from_tsplib_file(instance_path)
        length = dist.tour_length(tour_obj)
        
        elapsed = time.monotonic() - start
        trace = [(elapsed, length)]
        
        # Store diagnostics
        self._last_diagnostics = ERDiagnostics(
            runs_completed=1,
            time_limit_reached=False,
            trace=trace,
            backend="lkh",  # Optional: override defaults
            version="3.0.7",
        )
        
        return tour_obj, trace
    
    def _write_parameter_file(
        self,
        par_file: Path,
        instance_path: Path,
        tour_file: Path,
        time_limit: float,
        seed: int,
    ) -> None:
        """Generate LKH parameter file."""
        
        # LKH uses 1..2147483647 for seed
        lkh_seed = abs(seed) % 2147483647 + 1
        
        content = f"""PROBLEM_FILE = {instance_path}
OUTPUT_TOUR_FILE = {tour_file}
RUNS = 1
TIME_LIMIT = {time_limit}
SEED = {lkh_seed}
CANDIDATE_SET_TYPE = POPMUSIC
MAX_CANDIDATES = 8
INITIAL_PERIOD = 100
TRACE_LEVEL = 1
"""
        par_file.write_text(content)
    
    def _parse_tour_file(self, tour_file: Path) -> List[int]:
        """Parse LKH tour file (1-based) → 0-based list."""
        tour = []
        in_section = False
        
        for line in tour_file.read_text().splitlines():
            if line.startswith("TOUR_SECTION"):
                in_section = True
                continue
            if line.startswith("-1"):
                break
            if in_section and line.strip():
                node = int(line.strip()) - 1  # Convert to 0-based
                tour.append(node)
        
        return tour
    
    def _check_time_limit_reached(self, stdout: str) -> bool:
        """Check if LKH hit its time limit."""
        return "Time limit exceeded" in stdout
    
    def get_last_run_diagnostics(self) -> Optional[ERDiagnostics]:
        return self._last_diagnostics