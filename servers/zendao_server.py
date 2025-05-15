from enum import Enum
from pathlib import Path
from typing import List

import dotenv
import os

from requests.models import Response

from core._config import _const
from core._config._exception import SystemParameterException
from core.generator import report_exception
from core.deco import ServerRunner
from core.base import Server, Parameter
from core.root import BASE_DIR
from core.utils import HttpProtocolEnum, HttpMethodEnum, HiddenDefaultDict, DynamicFreezeObject
from servers.source.bug_file_controller import generate_bug_file

dotenv.load_dotenv(dotenv_path=Path(BASE_DIR) / "core" / ".env")


class ProductStatus(str, Enum):
    NORMAL = "normal"


class ProjectStatus(str, Enum):
    DOING = "doing"


class BugStatus(str, Enum):
    ALL = "all"
    UN_CLOSED = "unclosed"


class ZenDaoParameter(Parameter):

    def __init__(self, zendao_username=None,
                 zendao_password=None,
                 zendao_execution_id: int = None,
                 zendao_product_id: int = None,
                 zendao_bug_limit: int = None,
                 zendao_test_task_id: int = None,
                 zendao_version_id: int = None,
                 zendao_bug_status="all",
                 zendao_bug_filter_title=None,
                 zendao_bug_filter_title_not_contains=None,
                 *args, **kwargs):
        self.zendao_username = zendao_username
        self.zendao_password = zendao_password
        self.zendao_execution_id = int(zendao_execution_id)
        self.zendao_product_id = int(zendao_product_id)
        self.zendao_test_task_id = int(zendao_test_task_id)
        self.zendao_version_id = int(zendao_version_id)
        self.zendao_bug_limit = int(zendao_bug_limit) if zendao_bug_limit else 500
        self.zendao_bug_status = BugStatus.ALL.value if zendao_bug_status == BugStatus.ALL.value else BugStatus.UN_CLOSED.value
        self.zendao_bug_filter_title = zendao_bug_filter_title
        self.zendao_bug_filter_title_not_contains = zendao_bug_filter_title_not_contains


class ZenDaoSearchParameter(Parameter):

    def __init__(self, zendao_username=None, zendao_password=None, *args, **kwargs):
        self.zendao_username = zendao_username
        self.zendao_password = zendao_password


class _Tokenization:

    def __init__(self, token=None, *args, **kwargs):
        self.Token = token


class Product:
    def __init__(self, id=None, name=None, status=None, *args, **kwargs):
        self.id = id
        self.name = name
        self.status = status


class Project:
    def __init__(self, id=None, name=None, *args, **kwargs):
        self.id = id
        self.name = name


class Execution:
    def __init__(self, id=None, name=None, *args, **kwargs):
        self.id = id
        self.name = name


class Version:
    def __init__(self, id=None, name=None, bugs=None, *args, **kwargs):
        self.id = id
        self.name = name
        self.bugs = bugs


class Bug:
    def __init__(self, severity=None, resolution=None, execution=None, id=None, title=None, *args, **kwargs):
        self.severity = severity
        self.resolution = resolution
        self.execution = execution
        self.id = id
        self.title = title


class Task:

    def __init__(self, begin=None, end=None, executionName=None, name=None, id=None, *args, **kwargs):
        self.begin = begin
        self.end = end
        self.executionName = executionName
        self.name = name
        self.id = id


