"""Тесты для вспомогательных функций хранения."""

import json

from modbs.journal import append_event
from modbs.storage import append_jsonl, read_json, write_json


def test_storage_json_roundtrip(tmp_path) -> None:
    """Проверяем, что JSON сохраняется и читается без потерь."""

    path = tmp_path / "payload.json"
    payload = {"name": "test", "items": [1, 2], "meta": {"lang": "ru"}}

    write_json(path, payload)

    restored = read_json(path)

    assert restored == payload


def test_journal_append_only(tmp_path, monkeypatch) -> None:
    """Проверяем, что Job Journal добавляет строки, а не перезаписывает файл."""

    path = tmp_path / "journal.jsonl"
    monkeypatch.setattr("modbs.journal.JOURNAL_PATH", path)

    append_event(
        ts="2024-01-01T00:00:00Z",
        step_id="s1",
        status="Running",
        message="Старт",
        metrics={"ms": 1},
    )
    append_event(
        ts="2024-01-01T00:00:01Z",
        step_id="s1",
        status="Succeeded",
        message="Готово",
        metrics={"ms": 2},
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    restored = [json.loads(line) for line in lines]

    assert restored == [
        {
            "ts": "2024-01-01T00:00:00Z",
            "step_id": "s1",
            "status": "Running",
            "message": "Старт",
            "metrics": {"ms": 1},
        },
        {
            "ts": "2024-01-01T00:00:01Z",
            "step_id": "s1",
            "status": "Succeeded",
            "message": "Готово",
            "metrics": {"ms": 2},
        },
    ]


def test_journal_rejects_invalid_status(tmp_path, monkeypatch) -> None:
    """Проверяем, что Job Journal отклоняет недопустимый статус."""

    path = tmp_path / "journal.jsonl"
    monkeypatch.setattr("modbs.journal.JOURNAL_PATH", path)

    try:
        append_event(
            ts="2024-01-01T00:00:00Z",
            step_id="s1",
            status="Unknown",
            message="Ошибка статуса",
            metrics=None,
        )
    except ValueError as exc:
        assert "Недопустимый статус" in str(exc)
    else:
        raise AssertionError("Ожидали ValueError для недопустимого статуса")
