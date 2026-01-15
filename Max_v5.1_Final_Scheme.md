# Max v5.1 (Final) — AI-native build system для сборок Skyrim

> **Смысл схемы:** управлять сборками Skyrim как *build system*: строить план, исполнять, верифицировать и (при необходимости) ремонтировать пайплайны сборки с воспроизводимостью уровня **snapshot/release**.

---

## 1) Цель и позиционирование

Построить **AI-native CLI-платформу**, которая управляет сборками Skyrim как **build system**: строит план, исполняет, верифицирует и ремонтирует пайплайны сборки с воспроизводимостью уровня “snapshot/release”.

- **Вход:** intent / список модов / гайд / snapshot-план.
- **Выход:** рабочий workspace (MO2 instance + профили) и 4 обязательных артефакта состояния:
  **Plan IR / Lockfile / Provenance / Job Journal**.

Ключевой принцип комплаенса и воспроизводимости: *“everything comes from somewhere”* — платформа должна уметь объяснить происхождение каждого файла и **не заниматься bundling/redistributing модов**.

---

## 2) Главный сдвиг фокуса: manifest-first → build-system-first

Манифесты/IR/lockfile — **не цель и не обязательный ручной вход**. Они — **фиксируемые результаты и “фикстуры”**:

- для повторяемых сборок;
- для диагностики;
- для сравнения изменений;
- для воспроизводимого релиза.

Вход может быть «неформальным» (гайд/интент), но выход всегда формальный и проверяемый (lockfile + provenance + журнал).

---

## 3) Границы ответственности: LLM-агенты vs Deterministic Executor

### 3.1 LLM-агенты (умные, но без side-effects)

LLM-агенты выполняют:

- планирование (строят/обновляют DAG);
- диагностику (интерпретация логов/ошибок);
- подбор playbooks/skills;
- объяснение и формирование ProposedActions.

**Запрет:** прямые операции над FS/process/network (никаких «самовольно скопировать/удалить/скачать»).

### 3.2 Deterministic Executor (единственный слой side-effects)

Executor — единственный компонент, который:

- выполняет типизированные шаги через allowlist;
- применяет capability checks (в т.ч. destructive);
- пишет **Job Journal** и чекпоинты;
- проверяет declared outputs по verify-spec.

Эта граница снижает риск “агентного самоуправства” и повышает воспроизводимость.
В качестве ориентира по авторизации/безопасности tool-вызовов может использоваться MCP (см. ссылки).

---

## 4) “4 опоры” данных (обязательные артефакты)

### 4.1 Plan IR (mutable)
DAG типизированных шагов:

- параметры;
- `produces/consumes`;
- repair-hints;
- risk-level;
- ссылки на skills/playbooks.

### 4.2 Lockfile (immutable per snapshot/release)
“Что именно должно получиться”:

- версии/источники/хэши;
- expected outputs + инварианты;
- идентификатор релиза.

### 4.3 Provenance graph (immutable per snapshot/release)
Происхождение каждого артефакта и цепочка derivation:

- Downloaded / Generated / UserAuthored / ToolOutput / Metadata.

### 4.4 Job Journal (runtime)
State machine выполнения:

- `Succeeded | Failed | Blocked(reason)` по шагам;
- pause/resume;
- чекпоинты;
- логи, метрики, стоимость (время/диск/лимиты).

---

## 5) Workspace boundary: 3 зоны + Cost/Risk Ledger (always-on)

### 5.1 Три зоны

1. **RootState / StockGame (immutable-policy)** — управляемая “чистая база” игры и root-операции.
2. **Workspace zone** — MO2 instance (profiles/mods/overwrite + outputs тулчейна).
3. **Cache zone** — downloads/cache (дедуп, политика очистки, аудит).

### 5.2 RootState/StockGame как first-class доменная модель

Контракт:

- `RootSnapshot` / `RootApply` / `RootRollback` / `RootVerify`.

Практика “Stock Game” используется в экосистеме Wabbajack и Nolvus для поддержания чистоты папки игры (см. ссылки).

### 5.3 Cost/Risk Ledger (обязателен в каждом шаге)
На каждом шаге фиксировать:

- Δдиск по зонам + прогноз роста;
- budget по источникам (rate-limit);
- risk-flags: GUI-heavy шаги, volatility источника, disk pressure, потенциальный недетерминизм.

---

## 6) Backend v0: MO2/USVFS как WorkspaceBackend

MO2/USVFS — стратегический выбор для “универсальности” без собственной VFS:

- USVFS реализует userspace VFS, **используя API hooking**, чтобы переопределять файловые обращения выбранных процессов (см. ссылку на репозиторий USVFS).