@ServerRunner(ZenDaoParameter)
class ZenDaoServer(Server):

    @classmethod
    def ping(cls) -> bool:
        pass

    def __init__(self):
        super().__init__(domain=os.getenv("ZENDAO_BASE_DOMAIN"), protocol=HttpProtocolEnum.HTTPS)

    def set_base_headers(self):
        self.sender.headers = {"Content-Type": "application/json"}

    def tokenization(self):
        self.sender.method = HttpMethodEnum.POST
        self.sender.path = os.getenv("ZENDAO_LOGIN_PATH")
        self.sender.json = {"account": self.parameter.zendao_username or os.getenv("ZENDAO_USERNAME"),
                            "password": self.parameter.zendao_password or os.getenv("ZENDAO_PASSWORD")}
        self.sender.send()

    def set_tokenization_headers(self):
        _tokenization_instance = _Tokenization(**self.sender.result.json())
        if _tokenization_instance.Token is None:
            raise report_exception.HttpResponseException(
                _const.EXCEPTION.Http_Login_Failed_Exception % ("【禅道登录异常】" + str(self.sender.result.json()),))
        self.sender.patch_headers(_tokenization_instance.__dict__)

    def get_headers(self):
        return self.sender.headers

    def get_products(self):
        def _products_filter(product_list) -> list[Product]:
            res = []
            for product in product_list:
                _self_product = Product(**product)
                if _self_product.status == ProductStatus.NORMAL.value:
                    res.append(_self_product)
            return res

        self.sender.path = os.getenv("ZENDAO_PRODUCT_LIST")
        self.sender.method = HttpMethodEnum.GET
        result: Response = self.sender.send()

        class _ProductsFilter:
            def __init__(self, products=None, *args, **kwargs):
                self.products = products

        products = _ProductsFilter(**result.json()).products
        return _products_filter(products)

    def get_project(self, product_id):
        class _ProjectParams:
            def __init__(self, product_id):
                self.product = product_id
                self.status = ProjectStatus.DOING

        class _ProjectFilter:
            def __init__(self, projects=None, *args, **kwargs):
                self.projects = projects

        self.sender.path = os.getenv("ZENDAO_PROJECT_LIST")
        self.sender.method = HttpMethodEnum.GET
        self.sender.params = _ProjectParams(product_id).__dict__
        result: Response = self.sender.send()
        return [Project(**project) for project in _ProjectFilter(**result.json()).projects]

    def get_executions(self, project_id):
        class _ExecutionFilter:
            def __init__(self, executions, *args, **kwargs):
                self.executions = executions

        self.sender.path = os.getenv("ZENDAO_EXECUTION_LIST") % (project_id,)
        self.sender.method = HttpMethodEnum.GET
        self.sender.clean_params()
        result: Response = self.sender.send()
        return [Execution(**execution) for execution in _ExecutionFilter(**result.json()).executions]

    def get_versions(self, executions_id):
        self.sender.path = os.getenv("ZENDAO_VERSION_LIST") % (executions_id,)
        self.sender.method = HttpMethodEnum.GET
        self.sender.clean_params()
        result: Response = self.sender.send()
        return [Version(**version) for version in result.json()["builds"]]

    def _set_bug_list_by_version(self, executions_id):
        self.sender.path = os.getenv("ZENDAO_VERSION_LIST") % (executions_id,)
        self.sender.method = HttpMethodEnum.GET
        self.sender.clean_params()
        result: Response = self.sender.send()
        for version in result.json()["builds"]:
            version = Version(**version)
            if version.id == self.parameter.zendao_version_id:
                return version

    def get_bug_info(self, product_id, execution_id, version: Version):
        self.sender.path = os.getenv("ZENDAO_BUG_LIST") % (str(product_id),)
        self.sender.method = HttpMethodEnum.GET

        class _BugFilter:
            def __init__(self, bugs, *args, **kwargs):
                self.bugs = bugs

        class _BugParams:
            def __init__(self, limit, status):
                if limit:
                    self.limit = limit
                self.status = status

        def _gen_bug_summary_info(bug_list):
            class ResultDict:

                def __init__(self):
                    self.severity_mapping = HiddenDefaultDict(int, self.update_total)
                    self.resolution_mapping = HiddenDefaultDict(int)
                    self.postponed_bugs = {}
                    self.total = 0

                def update_total(self, _, old_value, new_value):
                    self.total += (new_value - old_value)

            result_dict = ResultDict()
            bug_origin_data = []
            for bug_data in bug_list:
                bug = Bug(**bug_data)
                result_dict.severity_mapping[bug.severity] += 1
                result_dict.resolution_mapping[bug.resolution] += 1
                if bug.resolution == 'postponed':
                    result_dict.postponed_bugs[bug.id] = bug.title
                bug_origin_data.append(bug_data)
            return result_dict.__dict__, bug_origin_data

        self.sender.params = _BugParams(self.parameter.zendao_bug_limit, self.parameter.zendao_bug_status).__dict__

        def bug_filter_callback(bug):
            return (
                    bug["id"] in version.bugs and
                    (
                            self.parameter.zendao_bug_filter_title is None or
                            self.parameter.zendao_bug_filter_title in bug["title"]
                    ) and
                    (
                            self.parameter.zendao_bug_filter_title_not_contains is None or
                            self.parameter.zendao_bug_filter_title_not_contains not in bug["title"]
                    )
            )

        filtered_bugs: List = self.sender.send(stream=True,
                                               filter_callback=bug_filter_callback,
                                               target="bugs.item")
        self.sender.clean_params()
        bug_list = _BugFilter(filtered_bugs).bugs
        return _gen_bug_summary_info(bug_list)

    def _get_test_task(self, call_back, product_id):
        self.sender.params = {
            "product": product_id
        }
        self.sender.path = os.getenv("ZENDAO_TESTTASKS_LIST")
        self.sender.method = HttpMethodEnum.GET
        filter_tasks: List = self.sender.send(stream=True,
                                              filter_callback=call_back,
                                              target="testtasks.item")
        return filter_tasks

    def get_test_tasks(self, product_id):
        test_tasks = self._get_test_task(lambda x: True, product_id)
        return [Task(**test_task) for test_task in test_tasks]

    def get_test_task(self, task_id, product_id):
        filter_tasks = self._get_test_task(lambda task: task["id"] == task_id, product_id)
        test_task = filter_tasks[0] if filter_tasks else None
        if test_task is None:
            raise report_exception.SystemParameterException(
                "参数错误：--zendao_test_task_id：{self.parameter.zendao_test_task_id}，该参数无法找到测试单")
        return Task(**test_task)

    def run(self, *args, **kwargs):
        execution_id = self.parameter.zendao_execution_id
        product_id = self.parameter.zendao_product_id
        version: Version = self._set_bug_list_by_version(execution_id)
        # 获取BUG列表信息
        bug_info, bug_origin_data = self.get_bug_info(product_id, execution_id, version)
        # 获取任务列表信息
        task_info = self.get_test_task(self.parameter.zendao_test_task_id, product_id)
        # 创建BUG文件
        bug_file_path = generate_bug_file(
            task_info.executionName.replace(" ", "") + "_" + os.getenv("ZENDAO_BUG_FILE_NAME"),
            bug_origin_data)
        return DynamicFreezeObject(bug=bug_info, task=task_info.__dict__, bug_file_path=bug_file_path)


