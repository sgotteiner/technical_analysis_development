import os
import sys
import time
import subprocess
import requests

print("=========================================================")
print("[STANDALONE TV APP ENGINE] DOWNLOADING & LAUNCHING DEBUG TV APP")
print("=========================================================")

# 1. Target directory inside workspace for standalone TV App
app_dir = os.path.join(os.getcwd(), "TradingView_App")
os.makedirs(app_dir, exist_ok=True)
tv_exe_path = os.path.join(app_dir, "TradingView.exe")

# 2. Check if direct standalone executable exists or download
if not os.path.exists(tv_exe_path):
    print("Downloading standalone TradingView Desktop binary from official CDN...")
    download_urls = [
        "https://tvd-packages.tradingview.com/stable/latest/win32/x64/TradingView.exe",
        "https://tvd-packages.tradingview.com/stable/2.11.0/win32/x64/TradingView.exe"
    ]
    downloaded = False
    for url in download_urls:
        try:
            print(f"Trying CDN: {url}")
            r = requests.get(url, stream=True, timeout=30)
            if r.status_code == 200:
                with open(tv_exe_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Successfully downloaded TradingView.exe ({os.path.getsize(tv_exe_path)} bytes)!")
                downloaded = True
                break
        except Exception as e:
            print(f"Failed URL {url}: {e}")
            
    if not downloaded:
        print("Could not download direct EXE from CDN.")
else:
    print(f"Found standalone TradingView.exe at: {tv_exe_path}")

# 3. Kill existing store processes to prevent conflict
print("Terminating existing TradingView processes...")
subprocess.run("taskkill /F /IM TradingView.exe", shell=True, capture_output=True)
time.sleep(2)

# 4. Launch standalone TradingView.exe with --remote-debugging-port=9222
if os.path.exists(tv_exe_path):
    print(f"Launching standalone TradingView App: {tv_exe_path} --remote-debugging-port=9222")
    subprocess.Popen([tv_exe_path, "--remote-debugging-port=9222", "--user-data-dir=" + os.path.join(app_dir, "data")])
    time.sleep(5)

# 5. Verify CDP port 9222 endpoint
print("Verifying CDP port 9222 endpoint...")
connected = False
for attempt in range(10):
    time.sleep(1.5)
    try:
        r = requests.get("http://localhost:9222/json/list", timeout=2)
        if r.status_code == 200:
            targets = r.json()
            print(f"\nSUCCESS! CDP Connection Established on Port 9222! Targets ({len(targets)}):")
            for t in targets:
                print(f" - [{t.get('type')}] {t.get('title')} ({t.get('url')})")
            connected = True
            break
    except Exception as e:
        print(f" Attempt {attempt+1}/10 connecting to port 9222...")

if connected:
    print("\nTRADINGVIEW DESKTOP APP DEBUG PORT IS 100% LIVE!")
else:
    print("\nCDP Port search finished.")

print("=========================================================\n")
