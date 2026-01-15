# MVP (Walking Skeleton) — AI-native Modlist Profile Builder (v0)

> **Цель MVP:** получить *работающий end-to-end срез* `init → plan → apply → report`, который создаёт/обновляет MO2 workspace и оставляет после себя **4 артефакта состояния**: Plan IR / Lockfile / Provenance / Job Journal. Интеллектуальный (AI) контур может быть “AI-ready” (интерфейс/контракт), без обязательной автоматизации планирования в MVP.

---

## 1) Scope MVP (фиксируем)

### 1.1 Что умеет (DoD)
1. **Инициализирует рабочее окружение** (workspace zones + state).
2. **Строит формальный план (Plan IR)** для выбранного сценария (без LLM, rule-based/шаблон).
3. **Исполняет план через deterministic executor** (allowlist шагов).
4. **Пишет Job Journal** (append-only JSONL) и чекпоинты.
5. **Формирует Lockfile и Provenance** для результатов прогона.
6. **Генерирует отчёт** `report.md` (что сделано/что проверено/что заблокировано).

### 1.2 Что НЕ умеет (вынести в “перспективы”)
- скачивать моды и интегрироваться с Nexus/Wabbajack (нет сетевых side-effects);
- запускать GUI-heavy генераторы (DynDOLOD/Nemesis/BodySlide);
- автоматически “понимать” текст гайда и строить DAG (только шаблонный planner).

---

## 2) CLI (минимальный набор)

- `modbs init <path>`
- `modbs plan --config <config.yaml>`
- `modbs apply`
- `modbs status`
- `modbs report`

Опционально:
- `--dry-run`
- `--mock-tools`

---

## 3) Workspace boundary (v0)

После `init` создаются зоны:

```text
<root>/
  rootstate/        # метаданные StockGame / snapshot info (v0)
  workspace/        # MO2 instance (portable/instance) и профили
  cache/            # downloads/cache placeholder (v0)
  state/            # артефакты Plan/Lock/Prov/Journal/Report
```

---

## 4) 4 артефакта состояния (MVP-реализация)

### 4.1 Plan IR (plan.ir.json)
Минимальная структура:

- `steps[]`: `{id, type, inputs, expected_outputs, verify_spec, risk_level}`
- `edges[]`: зависимости (можно пусто при линейном плане)
- `meta`: `{created_at, workspace_id, tool_versions?}`

### 4.2 Job Journal (job.journal.jsonl)
Append-only события:

- `{ts, step_id, status, message, metrics{disk_delta?}}`
- `status ∈ {Running, Succeeded, Failed, Blocked}`

### 4.3 Provenance (provenance.json)
Минимальный граф/список:

- артефакты: `{artifact_id, path, class, source, hash?, derived_from_step}`
- классы: `Generated | ToolOutput | UserAuthored | Metadata`

### 4.4 Lockfile (lockfile.json)
Snapshot результата:

- `release_id`
- `artifacts[]`: `{path, hash, source_ref?, invariants?}`

---

## 5) Allowlist шагов v0 (реально реализуемые)

1. `WorkspaceInit`
2. `WriteMO2Profile`
3. `RunLOOT` *(best-effort: real или mock)*
4. `Checkpoint`
5. `Report`

### 5.1 WriteMO2Profile (ядро доменной ценности MVP)
- создаёт/обновляет профиль MO2 (минимум: `modlist.txt` + базовые файлы профиля);
- верифицирует ожидаемые outputs (существование, размер, хэш/сигнатуры).

> Для дальнейшего расширения достаточно добавить шаги и адаптеры, не меняя контракт Journal/Provenance/Lockfile.

---

## 6) ToolAdapter v0: LOOT

### 6.1 Реальный режим (direct)
LOOT документирует CLI параметры `--game`, `--game-path`, `--auto-sort`, а также `--loot-data-path` (для изоляции данных и воспроизводимости).

- https://loot.readthedocs.io/en/stable/app/usage/initialisation.html

### 6.2 Fallback режимы (когда real невозможен/нестабилен)
- `mock`: возвращает структурированный результат “как будто LOOT отработал” (для демонстрации end-to-end и форматов).
- `blocked`: шаг завершаетcя статусом `Blocked(reason)` и фиксирует причину (нет бинаря, нет прав, неверный путь).

---

## 7) Минимальный Plan IR (пример)

```json
{
  "meta": {
    "schema": "modbs.plan_ir.v0",
    "created_at": "2026-01-14T00:00:00+01:00"
  },
  "steps": [
    {"id": "s1", "type": "WorkspaceInit", "inputs": {}, "expected_outputs": ["workspace/"], "verify_spec": {"exists": ["workspace/"]}, "risk_level": "low"},
    {"id": "s2", "type": "WriteMO2Profile", "inputs": {"profile": "Default"}, "expected_outputs": ["workspace/profiles/Default/modlist.txt"], "verify_spec": {"exists": ["workspace/profiles/Default/modlist.txt"]}, "risk_level": "low"},
    {"id": "s3", "type": "RunLOOT", "inputs": {"mode": "auto"}, "expected_outputs": ["state/loot.result.json"], "verify_spec": {"exists": ["state/loot.result.json"]}, "risk_level": "medium"},
    {"id": "s4", "type": "Report", "inputs": {}, "expected_outputs": ["state/report.md"], "verify_spec": {"exists": ["state/report.md"]}, "risk_level": "low"}
  ],
  "edges": [
    {"from": "s1", "to": "s2"},
    {"from": "s2", "to": "s3"},
    {"from": "s3", "to": "s4"}
  ]
}
```

---

## 8) Репозиторий (минимальная структура)

```text
modbs/
  __init__.py
  cli.py
  models.py
  storage.py
  executor.py
  verify.py
  report.py
  adapters/
    loot.py
schemas/
  plan_ir.schema.json
examples/
  config.example.yaml
```

---

## 9) Как запускать (локально)

1. `python -m venv .venv`
2. активировать venv
3. `pip install -r requirements.txt`
4. `python -m modbs init demo_ws`
5. `python -m modbs plan --config examples/config.example.yaml`
6. `python -m modbs apply`
7. `python -m modbs report`

**Результат:** в `demo_ws/state/` лежат Plan IR / Job Journal / Provenance / Lockfile / report.md.

---

## 10) Evidence pack для Главы 3 (что прикладывать)
- `plan.ir.json`
- `job.journal.jsonl` (1 успешный и 1 “Blocked/Failed” прогон)
- `lockfile.json`
- `provenance.json`
- `report.md`
- “до/после” профиля MO2 (файлы профиля как артефакты)

---

## Ссылки (первичные/официальные)
- LOOT Documentation — CLI параметры:
  https://loot.readthedocs.io/en/stable/app/usage/initialisation.html
- USVFS (MO2) — userspace VFS и API hooking:
  https://github.com/ModOrganizer2/usvfs
