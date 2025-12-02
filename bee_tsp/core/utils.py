# In bee_tsp/core/utils.py
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

def parse_tsplib_coords(path: Path) -> List[tuple[float, float]]:
    """Minimal TSPLIB parser."""
    coords = []
    in_section = False
        
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line == "NODE_COORD_SECTION":
                in_section = True
                continue
            if line == "EOF":
                break
            if in_section:
                parts = line.split()
                if len(parts) >= 3:
                    coords.append((float(parts[1]), float(parts[2])))
        
    return coords

@dataclass(frozen=True)
class ERDiagnostics:
    """Immutable record of run metadata."""
    backend: str = "edge_rand"
    version: str = "1.0"
    exit_code: int = 0
    time_limit_reached: bool = False
    runs_completed: int = 1
    trace: List[Tuple[float, int]] = None

    def __post_init__(self):
        # Need to handle mutable default for trace
        if self.trace is None:
            object.__setattr__(self, 'trace', [])