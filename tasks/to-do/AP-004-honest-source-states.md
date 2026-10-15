> LOCAL MVP: детализация AP-016/AP-017, не обязательная отдельная очередь. AP-003 package migration и cloud/deploy требования ниже заменены локальным scope docs/LOCAL_MVP.md. Текущие AC: честный localhost инструмент, без enterprise инфраструктуры.

# AP-004 — Реальные данные и честные ошибки

Priority: P0. Owner: UNASSIGNED. Blocked: зависимости/входы проверяются перед стартом.

## Цель
Убрать silent fallback; отличать live/cached/demo/empty/blocked/error.

## Зависимости
AP-003

## Scope
Не обходить 403/429/CAPTCHA; demo только explicit opt-in и маркировка; никаких fake live cards.

## Приёмка
<3 реальных объявлений сохраняются реальными; сбой не генерирует товары; source/fetched_at/coverage видны в API/UI.

## Результат
NOT_STARTED. Код/проверки/публикация/deploy не выполнялись.
