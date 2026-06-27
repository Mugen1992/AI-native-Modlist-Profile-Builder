"""Тесты для вспомогательных функций хранения."""

import json

from modbs.storage import append_jsonl, read_json, write_json


def test_storage_json_roundtrip(tmp_path) -> None:
    """Проверяем, что JSON сохраняется и читается без потерь."""

    path = tmp_path / "payload.json"
    payload = {"name": "test", "items": [1, 2], "meta": {"lang": "ru"}}

    write_json(path, payload)

    restored = read_json(path)

    assert restored == payload


def test_append_jsonl(tmp_path) -> None:
    """Проверяем, что append_jsonl корректно добавляет объекты в файл."""
    path = tmp_path / "test.jsonl"

    append_jsonl(path, {"id": 1, "val": "A"})
    append_jsonl(path, {"id": 2, "val": "B"})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"id": 1, "val": "A"}
    assert json.loads(lines[1]) == {"id": 2, "val": "B"}
