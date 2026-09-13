import os
import ctypes
import time
import subprocess

print("Closing any running TradingView instances...")
subprocess.run("taskkill /F /IM TradingView.exe", shell=True, capture_output=True)
time.sleep(2)

user_home = os.path.expanduser("~")
found = []
for root, dirs, files in os.walk(user_home):
    if "TradingView.exe" in files:
        found.append(os.path.join(root, "TradingView.exe"))

if found:
    target = found[0]
    print(f"Found TradingView executable: {target}")
    
    # Get 8.3 Short Path to prevent Unicode encoding failures in terminal
    buf = ctypes.create_unicode_buffer(500)
    ctypes.windll.kernel32.GetShortPathNameW(target, buf, 500)
    short_path = buf.value if buf.value else target
    print(f"8.3 Short Path: {short_path}")
    
    cmd = f'"{short_path}" --remote-debugging-port=9222'
    print(f"Executing: {cmd}")
    subprocess.Popen(cmd, shell=True)
    time.sleep(4)
    print("SUCCESS: TradingView Desktop App launched with CDP remote debugging on port 9222!")
else:
    print("ERROR: TradingView.exe not found under user directory.")
