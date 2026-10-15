import asyncio
import hashlib
import json
import os
import random
import re
import shutil
import sqlite3
import tempfile
import time
import urllib.parse
from typing import Awaitable, Callable, List, Optional, Tuple

import config
from models import FilterParams, ListingItem

# Популярные города: название (нижний регистр, «е» вместо «ё») -> адрес на Авито.
# Остальные города переводятся транслитерацией (см. resolve_city), поэтому вводить можно любой.
KNOWN_CITIES = {
    "москва": "moskva",
    "санкт-петербург": "sankt-peterburg", "спб": "sankt-peterburg", "питер": "sankt-peterburg", "петербург": "sankt-peterburg",
    "екатеринбург": "ekaterinburg", "новосибирск": "novosibirsk", "казань": "kazan",
    "нижний новгород": "nizhniy_novgorod", "самара": "samara", "челябинск": "chelyabinsk", "омск": "omsk",
    "ростов-на-дону": "rostov-na-donu", "уфа": "ufa", "красноярск": "krasnoyarsk", "воронеж": "voronezh",
    "пермь": "perm", "волгоград": "volgograd", "краснодар": "krasnodar", "саратов": "saratov",
    "тюмень": "tyumen", "тольятти": "tolyatti", "ижевск": "izhevsk", "барнаул": "barnaul",
    "ульяновск": "ulyanovsk", "иркутск": "irkutsk", "хабаровск": "habarovsk", "ярославль": "yaroslavl",
    "владивосток": "vladivostok", "махачкала": "mahachkala", "томск": "tomsk", "оренбург": "orenburg",
    "кемерово": "kemerovo", "новокузнецк": "novokuznetsk", "рязань": "ryazan", "набережные челны": "naberezhnye_chelny",
    "астрахань": "astrahan", "пенза": "penza", "липецк": "lipetsk", "киров": "kirov", "тула": "tula",
    "калининград": "kaliningrad", "курск": "kursk", "сочи": "sochi", "ставрополь": "stavropol",
    "севастополь": "sevastopol", "симферополь": "simferopol", "балашиха": "balashiha", "мурманск": "murmansk",
    "тверь": "tver", "иваново": "ivanovo", "белгород": "belgorod", "владимир": "vladimir", "чебоксары": "cheboksary",
    "россия": "rossiya", "вся россия": "rossiya", "по всей россии": "rossiya",
}

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y",
    "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def resolve_city(text: str) -> str:
    """Название города, написанное как угодно, -> адрес города на Авито (moskva, nizhniy_novgorod…)."""
    t = re.sub(r"\s+", " ", (text or "").strip().lower().replace("ё", "е"))
    t = re.sub(r"^(г\.?|город)\s+", "", t)
    if not t:
        return "moskva"
    if t in KNOWN_CITIES:
        return KNOWN_CITIES[t]
    if re.fullmatch(r"[a-z0-9_\-]+", t):  # уже адрес на латинице, например «nizhniy_novgorod»
        return t
    slug = "".join(_TRANSLIT.get(ch, ch) for ch in t.replace(" ", "_"))
    return re.sub(r"[^a-z0-9_\-]", "", slug) or "moskva"


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"

ProgressCb = Callable[[str, int], Awaitable[None]]


class AvitoBlocked(Exception):
    """Авито отдал капчу / 403 / 429."""


class CityNotFound(Exception):
    """Авито не знает такого адреса города (404)."""


# ---------------------------------------------------------------------------
# Куки из профиля Zen
# ---------------------------------------------------------------------------

def _read_avito_cookies(cookie_db: str) -> List[dict]:
    tmp_dir = tempfile.mkdtemp(prefix="zen_cookies_")
    try:
        # Копируем БД вместе с WAL — свежие куки часто лежат только там
        for suffix in ("", "-wal", "-shm"):
            src = cookie_db + suffix
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(tmp_dir, "cookies.sqlite" + suffix))
        conn = sqlite3.connect(os.path.join(tmp_dir, "cookies.sqlite"))
        try:
            rows = conn.execute(
                "SELECT host, name, value, path, isSecure, isHttpOnly FROM moz_cookies WHERE host LIKE ?",
                ("%avito.ru%",),
            ).fetchall()
        finally:
            conn.close()
        return [
            {"name": r[1], "value": r[2], "domain": r[0], "path": r[3], "secure": bool(r[4]), "httpOnly": bool(r[5])}
            for r in rows
        ]
    except Exception as e:
        print(f"[Scraper] Не удалось прочитать куки Zen ({cookie_db}): {e}")
        return []
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def get_zen_cookies() -> List[dict]:
    """Куки Авито из того профиля Zen, где их больше всего."""
    best: List[dict] = []
    if not config.ZEN_PROFILES_DIR.exists():
        return best
    for profile in config.ZEN_PROFILES_DIR.iterdir():
        db = profile / "cookies.sqlite"
        if db.exists():
            cookies = _read_avito_cookies(str(db))
            if len(cookies) > len(best):
                best = cookies
    return best