ZenDaoProduct = Product
ZenDaoProject = Project
ZenDaoExecution = Execution
ZenDaoBug = Bug
ZenDaoTestTask = Task
ZenDaoVersion = Version


class HelpAction:

    def __init__(self, zendao_username=None, zendao_password=None, get_products=None, get_projects=None,
                 get_executions=None, get_test_tasks=None, get_versions=None, *args, **kwargs):
        self.zendao_username = zendao_username
        self.zendao_password = zendao_password
        self.get_products = get_products
        self.get_projects = get_projects
        self.get_executions = get_executions
        self.get_test_tasks = get_test_tasks
        self.get_versions = get_versions

    def get_info(self):
        if any(x is not None for x in
               [self.get_products, self.get_projects, self.get_executions, self.get_test_tasks, self.get_versions]):
            if self.zendao_username is None or self.zendao_password is None:
                raise SystemParameterException("您正在查询禅道信息，参数：zendao_username、zendao_password不能为空。")
            zds = ZenDaoServer()
            zds.parameter = ZenDaoSearchParameter(**self.__dict__)
            zds.initialize()
        else:
            return False
        if self.get_products:
            product_list: list[ZenDaoProduct] = zds.get_products()
            for product in product_list:
                print(f"产品ID：{product.id}，产品名：{product.name}，产品状态：{product.status}")
            return True
        if self.get_projects:
            project_list: list[ZenDaoProject] = zds.get_project(self.get_projects)
            for project in project_list:
                print(f"项目ID:{project.id}，项目名称：{project.name}")
            return True
        if self.get_executions:
            execution_list: list[ZenDaoExecution] = zds.get_executions(self.get_executions)
            for execution in execution_list:
                print(f"版本ID：{execution.id}，执行名称：{execution.name}")
            return True
        if self.get_test_tasks:
            task_list: list[ZenDaoTestTask] = zds.get_test_tasks(self.get_test_tasks)
            for test_task in task_list:
                print(f"测试单ID：{test_task.id}，测试单名称：{test_task.name}")
            return True
        if self.get_versions:
            version_list: list[ZenDaoVersion] = zds.get_versions(self.get_versions)
            for version in version_list:
                print(f"版本ID：{version.id}，版本名称：{version.name}")
            return True
        return False
