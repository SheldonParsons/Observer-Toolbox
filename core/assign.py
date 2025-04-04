from functools import singledispatch
from typing import List

from core._config import _const
from core.execute import _runner


@singledispatch
def start(args, plugin):
    """
    主运行函数
    :param args: 运行参数
    :return:
    """

    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: None, plugins: List):
    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: int, plugins: List):
    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: str, plugins: List):
    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: list, plugins: List):
    if len(args) == 0 or len(args) % 2 != 0:
        raise KeyError(_const.EXCEPTION.CheckRunningArgs % ('[]',))
    for item in args:
        if (isinstance(item, int) or isinstance(item, str)) is False:
            raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))
    return _runner(args, plugins)
