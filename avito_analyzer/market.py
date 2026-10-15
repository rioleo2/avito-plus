import math
import re
from typing import List

from models import ListingItem, MarketStats

# Слова в названии, по которым объявление — не сам товар, а аксессуар / запчасти / услуга / «куплю».
# Если такое слово есть в самом запросе, объявление не отсеиваем.
NOT_THE_PRODUCT = [
    r"чехол", r"кабель", r"зарядк", r"защитн", r"стекл", r"плёнк", r"пленк", r"подставк", r"сумк", r"рюкзак",
    r"наклейк", r"геймпад", r"джойстик", r"контроллер", r"\bдиск(и|ов)?\b", r"\bигр[аыу]\b", r"\bигры\b",
    r"запчаст", r"на детал", r"на разбор", r"разбор", r"ремонт", r"аренд", r"прокат", r"обмен", r"куплю",
    r"скупк", r"выкуп", r"корпус", r"материнск", r"плата\b", r"дисплей", r"аккумулятор", r"шлейф", r"кронштейн",
    r"крепление", r"коробка от", r"пустая коробка", r"макет", r"муляж",
]

# Цена ниже этой доли медианы — подозрительно (запчасти, обман, «цена от», предоплата)
SUSPICIOUS_RATIO = 0.4


def calculate_percentile(sorted_data: List[int], percentile: float) -> int:
    if not sorted_data:
        return 0
    k = (len(sorted_data) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return int(sorted_data[int(k)])
    return int(sorted_data[int(f)] * (c - k) + sorted_data[int(c)] * (k - f))


def mark_relevance(listings: List[ListingItem], query: str) -> None:
    """Помечает аксессуары, запчасти и услуги как нерелевантные — они портят статистику рынка."""
    q = query.lower()
    patterns = [p for p in NOT_THE_PRODUCT if not re.search(p, q)]
    for item in listings:
        title = item.title.lower()
        item.relevant = not any(re.search(p, title) for p in patterns)


def _robust_prices(listings: List[ListingItem]) -> List[int]:
    """Цены «настоящих» предложений рынка без выбросов (слишком дешёвых и слишком дорогих)."""
    prices = sorted(i.price for i in listings if i.relevant and not i.unavailable and i.price > 0)
    if len(prices) < 5:
        return prices
    q1, q3 = calculate_percentile(prices, 25), calculate_percentile(prices, 75)
    iqr = q3 - q1
    med = calculate_percentile(prices, 50)
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    kept = [p for p in prices if lo <= p <= hi and p >= SUSPICIOUS_RATIO * med]
    return kept or prices


def calculate_market_stats(listings: List[ListingItem]) -> MarketStats:
    """Вилка цен рынка по релевантным объявлениям без выбросов."""
    prices = _robust_prices(listings)
    if not prices:
        return MarketStats(total_listings=0, min_price=0, max_price=0, avg_price=0,
                           median_price=0, p25_price=0, p75_price=0, price_distribution=[])

    min_p, max_p = int(prices[0]), int(prices[-1])
    num_bins = 5
    if min_p == max_p or len(prices) < 3:
        bins = [{"range": f"{min_p:,} ₽".replace(",", " "), "count": len(prices)}]
    else:
        step = (max_p - min_p) / num_bins
        bins = []
        for i in range(num_bins):
            low = int(min_p + i * step)
            high = int(min_p + (i + 1) * step) if i < num_bins - 1 else max_p
            last = i == num_bins - 1
            count = sum(1 for p in prices if (low <= p <= high if last else low <= p < high))
            label = f"{low // 1000}k–{high // 1000}k ₽" if high >= 10000 else f"{low}–{high} ₽"
            bins.append({"range": label, "min": low, "max": high, "count": count})

    return MarketStats(
        total_listings=len(prices),
        min_price=min_p,
        max_price=max_p,
        avg_price=int(sum(prices) / len(prices)),
        median_price=calculate_percentile(prices, 50),
        p25_price=calculate_percentile(prices, 25),
        p75_price=calculate_percentile(prices, 75),
        price_distribution=bins,
    )


def evaluate_listing(item: ListingItem, stats: MarketStats) -> None:
    """
    Считает скидку к рынку, итоговый балл, вердикт и 1–10 рейтинг.
    Балл = скидка к медиане (в %, ограничена) − штрафы за риски + поправка за состояние по оценке ИИ.
    """
    from analyzer import fallback_heuristic_analysis  # локальный импорт: analyzer тянет openai

    if item.ai_analysis is None:
        item.ai_analysis = fallback_heuristic_analysis(item)
    ai = item.ai_analysis
    med = stats.median_price

    if med <= 0 or item.price <= 0:
        item.score, item.discount_pct = 0.0, None
        return

    disc = (med - item.price) / med * 100
    item.discount_pct = round(disc, 1)
    ai.estimated_profit = max(med - item.price, 0)

    # Подозрительно дешёвое: только если выборка рынка достаточная
    item.suspicious = stats.total_listings >= 5 and item.price < SUSPICIOUS_RATIO * med

    score = max(-40.0, min(45.0, disc))
    if ai.critical:
        score -= 30
    elif ai.risks_and_defects:
        score -= 3 * min(len(ai.risks_and_defects), 3)
    if ai.condition_score is not None:
        score += (ai.condition_score - 6) * 2
    if item.suspicious:
        score -= 60
    if not item.relevant or not ai.is_target:
        score -= 100
    if item.unavailable:
        score -= 100
    item.score = round(score, 1)

    ai.deal_rating = max(1, min(10, round(5 + score / 9)))

    if item.unavailable:
        ai.verdict = "🚫 Снято с публикации"
    elif not item.relevant or not ai.is_target:
        ai.verdict = "🧩 Не сам товар (аксессуар/запчасти)"
    elif item.suspicious:
        ai.verdict = "🚨 Подозрительно дёшево"
    elif ai.critical:
        ai.verdict = "⚠️ Есть серьёзные риски"
    elif disc >= 20:
        ai.verdict = "🔥 Топ сделка"
    elif disc >= 8:
        ai.verdict = "✅ Хорошая цена"
    elif disc >= -8:
        ai.verdict = "⚖️ Рыночная цена"
    else:
        ai.verdict = "📈 Дороже рынка"


def is_deal_candidate(item: ListingItem) -> bool:
    """Подходит ли объявление для списка «самые выгодные»."""
    ai = item.ai_analysis
    return bool(
        item.relevant
        and not item.unavailable
        and not item.suspicious
        and ai
        and ai.is_target
        and not ai.critical
        and (item.discount_pct or 0) >= 3
    )
