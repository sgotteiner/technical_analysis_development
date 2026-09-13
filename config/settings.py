"""
Application & Environment Settings.
"""
import os
from dataclasses import dataclass

@dataclass
class AppSettings:
    project_name: str = "Trading Microservice API"
    version: str = "1.0.0"
    data_dir: str = os.path.abspath("data")
    cdp_port: int = 9222
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

settings = AppSettings()
