# Что мешает первому локальному запуску

15.10.2026. Новый scope — Windows PC + LM Studio. Готовых install/start/stop ещё нет; runtime/tests NOT_RUN.

1. **Исходники недоступны GitHub-only Claude.** Передать app/models/scraper/analyzer/market и templates/static из авторской папки, без profiles/cookies/.env/history. Это вход для реализации, не необходимость cloud repo migration.
2. **Нет воспроизводимого setup и запуска одной кнопкой.** AP-016: project venv, browser dependency, bounded startup/port/repeat/stop, понятные ошибки.
3. **LM Studio interface не настроен.** AP-016: реальная model selection, localhost endpoint, timeout, сообщение о выключенном API, поиск без AI. Просто открытое окно LM Studio не гарантирует API server.
4. **Выдача может быть неподтверждённой.** AP-017/AP-004/014: убрать generated/curated fallback из real mode, согласовать title/price/listing URL, source/time.
5. **Мало карточек/игнорируемые фильтры.** AP-017/AP-005: bounded multi-page source collection, dedup/«Ещё», honest filters/total. Доступ источника реально не проверен.
6. **Безопасный local UI.** Внешний текст нельзя вставлять raw innerHTML; URL validation, небольшой лимит запросов/deadlines/cleanup нужны и локально. Bind только 127.0.0.1, без полного accounts/auth проекта.

Фото и ranking — следующие части AP-017. «Лучшее» только в собранной сравнимой выборке; unknown/малый sample не основание обещать прибыль.

Cloud.ru, домен, HTTPS, production operator gates, Docker/systemd, отдельные DB/queues и src-package refactor **не блокируют** этот local MVP. При 403/429/CAPTCHA honest source unavailable; личная cookie DB автоматически не читается. Live permission/доступ не заменяются выдуманными данными.

[Реализация для Claude](CLAUDE_LOCAL_MVP_PROMPT.md), [короткая спецификация](LOCAL_MVP.md), [канбан](../tasks/BOARD.md).
