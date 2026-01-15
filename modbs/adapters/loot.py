"""Адаптер LOOT: mock/blocked режимы."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from modbs.storage import write_json


@dataclass(frozen=True)
class LootResult:
    """Результат выполнения LOOT."""

    status: str
    message: str
    output_path: str | None = None


def _resolve_root_path(ctx: Mapping[str, Any]) -> Path:
    """Возвращает корневой путь из контекста выполнения."""

    if "root_path" in ctx:
        return Path(ctx["root_path"])

    paths = ctx.get("paths", {})
    root = paths.get("root") if isinstance(paths, Mapping) else None
    if root:
        return Path(root)

    raise ValueError("Не задан корневой путь для LOOT")


def _run_mock(ctx: Mapping[str, Any]) -> LootResult:
    """Записывает фиктивный результат LOOT в state/."""

    root_path = _resolve_root_path(ctx)
    state_dir = root_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    result_path = state_dir / "loot.mock.json"

    # Фиктивный результат должен быть детерминированным для тестов.
    payload = {
        "mode": "mock",
        "status": "Succeeded",
        "summary": "LOOT mock result",
    }

    write_json(result_path, payload)

    return LootResult(
        status="Succeeded",
        message="LOOT mock результат сохранен.",
        output_path=str(result_path),
    )


def _run_blocked() -> LootResult:
    """Возвращает блокирующий статус при отсутствии бинаря/путей."""

    return LootResult(
        status="Blocked",
        message="LOOT недоступен: нет бинаря/путей.",
    )


def run(mode: str, ctx: Mapping[str, Any]) -> LootResult:
    """Запускает LOOT в заданном режиме."""

    if mode == "mock":
        return _run_mock(ctx)
    if mode == "blocked":
        return _run_blocked()

    raise ValueError(f"Неизвестный режим LOOT: {mode}")
