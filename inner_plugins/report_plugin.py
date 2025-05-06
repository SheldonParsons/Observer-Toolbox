import copy
from typing import Union

from core.deco import inner_plugin
from core.base import T, RunnerResult, Data
from core.generator import ServicePlugin
from inner_plugins.source.report_controller import dispatch_info_collection, generation_report


@inner_plugin
class ReportPlugin(ServicePlugin):
    server_allow_monitor_functions = ["run"]

    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        for reference_data_object in self.reference_data_object_list:
            generation_report(reference_data_object)
        return True

    def get_notify(self, data: Data):
        result: RunnerResult = data.result
        result_data = result.get_data()
        if not hasattr(self, "reference_data_object_list"):
            from core.generator import GlobalData
            self.reference_data_object_list = []
            report_type_list = GlobalData.system_parameters.report_type.split(",")
            for env in GlobalData.system_parameters.env:
                if env["name"] not in report_type_list:
                    continue
                reference_data_object = copy.deepcopy(GlobalData.system_parameters.__dict__)
                for key, value in env.items():
                    reference_data_object[key] = value
                self.reference_data_object_list.append(reference_data_object)
                del reference_data_object["env"]
        for reference_data_object in self.reference_data_object_list:
            dispatch_info_collection(result.source_name, reference_data_object,
                                     result_data)
