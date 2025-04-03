from typing import Union

from core.deco import inner_plugin
from core.base import T, RunnerResult, Data
from core.generator import ServicePlugin


@inner_plugin
class ReportPlugin(ServicePlugin):
    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        print("run inner ReportPlugin")
        return "result inner ReportPlugin"

    def get_notify(self, data: Data):
        print("*" * 10 + "inner ReportPlugin Monitor" + "*" * 10)
        print(f"method_name: {data.method_name}")
        print(f"obj:{data.obj}")
        print(f"data:{data.result}")
        result: RunnerResult = data.result
        print(f"source_name:{result.source_name}")
        print(f"source_type:{result.source_type}")
        print(f"get_data():{result.get_data()}")
