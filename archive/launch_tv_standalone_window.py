import os
import time
import subprocess
import requests

print("=========================================================")
print("[MCP STANDALONE ENGINE] LAUNCHING TRADINGVIEW APP WINDOW")
print("=========================================================")

profile_dir = r"C:\tmp\tv_standalone_app_profile"
os.makedirs(profile_dir, exist_ok=True)

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

print(f"1. Launching TradingView Standalone App Window with CDP port 9222...")
# --app flag renders as an isolated standalone Desktop App window (no browser tabs/URL bar)
cmd = f'"{chrome_path}" --app="https://www.tradingview.com/chart" --remote-debugging-port=9222 --user-data-dir="{profile_dir}"'
print(f"   Executing: {cmd}")
subprocess.Popen(cmd, shell=True)

print("2. Polling CDP endpoint until TradingView App window is fully connected...")
connected = False
for attempt in range(15):
    time.sleep(1.0)
    try:
        r = requests.get("http://localhost:9222/json/list", timeout=2)
        if r.status_code == 200:
            targets = r.json()
            tv_targets = [t for t in targets if t.get('type') == 'page' and ('tradingview' in t.get('url', '') or 'TradingView' in t.get('title', ''))]
            if tv_targets:
                print(f"\nSUCCESS! TradingView App Window Connected via CDP on Port 9222!")
                print(f" Target ID: {tv_targets[0]['id']}")
                print(f" Title:     {tv_targets[0]['title']}")
                print(f" URL:       {tv_targets[0]['url']}")
                connected = True
                break
    except Exception as e:
        print(f" Attempt {attempt+1}/15 waiting for CDP port 9222...")

if connected:
    print("\nTRADINGVIEW APP IS LIVE & CONNECTED TO MCP SERVER!")
else:
    print("\nFailed to bind CDP port.")

print("=========================================================\n")
