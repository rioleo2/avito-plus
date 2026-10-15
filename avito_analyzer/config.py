"""Настройки проекта. Любую можно переопределить переменной окружения."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Веб-сервер анализатора
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# LM Studio (OpenAI-совместимый сервер)
LM_BASE_URL = os.getenv("LM_BASE_URL", "http://127.0.0.1:1234/v1")
# Пусто — взять первую загруженную модель, которая не embedding
LM_MODEL = os.getenv("LM_MODEL", "")

# Куки Авито берём из профиля браузера Zen (чтобы Авито видел обычного пользователя)
ZEN_PROFILES_DIR = Path(os.getenv("ZEN_PROFILES_DIR", str(Path(os.getenv("APPDATA", "")) / "zen" / "Profiles")))

# Кэш выдачи, чтобы повторные запросы не долбили Авито и не ловили блокировку
CACHE_DIR = BASE_DIR / ".cache"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "1200"))

# Паузы между запросами к Авито (сек) — случайно в этом диапазоне
DELAY_PAGES = (3.0, 6.0)
DELAY_ITEMS = (2.0, 4.0)
