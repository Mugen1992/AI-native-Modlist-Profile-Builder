"""Генерация отчета report.md на основе journal + lockfile."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .storage import read_json, write_text


def _load_journal(path: Path) -> List[Dict[str, Any]]:
    """Считывает события из JSONL-журнала в виде списка словарей."""

    if not path.exists():
        return []

    events: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events


def _summarize_events(
    events: List[Dict[str, Any]],
) -> Tuple[List[str], Dict[str, Dict[str, str]], Dict[str, int]]:
    """Формирует сводку по финальным статусам шагов."""

    step_order: List[str] = []
    step_statuses: Dict[str, Dict[str, str]] = {}

    for event in events:
        step_id = str(event.get("step_id", "unknown"))
        if step_id not in step_statuses:
            step_order.append(step_id)
        step_statuses[step_id] = {
            "status": str(event.get("status", "Unknown")),
            "message": str(event.get("message", "")),
        }

    counts = {"Succeeded": 0, "Failed": 0, "Blocked": 0, "Running": 0, "Unknown": 0}
    for info in step_statuses.values():
        status = info.get("status", "Unknown")
        if status not in counts:
            counts["Unknown"] += 1
            continue
        counts[status] += 1

    return step_order, step_statuses, counts


def _collect_outputs(lockfile_payload: Dict[str, Any]) -> List[str]:
    """Извлекает список outputs из lockfile и дополняет обязательным report.md."""

    outputs: List[str] = []
    artifacts = lockfile_payload.get("artifacts", [])
    if isinstance(artifacts, list):
        for artifact in artifacts:
            path = artifact.get("path") if isinstance(artifact, dict) else None
            if isinstance(path, str):
                outputs.append(path)

    if "state/report.md" not in outputs:
        outputs.append("state/report.md")

    # Удаляем дубликаты, сохраняя порядок.
    seen = set()
    unique_outputs = []
    for path in outputs:
        if path in seen:
            continue
        seen.add(path)
        unique_outputs.append(path)

    return unique_outputs


def generate_report(root_path: Path) -> str:
    """Генерирует report.md в state/ на основе журнала и lockfile."""

    state_dir = root_path / "state"
    journal_path = state_dir / "job.journal.jsonl"
    lockfile_path = state_dir / "lockfile.json"
    report_path = state_dir / "report.md"

    events = _load_journal(journal_path)
    step_order, step_statuses, counts = _summarize_events(events)

    lockfile_payload: Dict[str, Any] = {}
    if lockfile_path.exists():
        lockfile_payload = read_json(lockfile_path)

    outputs = _collect_outputs(lockfile_payload)

    summary_lines = [
        "# Report",
        "",
        "## Summary",
        f"- Steps: {len(step_statuses)}",
        f"- Succeeded: {counts['Succeeded']}",
        f"- Failed: {counts['Failed']}",
        f"- Blocked: {counts['Blocked']}",
        f"- Running: {counts['Running']}",
        "",
        "### Step Statuses",
    ]

    for step_id in step_order:
        info = step_statuses[step_id]
        status = info.get("status", "Unknown")
        message = info.get("message", "").strip()
        detail = f" — {message}" if message else ""
        summary_lines.append(f"- {step_id}: {status}{detail}")

    outputs_lines = ["", "## Outputs"] + [f"- {path}" for path in outputs]

    reproduce_lines = [
        "",
        "## Reproduce",
        "- modbs init <path>",
        "- modbs plan --config <config.yaml>",
        "- modbs apply",
        "- modbs report",
    ]

    report_text = "\n".join(summary_lines + outputs_lines + reproduce_lines) + "\n"
    write_text(report_path, report_text)
    return report_text
