# AP-010 — Конфигурации развёртывания

Priority: P1. Owner: UNASSIGNED. Blocked: зависимости/входы проверяются перед стартом.

## Цель
Подготовить один выбранный systemd+proxy либо Compose вариант.

## Зависимости
AP-002, AP-003; OS/runtime выбран

## Scope
Только файлы; не устанавливать/перезапускать services, не создавать VM.

## Приёмка
Pinned artifact/entrypoint; nonroot, loopback, process cleanup, limits, env вне Git, rollback и health limits описаны.

## Результат
NOT_STARTED. Код/проверки/публикация/deploy не выполнялись.
