import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="ru-RU"
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        print("Открываем Авито с Stealth().apply_stealth_async...")
        try:
            resp = await page.goto("https://www.avito.ru/moskva?q=ps5", timeout=20000, wait_until="domcontentloaded")
            print("Status:", resp.status)
            await asyncio.sleep(4)
            content = await page.content()
            print("Title:", await page.title())
            if "Доступ ограничен" in content or "429" in content:
                print("Заблокировано.")
            else:
                soup = BeautifulSoup(content, "html.parser")
                cards = soup.select("[data-marker='item']")
                print("НАЙДЕНО РЕАЛЬНЫХ ОБЪЯВЛЕНИЙ:", len(cards))
                for c in cards[:3]:
                    t = c.select_one("[itemprop='name']") or c.select_one("h3")
                    a = c.select_one("a[data-marker='item-title']") or c.select_one("a[href*='/']")
                    p = c.select_one("[itemprop='price']") or c.select_one("[data-marker='item-price']")
                    print("  Товар:", t.get_text(strip=True) if t else "—")
                    print("  Реальная ссылка:", a.get("href") if a else "—")
                    print("  Цена:", p.get_text(strip=True) if p else "—")
        except Exception as e:
            print("Ошибка:", e)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
