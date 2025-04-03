from functools import singledispatch

from core._config import _const
from core.execute import _runner


@singledispatch
def start(args):
    """
    主运行函数
    :param args: 运行参数
    :return:
    """

    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: None):
    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: int):
    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: str):
    def _except():
        raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))

    return _except()


@start.register
def _(args: list):
    if len(args) == 0 or len(args) % 2 != 0:
        raise KeyError(_const.EXCEPTION.CheckRunningArgs % ('[]',))
    for item in args:
        if (isinstance(item, int) or isinstance(item, str)) is False:
            raise KeyError(_const.EXCEPTION.LoadingArgs % (str(args, )))
    return _runner(args)
