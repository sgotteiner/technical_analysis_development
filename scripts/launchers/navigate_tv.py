import time
import requests

print("Opening TradingView Chart Tab via CDP Endpoint...")
try:
    r = requests.put("http://localhost:9222/json/new?https://www.tradingview.com/chart")
    print(f"Status: {r.status_code}")
    print(f"Tab Info: {r.json()}")
except Exception as e:
    # Try GET method if PUT fails
    r = requests.get("http://localhost:9222/json/new?https://www.tradingview.com/chart")
    print(f"GET Status: {r.status_code}")
    print(f"Tab Info: {r.json()}")

time.sleep(3)
print("Verifying targets...")
targets = requests.get("http://localhost:9222/json/list").json()
for t in targets:
    print(f" - [{t.get('type')}] {t.get('title')} ({t.get('url')})")
