from core import generator
from servers import ZenDaoServer
from servers.zendao_server import ZenDaoProduct, ZenDaoProject, ZenDaoExecution


def zendao_abs():
    zds = ZenDaoServer()

    product_list: list[ZenDaoProduct] = zds.get_products()
    for product in product_list:
        print(f"product.id:{product.id},product.name:{product.name},product.status:{product.status}")

    project_list: list[ZenDaoProject] = zds.get_project(157)
    for project in project_list:
        print(f"product.id:{project.id},product.name:{project.name}")

    execution_list: list[ZenDaoExecution] = zds.get_executions(1123)
    for execution in execution_list:
        print(f"execution.id:{execution.id},execution.name:{execution.name}")


def main_testing1():
    generator.start(
        ["--zendao_product_id", 1123, "--zendao_execution_id", 3621, "--zendao_bug_limit", 10, "--zendao_bug_status",
         "all"])


def main_testing2():
    generator.start(["--zendao_username", "a80646", "--zendao_password", "Woaini^6636865", "--zendao_product_id", 1123,
                     "--zendao_execution_id", 3572])


if __name__ == '__main__':
    zendao_abs()
