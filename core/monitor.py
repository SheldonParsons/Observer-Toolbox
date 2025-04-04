from abc import ABCMeta, ABC
from typing import List

from core.root import SourceType


class MethodCallMonitor(type):
    disable_method = ["__init__", "get_notify"]

    def __getattr__(cls, name):
        """通过类代理访问元类属性，同时限制访问"""
        if name == "disable_method":
            return cls.__metaclass__.disable_method
        raise AttributeError(f"'{cls.__name__}' 不存在属性： '{name}'")

    def __new__(cls, name, bases, namespace):

        for attr_name, attr_value in namespace.items():
            for base in bases:
                if base.__name__ == "ServerPlugin":
                    if '__init__' in namespace:
                        raise TypeError(f"ServerPlugin 子类 {name} 禁止定义 __init__ 方法")
                    break
            if callable(attr_value):
                def make_wrapper(method):
                    def wrapper(self, *args, **kwargs):
                        result = method(self, *args, **kwargs)
                        if type(self).__class__ is MonitorBase:
                            from core.generator import PluginPool
                            Dispatcher(self, PluginPool.get_plugins(), method.__name__, result).notify()
                        return result

                    return wrapper

                namespace[attr_name] = make_wrapper(attr_value)
        return super().__new__(cls, name, bases, namespace)


class MonitorBase(MethodCallMonitor, ABCMeta):
    """组合元类"""
    pass


class GenericMonitor(ABC, metaclass=MonitorBase):
    source_type = SourceType.CUSTOMER
    source_name = None


class Dispatcher:

    def __init__(self, obj, plugin_pool, method_name, result):
        self.obj = obj
        self.plugin_pool = plugin_pool
        self.method_name = method_name
        self.result = result

    def notify(self):
        from core.base import Server, Plugin
        if isinstance(self.obj, Server):
            self.server_dispatch(**self.__dict__)
        elif isinstance(self.obj, Plugin):
            self.plugin_dispatch(**self.__dict__)
        else:
            self.standard_dispatch(**self.__dict__)

    @classmethod
    def server_dispatch(cls, obj, plugin_pool, method_name, result):
        cls._generic_dispatch(
            obj,
            plugin_pool,
            method_name,
            result,
            monitor_attr='server_allow_monitor_functions',
            identity_check=False
        )

    @classmethod
    def plugin_dispatch(cls, obj, plugin_pool, method_name, result):
        cls._generic_dispatch(
            obj,
            plugin_pool,
            method_name,
            result,
            monitor_attr='plugin_allow_monitor_functions',
            identity_check=True
        )

    @classmethod
    def standard_dispatch(cls, obj, plugin_pool, method_name, result):
        cls._generic_dispatch(
            obj,
            plugin_pool,
            method_name,
            result,
            monitor_attr="allow_monitor_functions",
            identity_check=False
        )

    @staticmethod
    def _get_monitor_class(_class=None) -> List:
        for key, value in _class.__dict__.items():
            if callable(value) and key != "__init__":
                yield key

    @classmethod
    def _generic_dispatch(cls, obj, plugin_pool, method_name, result, monitor_attr, identity_check):
        if method_name in type(obj).disable_method:
            return False

        for plugin in plugin_pool:
            if identity_check and plugin is obj:
                continue

            if hasattr(plugin, monitor_attr) and method_name in getattr(plugin, monitor_attr):
                from core.base import RunnerResult
                from core.base import Data
                result = result if isinstance(result, RunnerResult) else RunnerResult(obj, result)
                data_payload = Data(obj, result, method_name)
                plugin.get_notify(data_payload)
        return True
