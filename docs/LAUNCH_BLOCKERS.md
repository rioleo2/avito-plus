# Блокеры запуска и ближайшие шаги

Срез: 15.10.2026. Публичный поиск **NOT_READY** по статическим наблюдениям и непроверенным условиям запуска. Runtime-аудит/тесты не выполнялись.

| ID / состояние | Конкретный блокер | Основание | Условие закрытия |
|---|---|---|---|
| B01 OPEN | Ошибка/<3 live items подменяется заготовками; generic query генерирует товары/цены | scraper.py:160–186,282+ | AP-004: live/cached/demo/empty/blocked/error раздельны, 0/1/2 реальных результата не подменяются |
| B02 OPEN | Server collector читает личные Windows cookies по жёсткому пути | scraper.py:get_zen_cookies | AP-006: portable source без личного browser profile |
| B03 NOT_VERIFIED | Допустимый способ сбора и доступ из Cloud.ru не подтверждены | Live проверка не выполнялась; старые debug files не доказывают текущий ответ | AP-006/012: выбран источник/лимиты, bounded authorized pilot; 403/429/CAPTCHA — остановка, не обход |
| B04 OPEN | Большая часть UI-фильтров и page/per_page не применяется | models.py, app.py max_items=7, scraper.py URL/apply_text_filters | AP-005: support matrix, рабочие активные поля, disabled неподдерживаемые, bounds/pagination/cache isolation |
| B05 OPEN | Внешний title/description/location/URL вставляется через innerHTML | static/app.js:174–214 | AP-008: text nodes/URL validation, внешний текст не исполняется |
| B06 OPEN | Тяжёлый /api/analyze без auth/общего job budget/bounded queue | app.py | AP-008: закрытый pilot, request/queue/concurrency/deadline/cancel/cleanup limits |
| B07 OPEN | Зависимости/portable package не готовы | requirements.in candidate; src содержит README | AP-002/003/009: pinned deps/browser build, package/assets/entrypoint и чистое окружение |
| B08 OPEN | AI client localhost:1234 не перенесётся автоматически на VM | analyzer.py; heuristic может восприниматься как AI | AP-007: явный disabled/heuristic режим без client либо отдельно выбранный inference; честная маркировка |
| B09 NOT_VERIFIED | Исправления/остановка browser jobs/безопасная выдача не проверены исполнением | Приложение/тесты NOT_RUN | AP-009 offline acceptance, затем отдельно разрешённый AP-012 pilot |
| B10 UNSELECTED | Domain/cloud project/VM/OS/budget/admin access не выбраны | Нет указанных ресурсов/домена | AP-010/011: точные configs/решения; расходы/DNS/deploy отдельно по поручению |
| B11 NOT_VERIFIED | HTTPS/renewal, restart, health/limits и rollback на VM не проверены | Нет развёртывания | AP-012: фактическое evidence по выбранной среде; HTTP health не равен scraping readiness |
| B12 OPEN для импорта кода | Права автора/LICENSE и чистый source allowlist требуют проверки | Public repo; исходники содержат личный путь | AP-001: подтвердить права, проверить/очистить исходники перед публикацией; профили/history/captures не публикуются |

B01/B02/B04/B05/B06 — наблюдаемые дефекты текущего source, не доказательство эксплуатации или атаки. NOT_VERIFIED/UNSELECTED — пробелы проверки/решения, не инцидент сервиса. Структурный перенос, commit или поднятый HTTP сервер сами по себе blockers не закрывают.

## Ближайшие шаги

Уточнение по заметкам пользователя: AP-014 устраняет несовпадение товара/цены/ссылки; AP-005 теперь включает реальный multi-page сбор; AP-013 добавляет фото, AP-015 — объяснимый ranking. Фото и ranking не нужны для технического запуска, но входят в желаемое развитие продукта. Сначала достоверность и coverage, затем рекомендации; «лучшее» ограничено собранной сравнимой выборкой.

1. С автором согласовать права на code publication и допустимый источник данных. Если источник недоступен — пересмотреть сценарий до аренды VM.
2. AP-001/002: clean allowlist import и воспроизводимое окружение. .gitignore не заменяет просмотр публикуемых файлов.
3. AP-003: механический package перенос отдельно от функциональных правок.
4. AP-004/005/006/008: честная выдача, фильтры, portable source, DOM и request limits. AP-007: explicit heuristic/disabled AI.
5. AP-009: поручение на offline приёмку; исходные live test_*.py автоматически не запускать.
6. AP-010/011: configs/домен/бюджет; затем конкретное поручение на AP-012 — закрытый Cloud.ru pilot.
7. После подтверждённого результата/rollback отдельно решить о public beta.

GPU/собственная LLM, Kubernetes, микросервисы, PostgreSQL/Redis, extension и SPA не обязательны для первого пилота. Достаточно полезного честного поиска; AI можно выключить. Статистика должна показывать sample size/дату/ограничения, не гарантированную прибыль.

Все задачи реализации пока To do. AP-000 Done — только подготовка документов/структуры. При закрытии blocker записать точный результат/проверку и остаточные ограничения.
