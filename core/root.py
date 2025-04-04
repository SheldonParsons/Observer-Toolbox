import os
from enum import Enum

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SourceType(str, Enum):
    SERVER = "server"
    PLUGIN = "plugin"
    CUSTOMER = "customer"
