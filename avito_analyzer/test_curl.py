from curl_cffi import requests
from bs4 import BeautifulSoup

def test():
    s = requests.Session(impersonate="chrome124")
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://www.avito.ru/",
    }
    r = s.get("https://www.avito.ru/moskva?q=ps5", headers=headers, timeout=12)
    print("Status:", r.status_code, "HTML length:", len(r.text))
    if r.status_code == 200 and "Доступ ограничен" not in r.text:
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("[data-marker='item']")
        print("Cards found:", len(cards))
        for i, c in enumerate(cards[:3]):
            t = c.select_one("[itemprop='name']") or c.select_one("h3")
            a = c.select_one("a[data-marker='item-title']") or c.select_one("a[href*='/']")
            p = c.select_one("[itemprop='price']") or c.select_one("meta[itemprop='price']")
            desc = c.select_one("[class*='description']") or c.select_one("p")
            print(f"Card {i+1}:")
            print("  Title:", t.get_text(strip=True) if t else "No title")
            print("  Href:", a.get("href") if a else "No href")
            print("  Price:", p.get("content") or p.get_text(strip=True) if p else "No price")
            print("  Desc:", desc.get_text(strip=True)[:100] if desc else "No desc")
    else:
        print("Blocked / Captcha triggered. First 200 chars:")
        print(r.text[:200])

if __name__ == "__main__":
    test()
