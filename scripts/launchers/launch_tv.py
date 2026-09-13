import os
import sys
import time
import subprocess

print("Closing existing TradingView processes...")
subprocess.run("taskkill /F /IM TradingView.exe", shell=True, capture_output=True)
time.sleep(2)

# Find TradingView.exe using python os.walk on user home
user_home = os.path.expanduser("~")
target_exe = None

for root, dirs, files in os.walk(user_home):
    if "TradingView.exe" in files:
        target_exe = os.path.join(root, "TradingView.exe")
        break

if target_exe and os.path.exists(target_exe):
    print(f"Found TradingView executable: {target_exe}")
    cmd = f'"{target_exe}" --remote-debugging-port=9222'
    print(f"Executing: {cmd}")
    subprocess.Popen(cmd, shell=True)
    time.sleep(4)
    print("TradingView process launched with CDP port 9222!")
else:
    print("TradingView.exe not found.")
