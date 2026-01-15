"""CLI для управления жизненным циклом модульной сборки."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from modbs import generate_plan
from modbs.adapters.loot import run as run_loot
from modbs.apply import apply_plan
from modbs.executor import ExecutionResult, StepBlockedError
from modbs import journal
from modbs.journal import append_event
from modbs.models import PlanIR, StepIR
from modbs.report import generate_report
from modbs.state import write_state_artifacts
from modbs.storage import load_plan_ir, plan_ir_to_dict, read_json, write_json
from modbs.steps.workspace_init import workspace_init
from modbs.steps.write_mo2_profile import write_mo2_profile


def _read_config(path: Path) -> Dict[str, Any]:
    """Считывает JSON-конфиг и возвращает его как словарь."""

    if not path.exists():
        raise FileNotFoundError(f"Не найден файл конфигурации: {path}")

    try:
        return read_json(path)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Некорректный JSON-конфиг: {path}") from exc


def _resolve_root_path(config: Mapping[str, Any]) -> Path:
    """Определяет корневую директорию из конфига."""

    paths = config.get("paths", {})
    root = paths.get("root") if isinstance(paths, Mapping) else None
    if root:
        return Path(root)
    raise ValueError("В конфиге не задан paths.root")


def _resolve_profile_name(config: Mapping[str, Any]) -> str:
    """Определяет имя профиля из конфига."""

    profile_name = config.get("profile_name")
    if profile_name:
        return str(profile_name)
    raise ValueError("В конфиге не задан profile_name")


def _resolve_loot_mode(config: Mapping[str, Any]) -> str:
    """Определяет режим LOOT из конфига."""

    loot = config.get("loot", {})
    mode = loot.get("mode") if isinstance(loot, Mapping) else None
    if mode:
        return str(mode)
    raise ValueError("В конфиге не задан loot.mode")


def _utc_timestamp() -> str:
    """Возвращает ISO-строку с текущим временем UTC."""

    return datetime.now(timezone.utc).isoformat()


def _wrap_journaled_handler(
    handler,
    logged_step_ids: set[str],
):
    """Декоратор для записи статусов шага в журнал."""

    def _wrapper(step: StepIR, ctx: Dict[str, Any]) -> None:
        append_event(_utc_timestamp(), step.step_id, "Running", "Старт шага", None)
        try:
            handler(step, ctx)
        except StepBlockedError as exc:
            append_event(_utc_timestamp(), step.step_id, "Blocked", str(exc), None)
            logged_step_ids.add(step.step_id)
            raise
        except Exception as exc:  # noqa: BLE001
            append_event(_utc_timestamp(), step.step_id, "Failed", str(exc), None)
            logged_step_ids.add(step.step_id)
            raise
        else:
            append_event(_utc_timestamp(), step.step_id, "Succeeded", "Шаг выполнен", None)
            logged_step_ids.add(step.step_id)

    return _wrapper


def _handle_workspace_init(step: StepIR, ctx: Dict[str, Any]) -> None:
    """Handler для шага WorkspaceInit."""

    workspace_init(step, ctx)


def _handle_write_profile(step: StepIR, ctx: Dict[str, Any]) -> None:
    """Handler для шага WriteMO2Profile."""

    write_mo2_profile(step, ctx)


def _handle_run_loot(step: StepIR, ctx: Dict[str, Any]) -> None:
    """Handler для шага RunLOOT."""

    mode = ctx.get("loot_mode")
    if not mode:
        raise ValueError("Не задан режим LOOT для RunLOOT")

    result = run_loot(str(mode), ctx)
    if result.status == "Blocked":
        raise StepBlockedError(result.message)


def _handle_checkpoint(step: StepIR, ctx: Dict[str, Any]) -> None:
    """Handler для шага Checkpoint: фиксируем текущие артефакты состояния."""

    root_path = Path(ctx["root_path"])
    write_state_artifacts(root_path)


def _handle_report(step: StepIR, ctx: Dict[str, Any]) -> None:
    """Handler для шага Report."""

    root_path = Path(ctx["root_path"])
    generate_report(root_path)


def _build_handlers(logged_step_ids: set[str]) -> Dict[str, Any]:
    """Собирает allowlist обработчиков шагов с журналированием."""

    handlers = {
        "WorkspaceInit": _handle_workspace_init,
        "WriteMO2Profile": _handle_write_profile,
        "RunLOOT": _handle_run_loot,
        "Checkpoint": _handle_checkpoint,
        "Report": _handle_report,
    }

    return {
        step_type: _wrap_journaled_handler(handler, logged_step_ids)
        for step_type, handler in handlers.items()
    }


def _load_plan(root_path: Path) -> PlanIR:
    """Загружает план из state/plan.ir.json."""

    plan_path = root_path / "state" / "plan.ir.json"
    if not plan_path.exists():
        raise FileNotFoundError("Отсутствует state/plan.ir.json — сначала выполните plan")
    return load_plan_ir(str(plan_path))


def cmd_init(root_path: Path) -> None:
    """Инициализирует базовую структуру директорий."""

    step = StepIR(step_id="workspace_init", step_type="WorkspaceInit", label="Init")
    ctx = {"root_path": root_path}
    workspace_init(step, ctx)


def cmd_plan(config_path: Path) -> Path:
    """Генерирует Plan IR и сохраняет его в state/plan.ir.json."""

    config = _read_config(config_path)
    root_path = _resolve_root_path(config)

    plan = generate_plan(config)
    plan_path = root_path / "state" / "plan.ir.json"
    write_json(plan_path, plan_ir_to_dict(plan))
    return plan_path


def cmd_apply(root_path: Path | None, config_path: Path | None) -> ExecutionResult:
    """Выполняет план и фиксирует артефакты состояния."""

    config: Dict[str, Any] = {}
    if config_path:
        config = _read_config(config_path)

    if root_path is None:
        if config:
            root_path = _resolve_root_path(config)
        else:
            root_path = Path.cwd()

    plan = _load_plan(root_path)

    if not config:
        meta_config = plan.meta.get("config") if isinstance(plan.meta, Mapping) else None
        if isinstance(meta_config, Mapping):
            config = dict(meta_config)

    profile_name = _resolve_profile_name(config)
    loot_mode = _resolve_loot_mode(config)

    journal.JOURNAL_PATH = root_path / "state" / "job.journal.jsonl"

    logged_step_ids: set[str] = set()
    handlers = _build_handlers(logged_step_ids)

    ctx = {
        "root_path": root_path,
        "profile_name": profile_name,
        "loot_mode": loot_mode,
        "handlers": handlers,
        "paths": config.get("paths", {}),
    }

    result = apply_plan(plan, ctx)

    if result.status in {"Blocked", "Failed"}:
        step_id = result.blocked_step_id or result.failed_step_id
        if step_id and step_id not in logged_step_ids:
            append_event(
                _utc_timestamp(),
                step_id,
                result.status,
                result.message or "Шаг завершен с ошибкой",
                None,
            )

    return result


def cmd_report(root_path: Path) -> Path:
    """Генерирует report.md и возвращает путь к файлу."""

    report_text = generate_report(root_path)
    report_path = root_path / "state" / "report.md"
    if not report_text:
        raise RuntimeError("Не удалось сформировать отчет")
    return report_path


def _build_parser() -> argparse.ArgumentParser:
    """Создает argparse-парсер для CLI."""

    parser = argparse.ArgumentParser(prog="modbs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Создать рабочую структуру")
    init_parser.add_argument("root", type=Path, help="Корневая директория workspace")

    plan_parser = subparsers.add_parser("plan", help="Сгенерировать Plan IR")
    plan_parser.add_argument("--config", required=True, type=Path, help="Путь к JSON-конфигу")

    apply_parser = subparsers.add_parser("apply", help="Выполнить план")
    apply_parser.add_argument("--root", type=Path, help="Корневая директория workspace")
    apply_parser.add_argument("--config", type=Path, help="Путь к JSON-конфигу")

    report_parser = subparsers.add_parser("report", help="Сформировать отчет")
    report_parser.add_argument("--root", required=True, type=Path, help="Корневая директория")

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Точка входа CLI. Возвращает код завершения."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            cmd_init(args.root)
        elif args.command == "plan":
            cmd_plan(args.config)
        elif args.command == "apply":
            cmd_apply(args.root, args.config)
        elif args.command == "report":
            cmd_report(args.root)
        else:
            parser.error("Неизвестная команда")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Неожиданная ошибка: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
