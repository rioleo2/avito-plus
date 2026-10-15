> LOCAL MVP: детализация AP-016/AP-017, не обязательная отдельная очередь. AP-003 package migration и cloud/deploy требования ниже заменены локальным scope docs/LOCAL_MVP.md. Текущие AC: честный localhost инструмент, без enterprise инфраструктуры.

# AP-006 — Переносимый источник объявлений

Priority: P0. Owner: UNASSIGNED. Blocked: зависимости/входы проверяются перед стартом.

## Цель
Выбрать допустимый источник без чтения личного Windows browser cookie store.

## Зависимости
AP-003; решение об источнике

## Scope
Не stealth/credential extraction/proxy rotation; live проверки требуют отдельного поручения.

## Приёмка
Нет жёсткого пути пользователя; explicit source unavailable; resource/browser cleanup и deadlines; cloud reachability ещё отдельный gate.

## Результат
NOT_STARTED. Код/проверки/публикация/deploy не выполнялись.
