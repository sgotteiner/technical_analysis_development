import os
import sys
import time
import subprocess
import requests

print("=========================================================")
print("[MCP LAUNCHER] STARTING STANDALONE TRADINGVIEW APP WINDOW")
print("=========================================================")

print("1. Terminating background Chrome instances...")
subprocess.run("taskkill /F /IM chrome.exe", shell=True, capture_output=True)
time.sleep(2)

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data = r"C:\tmp\tv_mcp_session"
os.makedirs(user_data, exist_ok=True)

cmd = [
    chrome,
    "--app=https://www.tradingview.com/chart",
    "--remote-debugging-port=9222",
    f"--user-data-dir={user_data}"
]

print("2. Spawning standalone TradingView app process...")
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
proc = subprocess.Popen(cmd, creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP, close_fds=True)

print("3. Checking CDP port 9222 status...")
connected = False
for i in range(15):
    time.sleep(1)
    try:
        r = requests.get("http://127.0.0.1:9222/json/list", timeout=2)
        if r.status_code == 200:
            targets = r.json()
            print(f"SUCCESS: Connected to CDP port 9222! {len(targets)} targets active.")
            connected = True
            break
    except Exception as e:
        print(f" Attempt {i+1}/15 waiting for port 9222...")

if connected:
    print("TRADINGVIEW APP IS LIVE AND READY FOR MCP COMMANDS.")
else:
    print("FAILED to connect to port 9222.")

print("=========================================================")
