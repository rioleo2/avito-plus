# AP-008 — DOM, input и ограничения сервиса

Priority: P0. Owner: UNASSIGNED. Blocked: зависимости/входы проверяются перед стартом.

## Цель
Безопасно отобразить объявления и ограничить дорогие запросы до beta.

## Зависимости
AP-003, AP-004

## Scope
textContent/URL scheme+host checks, body bounds, auth пилота/rate+concurrency+queue/deadline; без production.

## Приёмка
External text не исполняется; небезопасные URLs отклонены; перегрузка ограничена; логи не раскрывают cookies/secret/raw captures; CDN assets закреплены.

## Результат
NOT_STARTED. Код/проверки/публикация/deploy не выполнялись.
