import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def search_yandex(q="ps5"):
    query = urllib.parse.quote(f"site:avito.ru/moskva {q}")
    url = f"https://yandex.ru/search/?text={query}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "ru-RU,ru;q=0.9"
        }
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        html = r.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select(".serp-item")
        print("Yandex serp items:", len(items))
        for it in items[:5]:
            a = it.select_one("a[href*='avito.ru']")
            t = it.select_one("h2") or it.select_one(".OrganicTitle")
            s = it.select_one(".organic__text") or it.select_one(".ExtendedText")
            if a:
                print("---")
                print("Title:", t.get_text(strip=True) if t else "")
                print("Href:", a.get("href"))
                print("Snippet:", s.get_text(strip=True)[:100] if s else "")

if __name__ == "__main__":
    search_yandex("ps5")
