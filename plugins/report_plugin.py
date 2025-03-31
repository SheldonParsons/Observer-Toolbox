import time
from typing import Any, Dict
from core.base import Plugin


class ReportGenerator(Plugin):
    def __init__(self):
        self.reports = []
    
    def on_data_collected(self, system_name: str, data: Dict[str, Any]):
        report_entry = {
            "system": system_name,
            "timestamp": time.localtime,  # 实际应该用datetime.now()
            "data": data
        }
        self.reports.append(report_entry)
        print(f"[{system_name}] 数据已记录到报告")
        print(report_entry)