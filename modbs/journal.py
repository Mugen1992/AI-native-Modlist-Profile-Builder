"""Работа с Job Journal (append-only JSONL)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .storage import append_jsonl

ALLOWED_STATUSES = {"Running", "Succeeded", "Failed", "Blocked"}
JOURNAL_PATH = Path("state/job.journal.jsonl")


def append_event(
    ts: str,
    step_id: str,
    status: str,
    message: str,
    metrics: Dict[str, Any] | None,
) -> None:
    """Добавляет событие в журнал в режиме append-only."""

    if status not in ALLOWED_STATUSES:
        raise ValueError(
            "Недопустимый статус Journal. "
            "Ожидались: Running, Succeeded, Failed, Blocked."
        )

    payload = {
        "ts": ts,
        "step_id": step_id,
        "status": status,
        "message": message,
        "metrics": metrics or {},
    }

    append_jsonl(JOURNAL_PATH, payload)
