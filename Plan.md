# MVP Plan - AI-native Modlist Profile Builder

## 1. Цель MVP
Собрать working end-to-end: `init → plan → apply → report`, создающий/обновляющий MO2 workspace и фиксирующий 4 артефакта состояния (Plan IR / Job Journal / Provenance / Lockfile) + derived Report.

## 2. Scope
**Входит:**
- CLI: `init`, `plan`, `apply`, `status`, `report`
- Plan IR (шаблонный/правил-ориентированный)
- Deterministic Executor с allowlist шагов
- Job Journal + Provenance + Lockfile + Report
- LOOT-адаптер (real/mock/blocked)

**Не входит:**
- скачивание/установка модов из сети
- GUI-heavy генераторы (DynDOLOD/Nemesis/BodySlide)
- RootState policy и xEdit (перспектива v1+)

## 3. Артефакты состояния
- `state/plan.ir.json`
- `state/job.journal.jsonl`
- `state/provenance.json`
- `state/lockfile.json`
- `state/report.md`

## 4. Allowlist шагов (v0)
1. WorkspaceInit
2. WriteMO2Profile
3. RunLOOT (real/mock/blocked)
4. Checkpoint
5. Report

## 5. Технологии
- Язык: Python 3.10+
- CLI: argparse (без новых зависимостей)
- Форматы: JSON, JSONL, YAML (опционально)
- Хранилище: файловая система
- ToolAdapter: subprocess (LOOT)

## 6. Этапы реализации
1. Инициализация workspace + state зон
2. Генерация Plan IR
3. Executor и allowlist шагов
4. Job Journal (JSONL)
5. Provenance + Lockfile
6. Report
7. LOOT Adapter (real/mock/blocked)

## 7. Definition of Done
- CLI команды работают end-to-end
- Все 4 артефакта создаются
- LOOT шаг отрабатывает в real/mock/blocked
- Report содержит резюме и результаты проверок

## 8. Риски и ограничения
- Нет сетевых side-effects
- Планировщик не использует LLM
- Воспроизводимость ограничена локальной средой
