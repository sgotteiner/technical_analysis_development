import os
import sys
import time
import subprocess

print("Stopping any running TradingView instances...")
subprocess.run("taskkill /F /IM TradingView.exe", shell=True, capture_output=True)
time.sleep(2)

home = os.path.expanduser("~")
appdata = os.path.join(home, "AppData")
print(f"Searching for TradingView.exe inside {appdata}...")

exe_path = None
for root, dirs, files in os.walk(appdata):
    if "TradingView.exe" in files:
        exe_path = os.path.join(root, "TradingView.exe")
        break

if exe_path and os.path.exists(exe_path):
    print(f"Found executable at: {exe_path}")
    print("Launching with --remote-debugging-port=9222...")
    subprocess.Popen([exe_path, "--remote-debugging-port=9222"])
    time.sleep(5)
    print("TradingView Desktop process successfully started with CDP on port 9222!")
else:
    print("ERROR: TradingView.exe was not found in AppData.")
