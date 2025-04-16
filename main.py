from typing import Union

from core.base import RunnerResult, Data, T
from core import generator
from core.generator import GenericServer, ServicePlugin, Parameter, Server, ServerRunner, PluginPool

from servers import ZenDaoServer
from servers.zendao_server import ZenDaoProduct, ZenDaoProject, ZenDaoExecution


def zen_dao_interface_testing():
    zds = ZenDaoServer()

    product_list: list[ZenDaoProduct] = zds.get_products()
    for product in product_list:
        print(f"product.id:{product.id},product.name:{product.name},product.status:{product.status}")

    project_list: list[ZenDaoProject] = zds.get_project(157)
    for project in project_list:
        print(f"project.id:{project.id},project.name:{project.name}")

    execution_list: list[ZenDaoExecution] = zds.get_executions(1123)
    for execution in execution_list:
        print(f"execution.id:{execution.id},execution.name:{execution.name}")


class ReportPlugin1(ServicePlugin):
    source_name = "ReportPlugin1--source_name-rewrite"

    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        print("run plugin 1")
        return "result plugin 1"

    def get_notify(self, data: Data):
        print("*" * 10 + "ReportPlugin1 Monitor" + "*" * 10)
        print(f"method_name: {data.method_name}")
        print(f"obj:{data.obj}")
        print(f"data:{data.result}")
        result: RunnerResult = data.result
        print(f"source_name:{result.source_name}")
        print(f"source_type:{result.source_type}")
        print(f"get_data():{result.get_data()}")


class ReportPlugin2(ServicePlugin):
    allow_monitor_functions = ["notice"]

    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        print("run plugin 2")
        return "result plugin 2"

    def get_notify(self, data: Data):
        print("*" * 10 + "ReportPlugin2 Monitor" + "*" * 10)
        print(f"method_name: {data.method_name}")
        print(f"obj:{data.obj}")
        print(f"data:{data.result}")
        result: RunnerResult = data.result
        print(f"source_name:{result.source_name}")
        print(f"source_type:{result.source_type}")
        print(f"get_data():{result.get_data()}")


class ReportPlugin3(ServicePlugin):
    allow_monitor_functions = ["notice"]

    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        print("run plugin 3")
        return "result plugin 3"

    def get_notify(self, data: Data):
        print("*" * 10 + "ReportPlugin3 Monitor" + "*" * 10)
        print(f"method_name: {data.method_name}")
        print(f"obj:{data.obj}")
        print(f"data:{data.result}")
        result: RunnerResult = data.result
        print(f"source_name:{result.source_name}")
        print(f"source_type:{result.source_type}")
        print(f"get_data():{result.get_data()}")


class ReportPlugin4(ServicePlugin):

    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        print("run plugin 3")
        return "result plugin 3"

    def get_notify(self, data: Data):
        print("*" * 10 + "ReportPlugin4 Monitor" + "*" * 10)
        print(f"method_name: {data.method_name}")
        print(f"obj:{data.obj}")
        print(f"data:{data.result}")
        result: RunnerResult = data.result
        print(f"source_name:{result.source_name}")
        print(f"source_type:{result.source_type}")
        print(f"get_data():{result.get_data()}")


class GenericMonitor(GenericServer):
    source_name = "GenericMonitor--source_name-rewrite"

    def notice(self):
        print("there is notice function")
        return "-----notice function-----"


class GenericParameter(Parameter):

    def __init__(self, name=None,
                 *args, **kwargs):
        self.name = name


@ServerRunner(GenericParameter)
class ListenTestServer(Server):

    @classmethod
    def ping(cls) -> bool:
        pass

    def __init__(self):
        super().__init__()

    def set_base_headers(self, *args, **kwargs) -> None:
        pass

    def tokenization(self) -> bool:
        pass

    def set_tokenization_headers(self):
        pass

    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        return self.parameter.name


def main_testing3():
    # report_plugin1 = ReportPlugin1()
    # report_plugin2 = ReportPlugin2()
    # report_plugin3 = ReportPlugin3()
    # PluginPool.register(report_plugin1)
    # PluginPool.register(report_plugin2)
    # PluginPool.register(report_plugin3)
    GenericMonitor().notice()
    generator.start(["--zendao_product_id", 157,
                     "--zendao_execution_id", 3568, "--zendao_bug_limit", 100, "--name", "sheldon parsons",
                     "--clean_temp_files", 2, "--kdocs_files_path",
                     "/Users/sheldon/Documents/GithubProject/Observer-Toolbox/kdocs_urls.txt","--close_inner_all", 1],
                    [ReportPlugin4()])


if __name__ == '__main__':
    main_testing3()
