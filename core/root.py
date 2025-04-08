import os
from enum import Enum
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SourceType(str, Enum):
    SERVER = "server"
    PLUGIN = "plugin"
    CUSTOMER = "customer"


def get_base_dir() -> Path:
    return Path(BASE_DIR) / "core" / "temp"
