"""Тесты для детерминированного исполнителя."""

from modbs.executor import ALLOWED_STEP_TYPES, execute
from modbs.models import PlanIR, StepIR


def test_executor_runs_steps_in_order() -> None:
    """Проверяем, что шаги выполняются строго по порядку."""

    steps = [
        StepIR(step_id="s1", step_type="WorkspaceInit", label="Init"),
        StepIR(step_id="s2", step_type="WriteMO2Profile", label="Profile"),
        StepIR(step_id="s3", step_type="RunLOOT", label="Loot"),
    ]
    plan = PlanIR(meta={}, steps=steps, edges=[])

    call_order: list[str] = []

    def make_handler() -> callable:
        def _handler(step: StepIR, ctx: dict) -> None:
            call_order.append(step.step_id)

        return _handler

    handlers = {step_type: make_handler() for step_type in ALLOWED_STEP_TYPES}

    result = execute(plan, {"handlers": handlers})

    assert result.status == "Succeeded"
    assert call_order == [step.step_id for step in steps]


def test_executor_blocks_unknown_step_type() -> None:
    """Проверяем, что неизвестный тип шага блокирует выполнение."""

    steps = [
        StepIR(step_id="s1", step_type="WorkspaceInit", label="Init"),
        StepIR(step_id="s2", step_type="UnknownStep", label="???"),
        StepIR(step_id="s3", step_type="Report", label="Report"),
    ]
    plan = PlanIR(meta={}, steps=steps, edges=[])

    call_order: list[str] = []

    def handler(step: StepIR, ctx: dict) -> None:
        call_order.append(step.step_id)

    handlers = {"WorkspaceInit": handler, "Report": handler}

    result = execute(plan, {"handlers": handlers})

    assert result.status == "Blocked"
    assert result.blocked_step_id == "s2"
    assert call_order == ["s1"]
