from core._config import PluginPool
from core.base import BaseRunnerResult, Data
from core import generator
from core.plugin_base import ServerPlugin
from servers import ZenDaoServer
from servers.zendao_server import ZenDaoProduct, ZenDaoProject, ZenDaoExecution


def zendao_abs():
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


class ReportPlugin(ServerPlugin):

    def run(self, *args, **kwargs) -> BaseRunnerResult:
        print("run plugin")

    def get_data(self, data: Data):
        print(f"method_name: {data.method_name}")
        print(f"obj:{data.obj}")
        print(f"data:{data.data}")


def main_testing3():
    report_plugin1 = ReportPlugin()
    report_plugin2 = ReportPlugin()
    PluginPool.register(report_plugin1)
    PluginPool.register(report_plugin2)
    generator.start(["--zendao_username", "a80646", "--zendao_password", "Woaini^6636865", "--zendao_product_id", 1123,
                     "--zendao_execution_id", 3572])


if __name__ == '__main__':
    main_testing3()