Архитектурно: интерфейс `WorkspaceBackend`, где MO2 — первая реализация; далее возможны другие backends.

---

## 7) Runtime loop как build-system

Цикл:

**Plan → Execute → Verify → Repair → Checkpoint**

- LLM-агенты формируют ProposedActions → валидатор IR → executor исполняет allowlisted шаги.
- Любой шаг обязан быть идемпотентным:
  `already_ok() → run() → verify() → checkpoint`.

---

## 8) Toolchain automation: “честная граница” через ToolAdapter

### 8.1 ToolAdapter контракт
`prepare_inputs → run → parse_logs → expected_outputs → verify_outputs → idempotency_check`

### 8.2 MVP-ready адаптеры (детерминируемые)

**LOOT**
- поддерживает `--game` и `--game-path`;
- поддерживает `--auto-sort` (требует `--game`);
- поддерживает `--loot-data-path` (важно для изоляции данных и воспроизводимости).

**xEdit**
- режим/игра выбирается аргументом или переименованием exe;
- поддержаны CLI-параметры для cleaning:
  - `-quickautoclean` + `-autoload <module>`;
  - `-autoexit`.

### 8.3 Генераторы и GUI-heavy инструменты (после MVP)

DynDOLOD/Nemesis/BodySlide и прочее подключаются только при наличии:

- управляемых сценариев (профили/конфиги);
- строгих expected outputs + verify;
- политики недетерминизма (cache keys, replay, known-good профили).

---

## 9) Таксономия шагов v0 → v1

### 9.1 MVP (v0)
- `Acquire`, `VerifyDownload`, `Extract`, `InstallToManager`
- `RootSnapshot`, `RootApply`, `RootRollback`, `RootVerify`
- `RunLOOT`
- `RunXEditQAC` / `RunXEditCheck` (по мере готовности парсинга/критериев)
- `Checkpoint`, `Report`

### 9.2 Расширение (v1+)
- `RunGenerator_*`, `PatchMerge_*`, `SmokeTest`, `PerfProbe`
- `ArtifactClassify`, `PolicyCheck(public)`

---

## 10) Quality tiers (Definition of Done / SLA уровни)

- **Tier 0:** целостность и воспроизводимость (структура, хэши, expected outputs, инварианты RootState).
- **Tier 1:** статическая валидность моддинга (LOOT сигналы + xEdit checks/clean-моды).
- **Tier 2 (optional):** smoke test “запуск до меню/минимальный сценарий” (без обещания “играбельности”).
- **Tier 3 (Max):** perf/regression (времена запуска, базовые метрики стабильности).

---

## 11) Error taxonomy v1 + deterministic remediation playbooks

Категории:

- `Auth`, `RateLimit`, `HashMismatch`, `CorruptArchive`
- `MissingMaster`, `PluginDependency`
- `ToolchainFailure` (LOOT/xEdit/generators)
- `Pathing`, `Permissions`, `DiskSpace`
- `SourceRemovedOrChanged`, `CacheCorruption`
- `SmokeTestFailure` (optional)

LLM-агент выбирает playbook и параметры; Executor исполняет строго типизированные шаги.

---

## 12) Incremental modding как build-system: impact model

### 12.1 Deterministic classification
Классы изменений по артефактам:

- plugins (`*.esp/*.esm/*.esl`)
- SKSE DLL
- root files (ENB/Reshade/engine-level)
- meshes/textures
- animation markers
- generator markers

### 12.2 Impact contract
- Invalidation keys: `LoadOrder`, `XEditOutput`, `DynDOLODOutput`, `NemesisOutput`, `RootState`, …
- шаги объявляют `produces/consumes`
- изменения объявляют `invalidates`
- Planner строит **минимальный downstream DAG** (аналог инкрементальной сборки).

---

## 13) Pause/Resume + rate limits как штатный Blocked(reason)

Источники могут иметь лимиты API (например, Nexus публикует пояснения про rate limits и “daily/hourly limit”).

Следствия для платформы:

- шаг переводится в `Blocked(rate_limit)` → checkpoint + `next_action_at`
- `resume` продолжает с последнего консистентного состояния
- scheduler учитывает API-budget в Cost/Risk Ledger

---

## 14) Public vs Private mode (компактные правила)

### 14.1 Private mode
- локальная автоматизация без “публичных ограничений”;
- lockfile/provenance всё равно рекомендованы (иначе теряется воспроизводимость/repair).

### 14.2 Public mode (metadata-first)
- запрет на inlining скачанных модов и перераспространение;
- provenance обязателен для всех outputs;
- строгая классификация артефактов.

---

