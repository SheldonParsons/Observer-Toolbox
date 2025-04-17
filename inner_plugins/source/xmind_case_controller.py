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


def _avg_func(self, result):
    self.undo += result.undo
    self.success += result.success
    self.failed += result.failed
    self.passed_rate = round(self.success / self.case_count * 100, 2)


@singleton
class TagResult:

    def __init__(self):
        self._data_origin_()
        self.title = ""

    def _data_origin_(self):
        self.node_results = []
        self.undo = 0
        self.success = 0
        self.failed = 0
        self.passed_rate = 0

    class _NodeResult:
        def __init__(self, title, path, makers):
            self.title = str(title)
            self.path = path
            self.makers = makers

    def append(self, title, path, makers):
        node_result = self._NodeResult(title, path, makers)
        self.node_results.append(node_result.__dict__)
        if node_result.makers is None:
            self.undo += 1
        elif 'task-done' in node_result.makers:
            self.success += 1
        elif "symbol-exclam" in node_result.makers:
            self.failed += 1
        self.get_and_set_passed_rate()

    def get_and_set_passed_rate(self):
        self.passed_rate = round(self.success / len(self.node_results) * 100, 2)
        return "{:.2f}%".format(self.passed_rate)

    def reset(self):
        self._data_origin_()

    def __repr__(self):
        return str(self.__dict__)


class FileResult:

    def __init__(self, file_path):
        self.tag_results = []
        self.file_path = file_path
        self.undo = 0
        self.success = 0
        self.failed = 0
        self.passed_rate = 0
        self.case_count = 0
        self.passed_rate = 0

    def append(self, result: TagResult):
        self.tag_results.append(result)
        self.case_count += len(result.node_results)
        _avg_func(self, result)

    def __repr__(self):
        return str(self.__dict__)


class CollectionResult:

    def __init__(self, zip_path):
        self.file_results = []
        self.case_count = 0
        self.undo = 0
        self.success = 0
        self.failed = 0
        self.passed_rate = 0
        self.zip_path = zip_path
        self.text = ""

    def append(self, result: FileResult):
        self.file_results.append(result)
        self.case_count += result.case_count
        _avg_func(self, result)
        self.text = self.get_text()

    def get_text(self):
        return "本次版本设计了 %s 条用例，通过了 %s 个用例，失败了 %s 个用例，未执行 %s 个用例，通过率 %s%%" % (
            self.case_count, self.success, self.failed, self.undo, self.passed_rate,)

    def __repr__(self):
        return str(self.__dict__)


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
            TagResult().append(self.title, self.cache_path, self.makers)
        self._is_final = value

    def __repr__(self):
        return str(self.__dict__)


def analyze_xmind(dir_list, zip_name):
    zip_path = get_base_dir() / zip_name
    collection_result = CollectionResult(zip_path)
    for file_path in dir_list:
        dict_data = xmind_to_dict(file_path)
        file_result = FileResult(file_path)
        for tag_data in dict_data:
            Node(**tag_data["topic"])
            tag_result = TagResult()
            tag_result.title = tag_data["title"]
            copied_file_result = copy.deepcopy(tag_result)
            file_result.append(copied_file_result)
            tag_result.reset()
        collection_result.append(file_result)
    zip_files(dir_list, zip_path)
    return collection_result


def zip_files(case_list: List[Union[str, Path]], output_path: Union[str, Path]):
    """
    打包文件列表为 zip 文件。

    :param case_list: 要打包的文件路径列表
    :param output_path: 输出 zip 文件路径
    """
    output_path = Path(output_path)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in case_list:
            file_path = Path(file)
            if file_path.is_file():
                zipf.write(file_path, arcname=file_path.name)
