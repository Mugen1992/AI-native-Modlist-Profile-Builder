"""Сериализация и десериализация Plan IR."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Union

from .models import EdgeIR, PlanIR, StepIR

PathLike = Union[str, Path]


def _atomic_write_text(path: Path, content: str) -> None:
    """Атомарно записывает текст: временный файл → rename."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def write_json(path: PathLike, payload: Any) -> None:
    """Сохраняет JSON с атомарной записью."""

    target = Path(path)
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    _atomic_write_text(target, content)


def read_json(path: PathLike) -> Any:
    """Считывает JSON из файла."""

    target = Path(path)
    with open(target, "r", encoding="utf-8") as handle:
        return json.load(handle)


def append_jsonl(path: PathLike, payloads: Iterable[Any] | Any) -> None:
    """Добавляет строки JSONL в файл без перезаписи существующих данных."""

    target = Path(path)
    if isinstance(payloads, (list, tuple)):
        items = list(payloads)
    else:
        items = [payloads]

    existing_text = ""
    if target.exists():
        existing_text = target.read_text(encoding="utf-8")

    new_lines = [json.dumps(item, ensure_ascii=False) for item in items]
    append_text = "\n".join(new_lines)

    combined = existing_text
    if combined and not combined.endswith("\n"):
        combined += "\n"
    if append_text:
        combined += append_text + "\n"

    _atomic_write_text(target, combined)


def write_text(path: PathLike, text: str) -> None:
    """Сохраняет текст с атомарной записью."""

    target = Path(path)
    _atomic_write_text(target, text)


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
