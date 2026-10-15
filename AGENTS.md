# Avito Plus — локальный MVP

Проект самостоятельный. Текущая цель — один Windows PC, LM Studio, установка один раз и запуск одной кнопкой. docs/LOCAL_MVP.md и AP-016/AP-017 заменяют прежние cloud-first scope/dependencies. Обычные технические решения принимай сам; спрашивай лишь при реальном blocker/недостающих исходниках или новых внешних полномочиях.

- Перед изменениями прочитай задачу и фактический root source. Сохраняй чужую работу; не рефакторить в src/SPA/services без необходимости.
- Канбан to-do → in-progress → done; папка определяет статус, BOARD — навигация. Не считать опубликованный prompt реализацией.
- LM Studio запускает/настраивает пользователь. Не скачивать модели, не подключать платный API, не убивать чужие процессы. Bind app/API только loopback; app-owned children cleanup.
- Не импортировать/публиковать profiles/cookies/history/real env/keys/captures, не копировать личные cookie базы автоматически. Первичный source import явным allowlist, не git add .
- Live Avito/browser/AI checks отдельно от offline. Исходные test_*.py не запускать автоматически. При 403/429/CAPTCHA остановка/честный статус, без обходов.
- Real/cached/demo/heuristic различимы; ошибка не генерирует fake cards. Внешний текст/AI output — недоверенные данные, безопасный DOM/URLs.
- Минимальные request/concurrency/time limits и cross-origin restrictions сохранить. Не строить multiuser auth, Docker/systemd/cloud/DB ради localhost MVP.
- Тестирование по явному поручению; промпт реализации разрешает offline/mock проверки своих изменений. Реальный inference/source requests и установки — только в указанном scope. Честно отмечать NOT_RUN.
- Не публиковать/merge/создавать cloud resources/домен/расходы и не писать людям без поручения. Документационная публикация не реализует launcher.
