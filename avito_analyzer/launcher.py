"""
Одна кнопка: проверяет зависимости → поднимает LM Studio и его сервер → запускает сайт → открывает браузер.
Запуск: двойной клик по start.bat (или `python launcher.py`).
"""
import importlib.util
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402

LM_MODELS_URL = config.LM_BASE_URL.rstrip("/") + "/models"
APP_URL = f"http://{config.APP_HOST}:{config.APP_PORT}"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def say(msg: str) -> None:
    print(f"[Запуск] {msg}", flush=True)


def http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def wait_for(url: str, seconds: int) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if http_ok(url):
            return True
        time.sleep(1.5)
    return False


# --- 1. Зависимости ---------------------------------------------------------

def ensure_dependencies() -> None:
    needed = {"fastapi": "fastapi", "uvicorn": "uvicorn", "jinja2": "jinja2", "openai": "openai", "playwright": "playwright"}
    if any(importlib.util.find_spec(mod) is None for mod in needed):
        say("Ставлю недостающие Python-пакеты (один раз)…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # Браузер Firefox для Playwright
    ms_playwright = Path(os.getenv("LOCALAPPDATA", "")) / "ms-playwright"
    if not list(ms_playwright.glob("firefox-*")):
        say("Скачиваю Firefox для Playwright (один раз, ~80 МБ)…")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "firefox"])


# --- 2. LM Studio -----------------------------------------------------------

def find_lmstudio_exe() -> Path | None:
    candidates = []
    if os.getenv("LMSTUDIO_EXE"):
        candidates.append(Path(os.environ["LMSTUDIO_EXE"]))
    path_file = BASE_DIR / "lmstudio_path.txt"
    if path_file.exists():
        candidates.append(Path(path_file.read_text(encoding="utf-8").strip().strip('"')))
    local = Path(os.getenv("LOCALAPPDATA", ""))
    candidates += [
        local / "Programs" / "LM Studio" / "LM Studio.exe",
        Path(os.getenv("ProgramFiles", "")) / "LM Studio" / "LM Studio.exe",
    ]
    return next((c for c in candidates if c and c.is_file()), None)


def ensure_lmstudio() -> None:
    if http_ok(LM_MODELS_URL):
        say("LM Studio уже работает — сервер отвечает.")
        return

    # Если установлен CLI `lms` — он умеет сам запускать сервер
    lms = Path.home() / ".lmstudio" / "bin" / ("lms.exe" if sys.platform == "win32" else "lms")
    exe = find_lmstudio_exe()
    if exe:
        say(f"Запускаю LM Studio: {exe}")
        subprocess.Popen([str(exe)], cwd=str(exe.parent), creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
        time.sleep(6)
    else:
        say("Не нашёл LM Studio. Укажите путь к .exe в файле lmstudio_path.txt (см. README) или запустите его вручную.")

    if lms.exists():
        subprocess.run([str(lms), "server", "start"], check=False, capture_output=True)

    say("Жду сервер LM Studio (до 2 минут)…")
    if wait_for(LM_MODELS_URL, 120):
        say("Сервер LM Studio отвечает.")
    else:
        say(
            "Сервер LM Studio не ответил. Откройте LM Studio → вкладка Developer → Start Server "
            "и загрузите модель. Сайт всё равно откроется — оценка будет без ИИ."
        )


# --- 3. Сайт ----------------------------------------------------------------

def run_site() -> int:
    if http_ok(APP_URL + "/api/health"):
        say("Сайт уже запущен — открываю.")
        webbrowser.open(APP_URL)
        return 0

    say("Запускаю сайт…")
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=str(BASE_DIR))
    try:
        if not wait_for(APP_URL + "/api/health", 40):
            say("Сайт не поднялся за 40 секунд — смотрите ошибки выше.")
            proc.terminate()
            return 1
        say(f"Готово: {APP_URL}  (закройте это окно или нажмите Ctrl+C, чтобы остановить)")
        webbrowser.open(APP_URL)
        return proc.wait()
    except KeyboardInterrupt:
        say("Останавливаю сайт…")
        proc.terminate()
        return 0


def main() -> int:
    ensure_dependencies()
    ensure_lmstudio()
    return run_site()


if __name__ == "__main__":
    sys.exit(main())