## 15) Self-improvement без fine-tuning: memory bank + retrieval/scoring + governance

### 15.1 Memory bank
На каждый прогон сохранять:

- features (версии, список модов, toolchain, параметры, среда);
- outcomes (tiers, ошибки, repair-циклы, time/disk).

### 15.2 Retrieval/scoring
На новом входе выбирать наиболее надёжные пайплайны/параметры по похожим кейсам.

### 15.3 Governance (обязательное)
Любое улучшение skills/парсеров/правил проходит:
**regression harness → canary → stable promotion**

Релизные snapshots (lockfile+provenance) неизменяемы.

---

## 16) Optional: Windows Sandbox (не часть MVP)
Windows Sandbox может конфигурироваться `.wsb` и запускаться как disposable среда. В MVP не является критерием успеха.

---

## 17) MVP для ВКР: “walking skeleton” (end-to-end срез)

Walking skeleton = минимальная end-to-end реализация, которая связывает основные архитектурные компоненты.

**MVP-1 (ядро надёжности):**
- CLI: `init, add, plan, apply, status, resume, doctor, report, --dry-run`
- Schemas: Plan IR + Job Journal state machine + Cache manager
- 1 ToolAdapter: LOOT (run + parse + Tier1 сигнал)
- RootState v0: snapshot/apply/verify (минимальный allowlist)
- Always-on ledger: Δdisk + rate-limit budget + risk flags

**MVP-2 (качество моддинга):**
- 2-й ToolAdapter: xEdit QAC/check (run + parse + критерии)
- Первые deterministic remediation playbooks (5–10 типовых)

---

## 18) Спецификации v0 как артефакты ВКР

1. **Spec-IR v0:** schema, step-types, produces/consumes, verify_spec.
2. **Spec-RootState v0:** snapshot/apply/rollback + инварианты + allowlisted root-операции.
3. **Spec-ErrorTaxonomy v0:** категории → playbooks → критерии “fixed”.
4. **Spec-PublicModeRules v0:** классификация артефактов + минимальные запреты/разрешения.

---

## ASCII runtime-диаграмма

```text
   [User Input: intent/modlist/guide/snapshot]
                    |
                    v
            +-----------------+
            |  LLM Agents     |  (plan/diagnose/repair/impact)
            | ProposedActions |
            +--------+--------+
                     |
                     v  (validate schema & policy)
            +--------------------+
            |   Plan IR Validator|
            +---------+----------+
                      |
                      v
            +--------------------+        writes/checkpoints
            | Deterministic      |------------------------------+
            | Executor (allowlist|                              |
            | + capabilities)    |                              v
            +----+----------+----+                      +---------------+
                 |          |                           | Job Journal   |
     FS/Net/Proc |          | outputs/derivation        | (pause/resume)|
                 v          v                           +---------------+
        +----------------+  +-------------------+
        | ToolAdapters   |  | Provenance Graph  |-----> Lockfile (release)
        | (LOOT/xEdit/..) |  | + Artifact Store |
        +--------+--------+  +-------------------+
                 |
                 v
  +-------------------+   +---------------------+   +------------------+
  | RootState/StockGame|  | Workspace (MO2/USVFS)|  | Cache (downloads)|
  | snapshot/apply/... |  | profiles/mods/...    |  | dedup/cleanup     |
  +-------------------+   +---------------------+   +------------------+
```

---

## Ссылки (первичные/официальные)

1. Wabbajack Documentation — Stock Game / “Keeping the Game Folder clean”:
   - https://wiki.wabbajack.org/modlist_author_documentation/Keeping%20the%20Game%20Folder%20clean.html
2. Nolvus — Stock Game (изолированная установка, “Steam install remains absolutely clean”):
   - https://www.nolvus.net/appendix/installer/tech
   - https://www.nolvus.net/guide/asc/stockgame
3. LOOT Documentation — CLI параметры (`--game`, `--game-path`, `--auto-sort`, `--loot-data-path`):
   - https://loot.readthedocs.io/en/stable/app/usage/initialisation.html
4. USVFS (Mod Organizer 2) — userspace VFS и API hooking:
   - https://github.com/ModOrganizer2/usvfs
5. Nexus Mods Help — пояснения про rate limits (“daily/hourly limit”):
   - https://help.nexusmods.com/article/105-i-have-reached-a-daily-or-hourly-limit-api-requests-have-been-consumed-rate-limit-exceeded-what-does-this-mean
6. Model Context Protocol — Authorization и Security Best Practices:
   - https://modelcontextprotocol.io/specification/draft/basic/authorization
   - https://modelcontextprotocol.io/specification/draft/basic/security_best_practices
