import functools

from core._config import PluginPool
from core.utils import IndexingDict

server_stock = IndexingDict()
plugin_pool = PluginPool


class ServerRunner:
    def __init__(self, parameter=None):
        self.parameter = parameter

    def __call__(self, cls):
        global server_stock

        @functools.wraps(cls)
        def wrapper(*args, **kwargs):
            return cls(*args, **kwargs)

        server_stock[wrapper] = self.parameter
        return wrapper


def inner_plugin(cls):
    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        obj = cls(*args, **kwargs)
        plugin_pool.register(obj)
        return obj

    return wrapper()
