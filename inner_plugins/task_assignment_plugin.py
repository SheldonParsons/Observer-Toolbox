#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :task_assignment_plugin.py
# @Time      :2025/4/27 9:00
# @Author    :邓某人
# @Function  :
from typing import Union

from core.deco import inner_plugin
from core.base import T, RunnerResult
from core.generator import ServicePlugin

from core.tooller.async_server import AsyncServerController
from core.utils import DynamicFreezeObject
from inner_plugins.source.task_assignment_controller import read_specific_columns


@inner_plugin
class TaskFilePlugin(ServicePlugin):
    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        save_path_list = AsyncServerController().generator_files(path="TaskFile")
        excel_list = list(filter(is_xlsx, save_path_list))[0]
        xmind_file_list = [file for file in save_path_list if file not in excel_list]
        excel_data = read_specific_columns(excel_list)
        return DynamicFreezeObject(excel_data=excel_data, xmind_file_list=xmind_file_list).__dict__


def is_xlsx(file_name):
    return file_name.endswith('.xlsx') and "测试任务分配" in file_name
