"""Интеграционные тесты для CLI сценариев."""

from pathlib import Path

from modbs.cli import cmd_apply, cmd_init, cmd_plan, cmd_report
from modbs.storage import read_json, write_json


def _write_config(root_path: Path) -> Path:
    """Создает минимальный JSON-конфиг для CLI."""

    config_path = root_path / "config.json"
    config_payload = {
        "profile_name": "MVP",
        "paths": {
            "root": str(root_path),
            "mo2": str(root_path / "mo2"),
            "skyrim": str(root_path / "skyrim"),
        },
        "loot": {"mode": "mock"},
    }

    write_json(config_path, config_payload)
    return config_path


def test_cli_init_creates_workspace_structure(tmp_path: Path) -> None:
    """Проверяем, что init создает базовую структуру каталогов."""

    cmd_init(tmp_path)

    assert (tmp_path / "workspace").exists()
    assert (tmp_path / "state").exists()
    assert (tmp_path / "cache").exists()
    assert (tmp_path / "rootstate").exists()


def test_cli_plan_creates_plan_ir(tmp_path: Path) -> None:
    """Проверяем, что plan создает plan.ir.json в state/."""

    config_path = _write_config(tmp_path)

    plan_path = cmd_plan(config_path)

    assert plan_path.exists()
    payload = read_json(plan_path)
    assert payload["steps"], "Ожидали список шагов в Plan IR"


def test_cli_apply_creates_state_artifacts(tmp_path: Path) -> None:
    """Проверяем, что apply создает state-артефакты и журнал."""

    config_path = _write_config(tmp_path)
    cmd_plan(config_path)

    result = cmd_apply(tmp_path, config_path)

    assert result.status == "Succeeded"
    assert (tmp_path / "state" / "job.journal.jsonl").exists()
    assert (tmp_path / "state" / "lockfile.json").exists()
    assert (tmp_path / "state" / "provenance.json").exists()
    assert (tmp_path / "state" / "report.md").exists()


def test_report_contains_step_statuses(tmp_path: Path) -> None:
    """Проверяем, что report содержит статусы шагов."""

    config_path = _write_config(tmp_path)
    cmd_plan(config_path)
    cmd_apply(tmp_path, config_path)

    report_path = cmd_report(tmp_path)

    content = report_path.read_text(encoding="utf-8")
    assert "- workspace_init: Succeeded" in content
    assert "- write_mo2_profile: Succeeded" in content
    assert "- run_loot: Succeeded" in content
    assert "- checkpoint: Succeeded" in content
    assert "- report: Succeeded" in content
