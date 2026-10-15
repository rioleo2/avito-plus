# План миграции кода

## 1. Зафиксировать и отобрать

Сохранить исходную папку без удаления/перезаписи. SOURCE_MANIFEST содержит SHA-256/размеры только пяти Python modules + UI + manual experiment files; не копирует их содержимое. GitHub public: перед импортом согласовать с автором право публикации и LICENSE, просмотреть код на credentials/личные пути. Browser profiles/history/debug captures исключить.

Создать отдельный чистый checkout/ветку для подготовки. Если GitHub ещё без первого commit, создать bootstrap history только из отобранных файлов; если branch уже существует, использовать её фактический head. Не предполагать SHA пустого repo. Первый импорт явным allowlist, просмотр diff; никакого git add . в исходной папке с браузерными профилями.

## 2. Воспроизводимое окружение

Выбрать совместимую Python minor version (предложение: 3.12, проверить на этапе реализации) и зафиксировать direct/transitive dependencies. Playwright требует отдельной установки соответствующего browser binary/OS dependencies — это часть build, не on-demand download в каждом запросе. Текущий requirements.in не lock и не гарантирует совместимость Jinja TemplateResponse.

Отделить runtime и manual experiment dependencies. Конфигурация через settings/env: source mode, concurrency/time limits, AI mode/URL/model, cache. .env.example сейчас задаёт будущий контракт и не меняет поведение кода.

## 3. Механический перенос

В src/avito_plus перенести пять modules, templates, static; исправить imports на package-relative, BASE_DIR resource paths, packaging assets/entrypoint. Сохранить API и UI. Перенос отделить commit-ом от поведенческих исправлений, чтобы можно было сравнить hashes/diff и откатить. Корневые оригиналы убирать только после принятия переноса и сохранённой истории. Не складывать копии исходников в docs.

Будущий entrypoint: avito_plus.app:app. Сейчас он не существует, не использовать для запуска до завершения AP-003. Не импортировать текущие app/analyzer/scraper ради инвентаризации.

## 4. Исправления до public beta

Сначала AP-004 честные live/cached/demo/error states; затем AP-005 валидация/фильтры/pagination/cache; AP-006 portable source без cookies личного пользователя; AP-007 optional inference; AP-008 безопасный DOM/URL, auth/limits/deadlines и закрытые API docs по выбранной политике.

При 403/429/CAPTCHA возвращать source unavailable/retry-after, не подставлять генерируемые карточки. Зафиксировать допустимый способ получения данных/разрешения и требования источника до реального сбора. Личный browser cookie store не становится серверной учётной записью. Не внедрять stealth/proxy rotation/обход CAPTCHA как решение развёртывания.

MVP может работать без LLM: явно маркированный heuristic summary с ограничениями. Поиск должен оставаться полезным при отключённом AI. AI result не подтверждает дефект/безопасность покупки и не гарантирует profit.

## 5. Приёмка и публикация

Будущая AP-009: offline fixtures/mock API, проверки source states/filter boundaries/pagination/cache isolation и безопасного HTML; live checks отдельным поручением с лимитами. Сейчас тесты не добавлялись/не запускались.

Публикация только чистой ветки с source allowlist, review структуры/конфигурации/лицензии. Сопоставить старые и новые пути, удалить неподдерживаемые UI-фильтры или показать disabled, не оставлять работающую кнопку с игнорируемым параметром. Tagged candidate → private pilot → domain rollout по DEPLOYMENT.

Готовность: воспроизводимая установка, сервер не зависит от личного ПК, нет скрытого demo fallback/unsafe DOM, источники доступны выбранным допустимым способом, есть лимиты и понятная ошибка. Перенос файлов сам по себе не делает продукт готовым.
