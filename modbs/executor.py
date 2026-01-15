"""Детерминированный исполнитель Plan IR с allowlist шагов."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .models import PlanIR, StepIR

StepHandler = Callable[[StepIR, Dict[str, Any]], None]

ALLOWED_STEP_TYPES = {
    "WorkspaceInit",
    "WriteMO2Profile",
    "RunLOOT",
    "Checkpoint",
    "Report",
}


class StepBlockedError(RuntimeError):
    """Ошибка для остановки шага со статусом Blocked."""


@dataclass(frozen=True)
class ExecutionResult:
    """Результат выполнения плана."""

    status: str
    executed_step_ids: List[str] = field(default_factory=list)
    blocked_step_id: Optional[str] = None
    failed_step_id: Optional[str] = None
    message: str = ""


def _resolve_handler(step: StepIR, handlers: Dict[str, StepHandler]) -> StepHandler:
    """Возвращает обработчик шага или выбрасывает ошибку."""

    handler = handlers.get(step.step_type)
    if handler is None:
        raise ValueError(f"Не найден обработчик для типа шага: {step.step_type}")
    return handler


def execute(plan: PlanIR, ctx: Dict[str, Any]) -> ExecutionResult:
    """Исполняет шаги плана по порядку и останавливается при ошибке.

    Поддерживаются только типы шагов из allowlist.
    """

    handlers = ctx.get("handlers", {})
    executed_step_ids: List[str] = []

    for step in plan.steps:
        if step.step_type not in ALLOWED_STEP_TYPES:
            return ExecutionResult(
                status="Blocked",
                executed_step_ids=executed_step_ids,
                blocked_step_id=step.step_id,
                message=f"Неизвестный тип шага: {step.step_type}",
            )

        try:
            handler = _resolve_handler(step, handlers)
            handler(step, ctx)
        except StepBlockedError as exc:
            return ExecutionResult(
                status="Blocked",
                executed_step_ids=executed_step_ids,
                blocked_step_id=step.step_id,
                message=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            return ExecutionResult(
                status="Failed",
                executed_step_ids=executed_step_ids,
                failed_step_id=step.step_id,
                message=str(exc),
            )

        executed_step_ids.append(step.step_id)

    return ExecutionResult(status="Succeeded", executed_step_ids=executed_step_ids)
