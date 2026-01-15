"""Генерация базового плана для сборки."""

from __future__ import annotations

from typing import Dict

from .models import EdgeIR, PlanIR, StepIR


def _build_linear_edges(step_ids: list[str]) -> list[EdgeIR]:
    """Создает линейные ребра по порядку шагов."""

    return [
        EdgeIR(source=step_ids[index], target=step_ids[index + 1])
        for index in range(len(step_ids) - 1)
    ]


def generate_plan(config: Dict[str, object]) -> PlanIR:
    """Генерирует базовый Plan IR с линейным списком шагов.

    Шаги идут строго в порядке:
    WorkspaceInit → WriteMO2Profile → RunLOOT → Checkpoint → Report.
    """

    steps = [
        StepIR(step_id="workspace_init", step_type="WorkspaceInit", label="Подготовить рабочее окружение"),
        StepIR(step_id="write_mo2_profile", step_type="WriteMO2Profile", label="Записать профиль MO2"),
        StepIR(step_id="run_loot", step_type="RunLOOT", label="Запустить LOOT"),
        StepIR(step_id="checkpoint", step_type="Checkpoint", label="Сделать контрольную точку"),
        StepIR(step_id="report", step_type="Report", label="Сформировать отчет"),
    ]
    step_ids = [step.step_id for step in steps]
    edges = _build_linear_edges(step_ids)
    meta = {
        "version": "1.0",
        "generator": "modbs.generate_plan",
        "config": config,
    }
    return PlanIR(meta=meta, steps=steps, edges=edges)
