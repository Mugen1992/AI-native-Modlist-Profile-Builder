"""Тесты для lockfile и provenance."""

from pathlib import Path

from modbs.adapters.loot import run as run_loot
from modbs.models import StepIR
from modbs.state import write_state_artifacts
from modbs.steps.workspace_init import workspace_init
from modbs.steps.write_mo2_profile import write_mo2_profile
from modbs.storage import read_json


def _prepare_outputs(root_path: Path, profile_name: str = "MVP") -> None:
    """Создает минимальные outputs для snapshot."""

    init_step = StepIR(step_id="s1", step_type="WorkspaceInit", label="Init")
    profile_step = StepIR(
        step_id="s2",
        step_type="WriteMO2Profile",
        label="Write",
        payload={"profile": profile_name},
    )

    ctx = {"root_path": root_path}

    workspace_init(init_step, ctx)
    write_mo2_profile(profile_step, ctx)
    run_loot("mock", ctx)


def test_lockfile_contains_hashes(tmp_path: Path) -> None:
    """Проверяем, что lockfile содержит sha256-хэши."""

    _prepare_outputs(tmp_path)

    write_state_artifacts(tmp_path, release_id="test-run")

    lockfile_path = tmp_path / "state" / "lockfile.json"
    lockfile = read_json(lockfile_path)
    artifacts = lockfile.get("artifacts", [])

    assert artifacts, "Ожидали хотя бы один артефакт в lockfile"
    assert any(item["path"].endswith("modlist.txt") for item in artifacts)

    for item in artifacts:
        hash_value = item.get("hash", "")
        assert hash_value.startswith("sha256:")
        assert len(hash_value) > len("sha256:")


def test_provenance_contains_all_outputs(tmp_path: Path) -> None:
    """Проверяем, что provenance содержит все выходные файлы."""

    _prepare_outputs(tmp_path)

    write_state_artifacts(tmp_path, release_id="test-run")

    provenance_path = tmp_path / "state" / "provenance.json"
    provenance = read_json(provenance_path)
    artifact_paths = {item["path"] for item in provenance.get("artifacts", [])}

    expected_paths = {
        "workspace/profiles/MVP/modlist.txt",
        "state/loot.mock.json",
    }

    assert expected_paths.issubset(artifact_paths)
