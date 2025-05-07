from functools import singledispatch
from typing import List

from core._config import _const
from core.execute import _runner
from core.utils import help_info


@singledispatch
def start(args, plugin=None):
    """
    主运行函数
    :param args: 运行参数
    :return:
    """

    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: None, plugins: List = None):
    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: int, plugins: List = None):
    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: str, plugins: List = None):
    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: list, plugins: List = None):
    if "--help" in args:
        help_info()
        return
    if len(args) == 0 or len(args) % 2 != 0:
        raise KeyError(_const.EXCEPTION.CheckRunningArgs % ('[]',))
    for item in args:
        if (isinstance(item, int) or isinstance(item, str)) is False:
            raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))
    return _runner(args, plugins)
