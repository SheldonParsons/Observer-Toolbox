import functools
from core.base import PluginManager
from core.utils import IndexableDict

server_stock = IndexableDict()

class ServerRunner:
    def __init__(self, parameter=None):
        self.parameter = parameter

    def __call__(self, cls):
        global server_stock
        server_stock[cls] = self.parameter

        @functools.wraps(cls)
        def wrapper(*args, **kwargs):
            return cls(*args, **kwargs)

        return wrapper
    

def report_callback(func):
    """装饰器：在run方法执行后触发插件回调"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # 执行原始方法
        result = func(self, *args, **kwargs)
        # 获取插件管理器实例
        manager = PluginManager()
        # 触发所有插件回调
        for plugin in manager.get_plugins():
            plugin.on_data_collected(self.__class__.__name__, result)
            
        return result
    return wrapper