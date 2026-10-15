import asyncio
from playwright.async_api import async_playwright

async def test_edge():
    async with async_playwright() as p:
        try:
            # Используем установленный в системе Edge
            browser = await p.chromium.launch(
                channel="msedge",
                headless=False,
                args=["--start-maximized"]
            )
            context = await browser.new_context(no_viewport=True)
            page = await context.new_page()
            print("Открываем Авито в реальном Edge...")
            await page.goto("https://www.avito.ru/moskva?q=ps5", timeout=20000)
            await asyncio.sleep(5)
            content = await page.content()
            print("Title страницы:", await page.title())
            if "429" in content or "Доступ ограничен" in content:
                print("Снова 429 блок")
            else:
                items = await page.query_selector_all("[data-marker='item']")
                print("УСПЕХ! Найдено реальных объявлений:", len(items))
                for it in items[:3]:
                    t = await it.query_selector("[itemprop='name']")
                    a = await it.query_selector("a[data-marker='item-title']")
                    print("  Заголовок:", await t.inner_text() if t else "—")
                    print("  Ссылка:", await a.get_attribute("href") if a else "—")
            await browser.close()
        except Exception as e:
            print("Ошибка:", e)

if __name__ == "__main__":
    asyncio.run(test_edge())
