> Обновление 15.10.2026: текущий scope — [локальный MVP](LOCAL_MVP.md). Этот документ сохраняет исходные наблюдения/план. Облако, package перенос и multiuser требования не являются условиями первого локального запуска.

# Целевая структура

Создан каркас документов и директорий. Файлы app.py/models.py/scraper.py/analyzer.py/market.py/templates/static остаются в исходном месте до AP-003.

```text
README.md, AGENTS.md, .gitignore, .dockerignore, .env.example
requirements.in                    кандидат; lock после выбора окружения
pyproject.toml                     появится при пакетировании AP-003
src/avito_plus/
  app.py                           FastAPI entrypoint
  models.py                        контракты запроса/выдачи
  scraper.py                       сначала без раздробления на 10 модулей
  analyzer.py                      optional AI / explicit heuristic mode
  market.py                        статистика наблюдаемой выборки
  settings.py                      централизованная конфигурация
  templates/index.html
  static/app.js
tests/
  unit/                            без сети/браузера/AI
  integration/                     API с подставным source/analyzer
  fixtures/                        только synthetic/sanitized
tools/manual/                      бывшие live experiments после очистки
infrastructure/
  README.md                        выбранная топология
  templates/                       будущие Docker/systemd/proxy configs
docs/
  BASELINE.md, MIGRATION.md, DEPLOYMENT.md, DECISIONS.md
  SOURCE_MANIFEST.json              hashes только разрешённых исходников
tasks/
  BOARD.md, TEMPLATE.md
  to-do/AP-*.md
  in-progress/
  done/AP-000.md
```

Не создавать отдельный SPA/Node build ради переноса. Сохранить GET /, POST /api/analyze, GET /api/health и пути /static, пока отдельная задача не изменит контракт. Playwright — source adapter, не часть UI. Browser profiles/data/logs лежат вне source tree и репозитория.

PostgreSQL/Redis/отдельная очередь не обязательны для закрытого однопользовательского пилота. Очередь/shared cache добавляются при реальном multiuser спросе и измеренной конкуренции. In-memory cache не общий между процессами и не ограничивает их суммарную нагрузку.
