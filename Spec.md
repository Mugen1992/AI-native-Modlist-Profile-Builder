# SDD v0.1 (MVP-safe) — AI-native Modlist Profile Builder

**Status:** BASELINE (Scope-Lock v0.1)
**Goal:** end-to-end контур `init → plan → apply → report` для сборки/обновления MO2 workspace/profile с фиксацией **machine-readable артефактов состояния**: **Plan IR / Job Journal / Provenance / Lockfile** и производного **human-readable Report**.
**TDD-first:** тесты пишутся до реализации (unit → integration → E2E).

---

## 1) Purpose & Context
Реализовать детерминированный build-system для MO2-профилей: планируем формальный набор шагов (без LLM), исполняем через allowlist-исполнитель и фиксируем все side-effects через state artifacts.

---

## 2) Scope (MVP)

### In-scope
- CLI: `init`, `plan`, `apply`, `status`, `report`
- Planner: rule-based генерация Plan IR
- Executor: deterministic allowlist executor
- State artifacts: Plan IR / Job Journal / Provenance / Lockfile (+ derived Report)
- LOOT adapter: `real / mock / blocked`

### Out-of-scope (v1+)
- загрузка/установка модов по сети (Nexus/Wabbajack)
- GUI-heavy генераторы (DynDOLOD/Nemesis/BodySlide)
- RootState policy, xEdit adapter, расширенная governance-логика

---

## 3) Architecture (SoC-friendly)
**High-level flow:** `CLI → Planner → Plan IR → Executor → State Artifacts → Report`

### Modules & Responsibilities
- `modbs/cli.py` — парсинг аргументов, вызов use-cases, вывод ошибок.
- `modbs/planner.py` — `generate_plan(config) -> PlanIR` (rule-based).
- `modbs/executor.py` — `execute(plan, ctx) -> ExecutionResult`; **единственный слой side-effects**.
- `modbs/storage.py` — чтение/запись JSON/JSONL/MD, **atomic write**.
- `modbs/journal.py` — append-only JSONL events.
- `modbs/state.py` — Provenance/Lockfile builders, hashing, snapshot.
- `modbs/report.py` — сборка `report.md` из journal + lockfile.
- `modbs/adapters/loot.py` — `run(mode, ctx) -> LootResult` (real/mock/blocked).
- `modbs/steps/*.py` — allowlist steps: `WorkspaceInit`, `WriteMO2Profile`, `RunLOOT`, `Checkpoint`, `Report`.

**Dependency rule:** CLI зависит от use-cases; Planner/Executor — от models/storage; Adapters изолированы.

---

## 4) Data Contracts (light)
**Single source of truth:** `schemas/` (JSON Schema) + `examples/`.
Spec содержит только минимальные формы и ссылки на schemas.

### 4.1 Plan IR — `state/plan.ir.json`
```json
{
  "meta": {"schema":"modbs.plan_ir.v0","created_at":"...","tool_version":"..."},
  "steps":[{"id":"s1","type":"WorkspaceInit","params":{}},{"id":"s2","type":"WriteMO2Profile","params":{"profile":"MVP"}}]
}
```

### 4.2 Job Journal — `state/job.journal.jsonl` (append-only)
```json
{"ts":"...","step_id":"s1","status":"Running","message":"...","metrics":{"ms":12}}
```
Статусы: `Running | Succeeded | Failed | Blocked`.

### 4.3 Provenance — `state/provenance.json`
```json
{
  "meta":{"schema":"modbs.provenance.v0"},
  "artifacts":[{"path":"state/report.md","class":"Generated","derived_from_step":"s5"}]
}
```

### 4.4 Lockfile — `state/lockfile.json`
```json
{
  "meta":{"schema":"modbs.lockfile.v0"},
  "release_id":"local-run-001",
  "artifacts":[{"path":"workspace/profiles/MVP/modlist.txt","hash":"sha256:..."}]
}
```

### 4.5 Report — `state/report.md`
Derived view из journal + lockfile: summary + outputs + reproduce.

---

## 5) Config (минимальный контракт входа Planner)
Минимально необходимы поля:
- `profile_name` (string)
- `paths.root` (string)
- `paths.mo2` (string)
- `paths.skyrim` (string)
- `loot.mode` (`real | mock | blocked`)
- `manifest_path` (optional)

---

## 6) Allowlist Steps (contracts for ключевые шаги)

### 6.1 WorkspaceInit
- **Input:** root path
- **Output:** директории `workspace/`, `state/`, `cache/`, `rootstate/`
- **Fail-Fast:** нет прав/некорректный путь → `Failed` + запись в journal.

### 6.2 WriteMO2Profile
- **Input:** profile name + manifest/config
- **Output:** `workspace/profiles/<name>/modlist.txt` (+ минимальные файлы профиля)

### 6.3 RunLOOT
- **Modes:** real / mock / blocked
- **Output:** loot result/log в `state/` + запись статуса

