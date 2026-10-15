"""Полный цикл: выдача Авито → рынок → проверка цен на страницах → ИИ → рейтинг выгодных."""
import asyncio
from contextlib import AsyncExitStack
from typing import Awaitable, Callable, List, Optional

import config
from analyzer import analyze_listing, fallback_heuristic_analysis, lm_status
from market import calculate_market_stats, evaluate_listing, is_deal_candidate, mark_relevance
from models import AnalysisResponse, FilterParams, ListingItem
from scraper import AvitoBlocked, AvitoScraper, _pause, apply_text_filters, load_cached_search, save_cached_search

ProgressCb = Callable[[str, int], Awaitable[None]]

BEST_DEALS_COUNT = 5
LLM_MAX_ITEMS = 6  # ~10 с на лот на локальной 7B-модели


async def _noop(stage: str, pct: int) -> None:
    pass


def _rank(listings: List[ListingItem]) -> List[ListingItem]:
    return sorted(listings, key=lambda i: i.score, reverse=True)


async def run_analysis(params: FilterParams, progress: Optional[ProgressCb] = None) -> AnalysisResponse:
    progress = progress or _noop
    warnings: List[str] = []

    async with AsyncExitStack() as stack:
        scraper = await stack.enter_async_context(AvitoScraper())

        # 1. Выдача Авито (несколько страниц), с кэшем на диске
        cached = load_cached_search(params) if params.use_cache else None
        if cached:
            listings, pages_done, age = cached
            await progress(f"Выдача взята из кэша ({age // 60} мин назад)", 35)
        else:
            try:
                listings, pages_done, warns = await scraper.search(params, progress)
                warnings += warns
                if listings:
                    save_cached_search(params, listings, pages_done)
            except AvitoBlocked as e:
                stale = load_cached_search(params, allow_stale=True)
                if not stale:
                    raise
                listings, pages_done, age = stale
                warnings.append(
                    f"Авито сейчас блокирует доступ ({e}). Показаны сохранённые данные {age // 60} мин назад — "
                    "цены могли измениться."
                )

        scraped_total = len(listings)
        listings = apply_text_filters(listings, params)
        if not listings:
            return AnalysisResponse(
                query=params.query, city=params.city, stats=calculate_market_stats([]), listings=[],
                pages_scraped=pages_done, scraped_total=scraped_total,
                warnings=warnings + ["По вашим фильтрам ничего не нашлось."],
            )

        # 2. Рынок: отсеиваем аксессуары/запчасти, считаем вилку цен, первичная оценка по эвристике
        await progress("Считаю рыночную вилку цен…", 40)
        mark_relevance(listings, params.query)
        stats = calculate_market_stats(listings)
        for item in listings:
            item.ai_analysis = fallback_heuristic_analysis(item)
            evaluate_listing(item, stats)

        # 3. Проверка лучших кандидатов на странице самого объявления (цена в выдаче бывает неверной)
        verified = 0
        candidates = [i for i in _rank(listings) if i.relevant and not i.unavailable][: params.verify_top]
        for n, item in enumerate(candidates, 1):
            await progress(f"Проверяю объявление {n} из {len(candidates)} на странице Авито…", 45 + int(30 * n / max(len(candidates), 1)))
            ok = await scraper.verify(item)
            if not ok:
                warnings.append(
                    "Авито начал блокировать открытие страниц объявлений — остальные цены не проверены, "
                    "помечены как «не проверено». Подождите 15–30 минут и повторите."
                )
                break
            if item.price_verified is not None:
                verified += 1
            item.ai_analysis = fallback_heuristic_analysis(item)  # описание могло стать полнее
            evaluate_listing(item, stats)
            if n < len(candidates):
                await _pause(config.DELAY_ITEMS)

        # 4. ИИ (LM Studio) — только для топа: на 150 объявлений локальная модель думала бы слишком долго
        llm_ok, model = lm_status()
        llm_used = False
        if not llm_ok:
            warnings.append(
                "LM Studio недоступен (сервер на :1234 не отвечает) — оценка только по правилам, без ИИ. "
                "Запустите LM Studio и включите сервер."
            )
        else:
            top = [i for i in _rank(listings) if i.relevant and not i.unavailable][:LLM_MAX_ITEMS]
            for n, item in enumerate(top, 1):
                await progress(f"ИИ ({model}) разбирает лот {n} из {len(top)}…", 78 + int(18 * n / max(len(top), 1)))
                analysis = await analyze_listing(item, params.query, stats)
                if analysis is None:
                    if n == 1:
                        warnings.append("LM Studio не ответил на запрос — остальное оценено по правилам.")
                        break
                    continue
                item.ai_analysis = analysis
                llm_used = True
                if not analysis.is_target:
                    item.relevant = False

        # Если ИИ вынес лот из «настоящих» — рынок пересчитываем уже без него
        stats = calculate_market_stats(listings)
        for item in listings:
            evaluate_listing(item, stats)

        # 5. Итог: сортировка по выгоде и топ лучших предложений
        await progress("Собираю итоговый рейтинг…", 97)
        ranked = _rank(listings)
        deals = [i for i in ranked if is_deal_candidate(i)]
        confirmed = [i for i in deals if i.price_verified is not None]
        best = confirmed[:BEST_DEALS_COUNT]
        if len(best) < min(3, len(deals)):
            best = (best + [i for i in deals if i not in best])[:BEST_DEALS_COUNT]
            warnings.append("Часть лучших предложений не удалось сверить на странице объявления — цена из выдачи.")

        return AnalysisResponse(
            query=params.query,
            city=params.city,
            stats=stats,
            listings=ranked,
            best_deals=[i.id for i in best],
            pages_scraped=pages_done,
            scraped_total=scraped_total,
            verified_count=verified,
            llm_used=llm_used,
            warnings=warnings,
        )
