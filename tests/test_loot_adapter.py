"""Тесты адаптера LOOT."""

from pathlib import Path

from modbs.adapters.loot import run
from modbs.storage import read_json


def test_loot_mock_mode_fallback(tmp_path: Path) -> None:
    """Проверяем fallback на paths.root и запись mock-результата."""

    ctx = {"paths": {"root": tmp_path}}

    result = run("mock", ctx)

    result_path = tmp_path / "state" / "loot.mock.json"

    assert result.status == "Succeeded"
    assert result.output_path == str(result_path)
    assert result_path.exists()

    payload = read_json(result_path)
    assert payload["mode"] == "mock"
    assert payload["status"] == "Succeeded"


def test_loot_blocked_when_no_binary(tmp_path: Path) -> None:
    """Проверяем, что при blocked возвращается причина отсутствия бинаря."""

    ctx = {"root_path": tmp_path}

    result = run("blocked", ctx)

    assert result.status == "Blocked"
    assert "нет бинаря/путей" in result.message
