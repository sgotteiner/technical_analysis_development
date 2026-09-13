import os
import time
import subprocess
import requests

print("=========================================================")
print("[CDP ENGINE] LAUNCHING CHROME TRADINGVIEW WITH USER DATA DIR")
print("=========================================================")

print("Step 1: Closing existing Chrome processes...")
subprocess.run("taskkill /F /IM chrome.exe", shell=True, capture_output=True)
time.sleep(2)

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

profile_dir = r"C:\tmp\chrome_dev_profile"
os.makedirs(profile_dir, exist_ok=True)

print(f"Step 2: Launching Chrome with CDP port 9222 and isolated profile...")
cmd = f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{profile_dir}" "https://www.tradingview.com/chart"'
subprocess.Popen(cmd, shell=True)

print("Step 3: Verifying CDP port 9222 endpoint...")
connected = False
for attempt in range(10):
    time.sleep(1)
    try:
        r = requests.get("http://localhost:9222/json/list", timeout=2)
        if r.status_code == 200:
            targets = r.json()
            print(f"\nSUCCESS! CDP Connection Established on Port 9222! Active Pages ({len(targets)}):")
            for t in targets:
                print(f" - [{t.get('type')}] {t.get('title')} ({t.get('url')})")
            connected = True
            break
    except Exception as e:
        print(f" Attempt {attempt+1}/10 connecting to port 9222...")

if connected:
    print("\nTRADINGVIEW CDP MCP SERVER IS NOW 100% OPERATIONAL!")
else:
    print("\nCDP Port failed to open.")

print("=========================================================\n")
