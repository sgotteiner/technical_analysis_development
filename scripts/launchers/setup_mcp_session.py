import os
import time
import subprocess
import requests

print("=========================================================")
print("[MCP INITIALIZER] STARTING CDP CHROME TRADINGVIEW SESSION")
print("=========================================================")

print("1. Closing background Chrome instances...")
subprocess.run("taskkill /F /IM chrome.exe", shell=True, capture_output=True)
time.sleep(2)

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

profile_dir = r"C:\tmp\chrome_dev_profile"
os.makedirs(profile_dir, exist_ok=True)

cmd = f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{profile_dir}" "https://www.tradingview.com/chart"'
print(f"2. Launching: {cmd}")
subprocess.Popen(cmd, shell=True)

print("3. Polling CDP endpoint until TradingView chart page is active...")
chart_ready = False

for attempt in range(15):
    time.sleep(1.5)
    try:
        r = requests.get("http://localhost:9222/json/list", timeout=3)
        if r.status_code == 200:
            targets = r.json()
            tv_target = [t for t in targets if t.get('type') == 'page' and 'tradingview.com/chart' in t.get('url', '')]
            if tv_target:
                print(f"\nSUCCESS! Found active TradingView Chart tab:")
                print(f" Target ID: {tv_target[0]['id']}")
                print(f" Title:     {tv_target[0]['title']}")
                print(f" URL:       {tv_target[0]['url']}")
                chart_ready = True
                break
            else:
                print(f" Attempt {attempt+1}/15: Chrome listening on 9222, waiting for tradingview.com/chart to load...")
    except Exception as e:
        print(f" Attempt {attempt+1}/15: Waiting for CDP port 9222...")

if chart_ready:
    print("\n=========================================================")
    print("READY! MCP SERVER CAN NOW CONTROL PINE EDITOR & STRATEGY TESTER")
    print("=========================================================\n")
else:
    print("\n=========================================================")
    print("WARNING: TradingView chart target not ready yet.")
    print("=========================================================\n")
