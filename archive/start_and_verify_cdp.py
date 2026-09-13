import os
import time
import subprocess
import requests

print("=========================================================")
print("[STANDALONE MCP LAUNCHER] STARTING TRADINGVIEW APP WINDOW")
print("=========================================================")

profile_dir = r"C:\tmp\tv_mcp_session"
os.makedirs(profile_dir, exist_ok=True)

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

print("1. Terminating previous background Chrome instances...")
subprocess.run("taskkill /F /IM chrome.exe", shell=True, capture_output=True)
time.sleep(2)

print(f"2. Launching TradingView Standalone App Window on Port 9222...")
cmd = f'"{chrome_path}" --app="https://www.tradingview.com/chart" --remote-debugging-port=9222 --user-data-dir="{profile_dir}"'
subprocess.Popen(cmd, shell=True)

print("3. Polling port 9222 until active...")
connected = False
for attempt in range(12):
    time.sleep(1.0)
    try:
        r = requests.get("http://127.0.0.1:9222/json/list", timeout=2)
        if r.status_code == 200:
            targets = r.json()
            print(f"\nSUCCESS! Connected to Port 9222 ({len(targets)} Targets):")
            for t in targets:
                print(f" - [{t.get('type')}] {t.get('title')} ({t.get('url')})")
            connected = True
            break
    except Exception as e:
        print(f" Attempt {attempt+1}/12 waiting for port 9222...")

if connected:
    print("\nTRADINGVIEW APP WINDOW IS READY FOR MCP COMMANDS!")
else:
    print("\nCDP Port failed to bind.")

print("=========================================================\n")
