import os
import time
import subprocess

profile_dir = os.path.join(os.environ.get("TEMP", "C:/tmp"), "chrome_tv_profile")
os.makedirs(profile_dir, exist_ok=True)

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

print(f"Launching isolated Chrome CDP instance from {chrome_path}...")
cmd = f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{profile_dir}" "https://www.tradingview.com/chart"'
subprocess.Popen(cmd, shell=True)

time.sleep(3)
print("CDP Chrome instance successfully launched on port 9222!")
