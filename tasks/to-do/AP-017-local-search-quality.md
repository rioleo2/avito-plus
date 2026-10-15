# AP-017 — полезная локальная выдача

Priority: P0 LOCAL. Owner: UNASSIGNED. Status: NOT_STARTED.

Цель: достоверные real listings, multi-page поиск, фото и объяснимое ranking без серверной инфраструктуры. AP-004/005/006/008/013/014/015 сохраняют детали; это единый продуктовый этап, не очередь из обязательных micro-PR.

Входы: авторский root source; AP-016 для удобной ручной приёмки. Разрешённый source scenario, без автоматического извлечения личных cookies. AP-003/010/011/012 не зависимости.

Приёмка: нет fake fallback; ID/цена/ссылка согласованы; несколько реальных страниц/dedup/bounds; unsupported filters не обещаются; безопасные фото/DOM; ranking среди сравнимой собранной выборки и честный insufficient-data. Ошибки/403/429/CAPTCHA не обходятся и не маскируются. Offline fixtures не подтверждают actual live source. Код/проверки NOT_RUN.
