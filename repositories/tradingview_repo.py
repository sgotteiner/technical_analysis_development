"""
TradingView Repository.
Handles browser CDP connections and remote automation calls for TradingView charts.
"""
import os
import subprocess
import time
from typing import Dict, Any
from config.settings import settings

class TradingViewRepository:
    def __init__(self, cdp_port: int = settings.cdp_port):
        self.cdp_port = cdp_port

    def is_cdp_active(self) -> bool:
        """Check if CDP port is open and responding."""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex(('127.0.0.1', self.cdp_port))
        sock.close()
        return result == 0

    def launch_chrome_cdp_session(self, chart_url: str = "https://www.tradingview.com/chart") -> Dict[str, Any]:
        """Launch isolated Chrome instance attached to CDP debugging port."""
        profile_dir = os.path.join(os.environ.get("TEMP", "C:/tmp"), "chrome_tv_profile")
        os.makedirs(profile_dir, exist_ok=True)
        
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            
        cmd = f'"{chrome_path}" --remote-debugging-port={self.cdp_port} --user-data-dir="{profile_dir}" "{chart_url}"'
        proc = subprocess.Popen(cmd, shell=True)
        time.sleep(3)
        return {
            "status": "launched",
            "cdp_port": self.cdp_port,
            "pid": proc.pid
        }
