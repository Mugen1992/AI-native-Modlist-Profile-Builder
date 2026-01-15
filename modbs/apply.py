"""Применение плана и фиксация артефактов состояния."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from .executor import ExecutionResult, execute
from .models import PlanIR
from .state import write_state_artifacts


def _resolve_root_path(ctx: Mapping[str, Any]) -> Path:
    """Возвращает корневой путь из контекста выполнения."""

    if "root_path" in ctx:
        return Path(ctx["root_path"])

    paths = ctx.get("paths", {})
    root = paths.get("root") if isinstance(paths, Mapping) else None
    if root:
        return Path(root)

    raise ValueError("Не задан корневой путь для apply")


def apply_plan(plan: PlanIR, ctx: Dict[str, Any]) -> ExecutionResult:
    """Исполняет план и после этого пишет lockfile/provenance."""

    result = execute(plan, ctx)

    # Даже при частичном выполнении полезно зафиксировать текущие outputs.
    root_path = _resolve_root_path(ctx)
    write_state_artifacts(root_path)

    return result
