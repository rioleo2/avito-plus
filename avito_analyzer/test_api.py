import urllib.request
import json
import time

def main():
    t0 = time.time()
    payload = json.dumps({"query": "MacBook Pro 14 M1 Pro", "city": "moskva"}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/analyze",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req, timeout=60)
    data = json.loads(res.read().decode())
    elapsed = time.time() - t0
    print(f"УСПЕШНО за {elapsed:.1f} сек!")
    print(f"Всего лотов: {len(data['listings'])}")
    print(f"Медианная цена рынка: {data['stats']['median_price']:,} ₽")
    top = data['listings'][0]
    print(f"Топ лот: {top['title']} за {top['price']:,} ₽")
    print(f"Вердикт ИИ: {top['ai_analysis']['verdict']}")
    print(f"Выгода: {top['ai_analysis'].get('estimated_profit', 0):,} ₽")

if __name__ == "__main__":
    main()
