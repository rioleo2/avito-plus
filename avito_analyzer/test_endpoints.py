from curl_cffi import requests
import json

def test_endpoints():
    s = requests.Session(impersonate="chrome124")
    
    # 1. Web API endpoint
    try:
        url = "https://www.avito.ru/api/1/main/items"
        r = s.get(url, timeout=5)
        print("Endpoint 1 status:", r.status_code, "len:", len(r.text))
    except Exception as e:
        print("Endpoint 1 error:", e)

    # 2. Desktop search with mobile UA
    try:
        url = "https://www.avito.ru/moskva?q=ps5"
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        r = s.get(url, headers=headers, timeout=5)
        print("Endpoint 2 (mobile UA) status:", r.status_code, "len:", len(r.text))
    except Exception as e:
        print("Endpoint 2 error:", e)

if __name__ == "__main__":
    test_endpoints()
