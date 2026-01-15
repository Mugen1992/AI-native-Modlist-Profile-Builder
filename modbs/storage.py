"""Сериализация и десериализация Plan IR."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict

from .models import EdgeIR, PlanIR, StepIR


def plan_ir_to_dict(plan: PlanIR) -> Dict[str, Any]:
    """Преобразует Plan IR в словарь для хранения."""

    return asdict(plan)


def plan_ir_from_dict(data: Dict[str, Any]) -> PlanIR:
    """Восстанавливает Plan IR из словаря."""

    steps = [StepIR(**step) for step in data.get("steps", [])]
    edges = [EdgeIR(**edge) for edge in data.get("edges", [])]
    meta = data.get("meta", {})
    return PlanIR(meta=meta, steps=steps, edges=edges)


def save_plan_ir(plan: PlanIR, path: str) -> None:
    """Сохраняет Plan IR в файл JSON."""

    with open(path, "w", encoding="utf-8") as handle:
        json.dump(plan_ir_to_dict(plan), handle, ensure_ascii=False, indent=2)


def load_plan_ir(path: str) -> PlanIR:
    """Загружает Plan IR из файла JSON."""

    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return plan_ir_from_dict(data)
