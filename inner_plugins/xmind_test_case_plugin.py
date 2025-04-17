import os
from pathlib import Path
from typing import Union

from core.deco import inner_plugin
from core.base import T, RunnerResult, Data
from core.generator import ServicePlugin
from core.root import BASE_DIR
from core.utils import DynamicObject
from inner_plugins.source.xmind_case_controller import analyze_xmind


@inner_plugin
class XmindPlugin(ServicePlugin):
    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        # TODO:暂时改为循环读取指定路径
        self.xmind_file_path = [Path(BASE_DIR) / "xmindcase" / "调账昵称.xmind",
                                Path(BASE_DIR) / "xmindcase" / "调账昵称2.xmind"]
        case_result = analyze_xmind(self.xmind_file_path, self.executionName + "_" + os.getenv("XMIND_CASE_ZIP_NAME"))
        print(f"case_result:{case_result.__dict__}")
        return DynamicObject(case_result=case_result)

    def get_notify(self, data: Data):
        result: RunnerResult = data.result
        rusult_data = result.get_data()
        if result.source_name == 'ZenDaoServer' and rusult_data:
            self.executionName = rusult_data.task.executionName.replace(" ", "")
