import asyncio
import json
import re
from typing import Optional, Tuple

from openai import OpenAI

import config
from models import AIAnalysis, ListingItem, MarketStats

_client = OpenAI(base_url=config.LM_BASE_URL, api_key="lm-studio", timeout=90.0)
_model_cache: Optional[str] = None

SYSTEM_PROMPT = (
    "Ты опытный перекупщик и эксперт по технике на Авито. Оцениваешь объявления трезво и осторожно. "
    "Отвечай СТРОГО одним JSON-объектом без пояснений и без markdown."
)

PROMPT_TEMPLATE = """Искали: "{query}"

Объявление: "{title}"
Цена: {price} ₽
Рынок по этому запросу: медиана {median} ₽, выгодная граница {p25} ₽.
Описание: "{description}"

Верни JSON:
{{
  "is_target_product": true,
  "summary": "до 12 слов: что продают и в каком состоянии",
  "why_good": ["конкретный плюс из текста"],
  "defects": ["только НЕГАТИВНОЕ из текста: дефект, износ, неполный комплект"],
  "red_flags": ["признак обмана или серьёзной проблемы"],
  "condition_score": 7
}}

Правила:
- is_target_product = false, если это аксессуар, запчасти, игра/диск, аренда, услуга ремонта или «куплю».
- why_good — плюсы (комплект, гарантия, чек, состояние). В defects плюсы НЕ писать.
- red_flags: iCloud/MDM/блокировка, «на запчасти», не включается, предоплата без встречи, цена сильно ниже рынка без объяснения.
- Не выдумывай. Если в тексте нет — пустой список. Максимум 2 пункта в каждом списке, каждый до 8 слов.
- condition_score 1–10 по описанию состояния, не по цене."""

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "listing_analysis",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "is_target_product": {"type": "boolean"},
                "summary": {"type": "string"},
                "why_good": {"type": "array", "items": {"type": "string"}},
                "defects": {"type": "array", "items": {"type": "string"}},
                "red_flags": {"type": "array", "items": {"type": "string"}},
                "condition_score": {"type": "integer"},
            },
            "required": ["is_target_product", "summary", "why_good", "defects", "red_flags", "condition_score"],
        },
    },
}

# Критичные риски по тексту — работает и без ИИ
CRITICAL_PATTERNS = [
    r"на запчаст", r"на детал", r"на разбор", r"не включа", r"не работа", r"не заряжа", r"не загружа",
    r"разбит", r"трещин", r"залит", r"после воды", r"icloud\s*(лок|заблок)", r"залочен", r"заблокирован",
    r"\bmdm\b", r"id\s*заблок", r"без документов", r"предоплат", r"\bбитый\b", r"битые пиксел",
]
MINOR_PATTERNS = {
    r"царапин|потертост|потёртост|скол|вмятин": "Следы износа (царапины/потёртости)",
    r"замен(ен|ён|а\s)|после ремонт|вскрывал|паян": "Был ремонт или замена деталей",
    r"торг уместен|срочно": "Срочная продажа — можно торговаться",
    r"без короб|без чека|без зарядк|без док": "Неполный комплект",
}


def lm_status() -> Tuple[bool, str]:
    """Доступен ли сервер LM Studio и какая модель будет использоваться."""
    global _model_cache
    try:
        models = [m.id for m in _client.models.list(timeout=3).data]
    except Exception:
        _model_cache = None
        return False, ""
    chat = [m for m in models if "embed" not in m.lower()]
    if config.LM_MODEL and config.LM_MODEL in models:
        _model_cache = config.LM_MODEL
    elif chat:
        _model_cache = chat[0]
    else:
        _model_cache = None
        return False, ""
    return True, _model_cache


