# -*-coding: Utf-8 -*-
# @File : xmind_test_case_plugin.py
# author: A80723, sheldon
# Time：2025/3/19
# Description：分析XMind文件并生成测试报告
import zipfile
from pathlib import Path
from typing import List, Union

from xmindparser import xmind_to_dict
from core.root import get_base_dir


class AggregatedResult:

    def __init__(self):
        self.undo = 0
        self.success = 0
        self.failed = 0
        self.passed_rate = 0.0
        self.case_count = 0

    def aggregate(self, result: 'AggregatedResult'):
        self.undo += result.undo
        self.success += result.success
        self.failed += result.failed
        self.case_count += result.case_count
        self._update_passed_rate()

    def _update_passed_rate(self):
        if self.case_count > 0:
            self.passed_rate = round(self.success / self.case_count * 100, 2)
        else:
            self.passed_rate = 0.0


class TagResult(AggregatedResult):
    class _NodeResult:
        def __init__(self, title: str, path: List[str], makers: List[str]):
            self.title = title
            self.path = path
            self.makers = makers

        def __repr__(self):
            return str(self.__dict__)

    def __init__(self):
        super().__init__()
        self.node_results: List[TagResult._NodeResult] = []
        self.title = ""

    def append(self, title: str, path: List[str], makers: List[str]):
        node = self._NodeResult(title, path, makers)
        self.node_results.append(node)

        if not makers:
            self.undo += 1
        elif 'task-done' in makers:
            self.success += 1
        elif "symbol-exclam" in makers:
            self.failed += 1

        self.case_count = len(self.node_results)
        self._update_passed_rate()

    def __repr__(self):
        return str(self.__dict__)


class FileResult(AggregatedResult):
    def __init__(self, file_path: Union[str, Path]):
        super().__init__()
        self.file_path = Path(file_path)
        self.tag_results: List[TagResult] = []

    def append(self, result: TagResult):
        self.tag_results.append(result)
        super().aggregate(result)

    def __repr__(self):
        return str(self.__dict__)


class CollectionResult(AggregatedResult):
    def __init__(self, zip_path: Union[str, Path]):
        super().__init__()
        self.zip_path = Path(zip_path)
        self.text = ""
        self.file_results: List[FileResult] = []

    def append(self, result: FileResult):
        self.file_results.append(result)
        super().aggregate(result)
        self.text = self._generate_summary_text()

    def _generate_summary_text(self) -> str:
        return (
            f"本次版本设计了 {self.case_count} 条用例，"
            f"通过了 {self.success} 个用例，"
            f"失败了 {self.failed} 个用例，"
            f"未执行 {self.undo} 个用例，"
            f"通过率 {self.passed_rate}%"
        )

    def __repr__(self):
        return str(self.__dict__)


class Node:
    def __init__(self, tag_result: TagResult, title: str = "", topics: Union[dict, list] = None,
                 makers: List[str] = None, parent_node: 'Node' = None):
        self.cache_path = []
        self.parent_node: Node = parent_node
        self.tag_result = tag_result
        self.title = title
        self.makers = makers or []
        self.topic = self._parse_topics(topics)
        self.is_final = self.topic is None

    def _parse_topics(self, topics: Union[dict, list]) -> Union[None, 'Node', List['Node']]:
        if topics is None:
            return None
        if isinstance(topics, dict):
            return Node(self.tag_result, parent_node=self, **topics)
        return [Node(self.tag_result, parent_node=self, **node) for node in topics]

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        self.cache_path = self.parent_node.cache_path.copy() if self.parent_node else []
        self.cache_path.append(value)

    @property
    def is_final(self):
        return self._is_final

    @is_final.setter
    def is_final(self, value: bool):
        self._is_final = value
        if value:
            self.tag_result.append(self.title, self.cache_path, self.makers)


def analyze_xmind(file_paths: List[Union[str, Path]], zip_name: str) -> CollectionResult:
    """
    分析XMind文件集合并生成聚合统计信息

    :param file_paths: XMind文件路径列表
    :param zip_name: 输出压缩包名称
    :return: 汇总结果对象
    """
    collection = CollectionResult(get_base_dir() / zip_name)

    for path in file_paths:
        file_result = FileResult(path)

        try:
            for sheet in xmind_to_dict(path):
                tag_result = TagResult()
                tag_result.title = sheet.get("title", "未识别title")
                Node(tag_result, **sheet["topic"])
                file_result.append(tag_result)
        except Exception as e:
            continue

        collection.append(file_result)

    _create_archive(file_paths, collection.zip_path)
    return collection


def _create_archive(files: List[Union[str, Path]], output_path: Path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            file = Path(file)
            if file.exists() and file.is_file():
                archive.write(file, arcname=file.name)
