# План Cloud.ru + домен

Status PLAN / NOT_DEPLOYED, 15.10.2026. Домен, VM/project/region, бюджет, владелец DNS и выбранный source mode пока UNKNOWN. Ресурсы не арендовались, DNS/сертификаты/ВМ не менялись.

## Топология MVP

```text
браузер → HTTPS домен → reverse proxy → FastAPI/Uvicorn на loopback
                                      ↓
                            ограниченный source adapter
                                      ↓
                        optional AI / explicit heuristic
```

Предлагается одна Linux VM Cloud.ru Evolution, выделенный непривилегированный service user, Python venv + systemd и Caddy либо Nginx как TLS proxy. Docker Compose — альтернатива, когда появится проверенный image; не вести сразу два способа deploy. Kubernetes, отдельная БД и load balancer для первого пилота не нужны.

Начальная оценка для web + одного browser job без LLM: 2 vCPU, 4 GB RAM, 30–40 GB SSD. Это гипотеза для замеров, не гарантированная ёмкость. При нескольких браузерах ресурсы могут потребоваться больше. Начать с одного Uvicorn worker и одного общего concurrency budget; cache/semaphore не общий между workers. GPU/LLM VM не выбирать до решения о модели/измерения памяти.

## Этап A — решения до покупки

Выбрать собственный домен/поддомен и независимый cloud project, регион/зону, OS, SSH public key/admin source IP, расходы/месячный предел и способ оплаты. Проверить текущий калькулятор Cloud.ru: compute + disk + public IP + traffic + backups/domain, optional inference отдельно. Цены в этом плане не рассчитаны и не обещается free tier.

Выбрать допустимый источник объявлений. Успех доступа с домашнего ПК не доказывает доступ из cloud IP. Если доступ ограничен, public pilot блокируется до согласованного способа, а не маскируется demo-выдачей.

## Этап B — VM и сеть (будущее поручение)

Создать VM и public IP, security group: SSH только с admin IP/VPN, 80/443 для web; 8000 и AI port не открывать в интернет. Разрешить требуемый исходящий DNS/HTTPS/обновления. SSH fingerprint проверить по доверенному каналу; не отключать host-key checking. На VM отдельный user, обновления, ограничение journald/log retention, resource/process bounds.

Официальные инструкции: [создание VM](https://cloud.ru/docs/virtual-machines/ug/topics/guides__create-vm), [public IP](https://cloud.ru/docs/public-ip/ug/topics/guides__allocate-ip). Выбор сети/прав проверяется по фактической конфигурации аккаунта.

## Этап C — закрытый staging

Развернуть pinned commit/artifact в /opt/avito-plus/releases/<release-id>, venv/browser binaries отдельно от request path. Secrets вне Git, файл конфигурации с ограниченным доступом. Рабочие data/cache/logs — /var/lib/avito-plus и journald с retention. Не копировать реальные browser profiles с ПК. Перед первым source request проверить отключение demo fallback, AI mode и лимиты.

Запуск будущего package: uvicorn avito_plus.app:app --host 127.0.0.1 --port 8000 --workers 1. Без reload. Proxy headers принимать только от доверенного loopback proxy. Это иллюстрация после AP-003, не готовая команда для текущих root sources. У systemd: отдельный user, Restart/on-failure с ограничением, рабочая директория, environment file, остановка browser children при restart, таймауты и MemoryMax/TasksMax под измеренный профиль. Точные units/paths на AP-010.

До публичного доступа — auth или IP allowlist на proxy. /api/health текущего кода проверяет только HTTP handler, не scraping/AI. Нужен отдельный статус зависимостей без запуска тяжёлого поиска на health check. Обязательны deadline/cancel/cleanup, bounded waiting queue и отказ при перегрузке; один semaphore не ограничивает количество ожидающих клиентов.

## Этап D — DNS и HTTPS

В авторитетной DNS-зоне добавить A на выбранный public IP; AAAA только при реальной IPv6 настройке. Если выбран Cloud DNS — делегировать зону по инструкции/выданным NS, сохранив существующие MX/TXT записи. Перенос nameservers не обязателен: можно оставить текущий DNS provider. Пример имени: app.example.org, это не зарегистрированный домен проекта.

[Cloud DNS records](https://cloud.ru/docs/clouddns/ug/topics/concepts__resource-record). HTTPS завершает proxy; настроить автоматическое продление и HTTP→HTTPS redirect. [FastAPI HTTPS](https://fastapi.tiangolo.com/deployment/https/) описывает эту схему. Для браузерного фронтенда оставить same-origin API, CORS wildcard не нужен.

## Этап E — пилот и rollback

По отдельному поручению проверить health/UI/static, разрешённый реальный запрос, source-blocked/empty/cached состояния, concurrent overload, AI timeout, перезапуск и прекращение browser jobs, отсутствие secrets в logs. Отдельно оценить доступ из cloud IP и длительность/RAM одного job. TLS/renewal и внешняя доступность проверяются по фактическому домену. Пока всё NOT_RUN.

Расширять доступ только после gates AP-004…009. Rollback: остановить приём новых jobs, дождаться/завершить их штатно, переключить release на предыдущий pinned artifact, проверить lightweight health/UI. Не заменять source identity плавающей веткой; env/config version согласованы с rollback. Не удалять пользовательские данные при откате.

Backup нужен для конфигурации/сохранённых пользовательских поисков, если они появятся; executable source восстанавливается из Git/artifact. Настроить retention, шифрование и пробу восстановления по выбранному scope. Сырые listing pages/history/cookies по умолчанию не хранить. Хранение данных пользователей/аналитика требуют отдельно выбранной privacy/retention политики.

## Условия допуска

Нет личных cookie зависимостей; live/demo/error различимы; применяемые фильтры честные; input/DOM безопасны; request/concurrency/time limits работают; AI отключаем; чистый release/reproducible deps; auth пилота; approved cloud budget/domain; выбран допустимый источник. Если источник из Cloud.ru не работает — сервер может быть технически поднят, но сервис поиска не считается работающим.
