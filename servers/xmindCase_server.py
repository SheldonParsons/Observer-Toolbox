# -*-coding: Utf-8 -*-
# @File : xmindCase_server .py
# author: A80723
# Time：2025/4/14 
# Description：
from core.base import Server, Parameter
from core.deco import ServerRunner
from core.async_server import AsyncServerController
from core.utils import DynamicObject
from servers.source.xmind_case_result import sum_statistics_data
from core.root import get_base_dir
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
            从路径里获取
        '''
    def run(self,  *args, **kwargs):
        #通过zentao获取项目和版本，拼接需要
        self.zip_path=get_base_dir()
        self.xmind_file_path=self.down_load_file()
        case_result, zip_path =sum_statistics_data(self.xmind_file_path)
        return DynamicObject(case_result=case_result, zip_path=zip_path).__dict__
