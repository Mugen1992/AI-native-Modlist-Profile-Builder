"""Тесты для генерации report.md."""

from pathlib import Path

from modbs.report import generate_report
from modbs.storage import append_jsonl, write_json


def test_report_contains_summary_and_statuses(tmp_path: Path) -> None:
    """Проверяем, что отчет содержит Summary и статусы шагов."""

    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    journal_path = state_dir / "job.journal.jsonl"
    append_jsonl(
        journal_path,
        [
            {
                "ts": "2024-01-01T00:00:00Z",
                "step_id": "workspace_init",
                "status": "Running",
                "message": "Старт",
                "metrics": {"ms": 1},
            },
            {
                "ts": "2024-01-01T00:00:01Z",
                "step_id": "workspace_init",
                "status": "Succeeded",
                "message": "Готово",
                "metrics": {"ms": 2},
            },
            {
                "ts": "2024-01-01T00:00:02Z",
                "step_id": "run_loot",
                "status": "Blocked",
                "message": "LOOT не найден",
                "metrics": {},
            },
        ],
    )

    lockfile_payload = {
        "meta": {"schema": "modbs.lockfile.v0"},
        "release_id": "test",
        "artifacts": [
            {"path": "state/job.journal.jsonl", "hash": "sha256:test"},
            {"path": "workspace/profiles/MVP/modlist.txt", "hash": "sha256:test2"},
        ],
    }
    write_json(state_dir / "lockfile.json", lockfile_payload)

    generate_report(tmp_path)

    report_path = state_dir / "report.md"
    assert report_path.exists()

    content = report_path.read_text(encoding="utf-8")
    assert "## Summary" in content
    assert "## Outputs" in content
    assert "## Reproduce" in content
    assert "- Succeeded: 1" in content
    assert "- Blocked: 1" in content
    assert "- workspace_init: Succeeded" in content
    assert "- run_loot: Blocked" in content
