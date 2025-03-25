import json
from enum import Enum

import dotenv
import os

from requests.models import Response

from core._config import _const
from core._config._exception import HttpResponseException
from core._deco import ServerRunner
from core.base import Server, Parameter
from core.utils import HttpProtocolEnum, HttpMethodEnum

dotenv.load_dotenv()


class ProductStatus(str, Enum):
    NORMAL = "normal"


class ProjectStatus(str, Enum):
    DOING = "doing"


class BugStatus(str, Enum):
    ALL = "all"


class ZenDaoParameter(Parameter):

    def __init__(self, zendao_username=None, zendao_password=None, zendao_execution_id=None, zendao_product_id=None,
                 zendao_bug_limit=2000, zendao_bug_status="all",
                 *args, **kwargs):
        self.zendao_username = zendao_username
        self.zendao_password = zendao_password
        self.zendao_execution_id = zendao_execution_id
        self.zendao_product_id = zendao_product_id
        self.zendao_bug_limit = zendao_bug_limit
        self.zendao_bug_status = zendao_bug_status


@ServerRunner(ZenDaoParameter)
class ZenDaoServer(Server):

    def __init__(self, parameter: ZenDaoParameter = None):
        super().__init__(os.getenv("ZENDAO_BASE_DOMIAN"), HttpProtocolEnum.HTTPS)
        self.parameter = ZenDaoParameter() if parameter is None else parameter
        self.set_base_headers()
        self.tokenization()
        self.set_tokenization_headers()

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
        def __init__(self, severity=None, resolution=None, execution=None, *args, **kwargs):
            self.severity = severity
            self.resolution = resolution
            self.execution = execution

    def set_base_headers(self):
        self.sender.headers = {"Content-Type": "application/json"}

    def tokenization(self):
        self.sender.method = HttpMethodEnum.POST
        self.sender.path = os.getenv("ZENDAO_LOGIN_PATH")
        self.sender.json = {"account": self.parameter.zendao_username or os.getenv("ZENDAO_USERNAME"),
                            "password": self.parameter.zendao_password or os.getenv("ZENDAO_PASSWORD")}
        self.sender.send()

    def set_tokenization_headers(self):
        _tokenization_instance = self._Tokenization(**json.loads(self.sender.result.text))
        if _tokenization_instance.Token is None:
            raise HttpResponseException(
                _const.EXCEPTION.HttpLoginFailedException % (
                    json.dumps(self.sender.result.json(), ensure_ascii=False),))
        self.sender.patch_headers(_tokenization_instance.__dict__)

    def get_headers(self):
        return self.sender.headers

    def get_products(self):
        def _products_filter(product_list) -> list['Product']:
            res = []
            for product in product_list:
                _self_product = self.Product(**product)
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
        return [self.Project(**project) for project in _ProjectFilter(**result.json()).projects]

    def get_executions(self, project_id):
        class _ExecutionFilter:
            def __init__(self, executions, *args, **kwargs):
                self.executions = executions

        self.sender.path = os.getenv("ZENDAO_EXECUTION_LIST") % (project_id,)
        self.sender.method = HttpMethodEnum.GET
        result: Response = self.sender.send()
        return [self.Execution(**execution) for execution in _ExecutionFilter(**result.json()).executions]

    def run(self, *args, **kwargs):
        execution_id = self.parameter.zendao_execution_id
        product_id = self.parameter.zendao_product_id
        self.sender.path = os.getenv("ZENDAO_BUG_LIST") % (str(product_id),)
        self.sender.method = HttpMethodEnum.GET

        class _BugFilter:
            def __init__(self, bugs, *args, **kwargs):
                self.bugs = bugs

        class _BugParams:
            def __init__(self, limit, status):
                self.limit = limit
                self.status = status

        def _bug_filter(bug_list):
            res = []
            result_dict = {}
            for bug in bug_list:
                _self_bug = self.Bug(**bug)
                if _self_bug.execution == execution_id:
                    res.append(_self_bug)
                    result_dict.setdefault(_self_bug.severity, 0)
                    result_dict[_self_bug.severity] += 1
                    result_dict.setdefault(_self_bug.resolution, 0)
                    result_dict[_self_bug.resolution] += 1
            result_dict.setdefault("total", len(res))
            return res, result_dict

        self.sender.params = _BugParams(self.parameter.zendao_bug_limit, self.parameter.zendao_bug_status).__dict__
        result: Response = self.sender.send()
        bug_list = _BugFilter(**result.json()).bugs
        res, result_dict = _bug_filter(bug_list)
        return res, result_dict


ZenDaoProduct = ZenDaoServer.Product
ZenDaoProject = ZenDaoServer.Project
ZenDaoExecution = ZenDaoServer.Execution
ZenDaoBug = ZenDaoServer.Bug
