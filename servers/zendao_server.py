from enum import Enum
from typing import List

import dotenv
import os

import openpyxl
from requests.models import Response

from core._config import _const
from core._config._exception import HttpResponseException
from core.deco import ServerRunner
from core.base import Server, Parameter
from core.utils import HttpProtocolEnum, HttpMethodEnum, HiddenDefaultDict, DynamicObject
from openpyxl import Workbook
from openpyxl.styles import Alignment


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
    def __init__(self, severity=None, resolution=None, execution=None, *args, **kwargs):
        self.severity = severity
        self.resolution = resolution
        self.execution = execution


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
        
        def export_zentaobugs(data, output_path="core/temp/bugs.xlsx"):
            """导出禅道Bug数据到Excel文件
            
            Args:
                data: Bug数据列表，每个元素为一个字典
                output_path: 输出文件路径（默认：output/bugs.xlsx）
            """
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # 创建Excel工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = "禅道Bug列表"

            # 定义表头与字段映射关系
            headers = [
                ("Bug编号", "id", "无"),
                ("Bug标题", "title", "无标题"),
                ("严重程度", "severity", "未指定"),
                ("优先级", "pri", "未指定"),
                ("重现步骤", "steps", "无描述"),
                ("bug状态", "status", "状态未知"),
                ("由谁创建", "openedBy", "匿名用户"),
                ("指派给", "assignedTo", "无指派"),
                ("创建日期", "openedDate", "无日期")
            ]

            # 写入表头并设置格式
            header_names = [h[0] for h in headers]
            ws.append(header_names)
            for col in ws[1]:
                col.alignment = Alignment(horizontal='center', vertical='center')
                col.font = openpyxl.styles.Font(bold=True)

            # 处理并写入数据
            for bug in data:
                row = []
                for header in headers:
                    field_name = header[1]
                    default_value = header[2]
                    
                    # 获取字段值并处理异常情况
                    value = bug.get(field_name)
                    if value in (None, "", []):
                        value = default_value
                    elif isinstance(value, list):
                        value = "\n".join(map(str, value))
                    row.append(str(value).strip() if value else default_value)

                ws.append(row)

            # 设置自动列宽（近似值）
            for column in ws.columns:
                max_length = 0
                column = list(column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                ws.column_dimensions[column[0].column_letter].width = adjusted_width

            # 保存文件
            wb.save(output_path)
            print(f"成功导出Bug数据到：{os.path.abspath(output_path)}")

        def _gen_bug_summary_info(bug_list):
            class ResultDict:

                def __init__(self):
                    self.severity_mapping = HiddenDefaultDict(int, self.update_total)
                    self.resolution_mapping = HiddenDefaultDict(int)
                    self.total = 0

                def update_total(self, _, old_value, new_value):
                    self.total += (new_value - old_value)

            result_dict = ResultDict()
            export_bug_list = []
            for bug in bug_list:
                _self_bug = Bug(**bug)
                if _self_bug.execution == execution_id:
                    result_dict.severity_mapping[_self_bug.severity] += 1
                    result_dict.resolution_mapping[_self_bug.resolution] += 1
                    export_bug_list.append(bug)
            export_zentaobugs(export_bug_list)
            return result_dict.__dict__

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
        execution_id = self.parameter.zendao_execution_id
        product_id = self.parameter.zendao_product_id

        bug_info = self.get_bug_info(product_id, execution_id)
        task_info = self.get_task_info(execution_id)
        return DynamicObject(bug=bug_info, task=task_info).__dict__


ZenDaoProduct = Product
ZenDaoProject = Project
ZenDaoExecution = Execution
ZenDaoBug = Bug
