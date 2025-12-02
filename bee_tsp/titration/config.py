#!/usr/bin/env python3
"""
Titration experiment configuration (immutable).
"""

from pydantic import BaseModel, Field
from typing import Literal, List
from pathlib import Path


class DistanceConfig(BaseModel):
    metric_tag: Literal["EUC_2D", "CEIL_2D", "ATT", "GEO"]
    validate_against_tsplib: bool = True


class RepairConfig(BaseModel):
    time_ms: int = Field(ge=50, le=1000)
    popmusic_cap_per_node: int = 8
    fallback_to_2opt: bool = True


class IntegratorConfig(BaseModel):
    name: Literal["eax", "ucr", "edge_rand", "popmusic", "lkh"]
    parents_per_round: int = Field(ge=2, le=12)
    offspring_per_round: int = Field(ge=1, le=5)
    repair: RepairConfig


class TitrationConfig(BaseModel):
    """Master experiment config."""
    tsplib_dir: Path
    instances: List[str]
    integrators: List[Literal["lkh", "eax", "ucr", "edge_rand"]]
    budgets: List[float]
    seeds: List[int] = Field(min_length=5)  # Reduced for laptop
    candidate_k: int = Field(ge=8, le=96)
    aws_hourly_rate: float = 0.34

    @classmethod
    def from_json(cls, path: Path) -> "TitrationConfig":
        """Load from file."""
        import json
        with open(path) as f:
            data = json.load(f)
        return cls(**data)