def extract_json_from_text(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None


def _ask_llm(item: ListingItem, query: str, stats: MarketStats) -> Optional[dict]:
    prompt = PROMPT_TEMPLATE.format(
        query=query,
        title=item.title,
        price=item.price,
        median=stats.median_price,
        p25=stats.p25_price,
        description=(item.full_description or item.description_snippet or "")[:1500],
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    kwargs = dict(model=_model_cache, messages=messages, temperature=0.1, max_tokens=300)
    try:
        resp = _client.chat.completions.create(response_format=RESPONSE_SCHEMA, **kwargs)
    except Exception:
        # Не все модели/версии LM Studio принимают json_schema — повторяем без него
        resp = _client.chat.completions.create(**kwargs)
    return extract_json_from_text(resp.choices[0].message.content or "")


def _as_list(v) -> list:
    return [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else []


def _sync_analyze(item: ListingItem, query: str, stats: MarketStats) -> Optional[AIAnalysis]:
    try:
        parsed = _ask_llm(item, query, stats)
    except Exception as e:
        print(f"[AI] Ошибка LM Studio для '{item.title[:40]}': {e}")
        return None
    if not parsed:
        return None

    red_flags = _as_list(parsed.get("red_flags"))
    defects = _as_list(parsed.get("defects"))
    heuristic = fallback_heuristic_analysis(item)
    try:
        cond = max(1, min(10, int(parsed.get("condition_score"))))
    except Exception:
        cond = None
    return AIAnalysis(
        summary=str(parsed.get("summary") or item.title),
        why_good=_as_list(parsed.get("why_good")),
        risks_and_defects=red_flags + [d for d in defects if d not in red_flags],
        extracted_specs=heuristic.extracted_specs,
        is_target=bool(parsed.get("is_target_product", True)),
        critical=bool(red_flags) or heuristic.critical,
        condition_score=cond,
        source="llm",
    )


async def analyze_listing(item: ListingItem, query: str, stats: MarketStats) -> Optional[AIAnalysis]:
    """Анализ через LM Studio. None — если ИИ не ответил (тогда остаётся эвристика)."""
    return await asyncio.to_thread(_sync_analyze, item, query, stats)


def fallback_heuristic_analysis(item: ListingItem) -> AIAnalysis:
    """Быстрый анализ без ИИ: характеристики и риски по ключевым словам."""
    text = (item.title + " " + item.full_description + " " + item.description_snippet).lower()
    specs, why_good, risks = {}, [], []

    for pat, label in ((r"\b(8|16|32|64)\s?(gb|гб)\b", "ram"),):
        m = re.search(pat, text)
        if m:
            specs[label] = f"{m.group(1)} GB"
    m = re.search(r"\b(128|256|512)\s?(gb|гб)\b|\b(1|2)\s?(tb|тб)\b", text)
    if m:
        specs["ssd"] = f"{m.group(1)} GB" if m.group(1) else f"{m.group(3)} TB"
    m = re.search(r"(?:акб|аккумулятор|батаре\w*|battery)\D{0,15}(\d{2,3})\s*%", text) or re.search(r"(\d{2,3})\s*%\s*(?:акб|аккумулятор)", text)
    if m:
        pct = int(m.group(1))
        specs["battery"] = f"{pct}%"
        if pct >= 88:
            why_good.append(f"Хорошая батарея: {pct}%")
        elif pct < 80:
            risks.append(f"Износ батареи ({pct}%)")
    if re.search(r"полный комплект|коробк", text) and not re.search(r"без короб", text):
        specs["kit"] = "Коробка/комплект"
        why_good.append("Заявлен полный комплект")
    if re.search(r"гарант", text):
        why_good.append("Есть гарантия")
    if re.search(r"чек", text) and not re.search(r"без чека", text):
        why_good.append("Есть чек")

    critical = False
    for pat in CRITICAL_PATTERNS:
        m = re.search(pat, text)
        if m:
            critical = True
            risks.append(f"Красный флаг в тексте: «{m.group(0).strip()}»")
            break
    for pat, label in MINOR_PATTERNS.items():
        if re.search(pat, text):
            risks.append(label)

    return AIAnalysis(
        summary=item.title,
        why_good=why_good,
        risks_and_defects=risks,
        extracted_specs=specs,
        critical=critical,
        source="heuristic",
    )
