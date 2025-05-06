import functools
from typing import List

row_description_cache_list = []


def register_row(name: str = ""):
    def _wrapper(func):
        @functools.wraps(func)
        def _inner(*args, **kwargs):
            row_list = func(*args, **kwargs)
            for row in row_list:
                row += [EmptyCell()] * (4 - len(row))
            return row_list

        row_description_cache_list.append({
            "name": name,
            "func": _inner
        })
        return _inner

    return _wrapper


class BaseCell:
    pass


class EmptyCell(BaseCell):
    pass


class CellInfo(BaseCell):

    def __init__(self, value, row_merge_count: int = None, col_merge_count: int = None, is_title: bool = False,
                 other_paragraphs: List = None):
        self.value = value
        self.row_merge_count = row_merge_count
        self.col_merge_count = col_merge_count
        self.is_title = is_title
        self.other_paragraphs = other_paragraphs


class CellSingleMixin(CellInfo):

    def __init__(self, value, is_title: bool = False):
        super().__init__(value, 1, 1, is_title)


class CellWholeRowMixin(CellInfo):

    def __init__(self, value, is_title: bool = True):
        super().__init__(value, 1, 4, is_title)


@register_row("基础信息")
def _1(data):
    _cache = []
    _cache.append(CellSingleMixin("项目名称", True))
    _cache.append(CellSingleMixin(data["project_name"], False))
    _cache.append(CellSingleMixin("测试时间", True))
    _cache.append(CellSingleMixin(data["time"], False))
    return [_cache]


@register_row("测试质检结果")
def _2(data):
    _cache = []
    _cache.append(CellSingleMixin("测试质检结果", True))
    _cache.append(CellInfo(data["test_result_text"], 1, 3, False))
    return [_cache]


@register_row("标题")
def _3(data):
    _cache = []
    _cache.append(CellWholeRowMixin("测试版本"))
    return [_cache]


@register_row("版本信息")
def _4(data):
    _cache = []
    _cache.append(CellSingleMixin("产品版本号", False))
    _cache.append(CellInfo(data["version"], 1, 3, False))
    return [_cache]


@register_row("系统地址")
def _5(data):
    _cache = []
    _cache.append(CellSingleMixin("应用系统访问地址", False))
    _cache.append(CellInfo(data["system_url"], 1, 3, False))
    return [_cache]


@register_row("Gitlab地址")
def _6(data):
    _cache = []
    _cache.append(CellSingleMixin("Gitlab地址", False))
    _cache.append(CellInfo(data["gitlab_url"], 1, 3, False))
    return [_cache]


@register_row("测试人员")
def _7(data):
    _cache = []
    _cache.append(CellSingleMixin("测试人员", False))
    _cache.append(CellInfo(data["tester"], 1, 3, False))
    return [_cache]


@register_row("标题")
def _8(data):
    _cache = []
    _cache.append(CellWholeRowMixin("测试内容"))
    return [_cache]


@register_row("测试模块")
def _9(data):
    _cache = []
    _cache.append(CellSingleMixin("测试模块", False))
    _cache.append(CellInfo(data["model"], 1, 3, False))
    return [_cache]


@register_row("详细功能")
def _10(data):
    _table_cache = []
    for model in data["models"]:
        for index, requirement in enumerate(model["requirement"]):
            _cache = []
            _cache.append(EmptyCell())
            if index == 0:
                _cache.append(CellInfo(model["model"], len(model["requirement"]), 1, False))
                _cache.append(CellInfo(requirement["name"], 1, 2, False))
            else:
                _cache.append(EmptyCell())
                _cache.append(CellInfo(requirement["name"], 1, 2, False))
            _table_cache.append(_cache)
    _table_cache[0][0] = CellInfo("详细功能", len(_table_cache), 1, False)
    return _table_cache


@register_row("测试类型")
def _11(data):
    _cache = []
    _cache.append(CellSingleMixin("测试类型", False))
    _cache.append(CellInfo(data["test_type"], 1, 3, False))
    return [_cache]


@register_row("标题")
def _12(data):
    _cache = []
    _cache.append(CellWholeRowMixin("测试结果"))
    return [_cache]


@register_row("实际结果")
def _13(data):
    _cache = []
    _cache.append(CellSingleMixin("实际结果", False))
    _cache.append(CellInfo(data["real_result"], 1, 3, False))
    return [_cache]


@register_row("测试结论")
def _14(data):
    _cache = []
    _cache.append(CellSingleMixin("测试结论", False))
    _cache.append(CellInfo(data["test_result"], 1, 3, False))
    return [_cache]


@register_row("项目风险")
def _15(data):
    _cache = []
    _cache.append(CellSingleMixin("项目风险", False))
    _cache.append(CellInfo(data["project_risk"], 1, 3, False))
    return [_cache]


@register_row("详细内容")
def _16(data):
    _cache = []
    _cache.append(CellWholeRowMixin("详细内容"))
    return [_cache]


@register_row("测试进度")
def _17(data):
    _cache = []
    _cache.append(CellSingleMixin("测试进度", False))
    _cache.append(CellInfo(data["test_progress"], 1, 3, False))
    return [_cache]


@register_row("测试用例")
def _18(data):
    _cache = []
    _cache.append(CellSingleMixin("测试用例", False))
    _cache.append(CellInfo(data["test_cases"], 1, 3, False, other_paragraphs=["{test_cases}"]))
    return [_cache]


@register_row("BUG汇总")
def _19(data):
    _cache = []
    _cache.append(CellSingleMixin("缺陷汇总", False))
    _cache.append(CellInfo(data["bugs"], 1, 3, False, other_paragraphs=["{test_bugs}"]))
    return [_cache]


@register_row("报告人")
def _20(data):
    _cache = []
    _cache.append(CellSingleMixin("报告人", True))
    _cache.append(CellInfo(data["sender"], 1, 3, False))
    return [_cache]


@register_row("复审人")
def _21(data):
    _cache = []
    _cache.append(CellSingleMixin("复审人", True))
    _cache.append(CellInfo(data["reviewer"], 1, 3, False))
    return [_cache]


def get_row_info(data) -> List[List[BaseCell]]:
    result = []
    for row in row_description_cache_list:
        row_result = row["func"](data)
        result.extend(row_result)
    return result
