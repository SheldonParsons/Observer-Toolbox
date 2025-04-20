import functools
import threading
from copy import deepcopy
from typing import Dict, TypeVar

T = TypeVar("T", bound=object)


def singleton(cls):
    instances = {}
    lock = threading.Lock()

    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class _PluginPool:

    def __init__(self, include_inner_plugin: bool = True):
        self.plugins = []
        self.include_inner_plugin: bool = include_inner_plugin

    def register(self, plugin):
        self.plugins.append(plugin)

    def get_plugins(self):
        if self.include_inner_plugin:
            import inner_plugins
            sort_list = getattr(inner_plugins, '__all__', None) or []
            order_map = {name: index for index, name in enumerate(sort_list)}
            self.plugins.sort(key=lambda p: order_map.get(type(p).__name__, float('inf')))
        return self.plugins

    def set_plugins(self, plugins):
        self.plugins = plugins

    def set_include_inner_plugin(self, flag):
        self.include_inner_plugin = flag


def _get_plugin_pool() -> _PluginPool:
    return _PluginPool()


@singleton
class _GlobalData:
    def __init__(self):
        self._lock = threading.Lock()
        self._data: Dict[str, T] = {}
        self.system_parameters = None
        self._version = 0  # 数据版本标识

    def set_data(self, value: Dict[str, T]) -> None:
        with self._lock:
            self._data = deepcopy(value)
            self._version += 1

    def get_data(self) -> Dict[str, T]:
        with self._lock:
            return deepcopy(self._data)

    @property
    def data(self) -> Dict[str, T]:
        return self.get_data()

    @data.setter
    def data(self, value: Dict[str, T]) -> None:
        self.set_data(value)

    def update_item(self, key: str, value: T) -> None:
        with self._lock:
            self._data[key] = value
            self._version += 1

    @property
    def version(self) -> int:
        with self._lock:
            return self._version

    def get_with_version(self) -> tuple[Dict[str, T], int]:
        with self._lock:
            return deepcopy(self._data), self._version


def _get_global_data() -> _GlobalData:
    return _GlobalData()


_PluginPool: _PluginPool = _get_plugin_pool()

_GlobalData: _GlobalData = _get_global_data()
