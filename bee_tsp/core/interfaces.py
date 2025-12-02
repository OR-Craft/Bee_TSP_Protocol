#!/usr/bin/env python3
"""
Abstract base classes for all integrators and tours.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from pathlib import Path

from bee_tsp.core.distance import Distance


class Tour(List[int]):
    """Validated tour permutation."""
    
    def __init__(self, data: List[int]):
        if not self._is_valid(data):
            raise ValueError(f"Invalid tour permutation: must be 0..n-1, got {data}")
        super().__init__(data)
    
    @staticmethod
    def _is_valid(tour: List[int]) -> bool:
        n = len(tour)
        return len(set(tour)) == n and min(tour) == 0 and max(tour) == n - 1


class Integrator(ABC):
    """All recombination operators implement this uniform interface."""
    
    @abstractmethod
    def solve(
        self,
        instance_path: Path,
        max_time_s: float,
        seed: int,
        candidate_k: int,
    ) -> Tuple[Tour, List[Tuple[float, int]]]:
        """
        Args:
            instance_path: Path to TSPLIB .tsp file
            max_time_s: Hard time budget in seconds
            seed: Random seed for reproducibility
            candidate_k: Candidate graph size (ignored by some solvers)
        Returns:
            A valid Tour and runtime trace (elapsed_s, length)
        """
        pass
    
    @abstractmethod
    def get_last_run_diagnostics(self) -> dict:
        """Return debug info: backend, version, time_limit_reached, etc."""
        pass