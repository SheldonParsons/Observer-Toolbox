# -*-coding: Utf-8 -*-
# @File : xmind_case_result .py
# author: A80723, sheldon
# Time：2025/3/19 
# Description：
import copy
import zipfile
from pathlib import Path
from typing import List, Union

from xmindparser import xmind_to_dict
from core.root import get_base_dir
from core.utils import singleton


class CollectionResult:

    def __init__(self, zip_path):
        self.results = []
        self.case_count = 0
        self.undo = 0
        self.success = 0
        self.failed = 0
        self.passed_rate = 0
        self.zip_path = zip_path
        self.text = ""

    def append(self, result):
        self.results.append(result)
        self.undo += result.undo
        self.success += result.success
        self.failed += result.failed
        self.case_count += len(result.results)
        self.passed_rate = round(self.success / self.case_count * 100, 2)
        self.text = self.set_text()

    def set_text(self):
        return "本次版本设计了 %s 条用例，通过了 %s 个用例，失败了 %s 个用例，未执行 %s 个用例，通过率 %s" % (
            len(self.results), self.success, self.failed, self.undo, self.passed_rate,)


@singleton
class FileResult:

    def __init__(self):
        self._data_origin_()

    def _data_origin_(self):
        self.results = []
        self.undo = 0
        self.success = 0
        self.failed = 0
        self.passed_rate = 0
        self.file_path = ""

    class _NodeResult:
        def __init__(self, title, path, makers):
            self.title = str(title)
            self.path = path
            self.makers = makers

    def append(self, title, path, makers):
        node_result = self._NodeResult(title, path, makers)
        self.results.append(node_result.__dict__)
        if node_result.makers is None:
            self.undo += 1
        elif 'task-done' in node_result.makers:
            self.success += 1
        elif "symbol-exclam" in node_result.makers:
            self.failed += 1

    def get_passed_rate(self):
        self.passed_rate = round(self.success / len(self.results) * 100, 2)
        return "{:.2f}%".format(self.passed_rate)

    def reset(self):
        self._data_origin_()


class Node:

    def __init__(self, title="", topics=None, makers=None, parent_node=None, *args, **kwargs):
        self.parent_node = parent_node
        self.title = title
        self.topic = self.topic_instance(topics)
        self.makers = makers
        self.is_final = self.topic is None

    def topic_instance(self, topic):
        if topic is None:
            return None
        if isinstance(topic, dict):
            return self.__class__(**topic, parent_node=self)
        if isinstance(topic, list):
            return [self.__class__(**node, parent_node=self) for node in topic]

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if self.parent_node is None:
            self.cache_path = [value]
        else:
            self.cache_path = [*self.parent_node.cache_path, value]
        self._title = value

    @property
    def is_final(self):
        return self._is_final

    @is_final.setter
    def is_final(self, value):
        if value:
            FileResult().append(self.title, self.cache_path, self.makers)
        self._is_final = value


def analyze_xmind(dir_list, zip_name):
    zip_path = get_base_dir() / zip_name
    collection_result = CollectionResult(zip_path)
    for file_path in dir_list:
        dict_data = xmind_to_dict(file_path)
        Node(**dict_data[0]['topic'])
        file_result = FileResult()
        file_result.file_path = file_path
        copied_file_result = copy.deepcopy(file_result)
        collection_result.append(copied_file_result)
        file_result.reset()
    zip_files(dir_list, zip_path)
    return collection_result


def zip_files(case_list: List[Union[str, Path]], output_path: Union[str, Path]) -> Path:
    """
    打包文件列表为 zip 文件。

    :param case_list: 要打包的文件路径列表
    :param output_path: 输出 zip 文件路径
    :return: 输出 zip 文件的 Path 对象
    """
    output_path = Path(output_path)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in case_list:
            file_path = Path(file)
            if file_path.is_file():
                zipf.write(file_path, arcname=file_path.name)
    return output_path
