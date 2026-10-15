import asyncio
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

profile_dir = os.path.abspath("real_browser_profile")

async def test():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(profile_dir, headless=True, channel="msedge")
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto("https://www.avito.ru/moskva?q=ps5", timeout=20000)
        await asyncio.sleep(2)
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        # Поиск всех ссылок с цифрами на конце (это конкретные объявления на Авито!)
        links = soup.find_all("a", href=True)
        item_links = []
        for a in links:
            href = a["href"]
            # На Авито конкретные объявления заканчиваются на _цифры (например /moskva/..._4401928312)
            if re.search(r"_\d{8,}$", href) and a.get_text(strip=True):
                item_links.append((a.get_text(strip=True), href))
        
        print("Найдено реальных объявлений на странице:", len(item_links))
        for t, h in item_links[:8]:
            full_url = f"https://www.avito.ru{h}" if h.startswith("/") else h
            print("TITLE:", t)
            print("URL:", full_url)
            print("---")
            
        await ctx.close()

if __name__ == "__main__":
    import re
    asyncio.run(test())
