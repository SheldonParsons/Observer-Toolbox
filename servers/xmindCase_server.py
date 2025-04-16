# -*-coding: Utf-8 -*-
# @File : xmindCase_server .py
# author: A80723
# Time：2025/4/14 
# Description：
from core.base import Server, Parameter
from core.deco import ServerRunner
from core.root import BASE_DIR
from core.tooller.async_server import AsyncServerController
from core.utils import DynamicObject
from servers.source.xmind_case_controller import sum_statistics_data
from pathlib import Path
import os

class XmindCaseParameter(Parameter):
    def __init__(self,xmind_file_path=None, *args, **kwargs):
        self.xmind_file_path=xmind_file_path

@ServerRunner(XmindCaseParameter)
class XmindCaseServer(Server):
    @classmethod
    def ping(cls) -> bool:
        pass

    def __init__(self):
        super().__init__()
        self.xmind_file_path=""
    def down_load_file(self):
        xmind_file_list=AsyncServerController().generator_files(path='xmindcase')
        return xmind_file_list
    def get_ximnd_path(self):
        '''
            从路径里获取xmind文件地址
        '''
        pass
    def get_xmind_path(self):
        dir = Path(BASE_DIR)
        directory = dir / "core" / "xmindcase"
        case_list = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                # 输出文件的完整路径
                if 'xmind' in file:
                    file_path = os.path.join(root, file)
                    case_list.append(file_path)
        return case_list
    def run(self,  *args, **kwargs):
        #通过zentao获取项目和版本，拼接需要
        from core.generator import GlobalData
        task_info = GlobalData.system_parameters.__dict__['taskinfo']
        self.zip_path=task_info["executionName"].replace(" ", "") + "_" + os.getenv("XMIND_CASE_ZIP_NAME")
        # self.xmind_file_path=self.down_load_file()
        # 暂时改为循环读取指定路径
        self.xmind_file_path=self.get_xmind_path()
        case_result, zip_path =sum_statistics_data(self.xmind_file_path,self.zip_path)
        return DynamicObject(case_result=case_result, zip_path=zip_path).__dict__
