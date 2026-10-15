# AP-016 — Windows запуск одной кнопкой + LM Studio

Priority: P0 LOCAL. Owner: UNASSIGNED. Status: NOT_STARTED.

Цель: один setup и ежедневные start/stop, loopback UI и понятное подключение к уже установленной LM Studio. Scope/AC — docs/LOCAL_MVP.md и docs/CLAUDE_LOCAL_MVP_PROMPT.md.

Входы: доступный авторский root source (AP-001), текущий код/config; Python/Windows версия уточняется только если реально мешает. AP-002 и AP-007 — детали этой работы, не обязательные отдельные циклы. AP-003 package migration не требуется.

Приёмка: повторяемый project-only setup, path с пробелами/кириллицей, repeat start/port conflict, bounded health, открытие браузера, stop только своих процессов; LM Studio unavailable/model selection/heuristic обозначены. Offline/mock checks отдельно от actual Windows/LM inference; последнее NOT_RUN до поручения. Здесь код/тесты/установка не выполнялись.
