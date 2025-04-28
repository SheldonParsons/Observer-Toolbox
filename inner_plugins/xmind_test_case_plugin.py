import os
from typing import Union

from core.deco import inner_plugin
from core.base import T, RunnerResult, Data
from core.generator import ServicePlugin
from core.utils import DynamicFreezeObject
from inner_plugins.source.xmind_case_controller import analyze_xmind


@inner_plugin
class XmindPlugin(ServicePlugin):
    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        case_result = analyze_xmind(self.xmind_path_list,
                                    '_'.join([self.executionName, os.getenv("XMIND_CASE_ZIP_NAME_SUFFIX")]))
        # print(f"case_result:{case_result}")
        return DynamicFreezeObject(case_result=case_result)

    def get_notify(self, data: Data):
        result: RunnerResult = data.result
        result_data = result.get_data()
        if result.source_name == 'ZenDaoServer' and result_data:
            self.executionName = result_data.task.executionName.replace(" ", "")
        if result.source_name == 'ExcelSummaryPlugin' and result_data:
            self.xmind_path_list = result_data.xmind_file_list
            print(f"self.xmind_path_list:{self.xmind_path_list}")
