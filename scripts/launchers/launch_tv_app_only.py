import os
import time
import subprocess
import requests

print("=========================================================")
print("[APP LAUNCHER] STARTING TRADINGVIEW DESKTOP APP ONLY")
print("=========================================================")

print("1. Terminating background TradingView.exe processes...")
subprocess.run("taskkill /F /IM TradingView.exe", shell=True, capture_output=True)
time.sleep(2)

user_home = os.path.expanduser("~")
tv_path = None
for root, dirs, files in os.walk(user_home):
    if "TradingView.exe" in files:
        tv_path = os.path.join(root, "TradingView.exe")
        break

if not tv_path:
    tv_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "TradingView", "TradingView.exe")

print(f"2. Launching TradingView Desktop App: {tv_path}")
env = os.environ.copy()
env["ELECTRON_RUN_AS_NODE"] = "0"
subprocess.Popen([tv_path, "--remote-debugging-port=9222"], env=env)

print("3. Waiting for TradingView Desktop CDP port 9222...")
connected = False
for attempt in range(12):
    time.sleep(1.5)
    try:
        r = requests.get("http://localhost:9222/json/list", timeout=2)
        if r.status_code == 200:
            targets = r.json()
            print(f"\nSUCCESS! TradingView Desktop App CDP Live on Port 9222! Active Targets ({len(targets)}):")
            for t in targets:
                print(f" - [{t.get('type')}] {t.get('title')} ({t.get('url')})")
            connected = True
            break
    except Exception as e:
        print(f" Attempt {attempt+1}/12 waiting for TradingView App on port 9222...")

if connected:
    print("\nTRADINGVIEW DESKTOP APP IS CONNECTED TO MCP!")
else:
    print("\nTradingView Desktop CDP port waiting.")

print("=========================================================\n")
