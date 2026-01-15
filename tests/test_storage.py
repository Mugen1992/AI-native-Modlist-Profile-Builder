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


def test_journal_append_only(tmp_path) -> None:
    """Проверяем, что JSONL добавляет строки, а не перезаписывает файл."""

    path = tmp_path / "journal.jsonl"

    append_jsonl(path, {"step": 1})
    append_jsonl(path, [{"step": 2}, {"step": 3}])

    lines = path.read_text(encoding="utf-8").splitlines()
    restored = [json.loads(line) for line in lines]

    assert restored == [{"step": 1}, {"step": 2}, {"step": 3}]