# ---------------------------------------------------------------------------
# JS-извлечение карточек из выдачи и данных со страницы объявления
# ---------------------------------------------------------------------------

EXTRACT_CARDS_JS = r"""
() => {
  const num = v => { const d = String(v || '').replace(/[^\d]/g, ''); return d ? parseInt(d, 10) : 0; };
  const biggest = srcset => {
    if (!srcset) return null;
    let best = null, bw = -1;
    srcset.split(',').forEach(part => {
      const m = part.trim().match(/^(\S+)\s+(\d+)w$/);
      if (m && +m[2] > bw) { bw = +m[2]; best = m[1]; }
    });
    return best;
  };
  const out = [];
  document.querySelectorAll('[data-marker="item"]').forEach(it => {
    const q = s => it.querySelector(s);
    const a = q('a[data-marker="item-title"]');
    if (!a) return;
    const href = (a.getAttribute('href') || '').split('?')[0];
    if (!href) return;
    const idm = href.match(/_(\d+)$/);
    const id = it.getAttribute('data-item-id') || (idm ? idm[1] : href);

    let price = num(q('meta[itemprop="price"]')?.content);
    if (!price) price = num(q('[data-marker="item-price"]')?.innerText);

    // Фото: кадры слайдера; для каждого берём самый крупный вариант из srcset, если он уже подгружен
    const images = [];
    it.querySelectorAll('[data-marker^="slider-image/image-"]').forEach(li => {
      const marker = li.getAttribute('data-marker').slice('slider-image/image-'.length);
      const u = biggest(li.querySelector('img')?.getAttribute('srcset')) || marker;
      if (u.startsWith('http')) images.push(u);
    });
    if (!images.length) {
      const main = q('img[itemprop="image"]');
      const u = biggest(main?.getAttribute('srcset')) || main?.getAttribute('src');
      if (u && u.startsWith('http')) images.push(u);
    }

    const text = it.innerText || '';
    const lines = text.split('\n').map(s => s.trim()).filter(Boolean);
    const dateRe = /^(\d+\s+\S+\s+назад|вчера.*|сегодня.*|только что|\d+\s+\S+\s+\d{1,2}:\d{2})$/i;
    const dateIdx = lines.findIndex(l => dateRe.test(l));
    const dateEl = q('[data-marker="item-date"]');
    const date = (dateEl?.innerText || (dateIdx >= 0 ? lines[dateIdx] : '')).trim();
    const seller = dateIdx >= 0 && lines[dateIdx + 1] ? lines[dateIdx + 1] : '';

    const descEl = q('div[class*="bottomBlock"] p') || q('[class*="ivaItemRedesign"] p');
    let desc = descEl ? descEl.innerText : '';
    if (!desc) {
      const ps = [...it.querySelectorAll('p')].map(p => p.innerText.trim()).sort((x, y) => y.length - x.length);
      desc = ps[0] || '';
    }
    const loc = (q('[data-marker="item-location"]') || q('[class*="geo-root"]'))?.innerText || '';
    // Собственная оценка цены от Авито («Рыночная цена», «Цена ниже рынка» и т.п.)
    const badge = lines.find(l => /(рыночная цена|ниже рынка|выше рынка|хорошая цена|низкая цена)/i.test(l)) || '';

    out.push({
      id: String(id), title: a.innerText.trim(), href, price, images,
      date, seller,
      desc: desc.replace(/\s+/g, ' ').trim(),
      loc: loc.replace(/\s+/g, ' ').trim(),
      badge,
    });
  });
  return out;
}
"""

ITEM_PAGE_JS = r"""
() => {
  const num = v => { const d = String(v || '').replace(/[^\d]/g, ''); return d ? parseInt(d, 10) : 0; };
  let price = 0;
  const pe = document.querySelector('[data-marker="item-view/item-price"]');
  price = num(pe?.getAttribute('content')) || num(document.querySelector('meta[itemprop="price"]')?.content);
  if (!price) {
    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
      try {
        const j = JSON.parse(s.textContent);
        const arr = Array.isArray(j) ? j : [j];
        for (const o of arr) { const p = o?.offers?.price ?? o?.offers?.[0]?.price; if (p) { price = num(p); break; } }
      } catch (e) {}
      if (price) break;
    }
  }
  if (!price) price = num(pe?.innerText);
  const desc = document.querySelector('[data-marker="item-view/item-description"]')?.innerText || '';
  const head = (document.body.innerText || '').slice(0, 6000);
  const closed = !!document.querySelector('[data-marker="item-view/closed-warning"]')
    || /снято с публикации|объявление закрыто|объявление не найдено|страница не найдена/i.test(head);
  const images = [];
  document.querySelectorAll('[data-marker="image-frame/image-wrapper"] img, [data-marker="item-view/gallery"] img').forEach(i => {
    const u = i.getAttribute('src');
    if (u && u.startsWith('http') && !images.includes(u)) images.push(u);
  });
  return { price, desc: desc.replace(/\s+/g, ' ').trim(), closed, images: images.slice(0, 8), title: document.title };
}
"""


