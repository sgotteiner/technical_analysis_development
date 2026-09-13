import os
import sys
import ctypes

user_home = os.path.expanduser("~")
print(f"User Home: {user_home}")

# Search for TradingView.exe
exe_path = None
for root, dirs, files in os.walk(os.path.join(user_home, "AppData")):
    if "TradingView.exe" in files:
        exe_path = os.path.join(root, "TradingView.exe")
        break

if not exe_path:
    # Try Program Files
    for root, dirs, files in os.walk(r"C:\Program Files"):
        if "TradingView.exe" in files:
            exe_path = os.path.join(root, "TradingView.exe")
            break

print(f"Full Executable Path: {exe_path}")

# Create a simple batch file in the project folder & Desktop
bat_content = f'@echo off\nstart "" "{exe_path}" --remote-debugging-port=9222\n'

project_bat = os.path.join(os.getcwd(), "Launch_TradingView_CDP.bat")
with open(project_bat, "w") as f:
    f.write(bat_content)

desktop_dir = os.path.join(user_home, "Desktop")
if os.path.exists(desktop_dir):
    desktop_bat = os.path.join(desktop_dir, "Launch_TradingView_CDP.bat")
    with open(desktop_bat, "w") as f:
        f.write(bat_content)

print(f"\n=========================================================")
print("CREATED EASY ONE-CLICK LAUNCHERS:")
print(f" 1. Project Folder: {project_bat}")
if os.path.exists(desktop_dir):
    print(f" 2. Desktop Launcher: {desktop_bat}")
print("=========================================================\n")
