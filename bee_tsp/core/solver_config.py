#!/usr/bin/env python3
"""
Configuration classes for solver parameters.
"""

from pydantic import BaseModel, Field
from typing import Literal, List
from pathlib import Path


class RepairConfig(BaseModel):
    """Unified repair budget for ALL integrators."""
    time_ms: int = Field(ge=50, le=1000)
    popmusic_cap_per_node: int = 8
    fallback_to_2opt: bool = True


class IntegratorConfig(BaseModel):
    """Common parameters every integrator must respect."""
    name: Literal["eax", "ucr", "edge_rand", "popmusic", "lkh"]
    parents_per_round: int = Field(ge=2, le=12)
    offspring_per_round: int = Field(ge=1, le=5)
    repair: RepairConfig


class SolverConfig(BaseModel):
    """Single source of truth for experiments."""
    instance_path: Path
    integrator: IntegratorConfig
    wall_time_s: float
    seeds: List[int] = Field(min_length=30)