### 6.4 Checkpoint
- **Output:** метаданные/хэши outputs текущего шага (для трассируемости и диагностики)

### 6.5 Report
- **Output:** `state/report.md`
- **Гарантируемые секции:** Summary, Outputs, Reproduce

---

## 7) CLI Behavior (без жёстких exit codes)

**Обязательное поведение:**
- `init` создаёт структуру директорий
- `plan` создаёт `plan.ir.json`
- `apply` выполняет шаги и пишет state artifacts
- `report` создаёт `report.md`
- `status` выводит summary (stdout)

**Рекомендуемые exit codes (не обязательны для MVP):**
- `0` — ok
- `2` — invalid input
- `3` — missing plan
- `4` — step failed

---

## 8) Success Criteria (Demo checklist)
1. `init` создал структуру workspace/state.
2. `plan` сгенерировал валидный `plan.ir.json`.
3. `apply` выполнил allowlist шаги и создал все state-артефакты.
4. LOOT шаг корректно ведёт себя в `mock`/`blocked`.
5. `report.md` содержит summary и список outputs.

---

## 9) TDD Strategy + Test Matrix

### 9.1 Unit tests
- `test_planner_generates_valid_plan_structure`
- `test_plan_ir_serialization_roundtrip`
- `test_storage_json_roundtrip`
- `test_journal_append_only`
- `test_executor_blocks_unknown_step_type`
- `test_lockfile_contains_hashes`

### 9.2 Integration
- `test_cli_init_creates_workspace_structure`
- `test_cli_plan_creates_plan_ir`
- `test_cli_apply_creates_state_artifacts`
- `test_report_contains_step_statuses`

### 9.3 Acceptance (E2E)
- `test_e2e_success_with_loot_mock`
- `test_e2e_blocked_when_loot_missing`

---

## 10) Test Data / Fixtures

**Fixture A (Success / mock LOOT)**
- Input: минимальный config (profile = `MVP`)
- Expected outputs:
  - `state/plan.ir.json`
  - `state/job.journal.jsonl` (все шаги `Succeeded`)
  - `state/provenance.json`
  - `state/lockfile.json`
  - `state/report.md`

**Fixture B (Blocked LOOT)**
- Input: тот же config, LOOT binary отсутствует
- Expected outputs:
  - `job.journal.jsonl` содержит `Blocked` для `RunLOOT`
  - `report.md` фиксирует blocked-статус и причину

---

## 11) Error Handling (Fail-Fast, Blocked vs Failed)
- Любая ошибка валидации входов → **не создаём/не перезаписываем state artifacts**, кроме append-only записи в job journal (и только при наличии `state/`).
- `Executor`: после `Failed`/`Blocked` не выполняет последующие шаги, если они зависят от результата.
- `RunLOOT`: отсутствие бинаря/доступа → **Blocked(reason)** (не `Failed`).

---

## 12) Non-functional Requirements
- **Determinism:** одинаковые входы **при фиксированных версиях инструментов** → одинаковые outputs/hashes; строгий детерминизм гарантируется в mock-режиме.
- **Minimal deps:** stdlib-first; новые зависимости только при необходимости.

---

## 13) Scope Lock (v0.1)
**No silent scope changes.** Любые новые фичи фиксируются в Scope Change Record (1 абзац: что добавляем, почему, влияние на риски/сроки).

---

# Appendix A — References
- Design by Contract: preconditions, postconditions, invariants.
- Fail-fast: раннее выявление ошибок.
- YAGNI: не реализуем лишние функции до явной необходимости.
- Docs-as-Code: документация хранится в репозитории рядом с кодом.

---

# Appendix B — Examples
## Example Plan IR
```json
{
  "meta": {
    "schema": "modbs.plan_ir.v0",
    "created_at": "2026-01-14T00:00:00+01:00"
  },
  "steps": [
    {
      "id": "s1",
      "type": "WorkspaceInit",
      "params": {}
    },
    {
      "id": "s2",
      "type": "WriteMO2Profile",
      "params": {
        "profile": "MVP"
      }
    },
    {
      "id": "s3",
      "type": "RunLOOT",
      "params": {
        "mode": "mock"
      }
    },
    {
      "id": "s4",
      "type": "Checkpoint",
      "params": {}
    },
    {
      "id": "s5",
      "type": "Report",
      "params": {}
    }
  ],
  "edges": [
    {"from": "s1", "to": "s2"},
    {"from": "s2", "to": "s3"},
    {"from": "s3", "to": "s4"},
    {"from": "s4", "to": "s5"}
  ]
}
```

## Example Report (outline)
```text
# Report

## Summary
- Steps: 5
- Succeeded: 4
- Blocked: 1 (RunLOOT)

## Outputs
- state/plan.ir.json
- state/job.journal.jsonl
- state/provenance.json
- state/lockfile.json
- state/report.md

## Reproduce
- modbs init <path>
- modbs plan --config <config.yaml>
- modbs apply
- modbs report
```
