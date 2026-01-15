"""Шаг WorkspaceInit: подготовка структуры каталогов."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from modbs.models import StepIR


def _resolve_root_path(ctx: Mapping[str, Any]) -> Path:
    """Возвращает корневой путь из контекста выполнения."""

    if "root_path" in ctx:
        return Path(ctx["root_path"])

    paths = ctx.get("paths", {})
    root = paths.get("root") if isinstance(paths, Mapping) else None
    if root:
        return Path(root)

    raise ValueError("Не задан корневой путь для WorkspaceInit")


def workspace_init(step: StepIR, ctx: Mapping[str, Any]) -> None:
    """Создаёт базовые каталоги рабочего окружения.

    Создаются директории: workspace/, state/, cache/, rootstate/.
    """

    root_path = _resolve_root_path(ctx)

    # Список обязательных директорий из спецификации шага.
    required_dirs = ["workspace", "state", "cache", "rootstate"]

    for dir_name in required_dirs:
        target = root_path / dir_name
        target.mkdir(parents=True, exist_ok=True)
