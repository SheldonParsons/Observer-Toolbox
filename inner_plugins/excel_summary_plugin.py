#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :excel_summary_plugin.py
# @Time      :2025/4/27 9:00
# @Author    :邓某人,Sheldon
# @Function  :
from typing import Union

from core.generator import report_exception
from core.deco import inner_plugin
from core.base import T, RunnerResult
from core.generator import ServicePlugin

from core.tooller.async_server import AsyncServerController
from core.utils import DynamicFreezeObject
from inner_plugins.source.excel_tree_controller import get_excel_tree_dict

SUMMARY_EXCEL_NAME = '测试任务分配.xlsx'


@inner_plugin
class ExcelSummaryPlugin(ServicePlugin):
    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        save_path_list = AsyncServerController().generator_files(path="global")
        excel_file_path = next(filter(lambda file_path: SUMMARY_EXCEL_NAME in file_path, save_path_list), None)
        if excel_file_path is None:
            raise report_exception.FileException(f"文件不存在：{SUMMARY_EXCEL_NAME}")
        xmind_file_list = [file_path for file_path in save_path_list if file_path.endswith(".xmind")]
        excel_data, pic_list = get_excel_tree_dict(excel_file_path)
        return DynamicFreezeObject(summary_data=excel_data, pic_list=pic_list, xmind_file_list=xmind_file_list)