# ---------------------------------------------------------------------------
# Кэш выдачи на диске
# ---------------------------------------------------------------------------

def _cache_path(params: FilterParams) -> str:
    key = json.dumps(
        [params.query.strip().lower(), resolve_city(params.city), params.pages, params.price_from, params.price_to,
         params.seller_type, params.delivery],
        ensure_ascii=False,
    )
    return str(config.CACHE_DIR / (hashlib.md5(key.encode("utf-8")).hexdigest() + ".json"))


def load_cached_search(params: FilterParams, allow_stale: bool = False) -> Optional[Tuple[List[ListingItem], int, int]]:
    """Возвращает (объявления, страниц, возраст кэша в секундах) или None."""
    path = _cache_path(params)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        age = int(time.time() - data["ts"])
        if age > config.CACHE_TTL_SECONDS and not allow_stale:
            return None
        return [ListingItem(**x) for x in data["items"]], data["pages"], age
    except Exception:
        return None


def save_cached_search(params: FilterParams, items: List[ListingItem], pages: int) -> None:
    try:
        config.CACHE_DIR.mkdir(exist_ok=True)
        with open(_cache_path(params), "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "pages": pages, "items": [i.model_dump() for i in items]}, f, ensure_ascii=False)
    except Exception as e:
        print(f"[Scraper] Не удалось записать кэш: {e}")


# ---------------------------------------------------------------------------
# Сборщик
# ---------------------------------------------------------------------------

def build_search_url(params: FilterParams, page_no: int) -> str:
    city_slug = resolve_city(params.city)
    query = {"q": params.query.strip()}
    if page_no > 1:
        query["p"] = str(page_no)
    if params.price_from:
        query["pmin"] = str(params.price_from)
    if params.price_to:
        query["pmax"] = str(params.price_to)
    if params.seller_type == "private":
        query["user"] = "1"
    elif params.seller_type == "company":
        query["user"] = "2"
    if params.delivery:
        query["d"] = "1"
    return f"https://www.avito.ru/{city_slug}?" + urllib.parse.urlencode(query)


def _is_blocked(status: Optional[int], title: str, html: str) -> bool:
    return (
        status in (403, 429)
        or "Доступ ограничен" in title
        or "проблема с IP" in title
        or ("Доступ ограничен" in html[:5000])
    )


async def _pause(rng: Tuple[float, float]) -> None:
    await asyncio.sleep(random.uniform(*rng))


class AvitoScraper:
    """Один браузер на весь запрос: выдача по страницам + проверка карточек."""

    def __init__(self) -> None:
        self._pw = None
        self._browser = None
        self._ctx = None
        self.blocked = False

    async def __aenter__(self) -> "AvitoScraper":
        from playwright.async_api import async_playwright

        self._pw = await async_playwright().start()
        self._browser = await self._pw.firefox.launch(headless=True)
        self._ctx = await self._browser.new_context(
            user_agent=UA, locale="ru-RU", viewport={"width": 1440, "height": 900}
        )
        cookies = get_zen_cookies()
        if cookies:
            await self._ctx.add_cookies(cookies)
        else:
            print("[Scraper] Куки Zen не найдены — Авито может чаще показывать капчу.")
        return self

    async def __aexit__(self, *exc) -> None:
        try:
            if self._browser:
                await self._browser.close()
        finally:
            if self._pw:
                await self._pw.stop()

    async def _load(self, page, url: str, is_search: bool = False) -> None:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        status = resp.status if resp else None
        await page.wait_for_timeout(1500)
        title = await page.title()
        html_head = (await page.content())[:6000]
        if _is_blocked(status, title, html_head):
            self.blocked = True
            raise AvitoBlocked(f"HTTP {status}, «{title[:60]}»")
        if is_search and status == 404:
            raise CityNotFound(url.split("?")[0])

    async def search(
        self, params: FilterParams, progress: Optional[ProgressCb] = None
    ) -> Tuple[List[ListingItem], int, List[str]]:
        """Возвращает (объявления, сколько страниц собрано, предупреждения)."""
        warnings: List[str] = []
        items: List[ListingItem] = []
        seen = set()
        pages_done = 0
        page = await self._ctx.new_page()
        try:
            for page_no in range(1, params.pages + 1):
                if progress:
                    await progress(f"Собираю страницу {page_no} из {params.pages} выдачи Авито…", 5 + int(30 * (page_no - 1) / params.pages))
                try:
                    await self._load(page, build_search_url(params, page_no), is_search=True)
                    if page_no == 1:
                        wanted = resolve_city(params.city)
                        landed = urllib.parse.urlparse(page.url).path.strip("/").split("/")[0]
                        if landed and landed != wanted:
                            warnings.append(
                                f"Авито открыл «{landed}» вместо «{wanted}» — проверьте, что город распознан верно."
                            )
                    try:
                        await page.wait_for_selector('[data-marker="item"]', timeout=8000)
                    except Exception:
                        pass
                    # Прокрутка подгружает ленивые фото и хвост выдачи
                    for _ in range(8):
                        await page.evaluate("window.scrollBy(0, 1500)")
                        await page.wait_for_timeout(300)
                    raw = await page.evaluate(EXTRACT_CARDS_JS)
                except AvitoBlocked as e:
                    if pages_done == 0:
                        raise
                    warnings.append(
                        f"Авито ограничил доступ на странице {page_no} ({e}). Показаны объявления с {pages_done} стр."
                    )
                    break

                if not raw:
                    if pages_done == 0:
                        warnings.append("На первой странице не нашлось карточек — возможно, запрос ничего не вернул.")
                    break

                for r in raw:
                    if r["id"] in seen or r["price"] <= 0:
                        continue
                    seen.add(r["id"])
                    images = r["images"]
                    items.append(
                        ListingItem(
                            id=r["id"],
                            title=r["title"],
                            price=r["price"],
                            url="https://www.avito.ru" + r["href"],
                            location=r["loc"],
                            date_posted=r["date"],
                            seller=r["seller"],
                            badge=r["badge"],
                            image_url=images[0] if images else None,
                            images=images,
                            description_snippet=r["desc"],
                            full_description=r["desc"],
                        )
                    )
                pages_done += 1
                if page_no < params.pages:
                    await _pause(config.DELAY_PAGES)
        finally:
            await page.close()
        return items, pages_done, warnings

    async def verify(self, item: ListingItem) -> bool:
        """
        Открывает объявление и сверяет цену/описание с выдачей.
        Возвращает False, если Авито заблокировал доступ (дальше проверять нет смысла).
        """
        page = await self._ctx.new_page()
        try:
            await self._load(page, item.url)
            await page.wait_for_timeout(1000)
            info = await page.evaluate(ITEM_PAGE_JS)
        except AvitoBlocked:
            return False
        except Exception as e:
            print(f"[Scraper] Не удалось открыть {item.url}: {e}")
            return True
        finally:
            await page.close()

        if info["closed"]:
            item.unavailable = True
            item.price_note = "Объявление снято с публикации"
            return True

        real = info["price"]
        if real > 0:
            if abs(real - item.price) / max(item.price, 1) > 0.01:
                item.listed_price = item.price
                item.price = real
                item.price_verified = False
                item.price_note = f"В выдаче было {item.listed_price:,} ₽, на странице {real:,} ₽".replace(",", " ")
            else:
                item.price_verified = True
        if info["desc"]:
            item.full_description = info["desc"]
        if info["images"]:
            merged = list(info["images"])
            for u in item.images:
                if u.split("?")[0] not in {m.split("?")[0] for m in merged}:
                    merged.append(u)
            item.images = merged[:8]
            item.image_url = item.images[0]
        return True


# ---------------------------------------------------------------------------
# Текстовые фильтры (слова в описании / исключить слова)
# ---------------------------------------------------------------------------

def apply_text_filters(listings: List[ListingItem], params: FilterParams) -> List[ListingItem]:
    include_words = [w.strip().lower() for w in (params.words_in_description or "").split(",") if w.strip()]
    exclude_words = [w.strip().lower() for w in (params.exclude_words or "").split(",") if w.strip()]

    filtered = []
    for item in listings:
        if params.price_from and item.price < params.price_from:
            continue
        if params.price_to and item.price > params.price_to:
            continue
        text = (item.title + " " + item.full_description + " " + item.description_snippet).lower()
        if include_words and not all(w in text for w in include_words):
            continue
        if exclude_words and any(w in text for w in exclude_words):
            continue
        filtered.append(item)
    return filtered
