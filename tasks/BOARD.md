# Avito Plus — канбан

Папки — источник статуса. Все задачи реализации пока не начаты. Приоритет P0 означает gate MVP, не разрешение внешнего действия.

## To do

| ID | Задача | Приоритет | Зависимости |
|---|---|---|---|
| [AP-001](to-do/AP-001-source-import.md) | Безопасный первый импорт и права публикации | P0 | Нет |
| [AP-002](to-do/AP-002-dependencies-settings.md) | Зависимости и настройки | P0 | AP-001 |
| [AP-003](to-do/AP-003-package-migration.md) | Перенос в src/avito_plus | P0 | AP-001, AP-002 |
| [AP-004](to-do/AP-004-honest-source-states.md) | Реальные данные и честные ошибки | P0 | AP-003 |
| [AP-005](to-do/AP-005-filters-cache-pagination.md) | Фильтры, валидация, cache и страницы | P0 | AP-003, AP-004 |
| [AP-006](to-do/AP-006-portable-data-source.md) | Переносимый источник объявлений | P0 | AP-003; решение об источнике |
| [AP-007](to-do/AP-007-optional-ai.md) | Необязательный AI и достоверные оценки | P1 | AP-002, AP-003 |
| [AP-008](to-do/AP-008-web-safety-limits.md) | DOM, input и ограничения сервиса | P0 | AP-003, AP-004 |
| [AP-009](to-do/AP-009-offline-acceptance.md) | Offline приёмка миграции | P0 | AP-004, AP-005, AP-006, AP-007, AP-008 |
| [AP-010](to-do/AP-010-deployment-artifacts.md) | Конфигурации развёртывания | P1 | AP-002, AP-003; OS/runtime выбран |
| [AP-011](to-do/AP-011-cloud-domain-decisions.md) | Выбор домена, VM и бюджета | P1 | Решение владельца |
| [AP-012](to-do/AP-012-private-pilot.md) | Закрытый пилот Cloud.ru | P0 | AP-009, AP-010, AP-011 |

Новые задачи по запросу пользователя:

- [AP-013 — фотографии](to-do/AP-013-listing-photos.md), P1.
- [AP-014 — соответствие товара, цены и ссылки](to-do/AP-014-listing-integrity.md), P0.
- [AP-015 — ранжирование выгодных предложений](to-do/AP-015-best-deals-ranking.md), P1.

AP-005 дополнена реальным multi-page сбором, а не только разбиением текущих 7 карточек. Все четыре задачи остаются To do. Порядок: достоверность → несколько страниц → фото/объяснимый ranking.

## In progress

Нет активных задач.

## Done

- [AP-000 — подготовка структуры и плана](done/AP-000-repository-planning.md). Только документация.
