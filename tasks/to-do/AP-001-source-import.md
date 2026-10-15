> LOCAL MVP: детализация AP-016/AP-017, не обязательная отдельная очередь. AP-003 package migration и cloud/deploy требования ниже заменены локальным scope docs/LOCAL_MVP.md. Текущие AC: честный localhost инструмент, без enterprise инфраструктуры.

Для работы с авторскими файлами локально не требуется ждать public source import/выбора LICENSE. Если Claude имеет файлы — реализовать local MVP; публикация кода отдельным allowlist действием.

# AP-001 — Безопасный первый импорт и права публикации

Priority: P0. Owner: UNASSIGNED. Blocked: зависимости/входы проверяются перед стартом.

## Цель
Согласовать права автора/LICENSE, отделить private artifacts и сделать чистый Git import по allowlist.

## Зависимости
Нет

## Scope
Только curated Python/UI/docs/config; profiles/cookies/history/captures не читаются и не публикуются.

## Приёмка
Git checkout/base установлен; staged files просмотрены; нет личных данных/секретов; public publication отдельно поручена.

## Результат
NOT_STARTED. Код/проверки/публикация/deploy не выполнялись.
