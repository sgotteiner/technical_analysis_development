import os
import time
import subprocess

print("Closing existing Chrome processes to allow CDP remote debugging port 9222...")
subprocess.run("taskkill /F /IM chrome.exe", shell=True, capture_output=True)
time.sleep(2)

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

print(f"Launching Chrome from: {chrome_path} with --remote-debugging-port=9222...")
subprocess.Popen([chrome_path, "--remote-debugging-port=9222", "https://www.tradingview.com/chart"])
time.sleep(4)
print("Chrome with CDP remote debugging launched!")
