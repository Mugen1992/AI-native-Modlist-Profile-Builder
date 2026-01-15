"""Тесты для шагов WorkspaceInit и WriteMO2Profile."""

from pathlib import Path

from modbs.models import StepIR
from modbs.steps.workspace_init import workspace_init
from modbs.steps.write_mo2_profile import write_mo2_profile


def _assert_dirs_exist(root: Path, names: list[str]) -> None:
    """Проверяет, что директории существуют и являются каталогами."""

    for name in names:
        target = root / name
        assert target.exists()
        assert target.is_dir()


def test_workspace_init_creates_required_directories(tmp_path: Path) -> None:
    """Проверяем, что WorkspaceInit создаёт структуру каталогов."""

    step = StepIR(step_id="s1", step_type="WorkspaceInit", label="Init")

    workspace_init(step, {"root_path": tmp_path})

    _assert_dirs_exist(tmp_path, ["workspace", "state", "cache", "rootstate"])


def test_write_mo2_profile_creates_modlist(tmp_path: Path) -> None:
    """Проверяем, что WriteMO2Profile создаёт modlist.txt."""

    step = StepIR(
        step_id="s2",
        step_type="WriteMO2Profile",
        label="Write",
        payload={"profile": "Default"},
    )

    write_mo2_profile(step, {"root_path": tmp_path})

    modlist_path = tmp_path / "workspace" / "profiles" / "Default" / "modlist.txt"
    assert modlist_path.exists()
    assert modlist_path.is_file()


def test_steps_integration_creates_workspace_and_profile(tmp_path: Path) -> None:
    """Интеграционный тест: шаги создают директории и профиль."""

    init_step = StepIR(step_id="s1", step_type="WorkspaceInit", label="Init")
    profile_step = StepIR(
        step_id="s2",
        step_type="WriteMO2Profile",
        label="Write",
        payload={"profile": "MVP"},
    )

    ctx = {"root_path": tmp_path}

    workspace_init(init_step, ctx)
    write_mo2_profile(profile_step, ctx)

    _assert_dirs_exist(tmp_path, ["workspace", "state", "cache", "rootstate"])
    modlist_path = tmp_path / "workspace" / "profiles" / "MVP" / "modlist.txt"
    assert modlist_path.exists()
