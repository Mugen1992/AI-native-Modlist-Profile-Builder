"""Модели Plan IR для планировщика."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class StepIR:
    """Описывает шаг плана."""

    step_id: str
    step_type: str
    label: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EdgeIR:
    """Описывает ребро между шагами."""

    source: str
    target: str


@dataclass(frozen=True)
class PlanIR:
    """Plan IR с метаданными, шагами и ребрами."""

    meta: Dict[str, Any]
    steps: List[StepIR]
    edges: List[EdgeIR]
