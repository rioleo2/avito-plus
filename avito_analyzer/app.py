import asyncio
import sys
import time
import uuid
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Предотвращение ошибок кодировки cp1251 в консоли Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import config
from analyzer import lm_status
from models import FilterParams, JobStatus
from pipeline import run_analysis
from scraper import AvitoBlocked, CityNotFound, resolve_city

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Avito Market AI Analyzer")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

JOBS: Dict[str, JobStatus] = {}
JOB_TIMES: Dict[str, float] = {}
JOB_TASKS: Dict[str, "asyncio.Task"] = {}
JOB_TTL = 3600
_run_lock = asyncio.Lock()  # один анализ за раз: Авито не любит параллельные запросы


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request, "index.html")


async def _run_job(job: JobStatus, params: FilterParams) -> None:
    async def progress(stage: str, pct: int) -> None:
        job.stage, job.progress = stage, max(job.progress, min(pct, 99))

    try:
        async with _run_lock:
            job.stage = "Запускаю браузер…"
            job.result = await run_analysis(params, progress)
        job.state, job.progress, job.stage = "done", 100, "Готово"
    except AvitoBlocked as e:
        job.state = "error"
        job.error = (
            f"Авито временно ограничил доступ с вашего IP ({e}). Это бывает после серии запросов подряд. "
            "Подождите 15–30 минут, не открывайте поиск в других местах, затем повторите. "
            "Повторные запросы с теми же параметрами берутся из кэша и Авито не нагружают."
        )
    except CityNotFound as e:
        job.state = "error"
        job.error = (
            f"Авито не знает город «{params.city}» (адрес {e}, ответ 404). Проверьте написание: "
            "например «Нижний Новгород», «Ростов-на-Дону». Можно ввести и адрес с Авито латиницей, например nizhniy_novgorod."
        )
    except asyncio.CancelledError:
        job.state, job.error, job.stage = "cancelled", None, "Отменено"
        raise
    except Exception as e:  # noqa: BLE001 — показываем пользователю любую причину
        print(f"[API] Ошибка анализа: {e!r}")
        job.state, job.error = "error", f"Не удалось выполнить анализ: {e}"


@app.post("/api/analyze", response_model=JobStatus)
async def start_analysis(params: FilterParams):
    now = time.time()
    for jid in [j for j, t in JOB_TIMES.items() if now - t > JOB_TTL]:
        JOBS.pop(jid, None)
        JOB_TIMES.pop(jid, None)
        JOB_TASKS.pop(jid, None)

    print(f"[API] Запрос на анализ: '{params.query}' в '{params.city}' ({resolve_city(params.city)}), страниц: {params.pages}")
    job = JobStatus(job_id=uuid.uuid4().hex[:12], stage="В очереди…")
    JOBS[job.job_id] = job
    JOB_TIMES[job.job_id] = now
    JOB_TASKS[job.job_id] = asyncio.create_task(_run_job(job, params))
    return job


@app.post("/api/jobs/{job_id}/cancel", response_model=JobStatus)
async def cancel_job(job_id: str):
    job, task = JOBS.get(job_id), JOB_TASKS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    job.state, job.stage = "cancelled", "Отменено"
    return job


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Задача не найдена (сервер перезапускали?)")
    return job


@app.get("/api/health")
async def health():
    ok, model = await asyncio.to_thread(lm_status)
    return {"status": "ok", "app": "Avito Market AI Analyzer", "lm_studio": ok, "model": model}


if __name__ == "__main__":
    import uvicorn

    # reload=False: на Windows с reload uvicorn переключается на Selector-луп, а Playwright нужен Proactor
    uvicorn.run("app:app", host=config.APP_HOST, port=config.APP_PORT, reload=False)
