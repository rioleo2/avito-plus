> LOCAL MVP: детализация AP-016/AP-017, не обязательная отдельная очередь. AP-003 package migration и cloud/deploy требования ниже заменены локальным scope docs/LOCAL_MVP.md. Текущие AC: честный localhost инструмент, без enterprise инфраструктуры.

# AP-002 — Зависимости и настройки

Priority: P0. Owner: UNASSIGNED. Blocked: зависимости/входы проверяются перед стартом.

## Цель
Выбрать Python version, runtime/dev deps, создать lock/settings.

## Зависимости
AP-001

## Scope
Без установки на VM; текущие .env.example переменные реализовать явно; зависимости manual scripts отдельно.

## Приёмка
Чистое окружение воспроизводимо, browser installation описана, secrets не в source; import-time AI/browser effects исключены.

## Результат
NOT_STARTED. Код/проверки/публикация/deploy не выполнялись.
