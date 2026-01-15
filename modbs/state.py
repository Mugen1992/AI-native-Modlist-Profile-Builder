"""Сбор артефактов состояния, вычисление хэшей и запись snapshot-файлов."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .storage import write_json

_LOCKFILE_NAME = "lockfile.json"
_PROVENANCE_NAME = "provenance.json"


def _iter_output_files(root_path: Path, extra_paths: Iterable[Path] | None = None) -> List[Path]:
    """Собирает список файлов-артефактов для snapshot."""

    output_dirs = [root_path / "workspace", root_path / "state"]
    output_files: List[Path] = []
    exclude_paths = {
        f"state/{_LOCKFILE_NAME}",
        f"state/{_PROVENANCE_NAME}",
    }

    for base_dir in output_dirs:
        if not base_dir.exists():
            continue
        for path in base_dir.rglob("*"):
            if not path.is_file():
                continue
            rel_path = path.relative_to(root_path).as_posix()
            if rel_path in exclude_paths:
                continue
            output_files.append(path)

    if extra_paths:
        for path in extra_paths:
            if path.exists() and path.is_file():
                output_files.append(path)

    output_files.sort(key=lambda item: item.relative_to(root_path).as_posix())
    return output_files


def _sha256_file(path: Path) -> str:
    """Вычисляет sha256 для файла и возвращает строку с префиксом."""

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def build_lockfile(root_path: Path, release_id: str = "local-run") -> Dict[str, Any]:
    """Формирует структуру lockfile со списком артефактов и хэшей."""

    artifacts: List[Dict[str, str]] = []
    for path in _iter_output_files(root_path):
        rel_path = path.relative_to(root_path).as_posix()
        artifacts.append(
            {
                "path": rel_path,
                "hash": _sha256_file(path),
            }
        )

    return {
        "meta": {"schema": "modbs.lockfile.v0"},
        "release_id": release_id,
        "artifacts": artifacts,
    }


def build_provenance(root_path: Path) -> Dict[str, Any]:
    """Формирует структуру provenance со списком артефактов."""

    artifacts: List[Dict[str, str]] = []
    for path in _iter_output_files(root_path):
        rel_path = path.relative_to(root_path).as_posix()
        artifacts.append(
            {
                "path": rel_path,
                "class": "Generated",
            }
        )

    return {
        "meta": {"schema": "modbs.provenance.v0"},
        "artifacts": artifacts,
    }


def write_state_artifacts(root_path: Path, release_id: str = "local-run") -> Dict[str, Dict[str, Any]]:
    """Записывает lockfile.json и provenance.json в state/."""

    state_dir = root_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    lockfile_payload = build_lockfile(root_path, release_id=release_id)
    provenance_payload = build_provenance(root_path)

    write_json(state_dir / _LOCKFILE_NAME, lockfile_payload)
    write_json(state_dir / _PROVENANCE_NAME, provenance_payload)

    return {"lockfile": lockfile_payload, "provenance": provenance_payload}
