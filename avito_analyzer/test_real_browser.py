import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import os

profile_dir = os.path.abspath("real_browser_profile")

async def test():
    async with async_playwright() as p:
        # Запуск с сохранением реальной сессии и cookies
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            channel="msedge", # Нативный браузер Edge
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        print("Открываем страницу поиска ps5 на Авито через реальный Edge...")
        try:
            await page.goto("https://www.avito.ru/moskva?q=ps5", timeout=25000)
            await asyncio.sleep(4)
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            cards = soup.select("[data-marker='item']")
            print("Найдено карточек:", len(cards))
            for i, c in enumerate(cards[:4]):
                t = c.select_one("[itemprop='name']") or c.select_one("h3")
                a = c.select_one("a[data-marker='item-title']") or c.select_one("a[href*='/']")
                p = c.select_one("[itemprop='price']") or c.select_one("[data-marker='item-price']")
                desc = c.select_one("[class*='description']") or c.select_one("p")
                
                title = t.get_text(strip=True) if t else ""
                href = a.get("href") if a else ""
                full_url = f"https://www.avito.ru{href}" if href.startswith("/") else href
                price = p.get_text(strip=True) if p else ""
                
                print(f"[{i+1}] {title} | {price}")
                print(f"     URL: {full_url}")
                print(f"     Desc: {desc.get_text(strip=True)[:80] if desc else ''}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(test())
