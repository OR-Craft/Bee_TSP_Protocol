from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path
import math

Coord = Tuple[float, float]

@dataclass(frozen=True)
class Distance:
    metric: str
    coords: Tuple[Coord, ...]
    
    def __post_init__(self):
        if self.metric not in {"EUC_2D", "CEIL_2D", "ATT", "GEO"}:
            raise ValueError(f"Unsupported metric: {self.metric}")
        object.__setattr__(self, 'coords', tuple(self.coords))
        object.__setattr__(self, 'n', len(self.coords))
    
    def _euc(self, i: int, j: int) -> int:
        """EUC_2D: round to nearest integer"""
        x1, y1 = self.coords[i]
        x2, y2 = self.coords[j]
        return int(round(math.hypot(x1 - x2, y1 - y2)))
    
    def _ceil(self, i: int, j: int) -> int:
        """CEIL_2D: ceiling of Euclidean distance"""
        x1, y1 = self.coords[i]
        x2, y2 = self.coords[j]
        return int(math.ceil(math.hypot(x1 - x2, y1 - y2)))
    
    def d(self, i: int, j: int) -> int:
        """Dispatch based on metric"""
        if i == j: 
            return 0
        if self.metric == "CEIL_2D":
            return self._ceil(i, j)
        else:  # Default to EUC_2D
            return self._euc(i, j)
    
    def tour_length(self, tour: List[int]) -> int:
        return sum(self.d(tour[i], tour[(i+1) % self.n]) for i in range(self.n))
    
    @classmethod
    def from_tsplib_file(cls, path: Path):
        """Auto-detect metric from TSPLIB file"""
        metric = "EUC_2D"  # Default
        coords = []
        
        with open(path) as f:
            in_section = False
            for line in f:
                line_upper = line.strip().upper()
                if line_upper.startswith("EDGE_WEIGHT_TYPE"):
                    metric = line.split(":")[1].strip()
                if line_upper == "NODE_COORD_SECTION":
                    in_section = True
                    continue
                if line_upper == "EOF":
                    break
                if in_section:
                    parts = line.split()
                    if len(parts) >= 3:
                        coords.append((float(parts[1]), float(parts[2])))
        
        return cls(metric=metric, coords=coords)