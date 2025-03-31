from abc import ABCMeta

from core._config import PluginPool

disable_method = ["__init__", "get_data"]


class MethodCallMonitor(type):
    def __new__(cls, name, bases, namespace):
        for attr_name, attr_value in namespace.items():
            if callable(attr_value):
                def make_wrapper(method):
                    def wrapper(self, *args, **kwargs):
                        result = method(self, *args, **kwargs)
                        plugin_pool = PluginPool.get_plugins()
                        if type(self).__class__ is MonitorBase:
                            cls.server_dispatch(self, plugin_pool, method.__name__, result)
                            cls.plugin_dispatch(self, plugin_pool, method.__name__, result)
                        return result

                    return wrapper

                namespace[attr_name] = make_wrapper(attr_value)
        return super().__new__(cls, name, bases, namespace)

    @staticmethod
    def server_dispatch(obj, plugin_pool, method_name, result):
        if method_name in disable_method:
            return
        from core.base import Server
        if isinstance(obj, Server) is False:
            return
        for plugin in plugin_pool:
            if method_name in plugin.server_monitor_functions:
                from core.base import Data
                data = Data(obj, result, method_name)
                plugin.get_data(data)

    @staticmethod
    def plugin_dispatch(obj, plugin_pool, method_name, result):
        if method_name in disable_method:
            return
        from core.plugin_base import Plugin
        if isinstance(obj, Plugin) is False:
            return
        for plugin in plugin_pool:
            if obj is not plugin:
                from core.base import Data
                data = Data(obj, result, method_name)
                plugin.get_data(data)


class MonitorBase(MethodCallMonitor, ABCMeta):
    """组合元类"""
    pass
