from enum import Enum
from pprint import pprint
from typing import List

import dotenv
import os

from requests.models import Response

from core._config import _const
from core._config._exception import HttpResponseException
from core.deco import ServerRunner
from core.base import Server, Parameter
from core.utils import HttpProtocolEnum, HttpMethodEnum, HiddenDefaultDict, DynamicObject
from core.tooller.async_server import AsyncServerController
from servers.source.bug_file_controller import generate_bug_file

dotenv.load_dotenv()


class ProductStatus(str, Enum):
    NORMAL = "normal"


class ProjectStatus(str, Enum):
    DOING = "doing"


class BugStatus(str, Enum):
    ALL = "all"


class ZenDaoParameter(Parameter):

    def __init__(self, zendao_username=None, zendao_password=None, zendao_execution_id: int = None,
                 zendao_product_id: int = None,
                 zendao_bug_limit: int = 2000, zendao_bug_status="all",
                 *args, **kwargs):
        self.zendao_username = zendao_username
        self.zendao_password = zendao_password
        self.zendao_execution_id = int(zendao_execution_id)
        self.zendao_product_id = int(zendao_product_id)
        self.zendao_bug_limit = int(zendao_bug_limit)
        self.zendao_bug_status = zendao_bug_status


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


class Bug:
    def __init__(self, severity=None, resolution=None, execution=None, id=None, title=None, *args, **kwargs):
        self.severity = severity
        self.resolution = resolution
        self.execution = execution
        self.id = id
        self.title = title


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
            raise HttpResponseException(
                _const.EXCEPTION.Http_Login_Failed_Exception % (self.sender.result.json(),))
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
        self.sender.params = _ProjectParams(product_id).__dict__
        result: Response = self.sender.send()
        return [Project(**project) for project in _ProjectFilter(**result.json()).projects]

    def get_executions(self, project_id):
        class _ExecutionFilter:
            def __init__(self, executions, *args, **kwargs):
                self.executions = executions

        self.sender.path = os.getenv("ZENDAO_EXECUTION_LIST") % (project_id,)
        self.sender.method = HttpMethodEnum.GET
        result: Response = self.sender.send()
        return [Execution(**execution) for execution in _ExecutionFilter(**result.json()).executions]

    def get_bug_info(self, product_id, execution_id):
        self.sender.path = os.getenv("ZENDAO_BUG_LIST") % (str(product_id),)
        self.sender.method = HttpMethodEnum.GET

        class _BugFilter:
            def __init__(self, bugs, *args, **kwargs):
                self.bugs = bugs

        class _BugParams:
            def __init__(self, limit, status):
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
                if bug.execution == execution_id:
                    result_dict.severity_mapping[bug.severity] += 1
                    result_dict.resolution_mapping[bug.resolution] += 1
                    if bug.resolution == 'postponed':
                        result_dict.postponed_bugs[bug.id] = bug.title
                    bug_origin_data.append(bug_data)
            return result_dict.__dict__, bug_origin_data

        self.sender.params = _BugParams(self.parameter.zendao_bug_limit, self.parameter.zendao_bug_status).__dict__
        bug_result: Response = self.sender.send()
        bug_list = _BugFilter(**bug_result.json()).bugs
        return _gen_bug_summary_info(bug_list)

    def get_task_info(self, execution_id):
        class _GetTask:

            def __init__(self, testtasks: List, *args, **kwargs):
                def _get_task():
                    for task in testtasks:
                        task = DynamicObject(**task)
                        if task.execution == execution_id:
                            return task.__dict__

                self.begin = None
                self.end = None
                self.executionName = None
                self.__dict__.update({k: v for k, v in _get_task().items() if k in self.__dict__})

            def get_task(self):
                if None in (self.begin, self.end, self.executionName):
                    raise HttpResponseException(_const.EXCEPTION.HTTP_Get_Task_Failed_Exception % (execution_id,))
                return self.__dict__

        self.sender.path = os.getenv("ZENDAO_TESTTASKS_LIST")
        del self.sender.params["status"]
        task_result: Response = self.sender.send()
        return _GetTask(**task_result.json()).get_task()

    def run(self, *args, **kwargs):
        # 借个地方做测试，嘻嘻
        save_path_list = AsyncServerController().generator_files(path="kkk/eee")
        pprint(save_path_list)
        execution_id = self.parameter.zendao_execution_id
        product_id = self.parameter.zendao_product_id
        # 获取BUG列表信息
        bug_info, bug_origin_data = self.get_bug_info(product_id, execution_id)
        # 获取任务列表信息
        task_info = self.get_task_info(execution_id)
        # 创建BUG文件
        bug_file_path = generate_bug_file(
            task_info["executionName"].replace(" ", "") + "_" + os.getenv("ZENDAO_BUG_FILE_NAME"),
            bug_origin_data)
        return DynamicObject(bug=bug_info, task=task_info, bug_file_path=bug_file_path).__dict__


ZenDaoProduct = Product
ZenDaoProject = Project
ZenDaoExecution = Execution
ZenDaoBug = Bug
