import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="ru-RU"
        )
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("Загружаем страницу Авито...")
        try:
            resp = await page.goto("https://www.avito.ru/moskva?q=ps5", wait_until="domcontentloaded", timeout=15000)
            print("HTTP Status:", resp.status)
            await asyncio.sleep(2)
            content = await page.content()
            print("Размер HTML:", len(content))

            if "Доступ ограничен" in content or "firewall" in content.lower():
                print("ОБНАРУЖЕНА БЛОКИРОВКА АВИТО (Капча / IP блок)")
            else:
                soup = BeautifulSoup(content, "html.parser")
                cards = soup.select("[data-marker='item']") or soup.select("div[itemtype*='Product']")
                print("Найдено карточек на странице:", len(cards))
                for i, c in enumerate(cards[:3]):
                    title_el = c.select_one("[itemprop='name']") or c.select_one("h3")
                    link_el = c.select_one("a[data-marker='item-title']") or c.select_one("a[href*='/']")
                    price_el = c.select_one("[itemprop='price']") or c.select_one("[data-marker='item-price']")
                    img_el = c.select_one("img[src*='images.avito.st']") or c.select_one("img")
                    desc_el = c.select_one("[class*='description']") or c.select_one("p")

                    print(f"--- Карточка {i+1} ---")
                    print("Заголовок:", title_el.get_text(strip=True) if title_el else "Нет")
                    print("Ссылка:", link_el.get("href") if link_el else "Нет")
                    print("Цена:", price_el.get_text(strip=True) if price_el else "Нет")
                    print("Картинка:", img_el.get("src") if img_el else "Нет")
                    print("Описание:", desc_el.get_text(strip=True)[:100] if desc_el else "Нет")
        except Exception as e:
            print("Ошибка:", e)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
