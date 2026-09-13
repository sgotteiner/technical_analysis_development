import os
import sys
import time
import socket
import threading
import subprocess
import requests

print("=========================================================")
print("[STANDALONE MCP ENGINE] LAUNCHING TV APP + IPV6 BRIDGE")
print("=========================================================")

# 1. Kill old Chrome instances
print("1. Cleaning up previous Chrome processes...")
subprocess.run("taskkill /F /IM chrome.exe", shell=True, capture_output=True)
time.sleep(2)

# 2. Launch Chrome standalone app window on IPv4 127.0.0.1:9222
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

# 3. Start IPv6 ::1 proxy to forward requests to IPv4 127.0.0.1:9222
def forward_data(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        try:
            src.close()
        except:
            pass
        try:
            dst.close()
        except:
            pass

def handle_client(cli_sock):
    try:
        target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target.connect(('127.0.0.1', 9222))
        t1 = threading.Thread(target=forward_data, args=(cli_sock, target), daemon=True)
        t2 = threading.Thread(target=forward_data, args=(target, cli_sock), daemon=True)
        t1.start()
        t2.start()
    except Exception as e:
        cli_sock.close()

def start_ipv6_bridge():
    try:
        srv = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('::1', 9222))
        srv.listen(20)
        print("3. IPv6 Proxy listening on [::1]:9222 -> forwarding to 127.0.0.1:9222")
        while True:
            cli, _ = srv.accept()
            threading.Thread(target=handle_client, args=(cli,), daemon=True).start()
    except Exception as e:
        print(f"IPv6 Proxy bind info: {e}")

# Start proxy thread
proxy_thread = threading.Thread(target=start_ipv6_bridge, daemon=True)
proxy_thread.start()

# 4. Verify endpoints
time.sleep(2)
v4_ok = False
v6_ok = False

for attempt in range(10):
    time.sleep(1)
    try:
        r4 = requests.get("http://127.0.0.1:9222/json/list", timeout=2)
        if r4.status_code == 200:
            v4_ok = True
    except:
        pass
    
    try:
        r6 = requests.get("http://[::1]:9222/json/list", timeout=2)
        if r6.status_code == 200:
            v6_ok = True
    except:
        pass

    if v4_ok and v6_ok:
        print("\nSUCCESS! BOTH IPv4 (127.0.0.1:9222) AND IPv6 ([::1]:9222) ARE FULLY ACTIVE!")
        print(f"Active CDP Targets: {len(r4.json())}")
        break
    else:
        print(f" Attempt {attempt+1}/10: IPv4={v4_ok}, IPv6={v6_ok}")

if v4_ok and v6_ok:
    print("TRADINGVIEW APP + MCP BRIDGE IS READY FOR ALL TOOLS.")
    # Keep script running to maintain the proxy thread
    while True:
        time.sleep(10)
else:
    print("FAILED to establish dual-stack CDP bridge.")

print("=========================================================")
