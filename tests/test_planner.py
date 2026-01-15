"""Тесты для планировщика и Plan IR."""

from modbs.planner import generate_plan
from modbs.storage import plan_ir_from_dict, plan_ir_to_dict


def test_planner_generates_valid_plan_structure() -> None:
    """Проверяем структуру плана и порядок шагов."""

    plan = generate_plan({"profile": "default"})

    assert [step.step_type for step in plan.steps] == [
        "WorkspaceInit",
        "WriteMO2Profile",
        "RunLOOT",
        "Checkpoint",
        "Report",
    ]
    assert len(plan.edges) == len(plan.steps) - 1
    assert plan.edges[0].source == plan.steps[0].step_id
    assert plan.edges[-1].target == plan.steps[-1].step_id


def test_plan_ir_serialization_roundtrip() -> None:
    """Проверяем, что сериализация и десериализация сохраняют данные."""

    plan = generate_plan({"profile": "default"})
    payload = plan_ir_to_dict(plan)
    restored = plan_ir_from_dict(payload)

    assert restored == plan
