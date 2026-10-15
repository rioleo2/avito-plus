> Обновление 15.10.2026: текущий scope — [локальный MVP](LOCAL_MVP.md). Этот документ сохраняет исходные наблюдения/план. Облако, package перенос и multiuser требования не являются условиями первого локального запуска.

# Исходный аудит, 15.10.2026

Проверка статическая: Python/JS/HTML прочитаны, live скрипты и приложение не запускались. Локальный каталог не Git checkout. Remote metadata: rioleo2/avito-plus public, size=0, default branch main. Metadata не доказывает конкретное состояние branch/commit.

| Наблюдение | Основание | Следствие / задача |
|---|---|---|
| Веб-приложение, не расширение | app.py FastAPI + templates/static; пользователь подтвердил формат | Сначала web MVP |
| Runtime-зависимости не закреплены | В корне нет requirements/pyproject до подготовки | AP-002 |
| AI зависит от localhost:1234 | analyzer.py создаёт OpenAI-compatible client при импорте, local-model | На ВМ модель отсутствует; AP-007 |
| Чтение личных cookies из Windows | scraper.py get_zen_cookies копирует SQLite профиля пользователя | Не переносить профиль/жёсткий путь; AP-006 |
| Сбой или <3 live listings заменяются curated dataset | scraper.py:160–186 | Нельзя выдавать fallback за свежий поиск; AP-004 |
| Generic query создаёт gen-* объявления/цены | scraper.py:282+ | Только явно отмеченный demo mode, не live result |
| Город переписывается в fallback без изменения исходных московских ссылок | get_curated_real_listings | Недостоверная локация; отключить fallback для real выдачи |
| Большинство фильтров пока не применяются | URL использует query/city; apply_text_filters — цена и включение/исключение слов | Radius/seller/rating/delivery и другие нельзя обещать; AP-005 |
| Pagination не связана с выдачей | app.py max_items=7; response pagination defaults, params page/per_page не используются | AP-005 |
| Cache key ограничен query/city, нет max size | scraper.py _cache | Уточнить raw vs filtered cache, все source-affecting поля, TTL/лимит, mutation isolation |
| Внешний текст вставляется в innerHTML | static/app.js:174–214 title/description/location/url | XSS/unsafe URLs исправить до общего доступа; AP-008 |
| Публичный POST может запускать браузер/AI без auth/лимитов | app.py /api/analyze | Закрытый пилот, concurrency/queue/timeout/rate limits; AP-008 |
| Статистика по малой/неоднородной выборке | market.py + всего до 7 live items | Показывать sample size/дату/качество, не весь рынок/гарантированную прибыль |
| Heuristic считает отсутствие найденных рисков хорошей ценой | analyzer.py fallback | Отсутствие признака не доказательство; маркировать heuristic и неопределённость |
| UI использует внешние CDN, lucide@latest | templates/index.html | Закрепить/self-host assets и учесть CSP/доступность |
| test_*.py — эксперименты с сетью/браузерами/AI | AST imports/calls | Перенести после ревизии в tools/manual, не считать offline suite |

Содержимое cookies/history/browser storage/debug HTML/JSON не исследовалось. Профили могут содержать сессии и личные данные: в public Git и образ они не входят. Сам .gitignore не исправляет уже опубликованные secrets; до публикации нужен staged allowlist review. Полноценный secret audit не выполнен.
