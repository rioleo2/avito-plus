# Avito Plus — простой локальный MVP

Папка определяет статус. Реализация ещё не начата. Не нужно проходить старый server backlog подряд.

## To do — ближайшие два этапа

| Задача | Результат |
|---|---|
| [AP-016](to-do/AP-016-local-launcher-lmstudio.md) | Setup + запуск/остановка одной кнопкой, LM Studio |
| [AP-017](to-do/AP-017-local-search-quality.md) | Реальные объявления, несколько страниц, фото, лучшие среди найденных |

Перед кодом нужен доступ к авторским исходникам; если Claude видит только GitHub docs — передать чистые source файлы, не browser profiles.

### Справочные детали, включены в два этапа

AP-001 source import; AP-002 dependencies; AP-004 honest source; AP-005 filters/pages; AP-006 local source; AP-007 LM Studio; AP-008 safe DOM/local limits; AP-009 offline acceptance; AP-013 photos; AP-014 identity/price/link; AP-015 ranking. Файлы остаются в to-do как детализация, не означают выполненную работу. После реализации закрывать только реально покрытые AC.

### Отложено, не блокирует local MVP

- [AP-003 package migration](to-do/AP-003-package-migration.md) — root layout достаточен.
- [AP-010 deploy configs](to-do/AP-010-deployment-artifacts.md).
- [AP-011 cloud/domain/budget](to-do/AP-011-cloud-domain-decisions.md).
- [AP-012 Cloud.ru pilot](to-do/AP-012-private-pilot.md).

## In progress

Нет активных задач. Публикация промпта не начинает работу Claude автоматически.

## Done

- [AP-000 — исходная документационная подготовка](done/AP-000-repository-planning.md). Не готовое приложение.

[Готовый промпт](../docs/CLAUDE_LOCAL_MVP_PROMPT.md). Обновлять BOARD вместе с реальным статусом папок.
